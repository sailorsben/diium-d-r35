/* Independent accounting fixtures: pacing, worker overlap, faults and mocks. */
#define _GNU_SOURCE
#include "snes-mvp/board.h"
#include "snes-mvp/audio-pipe.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
struct pair_row { unsigned frame,pointer_valid;uint64_t pace_wait,main_step_cpu,identity_observer,cpu,wall,admission,observer,step,generated;long before_khz,after_khz;struct audio_pipe_stats audio;struct board_video_metrics video; };
static struct pair_row pair_rows[1200];static unsigned pair_count=1200;
static unsigned submissions=1200;
static uint64_t final_video_cpu=960050000;
static struct audio_pipe_stats final_audio={.worker_cpu_ns=240050000,.enqueued=100,.accepted=100};
void board_video_metrics(struct board_video_metrics *out,int reset){(void)reset;memset(out,0,sizeof(*out));out->submitted=out->flipped=submissions;out->worker_cpu_ns=final_video_cpu;}
void audio_pipe_stats(struct audio_pipe_stats *out){*out=final_audio;}
#include "combined-headroom.h"
static void check(const char *root,const char *name,int mock,int failed,const char *expect){
 char dir[800],path[1400],text[6000];snprintf(dir,sizeof(dir),"%s/%s",root,name);assert(!mkdir(dir,0700));
 full_headroom(dir,mock,failed);snprintf(path,sizeof(path),"%s/headroom.txt",dir);FILE *f=fopen(path,"r");assert(f);size_t n=fread(text,1,sizeof(text)-1,f);text[n]=0;fclose(f);assert(strstr(text,expect));
 if(!strcmp(name,"pure-pacing"))assert(strstr(text,"service_mean_ns=9000000\n"));
}
int main(int argc,char **argv){
 assert(argc==2);assert(!mkdir(argv[1],0700));
 for(unsigned i=0;i<1200;i++){pair_rows[i].pointer_valid=1;pair_rows[i].step=16000000;pair_rows[i].pace_wait=8000000;pair_rows[i].audio.worker_cpu_ns=(i+1)*200000ull;pair_rows[i].video.worker_cpu_ns=(i+1)*800000ull;pair_rows[i].cpu=7000000;}
 check(argv[1],"pure-pacing",0,0,"sampled_warm_20_percent_headroom=MET_IN_THIS_WARM_SAMPLE");
 check(argv[1],"mock",1,0,"sampled_warm_20_percent_headroom=NOT_PHYSICAL");
 pair_rows[250].pointer_valid=0;check(argv[1],"pointer-drift",0,0,"sampled_warm_20_percent_headroom=INVALID_OR_INCOMPLETE");pair_rows[250].pointer_valid=1;
 submissions=1199;check(argv[1],"missing-frame",0,0,"sampled_warm_20_percent_headroom=INVALID_OR_INCOMPLETE");submissions=1200;
 pair_rows[250].pace_wait=17000000;check(argv[1],"invalid-wait",0,0,"sampled_warm_20_percent_headroom=INVALID_OR_INCOMPLETE");pair_rows[250].pace_wait=8000000;
 pair_rows[250].audio.worker_cpu_ns=1;check(argv[1],"worker-clock-regression",0,0,"sampled_warm_20_percent_headroom=INVALID_OR_INCOMPLETE");pair_rows[250].audio.worker_cpu_ns=251*200000ull;
 pair_rows[250].step=24000000;check(argv[1],"tail-overrun",0,0,"sampled_warm_20_percent_headroom=NOT_MET");pair_rows[250].step=16000000;
 check(argv[1],"fatal",0,1,"sampled_warm_20_percent_headroom=INVALID_OR_INCOMPLETE");
 pair_count=1199;check(argv[1],"short-run",0,0,"sampled_warm_20_percent_headroom=INVALID_OR_INCOMPLETE");
 pair_count=1200;
 final_audio.worker_cpu_ns=1;check(argv[1],"final-worker-regression",0,0,"sampled_warm_20_percent_headroom=INVALID_OR_INCOMPLETE");final_audio.worker_cpu_ns=240050000;
 final_audio.remaining=1;final_audio.accepted=99;check(argv[1],"undrained",0,0,"sampled_warm_20_percent_headroom=INVALID_OR_INCOMPLETE");final_audio.remaining=0;final_audio.accepted=100;
 final_audio.enqueued=101;check(argv[1],"final-PCM-mismatch",0,0,"sampled_warm_20_percent_headroom=INVALID_OR_INCOMPLETE");final_audio.enqueued=100;
 final_audio.cleared=1;final_audio.accepted=99;check(argv[1],"discarded-PCM",0,0,"sampled_warm_20_percent_headroom=INVALID_OR_INCOMPLETE");final_audio.cleared=0;final_audio.accepted=100;
 final_audio.error=5;check(argv[1],"final-audio-error",0,0,"sampled_warm_20_percent_headroom=INVALID_OR_INCOMPLETE");
 puts("PASS:14 independent accounting fixtures; final workers, draining, PCM equality, discarded data and final-error rejection; included worker cost; pure pacing distinction; mock, pointer drift, missing frame, bad wait/clock, tail overrun, fatal and incomplete rejection");return 0;
}
