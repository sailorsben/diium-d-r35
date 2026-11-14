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
    uint16_t *exit_background, *controls_frame;
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

static __attribute__((naked,noinline)) int stock_controls_body(void)
{
    __asm__ volatile("ldr ip, 1f\n\tldr pc, 2f\n\t1: .word 0x000d88e0\n\t2: .word 0x8f5c4");
}

ENTRY int controls_menu(void)
{
    if(controls_layout())
        PAUSE.controls_frame=FN(0x164abc,void *,size_t)(HOME_BYTES);
    if(PAUSE.controls_frame) {
        int result=stock_controls_body();
        pause_wait();
        FN(0x164d58,void,void *)(PAUSE.controls_frame);
        PAUSE.controls_frame=NULL;
        return result;
    }
    if(!controls_layout()) return stock_controls_body();
    const unsigned origin[7][2]={{261,206},{398,128},{512,128},{398,206},
                                 {512,206},{398,284},{512,284}};
    unsigned old[7][4];
    /* The stock selector and text renderer share these seven rectangles. */
    for(unsigned i=0;i<7;++i) {
        unsigned *rect=(unsigned *)(0x19a2e4+132*i);
        COPY(old[i],rect,sizeof(old[i]));
        rect[2]=origin[i][0]+old[i][2]-old[i][0];
        rect[3]=origin[i][1]+old[i][3]-old[i][1];
        rect[0]=origin[i][0];
        rect[1]=origin[i][1];
    }
    int result=stock_controls_body();
    for(unsigned i=0;i<7;++i) COPY((void *)(0x19a2e4+132*i),old[i],sizeof(old[i]));
    return result;
}

static __attribute__((used)) void controls_paint(uint16_t *original,unsigned w,unsigned h,
                                                size_t pitch,unsigned player)
{
    uint16_t *frame=PAUSE.controls_frame;
    if(!frame || w!=640 || h!=480 || pitch!=1280) {
        DISP(original,w,h,pitch);
        return;
    }
    if(player>3) player=0;
    pause_wait();
    settings_reset_text_clip();
    const uint16_t accent=S.applied_classic?0x8f5e:0xfe49;
    const char *const player_names[]={"Player 1","Player 2","Player 3","Player 4"};
    const char *const buttons[]={"L1","R1","X","Y","A","B"};
    /* Low bits index the pinned vendor's table at 0x198564; B is zero. */
    const char *const mapped[]={"B","Y","Select","Start","Up","Down",
        "Left","Right","A","X","L1","R1"};
    const unsigned order[]={0,1,2,5,3,4};
    int focus=VAR(0x1998f0,int);
    settings_box(frame,0,0,640,480,0x08a4);
    settings_box(frame,0,0,640,68,0x1127);
    settings_box(frame,0,67,640,68,0x320c);
    pause_label(frame,24,2,32,0xffff,"Controls");
    settings_box(frame,385,14,504,45,focus==0?accent:0x320c);
    settings_box(frame,386,15,503,44,focus==0?0x21ab:0x1127);
    pause_label(frame,402,5,21,0xffff,player_names[player]);
    home_battery(frame,HOME_BATTERY);
    pause_label(frame,29,65,20,0x9d17,"BUTTON MAPPING");
    for(unsigned i=0;i<6;++i) {
        unsigned x=25+296*(i%2), y=104+91*(i/2);
        unsigned mapping=((const unsigned *)0x1bb770)[player*6+order[i]];
        unsigned binding=mapping&0xffff;
        bool active=focus==(int)i+1;
        settings_box(frame,x,y,x+288,y+76,active?accent:0x320c);
        settings_box(frame,x+1,y+1,x+287,y+75,active?0x21ab:0x1127);
        settings_box(frame,x+13,y+19,x+65,y+58,0x08a4);
        pause_label(frame,x+27,y+12,23,accent,buttons[i]);
        pause_label(frame,x+81,y+2,17,0x9d17,"IN GAME");
        pause_label(frame,x+81,y+25,27,0xffff,binding<12?mapped[binding]:"Custom");
        if(mapping>>16) pause_label(frame,x+211,y+34,16,accent,"TURBO");
    }
    settings_box(frame,25,380,615,430,0x1127);
    settings_box(frame,25,380,27,430,accent);
    pause_label(frame,39,383,21,accent,"L2 + R2");
    pause_label(frame,143,383,21,0xffff,"Save as default for this system");
    settings_box(frame,0,432,640,480,0x10e6);
    menu_button(frame,25,442,BUTTON_DPAD);
    pause_label(frame,62,430,22,0xffff,"Move / change");
    menu_button(frame,254,442,BUTTON_A);
    pause_label(frame,291,430,22,0xffff,"Edit / apply");
    menu_button(frame,514,442,BUTTON_B);
    pause_label(frame,551,430,22,0xffff,"Back");
    bool owned=HOME.own_battery;
    own_menu_battery(true);
    DISP(frame,w,h,pitch);
    own_menu_battery(owned);
}

ENTRY void controls_first(uint16_t *frame,unsigned w,unsigned h,size_t pitch)
{ controls_paint(frame,w,h,pitch,0); }

__attribute__((naked)) ENTRY void controls_next(void)
{
    __asm__ volatile("push {r4, lr}\n\tldr r4, [sp,#16]\n\tsub sp, sp, #8\n\t"
                     "str r4, [sp]\n\tbl controls_paint\n\tadd sp, sp, #8\n\tpop {r4, pc}");
}

ENTRY void controls_panel(uint16_t *frame,size_t pitch,struct art_block *art,unsigned block)
{
    if(PAUSE.controls_frame) {
        FN(0x803a8,void,void *,size_t,struct art_block *,unsigned)(frame,pitch,art,block);
        return;
    }
    if(!controls_layout() || !frame || pitch!=1280) {
        FN(0x803a8,void,void *,size_t,struct art_block *,unsigned)(frame,pitch,art,block);
        return;
    }
    pause_wait();
    const uint16_t accent=S.applied_classic?0x8f5e:0xfe49, panel=0x10e6, edge=0x3a8d;
    settings_box(frame,230,56,640,480,0x08a4);
    settings_box(frame,235,74,623,453,edge);
    settings_box(frame,236,75,622,452,panel);
    settings_text(frame,254,93,"CONTROLS",2,accent);
    settings_box(frame,254,111,603,112,edge);
    settings_box(frame,252,199,358,254,edge);
    settings_box(frame,253,200,357,253,0x08a4);
    const char *keys[]={"L1","R1","X","Y","A","B"};
    for(unsigned i=0;i<6;++i) {
        unsigned x=369+114*(i%2), y=118+78*(i/2);
        settings_box(frame,x,y,x+106,y+58,edge);
        settings_box(frame,x+1,y+1,x+105,y+57,0x08a4);
        /* settings_text only has letters. Paint the shoulder's 1 here. */
        settings_text(frame,x+10,y+18,keys[i],2,accent);
        if(i<2) {
            settings_box(frame,x+26,y+18,x+28,y+32,accent);
            settings_box(frame,x+24,y+20,x+26,y+22,accent);
        }
    }
    settings_box(frame,254,354,603,355,edge);
    FN(0x85c94,void,void *,int,int,int,unsigned,const char *)(
        frame,254,352,18,accent,"L2 + R2  Save these controls");
    FN(0x85c94,void,void *,int,int,int,unsigned,const char *)(
        frame,254,375,18,accent,"as the default for this system.");
}

ENTRY void controls_preview(void *dest,const void *source)
{
    if(!controls_layout()) FN(0x8f538,void,void *,const void *)(dest,source);
}

ENTRY void controls_help_first(void *frame,int x,int y,int height,unsigned color,const char *text)
{
    if(!controls_layout())
        FN(0x85c94,void,void *,int,int,int,unsigned,const char *)(frame,x,y,height,color,text);
}
