/* Owned launch code linked into the pinned stock menu ELF, ARM32 only.
 * All stock entry points and data below are bound to the source SHA in the
 * assembler. No preloaded library, proxy libretro core or loader daemon. */
#include <libretro.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

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

#define D35_VIEWPORT_COPY COPY
#define D35_VIEWPORT_COMPARE CMP
#include "starfox-viewport.h"

_Static_assert(2u * D35_STARFOX_FRAME_BYTES <= SLOT, "Star Fox display and reference fit in a slot");

struct session {
    void *core, *pool;
    void (*wait_display)(void);
    void (*run)(void), (*unload)(void), (*deinit)(void);
    bool (*load)(const struct retro_game_info *);
    void (*av)(struct retro_system_av_info *);
    unsigned phase, w, h, shown, next, skip, recovery, auto_skip;
    bool previous, rgb565, starfox, zoomed;
    int16_t last[2];
    unsigned ticks, skipped, copies, repeats;
};
struct overlay {
    struct session game;
    bool auto_skip, select_held;
    uint16_t *settings_pixels;
    void *music;
    size_t music_bytes;
};
/* Reserved by extending the pinned RW LOAD's zero-filled tail. */
#define S VAR(0x1c4100, struct overlay)
_Static_assert(sizeof(struct overlay) <= 0x100, "overlay must fit reserved storage");

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
    if(!in || !n) return 0;
    if(!s->previous) { l=*in++; r=*in++; s->previous=true; --n; }
    while(n--) {
        int a=*in++, b=*in++;
        do {
            out[2*used]=(int16_t)((l*245+(a-l)*(int)phase)/245);
            out[2*used+1]=(int16_t)((r*245+(b-r)*(int)phase)/245);
            phase+=178;
            if(++used==2048) { FN(0xa2cc4, size_t, const int16_t *, size_t)(out,used); used=0; }
        } while(phase<245);
        phase-=245;
        l=a; r=b;
    }
    s->phase=phase; s->last[0]=(int16_t)l; s->last[1]=(int16_t)r;
    if(used) FN(0xa2cc4, size_t, const int16_t *, size_t)(out,used);
    return accepted;
}

static void snes_sample(int16_t l, int16_t r)
{ const int16_t pair[]={l,r}; snes_audio(pair,1); }

static void snes_video(const void *data, unsigned w, unsigned h, size_t pitch)
{
    struct session *s=&S.game;
    size_t bytes=2*w;
    if(!data || !w || !h || w>512 || h>512 || pitch<bytes || !s->pool) return;
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
        if(y==h) { ++s->repeats; return; }
    }
    /* Before reusing a submitted slot, fence the stock display worker. */
    if(s->copies>=2) s->wait_display();
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
    if(core==S.game.core && S.game.auto_skip) return snes_tick;
    return SYM(core,symbol);
}

static void release_snes(bool close_core)
{
    struct session *s=&S.game;
    if(s->pool) {
        if(s->copies) s->wait_display();
        /* DrawFrame retains the pointer for pause and previews. Clear it only
         * after the stock gameplay loop and its display jobs have finished. */
        VAR(0x1bd5f8, const void *)=NULL;
        FN(0x164d58, void, void *)(s->pool);
    }
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
            FN(0xa426c, void, void)(); /* Stock loop owns unload/deinit/dlclose. */
            FN(0x11be4, int, const char *, ...)("D35 direct: copies=%u equal=%u auto_ticks=%u dropped=%u\n",
                                              s->copies,s->repeats,s->ticks,s->skipped);
            release_snes(false);
            return 0;
        }
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
    } else if(VAR(0x1998d8, unsigned)==1 && !STRCMP(name,"setting.raw")) {
        uint16_t *frame=full_art_block(*art,size,0);
        if(frame && frame[0]==0x39e9 && frame[1]==0x31ea &&
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
    if(suffix(path,sizeof(path),WORK(),LAUNCHER "/d35-loader.cfg")) {
        FILE *f=FOPEN(path,"rb");
        char setting=0;
        if(f) { S.auto_skip=FREAD(&setting,1,1,f)==1 && setting=='1'; FCLOSE(f); }
    }
    VAR(0x1998d8,unsigned)=1;
    FN(0x81da0,void,void)();
}

static bool save_skip(bool value)
{
    char path[384],tmp[384];
    int (*replace)(const char *,const char *)=SYM(NULL,"rename");
    if(!replace || !suffix(path,sizeof(path),WORK(),LAUNCHER "/d35-loader.cfg") ||
       !suffix(tmp,sizeof(tmp),path,".tmp")) return false;
    FILE *f=FOPEN(tmp,"wb");
    if(!f) return false;
    const char setting=value?'1':'0';
    bool ok=FN(0x11eb4,size_t,const void *,size_t,size_t,FILE *)(&setting,1,1,f)==1 &&
        !FN(0x11fb0,int,FILE *)(f) && !FN(0x11b18,int,int)(FN(0x11df4,int,FILE *)(f));
    if(FCLOSE(f)) ok=false;
    return ok && !replace(tmp,path);
}

/* Compact glyphs for the new settings footer; keep the stock artwork intact. */
static const uint8_t glyph[26][7]={
 {14,17,17,31,17,17,17}, {}, {14,17,16,16,16,17,14}, {}, {31,16,16,30,16,16,31},
 {31,16,16,30,16,16,16}, {}, {}, {14,4,4,4,4,4,14}, {}, {17,18,20,24,20,18,17},
 {16,16,16,16,16,16,31}, {17,27,21,21,17,17,17}, {}, {14,17,17,17,17,17,14},
 {30,17,17,30,16,16,16}, {}, {30,17,17,30,20,18,17}, {15,16,16,14,1,1,30},
 {31,4,4,4,4,4,4}, {17,17,17,17,17,17,14}
};

ENTRY void stock_settings_frame(uint16_t *p,unsigned w,unsigned h,size_t pitch)
{
    if(p && w==640 && h==480 && pitch==1280) {
        void *driver=VAR(0x1b81a8,void *);
        void (*wait)(void)=driver?SYM(driver,"WaitDisp"):NULL;
        if(wait) {
            wait();
            for(unsigned y=354;y<376;++y) for(unsigned x=141;x<499;++x) p[y*640+x]=0x18c6;
            const char *text=S.auto_skip?"SELECT  FRAME SKIP  AUTO":"SELECT  FRAME SKIP  OFF";
            for(unsigned i=0;text[i];++i) if(text[i]!=' ')
                for(unsigned y=0;y<7;++y) for(unsigned x=0;x<5;++x)
                    if(glyph[text[i]-'A'][y]&(16u>>x))
                        for(unsigned dy=0;dy<2;++dy) for(unsigned dx=0;dx<2;++dx)
                            p[(358+2*y+dy)*640+175+12*i+2*x+dx]=0xffff;
            S.settings_pixels=p;
        }
    }
    DISP(p,w,h,pitch);
}

static bool select_down(void)
{ return FN(0x157c8,int,unsigned)(0x30f)==0; }

ENTRY unsigned stock_settings_input(void)
{
    unsigned keys=FN(0x86368,unsigned,void)();
    if(!select_down()) S.select_held=false;
    if(keys==1) {
        if(!S.select_held && save_skip(!S.auto_skip)) {
            S.auto_skip=!S.auto_skip;
            if(S.settings_pixels) stock_settings_frame(S.settings_pixels,640,480,1280);
        }
        S.select_held=true;
        return 0;
    }
    return keys;
}

ENTRY void stock_settings(void)
{
    S.select_held=select_down();
    FN(0x8dfe4,void,void)();
    S.settings_pixels=NULL;
}

struct sound {
    void *data;
    unsigned type, bytes_minus_one, channels_minus_one, rate, loop;
    void *begin, *end;
    unsigned phase;
};

ENTRY void stock_menu_music(unsigned channel,const struct sound *original)
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
