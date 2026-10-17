/* Cold replay only: no changed emulated calls/inputs and no native audio. */
#include "ui.h"
#include "fivegame-replay-progress.h"
struct d35_replay_progress *d35_replay_shared;
static void warm_video(const void *p,unsigned w,unsigned h,size_t pitch){(void)p;(void)w;(void)h;(void)pitch;}
static size_t warm_audio(const int16_t *p,size_t n){(void)p;return n;}
static void warm_sample(int16_t l,int16_t r){(void)l;(void)r;}
static int warm_record(const char *dir,unsigned count,uint64_t began,uint64_t cpu,const char *status){
    char path[1300],data[1024];
    int n=snprintf(data,sizeof(data),"cold_boot_calls=%u\nexpected_calls=8656\nwall_ns=%llu\nthread_CPU_ns=%llu\nstatus=%s\naudio_discarded_before_native_open=1\nphysical_display_warmup=1\nmeasured_metrics_reset_before_audio=1\n",
        count,(unsigned long long)(board_now_ns()-began),(unsigned long long)(thread_cpu_ns()-cpu),status);
    if(n<=0 || (size_t)n>=sizeof(data) || snprintf(path,sizeof(path),"%s/warmup.txt",dir)>=(int)sizeof(path))return 0;
    return save_file(path,data,(size_t)n);
}
static int warm_notice(uint16_t *pixels,unsigned count){
    char message[100];
    snprintf(message,sizeof(message),"Preparing gameplay: %u / 8656",count);
    ui_draw_notice(pixels,UI_WIDTH,"STAR FOX - COLD REPLAY",message);
    /* The board copies into owned chunk slots; drain before freeing/resetting. */
    return board_video_submit(pixels,UI_WIDTH,UI_HEIGHT,UI_WIDTH*2u)>=0;
}
static int game_warmup(const char *dir){
    const char *name=getenv("D35_GAME_WARMUP"),*result="invalid_input";
    unsigned count=0;char line[128];FILE *f=NULL;uint16_t *pixels=NULL;
    uint64_t began=board_now_ns(),cpu=thread_cpu_ns(),next=began;
    int ok=0;
    if(!name)goto done;
    f=fopen(name,"r");if(!f){result="input_open_failed";goto done;}
    if(!board_is_null()){
        pixels=calloc(UI_WIDTH*UI_HEIGHT,sizeof(*pixels));
        if(!pixels){result="notice_allocation_failed";goto done;}
    }
    if(d35_replay_shared){d35_replay_shared->calls=0;__sync_synchronize();d35_replay_shared->active=1;}
    p_retro_set_video_refresh(warm_video);p_retro_set_audio_sample_batch(warm_audio);p_retro_set_audio_sample(warm_sample);
    if(!warm_record(dir,0,began,cpu,"running")){result="progress_write_failed";goto done;}
    if(pixels&&!warm_notice(pixels,0)){result="display_failed";goto done;}
    next=board_now_ns()+2000000000ull;
    while(fgets(line,sizeof(line),f)){
        char *a=strtok(line," \r\n"),*b=strtok(NULL," \r\n");
        unsigned n=ability_number(a,10),bits=ability_number(b,16);
        if(!n||bits>65535||count>8656||n>8656-count)goto done;
        s.buttons=bits;
        for(unsigned i=0;i<n;i++){
            if(!(count%64)){
                if(stop_requested){setenv("D35_PAIR_ABORT","1",1);result="abort_signal";goto done;}
                if(board_poll_input()&BOARD_MENU){setenv("D35_PAIR_ABORT","1",1);result="abort_menu";goto done;}
                if(board_now_ns()>=next){
                    if(!warm_record(dir,count,began,cpu,"running")){result="progress_write_failed";goto done;}
                    if(pixels&&!warm_notice(pixels,count)){result="display_failed";goto done;}
                    next=board_now_ns()+2000000000ull;
                }
            }
            p_retro_run();count++;
            if(d35_replay_shared)d35_replay_shared->calls=count;
        }
    }
    if(ferror(f)){result="input_read_failed";goto done;}
    if(count==8656){result="completed";ok=1;}
done:
    if(f)fclose(f);
    p_retro_set_video_refresh(video);p_retro_set_audio_sample_batch(audio_batch);p_retro_set_audio_sample(audio_sample);s.buttons=0;
    board_wait_display();free(pixels);
    /* Warmup UI must never contaminate measured render/submit/worker totals. */
    board_video_metrics(NULL,1);
    if(!warm_record(dir,count,began,cpu,result))ok=0;
    if(d35_replay_shared){__sync_synchronize();d35_replay_shared->active=0;}
    return ok;
}
static void game_final_state(const char *dir){if(!s.loaded||s.failed)return;size_t n=p_retro_serialize_size();void *data=calloc(1,n);if(!data)return;if(p_retro_serialize(data,n)){char path[1300];snprintf(path,sizeof(path),"%s/end-state.bin",dir);(void)save_file(path,data,n);}free(data);}
