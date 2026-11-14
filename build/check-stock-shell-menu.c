/* Compare the actual stock ARM mixer in MP3 and direct PCM modes and execute
 * the owned settings hooks with file/GPIO/display boundaries controlled. */
#define main stock_audit_main
#include "check-stock-snes-loader.c"
#undef main
#include <inttypes.h>
#include <stdbool.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>

struct sound {
    void *data;
    unsigned type, bytes_minus_one, channels_minus_one, rate, loop;
    void *begin, *end;
    unsigned phase;
};
static const int16_t *expected;
static size_t total, output, calls;
static bool verify, select_held, accept_held, rename_fails;
static bool shutdown_fixture;
static unsigned shutdown_display, shutdown_calls;
static int shutdown_result;
static uint16_t *shutdown_pixels;
static unsigned active_key, flips, driver;
static uint16_t settings[640*480];
static const char *work;
static unsigned locale=1;

static uintptr_t target(uintptr_t at)
{ return at+8+((int32_t)(*(uint32_t *)at<<8)>>6); }
static const char *path(void) { return work; }
static void wait_display(void) {}
static int replace(const char *from,const char *to)
{ return rename_fails?-1:rename(from,to); }
static void *find(void *h, const char *name)
{
    if(h==&driver && !strcmp(name,"WaitDisp")) return wait_display;
    assert(!h && !strcmp(name,"rename"));
    return replace;
}
static int gpio(unsigned pin)
{
    assert(pin==0x30f || pin==0x204 || pin==0x30c);
    return !(pin==0x30f?select_held:pin==0x204?accept_held:active_key==8);
}
static unsigned joy(void) { return active_key; }
static void display(const void *pixels,unsigned w,unsigned h,size_t pitch)
{
    assert(w==640 && h==480 && pitch==1280);
    if(pixels!=settings) {
        assert(shutdown_fixture && pixels==shutdown_pixels);
        ++shutdown_display;
    }
    ++flips;
}

static int file_access(const char *name,int mode)
{
    if(!strcmp(name,"/usr/retro/d35-launcher1/power-off.sh"))
        return shutdown_fixture?0:-1;
    return access(name,mode);
}

static void *power_alloc(size_t bytes)
{
    assert(shutdown_fixture && bytes==614400 && !shutdown_pixels);
    return shutdown_pixels=malloc(bytes);
}

static void power_free(void *pixels)
{
    assert(pixels && pixels==shutdown_pixels);
    free(pixels);
    shutdown_pixels=NULL;
}

static int power_command(const char *command)
{
    assert(shutdown_fixture && shutdown_pixels);
    if(!strcmp(command,"/bin/sh /usr/retro/d35-launcher1/power-off.sh")) {
        ++shutdown_calls;
        return shutdown_result;
    }
    assert(!strcmp(command,"/sbin/poweroff") && !shutdown_result);
    puts("PASS confirmed shutdown requests Linux poweroff only after card preparation");
    exit(0);
}
static int fixed_time(struct timeval *tv,void *tz)
{ (void)tz; tv->tv_sec=0; tv->tv_usec=0; return 0; }
static void audio_sink(const int16_t *samples,unsigned n)
{
    assert(n==735);
    if(verify)
        for(unsigned i=0;i<n*2;++i) {
            assert(samples[i]==expected[output]/2);
            if(++output==total) output=0;
        }
    ++calls;
}
static uint64_t cpu_time(void)
{
    struct timespec t;
    assert(!clock_gettime(CLOCK_THREAD_CPUTIME_ID,&t));
    return (uint64_t)t.tv_sec*1000000000ull+t.tv_nsec;
}
static unsigned char *read_data(const char *name,size_t *length)
{
    FILE *f=fopen(name,"rb"); assert(f && !fseek(f,0,SEEK_END));
    long n=ftell(f); assert(n>0 && !fseek(f,0,SEEK_SET));
    unsigned char *p=malloc(n); assert(p && fread(p,1,n,f)==(size_t)n && !fclose(f));
    *length=n; return p;
}

static __attribute__((naked)) unsigned call_settings_key(unsigned row __attribute__((unused)),
                                                         uintptr_t hook __attribute__((unused)))
{
    __asm__ volatile("push {r11, lr}\n\tmov r11, r0\n\tblx r1\n\tpop {r11, pc}");
}

static unsigned settings_key(unsigned row,unsigned key,bool pressed)
{
    active_key=key;
    accept_held=pressed;
    return call_settings_key(row,target(flips%2?0x8e30c:0x8ea00));
}

static void settings_file(const char *expected_value)
{
    char name[1024];
    assert(snprintf(name,sizeof(name),"%s/d35-launcher1/d35-loader.cfg",work)<(int)sizeof(name));
    FILE *f=fopen(name,"rb");
    char actual[4]={0};
    assert(f && fread(actual,1,sizeof(actual)-1,f)==strlen(expected_value) && !fclose(f));
    assert(!strcmp(actual,expected_value));
}

static void settings_snapshot(const char *file)
{
    char name[1024];
    assert(snprintf(name,sizeof(name),"%s/%s",work,file)<(int)sizeof(name));
    FILE *f=fopen(name,"wb");
    assert(f && fwrite(settings,1,sizeof(settings),f)==sizeof(settings) && !fclose(f));
}

static void load_stock_settings(void)
{
    assert(*(unsigned *)0x1998d8==1);
    *(unsigned *)0x1998d8=locale;
}

static void check_menu_art(const char *expected_file)
{
    char name[1024];
    assert(snprintf(name,sizeof(name),"%s/%s",work,expected_file)<(int)sizeof(name));
    size_t size;
    void *expected_art=read_data(name,&size), *actual=NULL;
    int (*load)(void **,const char *)=(void *)0x82aa8;
    assert(load(&actual,"menu.raw") && *(unsigned *)0x19bc0c==size);
    assert(!memcmp(actual,expected_art,size));
    free(actual);
    free(expected_art);
}

static void settings_background(const char *expected_file)
{
    void **art=(void **)0x199908;
    int (*load)(void **,const char *)=(void *)target(0x8f48c);
    assert(load(art,"setting.raw"));
    char name[1024];
    assert(snprintf(name,sizeof(name),"%s/%s",work,expected_file)<(int)sizeof(name));
    size_t bytes;
    void *expected=read_data(name,&bytes);
    assert(*(unsigned *)0x19bc0c==bytes && !memcmp(expected,*art,bytes));
    free(expected);
    memcpy(settings,(uint8_t *)*art+*(uint32_t *)*art,sizeof(settings));
    ((void (*)(void *,size_t,void *,unsigned))0x803a8)(settings,1280,*art,4);
    void (*frame)(void *,unsigned,unsigned,size_t)=(void *)target(0x8e2c8);
    frame(settings,640,480,1280);
}

static void expect_option_sprite(unsigned index)
{
    const uint8_t *art=*(void **)0x199908;
    const uint16_t *rect=(const uint16_t *)(art+16*index+8);
    unsigned left=rect[0],top=rect[1],right=rect[2],bottom=rect[3];
    const uint16_t *source=(const uint16_t *)(art+((const uint32_t *)art)[4*index]);
    assert(index>=5 && index<=14 && left==90 && right==550 &&
           bottom-top==(*(const uint32_t *)art==240?37:39));
    for(unsigned y=top;y<bottom;++y) {
        assert(!memcmp(settings+y*640+left,source,(right-left)*2));
        source+=right-left;
    }
}

static void settings_dialog(void)
{
    settings_background("setting-new.raw");
    expect_option_sprite(6); /* Existing one-byte preference is Auto. */
    expect_option_sprite(9);
    assert(settings_key(2,0x40,false)==0x40);
    assert(settings_key(3,0x40,false)==0); /* Restore -> Frame Skip */
    expect_option_sprite(8);
    assert(settings_key(3,0x2000,true)==0);
    expect_option_sprite(7);
    settings_file("0N"); /* migrated from the one-byte Auto setting */
    unsigned before=flips;
    assert(settings_key(3,0x2000,true)==0 && flips==before);
    assert(settings_key(3,0x40,false)==0); /* Frame Skip -> Theme */
    expect_option_sprite(5);
    expect_option_sprite(11);
    settings_snapshot("settings-new.rgb565");
    rename_fails=true;
    assert(settings_key(3,0x2000,true)==0);
    settings_file("0N");
    expect_option_sprite(11);
    rename_fails=false;
    assert(settings_key(3,0,false)==0);
    assert(settings_key(3,0x2000,true)==0);
    settings_file("0C");
    expect_option_sprite(12);
    check_menu_art("menu-new.raw"); /* change is pending until Back */
    assert(settings_key(3,0x10,false)==0 && settings_key(3,0x10,false)==0);
    expect_option_sprite(5);
    expect_option_sprite(10);
    assert(settings_key(3,0x4000,false)==0x4000);
}

static void settings_classic_dialog(void)
{
    settings_background("setting-classic.raw");
    assert(settings_key(3,0x40,false)==0 && settings_key(3,0x40,false)==0);
    expect_option_sprite(12);
    settings_snapshot("settings-classic.rgb565");
    assert(settings_key(3,0x2000,true)==0);
    settings_file("0N");
    assert(settings_key(3,0x4000,false)==0x4000);
}

static void exercise_settings(void)
{
    long (*language)(const char *,char **,int)=(void *)target(0x81e6c);
    assert(language(NULL,NULL,10)==1 && language("",NULL,10)==1 && language("11",NULL,10)==1);
    assert(language("abc",NULL,10)==1 && language("0",NULL,10)==0 && language("10",NULL,10)==10);
    void (*load_options)(void)=(void *)target(0x98174);
    void (*open_settings)(void)=(void *)target(0x984dc);
    static char locale_def[64];
    memcpy(locale_def+32,"ui_en.bkp",10);
    *(void **)0x19993c=locale_def;
    *(void **)0x199940=locale_def;
    patch(0x81da0,(uintptr_t)load_stock_settings);
    load_options();
    check_menu_art("menu-new.raw");
    const unsigned caches[]={0x199900,0x199904,0x199908,0x19990c,0x199934};
    for(unsigned i=0;i<5;++i) *(void **)caches[i]=malloc(16);
    patch(0x8dfe4,(uintptr_t)settings_dialog);
    open_settings();
    for(unsigned i=0;i<5;++i) assert(!*(void **)caches[i]);
    check_menu_art("menu-classic.raw");
    load_options(); /* re-open persisted Classic */
    check_menu_art("menu-classic.raw");
    patch(0x8dfe4,(uintptr_t)settings_classic_dialog);
    open_settings();
    check_menu_art("menu-new.raw");
    locale=2;
    load_options();
    check_menu_art("menu-classic.raw");
    char themed[1024], unavailable[1024];
    assert(snprintf(themed,sizeof(themed),"%s/d35-launcher1/ui_en.bkp",work)<(int)sizeof(themed));
    assert(snprintf(unavailable,sizeof(unavailable),"%s/new-pack-unavailable.bkp",work)<(int)sizeof(unavailable));
    assert(!rename(themed,unavailable));
    locale=1;
    load_options();
    check_menu_art("menu-classic.raw");
    assert(!rename(unavailable,themed));
    puts("PASS exact baked Settings sprites, held A, failed save, old config migration, theme persistence and locale fallback");
}

static void exercise_state_paths(void)
{
    char stock[4096], direct[4096];
    assert(snprintf(stock,sizeof(stock),"%s/fixture.state",work)<(int)sizeof(stock));
    assert(snprintf(direct,sizeof(direct),"%s.d35-70d8851",stock)<(int)sizeof(direct));
    FILE *f=fopen(stock,"wb"); assert(f && fputc('S',f)=='S' && !fclose(f));
    f=fopen(direct,"wb"); assert(f && fputc('D',f)=='D' && !fclose(f));
    int (*slot_exists)(const char *,int)=(void *)target(0x91a24);
    FILE *(*preview_open)(const char *,const char *)=(void *)target(0x91268);
    FILE *(*thumbnail_append)(const char *,const char *)=(void *)target(0x91db4);
    assert(!slot_exists(stock,F_OK));
    f=preview_open(stock,"rb"); assert(f && fgetc(f)=='S' && !fclose(f));
    *(void **)0x1c4100=&driver; /* direct SNES session active */
    assert(!slot_exists(stock,F_OK));
    f=preview_open(stock,"rb"); assert(f && fgetc(f)=='D' && !fclose(f));
    f=thumbnail_append(stock,"ab"); assert(f && fputc('T',f)=='T' && !fclose(f));
    f=fopen(stock,"rb"); assert(f && fgetc(f)=='S' && fgetc(f)==EOF && !fclose(f));
    f=fopen(direct,"rb"); assert(f && fgetc(f)=='D' && fgetc(f)=='T' && !fclose(f));
    *(void **)0x1c4100=NULL;
    puts("PASS SNES pause-slot preview and thumbnail append use the private state file");
}

static void shutdown_dialog(void)
{
    settings_background("setting-new.raw");
    assert(settings_key(0,8,false)==0 && shutdown_display==1);
    assert(settings_key(0,8,false)==0 && shutdown_display==1 && !shutdown_calls);
    assert(settings_key(0,0x4000,false)==0 && !shutdown_pixels && !shutdown_calls);
    assert(settings_key(0,8,false)==0 && shutdown_display==2);
    shutdown_result=1<<8;
    assert(settings_key(0,0x2000,true)==0 && shutdown_calls==1 && shutdown_display==4);
    assert(settings_key(0,0x2000,true)==0 && shutdown_calls==1);
    assert(settings_key(0,0x4000,false)==0 && !shutdown_pixels);
    assert(settings_key(0,8,false)==0 && shutdown_display==5);
    shutdown_result=0;
    settings_key(0,0x2000,true);
    abort();
}

static void ordered_settings_dialog(void)
{
    settings_background("setting-new.raw");
    for(unsigned i=0;i<3;++i) assert(settings_key(2,0x40,false)==0);
    expect_option_sprite(14);
    assert(settings_key(2,0x40,false)==0x40);
    assert(settings_key(3,0x10,false)==0x10);
    assert(settings_key(2,0x2000,true)==0 && shutdown_display==1);
    assert(settings_key(2,0x4000,false)==0 && !shutdown_pixels && !shutdown_calls);
    assert(settings_key(2,0x10,false)==0);
    assert(settings_key(2,0x10,false)==0);
    assert(settings_key(2,0x10,false)==0);
    assert(settings_key(2,0x10,false)==0x10);
    puts("PASS Settings navigation places Frame Skip, Theme and Power Off before factory reset");
}

#ifndef D35_STOCK_MENU_ENTRY
#define D35_STOCK_MENU_ENTRY main
#endif
int D35_STOCK_MENU_ENTRY(int argc,char **argv)
{
    assert(argc==5 || argc==6);
    bool ordered=argc==6 && !strcmp(argv[5],"ordered");
    work=argv[3];
    map_vendor(argv[1]);
    patch(0x11ce0,(uintptr_t)fopen); patch(0x11f20,(uintptr_t)fclose);
    patch(0x11b84,(uintptr_t)fseek); patch(0x11e84,(uintptr_t)ftell);
    patch(0x11ed8,(uintptr_t)malloc); patch(0x11ddc,(uintptr_t)fread);
    patch(0x11b6c,(uintptr_t)free); patch(0x11c8c,(uintptr_t)memset);
    patch(0x11ecc,(uintptr_t)memcpy); patch(0x11d28,(uintptr_t)memmove);
    patch(0x11c20,(uintptr_t)puts); patch(0x11be4,(uintptr_t)quiet);
    patch(0x11b48,(uintptr_t)fixed_time); patch(0xa695c,(uintptr_t)audio_sink);
    patch(0x80bec,(uintptr_t)path); patch(0x12010,(uintptr_t)find);
    patch(0x157c8,(uintptr_t)gpio); patch(0x86368,(uintptr_t)joy);
    patch(0x11b60,(uintptr_t)strtol); patch(0x11eb4,(uintptr_t)fwrite);
    patch(0x11fb0,(uintptr_t)fflush); patch(0x11b18,(uintptr_t)fsync); patch(0x11df4,(uintptr_t)fileno);
    patch(0x11e0c,(uintptr_t)file_access);
    patch(0x11f74,(uintptr_t)strcmp); patch(0x11fc8,(uintptr_t)memcmp);
    patch(0x11d64,(uintptr_t)strcpy);
    patch(0x11e78,(uintptr_t)calloc); patch(0x11ee4,(uintptr_t)strlen);
    patch(0x11f08,(uintptr_t)usleep); patch(0x11f38,(uintptr_t)sprintf);
    patch(0xa6658,(uintptr_t)display);
    *(void **)0x1b81a8=&driver;
    bool pcm=!strcmp(argv[4],"pcm");
    assert(pcm || !strcmp(argv[4],"mp3"));
    size_t bytes;
    unsigned char *old=read_data(argv[2],&bytes);
    const struct sound mp3={old,1,1,1,22050,1,old,old+bytes,0};
    void (*play)(unsigned,const struct sound *)=(void *)(pcm?target(0x98360):0x8750c);
    void (*mix)(void)=(void *)0x88e60;
    play(0,&mp3);
    struct sound *player=(void *)0x1b8994;
    assert(player->type==(pcm?2u:1u));
    if(pcm) {
        char expected_path[4096];
        assert(snprintf(expected_path,sizeof(expected_path),"%s/d35-launcher1/d35-menu.pcm",work)<(int)sizeof(expected_path));
        expected=(int16_t *)read_data(expected_path,&total);
        total/=2;
        verify=true;
        for(size_t i=0;i<=total/1470;++i) mix(); /* check samples across the loop seam */
        verify=false;
    } else {
        for(unsigned i=0;i<90;++i) mix();
    }
    unsigned before=calls;
    uint64_t t=cpu_time();
    for(unsigned i=0;i<1800;++i) mix();
    uint64_t elapsed=cpu_time()-t;
    assert(calls-before==1800);
    ((void (*)(unsigned))0x873f4)(0);
    assert(!player->data);
    printf("music=%s fills=%zu mixer_ns=%"PRIu64"\n",argv[4],calls-before,elapsed);
    if(pcm && !ordered) exercise_settings();
    if(pcm) exercise_state_paths();
    free(old); free((void *)expected);
    if(argc==6) {
        assert(ordered || !strcmp(argv[5],"shutdown"));
        if(ordered) {
            static char locale_def[64];
            memcpy(locale_def+32,"ui_en.bkp",10);
            *(void **)0x19993c=locale_def;
            *(void **)0x199940=locale_def;
            patch(0x81da0,(uintptr_t)load_stock_settings);
        }
        shutdown_fixture=true;
        patch(0x164abc,(uintptr_t)power_alloc);
        patch(0x164d58,(uintptr_t)power_free);
        patch(0x11d4c,(uintptr_t)power_command);
        patch(0x8dfe4,(uintptr_t)(ordered?ordered_settings_dialog:shutdown_dialog));
        locale=1;
        ((void (*)(void))target(0x98174))();
        ((void (*)(void))target(0x984dc))();
        assert(ordered);
    }
    return 0;
}
