/* Stock main_menu remains the owner of lists, language and game dispatch. */
enum { HOME_WIDTH=640, HOME_HEIGHT=480, HOME_BYTES=640*480*2,
       HOME_LABEL_X=232, HOME_LABEL_Y=11, HOME_LABEL_W=320, HOME_LABEL_H=30,
       HOME_TILES=12, HOME_SHORTCUTS=6, HOME_STAY=9 };
#define HOME_ART LAUNCHER "/home-grid.rgb565"
#define HOME_MODE VAR(0x1998e0,unsigned)
#define HOME_TYPE VAR(0x199990,int)
#define HOME_PAD VAR(0x1b9b50,const volatile unsigned)
#define HOME_BATTERY VAR(0x1b9b28,const volatile int)

struct home_overlay {
    unsigned selected;
    bool type_open, inject_open;
    bool own_battery;
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

ENTRY void stock_home_adc_overlay(uint16_t *frame,unsigned width)
{
    if(!HOME.own_battery) FN(0x13e30,void,uint16_t *,unsigned)(frame,width);
}

static void home_battery(uint16_t *frame,int state)
{
    uint16_t ink=state<0 || state==4?0xfb69:S.applied_classic?0x8f5e:0xb69a;
    if(S.battery_percent && state>=0 && state<=4) {
        /* Midpoints of the five vendor bands, shown as an estimate. */
        static const uint8_t marks[8][7]={
            {0,0,0,10,21,0,0}, /* ~ */
            {14,17,17,17,17,17,14}, /* 0 */
            {4,12,4,4,4,4,14}, /* 1 */
            {30,1,1,14,1,1,30}, /* 3 */
            {31,16,16,30,1,1,30}, /* 5 */
            {31,1,2,4,8,8,8}, /* 7 */
            {14,17,17,15,1,1,14}, /* 9 */
            {25,26,4,4,8,11,19}, /* % */
        };
        const unsigned chars[]={0,6-(unsigned)state,1,7};
        for(unsigned i=0;i<4;++i)
            for(unsigned y=0;y<7;++y)
                for(unsigned x=0;x<5;++x)
                    if(marks[chars[i]][y]&(16u>>x)) {
                        unsigned left=576+12*i+2*x, top=19+2*y;
                        settings_box(frame,left,top,left+2,top+2,ink);
                    }
        return;
    }
    settings_box(frame,581,18,617,20,ink);
    settings_box(frame,581,33,617,35,ink);
    settings_box(frame,581,20,583,33,ink);
    settings_box(frame,615,20,617,33,ink);
    settings_box(frame,618,24,621,29,ink);
    unsigned bars=state<0 || state>5?0:state==5?4:4-(unsigned)state;
    for(unsigned i=0;i<bars;++i)
        settings_box(frame,585+i*7,22,590+i*7,31,ink);
    if(state==5) {
        settings_box(frame,598,16,600,37,0xff8d);
        settings_box(frame,594,25,604,28,0xff8d);
    }
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
    COPY(frame,base,HOME_BYTES);
    const unsigned x=20+152*(cursor%4), y=64+123*(cursor/4), w=144, h=115;
    const uint16_t *label=base+HOME_WIDTH*HOME_HEIGHT+cursor*HOME_LABEL_W*HOME_LABEL_H;
    for(unsigned row=0;row<HOME_LABEL_H;++row)
        COPY(frame+(HOME_LABEL_Y+row)*HOME_WIDTH+HOME_LABEL_X,
             label+row*HOME_LABEL_W,HOME_LABEL_W*2);
    uint16_t accent=S.applied_classic?0x8f5e:0xfe49;
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
    char path[384];
    void (*wait)(void)=shutdown_wait();
    if(LOCALE!=1 || !wait || VAR(0x199914,unsigned)!=HOME_WIDTH ||
       VAR(0x199918,unsigned)!=HOME_HEIGHT || !suffix(path,sizeof(path),WORK(),HOME_ART))
        return HOME_MODE;
    size_t bytes;
    uint16_t *base=read_bytes(path,expected,&bytes);
    if(!base || bytes!=expected || CMP((const char *)base+expected-4,"D354",4)) {
        if(base) FREE(base);
        return HOME_MODE;
    }
    uint16_t *frame=FN(0x164abc,void *,size_t)(HOME_BYTES);
    if(!frame) { FREE(base); return HOME_MODE; }

    volatile uint32_t *power=shutdown_available()?home_power_map():NULL;
    bool previous_power=power && (power[0x68/4]&8);
    unsigned cursor=HOME.selected<HOME_TILES?HOME.selected:0, mode=HOME_STAY;
    int battery=HOME_BATTERY;
    HOME.own_battery=true;
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
            if(key==0x4000 || esc) {
                S.power_frame=NULL;
                shutdown_release_art();
                redraw=true;
            } else if(key==0x2000 && !S.accept_held) {
                S.accept_held=true;
                shutdown_confirm();
            }
        } else if(key==0x2000) {
            HOME_TYPE=home_types[cursor];
            HOME.type_open=HOME.inject_open=true;
            mode=1;
        } else {
            for(unsigned i=0;i<HOME_SHORTCUTS;++i)
                if(key==home_shortcut_keys[i]) mode=home_shortcuts[i];
            unsigned next=home_move(cursor,key);
            if(next!=cursor) {
                cursor=next;
                vesper_transition(1);
                redraw=true;
            }
        }
        int charge=HOME_BATTERY;
        if(charge<0) {
            wait();
            HOME.own_battery=false;
            FN(0x836b4,void,void)();
            HOME.own_battery=true;
        }
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
    HOME.own_battery=false;
    FN(0x164d58,void,void *)(frame);
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
