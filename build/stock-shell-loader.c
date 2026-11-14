/* Owned launch code linked into the pinned stock menu ELF, ARM32 only.
 * All stock entry points and data below are bound to the source SHA in the
 * assembler. No preloaded library, proxy libretro core or loader daemon. */
#include <libretro.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <dirent.h>
#include "stock-shell-audio.h"

#define FN(at, ret, ...) ((ret (*)(__VA_ARGS__))(uintptr_t)(at))
#define VAR(at, type) (*(type *)(uintptr_t)(at))
#define ENTRY __attribute__((used, externally_visible))
#define OPEN FN(0x11d34, void *, const char *, int)
#define SYM FN(0x12010, void *, void *, const char *)
#define CLOSE FN(0x11c14, int, void *)
#define PUTS FN(0x11c20, int, const char *)
#define FOPEN FN(0x11ce0, FILE *, const char *, const char *)
#define FCLOSE FN(0x11f20, int, FILE *)
#define FREAD FN(0x11ddc, size_t, void *, size_t, size_t, FILE *)
#define FSEEK FN(0x11b84, int, FILE *, long, int)
#define FTELL FN(0x11e84, long, FILE *)
#define ALLOC FN(0x11ed8, void *, size_t)
#define FREE FN(0x11b6c, void, void *)
#define COPY FN(0x11ecc, void *, void *, const void *, size_t)
#define CMP FN(0x11fc8, int, const void *, const void *, size_t)
#define STRCMP FN(0x11f74, int, const char *, const char *)
#define ZERO FN(0x11c8c, void *, void *, int, size_t)
#define DISP FN(0xa6658, void, const void *, unsigned, unsigned, size_t)
#define STOCK_HANDLE VAR(0x1bd5dc, void *)
#define WORK FN(0x80bec, const char *, void)
#define SLOT (512u * 512u * 2u)
#define ROM_MAX (8u * 1024u * 1024u)
#define LAUNCHER "/d35-launcher1"
#define LOCALE VAR(0x1998d8, unsigned)
#define THEME_PACK LAUNCHER "/ui_en.bkp"
#define CLASSIC_SETTINGS_PACK LAUNCHER "/ui_classic.bkp"

enum battery_style { BATTERY_BARS, BATTERY_BARS_PERCENT, BATTERY_SOLID, BATTERY_STYLE_COUNT };

#define D35_VIEWPORT_COPY COPY
#define D35_VIEWPORT_COMPARE CMP
#include "starfox-viewport.h"

_Static_assert(2u * D35_STARFOX_FRAME_BYTES <= SLOT, "Star Fox display and reference fit in a slot");

struct session {
    void *core, *pool;
    void *audio_module;
    const struct d35_live_audio *audio;
    const unsigned *display_flags;
    int *stock_dsp;
    void (*wait_display)(void);
    void (*run)(void), (*unload)(void), (*deinit)(void);
    bool (*load)(const struct retro_game_info *);
    void (*av)(struct retro_system_av_info *);
    unsigned phase, w, h, shown, next, skip, recovery, auto_skip;
    bool previous, rgb565, starfox, zoomed;
    int16_t last[2];
    unsigned ticks, skipped, copies, repeats;
    unsigned display_ns;
    enum d35_presentation presentation;
    bool audio_running, audio_failed;
};
struct overlay {
    struct session game;
    bool auto_skip, select_held, accept_held;
    bool classic, applied_classic, new_art, save_failed, restore_highlight;
    unsigned extra_row;
    const void *baked_settings;
    uint16_t *settings_pixels;
    void *music;
    size_t music_bytes;
#ifdef D35_VESPER_LAUNCHER
    uint16_t *power_frame;
    bool start_held;
#ifdef D35_HOME_GRID
    const uint16_t *power_art;
    uint8_t battery_style;
#endif
#endif
};
/* Reserved by extending the pinned RW LOAD's zero-filled tail. */
#define S VAR(0x1c4100, struct overlay)
_Static_assert(sizeof(struct overlay) <= 0x100, "overlay must fit reserved storage");

#ifdef D35_HOME_GRID
static bool launcher_settings(bool from_classic);
static bool launcher_settings_available(void);
static void settings_reset_text_clip(void);
static void menu_button(uint16_t *frame,unsigned x,unsigned y,unsigned button);
enum { BUTTON_DPAD, BUTTON_ADJUST, BUTTON_A, BUTTON_B, BUTTON_START, BUTTON_SELECT };
static unsigned launcher_factory_navigation(unsigned row, unsigned key);
static bool launcher_factory_active(void);
static unsigned settings_key_poll(unsigned *held);
static bool menu_music_override(void);
static void menu_audio_lock(void);
static void menu_audio_unlock(void);
static bool start_builtin_music(void);
#endif

static bool suffix(char *out, size_t cap, const char *prefix, const char *tail)
{
    size_t i=0;
    while(*prefix && i+1<cap) out[i++]=*prefix++;
    if(*prefix) return false;
    while(*tail && i+1<cap) out[i++]=*tail++;
    out[i]=0;
    return !*tail;
}

static void *read_bytes(const char *path, size_t max, size_t *size)
{
    FILE *f=FOPEN(path,"rb");
    long n;
    void *data=NULL;
    *size=0;
    if(!f) return NULL;
    if(!FSEEK(f,0,SEEK_END) && (n=FTELL(f))>0 && (size_t)n<=max &&
       !FSEEK(f,0,SEEK_SET) && (data=ALLOC((size_t)n))) {
        if(FREAD(data,1,(size_t)n,f)==(size_t)n) *size=(size_t)n;
        else { FREE(data); data=NULL; }
    }
    FCLOSE(f);
    return data;
}

static bool is_tested_starfox(const uint8_t *rom, size_t bytes)
{
    enum { CART_BYTES = 1048576, COPIER_HEADER = 512, TITLE = 0x7fc0 };
    if(bytes == CART_BYTES + COPIER_HEADER) {
        rom += COPIER_HEADER;
        bytes -= COPIER_HEADER;
    }
    if(bytes != CART_BYTES || CMP(rom + TITLE, "STAR FOX             ", 21)) return false;
    /* Hash decoded content once at launch. The display crop is qualified for
     * this specific cartridge image, including copies with a copier header. */
    static const uint32_t crc_nibble[16] = {
        0x00000000, 0x1db71064, 0x3b6e20c8, 0x26d930ac,
        0x76dc4190, 0x6b6b51f4, 0x4db26158, 0x5005713c,
        0xedb88320, 0xf00f9344, 0xd6d6a3e8, 0xcb61b38c,
        0x9b64c2b0, 0x86d3d2d4, 0xa00ae278, 0xbdbdf21c
    };
    uint32_t crc = UINT32_MAX;
    while(bytes--) {
        crc ^= *rom++;
        crc = (crc >> 4) ^ crc_nibble[crc & 15];
        crc = (crc >> 4) ^ crc_nibble[crc & 15];
    }
    return (crc ^ UINT32_MAX) == UINT32_C(0x41a60b3f);
}

/* 32040 -> 44100 is 178 -> 245. Dividing all weights and the denominator
 * by 180 is exactly the v11 signed, truncating interpolation. */
static size_t snes_audio(const int16_t *in, size_t n)
{
    struct session *s=&S.game;
    int16_t out[2048*2];
    unsigned used=0, phase=s->phase;
    int l=s->last[0], r=s->last[1];
    size_t accepted=n;
    if(!in || !n || s->audio_failed) return 0;
    if(!s->previous) { l=*in++; r=*in++; s->previous=true; --n; }
    while(n--) {
        int a=*in++, b=*in++;
        do {
            out[2*used]=(int16_t)((l*245+(a-l)*(int)phase)/245);
            out[2*used+1]=(int16_t)((r*245+(b-r)*(int)phase)/245);
            phase+=178;
            if(++used==2048) {
                if(s->audio) {
                    if(s->audio->push(out,used)<0) { s->audio_failed=true; return 0; }
                } else FN(0xa2cc4, size_t, const int16_t *, size_t)(out,used);
                used=0;
            }
        } while(phase<245);
        phase-=245;
        l=a; r=b;
    }
    s->phase=phase; s->last[0]=(int16_t)l; s->last[1]=(int16_t)r;
    if(used) {
        if(s->audio) {
            if(s->audio->push(out,used)<0) { s->audio_failed=true; return 0; }
        } else FN(0xa2cc4, size_t, const int16_t *, size_t)(out,used);
    }
    return accepted;
}

static void snes_sample(int16_t l, int16_t r)
{ const int16_t pair[]={l,r}; snes_audio(pair,1); }

static void snes_video(const void *data, unsigned w, unsigned h, size_t pitch)
{
    struct session *s=&S.game;
    size_t bytes=2*w;
    if(!data || !w || !h || w>512 || h>512 || pitch<bytes || !s->pool) return;
    uint64_t began=s->audio?s->audio->now():0;
    const uint8_t *src=data;
    uint8_t *dst=(uint8_t *)s->pool+s->next*SLOT;
    if(s->shown && s->w==w && s->h==h) {
        const uint8_t *old=(uint8_t *)s->pool+(s->next^1)*SLOT;
        if(s->zoomed) old+=D35_STARFOX_FRAME_BYTES;
        unsigned y=0;
        /* Reject ordinary changed pictures before walking every scanline.
         * Samples are rejection-only; reuse still requires every byte. */
        const unsigned rows[3]={0,h/2,h-1};
        bool possible=true;
        for(unsigned i=0;i<3 && possible;++i) {
            const uint8_t *a=src+rows[i]*pitch, *b=old+rows[i]*bytes;
            for(unsigned x=0;x<bytes;x+=bytes/4?bytes/4:1)
                if(a[x]!=b[x]) { possible=false; break; }
        }
        if(possible) while(y<h && !CMP(src+y*pitch,old+y*bytes,bytes)) ++y;
        if(y==h) {
            ++s->repeats;
            s->presentation=D35_REPEATED_PICTURE;
            goto measured;
        }
    }
    if(s->audio) {
        /* The stock scaler has one source credit. The menu, thumbnail and
         * gameplay paths share this producer thread during the game. The
         * scaler can only release the credit between this load and DrawFrame. */
        if((__atomic_load_n(s->display_flags,__ATOMIC_ACQUIRE)&3u)!=1u) {
            s->presentation=D35_BUSY_DISPLAY;
            goto measured;
        }
    } else if(s->copies>=2) s->wait_display();
    s->zoomed=s->starfox && w==D35_STARFOX_WIDTH && h==D35_STARFOX_HEIGHT &&
        d35_starfox_border_is_black(src,pitch);
    /* Keep a copy of the original picture when presenting its expansion.
     * Duplicate detection must include the border as it can change in menus. */
    uint8_t *raw=s->zoomed?dst+D35_STARFOX_FRAME_BYTES:dst;
    if(pitch==bytes) COPY(raw,src,h*bytes);
    else for(unsigned y=0;y<h;++y) COPY(raw+y*bytes,src+y*pitch,bytes);
    if(s->zoomed) {
        unsigned view_width=w,view_height=h;
        const uint16_t *view=d35_starfox_viewport(raw,bytes,&view_width,&view_height);
        d35_starfox_expand_strided((uint16_t *)dst,view,w);
    }
    FN(0xa3438, void, const void *, unsigned, unsigned, size_t)(dst,w,h,bytes);
    s->w=w; s->h=h; s->shown=1; s->next^=1; ++s->copies;
    s->presentation=D35_SUBMITTED_PICTURE;
measured:
    if(s->audio) s->display_ns=(unsigned)(s->audio->now()-began);
}

static bool snes_environment(unsigned cmd, void *data)
{
    switch(cmd) {
    case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT:
        if(!data || *(enum retro_pixel_format *)data!=RETRO_PIXEL_FORMAT_RGB565) return false;
        S.game.rgb565=true;
        return true;
    case RETRO_ENVIRONMENT_SET_GEOMETRY:
        /* Stock cmd 37 writes past this structure. Video carries dimensions. */
        return data!=NULL;
    case RETRO_ENVIRONMENT_GET_AUDIO_VIDEO_ENABLE:
        if(!data) return false;
        *(int *)data=S.game.skip?2:3;
        return true;
    case RETRO_ENVIRONMENT_GET_CAN_DUPE:
        if(!data) return false;
        *(bool *)data=true;
        return true;
    case RETRO_ENVIRONMENT_GET_CORE_OPTIONS_VERSION:
        if(!data) return false;
        *(unsigned *)data=0;
        return true;
    case RETRO_ENVIRONMENT_GET_VARIABLE:
        if(!data) return false;
        ((struct retro_variable *)data)->value=NULL;
        return false;
    case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE:
        if(!data) return false;
        *(bool *)data=false;
        return true;
    case RETRO_ENVIRONMENT_SET_VARIABLES:
    case RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS:
        return true;
    default:
        return false;
    }
}

static void snes_tick(void)
{
    struct session *s=&S.game;
    if(s->audio) {
        if(!s->audio_running) {
            char directory[384];
            if(!suffix(directory,sizeof(directory),WORK(),LAUNCHER) ||
               s->audio->start(directory)<0) { s->audio_failed=true; return; }
            s->audio_running=true;
        }
        s->skip=0;
        s->presentation=D35_NO_PICTURE;
        s->display_ns=0;
        if(s->audio->admit()<0) { s->audio_failed=true; return; }
        s->run();
        if(s->audio->tick(s->presentation,s->display_ns)<0) s->audio_failed=true;
        return;
    }
    /* The stock loop already computed lateness for this tick. Keep two
     * rendered ticks between drops. Never suppress CPU, APU or input. */
    s->skip=s->shown && !s->recovery && VAR(0x1bd620, const int)>0;
    if(s->skip) { s->recovery=2; ++s->skipped; }
    else if(s->recovery) --s->recovery;
    ++s->ticks;
    s->run();
    s->skip=0;
}

ENTRY void *stock_resolve_run(void *core, const char *symbol)
{
    if(core==S.game.core && (S.game.auto_skip || S.game.audio)) return snes_tick;
    return SYM(core,symbol);
}

/* With an audio owner, its playable reserve gates production. The vendor
 * loop still handles input, watchdog, pause and core lifecycle. */
ENTRY int stock_game_sleep(unsigned microseconds)
{
    return S.game.audio?0:FN(0x11f08,int,unsigned)(microseconds);
}

ENTRY int stock_pause_audio(void)
{
    struct session *s=&S.game;
    if(s->audio_running) {
        int result=s->audio->stop("pause");
        s->audio_running=false;
        if(result<0) { s->audio_failed=true; return 1; }
    }
    if(s->audio && s->copies) s->wait_display();
    int result=FN(0x9b9f4,int,void)();
    if(s->audio) s->shown=0; /* The pause UI replaced the last picture. */
    return result;
}

ENTRY bool stock_audio_fault(void)
{
    FN(0x13fd4,void,void)();
    return S.game.audio_failed;
}

/* Load_Proc2's existing cleanup handles unload/deinit and returns to the
 * library. Preserve its frame and callee-saved registers on both paths. */
__attribute__((naked)) ENTRY void stock_audio_heartbeat(void)
{
    __asm__ volatile(
        "push {r4,lr}\n\tbl stock_audio_fault\n\tpop {r4,lr}\n\t"
        "cmp r0,#0\n\tbxeq lr\n\t"
        "movw ip,#0x4820\n\tmovt ip,#0xa\n\tbx ip");
}

#ifdef D35_STARFOX_NATIVE_AUDIO
static bool starfox_audio_unavailable(const char *reason)
{
    char path[384];
    if(suffix(path,sizeof(path),WORK(),LAUNCHER "/starfox-audio-handoff.log")) {
        FILE *file=FOPEN(path,"a");
        if(file) {
            size_t length=0;
            while(reason[length]) ++length;
            FN(0x11eb4,size_t,const void *,size_t,size_t,FILE *)(reason,1,length,file);
            FN(0x11fb0,int,FILE *)(file);
            FN(0x11b18,int,int)(FN(0x11df4,int,FILE *)(file));
            FCLOSE(file);
        }
    }
    return false;
}

static bool open_starfox_audio(void)
{
    struct session *s=&S.game;
    char path[384];
    void *driver=VAR(0x1b81a8,void *);
    if(!suffix(path,sizeof(path),WORK(),LAUNCHER "/libs/d35-starfox-audio.so")) return false;
    s->audio_module=OPEN(path,2);
    if(!s->audio_module) return starfox_audio_unavailable("audio_module_open_failed\n");
    const struct d35_live_audio *audio=SYM(s->audio_module,"d35_starfox_audio");
    s->display_flags=SYM(driver,"DisplayThreadflag");
    int *dsp=SYM(driver,"DSP");
    int (*release_oss)(void)=SYM(driver,"sound_driver_deinit");
    /* mui_run_game already waits for the menu sound thread to go idle. */
    if(!audio || !s->display_flags || !dsp || !release_oss)
        return starfox_audio_unavailable("audio_or_driver_symbol_missing\n");
    if(VAR(0x19cb7c,const volatile unsigned))
        return starfox_audio_unavailable("menu_audio_thread_still_active\n");
    if(*dsp>=0) {
        if(release_oss()<0) return starfox_audio_unavailable("stock_pcm_close_failed\n");
        *dsp=-1; /* Stock StopSound can still be called during pause. */
        s->stock_dsp=dsp;
    }
    s->audio=audio;
    return true;
}
#endif

static void release_snes(bool close_core)
{
    struct session *s=&S.game;
    if(s->audio_running && s->audio->stop(s->audio_failed?"audio_fault":"exit")<0)
        PUTS("D35: Star Fox native audio test failed. See the audio timing log.");
    if(s->pool) {
        if(s->copies) s->wait_display();
        /* DrawFrame retains the pointer for pause and previews. Clear it only
         * after the stock gameplay loop and its display jobs have finished. */
        VAR(0x1bd5f8, const void *)=NULL;
        FN(0x164d58, void, void *)(s->pool);
    }
    if(s->audio_module) CLOSE(s->audio_module);
    if(s->stock_dsp) FN(0xa6844,void,void)();
    if(close_core && s->core) CLOSE(s->core);
    STOCK_HANDLE=NULL;
    ZERO(s,0,sizeof(*s));
}

ENTRY int open_snes(const char *unused)
{
    (void)unused;
    struct session *s=&S.game;
    char path[384];
    if(!suffix(path,sizeof(path),WORK(),LAUNCHER "/libs/d35-snes.so")) return 0;
    s->core=OPEN(path,2);
    if(!s->core) goto failed;
    void *driver=VAR(0x1b81a8, void *);
    if(!driver || !(s->wait_display=SYM(driver,"WaitDisp"))) goto failed;
    s->pool=FN(0x164abc, void *, size_t)(2*SLOT);
    if(!s->pool) goto failed;

    void (*set_env)(retro_environment_t)=SYM(s->core,"retro_set_environment");
    void (*set_video)(retro_video_refresh_t)=SYM(s->core,"retro_set_video_refresh");
    void (*set_audio)(retro_audio_sample_t)=SYM(s->core,"retro_set_audio_sample");
    void (*set_batch)(retro_audio_sample_batch_t)=SYM(s->core,"retro_set_audio_sample_batch");
    void (*set_poll)(retro_input_poll_t)=SYM(s->core,"retro_set_input_poll");
    void (*set_input)(retro_input_state_t)=SYM(s->core,"retro_set_input_state");
    void (*init)(void)=SYM(s->core,"retro_init");
    unsigned (*version)(void)=SYM(s->core,"retro_api_version");
    s->av=SYM(s->core,"retro_get_system_av_info");
    s->load=SYM(s->core,"retro_load_game");
    s->unload=SYM(s->core,"retro_unload_game");
    s->deinit=SYM(s->core,"retro_deinit");
    s->run=SYM(s->core,"retro_run");
    if(!set_env || !set_video || !set_audio || !set_batch || !set_poll || !set_input ||
       !init || !version || !s->av || !s->load || !s->unload || !s->deinit || !s->run ||
       !SYM(s->core,"retro_get_region") || version()!=RETRO_API_VERSION) goto failed;
    FN(0x892c4, void, void)();
    ZERO((void *)0x1be32c,0,16);
    VAR(0x1bd664, unsigned)=VAR(0x1b8098, unsigned)=VAR(0x1bd684, unsigned)=0;
    VAR(0x19cb80, unsigned)=VAR(0x1bd610, unsigned)=0;
    STOCK_HANDLE=s->core;
    s->auto_skip=S.auto_skip;
    set_env(snes_environment); set_video(snes_video);
    set_audio(snes_sample); set_batch(snes_audio);
    set_poll((retro_input_poll_t)0xa2cc0); set_input((retro_input_state_t)0xa2f0c);
    init();
    return 1;
failed:
    release_snes(true);
    PUTS("D35: direct SNES core or display unavailable");
    return 0;
}

ENTRY int run_snes(const char *path, unsigned kind)
{
    struct session *s=&S.game;
    size_t bytes=0;
    void *rom;
    if(kind>=0x10000) {
        rom=VAR(0x1bba7c, void *); bytes=VAR(0x1bba8c, size_t);
        VAR(0x1bba7c, void *)=NULL; VAR(0x1bba8c, size_t)=0;
    } else rom=read_bytes(path,ROM_MAX,&bytes);
    char *name=(void *)0x1bd688;
    bool loaded=false;
    struct retro_system_av_info av;
    if(!rom || bytes<32768 || bytes>ROM_MAX || !suffix(name,256,path,"")) {
        if(rom) FREE(rom);
        PUTS("D35: SNES content could not be read");
        return -1;
    }
    if(!open_snes(NULL)) { FREE(rom); return -1; }
    s->starfox=is_tested_starfox(rom,bytes);
    {
        const struct retro_game_info game={name,rom,bytes,NULL};
        loaded=s->load(&game);
    }
    if(rom) FREE(rom); /* This exact core consumes memory during load_game. */
    if(loaded) {
        if(s->starfox) {
            void (*enable_cache)(bool)=SYM(s->core,"d35_raster_set_enabled");
            if(enable_cache) enable_cache(true);
        }
        s->av(&av);
        if(s->rgb565 && av.timing.sample_rate==32040.0) {
#ifdef D35_STARFOX_NATIVE_AUDIO
            if(s->starfox && !open_starfox_audio()) {
                PUTS("D35: Star Fox native audio or stock device handoff unavailable");
                goto rejected;
            }
#endif
            FN(0xa426c, void, void)(); /* Stock loop owns unload/deinit/dlclose. */
            FN(0x11be4, int, const char *, ...)("D35 direct: copies=%u equal=%u auto_ticks=%u dropped=%u\n",
                                              s->copies,s->repeats,s->ticks,s->skipped);
            release_snes(false);
            return 0;
        }
#ifdef D35_STARFOX_NATIVE_AUDIO
rejected:
#endif
        s->unload();
    }
    s->deinit();
    release_snes(true);
    PUTS("D35: SNES rejected content or negotiated an unsupported format");
    return -1;
}

/* Direct-core states are private to this core identity. All other systems
 * retain their original state paths. */
static bool state_path(char path[1024],const char *old)
{ return suffix(path,1024,old,".d35-70d8851"); }

ENTRY int stock_save_state(const char *original)
{
    char path[1024];
    if(!S.game.core) return FN(0xa37b0,int,const char *)(original);
    return state_path(path,original)?FN(0xa37b0,int,const char *)(path):-1;
}

ENTRY int stock_load_state(const char *original)
{
    char path[1024];
    if(!S.game.core) return FN(0xa3944,int,const char *)(original);
    if(!state_path(path,original)) return 0;
    int loaded=FN(0xa3944,int,const char *)(path);
    if(loaded) { S.game.previous=false; S.game.phase=0; S.game.recovery=0; }
    return loaded;
}

ENTRY int stock_state_access(const char *original,int mode)
{
    char path[1024];
    if(!S.game.core) return FN(0x11e0c,int,const char *,int)(original,mode);
    return state_path(path,original)?FN(0x11e0c,int,const char *,int)(path,mode):-1;
}

ENTRY FILE *stock_state_fopen(const char *original,const char *mode)
{
    char path[1024];
    if(!S.game.core) return FOPEN(original,mode);
    return state_path(path,original)?FOPEN(path,mode):NULL;
}

ENTRY void stock_save_snap(void)
{ if(!S.game.core) FN(0x9c9c8,void,void)(); }

static unsigned char search_character(unsigned char c)
{
    if(c>='A' && c<='Z') return c+('a'-'A');
    if((c>='a' && c<='z') || (c>='0' && c<='9') || c>=128) return c;
    return 0;
}

static bool search_field(const char *begin, const char *end,
                         const unsigned char *query, size_t length)
{
    for(const char *start=begin; start<end; ++start) {
        if(search_character(*start)!=query[0]) continue;
        size_t matched=1;
        for(const char *p=start+1; p<end && matched<length; ++p) {
            unsigned char c=search_character(*p);
            if(c && c!=query[matched]) break;
            if(c) ++matched;
        }
        if(matched==length) return true;
    }
    return false;
}

ENTRY int stock_search_row(const char *original_field, const char *query, const char *row)
{
    unsigned char normalized[128];
    size_t length=0;
    for(size_t i=0; i<sizeof(normalized) && query[i]; ++i) {
        unsigned char c=search_character(query[i]);
        if(c) normalized[length++]=c;
    }
    if(!length) return 1;
    /* Index rows hold the path, display title and three alternate names.
     * The basename can match without exposing the system directory or suffix. */
    for(unsigned field=0; field<5; ++field) {
        const char *end=row;
        while(*end && *end!=';' && *end!='\r' && *end!='\n') ++end;
        const char *begin=row, *last=end;
        if(!field) {
            for(const char *p=row; p<end; ++p) {
                if(*p=='/' || *p=='\\') { begin=p+1; last=end; }
                else if(*p=='.') last=p;
            }
        }
        if(search_field(begin,last,normalized,length)) return 1;
        if(*end!=';') break;
        row=end+1;
    }
    /* Preserve the vendor's subsequence matching for localized initials. */
    if(VAR(0x1998d8, unsigned)!=1)
        return FN(0x80acc, int, const char *, const char *)(original_field,query)!=0;
    return 0;
}

/* At the pinned call in mui_SearchThread, r11 holds the current index row.
 * r0 and r1 carry the vendor-selected field and the query. */
__attribute__((naked)) ENTRY void stock_search_match(void)
{
    __asm__ volatile("mov r2, r11\n\tb stock_search_row");
}

ENTRY int stock_parse_search_page(unsigned offset, char *end)
{
    *end='\0';
    return FN(0x8181c, int, unsigned)(offset);
}

/* The full-page path must terminate the last copied row before parsing.
 * r10 points at the next unused result byte at this call site. */
__attribute__((naked)) ENTRY void stock_search_finish_page(void)
{
    __asm__ volatile("mov r1, r10\n\tb stock_parse_search_page");
}

struct art_block {
    uint32_t offset;
    uint16_t width, height, left, top, right, bottom;
};

#define SETTINGS_ART VAR(0x199908, struct art_block *)

/* Only mui_LoadUIResource's locale archive open is redirected. Shared
 * fonts, language metadata, game files and stock packs keep their paths. */
ENTRY void *stock_theme_zip(const char *path,unsigned size,unsigned mode,const char *member)
{
    void *(*open_zip)(const char *,unsigned,unsigned)=FN(0xa2730,void *,const char *,unsigned,unsigned);
#ifdef D35_HOME_GRID
    if(path && !size && mode==2 && !S.applied_classic && S.new_art) {
        char stock[384], themed[384], filename[16];
        const char *locale=LOCALE<11?VAR(0x199938+4*LOCALE,const char *):NULL;
        if(locale && !CMP(locale+32,"ui_",3) && !CMP(locale+37,".bkp",5)) {
            filename[0]='/';
            COPY(filename+1,locale+32,10);
        } else COPY(filename,"/ui_en.bkp",11);
        if(suffix(stock,sizeof(stock),WORK(),filename) && !STRCMP(path,stock) &&
           suffix(themed,sizeof(themed),WORK(),THEME_PACK)) {
            void *zip=open_zip(themed,size,mode);
            if(zip) return zip;
        }
    }
    (void)member;
#else
    const char *alternate=NULL;
    if(LOCALE==1) {
        if(!S.applied_classic && S.new_art) alternate=THEME_PACK;
        else if(member && !STRCMP(member,"setting.raw")) alternate=CLASSIC_SETTINGS_PACK;
    }
    if(path && !size && mode==2 && alternate) {
        char stock[384], themed[384];
        const char *work=WORK();
        if(suffix(stock,sizeof(stock),work,"/ui_en.bkp") && !STRCMP(path,stock) &&
           suffix(themed,sizeof(themed),work,alternate)) {
            void *zip=open_zip(themed,size,mode);
            if(zip) return zip;
        }
    }
#endif
    return open_zip(path,size,mode);
}

/* mui_LoadUIResource keeps the member name in r6 at its OpenZipU call. */
__attribute__((naked)) ENTRY void stock_theme_resource(void)
{
    __asm__ volatile("mov r3, r6\n\tb stock_theme_zip");
}

static uint16_t *full_art_block(struct art_block *art, unsigned size, unsigned index)
{
    const unsigned frame_bytes=640u*480u*2u;
    if(size<sizeof(*art) || art[0].offset<(index+1)*sizeof(*art) ||
       art[0].offset>size || size<frame_bytes) return NULL;
    const struct art_block *b=&art[index];
    if(b->width!=640 || b->height!=480 || b->left || b->top ||
       b->right!=640 || b->bottom!=480 || b->offset<art[0].offset ||
       (b->offset&1) || b->offset>size-frame_bytes) return NULL;
    return (uint16_t *)((uint8_t *)art+b->offset);
}

static bool baked_settings_rows(struct art_block *art,unsigned size)
{
    const unsigned records=13;
    if(!full_art_block(art,size,0) || art[0].offset!=records*sizeof(*art)) return false;
    unsigned shift=art[1].top==116?18:0;
    for(unsigned i=1;i<records;++i) {
        const struct art_block *row=&art[i];
        unsigned y=(i<5?134+50*(i-1):i<9?339:382)-shift;
        unsigned height=i<5?54:39, bytes=2u*460u*height;
        if(row->width!=640 || row->height!=480 || row->left!=90 || row->right!=550 ||
           row->top!=y || row->bottom!=y+height || (row->offset&1) ||
           row->offset<art[0].offset || row->offset>size-bytes) return false;
    }
    return true;
}

#ifdef D35_HOME_GRID
static bool battery_settings(const struct art_block *art)
{ return art && art[0].offset==19*sizeof(*art); }

static bool ordered_settings(const struct art_block *art)
{ return battery_settings(art) || (art && art[0].offset==15*sizeof(*art)); }

static bool grid_settings_rows(struct art_block *art,unsigned size)
{
    if(!ordered_settings(art) || !full_art_block(art,size,0)) return false;
    unsigned shift=art[1].top==116?18:0;
    bool battery=battery_settings(art);
    for(unsigned i=1;i<(battery?19u:15u);++i) {
        const struct art_block *row=&art[i];
        unsigned y=i<4?134+50*(i-1):battery?
            (i==4?411:i<9?287:i<13?318:i<15?380:349):
            (i==4?404:i<9?288:i<13?326:365);
        y-=shift;
        unsigned height=i<4?54:battery?31:37, bytes=2u*460u*height;
        if(row->width!=640 || row->height!=480 || row->left!=90 || row->right!=550 ||
           row->top!=y || row->bottom!=y+height || (row->offset&1) ||
           row->offset<art[0].offset || size<bytes || row->offset>size-bytes) return false;
    }
    return true;
}
#endif

static void settings_heading(uint16_t *frame)
{
    /* Lowercase s at the original title's size and baseline. */
    static const char glyph_s[17][16]={
        "....+######+...", "...########+...", "..####++.+#+...",
        "..###..........", "..###..........", "..###+.........",
        "..+###++.......", "...######+.....", "....+######....",
        "......+#####...", "........+###+..", ".........###+..",
        ".........+##+..", "..#++...+###+..", ".+#########+...",
        "..########+....", "....++++......."
    };
    for(unsigned y=0; y<17; ++y)
        for(unsigned x=0; x<15; ++x) {
            char shade=glyph_s[y][x];
            if(shade!='.') frame[(20+y)*640+144+x]=shade=='#'?0xffff:0xa534;
        }
}

static void settings_tile(uint16_t *frame, const uint16_t *favorites)
{
    /* Reuse the beveled final S from the matching Favorites tile. The
     * surrounding colored pixels belong to its background. */
    for(unsigned y=0; y<40; ++y)
        for(unsigned x=0; x<32; ++x) {
            uint16_t p=favorites[(114+y)*640+312+x];
            unsigned r=(p>>11)*2, g=(p>>5)&63, b=(p&31)*2;
            if(r>=30 && g>=30 && b>=30 && r+8>=g && g+8>=r &&
               b+8>=g && g+8>=b && r+8>=b && b+8>=r)
                frame[(103+y)*640+293+x]=p;
        }
    for(unsigned y=147; y<=150; ++y)
        for(unsigned x=291; x<=326; ++x) frame[y*640+x]=frame[y*640+283];
}

ENTRY int stock_load_art(struct art_block **art, const char *name)
{
    int loaded=FN(0x82aa8, int, struct art_block **, const char *)(art,name);
    if(!loaded || !*art) return loaded;
    unsigned size=VAR(0x19bc0c, unsigned);
    if(!STRCMP(name,"type.raw")) {
        uint16_t *tile=full_art_block(*art,size,17);
        const uint16_t *favorites=full_art_block(*art,size,13);
        /* Apply the stock artwork correction only to the original frame. */
        if(tile && favorites && tile[0]==0x0821 && tile[1]==0x0021 &&
           tile[2]==0x0821 && tile[3]==0x0001) settings_tile(tile,favorites);
    } else if(!STRCMP(name,"setting.raw")) {
        bool baked=baked_settings_rows(*art,size);
#ifdef D35_HOME_GRID
        baked=baked || grid_settings_rows(*art,size);
#endif
        S.baked_settings=baked?*art:NULL;
        uint16_t *frame=full_art_block(*art,size,0);
        if(LOCALE==1 && !S.baked_settings && frame && frame[0]==0x39e9 && frame[1]==0x31ea &&
           frame[2]==0x3a09 && frame[3]==0x31ea) settings_heading(frame);
    }
    return loaded;
}

/* The locale list and its on-device chooser remain stock. English is
 * index one; honor all explicit valid language selections. */
ENTRY long stock_language(const char *value, char **end, int base)
{
    char *tail;
    if(!value || !*value) return 1;
    long selected=FN(0x11b60,long,const char *,char **,int)(value,&tail,base);
    if(end) *end=tail;
    return tail!=value && !*tail && selected>=0 && selected<=10?selected:1;
}

ENTRY void stock_load_settings(void)
{
    char path[384];
    S.auto_skip=false;
    S.classic=false;
    S.new_art=false;
#ifdef D35_HOME_GRID
    S.battery_style=BATTERY_BARS;
#endif
    if(suffix(path,sizeof(path),WORK(),LAUNCHER "/d35-loader.cfg")) {
        FILE *f=FOPEN(path,"rb");
        char settings[3]={0};
        if(f) {
            size_t bytes=FREAD(settings,1,sizeof(settings),f);
            S.auto_skip=bytes && settings[0]=='1';
            S.classic=bytes>=2 && settings[1]=='C';
#ifdef D35_HOME_GRID
            if(bytes==3 && settings[2]=='P') S.battery_style=BATTERY_BARS_PERCENT;
            if(bytes==3 && settings[2]=='S') S.battery_style=BATTERY_SOLID;
#endif
            FCLOSE(f);
        }
    }
    if(suffix(path,sizeof(path),WORK(),THEME_PACK)) {
        FILE *f=FOPEN(path,"rb");
        char magic[4];
        if(f) {
            S.new_art=FREAD(magic,1,sizeof(magic),f)==sizeof(magic) && !CMP(magic,"WQW\003",4);
            FCLOSE(f);
        }
    }
    S.applied_classic=S.classic;
    LOCALE=1;
    FN(0x81da0,void,void)();
}

/* Publish settings only after the complete new file is flushed. */
static bool save_config_bytes(const char *path,const void *data,size_t bytes)
{
    char tmp[400];
    int (*replace)(const char *,const char *)=SYM(NULL,"rename");
    if(!replace || !suffix(tmp,sizeof(tmp),path,".tmp")) return false;
    FILE *f=FOPEN(tmp,"wb");
    if(!f) return false;
    bool ok=FN(0x11eb4,size_t,const void *,size_t,size_t,FILE *)(data,1,bytes,f)==bytes &&
        !FN(0x11fb0,int,FILE *)(f) && !FN(0x11b18,int,int)(FN(0x11df4,int,FILE *)(f));
    if(FCLOSE(f)) ok=false;
    return ok && !replace(tmp,path);
}

static bool save_options(bool auto_skip,bool classic,unsigned battery_style)
{
    char path[384];
    const char settings[]={auto_skip?'1':'0',classic?'C':'N',battery_style==BATTERY_SOLID?'S':'P'};
    return suffix(path,sizeof(path),WORK(),LAUNCHER "/d35-loader.cfg") &&
        save_config_bytes(path,settings,battery_style==BATTERY_BARS?2:3);
}

/* Compact glyphs for the two launcher settings rows and the footer. */
static const uint8_t glyph[26][7]={
    {14,17,17,31,17,17,17}, {30,17,17,30,17,17,30}, {14,17,16,16,16,17,14},
    {30,17,17,17,17,17,30}, {31,16,16,30,16,16,31}, {31,16,16,30,16,16,16},
    {14,17,16,23,17,17,15}, {17,17,17,31,17,17,17}, {14,4,4,4,4,4,14},
    {7,2,2,2,18,18,12}, {17,18,20,24,20,18,17}, {16,16,16,16,16,16,31},
    {17,27,21,21,17,17,17}, {17,25,21,19,17,17,17}, {14,17,17,17,17,17,14},
    {30,17,17,30,16,16,16}, {14,17,17,17,21,18,13}, {30,17,17,30,20,18,17},
    {15,16,16,14,1,1,30}, {31,4,4,4,4,4,4}, {17,17,17,17,17,17,14},
    {17,17,17,17,17,10,4}, {17,17,17,21,21,21,10}, {17,17,10,4,10,17,17},
    {17,17,10,4,4,4,4}, {31,1,2,4,8,16,31}
};

static void settings_text(uint16_t *p,unsigned left,unsigned top,const char *text,
                          unsigned scale,uint16_t color)
{
    for(unsigned i=0;text[i];++i) {
        if(text[i]<'A' || text[i]>'Z') continue;
        for(unsigned y=0;y<7;++y) for(unsigned x=0;x<5;++x)
            if(glyph[text[i]-'A'][y]&(16u>>x))
                for(unsigned dy=0;dy<scale;++dy) for(unsigned dx=0;dx<scale;++dx)
                    p[(top+scale*y+dy)*640+left+scale*(6*i+x)+dx]=color;
    }
}

static void settings_box(uint16_t *p,unsigned x0,unsigned y0,unsigned x1,unsigned y1,uint16_t color)
{
    for(unsigned y=y0;y<y1;++y) for(unsigned x=x0;x<x1;++x) p[y*640+x]=color;
}

static bool button_down(unsigned pin)
{ return FN(0x157c8,int,unsigned)(pin)==0; }

#ifdef D35_HOME_GRID
static bool launcher_escape(unsigned keys)
{ return keys==9 && button_down(0x206); }

ENTRY unsigned launcher_menu_key(void)
{
    unsigned keys=FN(0x86368,unsigned,void)();
    return launcher_escape(keys)?0x4000:keys;
}
#endif

#ifdef D35_VESPER_LAUNCHER
#include "stock-shell-power.h"
#endif

static void settings_options(uint16_t *p)
{
    bool classic=S.applied_classic || LOCALE!=1 || !S.new_art;
    uint16_t accent=classic?0x5fdf:0xfe49;
    settings_box(p,62,340,578,445,classic?0x1149:0x08a3);
    const char *labels[]={"FRAME SKIP", "THEME"};
    const char *values[]={S.auto_skip?"AUTO":"OFF", S.classic || !S.new_art?"CLASSIC":"NEW"};
    for(unsigned i=0;i<2;++i) {
        unsigned top=346+36*i;
        bool selected=S.extra_row==i+1;
        settings_box(p,90,top,550,top+32,selected?accent:0x326b);
        settings_box(p,91,top+1,549,top+31,selected?0x31ec:0x1106);
        settings_text(p,124,top+9,labels[i],2,0xffff);
        settings_text(p,405,top+9,values[i],2,accent);
    }
    settings_text(p,111,423,"A CHANGE  B BACK",2,0xffff);
    const char *hint=S.save_failed?"SAVE FAILED":!S.new_art?"NEW ART MISSING":
        LOCALE!=1?"NEW ART IN ENGLISH":"BACK TO APPLY";
    settings_text(p,338,423,hint,2,accent);
}

static void baked_options(uint16_t *p,struct art_block *art)
{
    void (*blit)(void *,size_t,struct art_block *,unsigned)=FN(0x803a8,void,void *,size_t,struct art_block *,unsigned);
    blit(p,1280,art,5+2*(S.extra_row==1)+S.auto_skip);
    blit(p,1280,art,9+2*(S.extra_row==2)+(S.classic || !S.new_art));
#ifdef D35_HOME_GRID
    if(battery_settings(art)) {
        blit(p,1280,art,13+(S.extra_row==4));
        blit(p,1280,art,15+2*(S.extra_row==3)+(S.battery_style!=BATTERY_BARS));
    } else if(ordered_settings(art)) blit(p,1280,art,13+(S.extra_row==3));
#endif
    const uint16_t *base=(const uint16_t *)((const uint8_t *)art+art[0].offset);
    for(unsigned y=69;y<86;++y) COPY(p+y*640+105,base+y*640+105,430u*2u);
    if(S.save_failed) settings_text(p,105,70,"SAVE FAILED",2,0xfe49);
    else if(!S.new_art) settings_text(p,105,70,"NEW ART MISSING",2,0xfe49);
}

ENTRY void stock_settings_frame(uint16_t *p,unsigned w,unsigned h,size_t pitch)
{
#ifdef D35_HOME_GRID
    if(launcher_factory_active()) return;
    if(S.applied_classic && launcher_settings_available()) {
        if(p && w==640 && h==480 && pitch==1280) {
            shutdown_wait()();
            settings_reset_text_clip();
            menu_button(p,298,13,BUTTON_START);
            FN(0x85c94,int,void *,int,int,int,unsigned,const char *)(
                p,335,-2,20,0xffff,"Launcher options");
        }
        DISP(p,w,h,pitch);
        return;
    }
#endif
    if(p && w==640 && h==480 && pitch==1280) {
        void *driver=VAR(0x1b81a8,void *);
        void (*wait)(void)=driver?SYM(driver,"WaitDisp"):NULL;
        if(wait) {
            wait();
            if(SETTINGS_ART && S.extra_row
#ifdef D35_HOME_GRID
               && !ordered_settings(S.baked_settings)
#endif
            )
                FN(0x80424,void,void *,size_t,struct art_block *,unsigned)(p,pitch,SETTINGS_ART,4);
            else if(SETTINGS_ART && S.restore_highlight)
                FN(0x803a8,void,void *,size_t,struct art_block *,unsigned)(p,pitch,SETTINGS_ART,
#ifdef D35_HOME_GRID
                    ordered_settings(S.baked_settings)?3:
#endif
                    4);
#ifdef D35_HOME_GRID
            if(ordered_settings(S.baked_settings) && S.extra_row)
                FN(0x80424,void,void *,size_t,struct art_block *,unsigned)(p,pitch,SETTINGS_ART,3);
#endif
            S.restore_highlight=false;
            if(SETTINGS_ART && S.baked_settings==SETTINGS_ART) baked_options(p,SETTINGS_ART);
            else settings_options(p);
            S.settings_pixels=p;
#ifdef D35_VESPER_LAUNCHER
            if(shutdown_available()
#ifdef D35_HOME_GRID
               && !ordered_settings(S.baked_settings)
#endif
            ) {
                settings_box(p,407,10,622,45,0x08a3);
                settings_text(p,419,20,"START POWER OFF",2,0xaf9e);
            }
            if(S.power_frame) return;
#endif
        }
    }
    DISP(p,w,h,pitch);
}

static void change_option(unsigned row)
{
    bool auto_skip=row==1?!S.auto_skip:S.auto_skip;
    bool classic=row==2?!S.classic:S.classic;
    unsigned battery_style=BATTERY_BARS;
#ifdef D35_HOME_GRID
    battery_style=S.battery_style;
    if(row==3) battery_style=(battery_style+1==BATTERY_STYLE_COUNT)?BATTERY_BARS:battery_style+1;
#endif
#ifndef D35_HOME_GRID
    if(row==2 && !S.new_art) return;
#endif
    S.save_failed=!save_options(auto_skip,classic,battery_style);
    if(!S.save_failed) {
        S.auto_skip=auto_skip;
        S.classic=classic;
#ifdef D35_HOME_GRID
        S.battery_style=battery_style;
#endif
    }
}

ENTRY unsigned stock_settings_input(unsigned stock_row)
{
#ifdef D35_HOME_GRID
    unsigned keys=launcher_menu_key();
    if(launcher_factory_active()) return launcher_factory_navigation(stock_row,keys);
    if(S.applied_classic && launcher_settings_available()) {
        if(!button_down(0x30c)) S.start_held=false;
        if(keys==8 && !S.start_held) {
            S.start_held=true;
            /* The stock B path releases its locals before we open our list. */
            S.extra_row=1;
            return 0x4000;
        }
        return keys;
    }
#else
    unsigned keys=FN(0x86368,unsigned,void)();
#endif
    if(!button_down(0x30f)) S.select_held=false;
    if(!button_down(0x204)) S.accept_held=false;
#ifdef D35_VESPER_LAUNCHER
    if(!button_down(0x30c)) S.start_held=false;
    if(S.power_frame) {
        if(keys==0x4000) shutdown_cancel();
        else if(keys==0x2000 && !S.accept_held) {
            S.accept_held=true;
            shutdown_confirm();
        }
        return 0;
    }
    if(keys==8 && S.settings_pixels && shutdown_available()) {
        if(!S.start_held) shutdown_open();
        S.start_held=true;
        return 0;
    }
#endif
    if(keys==1) {
        if(!S.select_held) {
            change_option(1);
            if(S.settings_pixels) stock_settings_frame(S.settings_pixels,640,480,1280);
        }
        S.select_held=true;
        return 0;
    }
#ifdef D35_HOME_GRID
    if(S.settings_pixels && ordered_settings(S.baked_settings)) {
        unsigned power_row=battery_settings(S.baked_settings)?4:3;
        if(keys==0x40 && stock_row==2) {
            if(S.extra_row==power_row) { S.extra_row=0; return keys; }
            ++S.extra_row;
        } else if(keys==0x10 && stock_row==3) {
            S.extra_row=power_row;
            return keys;
        } else if(keys==0x10 && S.extra_row) {
            S.restore_highlight=--S.extra_row==0;
        } else if(keys==0x2000 && S.extra_row) {
            if(S.accept_held) return 0;
            S.accept_held=true;
            if(S.extra_row==power_row) {
                if(shutdown_available()) shutdown_open();
                return 0;
            }
            change_option(S.extra_row);
        } else return keys;
        stock_settings_frame(S.settings_pixels,640,480,1280);
        return 0;
    }
#endif
    if(S.settings_pixels && (S.extra_row || (stock_row==3 && keys==0x40))) {
        if(keys==0x40) {
            if(S.extra_row<2) ++S.extra_row;
        } else if(keys==0x10 && S.extra_row) {
            S.restore_highlight=--S.extra_row==0;
        } else if(keys==0x2000 && S.extra_row) {
            if(S.accept_held) return 0;
            S.accept_held=true;
            change_option(S.extra_row);
        } else return keys;
        stock_settings_frame(S.settings_pixels,640,480,1280);
        return 0;
    }
    return keys;
}

/* The pinned settings loop holds its row index in r11 at both poll sites. */
__attribute__((naked)) ENTRY void stock_settings_key(void)
{
    __asm__ volatile("mov r0, r11\n\tb stock_settings_input");
}

ENTRY void stock_settings(void)
{
    unsigned locale=LOCALE;
    S.extra_row=0;
    S.select_held=button_down(0x30f);
    S.accept_held=button_down(0x204);
#ifdef D35_VESPER_LAUNCHER
    S.start_held=button_down(0x30c);
#endif
    S.save_failed=S.restore_highlight=false;
#ifdef D35_HOME_GRID
    bool classic=S.applied_classic;
    if(classic)
        FN(0x8dfe4,void,void)();
    else
        launcher_settings(false);
    if(classic && S.extra_row==1) {
        S.extra_row=0;
        launcher_settings(true);
    }
#else
    FN(0x8dfe4,void,void)();
#endif
#ifdef D35_VESPER_LAUNCHER
    if(S.power_frame) shutdown_cancel();
#endif
    S.settings_pixels=NULL;
    if(S.applied_classic!=S.classic || locale!=LOCALE) {
        S.applied_classic=S.classic;
        /* The stock menu and pause entry points reload these slots on a
         * miss. Drop the old pack one canvas at a time after display use. */
        void *driver=VAR(0x1b81a8,void *);
        void (*wait)(void)=driver?SYM(driver,"WaitDisp"):NULL;
        if(wait) {
            wait();
            S.baked_settings=NULL;
            static const unsigned slots[]={0x199900,0x199904,0x199908,0x19990c,0x199934};
            for(unsigned i=0;i<sizeof(slots)/sizeof(*slots);++i) {
                void *old=VAR(slots[i],void *);
                VAR(slots[i],void *)=NULL;
                if(old) FREE(old);
            }
        }
    }
}

struct sound {
    void *data;
    unsigned type, bytes_minus_one, channels_minus_one, rate, loop;
    void *begin, *end;
    unsigned phase;
};

static void play_builtin_music(unsigned channel,const struct sound *original)
{
    if(channel==0 && original && original->type==1 && original->data) {
        char path[384];
        if(!S.music && suffix(path,sizeof(path),WORK(),LAUNCHER "/d35-menu.pcm")) {
            S.music=read_bytes(path,4u*1024u*1024u,&S.music_bytes);
            if(S.music && (S.music_bytes%4 || S.music_bytes<735*4)) {
                FREE(S.music); S.music=NULL; S.music_bytes=0;
            }
        }
        if(S.music) {
            const struct sound pcm={S.music,2,1,1,44100,1,S.music,
                                    (uint8_t *)S.music+S.music_bytes,0};
            FN(0x8750c,void,unsigned,const struct sound *)(channel,&pcm);
            return;
        }
    }
    FN(0x8750c,void,unsigned,const struct sound *)(channel,original);
}

ENTRY void stock_menu_music(unsigned channel,const struct sound *original)
{
#ifdef D35_HOME_GRID
    if(channel==0) {
        if(menu_music_override()) return;
        menu_audio_lock();
        if(!start_builtin_music() && original) play_builtin_music(channel,original);
        menu_audio_unlock();
        return;
    }
#endif
    play_builtin_music(channel,original);
}

#ifdef D35_VESPER_LAUNCHER
#include "stock-shell-vesper.h"
#endif

#ifdef D35_HOME_GRID
#include "stock-shell-home.h"
#include "stock-shell-pause.h"
#include "stock-shell-music.h"
#include "stock-shell-settings.h"
#endif
