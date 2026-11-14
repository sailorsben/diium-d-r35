/* The English Home owns the scrolling Settings screen. Keep the stock
 * locale chooser and factory-reset handlers available through their menus. */
#define UI_FRAME VAR(0x199910,uint16_t *)
#define UI_WIDTH VAR(0x199914,unsigned)
#define UI_HEIGHT VAR(0x199918,unsigned)
#define LED_STEP VAR(0x199ee0,int)
#define VOLUME_STEP VAR(0x1998dc,int)
#define STOCK_VOLUME VAR(0x1b9b4c,volatile int)
#define TIMER_HANDLE VAR(0x19958c,int)
#define UI_WORKERS VAR(0x19bc18,volatile unsigned)

enum { ROW_BRIGHTNESS, ROW_VOLUME, ROW_MUSIC, ROW_THEME, ROW_BATTERY,
       ROW_FRAME_SKIP, ROW_LANGUAGE, ROW_POWER, ROW_RESET, ROW_COUNT,
       VISIBLE_ROWS=5, MUSIC_FILES_MAX=64 };

struct settings_screen {
    uint16_t *frame;
    char (*tracks)[MUSIC_NAME_MAX+1];
    unsigned row, top, track_count;
    bool factory, reset_confirmed, language, language_opened;
    unsigned factory_steps, language_held;
    const char *message;
};
#define SETTINGS VAR(0x1c4700,struct settings_screen)
_Static_assert(sizeof(struct settings_screen)<=0x100, "settings screen reservation");

static unsigned bounded_level(int value, unsigned max)
{ return value<0?0:(unsigned)value>max?max:(unsigned)value; }

/* SetLEDLevel skips the entire timer ioctl when retro_version is zero and
 * does not check the ioctl result. This board uses the same timer0 PWM. */
static bool apply_brightness(unsigned step)
{
    if(step>3 || VAR(0x19ba20,int)==1) return false;
    if(VAR(0x1b9ca4,int) && TIMER_HANDLE<0) FN(0x14c60,void,void)();
    if(TIMER_HANDLE<0) TIMER_HANDLE=FN(0x11da0,int,const char *,int)("/dev/timer0",2);
    if(TIMER_HANDLE<0) return false;
    unsigned duty=((const unsigned *)0x199578)[step];
    if(!duty || duty>100) return false;
    unsigned request[]={1,10000,0,3,duty,0};
    if(FN(0x11d40,int,int,unsigned,const void *)(TIMER_HANDLE,0x40185400,request)) return false;
    VAR(0x199588,unsigned)=duty;
    return true;
}

ENTRY void launcher_apply_saved_brightness(int step)
{
    if(step>=0 && step<=3) apply_brightness((unsigned)step);
}

static void *read_stock_config(void)
{
    char path[384];
    if(!suffix(path,sizeof(path),WORK(),"/setting.xml")) return NULL;
    FILE *f=FOPEN(path,"rb");
    if(!f) return NULL;
    void *tree=FN(0xb00a0,void *,void *,FILE *,void *)(NULL,f,NULL);
    FCLOSE(f);
    return tree;
}

static bool save_stock_level(const char *name, unsigned value)
{
    char path[384],tmp[400];
    if(!suffix(path,sizeof(path),WORK(),"/setting.xml") ||
       !suffix(tmp,sizeof(tmp),path,".tmp")) return false;
    int (*replace)(const char *,const char *)=SYM(NULL,"rename");
    if(!replace) return false;
    void *tree=read_stock_config();
    if(!tree) return false;
    void *config=FN(0xb13f0,void *,void *,void *,const char *,const char *,const char *,int)(
        tree,tree,"config",NULL,NULL,1);
    char digits[]={(char)('0'+value),0};
    bool ok=false;
    if(config) {
        FN(0xacde0,void,void *,const char *,const char *)(config,name,digits);
        FILE *f=FOPEN(tmp,"wb");
        if(f) {
            ok=!FN(0xb01bc,int,void *,FILE *,void *)(tree,f,NULL) &&
                !FN(0x11fb0,int,FILE *)(f) && !FN(0x11b18,int,int)(FN(0x11df4,int,FILE *)(f));
            if(FCLOSE(f)) ok=false;
            if(ok) ok=!replace(tmp,path);
        }
    }
    FN(0xb103c,void,void *)(tree);
    return ok;
}

static int settings_label(uint16_t *frame,unsigned x,unsigned y,unsigned size,uint16_t ink,
                          const char *label)
{
    return FN(0x85c94,int,void *,int,int,int,unsigned,const char *)(
        frame,(int)x,(int)y,(int)size,ink,label);
}

static uint16_t settings_accent(void) { return S.classic?0x8f5e:0xfe49; }

static void screen_header(uint16_t *frame,const char *title)
{
    /* The stock font uses a shared clip rectangle left by the last screen. */
    unsigned *clip=(unsigned *)0x19bac4;
    clip[0]=0; clip[1]=0; clip[2]=640; clip[3]=480;
    settings_box(frame,0,0,640,480,S.classic?0x09c9:0x08a4);
    settings_box(frame,0,0,640,66,S.classic?0x12ab:0x10e6);
    settings_label(frame,26,12,32,0xffff,title);
    settings_box(frame,26,61,116,64,settings_accent());
    settings_box(frame,0,432,640,480,S.classic?0x12ab:0x10e6);
}

static void screen_row(uint16_t *frame,unsigned index,bool selected,const char *name,
                       const char *value)
{
    unsigned y=81+68*index;
    uint16_t accent=settings_accent(), line=selected?accent:0x328b;
    settings_box(frame,24,y,601,y+58,line);
    settings_box(frame,26,y+2,599,y+56,
                 selected?(S.classic?0x1a49:0x29ab):(S.classic?0x0a6a:0x1127));
    settings_label(frame,43,y+11,26,0xffff,name);
    if(value) settings_label(frame,397,y+13,23,selected?accent:0xbdf7,value);
}

static void screen_scroll(uint16_t *frame,unsigned top,unsigned count)
{
    if(count<=VISIBLE_ROWS) return;
    unsigned size=320*VISIBLE_ROWS/count, y=81+320*top/count;
    settings_box(frame,611,81,615,401,0x328b);
    settings_box(frame,611,y,615,y+size,settings_accent());
}

static const char *music_value(void)
{
    if(MUSIC.unavailable) return "Track unavailable";
    return MUSIC.mode==MUSIC_OFF?"Off":MUSIC.mode==MUSIC_MP3?"Custom MP3":"Start Line";
}

static void draw_settings(void)
{
    uint16_t *frame=SETTINGS.frame;
    shutdown_wait()();
    screen_header(frame,"Settings");
    const char *const names[]={"Brightness","Volume","Menu music","Theme","Battery display",
        "Frame skip","Language","Power off","Restore factory settings"};
    for(unsigned i=0;i<VISIBLE_ROWS && SETTINGS.top+i<ROW_COUNT;++i) {
        unsigned row=SETTINGS.top+i;
        const char *value=NULL;
        char level[12];
        if(row==ROW_BRIGHTNESS || row==ROW_VOLUME) {
            unsigned n=row==ROW_BRIGHTNESS?bounded_level(LED_STEP,3)+1:bounded_level(VOLUME_STEP,9);
            if(row==ROW_BRIGHTNESS) {
                level[0]='0'+n; level[1]='/'; level[2]='4'; level[3]=0;
            } else {
                level[0]='0'+n; level[1]='/'; level[2]='9'; level[3]=0;
            }
            value=level;
        } else if(row==ROW_MUSIC) value=music_value();
        else if(row==ROW_THEME) value=S.classic?"Classic":"New";
        else if(row==ROW_BATTERY) value=S.battery_percent?"Est. %":"Bars";
        else if(row==ROW_FRAME_SKIP) value=S.auto_skip?"Auto":"Off";
        else if(row==ROW_LANGUAGE) value="English";
        screen_row(frame,i,row==SETTINGS.row,names[row],value);
        if(row==ROW_BRIGHTNESS || row==ROW_VOLUME) {
            unsigned y=81+68*i+43, n=row==ROW_BRIGHTNESS?bounded_level(LED_STEP,3)+1:bounded_level(VOLUME_STEP,9);
            unsigned max=row==ROW_BRIGHTNESS?4:9;
            settings_box(frame,397,y,577,y+4,0x328b);
            if(n) settings_box(frame,397,y,397+180*n/max,y+4,settings_accent());
        }
    }
    screen_scroll(frame,SETTINGS.top,ROW_COUNT);
    const char *hint=(SETTINGS.row==ROW_BRIGHTNESS || SETTINGS.row==ROW_VOLUME)?
        "Left / Right  Adjust     B  Back":"A  Select    B  Back    Start  Power off";
    settings_label(frame,26,435,22,SETTINGS.message?settings_accent():0xd69a,
                   SETTINGS.message?SETTINGS.message:hint);
    DISP(frame,640,480,1280);
}

static unsigned settings_key_poll(unsigned *held)
{
    unsigned key=launcher_menu_key();
    *held&=HOME_PAD;
    return key&*held?0:key;
}

static void settings_idle(void)
{
    if(HOME_BATTERY<0) FN(0x836b4,void,void)();
    FN(0x11f08,int,unsigned)(16000);
}

static void scan_music_files(void)
{
    char path[384];
    if(!suffix(path,sizeof(path),WORK(),MUSIC_DIR)) return;
    DIR *dir=FN(0x11ca4,DIR *,const char *)(path);
    if(!dir) return;
    SETTINGS.tracks=ALLOC(MUSIC_FILES_MAX*sizeof(*SETTINGS.tracks));
    struct dirent *entry;
    while(SETTINGS.tracks && SETTINGS.track_count<MUSIC_FILES_MAX &&
          (entry=FN(0x11b78,struct dirent *,DIR *)(dir))) {
        if((entry->d_type!=DT_REG && entry->d_type!=DT_UNKNOWN) || !music_filename(entry->d_name)) continue;
        unsigned n=0;
        while(entry->d_name[n]) ++n;
        COPY(SETTINGS.tracks[SETTINGS.track_count++],entry->d_name,n+1);
    }
    FN(0x11bcc,int,DIR *)(dir);
    for(unsigned i=1;i<SETTINGS.track_count;++i) {
        unsigned j=i;
        char name[MUSIC_NAME_MAX+1];
        COPY(name,SETTINGS.tracks[i],sizeof(name));
        while(j && STRCMP(SETTINGS.tracks[j-1],name)>0) {
            COPY(SETTINGS.tracks[j],SETTINGS.tracks[j-1],sizeof(name));
            --j;
        }
        COPY(SETTINGS.tracks[j],name,sizeof(name));
    }
}

static void filename_label(char label[39],const char *name)
{
    unsigned i=0;
    unsigned at=0;
    while(i<22 && name[at]) {
        unsigned char c=name[at++];
        label[i++]=c<128?(char)c:'?';
        while(((unsigned char)name[at]&0xc0)==0x80) ++at;
    }
    if(name[at]) { label[i++]='.'; label[i++]='.'; label[i++]='.'; }
    label[i]=0;
}

static void music_picker(void)
{
    scan_music_files();
    unsigned row=MUSIC.mode==MUSIC_OFF?1:0, top=0;
    for(unsigned i=0;i<SETTINGS.track_count;++i)
        if(MUSIC.mode==MUSIC_MP3 && !STRCMP(SETTINGS.tracks[i],MUSIC.name)) { row=i+2; break; }
    unsigned total=SETTINGS.track_count+2, held=HOME_PAD|0x2000;
    const char *error=NULL;
    for(;;) {
        if(row>=top+VISIBLE_ROWS) top=row+1-VISIBLE_ROWS;
        if(row<top) top=row;
        shutdown_wait()();
        screen_header(SETTINGS.frame,"Menu music");
        for(unsigned i=top;i<total && i<top+VISIBLE_ROWS;++i) {
            char label[39];
            if(i>=2) filename_label(label,SETTINGS.tracks[i-2]);
            screen_row(SETTINGS.frame,i-top,i==row,i==0?"Start Line (built-in)":i==1?"Off":label,NULL);
        }
        screen_scroll(SETTINGS.frame,top,total);
        settings_label(SETTINGS.frame,26,435,21,0xd69a,error?error:
            SETTINGS.track_count?"A  Play and select    B  Back":"Add MP3 files to retro/d35-launcher1/music");
        DISP(SETTINGS.frame,640,480,1280);
        unsigned key;
        do { settings_idle(); key=settings_key_poll(&held); } while(!key);
        error=NULL;
        if(key==0x4000) break;
        if(key==0x10 && row) { --row; vesper_transition(1); }
        if(key==0x40 && row+1<total) { ++row; vesper_transition(1); }
        if(key==0x2000) {
            held|=0x2000;
            if(choose_music(row==0?MUSIC_BUILTIN:row==1?MUSIC_OFF:MUSIC_MP3,
                            row>=2?SETTINGS.tracks[row-2]:NULL)) break;
            error="Could not open or save this track";
        }
    }
    if(SETTINGS.tracks) FREE(SETTINGS.tracks);
    SETTINGS.tracks=NULL;
    SETTINGS.track_count=0;
}

static void adjust_level(unsigned row,int direction)
{
    bool brightness=row==ROW_BRIGHTNESS;
    int max=brightness?3:9;
    int current=(int)bounded_level(brightness?LED_STEP:VOLUME_STEP,(unsigned)max);
    int next=current+direction;
    if(next<0 || next>max) return;
    if(brightness && !apply_brightness((unsigned)next)) {
        SETTINGS.message="Backlight control unavailable";
        return;
    }
    if(!save_stock_level(brightness?"brightness":"volume",(unsigned)next)) {
        if(brightness) apply_brightness((unsigned)current);
        SETTINGS.message="Could not save settings";
        return;
    }
    if(brightness) LED_STEP=next;
    else {
        VOLUME_STEP=next;
        STOCK_VOLUME=next;
        FN(0x1258c,void,int)(next);
    }
}

static bool launcher_factory_active(void)
{ return SETTINGS.factory || SETTINGS.language; }

/* The stock reset routine clears its own game lists and resets volume and
 * brightness. Navigate to that one action without showing the old menu. */
static unsigned launcher_factory_navigation(unsigned row,unsigned key)
{
    if(SETTINGS.language) {
        if(SETTINGS.language_opened) return 0x4000;
        SETTINGS.language_opened=true;
        return 0x2000;
    }
    if(SETTINGS.reset_confirmed) return 0x4000;
    if(SETTINGS.factory_steps++>8 || key==0x4000) return 0x4000;
    return row<3?0x40:0x2000;
}

ENTRY unsigned launcher_language_key(void)
{
    if(!SETTINGS.language) return launcher_menu_key();
    return settings_key_poll(&SETTINGS.language_held);
}

ENTRY unsigned launcher_reset_key(void)
{
    if(!SETTINGS.factory) return launcher_menu_key();
    SETTINGS.reset_confirmed=true;
    return 0x2000;
}

ENTRY void launcher_reset_frame(const void *frame,unsigned width,unsigned height,size_t pitch)
{
    if(!SETTINGS.factory) DISP(frame,width,height,pitch);
}

static bool confirm_factory(void)
{
    shutdown_wait()();
    screen_header(SETTINGS.frame,"Restore factory settings");
    settings_label(SETTINGS.frame,28,131,25,0xffff,"Reset settings and clear your");
    settings_label(SETTINGS.frame,28,164,25,0xffff,"favorites and recent games?");
    settings_label(SETTINGS.frame,28,435,22,0xd69a,"A  Restore    B  Cancel");
    DISP(SETTINGS.frame,640,480,1280);
    unsigned held=HOME_PAD|0x2000;
    for(;;) {
        settings_idle();
        unsigned key=settings_key_poll(&held);
        if(key==0x4000) return false;
        if(key==0x2000) return true;
    }
}

static bool launcher_settings(void)
{
    if(LOCALE!=1 || UI_WIDTH!=640 || UI_HEIGHT!=480 || !UI_FRAME || !shutdown_wait()) return false;
    /* Stock Settings waits for the preview worker to release the canvas. */
    while(UI_WORKERS&8u) FN(0x11f08,int,unsigned)(1000);
    UI_WORKERS=1;
    shutdown_wait()();
    SETTINGS.frame=UI_FRAME;
    S.settings_pixels=UI_FRAME;
    SETTINGS.row=SETTINGS.top=0;
    SETTINGS.message=NULL;
    read_music_setting();
    unsigned held=HOME_PAD, locale=LOCALE;
    launcher_menu_key();
    draw_settings();
    for(;;) {
        settings_idle();
        unsigned key=settings_key_poll(&held);
        if(S.power_frame) {
            if(key==0x4000) shutdown_cancel();
            else if(key==0x2000) { held|=0x2000; shutdown_confirm(); }
            continue;
        }
        if(!key) continue;
        if(key!=0x10 && key!=0x40 && key!=0x80 && key!=0x20 &&
           key!=0x2000 && key!=0x4000 && key!=8) continue;
        SETTINGS.message=NULL;
        if(key==0x4000) break;
        if(key==0x10 && SETTINGS.row) { --SETTINGS.row; vesper_transition(1); }
        else if(key==0x40 && SETTINGS.row+1<ROW_COUNT) { ++SETTINGS.row; vesper_transition(1); }
        else if(key==0x80 || key==0x20) {
            if(SETTINGS.row<=ROW_VOLUME) adjust_level(SETTINGS.row,key==0x20?1:-1);
        } else if(key==0x2000 || key==8) {
            held|=key;
            unsigned row=SETTINGS.row;
            if(key==8 || row==ROW_POWER) {
                if(shutdown_available()) { shutdown_open(); held|=0x2000; continue; }
                SETTINGS.message="Power off is unavailable";
            } else if(row==ROW_THEME || row==ROW_FRAME_SKIP || row==ROW_BATTERY) {
                change_option(row==ROW_THEME?2:row==ROW_FRAME_SKIP?1:3);
                if(S.save_failed) SETTINGS.message="Could not save settings";
            } else if(row==ROW_MUSIC) {
                music_picker();
                held=HOME_PAD;
            } else if(row==ROW_LANGUAGE) {
                SETTINGS.language=true;
                SETTINGS.language_opened=false;
                SETTINGS.language_held=HOME_PAD|0x2000;
                FN(0x8dfe4,void,void)();
                SETTINGS.language=false;
                S.settings_pixels=SETTINGS.frame;
                held=HOME_PAD;
            } else if(row==ROW_RESET && confirm_factory()) {
                SETTINGS.reset_confirmed=false;
                SETTINGS.factory_steps=0;
                SETTINGS.factory=true;
                FN(0x8dfe4,void,void)();
                SETTINGS.factory=false;
                if(SETTINGS.reset_confirmed) {
                    if(save_options(false,false,false))
                        S.auto_skip=S.classic=S.battery_percent=false;
                    choose_music(MUSIC_BUILTIN,NULL);
                    launcher_apply_saved_brightness(LED_STEP);
                }
                held=HOME_PAD;
            }
        }
        if(LOCALE!=locale) break;
        if(SETTINGS.row<SETTINGS.top) SETTINGS.top=SETTINGS.row;
        else if(SETTINGS.row>=SETTINGS.top+VISIBLE_ROWS) SETTINGS.top=SETTINGS.row+1-VISIBLE_ROWS;
        draw_settings();
    }
    shutdown_wait()();
    return true;
}

ENTRY int search_caret(uint16_t *frame,int x,int y,int height,unsigned color,const char *text)
{
    if(UI_WIDTH!=640 || UI_HEIGHT!=480 || x<2 || x>=640 || y<0 || y>=460 || !frame)
        return FN(0x85c94,int,void *,int,int,int,unsigned,const char *)(frame,x,y,height,color,text);
    /* The blink loop saves and restores six pixels starting at x - 2. */
    unsigned top=(unsigned)y+6, bottom=(unsigned)y+26;
    if(bottom>480) bottom=480;
    settings_box(frame,(unsigned)x,top,(unsigned)x+1,bottom,(uint16_t)color);
    return x+1;
}
