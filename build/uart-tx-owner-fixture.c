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
static int loaded,attached,primary_reads;
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
    assert(!strcmp(path,"/sys/module/d35_uart_tx") || !strcmp(path,"/proc/d35_uart_tx") || !strcmp(path,"/proc/d35_uart_tx_off") || !strcmp(path,"/proc/d35_uart_tx_on"));
    if(loaded || mode("already_loaded"))return 0;
    errno=ENOENT;return -1;
}
int __wrap_open(const char *path,int flags,...) {
    if(!strcmp(path,"/proc/interrupts"))return 901;
    if(!strcmp(path,"/proc/stat"))return 904;
    if(!strcmp(path,"/proc/d35_uart_tx_on")){assert(loaded);return 903;}
    if(!strcmp(path,"/proc/d35_uart_tx")){assert(loaded);return 900;}
    if(!strcmp(path,"/proc/d35_uart_tx_off")){assert(loaded);return 902;}
    va_list ap;va_start(ap,flags);int permissions=(flags&O_CREAT)?va_arg(ap,int):0;va_end(ap);
    return __real_open(path,flags,permissions);
}
ssize_t __wrap_read(int fd,void *buffer,size_t cap) {
    char text[8192];
    if(fd==901)snprintf(text,sizeof(text)," CPU0\n 19: %llu GIC-0 69 Level (null)\n",tick/1000000*7);
    else if(fd==904) {
        if(mode("cpu_fail")){errno=EIO;return -1;}
        snprintf(text,sizeof(text),"cpu  10 0 20 200 0 0 0 0 0 0\n");
    } else if(fd==903) {
        if(mode("on_fail")){errno=EIO;return -1;}
        if(!mode("on_refuses"))attached=1;
        snprintf(text,sizeof(text),"version=4 start_result=%d attached=%d\n",attached?0:-19,attached);
    } else if(fd==902) {
        if(mode("stop_fail")){errno=EIO;return -1;}
        if(!mode("stop_refuses"))attached=0;
        snprintf(text,sizeof(text),"version=4 stop_result=%d restored=%d attached=%d\n",attached?-19:0,!attached,attached);
    } else if(fd==900) {
        primary_reads++;
        if(mode("read_fail") || (mode("frozen_fail") && primary_reads>10)){errno=EIO;return -1;}
        if(mode("cancel"))raise(SIGTERM);
        snprintf(text,sizeof(text),"version=4 result=%d irq=19 attached=%d calls=100 added=90 writes=80 full=0 empty_stop=10 stopped=0 urgent=0 fallback=10 fault=%d bypass=0 ctrl=0000b070 flags=05 fifo=8 head=100 tail=100 rx=0 tx=100 frame=0 parity=0 overrun=0 brk=0 cap=200000\n",mode("observer_refuses")?-19:0,mode("frozen_refuses") && primary_reads>10?1:attached,mode("fault_seen")?1:0);
    } else return __real_read(fd,buffer,cap);
    size_t n=strlen(text);assert(n<cap);memcpy(buffer,text,n);return (ssize_t)n;
}
int __wrap_close(int fd) { if(fd==900 || fd==901 || fd==902 || fd==903 || fd==904)return 0;return __real_close(fd); }
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
        if(mode("load_fail")){errno=EINVAL;result=-1;}else {loaded=1;attached=0;}
    } else if(number==SYS_delete_module) {
        assert(!strcmp(va_arg(ap,const char *),"d35_uart_tx"));assert(va_arg(ap,int)==O_NONBLOCK);assert(loaded);
        if(mode("unload_fail") || attached){errno=EBUSY;result=-1;}else loaded=0;
    } else abort();
    va_end(ap);return result;
}
