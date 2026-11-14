/* Execute the actual ARM hooks, with the display, joypad and power read mocked. */
#define D35_STOCK_MENU_ENTRY stock_menu_fixture_main
#include "check-stock-shell-menu.c"
#include <setjmp.h>

enum { W=640,H=480,PIXELS=W*H };
static uint16_t *grid_frame;
static unsigned draws, waits, calls_to_joy, confirms, unmaps;
static unsigned events[40], count, next_event;
static uint32_t power_regs[4096/4];
static bool power_case;
static jmp_buf powered_off;

static void grid_wait(void) { ++waits; }
static void *grid_find(void *handle,const char *name)
{
    assert(handle==&driver && !strcmp(name,"WaitDisp"));
    return grid_wait;
}
static void *grid_alloc(size_t bytes)
{
    assert(bytes==PIXELS*2 && !grid_frame);
    return grid_frame=malloc(bytes);
}
static void grid_free(void *pointer)
{
    assert(pointer==grid_frame && waits>draws);
    free(pointer);
    grid_frame=NULL;
}
static void grid_draw(const void *pixels,unsigned w,unsigned h,size_t pitch)
{
    assert(w==W && h==H && pitch==W*2 && pixels==grid_frame && waits>draws);
    ++draws;
}
static unsigned grid_joy(void)
{
    assert(next_event<count);
    unsigned event=events[next_event++];
    if(event==0x10000) { power_regs[0x68/4]=8; event=0; }
    if(event==0x20000) { power_regs[0x68/4]=0; event=0; }
    ++calls_to_joy;
    return event;
}
static int grid_delay(unsigned us) { assert(us==20000); return 0; }
static int grid_access(const char *path,int mode)
{
    assert(!strcmp(path,"/usr/retro/d35-launcher1/power-off.sh") && mode==4);
    return power_case?0:-1;
}
static int grid_open(const char *path,int flags)
{ assert(!strcmp(path,"/dev/mem") && flags==0); return 123; }
static long grid_map(void *address,size_t length,int protection,int flags,int fd,long offset)
{
    assert(!address && length==4096 && protection==1 && flags==1 && fd==123 &&
           (uint32_t)offset==0xd0000000u);
    return (long)power_regs;
}
static int grid_close(int fd) { assert(fd==123); return 0; }
static int grid_unmap(void *p,size_t bytes)
{ assert(p==power_regs && bytes==4096); ++unmaps; return 0; }
static int grid_command(const char *command)
{
    if(!strcmp(command,"/bin/sh /usr/retro/d35-launcher1/power-off.sh")) {
        ++confirms;
        return 0;
    }
    assert(!strcmp(command,"/sbin/poweroff") && confirms==1);
    longjmp(powered_off,1);
}

static __attribute__((naked)) unsigned dispatch(uintptr_t hook __attribute__((unused)))
{
    __asm__ volatile("push {r4,lr}\n\tblx r0\n\tmov r0,r4\n\tpop {r4,pc}");
}
static void sequence(const unsigned *keys,unsigned n)
{
    assert(n<=sizeof(events)/sizeof(*events));
    memcpy(events,keys,n*sizeof(*keys));
    count=n;
    next_event=0;
}

int main(int argc,char **argv)
{
    assert(argc==3);
    work=argv[2];
    map_vendor(argv[1]);
    patch(0x11ce0,(uintptr_t)fopen); patch(0x11f20,(uintptr_t)fclose);
    patch(0x11b84,(uintptr_t)fseek); patch(0x11e84,(uintptr_t)ftell);
    patch(0x11ed8,(uintptr_t)malloc); patch(0x11ddc,(uintptr_t)fread);
    patch(0x11b6c,(uintptr_t)free); patch(0x11ecc,(uintptr_t)memcpy);
    patch(0x80bec,(uintptr_t)path); patch(0x12010,(uintptr_t)grid_find);
    patch(0x86368,(uintptr_t)grid_joy); patch(0x11f08,(uintptr_t)grid_delay);
    patch(0x11e0c,(uintptr_t)grid_access); patch(0x8750c,(uintptr_t)quiet);
    patch(0x164abc,(uintptr_t)grid_alloc); patch(0x164d58,(uintptr_t)grid_free);
    patch(0xa6658,(uintptr_t)grid_draw); patch(0x11da0,(uintptr_t)grid_open);
    patch(0x11d70,(uintptr_t)grid_map); patch(0x11cd4,(uintptr_t)grid_close);
    patch(0x11efc,(uintptr_t)grid_unmap); patch(0x11d4c,(uintptr_t)grid_command);
    *(void **)0x1b81a8=&driver;
    *(unsigned *)0x1998d8=1;
    *(unsigned *)0x199914=W;
    *(unsigned *)0x199918=H;

    const unsigned shortcuts[]={8,1,0x1000,0x8000,0x400,0x800};
    const unsigned modes[]={5,3,4,2,0,6};
    for(unsigned i=0;i<6;++i) {
        unsigned keys[]={0,shortcuts[i]};
        sequence(keys,2);
        assert(dispatch(target(0x9846c))==modes[i] && next_event==2 && !grid_frame);
    }
    const unsigned types[]={2,3,1,7,4,6,5,0,8,9,10,11};
    unsigned (*type_key)(void)=(void *)target(0x89dc8);
    for(unsigned i=0;i<12;++i) {
        unsigned keys[]={0,0x2000};
        *(unsigned *)0x1c4300=i;
        sequence(keys,2);
        assert(dispatch(target(0x9846c))==1 && *(unsigned *)0x199990==types[i]);
        assert(type_key()==0x2000 && next_event==2 && !grid_frame);
    }
    unsigned navigation[]={0,0x40,0x20,0x10,0x80,0x2000};
    *(unsigned *)0x1c4300=0;
    sequence(navigation,6);
    assert(dispatch(target(0x9846c))==1 && *(unsigned *)0x199990==2 && draws==23);
    *(unsigned *)0x1998d8=3;
    *(unsigned *)0x1998e0=7;
    assert(dispatch(target(0x9846c))==7 && next_event==6);
    *(unsigned *)0x1998d8=1;

    power_case=true;
    unsigned cancel[]={0,0x10000,0x20000,0x4000,8};
    sequence(cancel,5);
    assert(dispatch(target(0x9846c))==5 && !confirms && unmaps==1 && !grid_frame);
    unsigned confirm[]={0,0x10000,0x20000,0x2000};
    sequence(confirm,4);
    if(!setjmp(powered_off)) {
        dispatch(target(0x9846c));
        abort();
    }
    assert(confirms==1 && next_event==4);
    free(grid_frame);
    puts("PASS ARM home dispatch, all 12 stock type IDs, six shortcuts, arrows, locale fallback and physical-key cancel/confirm");
    return 0;
}
