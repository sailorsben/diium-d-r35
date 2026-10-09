/* Passive Linux inventory. Never opens /dev nodes, changes drivers, or runs
 * copied vendor tools. Each potentially blocking read lives in an owned child.
 * Scheduling uses the kernel clock syscall, not libc's observed-broken vDSO. */
#define _GNU_SOURCE
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <glob.h>
#include <limits.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#ifdef __arm__
/* Modern cross headers name stat entry points introduced after device glibc. */
extern int __xstat64(int,const char *,struct stat64 *);
extern int __lxstat64(int,const char *,struct stat64 *);
extern int __fxstat64(int,int,struct stat64 *);
#define stat(p,s) __xstat64(3,p,s)
#define lstat(p,s) __lxstat64(3,p,s)
#define fstat(f,s) __fxstat64(3,f,s)
#else
#define stat(p,s) stat64(p,s)
#define lstat(p,s) lstat64(p,s)
#define fstat(f,s) fstat64(f,s)
#endif

#define MAX_CAPTURE (8u*1024u*1024u)
#define TOTAL_CAPTURE (48u*1024u*1024u)
#define MAX_JOBS 2500u
static char root[PATH_MAX], output[PATH_MAX];
static FILE *report;
static uint64_t start_ns, deadline_ns;
static unsigned jobs, missing, failures, truncations;
static size_t total_bytes;
static int capped, stuck;
static const char *group="identity";
typedef struct { int error, truncated; size_t bytes; } Result;

static unsigned number(const char *s) {
    unsigned n=0;
    for(;*s;s++) { if(*s<'0'||*s>'9'||n>100000000u) return 0;n=n*10u+(unsigned)(*s-'0'); }
    return n;
}

static uint64_t now_ns(void) {
    struct timespec t;
    if (syscall(SYS_clock_gettime,CLOCK_MONOTONIC,&t)) { perror("kernel clock"); exit(2); }
    return (uint64_t)t.tv_sec*1000000000ull+(uint64_t)t.tv_nsec;
}
static void quote(const char *s) {
    fputc('"',report);
    for (;*s;s++) { unsigned char c=(unsigned char)*s;
        if(c=='"'||c=='\\') { fputc('\\',report);fputc(c,report); }
        else if(c<32||c>=127) fprintf(report,"\\u%04x",c);
        else fputc(c,report);
    }
    fputc('"',report);
}
static int allowed(const char *p) {
    /* Fixed passive namespaces only. Reject traversal and device paths even
     * when called through the fixture/debug capture mode. */
    if(strstr(p,"/../")||strstr(p,"/./")||strstr(p,"//")||strlen(p)>=PATH_MAX-512) return 0;
    if(!strcmp(p,"/proc/kcore")||!strcmp(p,"/proc/kmsg")) return 0;
    return !strncmp(p,"/proc/",6)||!strncmp(p,"/sys/",5)||!strncmp(p,"/lib/",5)||
        !strncmp(p,"/system/",8)||!strncmp(p,"/bin/",5)||!strncmp(p,"/sbin/",6)||
        !strncmp(p,"/etc/",5)||!strcmp(p,"/init.rc")||!strcmp(p,"/init.project.rc")||
        !strcmp(p,"/sysinit")||!strcmp(p,"/power_key")||!strcmp(p,"/wdt")||!strcmp(p,"/showlogo")||!strcmp(p,"/gpu_env.sh");
}
static int resolve(char *dest,size_t n,const char *p) {
    int k=snprintf(dest,n,"%s%s",root,p);return k>=0&&(size_t)k<n;
}
static int room(void) {
    if(stuck||now_ns()>=deadline_ns||jobs>=MAX_JOBS||total_bytes>=TOTAL_CAPTURE) { capped=1;return 0; }
    return 1;
}
static void capture(const char *path,size_t limit) {
    char source[PATH_MAX],dest[PATH_MAX],name[40];int pipes[2],status=0;
    Result r={0,0,0};struct stat64 s;
    if(!room()) return;
    jobs++;
    snprintf(name,sizeof(name),"capture-%04u.bin",jobs);
    if(!allowed(path)||!resolve(source,sizeof(source),path)) r.error=EPERM;
    else if(lstat(source,&s)) r.error=errno;
    else if(!S_ISREG(s.st_mode)) r.error=EPERM; /* no FIFOs, links, or raw devices */
    if(limit>MAX_CAPTURE) limit=MAX_CAPTURE;
    if(limit>TOTAL_CAPTURE-total_bytes) limit=TOTAL_CAPTURE-total_bytes;
    snprintf(dest,sizeof(dest),"%s/%s",output,name);
    uint64_t begin=now_ns();
    if(!r.error&&pipe(pipes)) r.error=errno;
    else if(!r.error) {
        fflush(report);
        pid_t pid=fork();
        if(pid<0) { r.error=errno;close(pipes[0]);close(pipes[1]); }
        else if(!pid) {
            close(pipes[0]);
            int in=open(source,O_RDONLY|O_NONBLOCK|O_NOFOLLOW|O_CLOEXEC);
            int out=-1;
            if(in<0) r.error=errno;
            else {
                if(fstat(in,&s)||!S_ISREG(s.st_mode)) r.error=EPERM;
                else out=open(dest,O_WRONLY|O_CREAT|O_EXCL|O_CLOEXEC,0600);
                if(out<0&&!r.error) r.error=errno;
                char buf[8192];
                while(!r.error&&r.bytes<limit) {
                    size_t n=limit-r.bytes;if(n>sizeof(buf)) n=sizeof(buf);
                    ssize_t got=read(in,buf,n);
                    if(got<0) { if(errno==EINTR) continue;r.error=errno;break; }
                    if(!got) break;
                    ssize_t off=0;
                    while(off<got) {
                        ssize_t written=write(out,buf+off,(size_t)(got-off));
                        if(written<=0) { if(written<0&&errno==EINTR) continue;r.error=written<0?errno:EIO;break; }
                        off+=written;
                    }
                    r.bytes+=(size_t)off;
                }
                if(!r.error&&r.bytes==limit) {
                    char extra;ssize_t n=read(in,&extra,1);
                    if(n>0) r.truncated=1;else if(n<0) r.error=errno;
                }
                if(out>=0) { if(fsync(out)&&!r.error) r.error=errno;close(out); }
                close(in);
            }
            (void)!write(pipes[1],&r,sizeof(r));close(pipes[1]);_exit(0);
        } else {
            close(pipes[1]);
            uint64_t end=begin+2000000000ull;if(end>deadline_ns) end=deadline_ns;
            pid_t done=0;
            while(!(done=waitpid(pid,&status,WNOHANG))&&now_ns()<end) {
                struct timespec delay={0,1000000};syscall(SYS_nanosleep,&delay,NULL);
            }
            if(!done) {
                kill(pid,SIGKILL);uint64_t reap=now_ns()+250000000ull;
                while(!(done=waitpid(pid,&status,WNOHANG))&&now_ns()<reap) {
                    struct timespec delay={0,1000000};syscall(SYS_nanosleep,&delay,NULL);
                }
                r.error=ETIMEDOUT;
                if(!done) stuck=1;
            } else if(done<0||!WIFEXITED(status)||WEXITSTATUS(status)) r.error=EIO;
            else if(read(pipes[0],&r,sizeof(r))!=(ssize_t)sizeof(r)) r.error=EIO;
            close(pipes[0]);
        }
    }
    if(r.error==ENOENT||r.error==ENOTDIR) missing++;
    else if(r.error) failures++;
    if(r.truncated) truncations++;
    /* Include partial bytes left by killed readers in the budget. */
    if(!stat(dest,&s)&&S_ISREG(s.st_mode)) r.bytes=(size_t)s.st_size;
    total_bytes+=r.bytes;
    fprintf(report,"{\"kind\":\"capture\",\"group\":");quote(group);
    fprintf(report,",\"source\":");quote(path);fprintf(report,",\"output\":");
    if(r.bytes||!r.error) quote(name);else fputs("null",report);
    fprintf(report,",\"errno\":%d,\"bytes\":%zu,\"truncated\":%s,\"elapsed_ns\":%llu}\n",
        r.error,r.bytes,r.truncated?"true":"false",(unsigned long long)(now_ns()-begin));
    fflush(report);
}
static void metadata(const char *path) {
    char source[PATH_MAX],target[PATH_MAX];struct stat64 s;ssize_t n=-1;
    if(!room()||!resolve(source,sizeof(source),path)) return;
    jobs++;int e=lstat(source,&s)?errno:0;
    if(e&&e!=ENOENT&&e!=ENOTDIR) failures++;
    if(!e&&S_ISLNK(s.st_mode)) n=readlink(source,target,sizeof(target)-1);
    fprintf(report,"{\"kind\":\"metadata\",\"group\":");quote(group);
    fprintf(report,",\"source\":");quote(path);fprintf(report,",\"errno\":%d",e);
    if(!e) fprintf(report,",\"mode\":%u,\"size\":%llu,\"rdev\":%llu",
        (unsigned)s.st_mode,(unsigned long long)s.st_size,(unsigned long long)s.st_rdev);
    if(n>=0) { target[n]=0;fprintf(report,",\"link\":");quote(target); }
    fputs("}\n",report);
}
static int ends(const char *p,const char *suffix) {
    size_t a=strlen(p),b=strlen(suffix);return a>=b&&!strcmp(p+a-b,suffix);
}
static void tree(const char *path,unsigned depth,int copies) {
    char source[PATH_MAX],child[PATH_MAX];struct stat64 s;
    if(!room()||!resolve(source,sizeof(source),path)) return;
    metadata(path);
    if(lstat(source,&s)||!S_ISDIR(s.st_mode)) return;
    DIR *dir=opendir(source);
    if(!dir) {
        failures++;fprintf(report,"{\"kind\":\"directory_error\",\"source\":");quote(path);
        fprintf(report,",\"errno\":%d}\n",errno);return;
    }
    struct dirent64 *entry;
    while(room()) {
        errno=0;entry=readdir64(dir);
        if(!entry) {
            if(errno) {
                failures++;fprintf(report,"{\"kind\":\"directory_error\",\"source\":");quote(path);
                fprintf(report,",\"errno\":%d}\n",errno);
            }
            break;
        }
        if(!strcmp(entry->d_name,".")||!strcmp(entry->d_name,"..")) continue;
        int n=snprintf(child,sizeof(child),"%s/%s",path,entry->d_name);
        if(n<0||(size_t)n>=sizeof(child)||!resolve(source,sizeof(source),child)) continue;
        metadata(child);
        if(lstat(source,&s)) continue;
        if(S_ISDIR(s.st_mode)&&depth) tree(child,depth-1,copies);
        else if(S_ISREG(s.st_mode)&&copies==2) capture(child,65536);
        else if(S_ISREG(s.st_mode)&&copies==1&&
            (ends(child,".ko")||strstr(entry->d_name,"modules.")||ends(child,".order"))) capture(child,MAX_CAPTURE);
    }
    closedir(dir);
}
static void patterns(const char *pattern,size_t limit,int copies) {
    char source[PATH_MAX];glob_t g;
    if(!room()||!resolve(source,sizeof(source),pattern)) return;
    memset(&g,0,sizeof(g));int status=glob(source,GLOB_NOSORT,NULL,&g);
    if(!status) for(size_t i=0;i<g.gl_pathc&&room();i++) {
        const char *p=g.gl_pathv[i]+strlen(root);
        if(copies) capture(p,limit);else metadata(p);
    }
    globfree(&g);
}
static void phase(const char *name) {
    group=name;fprintf(report,"{\"kind\":\"phase\",\"name\":");quote(name);
    fprintf(report,",\"elapsed_ns\":%llu}\n",(unsigned long long)(now_ns()-start_ns));
    fflush(report);fsync(fileno(report));
}
static void files(const char *const *paths,size_t limit) {
    for(;*paths&&room();paths++) capture(*paths,limit);
}
int main(int argc,char **argv) {
    if(argc!=4&&argc!=6) { fprintf(stderr,"usage: device-survey ROOT OUTPUT SECONDS [PATH BYTES]\n");return 2; }
    if(strlen(argv[1])>PATH_MAX-512||strlen(argv[2])>PATH_MAX-64) return 2;
    snprintf(root,sizeof(root),"%s",!strcmp(argv[1],"/")?"":argv[1]);
    snprintf(output,sizeof(output),"%s",argv[2]);
    unsigned seconds=number(argv[3]);if(!seconds||seconds>45) return 2;
    if(mkdir(output,0700)) { perror("fresh output directory required");return 2; }
    char path[PATH_MAX];snprintf(path,sizeof(path),"%s/report.jsonl",output);
    report=fopen(path,"wx");if(!report) return 2;
    start_ns=now_ns();deadline_ns=start_ns+(uint64_t)seconds*1000000000ull;
    fputs("{\"kind\":\"start\",\"version\":1,\"raw_device_reads\":false,\"hardware_controls\":false}\n",report);
    if(argc==6) capture(argv[4],number(argv[5]));
    else {
        const char *identity[]={"/proc/sys/kernel/random/boot_id","/proc/version","/proc/cpuinfo","/proc/cmdline",
            "/proc/uptime","/proc/meminfo","/proc/stat","/proc/interrupts","/proc/mounts","/proc/1/mountinfo",
            "/proc/partitions","/proc/mtd","/proc/modules","/proc/devices","/proc/filesystems","/proc/iomem",
            "/proc/ioports","/proc/swaps","/proc/loadavg","/proc/buddyinfo","/proc/slabinfo",
            "/proc/kallsyms","/proc/config.gz","/sys/kernel/notes",NULL};
        files(identity,1024*1024);
        phase("boot-tools");
        const char *boot[]={"/init.rc","/init.project.rc","/etc/inittab","/etc/sdmount.sh","/gpu_env.sh",
            "/sysinit","/power_key","/wdt","/showlogo","/bin/nand_part_info","/bin/nandsync","/bin/busybox",NULL};
        files(boot,MAX_CAPTURE);
        const char *nand_modules[]={
            "/lib/modules/4.19.128/kernel/arch/arm/mach-gpa7xxxa/gp_nand/gp_nand_hal/GPA7XXXA/nand_hal.ko",
            "/lib/modules/4.19.128/kernel/arch/arm/mach-gpa7xxxa/gp_nand/gp_nand_module.ko",
            "/lib/modules/4.19.128/kernel/arch/arm/mach-gpa7xxxa/gp_nand/gp_blk_app.ko",
            "/system/lib/modules/4.19.128/kernel/arch/arm/mach-gpa7xxxa/gp_nand/gp_nand_hal/GPA7XXXA/nand_hal.ko",
            "/system/lib/modules/4.19.128/kernel/arch/arm/mach-gpa7xxxa/gp_nand/gp_nand_module.ko",
            "/system/lib/modules/4.19.128/kernel/arch/arm/mach-gpa7xxxa/gp_nand/gp_blk_app.ko",NULL};
        files(nand_modules,MAX_CAPTURE);
        phase("firmware-storage");
        tree("/sys/block",1,0);tree("/sys/class/mtd",1,0);
        const char *storage[]={"/sys/bus/spi/devices/*/modalias","/sys/bus/spi/devices/*/uevent",
            "/sys/bus/spi/devices/*/of_node/compatible","/sys/bus/spi/devices/*/of_node/name",
            "/sys/bus/spi/devices/*/of_node/reg","/sys/class/block/*/size","/sys/class/block/*/dev",
            "/sys/class/block/*/removable","/sys/class/block/*/ro","/sys/class/mtd/*/name",
            "/sys/class/mtd/*/type","/sys/class/mtd/*/size","/sys/class/mtd/*/erasesize",
            "/sys/class/mtd/*/writesize","/sys/class/mtd/*/dev",NULL};
        for(const char **p=storage;*p;p++) patterns(*p,65536,1);
        patterns("/sys/bus/spi/devices/*/driver",0,0);patterns("/sys/bus/spi/devices/*/of_node",0,0);
        phase("usb");tree("/sys/class/udc",1,0);tree("/sys/kernel/config/usb_gadget",2,0);
        const char *usb[]={"/sys/class/udc/*/uevent","/sys/class/udc/*/state","/sys/class/udc/*/current_speed",
            "/sys/bus/usb/devices/*/idVendor","/sys/bus/usb/devices/*/idProduct","/sys/bus/usb/devices/*/product",
            "/sys/bus/usb/devices/*/manufacturer","/sys/bus/usb/devices/*/uevent",NULL};
        for(const char **p=usb;*p;p++) patterns(*p,65536,1);
        phase("device-tree");tree("/sys/firmware/devicetree/base",10,2);
        capture("/sys/firmware/fdt",MAX_CAPTURE);
        phase("devices-processes");tree("/dev",1,0);
        patterns("/proc/[0-9]*/comm",4096,1);patterns("/proc/[0-9]*/status",16384,1);
        patterns("/proc/[0-9]*/maps",65536,1);patterns("/proc/[0-9]*/exe",0,0);
        patterns("/proc/[0-9]*/fd/*",0,0);
        const char *interfaces[]={"/proc/asound/cards","/proc/asound/devices","/proc/asound/pcm","/proc/asound/timers",
            "/proc/bus/input/devices","/proc/fb","/proc/tty/drivers","/proc/driver/rtc",NULL};
        files(interfaces,65536);
        const char *buses[]={"/sys/bus/i2c/devices/*/name","/sys/bus/i2c/devices/*/modalias",
            "/sys/bus/i2c/devices/*/uevent","/sys/bus/platform/devices/*/modalias",
            "/sys/bus/platform/devices/*/uevent","/sys/class/input/input*/name",
            "/sys/class/input/input*/capabilities/key","/sys/class/gpio/gpiochip*/label",
            "/sys/class/gpio/gpiochip*/base","/sys/class/gpio/gpiochip*/ngpio",
            "/sys/class/net/*/operstate","/sys/devices/system/cpu/cpu*/cache/index*/level",
            "/sys/devices/system/cpu/cpu*/cache/index*/size","/sys/devices/system/cpu/cpu*/cache/index*/type",NULL};
        for(const char **p=buses;*p;p++) patterns(*p,65536,1);
        phase("power-clocks");
        const char *power[]={"/sys/devices/system/cpu/cpu*/cpufreq/cpuinfo_cur_freq",
            "/sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq","/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor",
            "/sys/devices/system/cpu/cpu*/cpufreq/scaling_available_frequencies","/sys/class/thermal/thermal_zone*/type",
            "/sys/class/thermal/thermal_zone*/temp","/sys/class/power_supply/*/uevent",
            "/sys/class/hwmon/hwmon*/name","/sys/class/hwmon/hwmon*/temp*_input",NULL};
        for(const char **p=power;*p;p++) patterns(*p,65536,1);
        phase("module-runtime-inventory");
        tree("/bin",0,0);tree("/sbin",0,0);tree("/lib",1,0);tree("/system/bin",1,0);tree("/system/lib",1,0);
        tree("/lib/modules",10,1);tree("/system/lib/modules",10,1);
        phase("final-sample");capture("/proc/uptime",4096);capture("/proc/stat",65536);
        capture("/proc/interrupts",65536);capture("/proc/meminfo",65536);
    }
    fprintf(report,"{\"kind\":\"complete\",\"jobs\":%u,\"bytes\":%zu,\"missing\":%u,\"failures\":%u,"
        "\"truncated\":%u,\"capped\":%s,\"stuck_child\":%s,\"elapsed_ns\":%llu}\n",jobs,total_bytes,
        missing,failures,truncations,capped?"true":"false",stuck?"true":"false",(unsigned long long)(now_ns()-start_ns));
    fflush(report);int failed=fsync(fileno(report));fclose(report);
    int directory=open(output,O_RDONLY|O_DIRECTORY);if(directory>=0) { if(fsync(directory)) failed=1;close(directory); }
    return failed||stuck?1:0;
}
