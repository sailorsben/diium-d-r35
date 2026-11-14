/* Bridges for the stock 640x480 pause UI. Slot paths and load dispatch keep
 * the same core-specific rules as the rest of the launcher. */
enum { PAUSE_SLOTS=6, STOCK_THUMB_BYTES=153600 };
#define PAUSE_ART VAR(0x199934,const struct art_block *)
#define PAUSE_WIDTH VAR(0x199914,unsigned)
#define PAUSE_HEIGHT VAR(0x199918,unsigned)
#define PAUSE_RECT ((const unsigned *)0x199eb8)
#define PAUSE_SLOT_MAP ((const int (*)[6])0x19a61c)

struct pause_ui {
    uint16_t *thumb[PAUSE_SLOTS];
    bool replacement, accept_ready;
    int row;
    bool menu, redraw_only;
    unsigned exit_choice, exit_held;
    uint16_t *exit_background;
};
#define PAUSE VAR(0x1c4400,struct pause_ui)
_Static_assert(sizeof(struct pause_ui)<=0x100, "pause UI reservation");

static void pause_wait(void)
{
    void (*wait)(void)=shutdown_wait();
    if(wait) wait();
}

static void settings_confirm_sound(void);
static int pause_label(uint16_t *frame,int x,int y,int size,uint16_t color,const char *label);
static void pause_button_prompts(uint16_t *frame,int x,int y)
{
    menu_button(frame,x,y,BUTTON_DPAD);
    pause_label(frame,x+37,y-12,22,0xffff,"Move");
    menu_button(frame,x+143,y,BUTTON_A);
    pause_label(frame,x+180,y-12,22,0xffff,"Open");
    menu_button(frame,x+489,y,BUTTON_B);
    pause_label(frame,x+526,y-12,22,0xffff,"Back");
}

static int pause_label(uint16_t *frame,int x,int y,int size,uint16_t color,const char *label)
{
    return FN(0x85c94,int,void *,int,int,int,unsigned,const char *)(frame,x,y,size,color,label);
}

static bool pause_layout(void)
{
    return PAUSE_WIDTH==640 && PAUSE_HEIGHT==480 && shutdown_wait();
}

static void pause_list(uint16_t *frame,unsigned row)
{
    static const char *const labels[]={"Resume","Save State","Load State","Controls","Exit"};
    uint16_t accent=S.applied_classic?0x8f5e:0xfe49;
    settings_reset_text_clip();
    settings_box(frame,0,53,237,432,0x08a4);
    for(unsigned i=0;i<5;++i) {
        unsigned y=81+65*i;
        settings_box(frame,20,y,218,y+50,i==row?0x21ab:0x1127);
        if(i==row) settings_box(frame,20,y,24,y+50,accent);
        pause_label(frame,37,y+6,24,0xffff,labels[i]);
    }
}

ENTRY void launcher_pause_frame(uint16_t *frame,unsigned w,unsigned h,size_t pitch)
{
    if(pause_layout() && frame && w==640 && h==480 && pitch==1280) {
        pause_wait();
        if(!PAUSE.menu) PAUSE.row=0;
        PAUSE.menu=true;
        pause_list(frame,(unsigned)PAUSE.row);
        static const char *const help[][2]={
            {"Resume","Go back to the game."},
            {"Save State","Choose a slot to save your progress."},
            {"Load State","Open the save slots to pick a state."},
            {"Controls","View or change your button mapping."},
            {"Exit","Return to the library with or without saving."}
        };
        settings_box(frame,250,250,640,432,0x08a4);
        settings_box(frame,284,276,614,381,0x320c);
        settings_box(frame,285,277,613,380,0x1127);
        pause_label(frame,303,282,24,0xffff,help[PAUSE.row][0]);
        pause_label(frame,303,319,17,0xa638,help[PAUSE.row][1]);
        settings_box(frame,0,432,640,480,0x10e6);
        pause_button_prompts(frame,25,441);
    }
    DISP(frame,w,h,pitch);
}

/* The outer stock loop owns game pause setup and teardown. It only needs
 * to see Resume or a confirmed Exit. Submenus keep their original handlers. */
ENTRY unsigned launcher_pause_key(void)
{
    if(!PAUSE.menu || !pause_layout()) return FN(0x86368,unsigned,void)();
    uint16_t *frame=STOCK_UI_FRAME;
    unsigned key=launcher_menu_key();
    if(key==0x4000 || (key==0x2000 && PAUSE.row==0)) {
        if(key==0x2000) settings_confirm_sound();
        PAUSE.menu=false;
        return 0x2000;
    }
    if((key==0x10 && PAUSE.row>0) || (key==0x40 && PAUSE.row<4)) {
        PAUSE.row+=key==0x10?-1:1;
        vesper_transition(1);
    } else if(key==0x2000) {
        settings_confirm_sound();
        int result=1;
        switch(PAUSE.row) {
        case 1: result=FN(0x91818,int,void)(); break;
        case 2: result=FN(0x91050,int,void)(); break;
        case 3: result=FN(0x8f5c0,int,void)(); break;
        case 4: return 0x40; /* preserve the stock exit and cleanup path */
        }
        if(!result) {
            PAUSE.menu=false;
            return 0x2000;
        }
        /* Returning from a submenu leaves its picture on the shared frame.
         * The stock loop's redraw entry rebuilds the original game preview. */
        PAUSE.redraw_only=true;
        return 0x40;
    } else return 0;
    launcher_pause_frame(frame,640,480,1280);
    return 0;
}

static int pause_measure(uint16_t *frame,int size,const char *label)
{
    /* The stock function returns the right edge. An empty vertical clip
     * lets it measure without touching a pixel or needing another canvas. */
    unsigned *clip=(unsigned *)0x19bac4;
    unsigned top=clip[1];
    clip[1]=480;
    int width=pause_label(frame,0,0,size,0xffff,label);
    clip[1]=top;
    return width;
}

static void pause_center(uint16_t *frame,int y,int size,uint16_t ink,const char *label)
{
    int width=pause_measure(frame,size,label);
    if(width<0 || width>640) return;
    pause_label(frame,(640-width)/2,y,size,ink,label);
}

ENTRY void launcher_exit_frame(uint16_t *frame,unsigned w,unsigned h,size_t pitch)
{
    if(PAUSE.menu && pause_layout() && frame && w==640 && h==480 && pitch==1280) {
        pause_wait();
        if(PAUSE.exit_background)
            for(unsigned i=0;i<640u*480;++i) frame[i]=(PAUSE.exit_background[i]&0xe79c)>>2;
        else settings_box(frame,0,0,640,480,0x0842);
        settings_reset_text_clip();
        const uint16_t accent=S.applied_classic?0x8f5e:0xfe49;
        settings_box(frame,90,128,550,354,0x31cb);
        settings_box(frame,91,129,549,353,0x1127);
        settings_box(frame,302,153,338,155,accent);
        pause_center(frame,156,34,0xffff,"Exit game?");
        pause_center(frame,207,23,0xc618,"Return to the game library.");
        static const char *const actions[]={"Cancel","Save & Exit","Exit"};
        for(unsigned i=0;i<3;++i) {
            unsigned x=109+143*i;
            bool active=i==PAUSE.exit_choice;
            settings_box(frame,x,267,x+136,315,active?accent:0x31cb);
            settings_box(frame,x+1,268,x+135,314,active?0x21ab:0x08a4);
            int width=pause_measure(frame,21,actions[i]);
            if(width>0 && width<136)
                pause_label(frame,(int)(x+68)-width/2,265,21,0xffff,actions[i]);
        }
        int width=pause_measure(frame,20,"Confirm");
        unsigned x=(640u-36u-(unsigned)(width>0 && width<300?width:68))/2;
        menu_button(frame,x,322,BUTTON_A);
        pause_label(frame,x+36,313,20,0xc618,"Confirm");
    }
    bool owned=HOME.own_battery;
    if(PAUSE.menu && pause_layout()) own_menu_battery(true);
    DISP(frame,w,h,pitch);
    own_menu_battery(owned);
}

ENTRY unsigned launcher_exit_key(void)
{
    if(!PAUSE.menu || !pause_layout()) return FN(0x86368,unsigned,void)();
    unsigned key=settings_key_poll(&PAUSE.exit_held);
    if(key==0x4000) return 0x10;
    if(key==0x2000) {
        PAUSE.exit_held|=key;
        settings_confirm_sound();
        static const unsigned native[]={0x10,0x40,0x2000};
        return native[PAUSE.exit_choice];
    }
    if((key==0x80 && PAUSE.exit_choice) || (key==0x20 && PAUSE.exit_choice<2)) {
        PAUSE.exit_choice+=key==0x80?-1:1;
        vesper_transition(1);
        launcher_exit_frame(STOCK_UI_FRAME,640,480,1280);
    }
    return 0;
}

ENTRY int launcher_pause_exit(void)
{
    if(PAUSE.redraw_only) {
        PAUSE.redraw_only=false;
        return 1;
    }
    bool owned=PAUSE.menu && pause_layout();
    if(owned) {
        PAUSE.exit_choice=0;
        PAUSE.exit_held=HOME_PAD|0x2000;
        PAUSE.exit_background=ALLOC(HOME_BYTES);
        if(PAUSE.exit_background && STOCK_UI_FRAME) {
            pause_wait();
            COPY(PAUSE.exit_background,STOCK_UI_FRAME,HOME_BYTES);
        } else {
            FREE(PAUSE.exit_background);
            PAUSE.exit_background=NULL;
        }
    }
    int result=FN(0x92450,int,void)();
    if(PAUSE.exit_background) {
        FREE(PAUSE.exit_background);
        PAUSE.exit_background=NULL;
    }
    if(!result) {
        if(owned) VAR(0x1b9ce8,unsigned)=1; /* save success clears the stock pause result */
        PAUSE.menu=false;
    }
    return result;
}

static void release_thumbnails(void)
{
    for(unsigned slot=0;slot<PAUSE_SLOTS;++slot) {
        if(PAUSE.thumb[slot]) FREE(PAUSE.thumb[slot]);
        PAUSE.thumb[slot]=NULL;
    }
}

static bool preview_rect(void)
{
    unsigned x=PAUSE_RECT[0], y=PAUSE_RECT[1], w=PAUSE_RECT[2], h=PAUSE_RECT[3];
    return x<640 && y<480 && w>=86 && h>=60 && w<=640-x && h<=480-y;
}

static bool slot_rect(unsigned slot,unsigned *x,unsigned *y)
{
    const struct art_block *art=PAUSE_ART;
    if(!art || art[0].offset<7*sizeof(*art) || slot>=PAUSE_SLOTS) return false;
    *x=art[6].left+4+104*(slot%3);
    *y=art[6].top+3+75*(slot/3);
    return *x>=4 && *x+88<640 && *y>=3 && *y+63<480;
}

static void scale_thumbnail(uint16_t *dest,unsigned dw,unsigned dh,const uint16_t *src,
                            unsigned sw,unsigned sh)
{
    unsigned sy=0, fy=0;
    for(unsigned y=0;y<dh;++y) {
        unsigned sx=0, fx=0;
        for(unsigned x=0;x<dw;++x) {
            dest[x]=src[sy*sw+sx];
            fx+=sw;
            while(fx>=dw) { fx-=dw; ++sx; }
        }
        dest+=640;
        fy+=sh;
        while(fy>=dh) { fy-=dh; ++sy; }
    }
}

/* r8 is the scanned slot, r9 points to its presence flag. Return NULL on the
 * replacement path because the stock loop then advances to the next slot. */
static __attribute__((used)) FILE *load_slot(const char *path,const char *mode,unsigned slot,
                                            unsigned *present)
{
    FILE *file=stock_state_fopen(path,mode);
    if(!PAUSE.replacement || slot>=PAUSE_SLOTS) return file;
    *present=0;
    if(!file) return NULL;
    uint32_t state_bytes;
    long size=-1;
    if(!FSEEK(file,0,SEEK_END)) size=FTELL(file);
    if(size>4 && !FSEEK(file,0,SEEK_SET) &&
       FREAD(&state_bytes,1,sizeof(state_bytes),file)==sizeof(state_bytes) &&
       state_bytes && state_bytes<=(unsigned long)size-4) {
        /* The first word counts the compressed state only. The vendor
         * appends zlib data for a fixed buffer whose leading pixels are
         * the configured preview rectangle. */
        unsigned long offset=4ul+state_bytes;
        *present=1;
        unsigned x,y;
        size_t bytes=(size_t)size-offset;
        if(bytes && bytes<=STOCK_THUMB_BYTES+4096 && preview_rect() && slot_rect(slot,&x,&y) &&
           !FSEEK(file,(long)offset,SEEK_SET)) {
            uint16_t *frame=VAR(0x199910,uint16_t *);
            unsigned w=PAUSE_RECT[2], h=PAUSE_RECT[3];
            size_t out=STOCK_THUMB_BYTES;
            void *compressed=ALLOC(bytes);
            uint16_t *thumb=ALLOC(out);
            if(frame && compressed && thumb && FREAD(compressed,1,bytes,file)==bytes &&
               !FN(0x11bc0,int,void *,size_t *,const void *,size_t)(thumb,&out,compressed,bytes) &&
               out>=w*h*2) {
                scale_thumbnail(frame+y*640+x,86,60,thumb,w,h);
                PAUSE.thumb[slot]=thumb;
            } else if(thumb) FREE(thumb);
            if(compressed) FREE(compressed);
        }
    }
    FCLOSE(file);
    return NULL;
}

__attribute__((naked)) ENTRY void load_slot_probe(void)
{
    __asm__ volatile("mov r2, r8\n\tmov r3, r9\n\tb load_slot");
}

ENTRY void load_menu_copy(void *dest,const void *src,size_t bytes)
{
    if(PAUSE.replacement) { pause_wait(); release_thumbnails(); }
    COPY(dest,src,bytes);
}

static __attribute__((used)) int first_load_slot(const unsigned *present)
{
    if(PAUSE.replacement)
        for(unsigned slot=0;slot<PAUSE_SLOTS;++slot)
            if(present[slot]) return (int)slot;
    return -1;
}

static __attribute__((used)) void load_slot_frame(uint16_t *frame,unsigned w,unsigned h,
                                                 size_t pitch,int slot,bool first)
{
    if(PAUSE.replacement && w==640 && h==480 && pitch==1280 && frame && preview_rect()) {
        unsigned x=PAUSE_RECT[0], y=PAUSE_RECT[1], pw=PAUSE_RECT[2], ph=PAUSE_RECT[3];
        pause_wait();
        if(PAUSE.menu) pause_list(frame,2);
        if(slot>=0 && slot<PAUSE_SLOTS && PAUSE.thumb[slot]) {
            for(unsigned row=0;row<ph;++row)
                COPY(frame+(y+row)*640+x,PAUSE.thumb[slot]+row*pw,pw*2);
        } else {
            settings_box(frame,x,y,x+pw,y+ph,0x10a4);
            const char *label=slot<0?"NO SAVES":"NO PREVIEW";
            unsigned chars=slot<0?8:10;
            unsigned scale=pw>=12*chars?2:1;
            settings_text(frame,x+(pw-6*scale*chars)/2,y+(ph-7*scale)/2,label,scale,0xad96);
        }
        if(first && slot>=0 && slot<PAUSE_SLOTS && PAUSE_ART) {
            unsigned rx=PAUSE_ART[6].left+PAUSE_SLOT_MAP[slot][0];
            unsigned ry=PAUSE_ART[6].top+PAUSE_SLOT_MAP[slot][1];
            if(rx+96<640 && ry+66<480)
                FN(0x90f40,void,unsigned,unsigned,unsigned)(rx,ry,0xffff);
        }
    }
    DISP(frame,w,h,pitch);
}

/* The stock load loop keeps the selected slot in r4 and the active flag in
 * r5. Its six presence flags start 128 bytes into its stack frame. */
__attribute__((naked)) ENTRY void load_first_frame(void)
{
    __asm__ volatile(
        "push {r0-r3,r12,lr}\n\tadd r0, sp, #152\n\tbl first_load_slot\n\t"
        "mov r4, r0\n\tcmp r4, #0\n\tmovge r5, #1\n\tmovlt r5, #0\n\t"
        "pop {r0-r3,r12,lr}\n\t"
        "push {r4,r5,r12,lr}\n\tmov r12, #1\n\tstr r12, [sp, #4]\n\t"
        "bl load_slot_frame\n\tadd sp, sp, #12\n\tpop {pc}");
}

__attribute__((naked)) ENTRY void load_next_frame(void)
{
    __asm__ volatile(
        "push {r4,r5,r12,lr}\n\tmov r12, #0\n\tstr r12, [sp, #4]\n\t"
        "bl load_slot_frame\n\tadd sp, sp, #12\n\tpop {pc}");
}

static __attribute__((naked,noinline)) int stock_load_menu_body(void)
{
    __asm__ volatile("ldr r2, 1f\n\tldr pc, 2f\n\t1: .word 0x0010886c\n\t2: .word 0x91054");
}

ENTRY int load_menu(void)
{
    PAUSE.replacement=PAUSE_WIDTH==640 && PAUSE_HEIGHT==480 && shutdown_wait();
    PAUSE.accept_ready=false;
    int result=stock_load_menu_body();
    release_thumbnails();
    PAUSE.replacement=false;
    return result;
}

ENTRY unsigned load_slot_key(void)
{
    unsigned key=FN(0x86368,unsigned,void)();
    if(!PAUSE.replacement) return key;
    if(!(HOME_PAD&0x2000)) PAUSE.accept_ready=true;
    if(key==0x2000 && !PAUSE.accept_ready) return 0;
    if(key==0x10 || key==0x20 || key==0x40 || key==0x80) pause_wait();
    return key;
}

/* Both vanilla branches remain unchanged. B leaves the stock function
 * through its own epilogue with the same return value as a cancel. */
__attribute__((naked)) ENTRY void load_slot_cancel(void)
{
    __asm__ volatile("cmp r0, #0x4000\n\tmoveq r0, #1\n\tldreq pc, 1f\n\t"
                     "cmp r0, #64\n\tbx lr\n\t1: .word 0x91550");
}

static bool controls_layout(void)
{ return pause_layout(); }

static bool controls_turbo(void)
{ return VAR(0x1b9c74,int)>29; }

enum controls_focus { CONTROL_PLAYER, CONTROL_L1, CONTROL_R1, CONTROL_X,
                      CONTROL_Y, CONTROL_A, CONTROL_B };

static __attribute__((naked,noinline)) int stock_controls_body(void)
{
    __asm__ volatile("ldr ip, 1f\n\tldr pc, 2f\n\t1: .word 0x000d88e0\n\t2: .word 0x8f5c4");
}

static void controls_draw(uint16_t *frame,unsigned player,unsigned focus,bool editing,
                          unsigned selected,unsigned current);

ENTRY int controls_menu(void)
{
    if(!controls_layout()) return stock_controls_body();
    uint16_t *frame=FN(0x164abc,void *,size_t)(HOME_BYTES);
    if(!frame) return 1;
    static const uint8_t up[]={CONTROL_PLAYER,CONTROL_PLAYER,CONTROL_PLAYER,
                               CONTROL_R1,CONTROL_L1,CONTROL_R1,CONTROL_X};
    static const uint8_t down[]={CONTROL_X,CONTROL_Y,CONTROL_X,CONTROL_B,
                                 CONTROL_B,CONTROL_B,CONTROL_B};
    static const uint8_t left[]={CONTROL_PLAYER,CONTROL_L1,CONTROL_L1,
                                 CONTROL_Y,CONTROL_Y,CONTROL_X,CONTROL_Y};
    static const uint8_t right[]={CONTROL_PLAYER,CONTROL_R1,CONTROL_R1,
                                  CONTROL_A,CONTROL_X,CONTROL_A,CONTROL_A};
    static const uint8_t order[]={0,0,1,2,5,3,4};
    unsigned *map=(unsigned *)0x1bb770;
    unsigned focus=CONTROL_X, player=0, selected=0, held=HOME_PAD|0x2000;
    bool editing=false;
    for(;;) {
        unsigned *entry=map+player*6+order[focus];
        controls_draw(frame,player,focus,editing,selected,*entry);
        int battery=HOME_BATTERY;
        unsigned key;
        do {
            if(battery<0) FN(0x836b4,void,void)();
            FN(0x11f08,int,unsigned)(16000);
            key=settings_key_poll(&held);
        } while(!key && battery==HOME_BATTERY);
        if(!key) continue;
        if(key==0x4000) {
            if(!editing) break;
            editing=false;
        } else if(key==0x2000) {
            held|=key;
            if(editing) {
                if(*entry!=selected) {
                    *entry=selected;
                    VAR(0x1bb7d0,unsigned)=1;
                    FN(0xa34c0,void,const unsigned *,unsigned)(map,8);
                }
                editing=false;
            } else if(focus==CONTROL_PLAYER) player=(player+1)%4;
            else {
                selected=*entry;
                editing=true;
            }
            settings_confirm_sound();
        } else if(key==0x300 && !editing) {
            held|=key;
            FN(0x896ac,void,const char *)("default");
            settings_confirm_sound();
        } else if(key==0x10 || key==0x40 || key==0x80 || key==0x20) {
            if(editing) {
                unsigned input=selected&0xffff;
                input=input>=12?0:(input+(key==0x80 || key==0x10?11:1))%12;
                selected=(selected&0xffff0000)|input;
            } else if(focus==CONTROL_PLAYER && (key==0x80 || key==0x20))
                player=(player+(key==0x80?3:1))%4;
            else
                focus=key==0x10?up[focus]:key==0x40?down[focus]:key==0x80?left[focus]:right[focus];
            vesper_transition(1);
        } else if(editing && key==0x1000 && controls_turbo()) {
            held|=key;
            selected^=0x10000;
            vesper_transition(1);
        }
    }
    pause_wait();
    FN(0x164d58,void,void *)(frame);
    return 1;
}

static void controls_round(uint16_t *frame,unsigned x,unsigned y,unsigned w,unsigned h,
                           unsigned radius,uint16_t ink)
{
    for(unsigned row=0;row<h;++row) {
        unsigned distance=row<h/2?row:h-1-row, inset=0;
        if(distance<radius) {
            unsigned rise=radius-distance-1;
            while((radius-inset)*(radius-inset)+rise*rise>radius*radius) ++inset;
        }
        settings_box(frame,x+inset,y+row,x+w-inset,y+row+1,ink);
    }
}

static void controls_shape(uint16_t *frame,unsigned x,unsigned y,unsigned w,unsigned h,
                            unsigned rounding,uint16_t edge,uint16_t fill)
{
    controls_round(frame,x,y,w,h,rounding,edge);
    controls_round(frame,x+1,y+1,w-2,h-2,rounding-1,fill);
}

static void controls_keycap(uint16_t *frame,unsigned x,unsigned y,unsigned w,unsigned h,
                            const char *label,bool active,uint16_t accent)
{
    unsigned rounding=(w==h)?w/2:8;
    controls_shape(frame,x,y,w,h,rounding,active?accent:0x6c13,active?0x49a3:0x1948);
    if(active) controls_round(frame,x+3,y+3,w-6,h-6,rounding-3,0x49a3);
    unsigned size=w>=40?23:18;
    int width=pause_measure(frame,(int)size,label);
    if(width>0 && width<=(int)w)
        pause_label(frame,x+(w-width)/2,(int)y+((int)h+(int)size)/2-31,
                    size,active?accent:0xffff,label);
}

static void controls_draw(uint16_t *frame,unsigned player,unsigned focus,bool editing,
                          unsigned selected,unsigned current)
{
    static const char *const players[]={"Player 1","Player 2","Player 3","Player 4"};
    static const char *const buttons[]={"","L1","R1","X","Y","A","B"};
    /* Low bits index the pinned vendor table at 0x198564. B is zero. */
    static const char *const mapped[]={"B","Y","Select","Start","Up","Down",
                                      "Left","Right","A","X","L1","R1"};
    static const uint8_t defaults[]={0,10,11,9,1,8,0};
    static const uint16_t x[]={0,73,247,253,212,286,253};
    static const uint16_t y[]={0,100,100,153,194,194,234};
    const uint16_t accent=S.applied_classic?0x8f5e:0xfe49, soft=0xa5f9;
    unsigned binding=current&0xffff, draft=(editing?selected:current)&0xffff;
    const char *actual=binding<12?mapped[binding]:"Custom";
    const char *target=draft<12?mapped[draft]:"Custom";
    pause_wait();
    settings_reset_text_clip();
    settings_box(frame,0,0,640,480,0x08a4);
    settings_box(frame,0,0,640,59,0x1127);
    settings_box(frame,0,58,640,59,0x320c);
    pause_label(frame,25,7,32,0xffff,"Controls");
    controls_shape(frame,388,13,115,32,16,focus==0?accent:0x3aad,0x08c4);
    pause_label(frame,410,5,22,0xffff,players[player]);
    home_battery(frame,HOME_BATTERY);

    controls_shape(frame,25,80,328,272,17,0x29ea,0x1106);
    controls_shape(frame,58,116,263,214,24,0x326c,0x1127);
    controls_shape(frame,67,125,245,194,19,0x32ad,0x1148);
    controls_shape(frame,65,170,95,95,47,0x296a,0x1127);
    controls_shape(frame,225,170,95,95,47,0x296a,0x1127);
    controls_shape(frame,75,207,74,24,6,0x530c,0x21cb);
    controls_shape(frame,100,182,24,74,6,0x530c,0x21cb);
    settings_box(frame,101,208,123,230,0x21cb);
    controls_shape(frame,105,211,14,15,7,0x3aad,0x1948);
    controls_shape(frame,145,276,39,10,5,0x3aad,0x21cb);
    controls_shape(frame,192,276,39,10,5,0x3aad,0x21cb);
    for(unsigned stick=126;stick<=254;stick+=128) {
        controls_shape(frame,stick-19,298,38,38,19,0x32ac,0x1127);
        controls_shape(frame,stick-12,305,24,24,12,0x530c,0x21cb);
    }
    pause_label(frame,40,317,15,soft,"HANDHELD");
    for(unsigned i=1;i<=6;++i)
        controls_keycap(frame,x[i],y[i],i<=2?61:40,i<=2?34:40,buttons[i],focus==i,accent);

    controls_shape(frame,372,80,243,272,17,0x32ac,0x1127);
    if(!focus) {
        pause_label(frame,392,86,19,accent,"PLAYER");
        pause_label(frame,392,139,27,0xffff,players[player]);
        pause_label(frame,392,205,19,soft,"Change with Left / Right.");
    } else {
        if(editing) controls_shape(frame,386,94,95,29,14,0x9465,0x49a3);
        pause_label(frame,editing?396:392,86,19,editing?accent:soft,
                    editing?"EDITING":"SELECTED BUTTON");
        controls_keycap(frame,396,142,46,46,buttons[focus],true,accent);
        settings_box(frame,459,165,488,167,soft);
        for(unsigned i=0;i<7;++i) {
            settings_box(frame,482+i,158+i,484+i,160+i,soft);
            settings_box(frame,482+i,172-i,484+i,174-i,soft);
        }
        unsigned width=(draft>=2 && draft<=7) || draft>=12?94:46;
        controls_keycap(frame,(width>46?549:532)-width/2,142,width,46,target,false,accent);
        pause_label(frame,388,183,17,soft,"Handheld");
        pause_label(frame,502,183,17,soft,"In game");
        settings_box(frame,391,224,596,225,0x320c);
        if(editing) {
            pause_label(frame,392,234,24,0xffff,"Choose a game input");
            pause_label(frame,392,266,18,soft,"Current mapping:");
            pause_label(frame,530,266,18,0xffff,actual);
            if(controls_turbo())
                pause_label(frame,392,299,17,selected>>16?accent:soft,
                            selected>>16?"X  Turbo on":"X  Turbo off");
        } else {
            bool standard=current==defaults[focus];
            pause_label(frame,392,235,25,0xffff,standard?"Default mapping":"Button mapping");
            if(current>>16) pause_label(frame,392,265,18,accent,"Turbo enabled");
        }
    }

    controls_shape(frame,25,370,590,51,10,0x29ea,0x1127);
    controls_keycap(frame,38,380,36,30,"L2",false,accent);
    pause_label(frame,79,375,20,soft,"+");
    controls_keycap(frame,97,380,36,30,"R2",false,accent);
    pause_label(frame,150,373,22,0xffff,"Save as default for this system");
    settings_box(frame,0,432,640,480,0x1127);
    settings_box(frame,0,432,640,433,0x320c);
    menu_button(frame,25,442,BUTTON_DPAD);
    pause_label(frame,62,430,22,0xffff,editing?"Change":"Move");
    menu_button(frame,233,442,BUTTON_A);
    pause_label(frame,270,430,22,0xffff,editing?"Apply":focus?"Remap":"Next player");
    menu_button(frame,509,442,BUTTON_B);
    pause_label(frame,546,430,22,0xffff,editing?"Cancel":"Back");
    bool owned=HOME.own_battery;
    own_menu_battery(true);
    DISP(frame,640,480,1280);
    own_menu_battery(owned);
}
