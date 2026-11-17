/* Execute Reset Game through the compiled ARM pause key path. */
#define main stock_audit_main
#include "check-stock-snes-loader.c"
#undef main
#include <stdbool.h>

static unsigned key_index, reset_calls, sound_calls;
static const unsigned keys[]={0x2000,0,0x2000};
static int token;
static void wait_display(void) {}
static void reset_game(void) { ++reset_calls; }
static void ignored_frame(void) {}
static void sound_cue(unsigned channel,const void *cue)
{ assert(channel==1 && cue); ++sound_calls; }
static unsigned joy(void)
{
    assert(key_index<sizeof(keys)/sizeof(*keys));
    unsigned key=keys[key_index++];
    *(unsigned *)0x1b9b50=key;
    return key;
}
static void *lookup(void *handle,const char *name)
{
    if(handle==&token && !strcmp(name,"WaitDisp")) return wait_display;
    if(handle==&token && !strcmp(name,"retro_reset")) return reset_game;
    return NULL;
}

int main(int argc,char **argv)
{
    assert(argc==4);
    uintptr_t frame_entry=strtoul(argv[2],NULL,16);
    uintptr_t key_entry=strtoul(argv[3],NULL,16);
    map_vendor(argv[1]);
    static uint16_t frame[640*480];
    *(unsigned *)0x199914=640;
    *(unsigned *)0x199918=480;
    *(void **)0x199910=frame;
    *(void **)0x1b81a8=&token;
    *(void **)0x1bd5dc=&token;
    patch(0x12010,(uintptr_t)lookup);
    patch(0x86368,(uintptr_t)joy);
    patch(0x8750c,(uintptr_t)sound_cue);
    patch(frame_entry,(uintptr_t)ignored_frame); /* display is a separate seam */
    unsigned char *pause=(void *)0x1c4400;
    *(int *)(pause+28)=4; /* Reset Game row */
    pause[32]=1; /* menu active */
    unsigned (*key)(void)=(void *)key_entry;
    assert(key()==0x40 && pause[34] && !reset_calls);
    assert(key()==0 && pause[34] && !reset_calls);
    assert(key()==0x2000 && !pause[32] && reset_calls==1);
    assert(sound_calls>=2);
    puts("PASS Reset Game waits for a fresh A, resets the active core once, and resumes");
}
