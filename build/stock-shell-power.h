/* This action is reachable only from Settings, outside a game or update. */
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

static void shutdown_message(const char *title,const char *detail,const char *keys)
{
    void (*wait)(void)=shutdown_wait();
    if(!wait) return;
    wait();
    uint16_t *frame=S.power_frame;
    settings_box(frame,70,158,570,321,0x43af);
    settings_box(frame,72,160,568,319,0x08a3);
    settings_text(frame,102,184,title,3,0xffff);
    settings_text(frame,102,237,detail,2,0xd6da);
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
    shutdown_message("POWER OFF","SAVE DATA WILL BE FLUSHED","A POWER OFF     B CANCEL");
}

static void shutdown_cancel(void)
{
    void (*wait)(void)=shutdown_wait();
    if(!wait) return;
    wait();
    FN(0x164d58,void,void *)(S.power_frame);
    S.power_frame=NULL;
    DISP(S.settings_pixels,640,480,1280);
}

static void shutdown_confirm(void)
{
    int (*command)(const char *)=FN(0x11d4c,int,const char *);
    shutdown_message("POWERING OFF","SECURING THE SD CARD","PLEASE WAIT");
    int status=command("/bin/sh " SHUTDOWN_SCRIPT);
    if(status==(2<<8)) {
        shutdown_message("SHUTDOWN PAUSED","CHECK THE SD CARD ON PC","USE THE POWER BUTTON");
        for(;;) FN(0x11f08,int,unsigned)(200000);
    }
    if(status) {
        shutdown_message("CARD NOT SECURED","SHUTDOWN COULD NOT START","A RETRY     B CANCEL");
        return;
    }
    shutdown_message("SD CARD SAFE","REQUESTING POWER OFF","");
    if(command("/sbin/poweroff")) {
        shutdown_message("SD CARD SAFE","POWER OFF REQUEST FAILED","USE THE POWER BUTTON");
    }
    /* Keep the last message visible until init stops the launcher. If the
     * request fails, returning to normal UI would allow writes to a RO card. */
    for(;;) FN(0x11f08,int,unsigned)(200000);
}
