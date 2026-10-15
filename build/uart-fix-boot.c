/* Finite boot/rollback helper. The attached module owns its own reference;
 * no daemon, timer, IRQ cap, or SD writes in the interrupt handler. */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/syscall.h>
#include <sys/utsname.h>
#include <unistd.h>

/* 0=active/restored, 1=original safely retained, 64=uncertain: withhold stock. */
static int text(const char *path, const char *want) {
 char b[2048]; int fd=open(path,O_RDONLY|O_CLOEXEC);
 if(fd<0)return -1;
 ssize_t n; do {n=read(fd,b,sizeof(b)-1);}while(n<0 && errno==EINTR);
 close(fd); if(n<=0 || n==(ssize_t)sizeof(b)-1)return -1;
 b[n]=0;fputs(b,stdout);
 if(!strcmp(path,"/proc/d35_uart_tx") &&
    (!strstr(b," fault=0 ") || !strstr(b," bypass=0 ") || !strstr(b," cap=0\n")))return -1;
 return strstr(b,want)?0:-1;
}
static int present(void) {
 return !access("/sys/module/d35_uart_tx",F_OK) || !access("/proc/d35_uart_tx",F_OK) ||
  !access("/proc/d35_uart_tx_on",F_OK) || !access("/proc/d35_uart_tx_off",F_OK);
}
static int restore(void) {
 if(text("/proc/d35_uart_tx_off","stop_result=0 restored=1 attached=0"))return 64;
 if(syscall(SYS_delete_module,"d35_uart_tx",O_NONBLOCK) || present())return 64;
 return 0;
}
int main(int argc,char **argv) {
 struct utsname u;
 if(argc!=3 || geteuid()!=0 || uname(&u) || strcmp(u.release,"4.19.128"))return 1;
 if(!strcmp(argv[1],"stop"))return present()?restore():0;
 if(strcmp(argv[1],"start"))return 1;
 /* Never adopt or detach another owner's module, including a diagnostic. */
 if(present())return 64;
 int fd=open(argv[2],O_RDONLY|O_CLOEXEC);if(fd<0)return 1;
 int r=(int)syscall(SYS_finit_module,fd,"",0);close(fd);
 if(r)return present()?64:1;
 if(!text("/proc/d35_uart_tx_on","start_result=0 attached=1") &&
    !text("/proc/d35_uart_tx","version=4 result=0 irq=19 attached=1"))return 0;
 return restore()?64:1;
}
