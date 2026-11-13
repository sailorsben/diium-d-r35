/* D-R35 stock launcher overlay. The firmware writer keeps its own frame and
 * all of its original validation, retry and shutdown logic. */
enum { FLASH_W=640, FLASH_H=480, FLASH_PITCH=1280, FLASH_BYTES=614400 };
struct vesper_overlay {
    uint16_t *frame;
    void (*wait)(void);
    unsigned percent, drawn;
    bool preview, failed, requested;
    void *effect;
    size_t effect_bytes;
    bool effect_checked;
};
#define VESPER VAR(0x1c4200, struct vesper_overlay)
_Static_assert(sizeof(struct vesper_overlay)<=0x100, "Vesper overlay reservation");
#define PREVIEW_MARKER LAUNCHER "/vesper-preview.once"
#define PREVIEW_USED LAUNCHER "/vesper-preview.used"

ENTRY void vesper_menu_effect(unsigned channel,const struct sound *original)
{
    if(channel==1 && (original==(void *)0x1b9d18 || original==(void *)0x1b9d44) &&
       original->data) {
        if(!VESPER.effect_checked) {
            char path[384];
            VESPER.effect_checked=true;
            if(suffix(path,sizeof(path),WORK(),LAUNCHER "/d35-transition.pcm"))
                VESPER.effect=read_bytes(path,44100,&VESPER.effect_bytes);
            if(VESPER.effect_bytes%4) {
                FREE(VESPER.effect);
                VESPER.effect=NULL;
            }
        }
        if(VESPER.effect) {
            const struct sound cue={VESPER.effect,2,1,1,44100,0,VESPER.effect,
                                    (uint8_t *)VESPER.effect+VESPER.effect_bytes,0};
            FN(0x8750c,void,unsigned,const struct sound *)(channel,&cue);
            return;
        }
    }
    FN(0x8750c,void,unsigned,const struct sound *)(channel,original);
}

static bool vesper_frame_open(void)
{
    char path[384];
    void *driver=VAR(0x1b81a8,void *);
    VESPER.wait=driver?SYM(driver,"WaitDisp"):NULL;
    if(!VESPER.wait || !suffix(path,sizeof(path),WORK(),LAUNCHER "/vesper-update.rgb565"))
        return false;
    FILE *asset=FOPEN(path,"rb");
    if(!asset) return false;
    bool valid=!FSEEK(asset,0,SEEK_END) && FTELL(asset)==FLASH_BYTES && !FSEEK(asset,0,SEEK_SET);
    if(valid) {
        VESPER.frame=FN(0x164abc,void *,size_t)(FLASH_BYTES);
        if(VESPER.frame && FREAD(VESPER.frame,1,FLASH_BYTES,asset)!=FLASH_BYTES) {
            FN(0x164d58,void,void *)(VESPER.frame);
            VESPER.frame=NULL;
        }
    }
    FCLOSE(asset);
    VESPER.percent=0;
    VESPER.drawn=101;
    VESPER.failed=false;
    return VESPER.frame!=NULL;
}

static void vesper_frame_close(void)
{
    if(!VESPER.frame) return;
    VESPER.wait();
    FN(0x164d58,void,void *)(VESPER.frame);
    VESPER.frame=NULL;
}

static void vesper_number(uint16_t *frame,unsigned percent)
{
    static const uint8_t digits[][7]={
        {14,17,19,21,25,17,14},{4,12,4,4,4,4,14},{14,17,1,2,4,8,31},
        {30,1,1,14,1,1,30},{2,6,10,18,31,2,2},{31,16,16,30,1,1,30},
        {14,16,16,30,17,17,14},{31,1,2,4,8,8,8},{14,17,17,14,17,17,14},
        {14,17,17,15,1,1,14},{25,26,2,4,8,11,19}
    };
    unsigned sequence[]={percent/100,percent/10%10,percent%10,10};
    for(unsigned i=percent>=100?0:percent>=10?1:2;i<4;++i)
        for(unsigned y=0;y<7;++y)
            for(unsigned x=0;x<5;++x)
                if(digits[sequence[i]][y]&(16u>>x))
                    settings_box(frame,506+12*i+2*x,347+2*y,508+12*i+2*x,349+2*y,0xaf9e);
}

static void vesper_draw(unsigned percent)
{
    uint16_t *frame=VESPER.frame;
    if(!frame || percent==VESPER.drawn) return;
    VESPER.wait();
    settings_box(frame,504,344,554,365,0x0041);
    vesper_number(frame,percent);
    if(percent) settings_box(frame,89,373,89+(462u*percent)/100,384,0x673d);
    if(VESPER.preview) {
        settings_box(frame,65,403,575,433,0x0041);
        settings_text(frame,140,411,"PREVIEW   NO FIRMWARE WRITES",2,0xaf9e);
    } else if(percent==100) {
        settings_box(frame,85,340,500,368,0x0041);
        settings_text(frame,88,347,"UPDATE COMPLETE",2,0xaf9e);
    }
    DISP(frame,FLASH_W,FLASH_H,FLASH_PITCH);
    VESPER.drawn=percent;
}

ENTRY void vesper_update_prepare(void *frame,unsigned w,unsigned h,size_t pitch)
{
    if(VESPER.requested && frame && w==FLASH_W && h==FLASH_H && pitch==FLASH_PITCH && vesper_frame_open())
        vesper_draw(0);
    else DISP(frame,w,h,pitch);
}

/* The stock printf at this call site receives the offset and the percent
 * for the next sector. The stock comparison advances the offset. */
ENTRY void vesper_update_percent(const char *format,unsigned offset,unsigned percent)
{
    VESPER.percent=percent<100?percent:99;
    FN(0x1301c,void,const char *,unsigned,unsigned)(format,offset,percent);
}

ENTRY void vesper_update_progress(void *frame,unsigned w,unsigned h,size_t pitch)
{
    if(VESPER.frame) vesper_draw(VESPER.percent);
    else DISP(frame,w,h,pitch);
}

ENTRY void vesper_update_complete(void *frame,unsigned w,unsigned h,size_t pitch)
{
    if(VESPER.frame) vesper_draw(100);
    else DISP(frame,w,h,pitch);
}

ENTRY void vesper_update_detail(void *frame,unsigned w,unsigned h,size_t pitch)
{
    if(!VESPER.frame) DISP(frame,w,h,pitch);
}

ENTRY int vesper_update_program(void *image,unsigned bytes)
{
    int status=FN(0x130a0,int,void *,unsigned)(image,bytes);
    if(!status && VESPER.frame) {
        VESPER.wait();
        settings_box(VESPER.frame,76,303,564,437,0x0041);
        settings_text(VESPER.frame,164,338,"FIRMWARE UPDATE FAILED",2,0xfd49);
        settings_text(VESPER.frame,146,374,"KEEP POWER CONNECTED",2,0xffff);
        DISP(VESPER.frame,FLASH_W,FLASH_H,FLASH_PITCH);
        VESPER.failed=true;
    }
    return status;
}

static bool take_vesper_preview(void)
{
    char armed[384], used[384];
    if(!suffix(armed,sizeof(armed),WORK(),PREVIEW_MARKER) ||
       FN(0x11e0c,int,const char *,int)(armed,0) ||
       !suffix(used,sizeof(used),WORK(),PREVIEW_USED)) return false;
    int (*rename_file)(const char *,const char *)=SYM(NULL,"rename");
    if(!rename_file || rename_file(armed,used)) return false;
    FN(0x11b30,void,void)();
    return true;
}

static void vesper_preview_log(bool shown)
{
    char path[384];
    if(!suffix(path,sizeof(path),WORK(),LAUNCHER "/vesper-preview.log")) return;
    FILE *log=FOPEN(path,"wb");
    if(!log) return;
    const char *line=shown?"vesper-preview=complete frames=14 spi=unused\n":
                           "vesper-preview=display-unavailable spi=unused\n";
    size_t size=0;
    while(line[size]) ++size;
    FN(0x11eb4,size_t,const void *,size_t,size_t,FILE *)(line,1,size,log);
    FCLOSE(log);
    FN(0x11b30,void,void)();
}

ENTRY void vesper_update(const char *package)
{
    VESPER.requested=!FN(0x11e0c,int,const char *,int)(package,0);
    if(!VESPER.requested && take_vesper_preview()) {
        bool shown=vesper_frame_open();
        if(shown) {
            VESPER.preview=true;
            for(unsigned percent=0;percent<=96;percent+=8) {
                VESPER.percent=percent;
                vesper_update_progress(NULL,0,0,0);
                FN(0x11f08,int,unsigned)(185000);
            }
            vesper_update_complete(NULL,0,0,0);
            FN(0x11f08,int,unsigned)(850000);
            vesper_frame_close();
            VESPER.preview=false;
        }
        vesper_preview_log(shown);
        return;
    }
    FN(0x133fc,void,const char *)(package);
    if(VESPER.frame && VESPER.drawn!=100 && !VESPER.failed) {
        VESPER.wait();
        settings_box(VESPER.frame,76,303,564,437,0x0041);
        settings_text(VESPER.frame,158,351,"UPDATE COULD NOT START",2,0xfd49);
        DISP(VESPER.frame,FLASH_W,FLASH_H,FLASH_PITCH);
        VESPER.failed=true;
    }
    if(VESPER.failed) FN(0x11f08,int,unsigned)(1200000);
    vesper_frame_close();
    VESPER.failed=false;
}
