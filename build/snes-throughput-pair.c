/* Compare two independent libretro instances on the same logical CPU.
 * Alternate call order each frame; retain the same warmup, input and callbacks. */
#define main d35_single_main
#include "snes-throughput-replay.c"
#undef main

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
    set_environment(env);set_video_refresh(video);set_audio_sample_batch(audio);set_audio_sample(sample);
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
    bool both_cold_off=!strcmp(mode,"both-cold-off")||!strcmp(mode,"both-cold-off-toggle");
    bool toggle=!strcmp(mode,"full-toggle")||!strcmp(mode,"both-cold-off-toggle");
    assert(cold_off||oracle||off||no_target||half||both_cold_off||toggle||!strcmp(mode,"full"));
    unsigned cold=(unsigned)atoi(argv[4]);assert(cold==0||cold==8656);
    size_t rn,en;unsigned char *rom=read_file(argv[3],"game.sfc",&rn);
    uint32_t *expected=(uint32_t *)read_file(argv[3],"expected.bin",&en);assert(en==1200*12);
    uint16_t warm[8656],gameplay[1200];
    if(cold)read_inputs(argv[3],"warmup.txt",warm,cold);
    read_inputs(argv[3],"input.txt",gameplay,1200);
    struct instance c[]={setup(argv[1],argv[3],cold,rom,rn),setup(argv[2],argv[3],cold,rom,rn)};
    assert(c[0].handle!=c[1].handle);
    if(toggle) {
        for(unsigned k=0;k<2;k++) {
            void (*set_enabled)(bool)=dlsym(c[k].handle,"d35_raster_set_enabled");
            assert(set_enabled);set_enabled(k==1);
        }
    }
    uint64_t boot[2]={0}, times[1200][2];
    unsigned audio_frames[2]={0}, published[2]={0};
    for(unsigned i=0;i<cold;i++) {
        buttons=warm[i];
        for(unsigned j=0;j<2;j++) {
            unsigned k=(j+i)&1;
            enable=(both_cold_off || (k && cold_off))?2:3;
            uint64_t t=cpu();c[k].run();boot[k]+=cpu()-t;
        }
    }
    for(unsigned i=0;i<1200;i++) {
        buttons=gameplay[i];
        for(unsigned j=0;j<2;j++) {
            unsigned k=(j+i)&1;
            bool draw=!(k && (off || (half && i%2) || (oracle && i && expected[3*i]==expected[3*(i-1)])));
            enable=draw?3:2;videos=samples=0;
            if(draw && !(k && no_target))assert(c[k].acquire(target+32,sizeof(target)-64));
            uint64_t t=cpu();c[k].run();times[i][k]=cpu()-t;
            assert(videos==(unsigned)draw && samples==expected[3*i+2]);
            published[k]+=videos;audio_frames[k]+=samples;
        }
    }
    printf("cold,%"PRIu64",%"PRIu64"\n",boot[0],boot[1]);
    for(unsigned i=0;i<1200;i++)printf("%u,%"PRIu64",%"PRIu64"\n",i,times[i][0],times[i][1]);
    printf("published,%u,%u\naudio,%u,%u\n",published[0],published[1],audio_frames[0],audio_frames[1]);
    for(unsigned k=0;k<2;k++){c[k].unload();c[k].deinit();dlclose(c[k].handle);}
    free(rom);free(expected);return 0;
}
