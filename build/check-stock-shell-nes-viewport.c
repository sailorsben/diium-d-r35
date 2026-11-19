/* Execute the vendor NES launch and frame callbacks with the actual card core. */
#define main stock_audit_main
#include "check-stock-snes-loader.c"
#undef main
#include <dlfcn.h>
#include <stdbool.h>
#include <stdarg.h>
#include <unistd.h>

#include "libretro.h"

enum {
    NES_LOAD=0xa5058, PLAY_FRAME=0xa2cc4, INPUT_STATE=0xa2f0c,
    WORK_PATH=0x1b8a00, DISPLAY_CALLBACK=0x1be388,
    CORE_VIDEO_OUTPUT=0x89b74,
};

static const char *core_path, *rom_path;
static void *nes_core;
static const char *device_rom="/usr/003/fixture.nes";
static bool trim_edges;
static uint16_t trim_buffer[2][256*224];
static char driver_token;
static unsigned trim_waits;
static bool trim_live;
static unsigned frames, width, height, pitch;
static uint16_t last_frame[256*240];
static uint16_t device_chunk[256*240];
static uint16_t **core_output;
static unsigned capture_frame, input_button;
static retro_environment_t frontend_environment;
static bool (*core_load)(const struct retro_game_info *);
static void (*core_set_environment)(retro_environment_t);
static const char *overscan_value="default";
static const char receipt_path[]="/usr/retro/d35-launcher1/nes-viewport.log";
static const char receipt_temp[]="/usr/retro/d35-launcher1/nes-viewport.log.tmp";
static const char boot_id[]="12345678-1234-5678-abcd-123456789012";
static FILE *receipt_file;
static char receipt[160];
static bool receipt_published;
static uint32_t scaler_input[5];
static const void *scaler_source;
static uint16_t display_canvas[640*480];
static const char *input_replay;
static unsigned active_pin;

static int button_level(unsigned pin) { return pin!=active_pin; }
static unsigned no_usb(unsigned port) { (void)port; return 0; }

static int open_scaler(const char *path,int flags)
{
    assert(!strcmp(path,"/dev/pscaler_a") && flags==2);
    return 17;
}

static int ioctl_scaler(int fd,unsigned long request,...)
{
    assert(fd==17);
    va_list args;
    va_start(args,request);
    switch(request) {
    case 0x40e45000: {
        const uint32_t *config=va_arg(args,const uint32_t *);
        memcpy(scaler_input,config,sizeof(scaler_input));
        assert(config[6]==640 && config[7]==480);
        scaler_source=(const void *)(uintptr_t)config[14];
        assert(config[16]==(uintptr_t)display_canvas);
        break;
    }
    case 0x80045005:
        *va_arg(args,unsigned *)=2;
        break;
    default:
        assert(request==0x5003 || request==0x80045001 || request==0x80045004);
    }
    va_end(args);
    return 0;
}

static int close_scaler(int fd)
{
    assert(fd==17);
    return 0;
}

static void verify_scaler(const char *path)
{
    void *driver=dlopen(path,RTLD_NOW);
    assert(driver);
    void (*submit)(const void *,unsigned,unsigned,size_t)=dlsym(driver,"video_driver_disp_frame");
    void (*draw)(const void *,unsigned,unsigned)=dlsym(driver,"DrawVFB");
    assert(submit && draw);
    Dl_info mapping;
    assert(dladdr(draw,&mapping));
    uintptr_t code=(uintptr_t)mapping.dli_fbase;
    assert(!mprotect((void *)(code+0x1000),4096,PROT_READ|PROT_WRITE|PROT_EXEC));
    patch(code+0x1294,(uintptr_t)open_scaler);
    patch(code+0x1234,(uintptr_t)ioctl_scaler);
    patch(code+0x1354,(uintptr_t)close_scaler);

    /* One synthetic LCD output buffer. The driver's mode-zero queue and
     * source rectangle are real. Only the worker and scaler syscalls are mocked. */
    static uint32_t lcd[27];
    lcd[2]=(480u<<16)|640;
    lcd[6]=(uintptr_t)display_canvas;
    void **handle=dlsym(driver,"hDisp");
    const void *const *pending_frame=dlsym(driver,"Frame_data");
    const unsigned *pending_width=dlsym(driver,"Frame_width");
    const unsigned *pending_height=dlsym(driver,"Frame_height");
    assert(handle && pending_frame && pending_width && pending_height);
    *handle=lcd;
    submit(last_frame,width,height,pitch);
    assert(*pending_frame==last_frame && *pending_width==width && *pending_height==height);
    draw(*pending_frame,*pending_width,*pending_height);
    assert(scaler_source==last_frame && scaler_input[0]==0 &&
           scaler_input[1]==width && scaler_input[2]==height &&
           scaler_input[3]==0 && scaler_input[4]==0);
    printf("scaler source=%ux%u start=(%u,%u) output=640x480\n",
           scaler_input[1],scaler_input[2],scaler_input[3],scaler_input[4]);
    assert(!dlclose(driver));
}

static FILE *open_nes_rom(const char *path,const char *mode)
{
    if(!strcmp(path,device_rom)) {
        assert(!strcmp(mode,"rb"));
        return fopen(rom_path,mode);
    }
    FILE *file=tmpfile();
    assert(file);
    if(!strcmp(path,"/proc/sys/kernel/random/boot_id")) {
        assert(!strcmp(mode,"rb") && fputs(boot_id,file)>=0);
        rewind(file);
    } else {
        assert(!strcmp(path,receipt_temp) && !strcmp(mode,"wb"));
        receipt_file=file;
    }
    return file;
}

static int close_nes_file(FILE *file)
{
    if(file==receipt_file) {
        rewind(file);
        size_t n=fread(receipt,1,sizeof(receipt)-1,file);
        assert(n && !ferror(file));
        receipt[n]=0;
        receipt_file=NULL;
    }
    return fclose(file);
}

static int publish_receipt(const char *old,const char *new)
{
    assert(!strcmp(old,receipt_temp) && !strcmp(new,receipt_path) && receipt[0]);
    receipt_published=true;
    return 0;
}

static void *open_nes_core(const char *path,int mode)
{
    assert(!strcmp(path,"/usr/retro/libs/emu_nes.so") && mode==RTLD_NOW);
    nes_core=dlopen(core_path,mode);
    if(!nes_core) fprintf(stderr,"%s\n",dlerror());
    assert(nes_core);
    return nes_core;
}

static void capture_video(const void *frame,unsigned w,unsigned h,size_t stride)
{
    assert(frame && w<=256 && h<=240 && stride>=2*w);
    if(trim_edges) {
        assert(h==224 && trim_live);
        assert(frame==trim_buffer[frames%2]);
    }
    width=w; height=h; pitch=stride;
    ++frames;
    if(!capture_frame) return;
    const uint8_t *row=frame;
    for(unsigned y=0;y<h;++y,row+=stride)
        memcpy(last_frame+y*w,row,2*w);
}

static void *allocate_trim(size_t bytes)
{
    assert(trim_edges && !trim_live && bytes==sizeof(trim_buffer));
    trim_live=true;
    return trim_buffer;
}

static void wait_for_trim(void)
{
    assert(trim_live);
    ++trim_waits;
}

static void release_trim(void *pointer)
{
    assert(pointer==trim_buffer && trim_live && trim_waits==1);
    trim_live=false;
}

static size_t accept_audio(const int16_t *audio,size_t count)
{
    (void)audio;
    return count;
}

static int16_t read_button(unsigned port,unsigned device,unsigned index,unsigned id)
{
    return !port && device==RETRO_DEVICE_JOYPAD && !index && input_button==id;
}

static bool observe_environment(unsigned command,void *data)
{
    bool result=frontend_environment(command,data);
    if(command==RETRO_ENVIRONMENT_GET_VARIABLE) {
        const struct retro_variable *var=data;
        if(!strcmp(var->key,"fceumm_overscan"))
            overscan_value=result && var->value ? var->value : "default";
    }
    return result;
}

static void connect_environment(retro_environment_t environment)
{
    assert((uintptr_t)environment==ENVIRONMENT);
    frontend_environment=environment;
    core_set_environment(observe_environment);
}

static bool load_nes_rom(const struct retro_game_info *game)
{
    assert(!strcmp(game->path,device_rom) && game->data && game->size);
    assert(core_load(game));
    Dl_info core_info;
    assert(dladdr(core_load,&core_info));
    /* fceu_video_out in the card's core is null without /dev/chunkmem. */
    core_output=(uint16_t **)((uintptr_t)core_info.dli_fbase+CORE_VIDEO_OUTPUT);
    assert(!*core_output);
    *core_output=device_chunk;
    return true;
}

static void *resolve_nes(void *handle,const char *name)
{
    if(!handle) {
        assert(!strcmp(name,"rename"));
        return publish_receipt;
    }
    if(handle==&driver_token) {
        assert(trim_edges && !strcmp(name,"WaitDisp"));
        return wait_for_trim;
    }
    assert(handle==nes_core);
    if(!strcmp(name,"retro_set_environment")) {
        core_set_environment=dlsym(handle,name);
        assert(core_set_environment);
        return connect_environment;
    }
    if(!strcmp(name,"retro_load_game")) {
        core_load=dlsym(handle,name);
        assert(core_load);
        return load_nes_rom;
    }
    return dlsym(handle,name);
}

static void step(void (*run)(void),unsigned button,unsigned count)
{
    input_button=button;
    while(count--) run();
}

/* Restore an owner's local FCEUmm state and inject one GPIO scan in the
 * interval between the pause-chord check and the next emulated frame. */
static void replay_state_input(void (*run)(void))
{
    FILE *state=fopen(input_replay,"rb");
    assert(state && !fseek(state,0,SEEK_END));
    long length=ftell(state);
    assert(length>0);
    rewind(state);
    void *bytes=malloc((size_t)length);
    assert(bytes && fread(bytes,1,(size_t)length,state)==(size_t)length && !fclose(state));
    bool (*restore)(const void *,size_t)=dlsym(nes_core,"retro_unserialize");
    assert(restore && restore(bytes,(size_t)length));
    free(bytes);
    unsigned pin=0;
    const char *action=getenv("D35_INPUT_BUTTON");
    if(action && !strcmp(action,"esc")) pin=0x206;
    else if(action && !strcmp(action,"start")) pin=0x30c;
    else assert(action && !strcmp(action,"none"));
    unsigned instruction=*(unsigned *)0xa4554;
    assert((instruction>>24)==0xeb);
    int32_t displacement=(int32_t)(instruction<<8)>>6;
    void (*prepare)(void)=(void *)(uintptr_t)(0xa455c+displacement);
    for(unsigned i=0;i<80;++i) {
        active_pin=i==12?pin:0;
        ((void (*)(void))0x1599c)();
        prepare();
        capture_frame=i==79;
        run();
    }
}

static void replay_opening_battle(void (*run)(void),const struct retro_system_av_info *av)
{
    const unsigned idle=~0u, a=RETRO_DEVICE_ID_JOYPAD_A, right=RETRO_DEVICE_ID_JOYPAD_RIGHT;
    step(run,idle,2518);
    for(unsigned i=0;i<2;++i) { step(run,a,8); step(run,idle,55); }
    for(unsigned character=0;character<4;++character) {
        if(character) { step(run,right,6); step(run,idle,8); }
        for(unsigned i=0;i<7;++i) { step(run,a,8); step(run,idle,16); }
    }
    step(run,idle,160);
    capture_frame=1;
    for(unsigned i=0;i<3;++i) { step(run,a,8); step(run,idle,60); }
    printf("submitted=%ux%u pitch=%u frames=%u\n",width,height,pitch,frames);
    assert(frames==3722 && width==av->geometry.base_width);
    assert(height==av->geometry.base_height-(trim_edges?16:0));
    if(width==256) {
        /* The opening battle's left border uses column 1. */
        bool left_border=false;
        for(unsigned y=152-(trim_edges?8:0);y<231-(trim_edges?8:0);++y)
            left_border |= last_frame[y*width+1]!=last_frame[y*width];
        assert(left_border);
    }
}

static void replay_nes(void)
{
    void (*run)(void)=dlsym(nes_core,"retro_run");
    void (*av_info)(struct retro_system_av_info *)=dlsym(nes_core,"retro_get_system_av_info");
    assert(run && av_info);
    struct retro_system_av_info av;
    av_info(&av);
    printf("option=%s reported=%ux%u ",overscan_value,
           av.geometry.base_width,av.geometry.base_height);

    if(input_replay) replay_state_input(run);
    else replay_opening_battle(run,&av);
    void (*unload)(void)=dlsym(nes_core,"retro_unload_game");
    void (*deinit)(void)=dlsym(nes_core,"retro_deinit");
    assert(unload && deinit);
    *core_output=NULL;
    unload();
    deinit();
}

int main(int argc, char **argv)
{
    assert(argc>=7 && argc<=9 && (argc==7 || !strcmp(argv[7],"receipt")));
    trim_edges=argc==9 && !strcmp(argv[8],"trim");
    if(argc==9) assert(trim_edges);
    if(trim_edges) device_rom="/usr/003/Final Fantasy II - Chaos Rush 2.2b.nes";
    core_path=argv[2];
    rom_path=argv[3];
    input_replay=getenv("D35_INPUT_REPLAY");
    map_vendor(argv[1]);
    patch(FRAME_FLASH,(uintptr_t)frame_flash);
    patch(KEY_MAPPING,(uintptr_t)key_mapping);
    patch(LOAD_PROC2,(uintptr_t)replay_nes);
    patch(PLAY_FRAME,(uintptr_t)accept_audio);
    if(input_replay) {
        patch(0x157c8,(uintptr_t)button_level);
        patch(0x1537c,(uintptr_t)no_usb);
        memcpy((void *)0x19b8bc,(void *)0x16b254,16*sizeof(unsigned));
    } else patch(INPUT_STATE,(uintptr_t)read_button);
    patch(0x11be4,(uintptr_t)quiet);
    patch(0x11d34,(uintptr_t)open_nes_core);
    patch(0x12010,(uintptr_t)resolve_nes);
    patch(0x11ce0,(uintptr_t)open_nes_rom);
    patch(0x11e0c,(uintptr_t)access);
    patch(0x11f38,(uintptr_t)sprintf);
    patch(0x11d64,(uintptr_t)strcpy);
    patch(0x11f74,(uintptr_t)strcmp);
    patch(0x11e3c,(uintptr_t)strstr);
    patch(0x11b84,(uintptr_t)fseek);
    patch(0x11e84,(uintptr_t)ftell);
    patch(0x11ed8,(uintptr_t)malloc);
    patch(0x11ddc,(uintptr_t)fread);
    patch(0x11f20,(uintptr_t)close_nes_file);
    patch(0x11b6c,(uintptr_t)free);
    patch(0x11c8c,(uintptr_t)memset);
    patch(0x11eb4,(uintptr_t)fwrite);
    patch(0x11fb0,(uintptr_t)fflush);
    patch(0x11df4,(uintptr_t)fileno);
    patch(0x11b18,(uintptr_t)fsync);
    patch(0x11ecc,(uintptr_t)memcpy);
    patch(0x164abc,(uintptr_t)allocate_trim);
    patch(0x164d58,(uintptr_t)release_trim);
    if(trim_edges) *(void **)0x1b81a8=&driver_token;
    strcpy((char *)WORK_PATH,"/usr/retro");
    strcpy((char *)*(uint32_t *)(GOT+0x274),"/usr/");
    *(retro_video_refresh_t *)DISPLAY_CALLBACK=capture_video;
    ((int (*)(const char *,unsigned))NES_LOAD)(device_rom,5);
    assert(width==(unsigned)atoi(argv[5]) && pitch==2*width);
    assert(receipt_published==(argc>=8));
    assert(!trim_live && trim_waits==(unsigned)trim_edges);
    if(receipt_published) {
        char expected[160];
        snprintf(expected,sizeof(expected),"boot_id=%s\noverscan=disabled\nsubmitted=%ux%u pitch=%u\n",
                 boot_id,width,height,pitch);
        assert(!strcmp(receipt,expected));
        printf("%s",receipt);
    }
    verify_scaler(argv[4]);
    FILE *output=fopen(argv[6],"wb");
    assert(output && fwrite(last_frame,sizeof(*last_frame),width*height,output)==width*height);
    assert(!fclose(output) && !dlclose(nes_core));
    return 0;
}
