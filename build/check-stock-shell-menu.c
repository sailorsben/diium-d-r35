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
static bool verify, select_held;
static unsigned active_key, flips, driver;
static uint16_t settings[640*480];
static const char *work;

static uintptr_t target(uintptr_t at)
{ return at+8+((int32_t)(*(uint32_t *)at<<8)>>6); }
static const char *path(void) { return work; }
static void wait_display(void) {}
static void *find(void *h, const char *name)
{
    if(h==&driver && !strcmp(name,"WaitDisp")) return wait_display;
    assert(!h && !strcmp(name,"rename"));
    return rename;
}
static int gpio(unsigned pin) { assert(pin==0x30f); return !select_held; }
static unsigned joy(void) { return active_key; }
static void display(const void *pixels,unsigned w,unsigned h,size_t pitch)
{
    assert(pixels==settings && w==640 && h==480 && pitch==1280);
    assert(settings[354*640+141]==0x18c6 && settings[353*640+141]==0x7bef);
    ++flips;
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
static void exercise_settings(void)
{
    long (*language)(const char *,char **,int)=(void *)target(0x81e6c);
    assert(language(NULL,NULL,10)==1 && language("",NULL,10)==1 && language("11",NULL,10)==1);
    assert(language("abc",NULL,10)==1 && language("0",NULL,10)==0 && language("10",NULL,10)==10);
    unsigned (*keys)(void)=(void *)target(0x8e30c);
    void (*frame)(void *,unsigned,unsigned,size_t)=(void *)target(0x8e2c8);
    for(unsigned i=0;i<640*480;++i) settings[i]=0x7bef;
    frame(settings,640,480,1280);
    assert(flips==1);
    select_held=true; active_key=1;
    assert(keys()==0 && flips==2);
    assert(keys()==0 && flips==2);
    select_held=false; active_key=0;
    assert(keys()==0 && flips==2);
    active_key=0x40; assert(keys()==0x40);
    select_held=true; active_key=1;
    assert(keys()==0 && flips==3);
    puts("PASS English fallback, valid locale IDs, stock keys, settings redraw, held Select, persistent toggle");
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

int main(int argc,char **argv)
{
    assert(argc==5);
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
    patch(0x11e0c,(uintptr_t)access);
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
        for(unsigned i=0;i<970;++i) mix(); /* crosses the 16-second loop seam */
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
    if(pcm) { exercise_settings(); exercise_state_paths(); }
    free(old); free((void *)expected);
    return 0;
}
