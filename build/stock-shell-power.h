/* Home and Settings share the same confirmed shutdown outside games and updates. */
#define SHUTDOWN_SCRIPT "/usr/retro/d35-launcher1/power-off.sh"

static bool shutdown_available(void)
{
    return FN(0x11e0c,int,const char *,int)(SHUTDOWN_SCRIPT,4)==0;
}

static void (*shutdown_wait(void))(void)
{
    void *driver=VAR(0x1b81a8,void *);
    return driver?SYM(driver,"WaitDisp"):NULL;
}

enum power_view { POWER_CONFIRM, POWER_WORKING, POWER_PAUSED, POWER_RETRY,
                  POWER_SECURED, POWER_FAILED, POWER_VIEW_COUNT };

#ifdef D35_HOME_GRID
enum { POWER_X=77, POWER_Y=153, POWER_W=486, POWER_H=174,
       POWER_PANEL_PIXELS=POWER_W*POWER_H };
static void shutdown_confirm(void);

static uint16_t *read_dialog_art(const char *name,const char *signature,size_t theme_bytes)
{
    char path[384];
    if(!suffix(path,sizeof(path),WORK(),name)) return NULL;
    FILE *file=FOPEN(path,"rb");
    if(!file) return NULL;
    char version[4];
    uint16_t *art=NULL;
    if(!FSEEK(file,0,SEEK_END) && FTELL(file)==(long)(2*theme_bytes+4) &&
       !FSEEK(file,-4,SEEK_END) && FREAD(version,1,4,file)==4 && !CMP(version,signature,4) &&
       !FSEEK(file,S.applied_classic?(long)theme_bytes:0,SEEK_SET)) {
        art=ALLOC(theme_bytes);
        if(art && FREAD(art,1,theme_bytes,file)!=theme_bytes) { FREE(art); art=NULL; }
    }
    FCLOSE(file);
    return art;
}

static void shutdown_prepare_art(void)
{
    S.power_choice=false;
    S.power_dimmed=false;
    S.power_art=read_dialog_art(LAUNCHER "/power-dialog.rgb565","D35P",
                                POWER_VIEW_COUNT*POWER_PANEL_PIXELS*sizeof(uint16_t));
}

static void shutdown_release_art(void)
{
    FREE((void *)S.power_art);
    S.power_art=NULL;
}

static void dialog_panel(uint16_t *frame,const uint16_t *panel)
{
    for(unsigned y=0;y<POWER_H;++y)
        for(unsigned x=0;x<POWER_W;++x) {
            uint16_t pixel=panel[y*POWER_W+x];
            if(pixel) frame[(POWER_Y+y)*640+POWER_X+x]=pixel;
        }
}

static void dialog_highlight(uint16_t *frame,unsigned x,unsigned y,unsigned width,unsigned height)
{
    const uint16_t ink=S.applied_classic?0x8f5e:0xfeb0;
    /* Follow the rounded action edge. The unselected card comes from the asset. */
    for(unsigned row=0;row<height;++row) {
        static const uint8_t inset[]={7,5,3,2,2,1,1,0};
        unsigned cap=row<height/2?row:height-1-row;
        unsigned edge=cap<8?inset[cap]:0;
        if(!cap) {
            settings_box(frame,x+edge,y+row,x+width-edge,y+row+1,ink);
        } else {
            settings_box(frame,x+edge,y+row,x+edge+1,y+row+1,ink);
            settings_box(frame,x+width-edge-1,y+row,x+width-edge,y+row+1,ink);
        }
    }
}
#endif

static void shutdown_message(enum power_view view,const char *title,const char *detail,const char *keys)
{
    void (*wait)(void)=shutdown_wait();
    if(!wait) return;
    wait();
    uint16_t *frame=S.power_frame;
#ifdef D35_HOME_GRID
    S.power_view=view;
    bool choices=view==POWER_CONFIRM || view==POWER_RETRY;
    if(!S.power_dimmed) {
        for(unsigned i=0;i<640*480;++i) frame[i]=(frame[i]>>1)&0x7bef;
        S.power_dimmed=true;
    }
    if(S.power_art) {
        const uint16_t *panel=S.power_art+view*POWER_PANEL_PIXELS;
        dialog_panel(frame,panel);
        if(choices)
            dialog_highlight(frame,POWER_X+(S.power_choice?251:61),POWER_Y+111,174,37);
        DISP(frame,640,480,1280);
        return;
    }
#else
    (void)view;
#endif
    settings_box(frame,70,158,570,321,0x43af);
    settings_box(frame,72,160,568,319,0x08a3);
    settings_text(frame,102,184,title,3,0xffff);
    settings_text(frame,102,237,detail,2,0xd6da);
#ifdef D35_HOME_GRID
    if(choices) {
        unsigned left=137, right=328;
        settings_box(frame,left,264,left+175,294,0x1127);
        settings_box(frame,right,264,right+175,294,0x1127);
        dialog_highlight(frame,S.power_choice?right:left,264,175,30);
        settings_text(frame,188,272,"CANCEL",2,0xffff);
        settings_text(frame,364,272,view==POWER_RETRY?"RETRY":"TURN OFF",2,0xffff);
        settings_text(frame,139,301,"LEFT RIGHT CHOOSE   A CONFIRM",2,0xaf9e);
    } else
#endif
    settings_text(frame,102,283,keys,2,0xaf9e);
    DISP(frame,640,480,1280);
}

static void shutdown_open(void)
{
    void (*wait)(void)=shutdown_wait();
    if(!wait) return;
    wait();
    S.power_frame=FN(0x164abc,void *,size_t)(614400);
    if(!S.power_frame) return;
    COPY(S.power_frame,S.settings_pixels,614400);
    S.accept_held=button_down(0x204);
#ifdef D35_HOME_GRID
    shutdown_prepare_art();
#endif
    shutdown_message(POWER_CONFIRM,"POWER OFF","SAVE DATA WILL BE FLUSHED","A POWER OFF     B CANCEL");
}

static void shutdown_cancel(void)
{
    void (*wait)(void)=shutdown_wait();
    if(!wait) return;
    wait();
    FN(0x164d58,void,void *)(S.power_frame);
    S.power_frame=NULL;
#ifdef D35_HOME_GRID
    shutdown_release_art();
#endif
    DISP(S.settings_pixels,640,480,1280);
}

static void shutdown_confirm(void)
{
    int (*command)(const char *)=FN(0x11d4c,int,const char *);
    shutdown_message(POWER_WORKING,"POWERING OFF","SECURING THE SD CARD","PLEASE WAIT");
    int status=command("/bin/sh " SHUTDOWN_SCRIPT);
    if(status==(2<<8)) {
        shutdown_message(POWER_PAUSED,"SHUTDOWN PAUSED","CHECK THE SD CARD ON PC","USE THE POWER BUTTON");
        for(;;) FN(0x11f08,int,unsigned)(200000);
    }
    if(status) {
#ifdef D35_HOME_GRID
        S.power_choice=false;
#endif
        shutdown_message(POWER_RETRY,"CARD NOT SECURED","SHUTDOWN COULD NOT START","A RETRY     B CANCEL");
        return;
    }
    shutdown_message(POWER_SECURED,"SD CARD SAFE","REQUESTING POWER OFF","");
    if(command("/sbin/poweroff")) {
        shutdown_message(POWER_FAILED,"SD CARD SAFE","POWER OFF REQUEST FAILED","USE THE POWER BUTTON");
    }
    /* Keep the last message visible until init stops the launcher. If the
     * request fails, returning to normal UI would allow writes to a RO card. */
    for(;;) FN(0x11f08,int,unsigned)(200000);
}

#ifdef D35_HOME_GRID
/* True means dismiss; Home and Settings restore their own backgrounds. */
static bool shutdown_input(unsigned key)
{
    if(key==0x4000) return true;
    if(key==0x80 || key==0x20) {
        bool turn_off=key==0x20;
        if(S.power_choice!=turn_off) {
            S.power_choice=turn_off;
            if(S.power_view==POWER_RETRY)
                shutdown_message(POWER_RETRY,"CARD NOT SECURED","SHUTDOWN COULD NOT START","");
            else
                shutdown_message(POWER_CONFIRM,"POWER OFF","SAVE DATA WILL BE FLUSHED","");
        }
    } else if(key==0x2000 && !S.accept_held) {
        S.accept_held=true;
        if(!S.power_choice) return true;
        shutdown_confirm();
    }
    return false;
}
#endif
