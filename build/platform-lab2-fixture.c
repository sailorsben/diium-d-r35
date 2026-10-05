/* Development-only link wrappers: exercise the real owner/transport code. */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/soundcard.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
#define FD 9999
int __real_open(const char *,int,...);
int __real_close(int);
ssize_t __real_write(int,const void *,size_t);
int __real_ioctl(int,unsigned long,...);
int __real_poll(struct pollfd *,nfds_t,int);
static unsigned rate=44100,fragment=2048,stream_index,writes,polls;
static uint64_t began,accepted;
static int capture=-1;
static uint64_t now(void) {
    struct timespec t; syscall(SYS_clock_gettime,CLOCK_MONOTONIC,&t);
    return (uint64_t)t.tv_sec*1000000000ull+t.tv_nsec;
}
static uint64_t played(void) {
    uint64_t n=began?(now()-began)*rate*4u/1000000000ull:0;
    if(n>accepted) n=accepted;
    return n;
}
int __wrap_open(const char *p,int flags,...) {
    mode_t mode=0; va_list args;
    if(flags&O_CREAT) { va_start(args,flags); mode=(mode_t)va_arg(args,int); va_end(args); }
    if(strcmp(p,"/dev/dsp")) return __real_open(p,flags,mode);
    { char name[512]; const char *base=getenv("D35_LAB_FIXTURE_OUTPUT");
      if(!base) { errno=EINVAL; return -1; }
      snprintf(name,sizeof(name),"%s/fixture-%u.s16",base,stream_index++);
      capture=__real_open(name,O_WRONLY|O_CREAT|O_EXCL,0644);
      if(capture<0) return -1; }
    began=accepted=0; writes=polls=0; return FD;
}
int __wrap_close(int fd) {
    if(fd!=FD) return __real_close(fd);
    if(capture>=0) __real_close(capture);
    capture=-1; return 0;
}
int __wrap_ioctl(int fd,unsigned long command,...) {
    void *p=NULL; va_list args;
    if(command!=SNDCTL_DSP_RESET && command!=SNDCTL_DSP_POST) {
        va_start(args,command); p=va_arg(args,void *); va_end(args);
    }
    if(fd!=FD) return __real_ioctl(fd,command,p);
    if(command==SNDCTL_DSP_SETFRAGMENT) fragment=1u<<(*(int *)p&0xffff);
    else if(command==SNDCTL_DSP_SPEED) rate=(unsigned)*(int *)p;
    else if(command==SNDCTL_DSP_SETFMT || command==SNDCTL_DSP_CHANNELS) {}
    else if(command==SNDCTL_DSP_GETCAPS) *(int *)p=DSP_CAP_TRIGGER|DSP_CAP_MMAP;
    else if(command==SNDCTL_DSP_GETFMTS) *(int *)p=AFMT_S16_LE;
    else if(command==SNDCTL_DSP_GETBLKSIZE) *(int *)p=(int)fragment;
    else if(command==SNDCTL_DSP_GETTRIGGER) { errno=ENOTTY; return -1; }
    else if(command==SNDCTL_DSP_GETODELAY) *(int *)p=(int)(accepted-played());
    else if(command==SNDCTL_DSP_GETOSPACE) {
        audio_buf_info *s=p; s->fragsize=(int)fragment; s->fragstotal=4;
        s->bytes=(int)(fragment*4u)-(int)(accepted-played())-(int)fragment/2; s->fragments=s->bytes/(int)fragment;
    } else if(command==SNDCTL_DSP_GETOPTR) {
        count_info *c=p; uint64_t n=played(); c->bytes=(int)(n&0x7fffffff); c->ptr=(int)(n%(fragment*4u));
        c->blocks=(int)((accepted-n)/fragment);
    } else if(command==SNDCTL_DSP_RESET) { began=accepted=0; }
    else if(command!=SNDCTL_DSP_POST) { errno=EINVAL; return -1; }
    return 0;
}
ssize_t __wrap_write(int fd,const void *p,size_t size) {
    uint64_t queued,room; ssize_t n;
    if(fd!=FD) return __real_write(fd,p,size);
    ++writes; queued=accepted-played(); room=fragment*4u-queued;
    if(writes%7u==0 || !room) { errno=EAGAIN; return -1; }
    if(size>room) size=(size_t)room;
    if(size>137) size=137; /* Deliberately splits stereo samples. */
    n=__real_write(capture,p,size);
    if(n>0) { if(!began) began=now(); accepted+=(uint64_t)n; }
    return n;
}
int __wrap_poll(struct pollfd *fds,nfds_t count,int timeout) {
    struct pollfd copy[4]; nfds_t i; int fake=-1,rc,ready;
    if(count>4) return __real_poll(fds,count,timeout);
    for(i=0;i<count;++i) { copy[i]=fds[i]; fds[i].revents=0;
        if(fds[i].fd==FD) { fake=(int)i; copy[i].fd=-1; } }
    if(fake<0) return __real_poll(fds,count,timeout);
    ++polls;
    ready=accepted-played()<fragment*4u || polls%3u==0; /* Sometimes misleading. */
    rc=__real_poll(copy,count,ready?0:(timeout>2?2:timeout));
    if(rc<0) return rc;
    for(i=0;i<count;++i) fds[i].revents=copy[i].revents;
    if(ready) { fds[fake].revents=POLLOUT; ++rc; }
    return rc;
}
