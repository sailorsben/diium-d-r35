/* Read-only NOR identification on the surveyed SPI0.0, before stock starts.
 * Commands are fixed: status 05, JEDEC ID 9f. No command/configuration writer.
 * Linux v4.19 spi_ioc_transfer ABI agrees with exact vendor two-transfer reads. */
#define _GNU_SOURCE
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <linux/spi/spidev.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/sysmacros.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#ifdef __arm__
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

typedef char transfer_size_must_be_32[sizeof(struct spi_ioc_transfer)==32?1:-1];
typedef struct {
    int error,owner_pid,operations;
    uint32_t mode,speed;
    unsigned char bits,status_before,status_after,id[3][6];
    char stage[32];
} Result;
static char root[PATH_MAX];

static uint64_t now_ns(void) {
    struct timespec t;if(syscall(SYS_clock_gettime,CLOCK_MONOTONIC,&t)) _exit(2);
    return (uint64_t)t.tv_sec*1000000000ull+(uint64_t)t.tv_nsec;
}
static void delay(void) { struct timespec t={0,1000000};syscall(SYS_nanosleep,&t,NULL); }
static void stage(Result *r,const char *s) { snprintf(r->stage,sizeof(r->stage),"%s",s); }
static int numeric(const char *s) { if(!*s)return 0;for(;*s;s++)if(*s<'0'||*s>'9')return 0;return 1; }
static int pid_number(const char *s) {
    unsigned n=0;for(;*s;s++) { unsigned digit=(unsigned)(*s-'0');if(n>((unsigned)INT_MAX-digit)/10)return 0;n=n*10+digit; }
    return (int)n;
}

/* All live process FD metadata must be inspectable. A disappearing process is
 * expected; unknown permissions/enumeration errors fail closed. No device opens. */
static int owners(Result *r) {
    char path[PATH_MAX],fds[PATH_MAX],link[PATH_MAX];unsigned processes=0,entries=0;
    snprintf(path,sizeof(path),"%s/proc",root);DIR *proc=opendir(path);if(!proc)return errno;
    int error=0;struct dirent64 *p;
    while(!error) {
        errno=0;p=readdir64(proc);if(!p) { error=errno;break; }
        if(!numeric(p->d_name))continue;
        int pid=pid_number(p->d_name);if(!pid) { error=EOVERFLOW;break; }
        if(pid==getpid())continue;
        if(++processes>128) { error=E2BIG;break; }
        snprintf(fds,sizeof(fds),"%s/proc/%s/fd",root,p->d_name);
        DIR *fd=opendir(fds);if(!fd) { if(errno!=ENOENT)error=errno;continue; }
        struct dirent64 *f;
        while(!error) {
            errno=0;f=readdir64(fd);if(!f) { error=errno;break; }
            if(!numeric(f->d_name))continue;
            if(++entries>2048) { error=E2BIG;break; }
            snprintf(path,sizeof(path),"%s/%s",fds,f->d_name);
            ssize_t n=readlink(path,link,sizeof(link)-1);
            if(n<0) { if(errno!=ENOENT)error=errno;continue; }
            link[n]=0;struct stat64 s;int found=!strcmp(link,"/dev/spidev0.0");
            if(!found) {
                if(stat(path,&s)) { if(errno!=ENOENT)error=errno; }
                else found=S_ISCHR(s.st_mode)&&major(s.st_rdev)==153&&minor(s.st_rdev)==0;
            }
            if(found) {
                r->owner_pid=pid;error=EBUSY;
            }
        }
        closedir(fd);
    }
    closedir(proc);return error;
}

static int exchange(int fd,unsigned char command,unsigned char *data,unsigned length,uint32_t speed,Result *r) {
    /* No caller can request write-enable, program, erase or mode-changing opcodes. */
    if(!((command==0x05&&length==1)||(command==0x9f&&length==6)))return EPERM;
    struct spi_ioc_transfer t[2];memset(t,0,sizeof(t));memset(data,0xa5,length);
    t[0].tx_buf=(uintptr_t)&command;t[0].len=1;t[0].speed_hz=speed;t[0].bits_per_word=8;t[0].tx_nbits=1;
    t[1].rx_buf=(uintptr_t)data;t[1].len=length;t[1].speed_hz=speed;t[1].bits_per_word=8;t[1].rx_nbits=1;
    r->operations++;int got=ioctl(fd,SPI_IOC_MESSAGE(2),t);
    if(got<0)return errno;
    return got==(int)(length+1)?0:EIO;
}

static int identify(int fd,Result *r) {
    stage(r,"read-settings");
    if(ioctl(fd,SPI_IOC_RD_MODE32,&r->mode)||ioctl(fd,SPI_IOC_RD_BITS_PER_WORD,&r->bits)||ioctl(fd,SPI_IOC_RD_MAX_SPEED_HZ,&r->speed))return errno;
    if((r->mode&3)!=0&&(r->mode&3)!=3)return EPERM;
    if(r->mode&~(uint32_t)(SPI_CPOL|SPI_CPHA|SPI_TX_DUAL|SPI_TX_QUAD|SPI_RX_DUAL|SPI_RX_QUAD))return EPERM;
    if((r->bits&&r->bits!=8)||!r->speed)return EPERM;
    uint32_t speed=r->speed<1000000u?r->speed:1000000u;
    stage(r,"status-before");int e=exchange(fd,0x05,&r->status_before,1,speed,r);if(e)return e;
    if(r->status_before&1)return EBUSY;
    stage(r,"jedec-repeat");
    for(unsigned i=0;i<3;i++) {
        e=exchange(fd,0x9f,r->id[i],6,speed,r);if(e)return e;
        int untouched=1;for(unsigned j=0;j<6;j++)if(r->id[i][j]!=0xa5)untouched=0;
        if(!r->id[i][0]||r->id[i][0]==0xff||untouched)return ENODATA;
        if(i&&memcmp(r->id[0],r->id[i],6))return EILSEQ;
    }
    stage(r,"status-after");e=exchange(fd,0x05,&r->status_after,1,speed,r);if(e)return e;
    if(r->status_after&1)return EBUSY;
    uint32_t mode=0,speed_after=0;unsigned char bits=0;
    stage(r,"settings-after");
    if(ioctl(fd,SPI_IOC_RD_MODE32,&mode)||ioctl(fd,SPI_IOC_RD_BITS_PER_WORD,&bits)||ioctl(fd,SPI_IOC_RD_MAX_SPEED_HZ,&speed_after))return errno;
    if(mode!=r->mode||bits!=r->bits||speed_after!=r->speed)return ESTALE;
    stage(r,"identified");return 0;
}

static void work(Result *r) {
    stage(r,"owners-before");if((r->error=owners(r)))return;
    char path[PATH_MAX];snprintf(path,sizeof(path),"%s/dev/spidev0.0",root);struct stat64 s;
    stage(r,"device-identity");
    if(lstat(path,&s)) { r->error=errno;return; }
    if(!S_ISCHR(s.st_mode)||major(s.st_rdev)!=153||minor(s.st_rdev)!=0) { r->error=EPERM;return; }
    int fd=open(path,O_RDONLY|O_NOFOLLOW|O_CLOEXEC);if(fd<0) { r->error=errno;return; }
    if(fstat(fd,&s)||!S_ISCHR(s.st_mode)||major(s.st_rdev)!=153||minor(s.st_rdev)!=0)r->error=EPERM;
    else if(flock(fd,LOCK_EX|LOCK_NB))r->error=errno;
    else {
        stage(r,"owners-after");r->error=owners(r);
        if(!r->error)r->error=identify(fd,r);
    }
    close(fd);
}

static int save(FILE *f,Result *r,int timeout,int pending) {
    fprintf(f,"{\"version\":1,\"errno\":%d,\"stage\":\"%s\",\"owner_pid\":%d,\"operations\":%d,\"mode\":%u,\"bits\":%u,\"default_speed_hz\":%u,\"transfer_speed_limit_hz\":1000000,\"status_before\":%u,\"status_after\":%u,\"ids\":[",r->error,r->stage,r->owner_pid,r->operations,r->mode,r->bits,r->speed,r->status_before,r->status_after);
    for(unsigned i=0;i<3;i++) {
        if(i)fputc(',',f);
        fputc('"',f);for(unsigned j=0;j<6;j++)fprintf(f,"%02x",r->id[i][j]);fputc('"',f);
    }
    fprintf(f,"],\"timed_out\":%s,\"reap_pending\":%s,\"flash_writes\":false,\"global_config_writes\":false}\n",timeout?"true":"false",pending?"true":"false");
    fflush(f);return ferror(f)||fsync(fileno(f));
}

int main(int argc,char **argv) {
    if(argc!=3||strlen(argv[1])>PATH_MAX-512||strlen(argv[2])>PATH_MAX-64)return 2;
    snprintf(root,sizeof(root),"%s",!strcmp(argv[1],"/")?"":argv[1]);
    if(mkdir(argv[2],0700))return 2;
    char path[PATH_MAX];snprintf(path,sizeof(path),"%s/result.json",argv[2]);FILE *report=fopen(path,"wx");if(!report)return 2;
    int directory=open(argv[2],O_RDONLY|O_DIRECTORY);if(directory<0||fsync(fileno(report))||fsync(directory))return 2;
    close(directory);int pipefd[2];if(pipe(pipefd))return 2;
    uint64_t end=now_ns()+3000000000ull;pid_t pid=fork();if(pid<0)return 2;
    if(!pid) {
        close(pipefd[0]);Result r={0};work(&r);(void)!write(pipefd[1],&r,sizeof(r));close(pipefd[1]);_exit(0);
    }
    close(pipefd[1]);Result r={0};int status=0,timeout=0,pending=0;pid_t done;
    while(!(done=waitpid(pid,&status,WNOHANG))&&now_ns()<end)delay();
    if(!done) {
        timeout=1;kill(pid,SIGKILL);end=now_ns()+250000000ull;
        while(!(done=waitpid(pid,&status,WNOHANG))&&now_ns()<end)delay();
        r.error=ETIMEDOUT;stage(&r,"deadline");
        if(!done) {
            pending=1;save(report,&r,timeout,pending);
            /* Do not let init start a competing SPI owner while this child is
             * kernel-blocked. Consumed marker makes a later power cycle stock. */
            do { done=waitpid(pid,&status,0); } while(done<0&&errno==EINTR);
        }
    } else if(done<0||!WIFEXITED(status)||WEXITSTATUS(status)||read(pipefd[0],&r,sizeof(r))!=(ssize_t)sizeof(r)) {
        r.error=EIO;stage(&r,"child-result");
    }
    close(pipefd[0]);int failed=save(report,&r,timeout,pending);if(fclose(report))failed=1;
    return failed||r.error?1:0;
}
