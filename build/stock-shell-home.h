/* Stock main_menu remains the owner of lists, language and game dispatch. */
#include "stock-shell-battery-text.h"

enum { HOME_WIDTH=640, HOME_HEIGHT=480, HOME_BYTES=640*480*2,
       HOME_LABEL_X=194, HOME_LABEL_Y=11, HOME_LABEL_W=320, HOME_LABEL_H=30,
       HOME_TILES=12, HOME_SHORTCUTS=6, HOME_STAY=9 };
#define HOME_ART LAUNCHER "/home-grid.rgb565"
#define HOME_MODE VAR(0x1998e0,unsigned)
#define HOME_TYPE VAR(0x199990,int)
#define HOME_PAD VAR(0x1b9b50,const volatile unsigned)
#define HOME_BATTERY VAR(0x1b9b28,const volatile int)
#define HOME_PRESENTED_BATTERY VAR(0x1b9b24,volatile int)
#define STOCK_UI_FRAME VAR(0x199910,uint16_t *)
static void settings_confirm_sound(void);

struct nes_viewport {
    bool active, overscan_disabled;
    unsigned width, height, pitch;
    uint16_t *trim_buffers;
    void (*wait_display)(void);
    unsigned trim_slot;
};

enum { NES_WIDTH=256, NES_FULL_HEIGHT=240, NES_EDGE_ROWS=8,
       NES_VISIBLE_HEIGHT=NES_FULL_HEIGHT-2*NES_EDGE_ROWS,
       NES_TRIM_PIXELS=NES_WIDTH*NES_VISIBLE_HEIGHT };

struct home_overlay {
    unsigned selected;
    bool type_open, inject_open;
    volatile bool own_battery;
    bool classic_home;
    struct nes_viewport nes;
};
#define HOME VAR(0x1c4300,struct home_overlay)
_Static_assert(sizeof(struct home_overlay)<=0x100, "home overlay reservation");
_Static_assert(offsetof(struct home_overlay,type_open)==4 &&
               offsetof(struct home_overlay,inject_open)==5, "ARM back hook layout");

/* Native carousel indices and main_menu dispatch modes, independently
 * verified against the pinned vendor ELF. */
static const uint8_t home_types[]={3,2,1,7,5,6,4,0,8,9,10,11};
static const uint8_t home_shortcuts[]={5,3,4,2,0,6};
static const unsigned home_shortcut_keys[]={8,1,0x1000,0x8000,0x400,0x800};

static void home_battery_text(uint16_t *frame,unsigned x,unsigned y,int state)
{
    for(unsigned row=0;row<BATTERY_TEXT_H;++row) {
        uint16_t *pixel=frame+(y+row)*640+x;
        for(unsigned column=0;column<BATTERY_TEXT_W/2;++column) {
            unsigned coverage=battery_text[state][row][column];
            if(coverage) {
                menu_blend_pixel(pixel+column*2,0xf7bf,coverage>>4);
                menu_blend_pixel(pixel+column*2+1,0xf7bf,coverage&15);
            }
        }
    }
}

static __attribute__((optimize("Os"))) void home_battery_at(uint16_t *frame,int state,int shift)
{
    const uint16_t ink=state<0 || state==4?0xfe11:S.applied_classic?0x8ddd:0x9dba;
    const bool numbered=S.battery_style!=BATTERY_BARS && state>=0 && state<=4;
    const bool solid=S.battery_style==BATTERY_SOLID;
    const unsigned right=(solid?616:617)+shift, x=(solid?568:593)+shift;

    if(solid) {
        const unsigned percentage=state==5?100:numbered?90-20*state:0;
        const unsigned charge=x+1+(right-x-2)*percentage/100;
        const uint16_t rim=state==4?0xd54b:S.applied_classic?0x7cdc:0x7c91;
        const uint16_t track=S.applied_classic?0x1a8b:0x1949;
        const uint16_t fill=state==4?0x6a66:S.applied_classic?0x2b74:0x3351;
        static const uint8_t corner[]={3,1,1};
        settings_box(frame,right,21,right+3,33,rim);
        for(unsigned row=0;row<22;++row) {
            unsigned cap=row<11?row:21-row;
            unsigned inset=cap<3?corner[cap]:0;
            unsigned start=x+inset, end=right-inset, y=16+row;
            settings_box(frame,start,y,end,y+1,rim);
            if(inset) {
                menu_blend_pixel(frame+y*640+start-1,rim,6);
                menu_blend_pixel(frame+y*640+end,rim,6);
            }
            if(cap) {
                ++start;
                --end;
                settings_box(frame,start,y,end,y+1,track);
                settings_box(frame,start,y,charge<end?charge:end,y+1,fill);
            }
        }
    } else {
        const uint16_t inner=0x10c6;
        settings_box(frame,right+1,24,right+3,29,ink);
        settings_box(frame,x+2,20,right-2,33,ink);
        settings_box(frame,x,22,x+2,31,ink);
        settings_box(frame,right-2,22,right,31,ink);
        settings_box(frame,x+1,21,right-1,32,inner);
        menu_blend_pixel(frame+21*640+x+1,ink,12);
        menu_blend_pixel(frame+21*640+right-2,ink,12);
        menu_blend_pixel(frame+31*640+x+1,ink,12);
        menu_blend_pixel(frame+31*640+right-2,ink,12);
        const unsigned bars=state<0?0:state==5?4:state>=3?1:4-state;
        for(unsigned i=0;i<bars;++i)
            settings_box(frame,x+3+i*5,23,x+6+i*5,30,ink);
    }
    if(numbered) home_battery_text(frame,solid?(x+right-BATTERY_TEXT_W)/2:
                                  (unsigned)(551+shift),19,state);
    if(state==5) {
        unsigned center=(x+right)/2;
        static const int8_t bolt[][2]={
            {1,3},{0,2},{-1,2},{-2,1},{-3,3},{-1,2},{-2,1},{-2,0},{-3,-1}
        };
        for(unsigned row=0;row<sizeof(bolt)/sizeof(*bolt);++row)
            settings_box(frame,center+bolt[row][0],22+row,
                         center+bolt[row][1],23+row,0xff8d);
    }
}

static void home_battery(uint16_t *frame,int state)
{ home_battery_at(frame,state,0); }

/* Keep the vendor's FC directory/state identity. Only its visible NES title
 * changes; replacing the shared platform string would redirect save paths. */
__attribute__((naked)) static int stock_launcher_text(void *frame __attribute__((unused)),
                                                       int x __attribute__((unused)),
                                                       int y __attribute__((unused)),
                                                       int size __attribute__((unused)),
                                                       unsigned ink __attribute__((unused)),
                                                       const char *label __attribute__((unused)))
{
    __asm__ volatile("push {r4-r11, lr}\n\tldr pc, 1f\n\t1: .word 0x85c98");
}

ENTRY int launcher_text(void *frame,int x,int y,int size,unsigned ink,
                        const char *label)
{
    if(HOME.type_open && HOME_TYPE==7 && label &&
       label[0]=='F' && label[1]=='C' && !label[2]) label="NES";
    return stock_launcher_text(frame,x,y,size,ink,label);
}

/* FCEUmm defaults to a 240x224 overscan crop on this frontend. FF2's
 * battle status window uses the outer NES columns, so expose 256x240. */
__attribute__((naked)) static bool stock_environment(unsigned cmd __attribute__((unused)),
                                                      void *data __attribute__((unused)))
{
    __asm__ volatile("push {r4-r6, lr}\n\tldr pc, 1f\n\t1: .word 0xa2fcc");
}

ENTRY bool launcher_environment(unsigned cmd,void *data)
{
    if(cmd==RETRO_ENVIRONMENT_GET_VARIABLE && data) {
        struct retro_variable *var=data;
        if(var->key && !STRCMP(var->key,"fceumm_overscan")) {
            if(HOME.nes.active) HOME.nes.overscan_disabled=true;
            var->value="disabled";
            return true;
        }
    }
    return stock_environment(cmd,data);
}

__attribute__((naked)) static int stock_nes_load(const char *path __attribute__((unused)),
                                                 unsigned type __attribute__((unused)))
{
    __asm__ volatile("push {r4-r6, lr}\n\tldr pc, 1f\n\t1: .word 0xa505c");
}

static void open_chaos_rush_viewport(const char *path)
{
    const char *name=path;
    for(const char *p=path;*p;++p)
        if(*p=='/') name=p+1;
    if(STRCMP(name,"Final Fantasy II - Chaos Rush 2.2b.nes")) return;
    void *driver=VAR(0x1b81a8,void *);
    if(driver) HOME.nes.wait_display=SYM(driver,"WaitDisp");
    if(HOME.nes.wait_display)
        HOME.nes.trim_buffers=FN(0x164abc,void *,size_t)(2*NES_TRIM_PIXELS*sizeof(uint16_t));
}

/* Keep the latest NES session's display handoff in a small atomic receipt.
 * Perform card I/O after gameplay so this cannot block a frame or audio. */
ENTRY int launcher_nes_load(const char *path,unsigned type)
{
    ZERO(&HOME.nes,0,sizeof(HOME.nes));
    HOME.nes.active=true;
    open_chaos_rush_viewport(path);
    int result=stock_nes_load(path,type);
    HOME.nes.active=false;
    if(HOME.nes.trim_buffers) {
        HOME.nes.wait_display();
        FN(0x164d58,void,void *)(HOME.nes.trim_buffers);
        HOME.nes.trim_buffers=NULL;
    }

    char file[384], boot_id[37]={0}, record[160];
    if(!suffix(file,sizeof(file),WORK(),LAUNCHER "/nes-viewport.log")) return result;
    FILE *id=FOPEN("/proc/sys/kernel/random/boot_id","rb");
    if(id) {
        FREAD(boot_id,1,sizeof(boot_id)-1,id);
        FCLOSE(id);
    }
    int bytes=FN(0x11f38,int,char *,const char *,...)(record,
        "boot_id=%s\noverscan=%s\nsubmitted=%ux%u pitch=%u\n",
        boot_id,HOME.nes.overscan_disabled?"disabled":"unconfirmed",
        HOME.nes.width,HOME.nes.height,HOME.nes.pitch);
    if(bytes>0) save_config_bytes(file,record,(size_t)bytes);
    return result;
}

ENTRY void stock_home_adc_overlay(uint16_t *frame,unsigned width)
{
    /* DisplayADC also records the last presented battery state for redraws. */
    if(HOME.own_battery || (frame && width==HOME_WIDTH)) {
        HOME_PRESENTED_BATTERY=HOME_BATTERY;
        return;
    }
    FN(0x13e30,void,uint16_t *,unsigned)(frame,width);
}

/* Some driver paths resolve DisplayADC itself. Make both entry paths agree
 * on who owns the header. The original instructions continue at +4. */
__attribute__((naked)) static void stock_display_adc(uint16_t *frame __attribute__((unused)),
                                                   unsigned width __attribute__((unused)))
{
    __asm__ volatile("ldr r2, 1f\n\tldr pc, 2f\n\t1: .word 0x1851bc\n\t2: .word 0x13e34");
}

ENTRY void launcher_display_adc(uint16_t *frame,unsigned width)
{
    if(!frame || width==HOME_WIDTH || HOME.own_battery) {
        HOME_PRESENTED_BATTERY=HOME_BATTERY;
        return;
    }
    stock_display_adc(frame,width);
}

/* Paint the stock UI canvas before the display driver can copy or scale it.
 * The bundled driver's legacy frame-extend setter is a no-op. */
ENTRY void launcher_display_frame(const void *frame,unsigned w,unsigned h,size_t pitch)
{
    if(launcher_factory_active()) return;
    if(frame && frame==STOCK_UI_FRAME && w==640 && h==480 && pitch==1280 &&
       !HOME.own_battery && !S.game.core) {
        uint16_t *canvas=STOCK_UI_FRAME;
        int battery=HOME_BATTERY;
        /* Stock lists put their ROM count at the right edge of this header. */
        settings_box(canvas,358,10,448,43,0x08a4);
        home_battery_at(canvas,battery,-180);
        HOME_PRESENTED_BATTERY=battery;
    }
    typedef void (*submit_frame_fn)(const void *,unsigned,unsigned,size_t);
    submit_frame_fn submit=VAR(0x1be388,submit_frame_fn);
    if(submit) {
        if(HOME.nes.active && frame && w && h && frame!=STOCK_UI_FRAME) {
            if(HOME.nes.trim_buffers && w==NES_WIDTH && h==NES_FULL_HEIGHT &&
               pitch==NES_WIDTH*sizeof(uint16_t)) {
                /* The driver has at most one queued source. The other slot
                 * is safe to fill before handing the next picture over. */
                uint16_t *slot=HOME.nes.trim_buffers+HOME.nes.trim_slot*NES_TRIM_PIXELS;
                COPY(slot,(const uint8_t *)frame+NES_EDGE_ROWS*pitch,
                     NES_TRIM_PIXELS*sizeof(*slot));
                HOME.nes.trim_slot^=1;
                frame=slot;
                h=NES_VISIBLE_HEIGHT;
            }
            if(!HOME.nes.width) {
                HOME.nes.width=w;
                HOME.nes.height=h;
                HOME.nes.pitch=pitch;
            }
        }
        submit(frame,w,h,pitch);
    }
}

static void own_menu_battery(bool owned)
{
    HOME.own_battery=owned;
}

/* The same read-only status bit used by the stock power helper. Keep the
 * long-press helper and use a single mapping only while Home owns the UI. */
static volatile uint32_t *home_power_map(void)
{
    int (*open)(const char *,int,...)=FN(0x11da0,int,const char *,int,...);
    long (*map)(void *,size_t,int,int,int,long)=FN(0x11d70,long,void *,size_t,int,int,int,long);
    int fd=open("/dev/mem",0);
    if(fd<0) return NULL;
    long address=map(NULL,4096,1,1,fd,0xd0000000);
    FN(0x11cd4,int,int)(fd);
    return address==-1?NULL:(volatile uint32_t *)address;
}

static void home_compose(uint16_t *frame,const uint16_t *base,unsigned cursor,int battery)
{
    if(base) COPY(frame,base,HOME_BYTES);
    else {
        static const char *const titles[]={"GAME BOY","GAME BOY COLOR","GAME BOY ADV",
            "NES","SUPER NINTENDO","GENESIS","PLAYSTATION","ARCADE","CPS 1","CPS 2","IGS","NEO GEO"};
        settings_box(frame,0,0,640,480,0x08a4);
        settings_text(frame,20,22,"GAME LIBRARY",2,0xffff);
        settings_text(frame,20,448,"START SETTINGS    SELECT FAVORITES    A OPEN",2,0xffff);
        for(unsigned i=0;i<HOME_TILES;++i) {
            unsigned tx=20+152*(i%4), ty=64+123*(i/4);
            settings_box(frame,tx,ty,tx+144,ty+115,0x1127);
            settings_text(frame,tx+8,ty+47,titles[i],1,0xffff);
        }
    }
    const unsigned x=20+152*(cursor%4), y=64+123*(cursor/4), w=144, h=115;
    if(base) {
        const uint16_t *label=base+HOME_WIDTH*HOME_HEIGHT+cursor*HOME_LABEL_W*HOME_LABEL_H;
        for(unsigned row=0;row<HOME_LABEL_H;++row)
            COPY(frame+(HOME_LABEL_Y+row)*HOME_WIDTH+HOME_LABEL_X,
                 label+row*HOME_LABEL_W,HOME_LABEL_W*2);
    }
    uint16_t accent=0xfe49;
    settings_box(frame,x-2,y-2,x+w+2,y,accent);
    settings_box(frame,x-2,y+h,x+w+2,y+h+2,accent);
    settings_box(frame,x-2,y,x,y+h,accent);
    settings_box(frame,x+w,y,x+w+2,y+h,accent);
    home_battery(frame,battery);
}

static unsigned home_move(unsigned cursor,unsigned key)
{
    if(key==0x80 && cursor%4) return cursor-1;
    if(key==0x20 && cursor%4<3) return cursor+1;
    if(key==0x10 && cursor>=4) return cursor-4;
    if(key==0x40 && cursor+4<HOME_TILES) return cursor+4;
    return cursor;
}

ENTRY unsigned stock_home(void)
{
    const unsigned expected=HOME_BYTES+HOME_TILES*HOME_LABEL_W*HOME_LABEL_H*2+4;
    HOME.type_open=HOME.inject_open=false;
    if(S.applied_classic) {
        unsigned mode=HOME.classic_home?HOME_MODE:1;
        HOME.classic_home=true;
        return mode;
    }
    HOME.classic_home=false;
    char path[384];
    void (*wait)(void)=shutdown_wait();
    if(!wait || VAR(0x199914,unsigned)!=HOME_WIDTH ||
       VAR(0x199918,unsigned)!=HOME_HEIGHT)
        return 5; /* retry through the launcher Settings route, never the carousel */
    size_t bytes=0;
    uint16_t *base=suffix(path,sizeof(path),WORK(),HOME_ART)?read_bytes(path,expected,&bytes):NULL;
    if(base && (bytes!=expected || CMP((const char *)base+expected-4,"D354",4))) {
        FREE(base);
        base=NULL;
    }
    uint16_t *frame=FN(0x164abc,void *,size_t)(HOME_BYTES);
    bool allocated=frame!=NULL;
    if(!frame) frame=STOCK_UI_FRAME;
    if(!frame) { FREE(base); return 5; }

    volatile uint32_t *power=shutdown_available()?home_power_map():NULL;
    bool previous_power=power && (power[0x68/4]&8);
    unsigned cursor=HOME.selected<HOME_TILES?HOME.selected:0, mode=HOME_STAY;
    int battery=HOME_BATTERY;
    own_menu_battery(true);
    unsigned (*joy)(void)=FN(0x86368,unsigned,void);
    /* Drain the key that closed a list before allowing another dispatch. */
    unsigned held=HOME_PAD&0xffffu;
    joy();
    wait();
    home_compose(frame,base,cursor,battery);
    DISP(frame,HOME_WIDTH,HOME_HEIGHT,HOME_WIDTH*2);
    while(mode==HOME_STAY) {
        unsigned key=joy();
        held &= HOME_PAD;
        if(key&held) key=0;
        bool down=power && (power[0x68/4]&8);
        bool esc=launcher_escape(key);
        bool redraw=false;
        if(((down && !previous_power) || esc) && !S.power_frame && shutdown_available()) {
            S.power_frame=frame;
            S.accept_held=(HOME_PAD&0x2000)!=0;
            shutdown_prepare_art();
            shutdown_message(POWER_CONFIRM,"POWER OFF","SAVE DATA WILL BE FLUSHED","A POWER OFF     B CANCEL");
        } else if(S.power_frame) {
            if(!(HOME_PAD&0x2000)) S.accept_held=false;
            if(shutdown_input(esc?0x4000:key)) {
                if(key==0x2000) held|=key;
                S.power_frame=NULL;
                shutdown_release_art();
                redraw=true;
            }
        } else if(key==0x2000) {
            settings_confirm_sound();
            HOME_TYPE=home_types[cursor];
            HOME.type_open=HOME.inject_open=true;
            mode=1;
        } else {
            for(unsigned i=0;i<HOME_SHORTCUTS;++i)
                if(key==home_shortcut_keys[i]) { mode=home_shortcuts[i]; settings_confirm_sound(); }
            unsigned next=home_move(cursor,key);
            if(next!=cursor) {
                cursor=next;
                vesper_transition(1);
                redraw=true;
            }
        }
        int charge=HOME_BATTERY;
        if(charge<0) FN(0x836b4,void,void)();
        if(!S.power_frame && (redraw || charge!=battery)) {
            battery=charge;
            wait();
            home_compose(frame,base,cursor,battery);
            DISP(frame,HOME_WIDTH,HOME_HEIGHT,HOME_WIDTH*2);
        }
        previous_power=down;
        if(mode==HOME_STAY) FN(0x11f08,int,unsigned)(20000);
    }
    HOME.selected=cursor;
    if(power) FN(0x11efc,int,void *,size_t)((void *)power,4096);
    wait();
    own_menu_battery(false);
    if(allocated) FN(0x164d58,void,void *)(frame);
    FREE(base);
    return mode;
}

/* r4 is the stock dispatch mode; preserve the containing function's stack
 * and callee-saved state. The following instructions still set menu flags. */
__attribute__((naked)) ENTRY void stock_home_dispatch(void)
{
    __asm__ volatile("push {r3, lr}\n\tbl stock_home\n\tmov r4, r0\n\tpop {r3, pc}");
}

ENTRY unsigned stock_home_type_key(void)
{
    if(HOME.inject_open) { HOME.inject_open=false; return 0x2000; }
    return launcher_menu_key();
}

ENTRY void stock_home_type_frame(void *frame,unsigned w,unsigned h,size_t pitch)
{
    if(!HOME.inject_open) DISP(frame,w,h,pitch);
}

/* A direct platform visit uses the stock Back key but skips its intermediate
 * carousel. The stock epilogue still restores the caller's stack/registers. */
__attribute__((naked)) ENTRY void stock_home_type_back(void)
{
    __asm__ volatile(
        "movw r3, #0x4304\n\tmovt r3, #0x1c\n\tldrb r2, [r3]\n\tcmp r2, #0\n\t"
        "movne r2, #0\n\tstrneb r2, [r3]\n\tstrneb r2, [r3, #1]\n\t"
        "ldrne pc, 1f\n\tldr r3, [sp, #12]\n\tbx lr\n\t1: .word 0x89ed4");
}
