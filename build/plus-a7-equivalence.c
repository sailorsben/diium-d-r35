/* Compare actual baseline and candidate cores with independent callback sinks.
 * Inputs are owner-supplied ROM/state files; outputs contain only checksums. */
#define _GNU_SOURCE
#include <libretro.h>
#include <dlfcn.h>
#include <assert.h>
#include <stdio.h>
#include <signal.h>
#include <ucontext.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <zlib.h>
#include "snes9x2005/source/sa1.h"
#include "snes9x2005/source/apu_blargg.h"
struct core {
    void *handle;
    void (*set_environment)(retro_environment_t);
    void (*set_video_refresh)(retro_video_refresh_t);
    void (*set_audio_sample_batch)(retro_audio_sample_batch_t);
    void (*set_audio_sample)(retro_audio_sample_t);
    void (*set_input_poll)(retro_input_poll_t);
    void (*set_input_state)(retro_input_state_t);
    void (*init)(void),(*deinit)(void),(*run)(void),(*unload_game)(void);
    bool (*load_game)(const struct retro_game_info *);
    size_t (*serialize_size)(void);
    bool (*serialize)(void *,size_t),(*unserialize)(const void *,size_t);
    uint32_t pixels,pcm; size_t samples; unsigned videos,w,h,batches;
};
static struct core *active;
static unsigned frame;
static void fault(int sig,siginfo_t *info,void *context)
{
    ucontext_t *state=context;
    fprintf(stderr,"ARM check fault frame=%u address=%p pc=%08lx lr=%08lx r0=%08lx r1=%08lx r2=%08lx r3=%08lx\n",
        frame,info->si_addr,state->uc_mcontext.arm_pc,state->uc_mcontext.arm_lr,
        state->uc_mcontext.arm_r0,state->uc_mcontext.arm_r1,state->uc_mcontext.arm_r2,state->uc_mcontext.arm_r3);
    _Exit(128+sig);
}
static void normalize_pointers(unsigned char *bytes)
{
    SCPUState *cpu=(SCPUState *)bytes;
    SICPU *icpu=(SICPU *)(bytes+sizeof(SCPUState));
    size_t offset=sizeof(SCPUState)+sizeof(SICPU)+sizeof(SPPU)+sizeof(SDMA)*8+
                  0x10000+0x20000+0x20000+0x8000+SPC_SAVE_STATE_BLOCK_SIZE;
    SSA1 *sa1=(SSA1 *)(bytes+offset);
    uintptr_t base=(uintptr_t)cpu->PCBase; unsigned i;
    /* Upstream serializes raw host pointers. Compare logical CPU offsets;
     * strip only named pointer fields that load rebuilds for the new process. */
    cpu->PC=(uint8_t *)((uintptr_t)cpu->PC-base);
    if(cpu->PCAtOpcodeStart) cpu->PCAtOpcodeStart=(uint8_t *)((uintptr_t)cpu->PCAtOpcodeStart-base);
    if(cpu->WaitAddress) cpu->WaitAddress=(uint8_t *)((uintptr_t)cpu->WaitAddress-base);
    cpu->PCBase=NULL; icpu->UNUSED1=NULL; icpu->S9xOpcodes=NULL;
    sa1->S9xOpcodes=NULL;sa1->PC=sa1->PCBase=sa1->BWRAM=sa1->PCAtOpcodeStart=NULL;
    sa1->WaitAddress=sa1->WaitByteAddress1=sa1->WaitByteAddress2=NULL;
    for(i=0;i<MEMMAP_NUM_BLOCKS;i++) {
        if((uintptr_t)sa1->Map[i]>=4096) sa1->Map[i]=NULL;
        if((uintptr_t)sa1->WriteMap[i]>=4096) sa1->WriteMap[i]=NULL;
    }
}
static bool env(unsigned cmd,void *data)
{
    if(cmd==RETRO_ENVIRONMENT_SET_PIXEL_FORMAT) return *(enum retro_pixel_format *)data==RETRO_PIXEL_FORMAT_RGB565;
    if(cmd==RETRO_ENVIRONMENT_GET_AUDIO_VIDEO_ENABLE) { *(int *)data=3; return true; }
    if(cmd==RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE) { *(bool *)data=false; return true; }
    if(cmd==RETRO_ENVIRONMENT_GET_INPUT_BITMASKS) return true;
    if(cmd==RETRO_ENVIRONMENT_SET_VARIABLES || cmd==RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS) return true;
    return false;
}
static void video_cb(const void *p,unsigned w,unsigned h,size_t pitch)
{
    unsigned y; assert(p); active->w=w; active->h=h; ++active->videos;
    for(y=0;y<h;y++) active->pixels=crc32(active->pixels,(const unsigned char *)p+y*pitch,w*2);
}
static size_t audio_cb(const int16_t *p,size_t n)
{ active->pcm=crc32(active->pcm,(const unsigned char *)p,n*4); active->samples+=n; ++active->batches; return n; }
static void sample_cb(int16_t l,int16_t r) { int16_t p[2]={l,r}; (void)audio_cb(p,1); }
static void poll_cb(void) {}
static int16_t input_cb(unsigned port,unsigned device,unsigned index,unsigned id)
{
    uint16_t buttons=0; (void)index;
    if(port || device!=RETRO_DEVICE_JOYPAD) return 0;
    /* Map movement and short menu open/close impulses, deterministic per core. */
    if(frame%240<20) buttons=1u<<RETRO_DEVICE_ID_JOYPAD_RIGHT;
    if(frame%240==60) buttons=1u<<RETRO_DEVICE_ID_JOYPAD_X;
    if(frame%240==120) buttons=1u<<RETRO_DEVICE_ID_JOYPAD_B;
    return id==RETRO_DEVICE_ID_JOYPAD_MASK?(int16_t)buttons:id<16?(buttons>>id)&1:0;
}
static unsigned char *read_all(const char *path,size_t *n)
{
    FILE *f=fopen(path,"rb"); unsigned char *p; long size;
    assert(f && !fseek(f,0,SEEK_END)); size=ftell(f); assert(size>0 && size<16*1024*1024);
    rewind(f); p=malloc(size); assert(p && fread(p,1,size,f)==(size_t)size); fclose(f); *n=size; return p;
}
static void open_core(struct core *c,const char *path,const unsigned char *rom,size_t n)
{
    struct retro_game_info game={0};
    c->handle=dlopen(path,RTLD_NOW|RTLD_LOCAL); if(!c->handle) puts(dlerror()); assert(c->handle);
#define GET(name) do { *(void **)(&c->name)=dlsym(c->handle,"retro_"#name); assert(c->name); } while(0)
    GET(set_environment);GET(set_video_refresh);GET(set_audio_sample_batch);GET(set_audio_sample);
    GET(set_input_poll);GET(set_input_state);GET(init);GET(deinit);GET(run);GET(unload_game);
    GET(load_game);GET(serialize_size);GET(serialize);GET(unserialize);
#undef GET
    active=c;
    c->set_environment(env);c->set_video_refresh(video_cb);c->set_audio_sample_batch(audio_cb);
    c->set_audio_sample(sample_cb);c->set_input_poll(poll_cb);c->set_input_state(input_cb);
    c->init(); game.data=rom;game.size=n; assert(c->load_game(&game));
}
int main(int argc,char **argv)
{
    struct sigaction handler={0}; handler.sa_sigaction=fault; handler.sa_flags=SA_SIGINFO;
    assert(!sigaction(SIGSEGV,&handler,NULL));
    struct core old={0},candidate={0}; unsigned phase,f,iterations=600,split_frames=0;
    unsigned char *rom,*state,*a,*b; size_t n,state_n,size;
    assert(argc==5 || argc==6);
    if(argc==6) {
        const char *digit=argv[5]; unsigned requested=0;
        assert(*digit);
        while(*digit) {
            assert(*digit>='0' && *digit<='9' && requested<=10000);
            requested=requested*10u+(unsigned)(*digit++-'0');
        }
        assert(requested>=600 && requested<=10000);
        iterations=requested;
    }
    rom=read_all(argv[3],&n); state=read_all(argv[4],&state_n);
    assert(state_n>40 && !memcmp(state,"D35MVP01",8));
    open_core(&old,argv[1],rom,n);open_core(&candidate,argv[2],rom,n);
    size=old.serialize_size(); assert(size==candidate.serialize_size() && state_n==size+40);
    a=calloc(1,size);b=calloc(1,size); assert(a&&b);
    for(phase=0;phase<2;phase++) {
        if(phase) {
            active=&old;assert(old.unserialize(state+40,size));
            active=&candidate;assert(candidate.unserialize(state+40,size));
        }
        for(f=0;f<iterations;f++) {
            frame=f;
            old.pixels=old.pcm=old.samples=old.videos=0;
            candidate.pixels=candidate.pcm=candidate.samples=candidate.videos=0;
            old.batches=candidate.batches=0;
            active=&old;old.run();active=&candidate;candidate.run();
            if(candidate.batches>old.batches) ++split_frames;
            if(old.pixels!=candidate.pixels || old.pcm!=candidate.pcm || old.samples!=candidate.samples ||
               old.videos!=1 || candidate.videos!=1 || old.w!=candidate.w || old.h!=candidate.h) {
                printf("FAIL phase%u frame%u pixels%08x/%08x pcm%08x/%08x samples%u/%u\n",
                    phase,f,old.pixels,candidate.pixels,old.pcm,candidate.pcm,(unsigned)old.samples,(unsigned)candidate.samples);
                return 1;
            }
            if(!(f%30)) {
                active=&old;assert(old.serialize(a,size));active=&candidate;assert(candidate.serialize(b,size));
                normalize_pointers(a);normalize_pointers(b);
                if(memcmp(a,b,size)) {
                    size_t pos; unsigned differences=0;
                    for(pos=0;pos<size && differences<12;pos++) if(a[pos]!=b[pos]) {
                        printf("state difference offset%u %02x/%02x\n",(unsigned)pos,a[pos],b[pos]); ++differences;
                    }
                    printf("FAIL normalized serialized phase%u frame%u\n",phase,f); return 1;
                }
            }
        }
    }
    active=&old;old.unload_game();old.deinit();active=&candidate;candidate.unload_game();candidate.deinit();
    dlclose(old.handle);dlclose(candidate.handle);free(rom);free(state);free(a);free(b);
    printf("PASS: %u frames exact visible pixels, native PCM, geometry and periodic state with named host pointers normalized; intro and returned private snapshot\n",iterations*2);
    assert(split_frames>iterations);
    printf("PASS: earlier PCM publication splits %u frames into multiple byte-equivalent batches\n",split_frames);
    return 0;
}
