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
};
#define PAUSE VAR(0x1c4400,struct pause_ui)
_Static_assert(sizeof(struct pause_ui)<=0x100, "pause UI reservation");

static void pause_wait(void)
{
    void (*wait)(void)=shutdown_wait();
    if(wait) wait();
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

static bool controls_layout(void)
{ return LOCALE==1 && PAUSE_WIDTH==640 && PAUSE_HEIGHT==480; }

static __attribute__((naked,noinline)) int stock_controls_body(void)
{
    __asm__ volatile("ldr ip, 1f\n\tldr pc, 2f\n\t1: .word 0x000d88e0\n\t2: .word 0x8f5c4");
}

ENTRY int controls_menu(void)
{
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

ENTRY void controls_panel(uint16_t *frame,size_t pitch,struct art_block *art,unsigned block)
{
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
