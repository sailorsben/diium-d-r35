/* Bounded original-status capture owner. Standard module syscalls with flags=0 /
 * O_NONBLOCK only; no forced load/unload, memory devices or UART register writes.
 * No samples go to SD until measurement and owned-module teardown finish.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
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

static char report[65536];
static size_t used;
static volatile sig_atomic_t cancelled;
static void cancel(int signal_number) { (void)signal_number;cancelled=1; }
static uint64_t now(void) {
    struct timespec t;
    if(syscall(SYS_clock_gettime,CLOCK_MONOTONIC,&t))return 0;
    return (uint64_t)t.tv_sec*1000000000u+t.tv_nsec;
}
static void append(const char *format,...) {
    va_list ap;va_start(ap,format);
    int n=vsnprintf(report+used,sizeof(report)-used,format,ap);va_end(ap);
    if(n<0 || (size_t)n>=sizeof(report)-used)exit(90);
    used+=(size_t)n;
}
static void pause_until(uint64_t deadline) {
    for(;;) {
        uint64_t current=now();if(!current || current>=deadline || cancelled)return;
        uint64_t remaining=deadline-current;
        struct timespec t={(time_t)(remaining/1000000000u),(long)(remaining%1000000000u)};
        if(syscall(SYS_nanosleep,&t,NULL) && errno!=EINTR)return;
    }
}
static int read_text(const char *path,char *data,size_t cap) {
    int fd=open(path,O_RDONLY|O_CLOEXEC);if(fd<0)return -1;
    ssize_t n=read(fd,data,cap-1);int saved=errno;close(fd);errno=saved;
    if(n<0 || (size_t)n>=cap-1)return -1;
    data[n]=0;return (int)n;
}
static void irq_sample(const char *phase) {
    char data[8192];unsigned long count=0;int found=0;
    uint64_t begin=now();
    if(read_text("/proc/interrupts",data,sizeof(data))>=0) {
        char *p=data;
        while(*p) {
            char *q=p;unsigned int irq=0;int digits=0;
            while(*q==' ' || *q=='\t')q++;
            while(*q>='0' && *q<='9'){irq=irq*10u+(unsigned int)(*q++-'0');digits=1;}
            if(digits && *q++==':' && irq==19) {
                while(*q==' ' || *q=='\t')q++;
                count=0;digits=0;
                while(*q>='0' && *q<='9'){count=count*10ul+(unsigned long)(*q++-'0');digits=1;}
                if(digits){found=1;break;}
            }
            p=strchr(p,'\n');if(!p)break;p++;
        }
    }
    append("irq phase=%s begin_ns=%llu end_ns=%llu valid=%d count=%lu\n",phase,
           (unsigned long long)begin,(unsigned long long)now(),found,count);
}
static int snapshot(const char *label) {
 char text[8192];int n;
 irq_sample(label);
 uint64_t begin=now();n=read_text("/proc/stat",text,sizeof(text));
 if(n<0 || strncmp(text,"cpu ",4))return -1;
 char *end=strchr(text,'\n');if(!end)return -1;*end=0;
 append("cpu phase=%s begin_ns=%llu end_ns=%llu %s\n",label,(unsigned long long)begin,(unsigned long long)now(),text);
 n=read_text("/proc/d35_uart_tx",text,sizeof(text));if(n<0)return -1;
 append("status phase=%s owner_ns=%llu %s",label,(unsigned long long)now(),text);
 return strncmp(text,"version=4 ",10) || !strstr(text," result=0 ") || !strstr(text," fault=0 ") || !strstr(text," bypass=0 ")?-1:0;
}
static int control(int on) {
 char text[256];int n=read_text(on?"/proc/d35_uart_tx_on":"/proc/d35_uart_tx_off",text,sizeof(text));
 if(n<0){append("control=%s read_errno=%d\n",on?"on":"off",errno);return -1;}
 append("control=%s %s",on?"on":"off",text);
 return on?(!strstr(text,"start_result=0 attached=1")):(!strstr(text,"stop_result=0 restored=1 attached=0"));
}
static int flush(int fd) {
    size_t offset=0;
    while(offset<used){ssize_t n=write(fd,report+offset,used-offset);if(n<0 && errno==EINTR)continue;if(n<=0)return -1;offset+=(size_t)n;}
    used=0;return fsync(fd);
}
static int sync_parent(const char *path) {
    char parent[PATH_MAX];size_t n=strlen(path);if(n>=sizeof(parent))return -1;
    memcpy(parent,path,n+1);char *slash=strrchr(parent,'/');if(!slash)return -1;
    if(slash==parent)slash[1]=0;else *slash=0;
    int fd=open(parent,O_RDONLY|O_DIRECTORY|O_CLOEXEC);if(fd<0)return -1;
    int result=fsync(fd);close(fd);return result;
}
int main(int argc,char **argv) {
    if(argc!=3 || geteuid()!=0)return 2;
    struct utsname u;
    if(uname(&u) || strcmp(u.release,"4.19.128"))return 3;
    if(!access("/sys/module/d35_uart_tx",F_OK) || !access("/proc/d35_uart_tx",F_OK) || !access("/proc/d35_uart_tx_off",F_OK) || !access("/proc/d35_uart_tx_on",F_OK))return 4;
    int out=open(argv[2],O_WRONLY|O_CREAT|O_EXCL|O_CLOEXEC,0600);if(out<0)return 5;
    signal(SIGTERM,cancel);signal(SIGINT,cancel);
    append("version=uart-tx1 clock=kernel_syscall module_flags=0 unload_flags=O_NONBLOCK\n");
    append("phase=before_load kernel=%s pid=%ld\n",u.release,(long)getpid());
    if(!now() || flush(out) || sync_parent(argv[2])){close(out);return 6;}
    irq_sample("before_baseline");pause_until(now()+1000000000u);irq_sample("after_baseline");
    int fd=cancelled?-1:open(argv[1],O_RDONLY|O_CLOEXEC),loaded=0,result=0;
    if(fd<0){result=7;append("load_open_errno=%d\n",errno);}
    else {
        int r=(int)syscall(SYS_finit_module,fd,"",0);int saved=errno;close(fd);
        append("load_result=%d load_errno=%d\n",r,r<0?saved:0);
        if(r<0)result=8;else loaded=1;
    }
    if(loaded) {
        const char *names[]={"original0","corrected0","restored0","corrected1","restored1"};
        for(unsigned i=0;i<5 && !cancelled;i++) {
            if(i && control(i&1)){result=14;break;}
            append("phase=%s event=begin\n",names[i]);
            if(snapshot(names[i])){result=9;break;}
            pause_until(now()+5000000000ull);
            if(snapshot(names[i])){result=9;break;}
            append("phase=%s event=end\n",names[i]);
        }
        if(control(0))result=14;
        if(result!=14) {
            char frozen[8192];int n=read_text("/proc/d35_uart_tx",frozen,sizeof(frozen));
            if(n<0){append("frozen_read_errno=%d\n",errno);result=9;}
            else {append("phase=frozen\n%s",frozen);if(!strstr(frozen,"attached=0 "))result=13;}
        }
        int r=(int)syscall(SYS_delete_module,"d35_uart_tx",O_NONBLOCK);
        append("unload_result=%d unload_errno=%d\n",r,r<0?errno:0);
        if(r<0)result=10;
        else if(!access("/proc/d35_uart_tx",F_OK) || !access("/sys/module/d35_uart_tx",F_OK) || !access("/proc/d35_uart_tx_off",F_OK) || !access("/proc/d35_uart_tx_on",F_OK))result=11;
        else loaded=0;
    }
    irq_sample("before_final_baseline");pause_until(now()+1000000000u);irq_sample("after_final_baseline");
    append("phase=complete result=%d cancelled=%d module_remains=%d\n",result,(int)cancelled,loaded);
    if(flush(out))result=12;
    close(out);return result;
}
