/* Execute the actual replay header/UI with independent core/board fixtures. */
#define _GNU_SOURCE
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "fivegame-kernel-private-v2/runner/board.h"
static struct {unsigned buttons;int loaded,failed;} s;
static int stop_requested;
static unsigned calls,submits,waits,resets,records;
static uint64_t clock_ns;
static const char *mode;
static const uint16_t *inflight;
static void video(const void *p,unsigned w,unsigned h,size_t pitch){(void)p;(void)w;(void)h;(void)pitch;}
static size_t audio_batch(const int16_t *p,size_t n){(void)p;return n;}
static void audio_sample(int16_t l,int16_t r){(void)l;(void)r;}
static void (*video_cb)(const void *,unsigned,unsigned,size_t);
static size_t (*audio_cb)(const int16_t *,size_t);
static void (*sample_cb)(int16_t,int16_t);
static void p_retro_set_video_refresh(void (*cb)(const void *,unsigned,unsigned,size_t)){video_cb=cb;}
static void p_retro_set_audio_sample_batch(size_t (*cb)(const int16_t *,size_t)){audio_cb=cb;}
static void p_retro_set_audio_sample(void (*cb)(int16_t,int16_t)){sample_cb=cb;}
static void p_retro_run(void){
    assert(s.buttons==(calls<7?2u:8u));calls++;clock_ns+=5000000;
    video_cb(NULL,256,224,512);assert(audio_cb(NULL,17)==17);sample_cb(1,2);
    if(!strcmp(mode,"signal")&&calls==64)stop_requested=1;
}
static size_t p_retro_serialize_size(void){return 0;}
static int p_retro_serialize(void *p,size_t n){(void)p;(void)n;return 0;}
uint64_t board_now_ns(void){return clock_ns;}
static uint64_t thread_cpu_ns(void){return clock_ns;}
int board_is_null(void){return 0;}
uint32_t board_poll_input(void){return !strcmp(mode,"menu")&&calls>=64?BOARD_MENU:0;}
int board_video_submit(const void *p,unsigned w,unsigned h,size_t pitch){
    assert(w==640&&h==480&&pitch==1280);inflight=p;submits++;
    const char *dump=getenv("D35_WARMUP_SCREEN");
    if(dump&&submits==1){FILE *f=fopen(dump,"wb");assert(f&&fwrite(p,1,640*480*2,f)==640*480*2&&!fclose(f));}
    return !strcmp(mode,"display")?-1:0;
}
void board_wait_display(void){waits++;inflight=NULL;}
void board_video_metrics(struct board_video_metrics *out,int reset){
    (void)out;assert(reset==1&&!inflight);resets++;
}
static unsigned ability_number(const char *p,unsigned base){
    extern unsigned long legacy_strtoul(const char *,char **,int) __asm__("strtoul");
    if(!p||!*p)return UINT32_MAX;char *end;unsigned long n=legacy_strtoul(p,&end,(int)base);
    return *end||n>UINT32_MAX?UINT32_MAX:(unsigned)n;
}
static int save_file(const char *path,const void *data,size_t n){
    records++;FILE *f=fopen(path,"wb");assert(f);
    int ok=fwrite(data,1,n,f)==n;assert(!fflush(f)&&!fsync(fileno(f))&&!fclose(f));return ok;
}
#include "fivegame-warmup-progress.h"
int main(int argc,char **argv){
    assert(argc==3);mode=argv[1];struct d35_replay_progress shared={0};d35_replay_shared=&shared;
    int ok=game_warmup(argv[2]);
    assert(video_cb==video&&audio_cb==audio_batch&&sample_cb==audio_sample);
    assert(!shared.active&&shared.calls==calls&&s.buttons==0&&waits==1&&resets==1&&!inflight);
    if(!strcmp(mode,"complete")){assert(ok&&calls==8656&&records>2&&submits>1);}
    else if(!strcmp(mode,"menu")||!strcmp(mode,"signal")){assert(!ok&&calls==64&&getenv("D35_PAIR_ABORT"));}
    else {assert(!ok&&calls==0);}
    game_final_state(argv[2]);
    printf("PASS warmup fixture %s calls=%u records=%u notice_updates=%u callbacks_restored=1 display_drained=1 metrics_reset=1 native_audio_opened=0\n",mode,calls,records,submits);
    return 0;
}
