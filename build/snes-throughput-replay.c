/* Offline libretro replay. Input and output oracle are owner-supplied.
 * No vendor hardware calls. Timing mode does not hash/copy callback output. */
#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <dlfcn.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <zlib.h>
#include "libretro.h"

static int enable=3, verify, pixels;
static uint16_t buttons;
static uint32_t pixel_crc, pcm_crc, samples, videos, callback_layout;
static uint16_t target[512*240/2+128] __attribute__((aligned(64)));
static const void *offered_target;
static unsigned direct_frames;
static bool direct_frame;
#ifdef D35_DISPLAY_REUSE_PROBE
static void display_probe(const void *, unsigned, unsigned, size_t);
#endif

static bool env(unsigned cmd, void *arg) {
    switch (cmd) {
    case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT:
        return *(enum retro_pixel_format *)arg==RETRO_PIXEL_FORMAT_RGB565;
    case RETRO_ENVIRONMENT_GET_AUDIO_VIDEO_ENABLE: *(int *)arg=enable; return true;
    case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE: *(bool *)arg=false; return true;
    case RETRO_ENVIRONMENT_GET_INPUT_BITMASKS:
    case RETRO_ENVIRONMENT_SET_VARIABLES:
    case RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS: return true;
    default: return false;
    }
}
static void video(const void *p, unsigned w, unsigned h, size_t pitch) {
    if (!p) return;
    ++videos;
    direct_frame=p == offered_target;
    direct_frames += direct_frame;
#ifdef D35_DISPLAY_REUSE_PROBE
    if (verify) display_probe(p,w,h,pitch);
#endif
    if (verify && pixels)
        for (unsigned y=0;y<h;++y) pixel_crc=crc32(pixel_crc,(const uint8_t *)p+y*pitch,2*w);
}
static size_t audio(const int16_t *p,size_t n) {
    if (verify) {
        uint32_t size=(uint32_t)n;
        pcm_crc=crc32(pcm_crc,(const void *)p,4*n);
        callback_layout=crc32(callback_layout,(const void *)&size,sizeof(size));
    }
    samples+=n;
    return n;
}
static void sample(int16_t l,int16_t r) {const int16_t p[]={l,r};audio(p,1);}
static void poll(void) {}
static int16_t input(unsigned port,unsigned dev,unsigned ix,unsigned id) {
    if (port || ix || dev!=RETRO_DEVICE_JOYPAD) return 0;
    if (id==RETRO_DEVICE_ID_JOYPAD_MASK) return (int16_t)buttons;
    return id<16 ? (buttons>>id)&1 : 0;
}
static unsigned char *read_file(const char *root,const char *name,size_t *bytes) {
    char path[4096]; assert(snprintf(path,sizeof(path),"%s/%s",root,name)<(int)sizeof(path));
    FILE *f=fopen(path,"rb"); assert(f);
    assert(!fseek(f,0,SEEK_END)); long len=ftell(f); assert(len>0);
    assert(!fseek(f,0,SEEK_SET)); unsigned char *data=malloc(len+1); assert(data);
    assert(fread(data,1,len,f)==(size_t)len); assert(!fclose(f));
    data[len]=0; *bytes=len; return data;
}
static void read_inputs(const char *root,const char *name,uint16_t *out,unsigned count) {
    size_t bytes; unsigned char *data=read_file(root,name,&bytes);
    char *save=NULL,*line=strtok_r((char *)data,"\r\n",&save); unsigned i=0;
    while(line) {
        char *end; unsigned long n=strtoul(line,&end,10);
        assert(end!=line && (*end==' '||*end=='\t') && n>0 && n<=count-i);
        unsigned long mask=strtoul(end,&end,16); assert(!*end && mask<=65535);
        while(n--) out[i++]=mask;
        line=strtok_r(NULL,"\r\n",&save);
    }
    assert(i==count); free(data);
}
static uint64_t cpu(void) {
    struct timespec t; assert(!clock_gettime(CLOCK_THREAD_CPUTIME_ID,&t));
    return (uint64_t)t.tv_sec*1000000000+t.tv_nsec;
}
#ifdef D35_DISPLAY_REUSE_PROBE
#include "snes-display-reuse-probe.h"
#endif

int main(int argc,char **argv) {
    /* mode = full | cold-off | cold-tail | off | half | no-target | oracle-reuse.
     * off/half are ablations, not proposals for full presentation. */
    assert(argc==6);
    const char *mode=argv[4];
    int rotate=!strcmp(mode,"cold-rotate"), poison=!strcmp(mode,"cold-poison");
    int cold_off=!strcmp(mode,"cold-off") || rotate || poison, cold_tail=!strcmp(mode,"cold-tail"),
        off=!strcmp(mode,"off"), half=!strcmp(mode,"half"), no_target=!strcmp(mode,"no-target"),
        oracle_reuse=!strcmp(mode,"oracle-reuse");
    assert(cold_off||cold_tail||off||half||no_target||oracle_reuse||!strcmp(mode,"full"));
    verify=!strcmp(argv[5],"verify"); assert(verify||!strcmp(argv[5],"time"));
    unsigned cold=(unsigned)atoi(argv[3]); assert(cold==0||cold==8656);
    uint16_t warm[8656], gameplay[1200];
    if(cold) read_inputs(argv[2],"warmup.txt",warm,cold);
    read_inputs(argv[2],"input.txt",gameplay,1200);
    size_t rn, en, sn; unsigned char *rom=read_file(argv[2],"game.sfc",&rn);
    uint32_t *expected=(uint32_t *)read_file(argv[2],"expected.bin",&en); assert(en==1200*3*4);
    void *handle=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);
    if(!handle) {fprintf(stderr,"%s\n",dlerror());return 2;}
#define BIND(name,type) __typeof__(type) *name=dlsym(handle,"retro_" #name); assert(name)
    BIND(set_environment,void(retro_environment_t)); BIND(set_video_refresh,void(retro_video_refresh_t));
    BIND(set_audio_sample_batch,void(retro_audio_sample_batch_t)); BIND(set_audio_sample,void(retro_audio_sample_t));
    BIND(set_input_state,void(retro_input_state_t)); BIND(set_input_poll,void(retro_input_poll_t));
    BIND(init,void(void)); BIND(load_game,bool(const struct retro_game_info *));
    BIND(unload_game,void(void)); BIND(deinit,void(void)); BIND(run,void(void));
    BIND(unserialize,bool(const void *,size_t)); BIND(serialize_size,size_t(void));
#undef BIND
    unsigned (*acquire)(void *,size_t)=dlsym(handle,"d35_output_acquire"); assert(acquire);
    void (*census)(uint64_t *)=dlsym(handle,"d35_fx_census");
    void (*fx_loops)(uint32_t *)=dlsym(handle,"d35_fx_loops");
    void (*fx_batch_counts)(uint64_t *)=dlsym(handle,"d35_fx_batch_counts");
    static uint32_t loops[1024][4];
    void (*dma_census)(uint64_t *)=dlsym(handle,"d35_dma_census");
    unsigned (*reuse_read)(void)=dlsym(handle,"d35_reuse_read");
    void (*span_read)(unsigned *)=dlsym(handle,"d35_span_read");
    void (*offset_read)(uint64_t *)=dlsym(handle,"d35_offset_read");
    void (*raster_census)(uint64_t *)=dlsym(handle,"d35_raster_census");
    void (*raster_set_enabled)(bool)=dlsym(handle,"d35_raster_set_enabled");
    void (*fx_set_enabled)(bool)=dlsym(handle,"d35_fx_set_enabled");
    void (*apu_census)(uint64_t *)=dlsym(handle,"d35_apu_census");
    void (*unity_census)(uint64_t *)=dlsym(handle,"d35_unity_census");
    void (*port_census)(uint64_t *)=dlsym(handle,"d35_port_census");
    uint64_t fx[1026];
    set_environment(env);set_video_refresh(video);set_audio_sample_batch(audio);set_audio_sample(sample);
    set_input_state(input);set_input_poll(poll);init();
    struct retro_game_info g={.data=rom,.size=rn}; assert(load_game(&g));
    if(!cold) {
        unsigned char *state=read_file(argv[2],"scene.state",&sn);
        assert(sn==serialize_size()+40 && !memcmp(state,"D35MVP01",8));
        assert(unserialize(state+40,sn-40)); free(state);
    }
    unsigned check=verify; verify=0;
    if(raster_set_enabled) raster_set_enabled(true);
    if(fx_set_enabled) fx_set_enabled(true);
    uint64_t warm_begin=cpu();
    for(unsigned i=0;i<cold;i++) {
        enable=(cold_off || (cold_tail && i+64<cold))?2:3; buttons=warm[i];run();
    }
    uint64_t warm_ns=cpu()-warm_begin;
    verify=check;
    if(census) {
        census(fx); printf("cold_gsu ns=%"PRIu64" runs=%"PRIu64"\n",fx[1024],fx[1025]);
    }
    if(fx_loops) fx_loops(loops[0]);
    if(fx_batch_counts) fx_batch_counts(fx);
    if(dma_census) dma_census(fx);
    if(offset_read) offset_read(fx);
    if(raster_census) raster_census(fx);
    if(apu_census) apu_census(fx);
    if(unity_census) unity_census(fx);
    if(port_census) port_census(fx);
    printf("cold_cpu_ns=%"PRIu64" cold_calls=%u\n",warm_ns,cold);
    uint64_t block[1200];
    unsigned match=0,mismatch=0,first=1200,published=0,audio_frames=0,previous_crc=0;
    unsigned reuse_eligible=0,reuse_matches=0,reuse_false=0;
    unsigned span[7], span_totals[7]={0}, span_false=0;
    unsigned direct_mismatches=0;
    static uint16_t rotating[3][sizeof(target)/sizeof(*target)] __attribute__((aligned(64)));
    direct_frames=0;
    for(unsigned i=0;i<1200;i++) {
        unsigned reuse=oracle_reuse && i && expected[3*i]==expected[3*(i-1)];
        enable=(off||(half && i%2)||reuse)?2:3;
        pixels=enable&1;
        buttons=gameplay[i]; pixel_crc=pcm_crc=samples=videos=0;
        offered_target=NULL;
        direct_frame=false;
        if (pixels && !no_target && (!rotate || i%4 != 3)) {
            uint16_t *storage=(rotate || poison)?rotating[i%3]:target;
            if (poison) memset(storage,(int)(i%255+1),sizeof(target));
            offered_target=storage+32;
            assert(acquire(storage+32,sizeof(target)-64));
        }
        uint64_t start=cpu(); run(); block[i]=cpu()-start;
        assert(videos==(unsigned)pixels);
        published+=videos; audio_frames+=samples;
        if(verify) {
            if(reuse) pixel_crc=previous_crc;
            if(((pixels||reuse) && pixel_crc!=expected[3*i]) || pcm_crc!=expected[3*i+1] || samples!=expected[3*i+2]) {
                if(!mismatch) {first=i;fprintf(stderr,"first mismatch frame=%u pixels=%d pcm=%d sample_count=%d\n",i,
                    (pixels||reuse)&&pixel_crc!=expected[3*i],pcm_crc!=expected[3*i+1],samples!=expected[3*i+2]);}
                ++mismatch;
                direct_mismatches+=direct_frame;
            } else ++match;
            previous_crc=pixel_crc;
            const uint32_t boundary=UINT32_MAX;
            callback_layout=crc32(callback_layout,(const void *)&boundary,sizeof(boundary));
        }
        if(reuse_read) {
            unsigned flags=reuse_read();
            reuse_eligible+=flags&1;
            if(flags&2) {
                ++reuse_matches;
                if(!i || expected[3*i]!=expected[3*(i-1)]) ++reuse_false;
            }
        }
        if(span_read) {
            span_read(span);
            for(unsigned j=0;j<5;++j)span_totals[j]+=span[j];
            span_totals[5]|=span[5];span_totals[6]+=span[6];
            if(span[6] && (!i || expected[3*i]!=expected[3*(i-1)]))++span_false;
        }
    }
    for(unsigned i=0;i<1200;i++)printf("%u,%"PRIu64"\n",i,block[i]);
    if(census) {
        census(fx);
        printf("game_gsu ns=%"PRIu64" runs=%"PRIu64"\n",fx[1024],fx[1025]);
        for(unsigned i=0;i<1024;i++) if(fx[i])printf("opcode %03x %"PRIu64"\n",i,fx[i]);
    }
    if(fx_loops) {
        fx_loops(loops[0]);
        for(unsigned i=0;i<1024;i++)
            if(loops[i][3])printf("loop %06"PRIx32" %04"PRIx32" %08"PRIx32" %"PRIu32"\n",
                                  loops[i][0],loops[i][1],loops[i][2],loops[i][3]);
    }
    if(fx_batch_counts) {
        fx_batch_counts(fx);
        printf("fx_batch fill_batches=%"PRIu64" fill_guest_ops=%"PRIu64
               " plot_batches=%"PRIu64" plot_guest_ops=%"PRIu64"\n",fx[0],fx[1],fx[2],fx[3]);
    }
    if(dma_census) {
        dma_census(fx);
        printf("game_dma spans=%"PRIu64" bytes=%"PRIu64" same=%"PRIu64" same_bytes=%"PRIu64"\n",fx[0],fx[1],fx[2],fx[3]);
    }
    if(reuse_read) printf("reuse_key eligible=%u hits=%u false=%u\n",reuse_eligible,reuse_matches,reuse_false);
    if(span_read) printf("span_key calls=%u eligible=%u rows=%u hits=%u hit_rows=%u modes=%u complete=%u false=%u\n",
        span_totals[0],span_totals[1],span_totals[2],span_totals[3],span_totals[4],span_totals[5],span_totals[6],span_false);
    if(offset_read) {
        offset_read(fx);
        printf("offset_rows calls=%"PRIu64" full=%"PRIu64"\n",fx[0],fx[1]);
    }
    if(raster_census) {
        raster_census(fx);
        printf("raster offset_rows=%"PRIu64" offset_bands=%"PRIu64" offset_columns=%"PRIu64
               " offset_row_draws=%"PRIu64" offset_draws=%"PRIu64" offset_batched_rows=%"PRIu64
               " offset_full_rows=%"PRIu64" obj_rows=%"PRIu64" obj_bands=%"PRIu64
               " obj_batched_rows=%"PRIu64" obj_saved_visits=%"PRIu64"\n",
               fx[0],fx[1],fx[2],fx[3],fx[4],fx[5],fx[6],fx[7],fx[8],fx[9],fx[10]);
    }
    if(apu_census) {
        apu_census(fx);
        printf("apu_census hblank=%"PRIu64" interpreter=%"PRIu64" empty=%"PRIu64
               " retire=%"PRIu64" read=%"PRIu64" write=%"PRIu64" publish=%"PRIu64"\n",
               fx[0],fx[1],fx[2],fx[3],fx[4],fx[5],fx[6]);
    }
    if(unity_census) {
        unity_census(fx);
        printf("unity_census callbacks=%"PRIu64" eligible=%"PRIu64" scalar_samples=%"PRIu64"\n",fx[0],fx[1],fx[2]);
    }
    if(port_census) {
        port_census(fx);
        printf("port_census accesses=%"PRIu64" empty=%"PRIu64"\n",fx[0],fx[1]);
    }
    if(verify) printf("callback_layout=%08"PRIx32"\n",callback_layout);
    if (rotate || poison) printf("direct_frames=%u direct_mismatches=%u\n",direct_frames,direct_mismatches);
#ifdef D35_DISPLAY_REUSE_PROBE
    display_probe_report();
#endif
    printf("published=%u audio_frames=%u verified=%u mismatched=%u first_mismatch=%u\n",
           published,audio_frames,match,mismatch,first);
    unload_game();deinit();dlclose(handle);free(rom);free(expected);
    return mismatch?3:0;
}
