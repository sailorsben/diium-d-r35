/* Measurement only: sample the current main thread without changing core code. */
#ifndef D35_MAIN_PC_SAMPLER_H
#define D35_MAIN_PC_SAMPLER_H
#include <dlfcn.h>
#include <elf.h>
#include <errno.h>
#include <link.h>
#include <pthread.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/syscall.h>
#include <time.h>
#include <ucontext.h>
#include <unistd.h>
enum { PC_SAMPLE_CAP=32768 };
struct pc_sample_row {uint32_t frame,offset;};
static struct {
 timer_t timer;int signal,started,error,created,handler_installed,mask_saved;
 uintptr_t base,entry,lo[4],hi[4];unsigned ranges;
 struct sigaction old_action;sigset_t old_mask;
 volatile sig_atomic_t frame,active,count,dropped,outside,idle;
 volatile sig_atomic_t overruns,max_overrun;
 uint64_t began_cpu_ns,ended_cpu_ns;
 struct pc_sample_row rows[PC_SAMPLE_CAP];
} pc_sample;
static int pc_ranges(struct dl_phdr_info *i,size_t n,void *p){
 (void)n;(void)p;unsigned owns=0;
 for(unsigned j=0;j<i->dlpi_phnum;j++)if(i->dlpi_phdr[j].p_type==PT_LOAD&&(i->dlpi_phdr[j].p_flags&PF_X)){
  uintptr_t lo=i->dlpi_addr+i->dlpi_phdr[j].p_vaddr,hi=lo+i->dlpi_phdr[j].p_memsz;
  if(pc_sample.entry>=lo&&pc_sample.entry<hi)owns=1;
 }
 if(!owns)return 0;pc_sample.base=(uintptr_t)i->dlpi_addr;
 for(unsigned j=0;j<i->dlpi_phnum;j++)if(i->dlpi_phdr[j].p_type==PT_LOAD&&(i->dlpi_phdr[j].p_flags&PF_X)){
  if(pc_sample.ranges==4)return 1;
  unsigned k=pc_sample.ranges++;pc_sample.lo[k]=pc_sample.base+i->dlpi_phdr[j].p_vaddr;pc_sample.hi[k]=pc_sample.lo[k]+i->dlpi_phdr[j].p_memsz;
 }return 1;
}
static void pc_signal(int sig,siginfo_t *info,void *context){
 (void)sig;
 if(info->si_code==SI_TIMER&&info->si_overrun>0){pc_sample.overruns+=info->si_overrun;if(info->si_overrun>pc_sample.max_overrun)pc_sample.max_overrun=info->si_overrun;}
 if(!pc_sample.active){pc_sample.idle++;return;}
 const ucontext_t *u=(const ucontext_t *)context;
#if defined(__arm__)
 uintptr_t pc=(uintptr_t)u->uc_mcontext.arm_pc;
#elif defined(__x86_64__)
 uintptr_t pc=(uintptr_t)u->uc_mcontext.gregs[REG_RIP];
#else
#error Unsupported PC sampler architecture
#endif
 uint32_t offset=UINT32_MAX;
 for(unsigned k=0;k<pc_sample.ranges;k++)if(pc>=pc_sample.lo[k]&&pc<pc_sample.hi[k]){offset=(uint32_t)(pc-pc_sample.base);break;}
 if(offset==UINT32_MAX)pc_sample.outside++;
 sig_atomic_t row=pc_sample.count;if(row==PC_SAMPLE_CAP){pc_sample.dropped++;return;}
 pc_sample.rows[row]=(struct pc_sample_row){(uint32_t)pc_sample.frame,offset};pc_sample.count=row+1;
}
/* Disarm, block and drain pending timer signals before restoring the handler.
 * The selected signal is never changed on another thread. */
static void pc_stop_timer(void){
 if(!pc_sample.handler_installed)return;
 sigset_t set;sigemptyset(&set);sigaddset(&set,pc_sample.signal);pthread_sigmask(SIG_BLOCK,&set,NULL);
 if(pc_sample.created){struct itimerspec zero;memset(&zero,0,sizeof(zero));timer_settime(pc_sample.timer,0,&zero,NULL);timer_delete(pc_sample.timer);pc_sample.created=0;}
 pc_sample.active=0;struct timespec zero={0,0};while(sigtimedwait(&set,NULL,&zero)>=0){}
 struct timespec now;if(!syscall(SYS_clock_gettime,CLOCK_THREAD_CPUTIME_ID,&now))pc_sample.ended_cpu_ns=(uint64_t)now.tv_sec*1000000000u+now.tv_nsec;
 sigaction(pc_sample.signal,&pc_sample.old_action,NULL);pc_sample.handler_installed=0;
 if(pc_sample.mask_saved)pthread_sigmask(SIG_SETMASK,&pc_sample.old_mask,NULL);
 pc_sample.started=0;
}
static int pc_start_timer(void *entry){
 memset(&pc_sample,0,sizeof(pc_sample));pc_sample.signal=SIGRTMIN+5;
 pc_sample.entry=(uintptr_t)entry;
 dl_iterate_phdr(pc_ranges,NULL);if(!pc_sample.ranges){pc_sample.error=ENOEXEC;return -1;}
 if(sigaction(pc_sample.signal,NULL,&pc_sample.old_action)){pc_sample.error=errno;return -1;}
 if(pc_sample.old_action.sa_handler!=SIG_DFL){pc_sample.error=EBUSY;return -1;}
 struct sigaction action;memset(&action,0,sizeof(action));action.sa_sigaction=pc_signal;action.sa_flags=SA_SIGINFO|SA_RESTART;sigemptyset(&action.sa_mask);
 if(sigaction(pc_sample.signal,&action,NULL)){pc_sample.error=errno;return -1;}pc_sample.handler_installed=1;
 sigset_t set;sigemptyset(&set);sigaddset(&set,pc_sample.signal);
 int rc=pthread_sigmask(SIG_UNBLOCK,&set,&pc_sample.old_mask);if(rc){pc_sample.error=rc;pc_stop_timer();return -1;}pc_sample.mask_saved=1;
 struct sigevent event;memset(&event,0,sizeof(event));event.sigev_notify=SIGEV_THREAD_ID;event.sigev_signo=pc_sample.signal;event._sigev_un._tid=(pid_t)syscall(SYS_gettid);
 if(timer_create(CLOCK_THREAD_CPUTIME_ID,&event,&pc_sample.timer)){pc_sample.error=errno;pc_stop_timer();return -1;}pc_sample.created=1;
 struct itimerspec period;memset(&period,0,sizeof(period));period.it_value.tv_nsec=period.it_interval.tv_nsec=1000000;
 struct timespec now;if(!syscall(SYS_clock_gettime,CLOCK_THREAD_CPUTIME_ID,&now))pc_sample.began_cpu_ns=(uint64_t)now.tv_sec*1000000000u+now.tv_nsec;
 if(timer_settime(pc_sample.timer,0,&period,NULL)){pc_sample.error=errno;pc_stop_timer();return -1;}
 pc_sample.started=1;return 0;
}
static void pc_enter_frame(unsigned frame){pc_sample.frame=(sig_atomic_t)frame;pc_sample.active=pc_sample.started;}
static void pc_leave_frame(void){pc_sample.active=0;}
static int pc_flush(const char *directory){
 char path[1400];snprintf(path,sizeof(path),"%s/main-pc.csv",directory);FILE *f=fopen(path,"w");if(!f)return -1;
 fprintf(f,"#clock=CLOCK_THREAD_CPUTIME_ID\n#timer_interval_requested_ns=1000000\n#error=%d\n#samples=%d\n#dropped=%d\n#outside_core=%d\n#idle=%d\n#timer_overruns=%d\n#max_overrun=%d\n#observed_thread_CPU_ns=%llu\nframe,ELF_offset\n",pc_sample.error,(int)pc_sample.count,(int)pc_sample.dropped,(int)pc_sample.outside,(int)pc_sample.idle,(int)pc_sample.overruns,(int)pc_sample.max_overrun,(unsigned long long)(pc_sample.ended_cpu_ns-pc_sample.began_cpu_ns));
 for(sig_atomic_t i=0;i<pc_sample.count;i++)fprintf(f,"%u,%08x\n",pc_sample.rows[i].frame,pc_sample.rows[i].offset);
 fflush(f);int rc=fsync(fileno(f));if(fclose(f))rc=-1;return rc;
}
#endif
