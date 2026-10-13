/* Measurement-only, full-frame matched variant crossover. Private fixtures. */
#define _GNU_SOURCE
#include "snes-mvp/board.h"
#include "snes-mvp/runner.h"
#include "snes-mvp/startup.h"
#include "fullpaths-identity.h"
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <sys/stat.h>
#include <unistd.h>
static volatile sig_atomic_t stopped;
static void stop(int sig){(void)sig;stopped=1;runner_request_stop();}
int main(int argc,char **argv){
 if(argc!=3)return 2;
 char dir[1200],core[1200],state[1200],input[1200],expected[1200],path[1300];
 unsigned count=0;int failed=0;unsigned limit=D35_FULL_RUNS;
 const char *bound=getenv("D35_FULL_RUN_LIMIT");
 if(bound){unsigned n=0;while(*bound){if(*bound<'0'||*bound>'9'||n>limit)return 2;n=n*10u+(unsigned)(*bound++-'0');}if(!n||n>limit)return 2;limit=n;}
 signal(SIGINT,stop);signal(SIGTERM,stop);startup_begin();
 if(board_open(getenv("D35_ABILITY_MOCK")!=NULL)<0){startup_end();return 1;}startup_ready();
 for(unsigned seq=0;seq<limit&&!stopped;seq++){
  if(board_poll_input()&BOARD_MENU){stopped=1;break;}
  const struct full_run *r=&full_runs[seq];
  snprintf(dir,sizeof(dir),"%s/run-%03u",argv[1],seq);
  snprintf(core,sizeof(core),"%s/cores/%s.so",argv[1],full_variants[r->variant]);
  snprintf(state,sizeof(state),"%s/cases/%03u/%s.state",argv[1],r->fixture,full_variants[r->variant]);
  snprintf(input,sizeof(input),"%s/cases/%03u/input.txt",argv[1],r->fixture);
  snprintf(expected,sizeof(expected),"%s/cases/%03u/expected.bin",argv[1],r->fixture);
  if(mkdir(dir,0700)){failed++;break;}
  snprintf(path,sizeof(path),"%s/begin.txt",dir);FILE *begin=fopen(path,"w");
  if(!begin){failed++;break;}
  fprintf(begin,"suite=1.19-fullpaths1\nrun=%u\nfixture=%u\nvariant=%s\nrepeat=%u\nphase=before_audio_display_workers\n",seq,r->fixture,full_variants[r->variant],r->repeat);
  fflush(begin);fsync(fileno(begin));fclose(begin);
  setenv("D35_PAIR_STATE",state,1);setenv("D35_PAIR_START","0",1);setenv("D35_PAIR_LIMIT","1200",1);
  setenv("D35_ABILITY_INPUT",input,1);setenv("D35_ABILITY_EXPECTED",expected,1);
  setenv("D35_FULL_VARIANT",full_variants[r->variant],1);
  fprintf(stderr,"fullpaths run=%u/%u fixture=%u variant=%s repeat=%u\n",seq,limit,r->fixture,full_variants[r->variant],r->repeat);
  int rc=runner_run(argv[2],core,dir);if(rc)failed++;
  snprintf(path,sizeof(path),"%s/result.txt",dir);FILE *f=fopen(path,"w");
  if(f){fprintf(f,"run=%u\nfixture=%u\nvariant=%s\nrepeat=%u\nrunner_rc=%d\nerror=%s\naudio_worker_joined=1\ndisplay_idle=1\n",seq,r->fixture,full_variants[r->variant],r->repeat,rc,runner_last_error());fflush(f);fsync(fileno(f));fclose(f);}
  count++;sync();if(getenv("D35_PAIR_ABORT"))stopped=1;
 }
 snprintf(path,sizeof(path),"%s/suite-result.txt",argv[1]);FILE *f=fopen(path,"w");
 if(f){fprintf(f,"suite=1.19-fullpaths1\nruns=%u\nplanned=%u\nfailures=%d\nstopped=%d\nframeskip=0\n",count,limit,failed,(int)stopped);fflush(f);fsync(fileno(f));fclose(f);}
 fprintf(stderr,"fullpaths end runs=%u failures=%d stopped=%d\n",count,failed,(int)stopped);
 board_close();startup_end();return failed?1:0;
}
