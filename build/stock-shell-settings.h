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

enum { ROW_BRIGHTNESS, ROW_THEME, ROW_BATTERY, ROW_VOLUME, ROW_MUSIC,
       ROW_FRAME_SKIP, ROW_LANGUAGE, ROW_POWER, ROW_RESET, ROW_COUNT,
       VISIBLE_ROWS=5, MUSIC_FILES_MAX=64, SETTINGS_TOP=70,
       SETTINGS_BOTTOM=420, ROW_HEIGHT=52, GROUP_HEIGHT=28 };

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

#include "stock-shell-settings-icons.h"

static const uint8_t settings_row_icon[ROW_COUNT]={
    [ROW_BRIGHTNESS]=SETTINGS_MASK_BRIGHTNESS, [ROW_THEME]=SETTINGS_MASK_THEME,
    [ROW_BATTERY]=SETTINGS_MASK_BATTERY, [ROW_VOLUME]=SETTINGS_MASK_VOLUME,
    [ROW_MUSIC]=SETTINGS_MASK_MUSIC, [ROW_FRAME_SKIP]=SETTINGS_MASK_FRAME_SKIP,
    [ROW_LANGUAGE]=SETTINGS_MASK_LANGUAGE, [ROW_POWER]=SETTINGS_MASK_POWER,
    [ROW_RESET]=SETTINGS_MASK_RESET,
};

static void settings_blend_pixel(uint16_t *pixel,uint16_t ink,unsigned alpha)
{
    if(!alpha) return;
    if(alpha==3) { *pixel=ink; return; }
    unsigned bg=*pixel, weight=3-alpha;
    unsigned r=((ink>>11)*alpha+(bg>>11)*weight+1)/3;
    unsigned g=(((ink>>5)&63)*alpha+((bg>>5)&63)*weight+1)/3;
    unsigned b=((ink&31)*alpha+(bg&31)*weight+1)/3;
    *pixel=(uint16_t)((r<<11)|(g<<5)|b);
}

static void settings_mask(uint16_t *frame,unsigned x,unsigned y,
                          const uint8_t mask[][SETTINGS_ICON_SIZE/4],bool mirrored,uint16_t color)
{
    for(unsigned j=0;j<SETTINGS_ICON_SIZE;++j) {
        uint16_t *pixel=frame+(y+j)*640+x;
        unsigned row=mirrored && j>=SETTINGS_ICON_SIZE/2?SETTINGS_ICON_SIZE-1-j:j;
        for(unsigned i=0;i<SETTINGS_ICON_SIZE/4;++i) {
            unsigned coverage=mask[row][i];
            if(coverage)
                for(unsigned k=0;k<4;++k)
                    settings_blend_pixel(pixel+4*i+k,color,(coverage>>(6-2*k))&3);
        }
    }
}

static void settings_icon(uint16_t *frame,unsigned x,unsigned y,unsigned icon,bool selected)
{
    uint16_t rim, fill, ink;
    if(S.classic) {
        rim=selected?0x5557:0x3b8f;
        fill=selected?0x1a4a:0x11c8;
        ink=selected?0x9f3e:0xb6fc;
    } else {
        rim=selected?0x9326:0x322c;
        fill=selected?0x4189:0x1148;
        ink=selected?0xfe8c:0xb67c;
    }
    settings_mask(frame,x,y,settings_tiles[0],true,rim);
    settings_mask(frame,x,y,settings_tiles[1],true,fill);
    settings_mask(frame,x,y,settings_masks[icon],false,ink);
}

static void screen_header(uint16_t *frame,const char *title)
{
    /* The stock font uses a shared clip rectangle left by the last screen. */
    unsigned *clip=(unsigned *)0x19bac4;
    clip[0]=0; clip[1]=0; clip[2]=640; clip[3]=480;
    settings_box(frame,0,0,640,480,S.classic?0x09c9:0x08a4);
    uint16_t chrome=S.classic?0x12ab:0x10e6;
    settings_box(frame,0,0,640,56,chrome);
    settings_box(frame,0,55,640,56,0x328b);
    settings_label(frame,24,8,32,0xffff,title);
    home_battery(frame,HOME_BATTERY);
    settings_box(frame,0,430,640,480,chrome);
    settings_box(frame,0,430,640,431,0x328b);
}

static void settings_group(uint16_t *frame,unsigned y,const char *label)
{
    settings_label(frame,24,y-7,19,S.classic?0x96b8:0x8db7,label);
    settings_box(frame,24,y+23,598,y+24,0x328b);
}

static void screen_row(uint16_t *frame,unsigned y,bool selected,unsigned icon,const char *name)
{
    if(selected) {
        settings_box(frame,24,y,598,y+ROW_HEIGHT-1,S.classic?0x1a49:0x21ab);
        settings_box(frame,24,y+1,28,y+ROW_HEIGHT-2,settings_accent());
    }
    settings_box(frame,88,y+ROW_HEIGHT-1,598,y+ROW_HEIGHT,0x222a);
    settings_icon(frame,36,y+(ROW_HEIGHT-SETTINGS_ICON_SIZE)/2,icon,selected);
    settings_label(frame,88,y+5,26,0xffff,name);
}

static void settings_chevron(uint16_t *frame,unsigned x,unsigned y,bool right,uint16_t tint)
{
    for(unsigned i=0;i<7;++i) {
        unsigned dx=right?i:6-i;
        settings_box(frame,x+dx,y+i,x+dx+2,y+i+2,tint);
        settings_box(frame,x+dx,y+12-i,x+dx+2,y+14-i,tint);
    }
}

static void settings_key(uint16_t *frame,unsigned x,unsigned w,const char *key)
{
    settings_box(frame,x,442,x+w,468,0x4b71);
    settings_box(frame,x+1,443,x+w-1,467,0x1127);
    settings_label(frame,x+7,430,18,settings_accent(),key);
}

static void settings_arrows_key(uint16_t *frame)
{
    settings_box(frame,185,442,241,468,0x4b71);
    settings_box(frame,186,443,240,467,0x1127);
    settings_chevron(frame,196,448,false,settings_accent());
    settings_chevron(frame,222,448,true,settings_accent());
}

static void settings_footer(uint16_t *frame,const char *action,bool adjust,const char *message)
{
    settings_key(frame,541,25,"B");
    settings_label(frame,574,430,22,0xffff,"Back");
    if(message) {
        settings_label(frame,24,430,20,settings_accent(),message);
        return;
    }
    settings_key(frame,24,56,"D-pad");
    settings_label(frame,89,430,22,0xffff,"Move");
    if(adjust) {
        settings_arrows_key(frame);
        settings_label(frame,250,430,22,0xffff,action);
    } else if(action) {
        settings_key(frame,185,25,"A");
        settings_label(frame,219,430,22,0xffff,action);
    }
}

static void screen_scroll(uint16_t *frame,unsigned top,unsigned count)
{
    if(count<=VISIBLE_ROWS) return;
    unsigned height=SETTINGS_BOTTOM-SETTINGS_TOP, size=height*VISIBLE_ROWS/count;
    unsigned y=SETTINGS_TOP+(height-size)*top/(count-VISIBLE_ROWS);
    settings_box(frame,614,SETTINGS_TOP,617,SETTINGS_BOTTOM,0x328b);
    settings_box(frame,613,y,618,y+size,settings_accent());
}

static void settings_filename(uint16_t *frame,unsigned x,unsigned y,unsigned size,unsigned width,
                              uint16_t color,const char *name);

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
    const char *const names[]={"Brightness","Theme","Battery display","Volume","Menu music",
        "Frame skip","Language","Power off","Restore factory settings"};
    unsigned y=SETTINGS_TOP;
    for(unsigned i=0;i<VISIBLE_ROWS && SETTINGS.top+i<ROW_COUNT;++i) {
        unsigned row=SETTINGS.top+i;
        bool selected=row==SETTINGS.row;
        if(i==0 || row==ROW_VOLUME || row==ROW_FRAME_SKIP) {
            settings_group(frame,y,row<ROW_VOLUME?"DISPLAY":row<ROW_FRAME_SKIP?"SOUND":"SYSTEM");
            y+=GROUP_HEIGHT;
        }
        screen_row(frame,y,selected,settings_row_icon[row],names[row]);
        uint16_t ink=selected?settings_accent():0xbdf7;
        const char *value=NULL;
        if(row==ROW_BRIGHTNESS || row==ROW_VOLUME) {
            unsigned n=row==ROW_BRIGHTNESS?bounded_level(LED_STEP,3)+1:bounded_level(VOLUME_STEP,9);
            unsigned max=row==ROW_BRIGHTNESS?4:9;
            char level[]={'0'+n,'/','0'+max,0};
            settings_label(frame,531,y+6,22,ink,level);
            for(unsigned j=0;j<max;++j) {
                unsigned x=405+112*j/max, next=405+112*(j+1)/max;
                settings_box(frame,x,y+22,next-3,y+30,j<n?ink:0x3aaf);
            }
            if(selected) {
                settings_chevron(frame,383,y+19,false,ink);
                settings_chevron(frame,577,y+19,true,ink);
            }
        } else if(row==ROW_MUSIC) {
            if(MUSIC.mode==MUSIC_MP3 && !MUSIC.unavailable) {
                settings_filename(frame,387,y+7,23,181,ink,MUSIC.name);
            } else value=music_value();
        }
        else if(row==ROW_THEME) value=S.classic?"Classic":"New";
        else if(row==ROW_BATTERY) value=S.battery_percent?"Est. %":"Bars";
        else if(row==ROW_FRAME_SKIP) value=S.auto_skip?"Auto":"Off";
        else if(row==ROW_LANGUAGE) value="English";
        if(value) {
            unsigned *clip=(unsigned *)0x19bac4;
            clip[2]=569;
            settings_label(frame,387,y+7,23,ink,value);
            clip[2]=640;
        }
        if(row!=ROW_BRIGHTNESS && row!=ROW_VOLUME)
            settings_chevron(frame,577,y+19,true,selected?ink:0x5bf2);
        y+=ROW_HEIGHT;
    }
    screen_scroll(frame,SETTINGS.top,ROW_COUNT);
    const char *const actions[]={"Adjust brightness","Switch theme","Switch display","Adjust volume",
        "Choose music","Switch mode","Choose language","Power off","Review reset"};
    settings_footer(frame,actions[SETTINGS.row],SETTINGS.row==ROW_BRIGHTNESS ||
                   SETTINGS.row==ROW_VOLUME,SETTINGS.message);
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

static void settings_filename(uint16_t *frame,unsigned x,unsigned y,unsigned size,unsigned width,
                              uint16_t color,const char *name)
{
    char label[47];
    unsigned i=0, at=0;
    while(i<sizeof(label)-4 && name[at]) {
        unsigned char c=name[at++];
        label[i++]=c<128?(char)c:'?';
        while(((unsigned char)name[at]&0xc0)==0x80) ++at;
    }
    label[i]=0;
    /* The stock font reports the right edge. An empty vertical clip measures
     * without writing pixels; only file labels need measurement. */
    unsigned *clip=(unsigned *)0x19bac4;
    clip[1]=480;
    if(name[at] || settings_label(frame,0,y,size,color,label)>(int)width) {
        do {
            if(i) --i;
            label[i]='.'; label[i+1]='.'; label[i+2]='.'; label[i+3]=0;
        } while(i && settings_label(frame,0,y,size,color,label)>(int)width);
    }
    clip[1]=0;
    clip[2]=x+width;
    settings_label(frame,x,y,size,color,label);
    clip[2]=640;
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
        settings_group(SETTINGS.frame,SETTINGS_TOP,"CHOOSE A TRACK");
        for(unsigned i=top;i<total && i<top+VISIBLE_ROWS;++i) {
            unsigned y=SETTINGS_TOP+GROUP_HEIGHT+(i-top)*ROW_HEIGHT;
            screen_row(SETTINGS.frame,y,i==row,i==1?SETTINGS_MASK_MUTE:SETTINGS_MASK_MUSIC,
                       i==0?"Start Line":i==1?"Off":"");
            bool active=i==0?MUSIC.mode==MUSIC_BUILTIN:i==1?MUSIC.mode==MUSIC_OFF:
                MUSIC.mode==MUSIC_MP3 && !STRCMP(SETTINGS.tracks[i-2],MUSIC.name);
            if(active) settings_label(SETTINGS.frame,494,y+8,20,settings_accent(),"Selected");
            else if(i==0) settings_label(SETTINGS.frame,494,y+8,20,0xbdf7,"Built-in");
            if(i>=2) settings_filename(SETTINGS.frame,88,y+5,26,active?394:495,
                                       0xffff,SETTINGS.tracks[i-2]);
        }
        screen_scroll(SETTINGS.frame,top,total);
        if(!SETTINGS.track_count)
            settings_label(SETTINGS.frame,29,233,19,0xbdf7,"Add MP3s to retro/d35-launcher1/music");
        settings_footer(SETTINGS.frame,row==1?"Turn music off":"Play this track",false,error);
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
    settings_box(SETTINGS.frame,24,126,616,306,S.classic?0x1a49:0x21ab);
    settings_icon(SETTINGS.frame,41,148,SETTINGS_MASK_RESET,true);
    settings_label(SETTINGS.frame,92,142,27,0xffff,"Reset launcher preferences?");
    settings_label(SETTINGS.frame,92,193,22,0xd69a,"This also clears favorites and recent games.");
    settings_label(SETTINGS.frame,92,228,22,0xd69a,"A confirms. B returns to Settings.");
    settings_key(SETTINGS.frame,24,25,"A");
    settings_label(SETTINGS.frame,59,430,22,0xffff,"Restore");
    settings_key(SETTINGS.frame,510,25,"B");
    settings_label(SETTINGS.frame,544,430,22,0xffff,"Cancel");
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
            if(SETTINGS.row==ROW_BRIGHTNESS || SETTINGS.row==ROW_VOLUME)
                adjust_level(SETTINGS.row,key==0x20?1:-1);
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
