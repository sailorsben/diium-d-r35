/* Execute the vendor GPIO scan, turbo path, and actual libretro callback.
 * The injected levels and USB reports stand in for connected hardware. */
#define main stock_fixture_main
#include "check-stock-snes-loader.c"
#undef main
#include <unistd.h>

enum { ESC=1u<<16, BOTH=9 };
static unsigned contacts,usb[4];
static const unsigned pins[]={0x205,0x30b,0x30f,0x30c,0x200,0x201,0x202,0x203,
                             0x204,0x30d,0x30a,0x208,0x207,0x30e,0x206};
static const unsigned native[]={0x4000,0x8000,1,8,0x10,0x40,0x80,0x20,
                               0x2000,0x1000,0x400,0x800,0x100,0x200,ESC};
static int gpio_level(unsigned pin)
{
    for(unsigned i=0;i<15;++i)
        if(pins[i]==pin) return !(contacts&native[i]);
    assert(pin==0x209 || pin==0x20a);
    return 1;
}
static unsigned usb_read(unsigned port) { assert(port<4); return usb[port]; }
static void (*frame_input)(void);
static unsigned read_pad(unsigned port)
{
    unsigned keys=0;
    for(unsigned id=0;id<14;++id) {
        int16_t (*read)(unsigned,unsigned,unsigned,unsigned)=(void *)0xa2f0c;
        if(read(port,1,0,id)) keys|=1u<<id;
    }
    return keys;
}
static unsigned target_of_call(unsigned at)
{
    unsigned op=*(unsigned *)at;
    assert((op>>24)==0xeb);
    return at+8+(((int32_t)(op<<8)>>6)&~3u);
}
static void sample(unsigned levels)
{
    contacts=levels;
    ((void (*)(void))0x1599c)();
    frame_input();
}

static const char *test_dir;
static int save_result;
static int test_access(const char *path,int mode)
{
    assert(!strcmp(path,"/usr/retro/d35-launcher1/ff2-controls.log") && !mode);
    return access("ff2-controls.log",F_OK);
}
static FILE *test_open(const char *path,const char *mode)
{
    if(!strcmp(path,"/proc/sys/kernel/random/boot_id")) return fopen(path,mode);
    const char *name=strrchr(path,'/');
    assert(name && (!strcmp(name,"/ff2-controls.log.tmp") || !strcmp(name,"/nes-viewport.log.tmp")));
    return fopen(name+1,mode);
}
static int test_rename(const char *a,const char *b)
{ return rename(strrchr(a,'/')+1,strrchr(b,'/')+1); }
static void wait_display(void) {}
static void *test_symbol(void *handle,const char *name)
{
    if(handle==(void *)1 && !strcmp(name,"WaitDisp")) return wait_display;
    assert(!handle && !strcmp(name,"rename")); return test_rename;
}
static int mock_save(const char *path)
{ assert(!strcmp(path,"test-slot")); return save_result; }
static unsigned slot_event(void) { return 0x2000; }
static void quiet_sound(unsigned channel,const void *sound) { assert(channel==1 && sound); }
static int mock_slot_ui(void)
{
    unsigned (*slot)(void)=(void *)(uintptr_t)target_of_call(0x91c94);
    int (*save)(const char *)=(void *)(uintptr_t)target_of_call(0x91d9c);
    /* The stock slot UI confirms A and calls the shared serializer. */
    contacts=0x2000;
    ((void (*)(void))0x1599c)();
    assert(slot()==0x2000 && save("test-slot")==save_result);
    return 0;
}
static int test_play(const char *path,unsigned type)
{
    assert(strstr(path,"Chaos Rush") && type==5);
    sample(0); sample(0x10); sample(0); sample(8); sample(0); sample(ESC);
    unsigned char *pause=(void *)0x1c4400;
    *(int *)(pause+28)=1; /* Save State row */
    pause[32]=1;
    *(void **)0x1b81a8=(void *)1;
    unsigned (*pause_key)(void)=(void *)(uintptr_t)target_of_call(0x9bc08);
    assert(pause_key()==0x2000 && !pause[32]);
    *(void **)0x1b81a8=NULL;
    sample(0);
    return 42;
}
static void check_capture(uintptr_t nested_loader)
{
    assert(!chdir(test_dir) && access("ff2-controls.log",F_OK)<0);
    patch(nested_loader,(uintptr_t)test_play);
    patch(0x11e0c,(uintptr_t)test_access);
    patch(0x11ce0,(uintptr_t)test_open);
    patch(0x11ddc,(uintptr_t)fread); patch(0x11f20,(uintptr_t)fclose);
    patch(0x11f38,(uintptr_t)sprintf); patch(0x11eb4,(uintptr_t)fwrite);
    patch(0x11fb0,(uintptr_t)fflush); patch(0x11df4,(uintptr_t)fileno);
    patch(0x11b18,(uintptr_t)fsync); patch(0x11c8c,(uintptr_t)memset);
    patch(0x11ed8,(uintptr_t)malloc); patch(0x11b6c,(uintptr_t)free);
    patch(0x11f74,(uintptr_t)strcmp); patch(0x12010,(uintptr_t)test_symbol);
    patch(0x86368,(uintptr_t)slot_event); patch(0xa37b0,(uintptr_t)mock_save);
    patch(0x91818,(uintptr_t)mock_slot_ui); patch(0x8750c,(uintptr_t)quiet_sound);
    *(unsigned *)0x199914=640; *(unsigned *)0x199918=480;
    memcpy((void *)0x19b8bc,(void *)0x16b254,16*sizeof(unsigned));
    *(unsigned *)0x1b81a0=0; usb[0]=usb[1]=0;
    strcpy((void *)0x1b8a00,"/usr/retro");
    int (*launch)(const char *,unsigned)=(void *)0xa5058;
    const char *rom="/usr/003/Final Fantasy II - Chaos Rush 2.2b.nes";
    assert(launch(rom,5)==42 && access("ff2-controls.log",F_OK)<0);
    save_result=1;
    assert(launch(rom,5)==42);
    FILE *log=fopen("ff2-controls.log","rb");
    assert(log);
    char text[2000]={0};
    assert(fread(text,1,sizeof(text)-1,log)>0 && !fclose(log));
    assert(strstr(text,"boot=") && strstr(text,"dropped=0") && strstr(text," slot ") &&
           strstr(text," serialize ") && strstr(text," saved ") &&
           strstr(text,"game 10000 0 00000009 00000009 00000000 0000") &&
           strstr(text," open-slots ") && strstr(text," close-slots ") &&
           strstr(text,"contact_edges=7 dropped=0") && strstr(text," 10000 0\n"));
    assert(launch(rom,5)==42); /* A completed physical run must stay available. */
    log=fopen("ff2-controls.log","rb");
    char next[2000]={0};
    assert(log && fread(next,1,sizeof(next)-1,log)>0 && !fclose(log) && !strcmp(text,next));
    puts("PASS one-shot capture through NES entry, save-slot callsites, and normal exit");
}
int main(int argc,char **argv)
{
    assert(argc==3 || argc==5);
    map_vendor(argv[1]);
    int repaired=atoi(argv[2]);
    patch(0x157c8,(uintptr_t)gpio_level);
    patch(0x1537c,(uintptr_t)usb_read);
    unsigned *mapping=(unsigned *)0x19b8bc;
    /* Check the fixture's expected directions/buttons against the shipped
     * libretro mask table, then give both players that default mapping. */
    assert(!memcmp(native,(void *)0x16b254,12*sizeof(unsigned)));
    for(unsigned p=0;p<4;++p)
        memcpy(mapping+16*p,(void *)0x16b254,16*sizeof(unsigned));
    frame_input=(void *)(uintptr_t)target_of_call(0xa4554);
    unsigned *keys=(unsigned *)0x1b9b50,*game=(unsigned *)0x1bd670;
    for(unsigned combination=0;combination<(1u<<15);++combination) {
        unsigned physical=0;
        for(unsigned i=0;i<15;++i)
            if(combination&(1u<<i)) physical|=native[i];
        sample(physical);
        unsigned expected=physical&0xffff;
        unsigned menu=expected|((physical&ESC)?BOTH:0);
        assert(*keys==menu && *game==(repaired?expected:menu));
        if(!(combination&(1u<<14)) || combination==(1u<<14))
            assert((read_pad(0)&0xfff)==((combination&0xfff)|
                   ((!repaired && (physical&ESC))?12:0)));
    }
    sample(ESC);
    printf("Esc alone: menu=%x core(Start,Select)=%x\n",*keys,read_pad(0)&12);
    for(unsigned i=0;i<4;++i) {
        usb[0]=((i&1)?8:0)|((i&2)?1:0);
        usb[1]=8;
        sample(ESC|0x2000);
        assert(*game==(0x2000|(repaired?usb[0]:BOTH)) && (read_pad(1)&12)==8);
    }
    /* Rotate the D-pad, remap physical A to logical Start, keep Esc isolated. */
    *(unsigned *)0x1b81a0=1;
    usb[0]=0; mapping[3]=0x2000; mapping[8]=8;
    sample(ESC|0x10|0x2000);
    assert((*game&0xf0)==0x80 && (read_pad(0)&8) && !!(read_pad(0)&256)==!repaired);
    puts("PASS 32768 physical combinations, USB players, rotated D-pad and custom mapping");
    if(argc==5) {
        test_dir=argv[4];
        check_capture(strtoul(argv[3],NULL,16));
    }
    return 0;
}
