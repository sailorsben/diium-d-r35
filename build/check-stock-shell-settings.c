/* Execute the redesigned Settings entry and real MP3 mixer in the ARM ELF. */
#define D35_STOCK_MENU_ENTRY menu_fixture_main
#include "check-stock-shell-menu.c"
#include <dirent.h>
#include <pthread.h>
#include <ctype.h>
#include <setjmp.h>

enum { DOWN=0x40, UP=0x10, LEFT=0x80, RIGHT=0x20, A=0x2000, B=0x4000 };
static const unsigned *keys;
static size_t key_count, key_index;
static unsigned backlight_calls, duty, mixer_blocks, nonzero_blocks, frames;
static bool timer_fail, brightness, reset_seen, picker_seen, scroll_seen, factory_seen;
static bool brightness_error, corrupt_seen;
static char snapshot[1024];
static bool real_font;

static int test_text(uint16_t *frame,int x,int y,int height,unsigned color,const char *text)
{
    assert(frame==settings && x>=0 && x<640 && y>=0 && y+29<480);
    if(!strcmp(text,"Brightness")) { brightness=true; assert(height==26); }
    if(!strcmp(text,"Restore factory settings")) { reset_seen=true; scroll_seen=frames>5; }
    if(!strcmp(text,"A  Restore    B  Cancel")) factory_seen=true;
    if(!strcmp(text,"Off") && picker_seen) assert(height>=23);
    if(!strcmp(text,"Tiny track.MP3")) picker_seen=true;
    if(!strcmp(text,"Backlight control unavailable")) brightness_error=true;
    if(!strcmp(text,"Could not open or save this track")) corrupt_seen=true;
    if(!strcmp(text,"Tiny track.MP3") && snapshot[0]==0) {
        assert(snprintf(snapshot,sizeof(snapshot),"%s/picker.rgb565",work)<(int)sizeof(snapshot));
    }
    if(real_font)
        return ((int (*)(uint16_t *,int,int,int,unsigned,const char *))0x85c94)(
            frame,x,y,height,color,text);
    frame[(y+29)*640+x]=(uint16_t)color;
    return x+10;
}

static void test_frame(const void *pixels,unsigned w,unsigned h,size_t pitch)
{
    assert(w==640 && h==480 && pitch==1280 && pixels==settings);
    if(frames==0) {
        char initial[1024];
        assert(snprintf(initial,sizeof(initial),"%s/settings-first.rgb565",work)<(int)sizeof(initial));
        FILE *f=fopen(initial,"wb");
        assert(f && fwrite(settings,sizeof(settings),1,f)==1 && !fclose(f));
    }
    if(snapshot[0]) {
        FILE *f=fopen(snapshot,"wb");
        assert(f && fwrite(settings,sizeof(settings),1,f)==1 && !fclose(f));
        snapshot[0]=0;
    }
    ++frames;
}

static unsigned test_joy(void)
{
    assert(key_index<key_count);
    unsigned key=keys[key_index++];
    *(unsigned *)0x1b9b50=key;
    return key;
}

static int timer_open(const char *name,int mode)
{
    assert(!strcmp(name,"/dev/timer0") && mode==2);
    return 318;
}

static int pwm(int fd,unsigned request,const unsigned *args)
{
    assert(fd==318 && request==0x40185400 && args[0]==1 && args[1]==10000);
    assert(args[2]==0 && args[3]==3 && args[5]==0);
    ++backlight_calls;
    duty=args[4];
    return timer_fail?-1:0;
}

static void capture_audio(const int16_t *data,unsigned count)
{
    assert(count==735);
    ++mixer_blocks;
    for(unsigned i=0;i<count*2;++i)
        if(data[i]) { ++nonzero_blocks; break; }
}

static void drive(const unsigned *sequence,size_t count)
{
    keys=sequence; key_count=count; key_index=0;
    *(unsigned *)0x1b9b50=0;
    ((void (*)(void))target(0x984dc))();
    assert(key_index==count);
}

static void file_contents(const char *relative,const char *contains)
{
    char path[1024];
    assert(snprintf(path,sizeof(path),"%s/%s",work,relative)<(int)sizeof(path));
    size_t n;
    unsigned char *data=read_data(path,&n);
    char *line=malloc(n+1);
    assert(line);
    memcpy(line,data,n); line[n]=0;
    assert(strstr(line,contains));
    free(line); free(data);
}

static void route(void)
{
    const unsigned first[]={0,LEFT,B};
    drive(first,sizeof(first)/sizeof(*first));
    assert(brightness && duty==50 && backlight_calls==1 && *(int *)0x199ee0==1);
    file_contents("setting.xml","brightness=\"1\"");
    file_contents("setting.xml","language=\"1\"");
    timer_fail=true;
    const unsigned fail[]={0,RIGHT,B};
    drive(fail,sizeof(fail)/sizeof(*fail));
    assert(brightness_error && *(int *)0x199ee0==1);
    file_contents("setting.xml","brightness=\"1\"");
    timer_fail=false;
    ((void (*)(int))target(0x81ee4))(0);
    assert(duty==30);
    ((void (*)(int))target(0x81ee4))(99);
    assert(duty==30);
    puts("PASS brightness updates timer0 with checked duty and saves only successful settings");
    const unsigned scroll[]={0,DOWN,DOWN,DOWN,DOWN,DOWN,DOWN,DOWN,DOWN,A,0,B,B};
    drive(scroll,sizeof(scroll)/sizeof(*scroll));
    assert(scroll_seen && reset_seen && factory_seen);
    puts("PASS five full-size rows scroll to factory reset and B cancels");
    /* The false .mp3 sorts first. A real file must work after the rejected choice. */
    const unsigned select[]={0,DOWN,DOWN,A,0,DOWN,DOWN,A,0,DOWN,A,0,B};
    drive(select,sizeof(select)/sizeof(*select));
    assert(picker_seen && corrupt_seen);
    file_contents("d35-launcher1/d35-music.cfg","MTiny track.MP3");
    void (*mix)(void)=(void *)target(0x8918c);
    for(unsigned i=0;i<1100;++i) mix();
    assert(mixer_blocks==1100 && nonzero_blocks>1000);
    ((void (*)(unsigned))target(0x87754))(0);
    nonzero_blocks=0;
    mix();
    assert(nonzero_blocks==0);
    ((void (*)(unsigned,const struct sound *))target(0x87b80))(0,NULL);
    for(unsigned i=0;i<12;++i) mix();
    assert(nonzero_blocks>0);
    const unsigned mute[]={0,DOWN,DOWN,A,0,UP,UP,A,0,B};
    drive(mute,sizeof(mute)/sizeof(*mute));
    file_contents("d35-launcher1/d35-music.cfg","O");
    nonzero_blocks=0;
    for(unsigned i=0;i<16;++i) mix(); /* Let the navigation cue finish on channel 1. */
    nonzero_blocks=0;
    mix();
    assert(nonzero_blocks==0);
    const unsigned builtin[]={0,DOWN,DOWN,A,0,UP,A,0,B};
    drive(builtin,sizeof(builtin)/sizeof(*builtin));
    for(unsigned i=0;i<12;++i) mix();
    assert(nonzero_blocks>0);
    puts("PASS custom MP3 picker, invalid file, loop, game close/resume, Off and bundled playback");
}

int main(int argc,char **argv)
{
    assert(argc==3 || argc==4);
    real_font=argc==4 && !strcmp(argv[3],"font");
    work=argv[2];
    map_vendor(argv[1]);
    patch(0x11ce0,(uintptr_t)fopen); patch(0x11f20,(uintptr_t)fclose);
    patch(0x11b84,(uintptr_t)fseek); patch(0x11e84,(uintptr_t)ftell);
    patch(0x11ddc,(uintptr_t)fread); patch(0x11eb4,(uintptr_t)fwrite);
    patch(0x11fb0,(uintptr_t)fflush); patch(0x11df4,(uintptr_t)fileno);
    patch(0x11b18,(uintptr_t)fsync); patch(0x11ed8,(uintptr_t)malloc);
    patch(0x11b6c,(uintptr_t)free); patch(0x11c8c,(uintptr_t)memset);
    patch(0x11ecc,(uintptr_t)memcpy); patch(0x11d28,(uintptr_t)memmove);
    patch(0x11f74,(uintptr_t)strcmp); patch(0x11fc8,(uintptr_t)memcmp);
    patch(0x11e78,(uintptr_t)calloc); patch(0x11ee4,(uintptr_t)strlen);
    patch(0x11d64,(uintptr_t)strcpy); patch(0x11be4,(uintptr_t)quiet);
    patch(0x11c20,(uintptr_t)puts); patch(0x11f08,(uintptr_t)usleep);
    patch(0x11ca4,(uintptr_t)opendir); patch(0x11b78,(uintptr_t)readdir);
    patch(0x11bcc,(uintptr_t)closedir);
    patch(0x11d58,(uintptr_t)realloc);
    patch(0x11e18,(uintptr_t)putc); patch(0x11e30,(uintptr_t)getc);
    patch(0x11d10,(uintptr_t)pthread_once);
    patch(0x11de8,(uintptr_t)pthread_getspecific);
    patch(0x11ef0,(uintptr_t)pthread_setspecific);
    patch(0x11e54,(uintptr_t)pthread_key_create);
    patch(0x11e6c,(uintptr_t)__ctype_b_loc);
    patch(0x12064,(uintptr_t)strdup);
    patch(0x12040,(uintptr_t)strchr);
    patch(0x11ba8,(uintptr_t)strncmp);
    patch(0x11e3c,(uintptr_t)strstr);
    patch(0x11f38,(uintptr_t)sprintf);
    patch(0x11b48,(uintptr_t)fixed_time);
    patch(0x11fbc,(uintptr_t)_setjmp);
    patch(0x11ec0,(uintptr_t)longjmp);
    patch(0x80bec,(uintptr_t)path); patch(0x12010,(uintptr_t)find);
    patch(0x157c8,(uintptr_t)gpio); patch(0x86368,(uintptr_t)test_joy);
    if(!real_font) patch(0x85c94,(uintptr_t)test_text);
    patch(0xa6658,(uintptr_t)test_frame);
    patch(0x11da0,(uintptr_t)timer_open); patch(0x11d40,(uintptr_t)pwm);
    patch(0xa695c,(uintptr_t)capture_audio);
    *(void **)0x1b81a8=&driver;
    *(void **)0x199910=settings;
    *(unsigned *)0x199914=640;
    *(unsigned *)0x199918=480;
    *(int *)0x199ee0=2;
    *(int *)0x19958c=-1;
    *(unsigned *)0x1998d8=1;
    if(real_font) {
        ((void (*)(void))0x85a88)();
        assert(*(void **)0x1b9d14);
        const unsigned paint[]={0,B};
        drive(paint,sizeof(paint)/sizeof(*paint));
        puts("PASS actual vendor font paints the full-size Settings view");
        return 0;
    }
    route();
    int (*caret)(uint16_t *,int,int,int,unsigned,const char *)=(void *)target(0x99b2c);
    memset(settings,0,sizeof(settings));
    assert(caret(settings,240,76,20,0xffff,"]")==241);
    for(unsigned i=0;i<640*480;++i)
        assert(settings[i]==((i%640==240 && i/640>=82 && i/640<102)?0xffff:0));
    puts("PASS search caret draws within the six-pixel blink strip");
    return 0;
}
