/* Link-time syscall/filesystem fixture for the actual production owner.
 * Never forwards module syscalls to any kernel. Artificial time, no A7 timing.
 */
#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/utsname.h>
#include <time.h>
#include <unistd.h>
static int loaded;
static unsigned long long tick=1000000000ull;
static int mode(const char *name) { const char *v=getenv("D35_OWNER_CASE");return v && !strcmp(v,name); }
int __real_open(const char *,int,...);
ssize_t __real_read(int,void *,size_t);
int __real_close(int);
int __real_fsync(int);
uid_t __wrap_geteuid(void) { return 0; }
int __wrap_uname(struct utsname *u) { memset(u,0,sizeof(*u));strcpy(u->release,mode("wrong_kernel")?"4.19.129":"4.19.128");return 0; }
int __wrap_access(const char *path,int mode_flags) {
    assert(mode_flags==F_OK);
    assert(!strcmp(path,"/sys/module/d35_uart_state") || !strcmp(path,"/proc/d35_uart_state"));
    if(loaded || mode("already_loaded"))return 0;
    errno=ENOENT;return -1;
}
int __wrap_open(const char *path,int flags,...) {
    if(!strcmp(path,"/proc/interrupts"))return 901;
    if(!strcmp(path,"/proc/d35_uart_state")){assert(loaded);return 900;}
    va_list ap;va_start(ap,flags);int permissions=(flags&O_CREAT)?va_arg(ap,int):0;va_end(ap);
    return __real_open(path,flags,permissions);
}
ssize_t __wrap_read(int fd,void *buffer,size_t cap) {
    char text[512];
    if(fd==901)snprintf(text,sizeof(text)," CPU0\n 19: %llu GIC-0 69 Level (null)\n",tick/1000000*7);
    else if(fd==900) {
        if(mode("read_fail")){errno=EIO;return -1;}
        if(mode("cancel"))raise(SIGTERM);
        snprintf(text,sizeof(text),"version=1 result=%d irq=19 ctrl=00004000 flags=00 tx=0 rx=0 head=0 tail=0 mismatch=1\n",mode("observer_refuses")?-19:0);
    } else return __real_read(fd,buffer,cap);
    size_t n=strlen(text);assert(n<cap);memcpy(buffer,text,n);return (ssize_t)n;
}
int __wrap_close(int fd) { if(fd==900 || fd==901)return 0;return __real_close(fd); }
int __wrap_fsync(int fd) { if(mode("sync_fail")){errno=EIO;return -1;}return __real_fsync(fd); }
long __wrap_syscall(long number,...) {
    va_list ap;va_start(ap,number);long result=0;
    if(number==SYS_clock_gettime) {
        assert(va_arg(ap,int)==CLOCK_MONOTONIC);struct timespec *t=va_arg(ap,struct timespec *);
        tick+=1000;t->tv_sec=(time_t)(tick/1000000000);t->tv_nsec=(long)(tick%1000000000);
    } else if(number==SYS_nanosleep) {
        const struct timespec *t=va_arg(ap,const struct timespec *);assert(!va_arg(ap,void *));
        tick+=(unsigned long long)t->tv_sec*1000000000ull+t->tv_nsec;
    } else if(number==SYS_finit_module) {
        assert(va_arg(ap,int)>=0);assert(!strcmp(va_arg(ap,const char *),""));assert(va_arg(ap,int)==0);
        assert(!loaded);
        if(mode("load_fail")){errno=EINVAL;result=-1;}else loaded=1;
    } else if(number==SYS_delete_module) {
        assert(!strcmp(va_arg(ap,const char *),"d35_uart_state"));assert(va_arg(ap,int)==O_NONBLOCK);assert(loaded);
        if(mode("unload_fail")){errno=EBUSY;result=-1;}else loaded=0;
    } else abort();
    va_end(ap);return result;
}
