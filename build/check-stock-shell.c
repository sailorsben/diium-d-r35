/* Execute the stock ELF launch boundary and real ARM cores with fake devices. */
#define main stock_audit_main
#include "check-stock-snes-loader.c"
#undef main
#include <dlfcn.h>
#include <errno.h>
#include <inttypes.h>
#include <libretro.h>
#include <sys/stat.h>
#include <time.h>
#include <zlib.h>
#include "snes9x2005/source/sa1.h"
#include "snes9x2005/source/apu_blargg.h"

static const char *work, *reference, *rom, *fixture_dir;
static unsigned ncore, nclose, driver_token, patched, force_auto, fail_load, entered;
static uint32_t video_crc, visible_crc, pcm_crc, layout_crc, state_crc;
static unsigned pictures, sampled, completed, copies, drained, chunk_frees, wait_calls;
static unsigned predecoded, verify, ticks=1200;
static void *pool;
static uint64_t begin_ns, launch_ns, game_ns, warm_ns;
static uint16_t input_mask, inputs[1200], cold[8656];
static const void *last_picture;
static unsigned last_width,last_height;
static uint64_t total_frames;
static bool paired, baseline_active;
static uint64_t baseline_ns;

static void normalize_pointers(unsigned char *bytes)
{
    SCPUState *cpu=(SCPUState *)bytes;
    SICPU *icpu=(SICPU *)(bytes+sizeof(SCPUState));
    size_t offset=sizeof(SCPUState)+sizeof(SICPU)+sizeof(SPPU)+sizeof(SDMA)*8+
                  0x10000+0x20000+0x20000+0x8000+SPC_SAVE_STATE_BLOCK_SIZE;
    SSA1 *sa1=(SSA1 *)(bytes+offset);
    uintptr_t base=(uintptr_t)cpu->PCBase;
    cpu->PC=(uint8_t *)((uintptr_t)cpu->PC-base);
    if(cpu->PCAtOpcodeStart) cpu->PCAtOpcodeStart=(uint8_t *)((uintptr_t)cpu->PCAtOpcodeStart-base);
    if(cpu->WaitAddress) cpu->WaitAddress=(uint8_t *)((uintptr_t)cpu->WaitAddress-base);
    cpu->PCBase=NULL; icpu->UNUSED1=NULL; icpu->S9xOpcodes=NULL;
    sa1->S9xOpcodes=NULL; sa1->PC=sa1->PCBase=sa1->BWRAM=sa1->PCAtOpcodeStart=NULL;
    sa1->WaitAddress=sa1->WaitByteAddress1=sa1->WaitByteAddress2=NULL;
    for(unsigned i=0;i<MEMMAP_NUM_BLOCKS;++i) {
        if((uintptr_t)sa1->Map[i]>=4096) sa1->Map[i]=NULL;
        if((uintptr_t)sa1->WriteMap[i]>=4096) sa1->WriteMap[i]=NULL;
    }
}

static uint64_t cpu_time(void)
{
    struct timespec ts;
    assert(!clock_gettime(CLOCK_THREAD_CPUTIME_ID,&ts));
    return (uint64_t)ts.tv_sec*1000000000ull+(uint64_t)ts.tv_nsec;
}
static const char *work_path(void) { return work; }
static void *open_actual_core(const char *path,int mode)
{
    assert(mode==RTLD_NOW);
    assert(!strcmp(path,patched?"fixture/libs/d35-snes.so":"/usr/retro/libs/emu_sfc.so"));
    ++ncore;
    char direct[4096];
    assert(snprintf(direct,sizeof(direct),"%s/libs/d35-snes.so",work)<(int)sizeof(direct));
    void *h=dlopen(patched?direct:reference,mode);
    if(!h) fprintf(stderr,"%s\n",dlerror());
    assert(h);
    return h;
}
static int close_actual_core(void *h) { ++nclose; return dlclose(h); }
static void wait_display(void) { ++wait_calls; drained=1; }
static void *alloc_chunk(size_t n) { assert(!pool && n==2*512*512*2); return pool=malloc(n); }
static void free_chunk(void *p) { assert(p==pool && (!copies||drained)); free(p); pool=NULL; ++chunk_frees; }
static int16_t replay_input(unsigned port,unsigned dev,unsigned idx,unsigned id)
{
    if(port||idx||dev!=RETRO_DEVICE_JOYPAD) return 0;
    return id<16?(input_mask>>id)&1:0;
}
static int reject(const struct retro_game_info *g) { assert(g->size>=32768); return 0; }
static void *resolve_actual(void *h,const char *s)
{
    if(h==&driver_token) { assert(!strcmp(s,"WaitDisp")); return wait_display; }
    if(fail_load && !strcmp(s,"retro_load_game")) return reject;
    return dlsym(h,s);
}
static size_t sink_audio(const int16_t *p,size_t n)
{
    if(sampled) {
        if(verify) {
            pcm_crc=crc32(pcm_crc,(const uint8_t *)p,4*n);
            uint32_t len=n;
            layout_crc=crc32(layout_crc,(const uint8_t *)&len,4);
        }
        total_frames+=n;
    }
    return 0; /* exact stock sink convention */
}
static void sink_video(const void *p,unsigned w,unsigned h,size_t pitch)
{
    if(!p) return;
    assert(w && h && pitch==w*2);
    if(baseline_active) return;
    if(patched) {
        assert(p==pool || p==(uint8_t *)pool+512*512*2);
        assert(p!=last_picture);
        assert(copies<2 || drained);
    }
    last_picture=p; last_width=w; last_height=h; drained=0;
    ++copies;
    if(sampled) ++pictures;
}
static unsigned char *read_binary(const char *path,size_t *n)
{
    FILE *f=fopen(path,"rb"); assert(f && !fseek(f,0,SEEK_END));
    long len=ftell(f); assert(len>0 && !fseek(f,0,SEEK_SET));
    unsigned char *p=malloc(len); assert(p && fread(p,1,len,f)==(size_t)len && !fclose(f));
    *n=len; return p;
}
static void read_input(const char *name,uint16_t *table,unsigned len)
{
    char p[4096]; assert(snprintf(p,sizeof(p),"%s/%s",fixture_dir,name)<(int)sizeof(p));
    FILE *f=fopen(p,"r"); assert(f); unsigned repeat,mask,i=0;
    while(fscanf(f,"%u %x",&repeat,&mask)==2) {
        assert(repeat && repeat<=len-i && mask<=65535);
        while(repeat--) table[i++]=(uint16_t)mask;
    }
    assert(i==len && !fclose(f));
}
static uintptr_t branch_target(uintptr_t pc)
{
    int32_t word=*(int32_t *)pc;
    return pc+8+((int32_t)((uint32_t)word<<8)>>6);
}
static void play_fixture(void)
{
    launch_ns=cpu_time()-begin_ns;
    ++entered;
    void *h=*(void **)0x1bd5dc;
    void (*run)(void)=dlsym(h,"retro_run");
    if(patched) {
        void *(*resolve_run)(void *,const char *)=(void *)branch_target(0xa42e8);
        void (*effective)(void)=resolve_run(h,"retro_run");
        assert((run!=effective)==force_auto);
        run=effective;
    }
    size_t (*state_size)(void)=dlsym(h,"retro_serialize_size");
    bool (*serialize)(void *,size_t)=dlsym(h,"retro_serialize");
    bool (*unserialize)(const void *,size_t)=dlsym(h,"retro_unserialize");
    void (*unload)(void)=dlsym(h,"retro_unload_game");
    void (*deinit)(void)=dlsym(h,"retro_deinit");
    assert(run&&state_size&&serialize&&unserialize&&unload&&deinit);
    void *adapter=NULL;
    void (*base_run)(void)=NULL, (*base_unload)(void)=NULL, (*base_deinit)(void)=NULL;
    bool (*base_unserialize)(const void *,size_t)=NULL;
    if(paired) {
        const char *other=getenv("D35_PAIR_CORE"); assert(other);
        assert(!setenv("D35_PLUS_CORE",other,1));
        adapter=dlopen(reference,RTLD_NOW|RTLD_LOCAL); assert(adapter);
        void (*set_env)(retro_environment_t)=dlsym(adapter,"retro_set_environment");
        void (*set_video)(retro_video_refresh_t)=dlsym(adapter,"retro_set_video_refresh");
        void (*set_audio)(retro_audio_sample_batch_t)=dlsym(adapter,"retro_set_audio_sample_batch");
        void (*set_input)(retro_input_state_t)=dlsym(adapter,"retro_set_input_state");
        void (*init)(void)=dlsym(adapter,"retro_init");
        bool (*load)(const struct retro_game_info *)=dlsym(adapter,"retro_load_game");
        base_run=dlsym(adapter,"retro_run"); base_unload=dlsym(adapter,"retro_unload_game");
        base_deinit=dlsym(adapter,"retro_deinit"); base_unserialize=dlsym(adapter,"retro_unserialize");
        assert(set_env&&set_video&&set_audio&&set_input&&init&&load&&base_run&&base_unserialize);
        set_env((retro_environment_t)ENVIRONMENT); set_video(sink_video);
        set_audio(sink_audio); set_input(replay_input); init();
        size_t length; unsigned char *bytes=read_binary(rom,&length);
        struct retro_game_info game={rom,bytes,length,NULL};
        assert(load(&game)); free(bytes);
    }
    char state_path[4096];
    assert(snprintf(state_path,sizeof(state_path),"%s/scene.state",fixture_dir)<(int)sizeof(state_path));
    if(!access(state_path,F_OK)) {
        size_t n; unsigned char *data=read_binary(state_path,&n);
        assert(n>40 && !memcmp(data,"D35MVP01",8));
        if(patched) assert(unserialize(data+40,n-40));
        else {
            uint32_t bytes=n-40;
            memcpy(data+24,"D35PLUS1",8); memcpy(data+32,&bytes,4); memcpy(data+36,"a79d",4);
            assert(unserialize(data+24,n-24));
        }
        if(paired) {
            uint32_t bytes=n-40;
            memcpy(data+24,"D35PLUS1",8); memcpy(data+32,&bytes,4); memcpy(data+36,"a79d",4);
            assert(base_unserialize(data+24,n-24));
        }
        free(data);
    } else {
        read_input("warmup.txt",cold,8656);
        uint64_t t=cpu_time();
        for(unsigned i=0;i<8656;++i) {
            input_mask=cold[i]; run();
            if(paired) { baseline_active=true; base_run(); baseline_active=false; }
        }
        warm_ns=cpu_time()-t;
    }
    read_input("input.txt",inputs,1200);
    sampled=1;
    unsigned start_copies=copies;
    for(unsigned i=0;i<ticks;++i) {
        unsigned before=copies;
        input_mask=inputs[i];
        *(int *)0x1bd620=i>=12 && i%60<18;
        if(paired && !(i%2)) {
            baseline_active=true;
            uint64_t t=cpu_time(); base_run(); baseline_ns+=cpu_time()-t;
            baseline_active=false;
        }
        uint64_t t=cpu_time(); run(); game_ns+=cpu_time()-t;
        if(paired && i%2) {
            baseline_active=true;
            uint64_t base_time=cpu_time(); base_run(); baseline_ns+=cpu_time()-base_time;
            baseline_active=false;
        }
        if(verify) {
            assert(last_picture && last_width && last_height);
            if(copies!=before || !i)
                visible_crc=crc32(0,last_picture,last_width*last_height*2);
            video_crc=crc32(video_crc,(const uint8_t *)&visible_crc,4);
            uint32_t end=UINT32_MAX;
            layout_crc=crc32(layout_crc,(const uint8_t *)&end,4);
        }
        ++completed;
    }
    sampled=0;
    assert(pictures==copies-start_copies);
    size_t size=state_size(); unsigned char *data=malloc(size);
    assert(data && serialize(data,size));
    size_t header=patched?0:16;
    normalize_pointers(data+header);
    state_crc=crc32(0,data+header,size-header); free(data);
    if(paired) { base_unload(); base_deinit(); assert(!dlclose(adapter)); }
    unload(); deinit(); assert(!close_actual_core(h));
}
static void *alias_open(const char *p,int mode)
{
    if(!strcmp(p,"fixture/libs/d35-snes.so")) {
        assert(mode==2 && patched);
        ++ncore;
        const char *path=getenv("D35_PLUS_CORE");
        assert(path);
        void *h=dlopen(path,mode);
        if(!h) fprintf(stderr,"%s\n",dlerror());
        assert(h);
        return h;
    }
    return open_actual_core(p,mode);
}

int main(int argc,char **argv)
{
    assert(argc==8);
    patched=strcmp(argv[5],"stock")!=0;
    paired=!strcmp(argv[5],"paired");
    force_auto=!strcmp(argv[5],"auto");
    predecoded=!strcmp(argv[5],"zip");
    fail_load=!strcmp(argv[5],"reject");
    verify=!strcmp(argv[6],"verify");
    ticks=strtoul(argv[7],NULL,10); assert(ticks && ticks<=1200);
    work="fixture"; reference=argv[4]; fixture_dir=argv[3];
    char path[4096];
    assert(snprintf(path,sizeof(path),"%s/game.sfc",fixture_dir)<(int)sizeof(path));
    rom=path;
    /* Stock copies its filename into a 256-byte global. */
    assert(strlen(rom)<256);
    assert(!setenv("D35_PLUS_CORE",argv[2],1) && !setenv("D35_TEST_HEAP_VIDEO","1",1));
    assert(!setenv("D35_V10_DISABLE","1",1));
    map_vendor(argv[1]);
    patch(0x11d34,(uintptr_t)alias_open);
    patch(0x12010,(uintptr_t)resolve_actual);
    patch(0x11c14,(uintptr_t)close_actual_core);
    patch(0x11be4,(uintptr_t)quiet);
    patch(0x11d64,(uintptr_t)strcpy); patch(0x11bfc,(uintptr_t)stpcpy);
    patch(0x11f74,(uintptr_t)strcmp); patch(0x11ce0,(uintptr_t)fopen);
    patch(0x11b84,(uintptr_t)fseek); patch(0x11e84,(uintptr_t)ftell);
    patch(0x11ed8,(uintptr_t)malloc); patch(0x11ddc,(uintptr_t)fread);
    patch(0x11f20,(uintptr_t)fclose); patch(0x11b6c,(uintptr_t)free);
    patch(0x11c20,(uintptr_t)puts); patch(0x11c8c,(uintptr_t)memset);
    patch(0x11ecc,(uintptr_t)memcpy); patch(0x11fc8,(uintptr_t)memcmp);
    patch(0x80bec,(uintptr_t)work_path); patch(0x164abc,(uintptr_t)alloc_chunk);
    patch(0x164d58,(uintptr_t)free_chunk); patch(0xa2cc4,(uintptr_t)sink_audio);
    patch(0xa3438,(uintptr_t)sink_video); patch(0xa2f0c,(uintptr_t)replay_input);
    patch(FRAME_FLASH,(uintptr_t)frame_flash); patch(KEY_MAPPING,(uintptr_t)key_mapping);
    patch(LOAD_PROC2,(uintptr_t)play_fixture);
    strcpy((char *)*(uint32_t *)(GOT+0x274),"/usr/");
    *(void **)0x1b81a8=&driver_token;
    *(uint8_t *)0x1c4100=0; /* mapping and zero-fill present */
    /* Ask the production settings entry to read the same persistent option
     * used on the device. Only the hardware-dependent stock settings body is stubbed. */
    if(patched) {
        assert(!mkdir("fixture",0755) || errno==EEXIST);
        FILE *f=fopen("fixture/d35-loader.cfg","wb"); assert(f);
        assert(fputc(force_auto?'1':'0',f)!=EOF && !fclose(f));
        patch(0x81da0,(uintptr_t)frame_flash);
        ((void (*)(void))branch_target(0x98174))();
    }
    if(predecoded) {
        size_t bytes;
        *(void **)0x1bba7c=read_binary(rom,&bytes);
        *(size_t *)0x1bba8c=bytes;
    }
    int (*launch_game)(const char *,unsigned)=(void *)SNES_LOAD;
    begin_ns=cpu_time();
    int rc=launch_game(rom,predecoded?0x10004:4);
    if(fail_load) assert(rc<0 && entered==0);
    else assert(rc==0 && entered==1 && completed==ticks);
    assert(ncore==1 && nclose==1);
    assert(!patched || (!pool && chunk_frees==1 && (!copies||wait_calls) && !*(void **)0x1bd5dc));
    printf("mode=%s ticks=%u pictures=%u pcm_frames=%"PRIu64" video=%08x pcm=%08x layout=%08x state=%08x launch_ns=%"PRIu64" game_ns=%"PRIu64" warm_ns=%"PRIu64" baseline_ns=%"PRIu64"\n",
           argv[5],completed,pictures,total_frames,video_crc,pcm_crc,layout_crc,state_crc,launch_ns,game_ns,warm_ns,baseline_ns);
    return 0;
}
