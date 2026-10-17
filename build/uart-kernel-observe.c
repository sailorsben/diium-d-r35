/* Bounded passive proc snapshots, kernel-syscall timing, no device access. */
#define _GNU_SOURCE
#include <sys/syscall.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <time.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#ifndef OBSERVE_NS
#define OBSERVE_NS 5000000000ull
#endif
static uint64_t now(void){struct timespec t;if(syscall(SYS_clock_gettime,CLOCK_MONOTONIC,&t))exit(2);return (uint64_t)t.tv_sec*1000000000ull+t.tv_nsec;}
static int snapshot(const char *root,const char *out,const char *tag){
 const char *paths[]={"/proc/interrupts","/proc/tty/driver/gp serial","/proc/stat","/proc/modules","/proc/version","/proc/cmdline","/proc/sys/kernel/random/boot_id"};
 const char *names[]={"interrupts","serial","stat","modules","version","cmdline","boot-id"};
 char src[1400],dst[1400],buf[32768];int failed=0;
 for(unsigned i=0;i<sizeof(paths)/sizeof(*paths);i++){
  snprintf(src,sizeof(src),"%s%s",root,paths[i]);snprintf(dst,sizeof(dst),"%s/%s-%s.txt",out,tag,names[i]);
  int in=open(src,O_RDONLY|O_CLOEXEC),fd=open(dst,O_WRONLY|O_CREAT|O_EXCL|O_CLOEXEC,0600);if(fd<0){if(in>=0)close(in);return 1;}
  if(in<0){dprintf(fd,"read_error=%d\n",errno);failed=1;}
  else {ssize_t n;size_t total=0;while((n=read(in,buf,sizeof(buf)))>0){total+=(size_t)n;if(total>131072){failed=1;break;}if(write(fd,buf,(size_t)n)!=n){failed=1;break;}}if(n<0)failed=1;close(in);}
  if(fsync(fd))failed=1;if(close(fd))failed=1;
 }
 snprintf(dst,sizeof(dst),"%s/%s-presence.txt",out,tag);int fd=open(dst,O_WRONLY|O_CREAT|O_EXCL|O_CLOEXEC,0600);if(fd<0)return 1;
 snprintf(src,sizeof(src),"%s/proc/d35_uart_tx",root);dprintf(fd,"runtime_UART_proc_present=%d\n",access(src,F_OK)==0);
 snprintf(src,sizeof(src),"%s/sys/module/d35_uart_tx",root);dprintf(fd,"runtime_UART_module_present=%d\n",access(src,F_OK)==0);
 if(fsync(fd))failed=1;if(close(fd))failed=1;return failed;
}
int main(int argc,char **argv){
 if(argc!=3||strlen(argv[1])>1000||strlen(argv[2])>1000)return 2;
 const char *root=!strcmp(argv[1],"/")?"":argv[1];if(mkdir(argv[2],0700))return 2;
 uint64_t a=now();int failed=snapshot(root,argv[2],"before");uint64_t b=now(),end=b+OBSERVE_NS;
 while(now()<end){uint64_t left=end-now();if(left>OBSERVE_NS)continue;struct timespec t={(time_t)(left/1000000000ull),(long)(left%1000000000ull)};if(nanosleep(&t,NULL)&&errno!=EINTR)return 2;}
 uint64_t c=now();failed|=snapshot(root,argv[2],"after");uint64_t d=now();char path[1400];snprintf(path,sizeof(path),"%s/timing.txt",argv[2]);FILE *f=fopen(path,"wx");if(!f)return 2;
 fprintf(f,"begin_snapshot_start_ns=%llu\nbegin_snapshot_end_ns=%llu\nend_snapshot_start_ns=%llu\nend_snapshot_end_ns=%llu\nrelative_wait_ns=%llu\nfailed=%d\nflash_writes=0\nUART_configuration_writes=0\n",(unsigned long long)a,(unsigned long long)b,(unsigned long long)c,(unsigned long long)d,(unsigned long long)OBSERVE_NS,failed);
 if(fflush(f)||fsync(fileno(f))||fclose(f))return 2;int dir=open(argv[2],O_RDONLY|O_DIRECTORY);if(dir<0)return 2;int r=fsync(dir);close(dir);return failed||r?1:0;
}
