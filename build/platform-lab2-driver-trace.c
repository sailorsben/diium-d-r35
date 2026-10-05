/* Observe the exact vendor syscalls without ptrace or changing their order.
 * ARM32 varargs match the shipped open/ioctl ABI. Only display/scaler FDs
 * enter the bounded RAM trace; unrelated calls pass straight to the kernel. */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/soundcard.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
#define CAP 16384u
static int kinds[256],phase;
struct row { uint64_t begin,end; uint32_t command,argument; int operation,kind,fd,rc,error,phase,status; uint32_t metadata[8]; };
static struct row rows[CAP];
static unsigned count,dropped,flushed;
static uint64_t now(void) {
    struct timespec t={0,0};
    syscall(SYS_clock_gettime,CLOCK_MONOTONIC,&t);
    return (uint64_t)t.tv_sec*1000000000ull+t.tv_nsec;
}
void lab2_driver_phase(int value) { __atomic_store_n(&phase,value,__ATOMIC_RELEASE); }
static void save(int operation,int kind,int fd,uint32_t command,uintptr_t argument,int rc,int error,uint64_t begin,int status,const uint32_t *metadata) {
    unsigned i=__atomic_fetch_add(&count,1u,__ATOMIC_RELAXED);
    if(i>=CAP) { __atomic_fetch_add(&dropped,1u,__ATOMIC_RELAXED); return; }
    rows[i]=(struct row){begin,now(),command,(uint32_t)argument,operation,kind,fd,rc,error,
                        __atomic_load_n(&phase,__ATOMIC_ACQUIRE),status,{0}};
    if(metadata) memcpy(rows[i].metadata,metadata,sizeof(rows[i].metadata));
}
int open(const char *name,int flags,...) {
    mode_t mode=0; va_list args; uint64_t begin=0; int rc,error,kind=0;
    if(flags&O_CREAT) { va_start(args,flags); mode=(mode_t)va_arg(args,int); va_end(args); }
    if(!strcmp(name,"/dev/pscaler_a")) kind=1;
    else if(!strcmp(name,"/dev/disp0") || !strcmp(name,"/dev/disp1")) kind=2;
    if(kind) begin=now();
    rc=(int)syscall(SYS_open,name,flags,mode); error=rc<0?errno:0;
    if(rc>=0 && rc<256) __atomic_store_n(&kinds[rc],kind,__ATOMIC_RELEASE);
    if(kind) save(0,kind,rc,(uint32_t)flags,0,rc,error,begin,-1,NULL);
    if(rc<0) errno=error;
    return rc;
}
int ioctl(int fd,unsigned long command,...) {
    uintptr_t argument=0; va_list args; uint64_t begin=0; int rc,error,status=-1;
    int kind=fd>=0 && fd<256?__atomic_load_n(&kinds[fd],__ATOMIC_ACQUIRE):0;
    uint32_t metadata[8]={0};
    /* The recovered no-argument stop/update/wait commands do not consume r2.
     * All encoded vendor requests retain their literal pointer/scalar r2. */
    if(command!=0x5003u && command!=0x6402u && command!=0x6407u &&
       command!=SNDCTL_DSP_RESET && command!=SNDCTL_DSP_POST) {
        va_start(args,command); argument=va_arg(args,uintptr_t); va_end(args);
    }
    if(kind==1 && command==0x40e45000u && argument) {
        const uint32_t *p=(const uint32_t *)argument; const unsigned char *b=(const unsigned char *)argument;
        metadata[0]=p[14]; metadata[1]=p[16]; metadata[2]=p[17];
        metadata[3]=(p[1]&65535u)<<16|(p[2]&65535u); metadata[4]=(p[6]&65535u)<<16|(p[7]&65535u);
        metadata[5]=b[72]|(uint32_t)b[84]<<8|(uint32_t)b[98]<<16|(uint32_t)b[99]<<24; metadata[6]=b[152];
    } else if(kind==2 && command==0x402c6413u && argument) {
        const uint16_t *p=(const uint16_t *)argument;
        metadata[3]=(uint32_t)p[0]<<16|p[1]; metadata[6]=p[2]; metadata[7]=((const uint32_t *)argument)[2];
    }
    if(kind) begin=now();
    rc=(int)syscall(SYS_ioctl,fd,command,argument); error=rc<0?errno:0;
    if(kind==1 && command==0x80045005u && rc>=0 && argument) status=*(int *)argument;
    if(kind) save(1,kind,fd,(uint32_t)command,argument,rc,error,begin,status,metadata);
    if(rc<0) errno=error;
    return rc;
}
int close(int fd) {
    int kind=fd>=0 && fd<256?__atomic_load_n(&kinds[fd],__ATOMIC_ACQUIRE):0;
    uint64_t begin=kind?now():0; int rc=(int)syscall(SYS_close,fd),error=rc<0?errno:0;
    if(kind) save(2,kind,fd,0,0,rc,error,begin,-1,NULL);
    if(rc==0 && fd>=0 && fd<256) __atomic_store_n(&kinds[fd],0,__ATOMIC_RELEASE);
    if(rc<0) errno=error;
    return rc;
}
int lab2_driver_flush(const char *path) {
    unsigned i,n=__atomic_load_n(&count,__ATOMIC_ACQUIRE); FILE *f=fopen(path,"w");
    if(!f) return -1;
    fprintf(f,"operation,kind,phase,fd,command,argument,rc,errno,begin_ns,end_ns,status,input_addr,output_a,output_b,input_wh,output_wh,queue_drop_flags,h_first_or_pitch,bitmap_addr\n");
    if(n>CAP) n=CAP;
    for(i=flushed;i<n;++i) { struct row *r=&rows[i];
        fprintf(f,"%d,%d,%d,%d,%u,%u,%d,%d,%llu,%llu,%d,%u,%u,%u,%u,%u,%u,%u,%u\n",r->operation,r->kind,r->phase,r->fd,
                r->command,r->argument,r->rc,r->error,(unsigned long long)r->begin,(unsigned long long)r->end,r->status,
                r->metadata[0],r->metadata[1],r->metadata[2],r->metadata[3],r->metadata[4],r->metadata[5],r->metadata[6],r->metadata[7]); }
    fprintf(f,"# captured=%u dropped=%u\n",n-flushed,__atomic_load_n(&dropped,__ATOMIC_ACQUIRE));
    { int rc=fflush(f); if(!rc) rc=fsync(fileno(f)); if(fclose(f)<0) rc=-1; if(!rc) flushed=n; return rc; }
}
