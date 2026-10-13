/* Independent bounded casts, with native audio/display. No fatal suppression. */
#define _GNU_SOURCE
#include "snes-mvp/board.h"
#include "snes-mvp/runner.h"
#include "snes-mvp/startup.h"
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <sys/stat.h>
#include <unistd.h>
static volatile sig_atomic_t stopped;
static void stop(int sig){(void)sig;stopped=1;runner_request_stop();}
static unsigned number(const char *s){unsigned n=0;while(*s){if(*s<'0'||*s>'9'||n>400)return 401;n=n*10u+(unsigned)(*s++-'0');}return n;}
int main(int argc,char **argv){
 if(argc!=3)return 2;char dir[1200],core[1200],state[1200],input[1200],expected[1200];unsigned count=0;int failed=0;
 signal(SIGINT,stop);signal(SIGTERM,stop);startup_begin();if(board_open(getenv("D35_ABILITY_MOCK")!=NULL)<0){startup_end();return 1;}startup_ready();
 const char *start=getenv("D35_ABILITY_FIRST"),*end=getenv("D35_ABILITY_END");unsigned first=start?number(start):0,last=end?number(end):400;
 if(first>=last||last>400){board_close();startup_end();return 2;}
 for(unsigned seq=first;seq<last&&!stopped;seq++){
  if(board_poll_input()&BOARD_MENU){stopped=1;break;}
  snprintf(dir,sizeof(dir),"%s/run-%03u",argv[1],seq);snprintf(core,sizeof(core),"%s/plus-a7.so",argv[1]);snprintf(state,sizeof(state),"%s/cases/%03u/scene.state",argv[1],seq);snprintf(input,sizeof(input),"%s/cases/%03u/input.txt",argv[1],seq);snprintf(expected,sizeof(expected),"%s/cases/%03u/expected.bin",argv[1],seq);
  if(mkdir(dir,0700)){failed++;break;}
  char begin_path[1300];snprintf(begin_path,sizeof(begin_path),"%s/begin.txt",dir);FILE *begin=fopen(begin_path,"w");if(!begin){failed++;break;}fprintf(begin,"case=%u\nphase=before_audio_display_workers\n",seq);fflush(begin);fsync(fileno(begin));fclose(begin);
  setenv("D35_PAIR_STATE",state,1);setenv("D35_PAIR_START","0",1);setenv("D35_PAIR_LIMIT","1200",1);setenv("D35_ABILITY_INPUT",input,1);setenv("D35_ABILITY_EXPECTED",expected,1);
  fprintf(stderr,"ability seq=%u/%u begin independent fixture\n",seq,last);int rc=runner_run(argv[2],core,dir);if(rc)failed++;
  char path[1300];snprintf(path,sizeof(path),"%s/result.txt",dir);FILE *f=fopen(path,"w");if(f){fprintf(f,"case=%u\nrunner_rc=%d\nerror=%s\naudio_worker_joined=1\ndisplay_idle=1\n",seq,rc,runner_last_error());fflush(f);fsync(fileno(f));fclose(f);}
  fprintf(stderr,"ability seq=%u result=%d audio closed/display idle; evidence flushed\n",seq,rc);count++;sync();if(getenv("D35_PAIR_ABORT"))stopped=1;
 }
 fprintf(stderr,"ability suite end cases=%u failures=%d stopped=%d\n",count,failed,(int)stopped);board_close();startup_end();return failed?1:0;
}
