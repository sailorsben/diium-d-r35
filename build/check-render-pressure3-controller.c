/* Actual controller + frozen threaded audio owner; deterministic fake device.
 * Qualifies ownership/error propagation and executed bursts, never performance. */
#define main pressure_controller_main
#ifndef PRESSURE_CONTROLLER
#define PRESSURE_CONTROLLER "render-pressure3.c"
#endif
#include PRESSURE_CONTROLLER
#undef main
#include <assert.h>
static unsigned finishes,closes,inject_finish_error;
static unsigned busy_credit,try_calls,blocking_calls;
static uint64_t accepted;
static uint16_t pixels[RP_MAX];
static struct board_video_metrics vm;
int board_open(int null_backend){(void)null_backend;return 0;}
void board_close(void){}
int board_is_null(void){return 0;}
const char *board_last_error(void){return "";}
int board_video_reserve(void){blocking_calls++;return 0;}
int board_video_try_reserve(void){try_calls++;return busy_credit?0:1;}
void *board_video_target(size_t *bytes){*bytes=sizeof(pixels);return pixels;}
void board_video_cancel(void){}
int board_video_submit(const void *p,unsigned w,unsigned h,size_t pitch){
 (void)pitch;vm.submitted++;vm.scaled++;vm.flipped++;
 if(p==pixels)vm.direct_submitted++;else vm.copied_payload_bytes+=(uint64_t)w*h*2;
 return 0;
}
void board_video_metrics(struct board_video_metrics *out,int reset){if(out)*out=vm;if(reset)memset(&vm,0,sizeof(vm));}
void board_wait_display(void){}
uint32_t board_poll_input(void){return 0;}
int board_audio_open(unsigned rate){(void)rate;accepted=0;finishes=0;return 44100;}
ssize_t board_audio_write(const int16_t *pcm,size_t n){(void)pcm;accepted+=n;return (ssize_t)n;}
int board_audio_observe(struct board_audio_state *d){
 memset(d,0,sizeof(*d));d->rate=44100;d->period=128;d->buffer=3712;d->prime=2823;
 d->queued=accepted<2823?(unsigned)accepted:2823;d->avail=d->buffer-d->queued;
 d->started=accepted>=2823;d->state=d->started?3:2;d->boundary=1946157056;
 d->appl_ptr=(unsigned)accepted;d->hw_ptr=(unsigned)accepted-d->queued;
 d->epoch_transferred=accepted;d->epoch=1;d->observed_ns=now();return 0;
}
int board_audio_avail_min(unsigned n){(void)n;return 0;}
int board_audio_fd(void){return -1;}
int board_audio_finish(void){
 finishes++;if(inject_finish_error||finishes>1){errno=77;return -1;}return 0;
}
void board_audio_close(void){closes++;}
const char *board_audio_error(void){return "owned finish fixture";}
uint64_t board_now_ns(void){return now();}
void board_sleep_until(uint64_t deadline){while(now()<deadline){struct timespec t={0,1000000};syscall(SYS_nanosleep,&t,NULL);}}
void pcm_cost_flush(const char *dir){(void)dir;}
void startup_begin(void){}
void startup_ready(void){}
void startup_end(void){}
static int run_cell(unsigned kind,int load,unsigned count,int fault){
 inject_finish_error=(unsigned)fault;unsigned before=closes;
 int result=phase(0,2,kind,kind==5,0,1,load,1,count);
 if(finishes!=1 || closes!=before+1 || result!=(fault?-1:0))return 1;
 return 0;
}
int main(int argc,char **argv){
 if(argc!=2)return 2;output=argv[1];overall_deadline=now()+60000000000ull;
 GFX.ZERO=calloc(65536,2);if(!GFX.ZERO)return 3;rp_zero_table();
 if(run_cell(6,0,5,0))return 10;
 if(run_cell(5,0,5,0))return 11;
 if(run_cell(6,0,5,1))return 12;
 if(run_cell(5,-24,60,0))return 13;
 if(run_cell(5,-48,60,0))return 14;
 if(run_cell(5,-80,60,0))return 15;
 busy_credit=1;unsigned calls=blocking_calls;
 if(run_cell(5,0,5,0)||blocking_calls!=calls||!try_calls)return 16;
 busy_credit=0;presentation_policy=0;calls=blocking_calls;
 if(run_cell(5,0,5,0)||blocking_calls!=calls+5)return 17;
 puts("PASS actual controller / frozen threaded audio owner: single finish, finish failure propagation, close/join, six executed bursts");
 free(GFX.ZERO);return 0;
}
