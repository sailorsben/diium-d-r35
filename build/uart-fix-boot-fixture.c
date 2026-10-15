/* ARM helper seam: module syscalls never reach a real kernel. */
#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/syscall.h>
#include <sys/utsname.h>
#include <unistd.h>
static int loaded,attached,loads,unloads;
static int mode(const char *s){return !strcmp(getenv("FIX_CASE"),s);}
__attribute__((constructor)) static void setup(void){if(!strncmp(getenv("FIX_CASE"),"stop_",5)){loaded=1;attached=1;}}
uid_t __wrap_geteuid(void){return mode("nonroot")?1000:0;}
int __wrap_uname(struct utsname *u){memset(u,0,sizeof(*u));strcpy(u->release,mode("kernel")?"4.19.129":"4.19.128");return 0;}
int __wrap_access(const char *p,int f){assert(f==F_OK && (!strncmp(p,"/proc/d35_uart_tx",17) || !strcmp(p,"/sys/module/d35_uart_tx")));return loaded || mode("existing")?0:-1;}
int __wrap_open(const char *p,int f,...){assert(f==(O_RDONLY|O_CLOEXEC));if(!strcmp(p,"fixture.ko"))return mode("missing")?-1:900;if(!strcmp(p,"/proc/d35_uart_tx_on"))return 901;if(!strcmp(p,"/proc/d35_uart_tx_off"))return 902;if(!strcmp(p,"/proc/d35_uart_tx"))return 903;abort();}
int __wrap_close(int fd){assert(fd>=900 && fd<=903);return 0;}
ssize_t __wrap_read(int fd,void *p,size_t n){
 const char *s=NULL;assert(loaded);
 if(fd==901){if(mode("on_read")){attached=1;errno=EIO;return -1;}attached=!mode("refuse");s=attached?"version=4 start_result=0 attached=1\n":"version=4 start_result=-19 attached=0\n";}
 if(fd==902){if(mode("off_read")){errno=EIO;return -1;}if(!mode("off_refuse") && !mode("stop_refuse"))attached=0;s=attached?"version=4 stop_result=-19 restored=0 attached=1\n":"version=4 stop_result=0 restored=1 attached=0\n";}
 if(fd==903){if(mode("status") || mode("off_read") || mode("off_refuse") || mode("unload"))return -1;s=mode("fault")?"version=4 result=0 irq=19 attached=1 calls=0 fault=1 bypass=0 cap=0\n":mode("capped")?"version=4 result=0 irq=19 attached=1 calls=0 fault=0 bypass=0 cap=200000\n":"version=4 result=0 irq=19 attached=1 calls=0 fault=0 bypass=0 cap=0\n";}
 assert(s && strlen(s)<n);memcpy(p,s,strlen(s));return strlen(s);
}
long __wrap_syscall(long nr,...){
 va_list a;va_start(a,nr);
 if(nr==SYS_finit_module){assert(va_arg(a,int)==900);assert(!strcmp(va_arg(a,char *),""));assert(va_arg(a,int)==0);loads++;if(mode("load")){va_end(a);return -1;}loaded=1;}
 else if(nr==SYS_delete_module){assert(!strcmp(va_arg(a,char *),"d35_uart_tx"));assert(va_arg(a,int)==O_NONBLOCK);assert(loaded && !attached);unloads++;if(mode("unload")){va_end(a);return -1;}loaded=0;}
 else abort();va_end(a);return 0;
}
__attribute__((destructor)) static void verify(void){
 if(mode("normal")){assert(loaded && attached && loads==1 && !unloads);}
 else if(mode("off_read") || mode("off_refuse") || mode("stop_refuse")){assert(loaded && attached && !unloads);}
 else if(mode("unload")){assert(loaded && !attached && unloads==1);}
 else if(mode("refuse") || mode("status") || mode("on_read") || mode("fault") || mode("capped") || mode("stop_normal")){assert(!loaded && !attached && unloads==1);}
 else assert(!loaded && !attached);
}
