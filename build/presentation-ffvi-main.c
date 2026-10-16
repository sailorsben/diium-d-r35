/* Matched real-core measurement, owned child supervisor and bounded replay. */
#define _GNU_SOURCE
#include "runner/board.h"
#include "runner/runner.h"
#include "runner/startup.h"
#include "identity.h"
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
static volatile sig_atomic_t stopped;
int main(int argc,char **argv);
static void stop(int sig){(void)sig;stopped=1;runner_request_stop();}
static uint64_t now(void){struct timespec t;if(syscall(SYS_clock_gettime,CLOCK_MONOTONIC,&t))return 0;return (uint64_t)t.tv_sec*1000000000u+t.tv_nsec;}
static void relative_wait(void){struct timespec t={0,100000000};while(syscall(SYS_nanosleep,&t,&t)<0&&errno==EINTR){} }
static void durable(FILE *f){if(fflush(f)||fsync(fileno(f))||fclose(f))_exit(72);}
static int supervise(char **argv){
 pid_t child=fork();int status=0,reaped=0,forced=0;uint64_t deadline=now()+2100000000000ull;
 if(child<0)return 72;
 if(!child){argv[1]="--run";exit(main(5,argv));}
 for(;;){pid_t r=waitpid(child,&status,WNOHANG);if(r==child){reaped=1;break;}if(r<0&&errno!=EINTR)break;
  if(stopped||!now()||now()>=deadline){kill(child,SIGTERM);forced=1;break;}relative_wait();}
 if(forced){uint64_t until=now()+3000000000ull;do{if(waitpid(child,&status,WNOHANG)==child){reaped=1;break;}relative_wait();}while(now()<until);
  if(!reaped){kill(child,SIGKILL);until=now()+3000000000ull;do{if(waitpid(child,&status,WNOHANG)==child){reaped=1;break;}relative_wait();}while(now()<until);}}
 char path[1400];snprintf(path,sizeof(path),"%s/supervisor.txt",argv[2]);FILE *f=fopen(path,"w");
 if(!f)return 72;fprintf(f,"child=%ld\nreaped=%d\nforced=%d\nraw_status=%d\n",(long)child,reaped,forced,status);durable(f);
 if(!reaped||forced||!WIFEXITED(status))return 72;
 int rc=WEXITSTATUS(status);return rc==0||rc==1||rc==5?rc:72;
}
int main(int argc,char **argv){
 if(argc!=5)return 2;signal(SIGINT,stop);signal(SIGTERM,stop);
 if(!strcmp(argv[1],"--supervise"))return supervise(argv);
 if(strcmp(argv[1],"--run"))return 2;
 char dir[1200],state[1200],input[1200],expected[1200],core[1200],path[1400],policy[8],load[16];
 unsigned count=0,failed=0,limit=sizeof(ffvi_runs)/sizeof(ffvi_runs[0]);
 const char *bound=getenv("D35_FFVI_RUN_LIMIT");if(bound){unsigned n=0;while(*bound){if(*bound<'0'||*bound>'9'||n>limit)return 2;n=n*10u+(unsigned)(*bound++-'0');}if(!n||n>limit)return 2;limit=n;}
 startup_begin();if(board_open(getenv("D35_ABILITY_MOCK")!=NULL)<0){startup_end();return 72;}startup_ready();
 for(unsigned seq=0;seq<limit&&!stopped;seq++){
  if(board_poll_input()&BOARD_MENU){stopped=1;break;}
  const struct ffvi_run *r=&ffvi_runs[seq];
  snprintf(dir,sizeof(dir),"%s/run-%03u",argv[2],seq);
  snprintf(core,sizeof(core),"%s/plus-a7.so",argv[3]);
  snprintf(state,sizeof(state),"%s/cases/%03u/scene.state",argv[3],r->fixture);
  snprintf(input,sizeof(input),"%s/cases/%03u/input.txt",argv[3],r->fixture);
  snprintf(expected,sizeof(expected),"%s/cases/%03u/expected.bin",argv[3],r->fixture);
  if(mkdir(dir,0700)){failed++;break;}
  snprintf(path,sizeof(path),"%s/begin.txt",dir);FILE *f=fopen(path,"w");if(!f){failed++;break;}
  fprintf(f,"suite=presentation-ffvi1\nrun=%u\nfixture=%u\nspell=%s\nrepeat=%u\npolicy=%u\nload_ms=%u\ncalls=1200\n",seq,r->fixture,spell_names[r->fixture],r->repeat,r->policy,r->load_ms);durable(f);
  snprintf(policy,sizeof(policy),"%u",r->policy);snprintf(load,sizeof(load),"%u",r->load_ms);
  setenv("D35_PRESENTATION_POLICY",policy,1);setenv("D35_PRESENTATION_LOAD_MS",load,1);
  setenv("D35_PAIR_STATE",state,1);setenv("D35_PAIR_START","0",1);setenv("D35_PAIR_LIMIT","1200",1);
  setenv("D35_ABILITY_INPUT",input,1);setenv("D35_ABILITY_EXPECTED",expected,1);setenv("D35_FULL_VARIANT",policy,1);
  int rc=runner_run(argv[4],core,dir);if(rc)failed++;
  snprintf(path,sizeof(path),"%s/result.txt",dir);f=fopen(path,"w");if(!f){failed++;break;}
  fprintf(f,"runner_rc=%d\nerror=%s\naudio_worker_joined=1\ndisplay_idle=1\n",rc,runner_last_error());durable(f);
  count++;sync();if(getenv("D35_PAIR_ABORT"))stopped=1;
 }
 board_close();startup_end();snprintf(path,sizeof(path),"%s/suite-result.txt",argv[2]);FILE *f=fopen(path,"w");if(!f)return 72;
 fprintf(f,"suite=presentation-ffvi1\nruns=%u\nplanned=%u\nfailures=%u\nstopped=%d\nboard_closed=1\n",count,limit,failed,(int)stopped);durable(f);
 return stopped?5:failed?1:0;
}
