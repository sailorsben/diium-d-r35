#define _GNU_SOURCE
#include "main-pc-sampler.h"
#include <assert.h>
#include <stdlib.h>
static volatile unsigned busy_value;
static __attribute__((noinline)) void busy(void){for(unsigned j=0;j<24000000;j++)busy_value=busy_value*1664525u+1013904223u;}
int main(int argc,char **argv){
 assert(argc==2);
 if(pc_start_timer((void *)busy)){printf("UNAVAILABLE: thread CPU timer errno=%d\n",pc_sample.error);return 77;}
 for(unsigned frame=0;frame<4;frame++){pc_enter_frame(frame);busy();pc_leave_frame();}
 pc_stop_timer();printf("captured=%d dropped=%d outside=%d\n",(int)pc_sample.count,(int)pc_sample.dropped,(int)pc_sample.outside);assert(pc_sample.count>5&&pc_sample.dropped==0);
 for(int j=0;j<pc_sample.count;j++)assert(pc_sample.rows[j].frame<4);
 assert(pc_flush(argv[1])==0);
 /* Prove no pending timer can hit the restored default handler. */
 busy();assert(pc_start_timer((void *)busy)==0);pc_enter_frame(0);busy();pc_leave_frame();pc_stop_timer();busy();
 printf("PASS: PC capture, bounded records, frame ownership, disarm/drain and restart; no A7 timing claim\n");return 0;
}
