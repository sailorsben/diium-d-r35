#define _GNU_SOURCE
#include "snes-mvp/board.h"
#include "snes-mvp/timing.h"
#include "snes-mvp/startup.h"
#include "snes-mvp/platform.h"
#include "snes-mvp/ui.h"
#include "platform-lab2-font.h"
#include <arm_neon.h>
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <pthread.h>
#include <signal.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/eventfd.h>
#include <sys/ioctl.h>
#include <sys/prctl.h>
#include <sys/soundcard.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/sysmacros.h>
#include <sys/timerfd.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define NS 1000000000ull
#define PERIOD 16688155ull
#define TRACE_CAP 4096u
#define TIMER_CAP 1200u
#define RING_BYTES 32768u
#define FRAME_BYTES (256u*224u*2u)
static int journal=-1, simulated, quick, fixture_stall, fixture_oss;
static uint64_t deadline_ns=120*NS;
static const char *output;
static _Atomic int stopped;
static volatile uint32_t sink;
static uint16_t canvas[UI_WIDTH*UI_HEIGHT], image[256*224];
extern void lab2_driver_phase(int);
extern int lab2_driver_flush(const char *);
static void stop_signal(int sig) { (void)sig; stopped=1; }
static uint64_t cpu_now(void) {
    struct timespec t={0,0};
    if(syscall(SYS_clock_gettime,CLOCK_THREAD_CPUTIME_ID,&t)<0) return 0;
    return (uint64_t)t.tv_sec*NS+t.tv_nsec;
}
static void path(char *p,size_t n,const char *leaf) { snprintf(p,n,"%s/%s",output,leaf); }
static void record(const char *fmt,...) {
    char line[2048]; va_list ap; int n; size_t off=0;
    va_start(ap,fmt); n=vsnprintf(line,sizeof(line)-2,fmt,ap); va_end(ap);
    if(n<0 || n>=(int)sizeof(line)-2) _exit(90);
    line[n++]='\n';
    while(off<(size_t)n) { ssize_t r=write(journal,line+off,(size_t)n-off);
        if(r<0 && errno==EINTR) continue;
        if(r<=0) _exit(90);
        off+=(size_t)r;
    }
    if(fsync(journal)<0) _exit(90);
}
static FILE *report_file(const char *leaf) {
    char p[512]; FILE *f; path(p,sizeof(p),leaf); f=fopen(p,"w");
    if(!f) _exit(90);
    return f;
}
static void finish_file(FILE *f) {
    if(fflush(f)<0 || fsync(fileno(f))<0 || fclose(f)<0) _exit(90);
}
static void copy_file(FILE *f,const char *p,size_t limit) {
    char b[1024]; int fd=open(p,O_RDONLY|O_NONBLOCK|O_CLOEXEC);
    fprintf(f,"\n--- %s ---\n",p);
    if(fd<0) { fprintf(f,"unavailable errno=%d\n",errno); return; }
    while(limit) { ssize_t n=read(fd,b,limit<sizeof(b)?limit:sizeof(b));
        if(n<0 && errno==EINTR) continue;
        if(n<=0) { if(n<0) fprintf(f,"read_errno=%d\n",errno); break; }
        fwrite(b,1,(size_t)n,f); limit-=(size_t)n;
    }
    close(fd);
}
/* Use the target's 64-bit inode ABI, including when QEMU sees host NTFS. */
extern int __xstat64(int,const char *,struct stat64 *);
static void node(FILE *f,const char *p) {
    struct stat64 s; char base[256],link[512]; ssize_t n;
    if(__xstat64(3,p,&s)<0) { fprintf(f,"node=%s errno=%d\n",p,errno); return; }
    fprintf(f,"node=%s mode=%o major=%u minor=%u inode=%llu\n",p,(unsigned)s.st_mode,
            major(s.st_rdev),minor(s.st_rdev),(unsigned long long)s.st_ino);
    if(!S_ISCHR(s.st_mode)) return;
    snprintf(base,sizeof(base),"/sys/dev/char/%u:%u/device/driver",major(s.st_rdev),minor(s.st_rdev));
    n=readlink(base,link,sizeof(link)-1);
    if(n>=0) { link[n]=0; fprintf(f,"driver_link=%s target=%s\n",base,link); }
    else fprintf(f,"driver_link=%s errno=%d\n",base,errno);
}
static void directory(FILE *f,const char *p,unsigned cap) {
    DIR *d=opendir(p); struct dirent64 *e; unsigned count=0; char child[512];
    fprintf(f,"\n--- directory %s cap=%u ---\n",p,cap);
    if(!d) { fprintf(f,"unavailable errno=%d\n",errno); return; }
    while(count<cap && (e=readdir64(d))) {
        if(e->d_name[0]=='.') continue;
        snprintf(child,sizeof(child),"%s/%s",p,e->d_name); node(f,child); ++count;
    }
    fprintf(f,"entries=%u capped=%d\n",count,count==cap); closedir(d);
}
static void kernel_interfaces(FILE *f) {
    FILE *symbols=fopen("/proc/kallsyms","r"); char line[512]; unsigned found=0,read_lines=0,counts[8]={0};
    fprintf(f,"\n--- selected kernel interfaces ---\n");
    if(!symbols) { fprintf(f,"unavailable errno=%d\n",errno); return; }
    while(read_lines++<200000u && fgets(line,sizeof(line),symbols)) {
        int kind=strstr(line,"pscaler")?0:strstr(line,"chunkmem")?1:strstr(line,"pcm_oss")?2:
                 strstr(line,"gp_disp")?3:(strstr(line,"gp_audio") || strstr(line,"gp_i2s"))?4:
                 strstr(line,"galcore")?5:strstr(line,"hrtimer")?6:strstr(line,"clockevents")?7:-1;
        if(kind>=0 && counts[kind]<32u) { ++counts[kind]; fputs(line,f); ++found; }
    }
    fprintf(f,"selected=%u scanned_lines=%u per_class_cap=32 scan_capped=%d\n",found,read_lines,read_lines>=200000u); fclose(symbols);
}
static void kernel_config(void) {
    char p[512],b[1024]; int source=open("/proc/config.gz",O_RDONLY|O_NONBLOCK|O_CLOEXEC),target=-1,error=0;
    size_t bytes=0,limit=131072; path(p,sizeof(p),"kernel-config.gz");
    if(source<0) { record("event=kernel_config available=0 errno=%d",errno); return; }
    target=open(p,O_WRONLY|O_CREAT|O_EXCL|O_CLOEXEC,0644); if(target<0) _exit(90);
    while(bytes<limit) { ssize_t n=read(source,b,sizeof(b)); size_t off=0;
        if(n<0 && errno==EINTR) continue;
        if(n<=0) { if(n<0) error=errno; break; }
        while(off<(size_t)n) { ssize_t wrote=write(target,b+off,(size_t)n-off); if(wrote<0 && errno==EINTR) continue;
            if(wrote<=0) _exit(90);
            off+=(size_t)wrote; }
        bytes+=(size_t)n;
    }
    if(fsync(target)<0) _exit(90);
    close(target); close(source); record("event=kernel_config available=1 bytes=%u capped=%d errno=%d",(unsigned)bytes,bytes==limit,error);
}
static void snapshot(const char *leaf,int inventory) {
    FILE *f=report_file(leaf); char ring[32768]; int n;
    const char *basic[]={"/proc/sys/kernel/random/boot_id","/proc/uptime","/proc/stat",
        "/proc/meminfo","/proc/interrupts","/proc/self/status","/proc/self/maps"};
    unsigned i; fprintf(f,"version=lab2 kernel_ns=%llu simulated=%d\n",(unsigned long long)timing_now_ns(),simulated);
    for(i=0;i<sizeof(basic)/sizeof(basic[0]);++i) copy_file(f,basic[i],8192);
    if(inventory) {
        const char *extra[]={"/proc/cpuinfo","/proc/version","/proc/cmdline","/proc/devices",
            "/proc/mounts","/proc/self/timerslack_ns","/proc/timer_list","/proc/asound/cards",
            "/sys/devices/system/clocksource/clocksource0/current_clocksource",
            "/sys/devices/system/clocksource/clocksource0/available_clocksource",
            "/sys/kernel/tracing/trace_clock","/sys/kernel/tracing/available_events",
            "/sys/kernel/debug/tracing/trace_clock","/sys/kernel/debug/tracing/available_events",
            "/sys/kernel/debug/clk/clk_summary","/sys/class/misc/pscaler_a/dev",
            "/sys/class/misc/chunkmem/dev","/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq"};
        for(i=0;i<sizeof(extra)/sizeof(extra[0]);++i) copy_file(f,extra[i],16384);
        directory(f,"/dev",160); directory(f,"/dev/snd",32);
        directory(f,"/sys/class/sound",32); directory(f,"/sys/class/misc",64);
        kernel_interfaces(f);
    }
    n=(int)syscall(SYS_syslog,3,ring,sizeof(ring)); fprintf(f,"\n--- kernel ring ---\n");
    if(n>0) fwrite(ring,1,(size_t)n,f); else fprintf(f,"unavailable errno=%d\n",errno);
    finish_file(f);
}
static int notice(const char *title,const char *message) {
    ui_draw_notice(canvas,UI_WIDTH,title,message);
    if(board_video_submit(canvas,UI_WIDTH,UI_HEIGHT,UI_WIDTH*2)<0) return -1;
    board_wait_display(); platform_heartbeat_tick(); return 0;
}
static void flush_driver(unsigned index) {
    char leaf[64],p[512]; board_wait_display();
    snprintf(leaf,sizeof(leaf),"driver-calls-%u.csv",index); path(p,sizeof(p),leaf);
    if(lab2_driver_flush(p)<0) _exit(90);
}
static void cpu_work(uint64_t duration) {
    uint64_t began=cpu_now(); uint32_t x=sink|1u; unsigned i;
    do { for(i=0;i<256;++i) { x=x*1664525u+1013904223u; x^=x>>13; } }
    while(!stopped && cpu_now()-began<duration);
    sink=x;
}
struct load_run { int stop; uint64_t cpu; };
static void *load_worker(void *arg) {
    struct load_run *r=arg; uint32_t x=123; unsigned i; uint64_t began=cpu_now();
    while(!stopped && !__atomic_load_n(&r->stop,__ATOMIC_ACQUIRE)) {
        for(i=0;i<1024;++i) { x=x*1664525u+1013904223u; x^=x>>13; }
        __asm__ volatile("" : "+r"(x));
    }
    r->cpu=cpu_now()-began; return NULL;
}
struct timer_sample { uint64_t begin,end,cpu,requested,slack,expirations; int method,load,rc,error; };
static struct timer_sample timer_samples[TIMER_CAP];
static int timer_tests(void) {
    const unsigned waits[]={1,2,5}; unsigned sl,load,method,w,i,n=0;
    long original=syscall(SYS_prctl,PR_GET_TIMERSLACK,0UL,0UL,0UL,0UL);
    int fd=timerfd_create(CLOCK_MONOTONIC,TFD_NONBLOCK|TFD_CLOEXEC),failed=0;
    struct timespec res={0,0}; int rc;
    errno=0; rc=(int)syscall(SYS_clock_getres,CLOCK_MONOTONIC,&res);
    record("event=timer_capability getres_rc=%d errno=%d resolution_ns=%llu original_slack_ns=%ld timerfd_fd=%d",
           rc,rc<0?errno:0,(unsigned long long)((uint64_t)res.tv_sec*NS+res.tv_nsec),original,fd);
    for(sl=0;sl<2 && !stopped;++sl) {
        long applied;
        if(sl && original<0) continue;
        errno=0; rc=sl?(int)syscall(SYS_prctl,PR_SET_TIMERSLACK,1UL,0UL,0UL,0UL):0;
        applied=syscall(SYS_prctl,PR_GET_TIMERSLACK,0UL,0UL,0UL,0UL);
        record("event=timer_slack reduced=%u set_rc=%d measured_ns=%ld",sl,rc,applied);
        if(sl && rc<0) continue;
        for(load=0;load<2 && !stopped;++load) {
            pthread_t thread; struct load_run r={0,0}; int started=0;
            if(load) { rc=pthread_create(&thread,NULL,load_worker,&r); if(rc) { failed=rc; break; } started=1; }
            for(method=0;method<4 && !stopped;++method) for(w=0;w<3 && !stopped;++w) {
                if(method==3 && fd<0) continue;
                for(i=0;i<(quick?2u:24u) && !stopped;++i) {
                    struct timer_sample *s=&timer_samples[n++]; struct timespec t={0,(long)waits[w]*1000000};
                    uint64_t cpu=cpu_now(); memset(s,0,sizeof(*s)); s->requested=(uint64_t)t.tv_nsec;
                    s->method=(int)method; s->load=(int)load; s->slack=applied<0?0:(uint64_t)applied;
                    platform_heartbeat_tick(); s->begin=timing_now_ns(); errno=0;
                    if(method==0) s->rc=nanosleep(&t,NULL);
                    else if(method==1) s->rc=(int)syscall(SYS_clock_nanosleep,CLOCK_MONOTONIC,0,&t,NULL);
                    else if(method==2) s->rc=poll(NULL,0,(int)waits[w]);
                    else { struct itimerspec setting={{0,0},t}; struct pollfd p={fd,POLLIN,0};
                        s->rc=timerfd_settime(fd,0,&setting,NULL);
                        if(!s->rc) { s->rc=poll(&p,1,200); if(s->rc>0) {
                            ssize_t got=read(fd,&s->expirations,sizeof(s->expirations));
                            if(got!=(ssize_t)sizeof(s->expirations)) s->rc=-1;
                        } else if(!s->rc) { s->rc=-1; errno=ETIMEDOUT; } }
                    }
                    s->error=s->rc<0?errno:0; s->end=timing_now_ns(); s->cpu=cpu_now()-cpu;
                }
                if(board_poll_input()&BOARD_MENU) stopped=1;
            }
            if(started) { __atomic_store_n(&r.stop,1,__ATOMIC_RELEASE); pthread_join(thread,NULL); }
            record("event=timer_context reduced=%u load=%u worker_cpu_ns=%llu",sl,load,(unsigned long long)r.cpu);
        }
    }
    if(original>=0) {
        long restored;
        rc=(int)syscall(SYS_prctl,PR_SET_TIMERSLACK,(unsigned long)original,0UL,0UL,0UL,0UL);
        restored=syscall(SYS_prctl,PR_GET_TIMERSLACK,0UL,0UL,0UL,0UL);
        record("event=timer_restore rc=%d original_ns=%ld current_ns=%ld",rc,original,restored);
        if(rc<0 || restored!=original) failed=EIO;
    }
    if(fd>=0) close(fd);
    { FILE *f=report_file("timers.csv"); fputs("method,load,requested_ns,slack_ns,begin_ns,end_ns,cpu_ns,rc,errno,expirations\n",f);
      for(i=0;i<n;++i) { struct timer_sample *s=&timer_samples[i];
          fprintf(f,"%d,%d,%llu,%llu,%llu,%llu,%llu,%d,%d,%llu\n",s->method,s->load,
                  (unsigned long long)s->requested,(unsigned long long)s->slack,(unsigned long long)s->begin,
                  (unsigned long long)s->end,(unsigned long long)s->cpu,s->rc,s->error,(unsigned long long)s->expirations); }
      finish_file(f); }
    record("event=timer_end samples=%u failed=%d",n,failed); return failed?-1:0;
}

struct observation {
    uint64_t begin,query_begin,end,accepted; int operation,rc,error,revents,requested;
    int delay_rc,delay_error,delay,space_rc,space_error,space,ptr_rc,ptr_error,bytes,ptr,blocks;
};
static struct observation trace[TRACE_CAP];
static unsigned trace_count,trace_dropped;
static void observe(int fd,uint64_t accepted,int op,int rc,int error,int revents,int requested,uint64_t begin) {
    audio_buf_info space; count_info ptr; struct observation *s;
    if(trace_count==TRACE_CAP) { ++trace_dropped; return; }
    s=&trace[trace_count++]; memset(s,0,sizeof(*s)); s->begin=begin; s->accepted=accepted;
    s->operation=op; s->rc=rc; s->error=error; s->revents=revents; s->requested=requested;
    s->query_begin=timing_now_ns();
    errno=0; s->delay_rc=ioctl(fd,SNDCTL_DSP_GETODELAY,&s->delay); s->delay_error=s->delay_rc<0?errno:0;
    errno=0; s->space_rc=ioctl(fd,SNDCTL_DSP_GETOSPACE,&space); s->space_error=s->space_rc<0?errno:0;
    if(!s->space_rc) s->space=space.bytes;
    errno=0; s->ptr_rc=ioctl(fd,SNDCTL_DSP_GETOPTR,&ptr); s->ptr_error=s->ptr_rc<0?errno:0;
    if(!s->ptr_rc) { s->bytes=ptr.bytes; s->ptr=ptr.ptr; s->blocks=ptr.blocks; }
    s->end=timing_now_ns();
}
static void flush_trace(const char *leaf) {
    unsigned i; FILE *f=report_file(leaf);
    fputs("operation,requested,rc,errno,revents,begin_ns,query_begin_ns,end_ns,accepted_bytes,delay_rc,delay_errno,delay_bytes,space_rc,space_errno,free_bytes,ptr_rc,ptr_errno,ptr_bytes,ptr,blocks\n",f);
    for(i=0;i<trace_count;++i) { struct observation *s=&trace[i];
        fprintf(f,"%d,%d,%d,%d,%d,%llu,%llu,%llu,%llu,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n",
                s->operation,s->requested,s->rc,s->error,s->revents,(unsigned long long)s->begin,
                (unsigned long long)s->query_begin,(unsigned long long)s->end,(unsigned long long)s->accepted,s->delay_rc,s->delay_error,s->delay,
                s->space_rc,s->space_error,s->space,s->ptr_rc,s->ptr_error,s->bytes,s->ptr,s->blocks);
    }
    finish_file(f); record("event=trace_saved file=%s samples=%u dropped=%u",leaf,trace_count,trace_dropped);
    trace_count=trace_dropped=0;
}
static int audio_open(unsigned rate,unsigned fragment) {
    int fd,fmt=AFMT_S16_LE,channels=2,value=(int)rate,frag=(4<<16)|(int)fragment,rc,error;
    audio_buf_info space; const unsigned commands[]={SNDCTL_DSP_GETCAPS,SNDCTL_DSP_GETFMTS,SNDCTL_DSP_GETBLKSIZE,SNDCTL_DSP_GETTRIGGER};
    const char *names[]={"GETCAPS","GETFMTS","GETBLKSIZE","GETTRIGGER"}; unsigned i;
    fd=open("/dev/dsp",O_WRONLY|O_NONBLOCK|O_CLOEXEC);
    if(fd<0) { record("event=audio_open_error rate=%u errno=%d",rate,errno); return -1; }
    errno=0; rc=ioctl(fd,SNDCTL_DSP_SETFRAGMENT,&frag); error=rc<0?errno:0;
    record("event=fragment_hint log2_bytes=%u rc=%d errno=%d",fragment,rc,error);
    if(ioctl(fd,SNDCTL_DSP_SETFMT,&fmt)<0 || fmt!=AFMT_S16_LE ||
       ioctl(fd,SNDCTL_DSP_CHANNELS,&channels)<0 || channels!=2 ||
       ioctl(fd,SNDCTL_DSP_SPEED,&value)<0 || value!=(int)rate) {
        record("event=audio_config_error requested=%u accepted=%d fmt=%d channels=%d errno=%d",rate,value,fmt,channels,errno);
        close(fd); return -1;
    }
    for(i=0;i<4;++i) { int v=0; errno=0; rc=ioctl(fd,commands[i],&v);
        record("event=audio_capability name=%s command=%u rc=%d errno=%d value=%d",names[i],commands[i],rc,rc<0?errno:0,v); }
    memset(&space,0,sizeof(space)); errno=0; rc=ioctl(fd,SNDCTL_DSP_GETOSPACE,&space);
    record("event=audio_config requested_rate=%u accepted_rate=%d requested_log2=%u space_rc=%d errno=%d fragment_bytes=%d fragments=%d capacity_bytes=%d",
           rate,value,fragment,rc,rc<0?errno:0,space.fragsize,space.fragstotal,space.fragstotal*space.fragsize);
    return fd;
}
static void tone(int16_t *p,unsigned frames,unsigned rate,uint64_t start,uint64_t total) {
    unsigned i; uint64_t ramp=rate/50u;
    for(i=0;i<frames;++i) { uint64_t at=start+i,phase=(at*400u)%rate,remaining=total>at?total-at:0;
        int v=(int)(phase*2400u/rate); if(v>1200) v=2400-v; v-=600;
        if(at<ramp) v=(int)((int64_t)v*(int64_t)at/(int64_t)ramp);
        if(remaining<ramp) v=(int)((int64_t)v*(int64_t)remaining/(int64_t)ramp);
        if(at==0 || at+1>=total) v=0;
        p[i*2]=p[i*2+1]=(int16_t)v;
    }
}
static int drain_audio(int fd,uint64_t accepted) {
    uint64_t began=timing_now_ns(); int empty=0,rc;
    errno=0; rc=ioctl(fd,SNDCTL_DSP_POST,0);
    observe(fd,accepted,4,rc,rc<0?errno:0,0,0,began);
    while(!stopped && timing_now_ns()-began<500000000ull) {
        int delay=-1; uint64_t t=timing_now_ns(); errno=0;
        rc=ioctl(fd,SNDCTL_DSP_GETODELAY,&delay); observe(fd,accepted,3,rc,rc<0?errno:0,0,0,t);
        if(!rc && delay==0) { empty=1; break; }
        timing_sleep_until(t+5000000ull); platform_heartbeat_tick();
    }
    record("event=drain observed_empty=%d elapsed_ns=%llu",empty,(unsigned long long)(timing_now_ns()-began));
    errno=0; rc=ioctl(fd,SNDCTL_DSP_RESET,0); observe(fd,accepted,5,rc,rc<0?errno:0,0,0,timing_now_ns());
    record("event=audio_reset rc=%d",rc); return empty;
}
static int transport(unsigned rate,unsigned fragment,unsigned quantum,unsigned index) {
    int fd,error=0; int16_t samples[1024]; unsigned offset=0,pending=0; char leaf[64];
    uint64_t generated=0,accepted=0,total=quick?rate/8u:rate*2u,start,cpu,until;
    lab2_driver_phase(10+(int)index); notice("AUDIO TRANSPORT","SMOOTH TONES / AUTOMATIC");
    record("event=transport_begin index=%u rate=%u log2=%u quantum_frames=%u",index,rate,fragment,quantum);
    if(simulated && !fixture_oss) { record("event=audio_skipped index=%u",index); return 0; }
    fd=audio_open(rate,fragment); if(fd<0) return -1;
    trace_count=trace_dropped=0; start=timing_now_ns(); cpu=cpu_now(); until=start+(quick?NS:5*NS);
    observe(fd,0,0,0,0,0,0,start);
    while(!stopped && accepted<total*4u && timing_now_ns()<until) {
        ssize_t wrote; uint64_t t; unsigned request;
        platform_heartbeat_tick();
        if(!pending) { unsigned count=(unsigned)((total-generated)<quantum?total-generated:quantum);
            tone(samples,count,rate,generated,total); generated+=count; pending=count*4u; offset=0; }
        request=pending; t=timing_now_ns(); errno=0; wrote=write(fd,(unsigned char *)samples+offset,pending);
        if(wrote>0) { accepted+=(uint64_t)wrote; offset+=(unsigned)wrote; pending-=(unsigned)wrote; }
        error=wrote<0?errno:0; observe(fd,accepted,1,(int)wrote,error,0,(int)request,t);
        if(wrote<0 && error==EINTR) continue;
        if(wrote<0 && error!=EAGAIN && error!=EWOULDBLOCK) break;
        if(wrote<=0) { struct pollfd p={fd,POLLOUT,0}; int rc;
            t=timing_now_ns(); errno=0; rc=poll(&p,1,100); error=rc<0?errno:0;
            observe(fd,accepted,2,rc,error,p.revents,100,t);
            if(rc<0 && error!=EINTR) break;
            if(p.revents&(POLLERR|POLLHUP|POLLNVAL)) { error=EIO; break; }
            /* Preserve immediate-readiness/EAGAIN mismatch; bound its CPU use. */
            if(timing_now_ns()-t<1000000ull) timing_sleep_until(t+1000000ull);
        }
    }
    cpu=cpu_now()-cpu;
    record("event=transport_end index=%u generated_frames=%llu accepted_bytes=%llu target_bytes=%llu active_ns=%llu cpu_ns=%llu complete=%d final_errno=%d",
           index,(unsigned long long)generated,(unsigned long long)accepted,(unsigned long long)(total*4u),
           (unsigned long long)(timing_now_ns()-start),(unsigned long long)cpu,accepted==total*4u,error);
    drain_audio(fd,accepted); close(fd); snprintf(leaf,sizeof(leaf),"transport-%u.csv",index); flush_trace(leaf);
    return accepted==total*4u || stopped?0:-1;
}

static void fill_pixels(uint16_t *p,unsigned count,uint16_t value) {
    unsigned i; uint16x8_t v=vdupq_n_u16(value);
    for(i=0;i+8<=count;i+=8) vst1q_u16(p+i,v);
    for(;i<count;++i) p[i]=value;
}
static void label(unsigned x,unsigned y,const char *s,unsigned scale,uint16_t color) {
    unsigned row,bit,xx,yy;
    for(;*s && x+5*scale<=256;++s,x+=6*scale) {
        const unsigned char *glyph=lab2_glyph((unsigned char)*s);
        for(row=0;row<7;++row) for(bit=0;bit<5;++bit) if(glyph[row]&(16u>>bit))
            for(yy=0;yy<scale && y+row*scale+yy<224;++yy) for(xx=0;xx<scale;++xx)
                image[(y+row*scale+yy)*256+x+bit*scale+xx]=color;
    }
}
static void draw_test_frame(int event_wait,int burst,unsigned rate,unsigned frames) {
    char number[32]; fill_pixels(image,256*224,0x0843);
    label(16,18,"LAB 2",3,0x571b);
    label(16,62,event_wait?"DEVICE PACING":"TIMER PACING",2,0xffff);
    snprintf(number,sizeof(number),"%u HZ",rate); label(16,99,number,2,0xce79);
    label(16,137,burst?"CPU BURSTS":"STEADY CPU",2,0xffff);
    label(16,174,"AUTO / MENU STOP",1,0xce79);
    fill_pixels(image+212*256,(frames%240u)+1u,0x571b);
}
static int memory_test(void) {
    struct { uint32_t physical,mapped,bytes; } chunk={0,0,FRAME_BYTES};
    int fd=-1,rc; uint16_t *heap=NULL,*mapped=NULL; unsigned mode,i,j,loops=quick?2u:80u;
    notice("MEMORY PATH","HEAP / CHUNK / COPY");
    if(simulated) { record("event=memory_skipped reason=simulated"); return 0; }
    rc=posix_memalign((void **)&heap,16,FRAME_BYTES); if(rc) return -1;
    fd=open("/dev/chunkmem",O_RDWR|O_CLOEXEC);
    if(fd<0 || ioctl(fd,0xc00c4301u,&chunk)<0 || !chunk.mapped) { free(heap); if(fd>=0) close(fd); return -1; }
    mapped=(uint16_t *)(uintptr_t)chunk.mapped; fill_pixels(heap,FRAME_BYTES/2,0x571b);
    record("event=memory_mapping physical=%u mapped=%u bytes=%u",chunk.physical,chunk.mapped,chunk.bytes);
    for(mode=0;mode<4 && !stopped;++mode) {
        uint64_t began=timing_now_ns(),cpu=cpu_now();
        for(i=0;i<loops && !stopped;++i) {
            if(mode==0) fill_pixels(heap,FRAME_BYTES/2,0x571b);
            else if(mode==1) fill_pixels(mapped,FRAME_BYTES/2,0x571b);
            else if(mode==2) memcpy(mapped,heap,FRAME_BYTES);
            else { fill_pixels(heap,FRAME_BYTES/2,0x571b); memcpy(mapped,heap,FRAME_BYTES); }
            sink^=((volatile uint16_t *)(mode==0?heap:mapped))[i%(FRAME_BYTES/2)];
        }
        cpu=cpu_now()-cpu;
        record("event=memory mode=%u bytes=%u loops=%u cpu_ns=%llu wall_ns=%llu",mode,FRAME_BYTES,i,
               (unsigned long long)cpu,(unsigned long long)(timing_now_ns()-began));
    }
    for(j=0;j<FRAME_BYTES/2;++j) if(mapped[j]!=0x571b || heap[j]!=0x571b) break;
    snapshot("memory-mappings.txt",0);
    rc=ioctl(fd,0x400c4303u,&chunk); close(fd); free(heap);
    record("event=memory_end exact=%d free_rc=%d",j==FRAME_BYTES/2,rc); return j==FRAME_BYTES/2 && !rc?0:-1;
}

/* One audio owner holds this mutex across nonblocking write, queue bookkeeping
 * and GETODELAY publication. Producer never reads the device independently. */
struct controller {
    pthread_mutex_t lock; pthread_cond_t changed;
    unsigned char ring[RING_BYTES]; unsigned read,count; int stop,error,fd,event,timer;
    unsigned rate,limit; int event_wait;
    uint64_t accepted,owner_cpu,waits,timeouts,immediate,fallbacks;
    int observed_delay; uint64_t observation_ns;
};
static void notify_owner(struct controller *c) { uint64_t one=1; ssize_t r=write(c->event,&one,sizeof(one)); (void)r; }
static void owner_fail(struct controller *c,int error) {
    pthread_mutex_lock(&c->lock); c->error=error; c->stop=1;
    pthread_cond_broadcast(&c->changed); pthread_mutex_unlock(&c->lock);
}
static int owner_sample(struct controller *c) {
    int delay=-1,rc; uint64_t t=timing_now_ns(); errno=0;
    rc=ioctl(c->fd,SNDCTL_DSP_GETODELAY,&delay);
    observe(c->fd,c->accepted,6,rc,rc<0?errno:0,0,(int)c->count,t);
    if(rc<0 || delay<0) return -1;
    c->observed_delay=delay; c->observation_ns=timing_now_ns(); return 0;
}
static void *controller_worker(void *arg) {
    struct controller *c=arg; uint64_t cpu=cpu_now();
    for(;;) {
        int have,budget,rc,error; uint64_t t; struct pollfd p[2];
        pthread_mutex_lock(&c->lock);
        if(c->stop || stopped) { pthread_mutex_unlock(&c->lock); break; }
        if(c->count) {
            unsigned n=RING_BYTES-c->read; ssize_t r;
            if(n>c->count) n=c->count;
            t=timing_now_ns(); errno=0; r=write(c->fd,c->ring+c->read,n); error=r<0?errno:0;
            if(r>0) { c->accepted+=(uint64_t)r; c->count-=(unsigned)r; c->read=(c->read+(unsigned)r)%RING_BYTES; }
            observe(c->fd,c->accepted,1,(int)r,error,0,(int)n,t);
            if(r<0 && error!=EAGAIN && error!=EWOULDBLOCK && error!=EINTR) c->error=error;
        }
        if(owner_sample(c)<0) c->error=EIO;
        have=c->count!=0;
        /* Reserve one maximum native frame against observed total lead. */
        budget=(uint64_t)c->count+(unsigned)c->observed_delay+(c->rate/59u+1u)*4u>c->limit;
        pthread_cond_broadcast(&c->changed);
        if(c->error) { pthread_mutex_unlock(&c->lock); break; }
        pthread_mutex_unlock(&c->lock);
        p[0].fd=c->event; p[0].events=POLLIN; p[0].revents=0;
        p[1].fd=c->fd; p[1].events=POLLOUT; p[1].revents=0;
        t=timing_now_ns(); ++c->waits;
        if(!have && !budget) rc=poll(p,1,100);
        else if(c->event_wait) rc=poll(p,2,100);
        else { p[1].fd=c->timer; p[1].events=POLLIN;
            { struct itimerspec setting={{0,0},{0,2000000}};
              if(timerfd_settime(c->timer,0,&setting,NULL)<0) { owner_fail(c,errno); break; } }
            rc=poll(p,2,100);
        }
        error=rc<0?errno:0;
        if(!rc) ++c->timeouts;
        if(rc>0 && timing_now_ns()-t<1000000ull) ++c->immediate;
        pthread_mutex_lock(&c->lock);
        observe(c->fd,c->accepted,7,rc,error,p[1].revents,have,t);
        pthread_mutex_unlock(&c->lock);
        if(rc<0 && error!=EINTR) { owner_fail(c,error); break; }
        if((p[0].revents|p[1].revents)&(POLLERR|POLLHUP|POLLNVAL)) { owner_fail(c,EIO); break; }
        if(p[0].revents&POLLIN) { uint64_t value; while(read(c->event,&value,sizeof(value))>0) {} }
        if(!c->event_wait && (p[1].revents&POLLIN)) { uint64_t value; ssize_t got=read(c->timer,&value,sizeof(value)); (void)got; }
        if(c->event_wait && (have || budget) && rc>0 && timing_now_ns()-t<1000000ull) {
            ++c->fallbacks; timing_sleep_until(t+1000000ull);
        }
    }
    pthread_mutex_lock(&c->lock); c->stop=1; c->owner_cpu=cpu_now()-cpu;
    pthread_cond_broadcast(&c->changed); pthread_mutex_unlock(&c->lock); return NULL;
}
static struct controller ctl;
struct producer_row { uint64_t begin,admitted,work_end,published,submitted,cpu,observation; unsigned samples,lead; };
static struct producer_row producer_rows[256];
static int wait_changed(struct controller *c) {
    struct timespec now; uint64_t t; int rc;
    if(syscall(SYS_clock_gettime,CLOCK_REALTIME,&now)<0) return -1;
    t=(uint64_t)now.tv_sec*NS+now.tv_nsec+100000000ull;
    now.tv_sec=(time_t)(t/NS); now.tv_nsec=(long)(t%NS);
    rc=pthread_cond_timedwait(&c->changed,&c->lock,&now);
    return rc==0 || rc==ETIMEDOUT?0:-1;
}
static int controller_test(unsigned rate,int event_wait,int burst,unsigned index) {
    struct controller *c=&ctl; pthread_t worker; int rc,failed=0; unsigned frames=0;
    uint64_t start,active_end,cpu,wait_ns=0,frac=0,generated=0,frame_cpu_max=0;
    uint64_t total=quick?rate/2u:rate*4u; int16_t pcm[2048]; char leaf[64];
    lab2_driver_phase(20+(int)index); notice(event_wait?"DEVICE PACING":"TIMER PACING",burst?"BURST CPU / EVERY DRAW":"STEADY CPU / EVERY DRAW");
    record("event=controller_begin index=%u rate=%u event_wait=%d burst=%d lead_limit_ms=45",index,rate,event_wait,burst);
    if(simulated && !fixture_oss) { record("event=controller_skipped index=%u",index); return 0; }
    memset(c,0,sizeof(*c)); c->fd=audio_open(rate,10); if(c->fd<0) return -1;
    c->event=eventfd(0,EFD_NONBLOCK|EFD_CLOEXEC); c->timer=timerfd_create(CLOCK_MONOTONIC,TFD_NONBLOCK|TFD_CLOEXEC);
    if(c->event<0 || c->timer<0) { if(c->event>=0) close(c->event); if(c->timer>=0) close(c->timer); close(c->fd); return -1; }
    c->rate=rate; c->limit=(unsigned)((uint64_t)rate*45u*4u/1000u); c->event_wait=event_wait;
    pthread_mutex_init(&c->lock,NULL); pthread_cond_init(&c->changed,NULL);
    trace_count=trace_dropped=0; board_video_metrics(&(struct board_video_metrics){0},1);
    rc=pthread_create(&worker,NULL,controller_worker,c); if(rc) { failed=rc; goto unstarted; }
    start=timing_now_ns(); cpu=cpu_now();
    while(!stopped && generated<total && timing_now_ns()-start<(quick?2*NS:8*NS)) {
        unsigned count,bytes,tail,first; uint64_t began,frame_cpu;
        struct producer_row *pr=&producer_rows[frames]; memset(pr,0,sizeof(*pr));
        platform_heartbeat_tick(); if(board_poll_input()&BOARD_MENU) { stopped=1; break; }
        frac+=(uint64_t)rate*PERIOD; count=(unsigned)(frac/NS); frac%=NS;
        if(count>total-generated) count=(unsigned)(total-generated);
        bytes=count*4u; began=timing_now_ns(); pr->begin=began; pr->samples=count;
        pthread_mutex_lock(&c->lock);
        while(!c->stop && !stopped && ((uint64_t)c->count+(unsigned)c->observed_delay+bytes>c->limit || RING_BYTES-c->count<bytes))
            if(wait_changed(c)<0) { c->error=EIO; c->stop=1; break; }
        failed=c->error; rc=c->stop; pr->lead=c->count+(unsigned)c->observed_delay;
        pr->observation=c->observation_ns; pthread_mutex_unlock(&c->lock);
        pr->admitted=timing_now_ns();
        wait_ns+=timing_now_ns()-began; if(rc || failed || stopped) break;
        frame_cpu=cpu_now(); cpu_work(12000000ull);
        if(burst && frames%30u==29u) cpu_work(16000000ull); /* 28ms total every 30 calls. */
        frame_cpu=cpu_now()-frame_cpu; if(frame_cpu>frame_cpu_max) frame_cpu_max=frame_cpu;
        pr->cpu=frame_cpu; pr->work_end=timing_now_ns();
        tone(pcm,count,rate,generated,total); generated+=count;
        pthread_mutex_lock(&c->lock); tail=(c->read+c->count)%RING_BYTES; first=RING_BYTES-tail;
        if(first>bytes) first=bytes;
        memcpy(c->ring+tail,pcm,first); memcpy(c->ring,(unsigned char *)pcm+first,bytes-first); c->count+=bytes;
        pthread_mutex_unlock(&c->lock); notify_owner(c); pr->published=timing_now_ns();
        draw_test_frame(event_wait,burst,rate,frames);
        if(board_video_submit(image,256,224,512)<0) { failed=EIO; break; }
        pr->submitted=timing_now_ns();
        ++frames;
    }
    active_end=timing_now_ns(); cpu=cpu_now()-cpu;
    { uint64_t until=timing_now_ns()+500000000ull;
      pthread_mutex_lock(&c->lock);
      while(c->count && !c->stop && !stopped && timing_now_ns()<until) if(wait_changed(c)<0) break;
      c->stop=1; pthread_mutex_unlock(&c->lock); notify_owner(c); pthread_join(worker,NULL); }
    board_wait_display();
    { struct board_video_metrics m; board_video_metrics(&m,0);
      record("event=controller_end index=%u frames=%u generated_frames=%llu accepted_bytes=%llu ring_bytes=%u active_ns=%llu elapsed_ns=%llu producer_cpu_ns=%llu owner_cpu_ns=%llu producer_wait_ns=%llu max_frame_cpu_ns=%llu polls=%llu poll_timeouts=%llu immediate_wakes=%llu fallback_sleeps=%llu submitted=%llu flipped=%llu error=%d complete=%d",
             index,frames,(unsigned long long)generated,(unsigned long long)c->accepted,c->count,
             (unsigned long long)(active_end-start),
             (unsigned long long)(timing_now_ns()-start),(unsigned long long)cpu,(unsigned long long)c->owner_cpu,
             (unsigned long long)wait_ns,(unsigned long long)frame_cpu_max,(unsigned long long)c->waits,
             (unsigned long long)c->timeouts,(unsigned long long)c->immediate,(unsigned long long)c->fallbacks,
             (unsigned long long)m.submitted,(unsigned long long)m.flipped,c->error?c->error:failed,
             generated==total && c->accepted==total*4u && !c->error && !failed); }
    drain_audio(c->fd,c->accepted); snprintf(leaf,sizeof(leaf),"controller-%u.csv",index); flush_trace(leaf);
    { unsigned j; FILE *f; snprintf(leaf,sizeof(leaf),"producer-%u.csv",index); f=report_file(leaf);
      fputs("frame,samples,begin_ns,admitted_ns,work_end_ns,published_ns,submitted_ns,cpu_ns,observed_lead_bytes,observation_ns\n",f);
      for(j=0;j<frames;++j) { struct producer_row *r=&producer_rows[j];
          fprintf(f,"%u,%u,%llu,%llu,%llu,%llu,%llu,%llu,%u,%llu\n",j,r->samples,(unsigned long long)r->begin,
                  (unsigned long long)r->admitted,(unsigned long long)r->work_end,(unsigned long long)r->published,
                  (unsigned long long)r->submitted,(unsigned long long)r->cpu,r->lead,(unsigned long long)r->observation); }
      finish_file(f); }
    if(generated!=total || c->accepted!=total*4u || c->error) failed=failed?failed:EIO;
unstarted:
    close(c->event); close(c->timer); close(c->fd); pthread_mutex_destroy(&c->lock); pthread_cond_destroy(&c->changed);
    return failed && !stopped?-1:0;
}
static int selftest(void) {
    int16_t pcm[2048]; unsigned i; uint64_t frac=0,frames=0;
    for(i=0;i<60000;++i) { frac+=32040ull*PERIOD; frames+=frac/NS; frac%=NS; }
    if(frames!=32040ull*PERIOD*60000ull/NS) return -1;
    tone(pcm,1024,32040,0,1024);
    if(pcm[0]!=0 || pcm[2046]!=0) return -1;
    for(i=0;i<1024;++i) if(pcm[i*2]!=pcm[i*2+1] || pcm[i*2]>600 || pcm[i*2]<-600) return -1;
    /* Byte ring wrap must preserve a partial stereo-frame tail. */
    { unsigned char ring[16]={0},expected[13]; unsigned head=11,n=13,first=16-head;
      for(i=0;i<n;++i) expected[i]=(unsigned char)(i+31);
      memcpy(ring+head,expected,first); memcpy(ring,expected+first,n-first);
      for(i=0;i<n;++i) if(ring[(head+i)%16]!=expected[i]) return -1; }
    return 0;
}
static int suite(void) {
    char p[512]; int failed=0; unsigned i;
    const unsigned profiles[][3]={{32040,11,128},{44100,11,128},{32040,10,256},{44100,10,256},{44100,9,64}};
    signal(SIGTERM,stop_signal); signal(SIGINT,stop_signal);
    path(p,sizeof(p),"startup.log"); setenv("D35_MVP_STARTUP_LOG",p,1); startup_begin();
    record("event=run_begin version=lab2 simulated=%d pid=%ld kernel_ns=%llu",simulated,(long)getpid(),(unsigned long long)timing_now_ns());
    if(fixture_stall) { signal(SIGTERM,SIG_IGN); for(;;) pause(); }
    snapshot("inventory.txt",1); if(!simulated) kernel_config();
    if(selftest()<0 || board_open(simulated)<0) { record("event=initialization_error"); return 3; }
    board_set_input_trace(0);
    if(notice("D-R35 LAB 2","AUTO TEST / ABOUT 90 SECONDS")<0) goto fail;
    notice("TIMER CONTRACT","IDLE / LOAD / TIMER SLACK");
    if(timer_tests()<0) failed=1;
    if(!stopped && memory_test()<0) failed=1;
    for(i=0;i<5 && !stopped;++i) {
        if(transport(profiles[i][0],profiles[i][1],profiles[i][2],i)<0) failed=1;
        flush_driver(10+i);
        if(board_poll_input()&BOARD_MENU) stopped=1;
    }
    if(!stopped) { if(controller_test(32040,0,0,0)<0) failed=1; flush_driver(20); }
    if(!stopped) { if(controller_test(32040,1,0,1)<0) failed=1; flush_driver(21); }
    if(!stopped) { if(controller_test(32040,1,1,2)<0) failed=1; flush_driver(22); }
    if(!stopped) { if(controller_test(44100,1,1,3)<0) failed=1; flush_driver(23); }
    snapshot("latest-platform.txt",0);
    notice(stopped?"TEST CANCELLED":"TEST COMPLETE",failed?"ISSUES RECORDED / RETURNING":"LOGS SAVED / STOCK NEXT");
    board_close(); path(p,sizeof(p),"driver-calls.csv"); if(lab2_driver_flush(p)<0) _exit(90);
    snapshot("final-platform.txt",0);
    record("event=run_end status=%s issues=%d kernel_ns=%llu",stopped?"cancelled":"complete",failed,(unsigned long long)timing_now_ns());
    return 0; /* Capability failures are data; cleanup succeeded. */
fail:
    record("event=run_error message=%s",board_last_error()); board_close(); return 4;
}
static int supervise(void) {
    pid_t child; int status,term=0,killed=0; uint64_t start=timing_now_ns();
    record("event=supervisor_begin deadline_ns=%llu",(unsigned long long)deadline_ns);
    child=fork(); if(child<0) return 5;
    if(!child) { int rc=suite(); close(journal); _exit(rc); }
    for(;;) {
        pid_t r=waitpid(child,&status,WNOHANG); uint64_t elapsed=timing_now_ns()-start;
        if(r==child) { record("event=supervisor_end child=%ld status=%d term=%d killed=%d",(long)child,status,term,killed);
            return term?72:(WIFEXITED(status)?WEXITSTATUS(status):6); }
        if(r<0 && errno!=EINTR) return 6;
        if(!term && elapsed>=deadline_ns) {
            char src[256]; FILE *f=report_file("timeout-child.txt");
            snprintf(src,sizeof(src),"/proc/%ld/status",(long)child); copy_file(f,src,4096);
            snprintf(src,sizeof(src),"/proc/%ld/wchan",(long)child); copy_file(f,src,512);
            snprintf(src,sizeof(src),"/proc/%ld/stack",(long)child); copy_file(f,src,4096); finish_file(f);
            snapshot("timeout-platform.txt",0); record("event=deadline action=term"); kill(child,SIGTERM); term=1;
        }
        if(!killed && elapsed>=deadline_ns+(simulated?100000000ull:3*NS)) {
            record("event=deadline action=kill"); kill(child,SIGKILL); killed=1;
        }
        timing_sleep_until(timing_now_ns()+100000000ull);
    }
}
int main(int argc,char **argv) {
    int i,self=0,supervised=0,preview=0; char p[512];
    for(i=1;i<argc;++i) {
        if(!strcmp(argv[i],"--selftest")) self=1;
        else if(!strcmp(argv[i],"--null")) simulated=1;
        else if(!strcmp(argv[i],"--quick")) quick=1;
        else if(!strcmp(argv[i],"--supervise")) supervised=1;
        else if(!strcmp(argv[i],"--fixture-stall")) fixture_stall=1;
        else if(!strcmp(argv[i],"--fixture-oss")) fixture_oss=1;
        else if(!strcmp(argv[i],"--preview")) preview=1;
        else if(!strcmp(argv[i],"--deadline-ms") && i+1<argc) {
            const char *s=argv[++i]; unsigned long value=0;
            if(!*s) return 1;
            for(;*s;++s) { if(*s<'0' || *s>'9' || value>120000) return 1; value=value*10u+(unsigned)(*s-'0'); }
            if(value<20 || value>120000) return 1;
            deadline_ns=(uint64_t)value*1000000ull;
        } else if(!strcmp(argv[i],"--output") && i+1<argc) output=argv[++i];
        else return 1;
    }
    if(self) { if(selftest()<0) return 2; puts("PASS: fractional native PCM, ramp endpoints, stereo, partial-byte ring wrap"); return 0; }
    if(preview && output && strlen(output)<=350) {
        FILE *f; unsigned j; draw_test_frame(1,1,32040,100); f=report_file("preview.ppm");
        fputs("P6\n256 224\n255\n",f);
        for(j=0;j<256*224;++j) { unsigned v=image[j]; unsigned char rgb[3]={(v>>11)*255/31,((v>>5)&63)*255/63,(v&31)*255/31}; fwrite(rgb,1,3,f); }
        finish_file(f); return 0;
    }
    if(!output || strlen(output)>350 || !supervised || ((fixture_stall || fixture_oss || quick || deadline_ns!=120*NS) && !simulated)) return 1;
    path(p,sizeof(p),"results.log"); journal=open(p,O_WRONLY|O_CREAT|O_EXCL|O_CLOEXEC,0644);
    if(journal<0 || !timing_now_ns() || !cpu_now()) return 1;
    i=supervise(); close(journal); return i;
}
