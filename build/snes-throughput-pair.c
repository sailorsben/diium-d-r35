/* Compare two independent libretro instances on the same logical CPU.
 * Alternate call order each frame; retain the same warmup, input and callbacks. */
#define main d35_single_main
#include "snes-throughput-replay.c"
#undef main
#include <sys/syscall.h>
#include <unistd.h>

/* Keep the replay parser on the firmware's legacy libc symbols. */
extern long syscall(long, ...);

static bool device;
static uint64_t callback_cpu;

static uint64_t kernel_time(clockid_t id) {
    struct timespec t;
    assert(!syscall(SYS_clock_gettime,id,&t));
    return (uint64_t)t.tv_sec*1000000000+t.tv_nsec;
}

static void device_video(const void *p,unsigned w,unsigned h,size_t pitch) {
    if(!verify) { video(p,w,h,pitch);return; }
    uint64_t start=kernel_time(CLOCK_THREAD_CPUTIME_ID);
    video(p,w,h,pitch);
    callback_cpu+=kernel_time(CLOCK_THREAD_CPUTIME_ID)-start;
}

static size_t device_audio(const int16_t *p,size_t n) {
    if(!verify) return audio(p,n);
    uint64_t start=kernel_time(CLOCK_THREAD_CPUTIME_ID);
    size_t result=audio(p,n);
    callback_cpu+=kernel_time(CLOCK_THREAD_CPUTIME_ID)-start;
    return result;
}

static void device_sample(int16_t left,int16_t right) {
    const int16_t stereo[]={left,right};
    device_audio(stereo,1);
}

struct instance {
    void *handle;
    void (*run)(void), (*unload)(void), (*deinit)(void);
    unsigned (*acquire)(void *,size_t);
};

static struct instance setup(const char *path, const char *root, unsigned cold, void *rom,size_t rn) {
    struct instance c={0};
    c.handle=dlopen(path,RTLD_NOW|RTLD_LOCAL);
    if(!c.handle) {fputs(dlerror(),stderr);abort();}
#define BIND(name,type) __typeof__(type) *name=dlsym(c.handle,"retro_" #name); assert(name)
    BIND(set_environment,void(retro_environment_t)); BIND(set_video_refresh,void(retro_video_refresh_t));
    BIND(set_audio_sample_batch,void(retro_audio_sample_batch_t)); BIND(set_audio_sample,void(retro_audio_sample_t));
    BIND(set_input_state,void(retro_input_state_t)); BIND(set_input_poll,void(retro_input_poll_t));
    BIND(init,void(void)); BIND(load_game,bool(const struct retro_game_info *));
    BIND(unload_game,void(void)); BIND(deinit,void(void)); BIND(run,void(void));
    BIND(unserialize,bool(const void *,size_t)); BIND(serialize_size,size_t(void));
#undef BIND
    c.run=run;c.unload=unload_game;c.deinit=deinit;
    c.acquire=dlsym(c.handle,"d35_output_acquire");assert(c.acquire);
    set_environment(env);set_video_refresh(device?device_video:video);
    set_audio_sample_batch(device?device_audio:audio);set_audio_sample(device?device_sample:sample);
    set_input_state(input);set_input_poll(poll);init();
    struct retro_game_info g={.data=rom,.size=rn}; assert(load_game(&g));
    if(!cold) {
        size_t sn;unsigned char *state=read_file(root,"scene.state",&sn);
        assert(sn==serialize_size()+40 && !memcmp(state,"D35MVP01",8));
        assert(unserialize(state+40,sn-40));free(state);
    }
    return c;
}

int main(int argc,char **argv) {
    assert(argc==6);
    const char *mode=argv[5];
    bool cold_off=!strcmp(mode,"cold-off"),oracle=!strcmp(mode,"oracle-reuse"),off=!strcmp(mode,"off");
    bool no_target=!strcmp(mode,"no-target"), half=!strcmp(mode,"half");
    bool fx_toggle_device=!strcmp(mode,"both-cold-off-fx-toggle-device");
    bool fx_toggle=fx_toggle_device||!strcmp(mode,"both-cold-off-fx-toggle");
    bool brr_cold=!strcmp(mode,"both-cold-off-brr-toggle");
    bool brr_toggle=brr_cold||!strcmp(mode,"full-brr-toggle");
    bool brr_compare=!strcmp(mode,"both-cold-off-brr-compare")||!strcmp(mode,"full-brr-compare");
    device=fx_toggle_device||!strcmp(mode,"device")||!strcmp(mode,"both-cold-off-device");
    bool both_cold_off=!strcmp(mode,"both-cold-off")||!strcmp(mode,"both-cold-off-toggle")||
                       !strcmp(mode,"both-cold-off-device")||fx_toggle||brr_cold||
                       !strcmp(mode,"both-cold-off-brr-compare");
    bool toggle=!strcmp(mode,"full-toggle")||!strcmp(mode,"both-cold-off-toggle");
    assert(cold_off||oracle||off||no_target||half||both_cold_off||toggle||device||
           brr_toggle||brr_compare||!strcmp(mode,"full"));
    unsigned cold=(unsigned)atoi(argv[4]);assert(cold==0||cold==8656);
    if(device) {
        assert(both_cold_off==!!cold);
        alarm(cold?420:75);
    }
    size_t rn,en;unsigned char *rom=read_file(argv[3],"game.sfc",&rn);
    uint32_t *expected=(uint32_t *)read_file(argv[3],"expected.bin",&en);assert(en==1200*12);
    uint16_t warm[8656],gameplay[1200];
    if(cold)read_inputs(argv[3],"warmup.txt",warm,cold);
    read_inputs(argv[3],"input.txt",gameplay,1200);
    struct instance c[]={setup(argv[1],argv[3],cold,rom,rn),setup(argv[2],argv[3],cold,rom,rn)};
    assert(c[0].handle!=c[1].handle);
    if(toggle||fx_toggle) {
        for(unsigned k=0;k<2;k++) {
            void (*set_enabled)(bool)=dlsym(c[k].handle,fx_toggle?"d35_fx_set_enabled":"d35_raster_set_enabled");
            assert(set_enabled);set_enabled(k==1);
        }
    }
    if(brr_toggle||brr_compare) {
        for(unsigned k=0;k<2;k++) {
            void (*set_raster)(bool)=dlsym(c[k].handle,"d35_raster_set_enabled");
            assert(set_raster);
            set_raster(true);
            if(brr_toggle) {
                void (*set_brr)(bool)=dlsym(c[k].handle,"d35_brr_set_enabled");
                assert(set_brr);
                set_brr(k==1);
            }
        }
    }
    void (*brr_read)(uint64_t *)=dlsym(c[1].handle,"d35_brr_read");
    uint64_t brr_before[6]={0},brr_after[6]={0};
    uint64_t boot[2]={0}, times[1200][2];
    uint64_t wall[1200][2], observer[1200][2];
    uint32_t layout[2]={0};
    unsigned audio_frames[2]={0}, published[2]={0};
    for(unsigned i=0;i<cold;i++) {
        buttons=warm[i];
        for(unsigned j=0;j<2;j++) {
            unsigned k=(j+i)&1;
            enable=(both_cold_off || (k && cold_off))?2:3;
            uint64_t t=device?kernel_time(CLOCK_THREAD_CPUTIME_ID):cpu();
            c[k].run();
            boot[k]+=(device?kernel_time(CLOCK_THREAD_CPUTIME_ID):cpu())-t;
        }
        if(device && (i+1)%1024==0) fprintf(stderr,"cold_calls_per_arm=%u\n",i+1);
    }
    if(brr_read) brr_read(brr_before);
    if(device) { verify=pixels=1;fprintf(stderr,"cold_calls_per_arm=%u gameplay_started\n",cold); }
    for(unsigned i=0;i<1200;i++) {
        buttons=gameplay[i];
        for(unsigned j=0;j<2;j++) {
            unsigned k=(j+i)&1;
            bool draw=!(k && (off || (half && i%2) || (oracle && i && expected[3*i]==expected[3*(i-1)])));
            enable=draw?3:2;videos=samples=0;
            if(draw && !(k && no_target))assert(c[k].acquire(target+32,sizeof(target)-64));
            if(device) {
                callback_layout=layout[k];pixel_crc=pcm_crc=0;callback_cpu=0;
                uint64_t elapsed=kernel_time(CLOCK_MONOTONIC),t=kernel_time(CLOCK_THREAD_CPUTIME_ID);
                c[k].run();
                times[i][k]=kernel_time(CLOCK_THREAD_CPUTIME_ID)-t;
                wall[i][k]=kernel_time(CLOCK_MONOTONIC)-elapsed;
                observer[i][k]=callback_cpu;
                if(pixel_crc!=expected[3*i] || pcm_crc!=expected[3*i+1] || samples!=expected[3*i+2]) {
                    fprintf(stderr,"oracle_mismatch arm=%u frame=%u rgb=%u pcm=%u count=%u\n",k,i,
                            pixel_crc!=expected[3*i],pcm_crc!=expected[3*i+1],samples!=expected[3*i+2]);
                    return 3;
                }
                const uint32_t boundary=UINT32_MAX;
                layout[k]=crc32(callback_layout,(const void *)&boundary,sizeof(boundary));
            } else {
                uint64_t t=cpu();c[k].run();times[i][k]=cpu()-t;
            }
            assert(videos==(unsigned)draw && samples==expected[3*i+2]);
            published[k]+=videos;audio_frames[k]+=samples;
        }
        if(device && (i+1)%300==0) fprintf(stderr,"gameplay_calls_per_arm=%u\n",i+1);
    }
    printf("cold,%"PRIu64",%"PRIu64"\n",boot[0],boot[1]);
    for(unsigned i=0;i<1200;i++) {
        printf("%u,%"PRIu64",%"PRIu64,i,times[i][0],times[i][1]);
        if(device) printf(",%"PRIu64",%"PRIu64",%"PRIu64",%"PRIu64,
                          wall[i][0],wall[i][1],observer[i][0],observer[i][1]);
        putchar('\n');
    }
    printf("published,%u,%u\naudio,%u,%u\n",published[0],published[1],audio_frames[0],audio_frames[1]);
    if(brr_read) {
        brr_read(brr_after);
        printf("brr probes=%"PRIu64" passes=%"PRIu64" active_ticks=%"PRIu64
               " last_hits=%"PRIu64" profile_cpu_ns=%"PRIu64" max_probe_cpu_ns=%"PRIu64"\n",
               brr_after[0]-brr_before[0],brr_after[1]-brr_before[1],
               brr_after[2]-brr_before[2],brr_after[3],
               brr_after[4]-brr_before[4],brr_after[5]);
    }
    if(device) {
        assert(layout[0]==layout[1]);
        printf("oracle,1200,1200,%08"PRIx32",%08"PRIx32"\n",layout[0],layout[1]);
    }
    for(unsigned k=0;k<2;k++){c[k].unload();c[k].deinit();dlclose(c[k].handle);}
    free(rom);free(expected);return 0;
}
