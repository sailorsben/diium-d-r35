/* Run the real stock pause sprite compositor and controls layout. */
#define main stock_audit_main
#include "check-stock-snes-loader.c"
#undef main
#include <stdbool.h>
#include <zlib.h>

enum { UI=0x1998d8, WIDTH=640, HEIGHT=480, STRIDE=1280 };
static uint16_t frame[HEIGHT][WIDTH];
static void *game_art;
static uint16_t *preview;
static uint32_t keymap[128];
static bool checking_load, accept_held;
static unsigned load_case, load_frames, key_index, loaded_slot;
static const char *fixture_dir;

static void no_preview(void) {}
static void text_run(void *target, int x, int y, int height, unsigned color, const char *text)
{
    assert(text && *text);
    (void)target; (void)x; (void)y; (void)height; (void)color;
}

static void display(void *buffer, unsigned width, unsigned height, unsigned stride)
{
    assert(width==WIDTH && height==HEIGHT && stride==STRIDE);
    if(checking_load) {
        assert(buffer==frame);
        unsigned slot=load_case==0?2:load_case==1?1:6;
        if(load_case==0 && load_frames) slot=load_frames==1?5:4;
        assert(frame[92][350]==(slot==2?0xf800:slot==4?0x07e0:0x10a4));
        if(slot<6) {
            const int (*origins)[6]=(void *)0x19a61c;
            assert(frame[286+origins[slot][1]+20][292+origins[slot][0]+1]==0xffff);
        }
        ++load_frames;
        return;
    }
    assert(!"unexpected display outside save-slot fixture");
}

static void verify_save_slots(void)
{
    uint32_t *records=game_art;
    uint16_t *pixels=(void *)((char *)game_art+records[0]);
    memcpy(frame,pixels,sizeof(frame));
    ((void (*)(void *, unsigned, const void *, unsigned))0x803a8)(frame,STRIDE,game_art,6);
    const int (*stock_slots)[6]=(const void *)0x19a61c;
    for(int slot=0; slot<6; ++slot) {
        int x=296+104*(slot%3), y=289+75*(slot/3);
        int rim_x=292+stock_slots[slot][0], rim_y=286+stock_slots[slot][1];
        uint16_t center=frame[y+29][x+42];
        uint16_t gutter=frame[y+29][rim_x+96];
        assert(center!=frame[y+18][x+42]);
        ((void (*)(int,int,unsigned))0x90f40)(rim_x,rim_y,0xf800);
        assert(frame[y+29][rim_x+1]==0xf800 && frame[y+29][rim_x+92]==0xf800);
        assert(frame[y+29][x+42]==center && frame[y+29][rim_x+96]==gutter);
    }
    puts("PASS stock slot compositor and selection rim leave all six thumbnail interiors and gutters intact");
}

static const char *work_path(void) { return fixture_dir; }
static unsigned read_joy(void)
{
    const unsigned browse[]={0,0x2000,0,0x40,0x80,0x2000};
    const unsigned load_now[]={0,0x2000,0,0x2000};
    const unsigned cancel[]={0,0x4000};
    const unsigned *keys=load_case==0?browse:load_case==1?load_now:cancel;
    unsigned count=load_case==0?6:load_case==1?4:2;
    assert(key_index<count);
    unsigned event=keys[key_index++];
    accept_held=event==0x2000;
    *(unsigned *)0x1b9b50=accept_held?0x2000:0;
    return event;
}

static int visit_slot(const char *path)
{
    size_t n=strlen(path);
    assert(n && path[n-1]>='0' && path[n-1]<='5');
    loaded_slot=(unsigned)(path[n-1]-'0');
    return 1;
}

static unsigned zero_game_type(void) { return 0; }
static unsigned zero_ticks(void) { return 0; }
static void wait_menu(void) {}
static int slot_path(char *out,const char *format,const char *work,const char *system,
                     const char *title,unsigned slot)
{
    (void)format;
    (void)system;
    (void)title;
    return sprintf(out,"%s/slot%u",work,slot);
}
static void *load_symbols(void *driver,const char *name)
{
    assert(driver==frame && !strcmp(name,"WaitDisp"));
    return wait_menu;
}

static void write_slot(unsigned slot,uint16_t pixel,bool corrupt)
{
    char path[1024];
    assert(snprintf(path,sizeof(path),"%s/slot%u",fixture_dir,slot)<(int)sizeof(path));
    FILE *f=fopen(path,"wb");
    assert(f);
    uint32_t state_bytes=4, placeholder=0;
    assert(fwrite(&state_bytes,4,1,f)==1 && fwrite(&placeholder,4,1,f)==1);
    /* Archived saves decompress to this fixed size. Only the leading
     * 190x142 words are the preview; the padding must be ignored. */
    uint16_t pixels[153600/2]={0};
    for(unsigned i=0;i<190*142;++i) pixels[i]=pixel;
    unsigned char compressed[1024];
    unsigned long bytes=sizeof(compressed);
    assert(compress(compressed,&bytes,(const void *)pixels,sizeof(pixels))==Z_OK);
    if(corrupt) compressed[0]=0;
    assert(fwrite(compressed,1,bytes,f)==bytes && !fclose(f));
}

static int state_access(const char *path,int mode)
{
    size_t n=strlen(path);
    assert(n && path[n-1]>='0' && path[n-1]<='5' && mode==0);
    unsigned slot=(unsigned)(path[n-1]-'0');
    return (load_case==0 && (slot==2 || slot==4)) ||
           (load_case==1 && slot==1)?0:-1;
}

static FILE *open_state(const char *path,const char *mode)
{
    size_t n=strlen(path);
    char fixture[1024];
    assert(n && snprintf(fixture,sizeof(fixture),"%s/slot%c",fixture_dir,path[n-1])
            <(int)sizeof(fixture));
    return fopen(fixture,mode);
}

static void verify_load_slots(void)
{
    checking_load=true;
    const unsigned rect[]={348,90,190,142};
    memcpy((void *)0x199eb8,rect,sizeof(rect));
    *(void **)0x1b81a8=frame;
    patch(0x12010,(uintptr_t)load_symbols);
    patch(0x80bec,(uintptr_t)work_path);
    patch(0xa4178,(uintptr_t)zero_game_type);
    patch(0x11f38,(uintptr_t)slot_path);
    patch(0x11e0c,(uintptr_t)state_access);
    patch(0x11ce0,(uintptr_t)open_state);
    patch(0x11b84,(uintptr_t)fseek);
    patch(0x11e84,(uintptr_t)ftell);
    patch(0x11ddc,(uintptr_t)fread);
    patch(0x11ed8,(uintptr_t)malloc);
    patch(0x11b6c,(uintptr_t)free);
    patch(0x11f20,(uintptr_t)fclose);
    patch(0x11bc0,(uintptr_t)uncompress);
    patch(0x8327c,(uintptr_t)zero_ticks);
    patch(0x836b4,(uintptr_t)wait_menu);
    patch(0x86368,(uintptr_t)read_joy);
    patch(0xa3944,(uintptr_t)visit_slot);
    write_slot(1,0xffff,true);
    write_slot(2,0xf800,false);
    write_slot(4,0x07e0,false);
    static char title[]="fixture";
    static char *preview_path=title;
    static unsigned modal_flag, load_flag;
    *(void **)(GOT+0x2b8)=title;
    *(void **)(GOT+0x39c)=&preview_path;
    *(void **)(GOT+0x460)=&modal_flag;
    *(void **)(GOT+0x200)=&load_flag;
    int (*load_menu)(void)=(void *)0x91050;
    for(load_case=0;load_case<3;++load_case) {
        key_index=load_frames=0;
        loaded_slot=6;
        int result=load_menu();
        assert(result==(load_case==2) && loaded_slot==(load_case==0?4:load_case==1?1:6));
        assert(load_frames==(load_case==0?3:1));
    }
    puts("PASS Load State selects the first save, ignores held A, refreshes preview and lets B cancel an empty grid");
}

int main(int argc, char **argv)
{
    assert(argc==4);
    fixture_dir=argv[3];
    map_vendor(argv[1]);
    FILE *file=fopen(argv[2],"rb");
    assert(file && !fseek(file,0,SEEK_END));
    long size=ftell(file);
    assert(size>0 && !fseek(file,0,SEEK_SET));
    game_art=malloc((size_t)size);
    assert(game_art && fread(game_art,1,(size_t)size,file)==(size_t)size && !fclose(file));
    patch(0x11ecc,(uintptr_t)memcpy);
    patch(0x11d64,(uintptr_t)strcpy);
    patch(0x8f538,(uintptr_t)no_preview);
    patch(0x85c94,(uintptr_t)text_run);
    patch(0xa6658,(uintptr_t)display);
    *(void **)0x1b81a8=frame;
    static uint8_t english[80];
    *(unsigned *)UI=1;
    *(void **)(UI+25*4)=english;
    *(void **)(UI+0x38)=frame;
    *(unsigned *)(UI+0x3c)=WIDTH;
    *(unsigned *)(UI+0x40)=HEIGHT;
    *(void **)(UI+0x5c)=game_art;
    *(void **)(GOT+0x304)=keymap;
    *(void **)(GOT+0x39c)=&preview;
    verify_save_slots();
    verify_load_slots();
    free(game_art);
    return 0;
}
