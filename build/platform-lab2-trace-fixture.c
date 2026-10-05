/* Actual dlopen seam: a shared driver calls the exported syscall observer. */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/syscall.h>
#include <time.h>
extern long __real_syscall(long,...);
extern int lab2_driver_flush(const char *);
static int configured,waited,status_seen,closed;
long __wrap_syscall(long command,...) {
    va_list args; long result=-1; va_start(args,command);
    if(command==SYS_clock_gettime) {
        int clock=va_arg(args,int); struct timespec *p=va_arg(args,struct timespec *);
        result=__real_syscall(command,clock,p);
    } else if(command==SYS_open) {
        const char *p=va_arg(args,const char *); int flags=va_arg(args,int); unsigned mode=va_arg(args,unsigned);
        result=!strcmp(p,"/dev/pscaler_a")?100:__real_syscall(command,p,flags,mode);
    } else if(command==SYS_ioctl) {
        int fd=va_arg(args,int); unsigned long request=va_arg(args,unsigned long); uintptr_t arg=va_arg(args,uintptr_t);
        if(fd!=100) { errno=EBADF; result=-1; }
        else if(request==0x40e45000u) { configured=arg && ((unsigned char *)arg)[227]==0x5a; result=configured?0:-1; }
        else if(request==0x80045004u) { waited=arg==3000; result=waited?0:-1; }
        else if(request==0x80045005u) { *(int *)arg=2; status_seen=1; result=0; }
        else if(request==0x5003u || request==0x80045001u) result=0;
    } else if(command==SYS_close) {
        int fd=va_arg(args,int); if(fd==100) { closed=1; result=0; } else result=__real_syscall(command,fd);
    }
    va_end(args); return result;
}
int main(int argc,char **argv) {
    void *driver; int (*run)(void);
    if(argc!=3) return 1;
    driver=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL); if(!driver) { puts(dlerror()); return 2; }
    *(void **)(&run)=dlsym(driver,"fixture"); if(!run || run()) return 3;
    if(!configured || !waited || !status_seen || !closed || lab2_driver_flush(argv[2])) return 4;
    dlclose(driver); puts("PASS: actual dlopen driver, 228-byte pointer, scalar 3000, status bit and close"); return 0;
}
