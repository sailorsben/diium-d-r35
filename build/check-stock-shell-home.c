/* Execute the actual ARM hooks, with the display, joypad and power read mocked. */
#define D35_STOCK_MENU_ENTRY stock_menu_fixture_main
#include "check-stock-shell-menu.c"
#include <setjmp.h>

enum { W=640,H=480,PIXELS=W*H };
static uint16_t *grid_frame;
static unsigned draws, waits, confirms, unmaps, cue_calls, adc_calls;
static unsigned events[40], count, next_event;
static uint32_t power_regs[4096/4];
static bool power_case;
static jmp_buf powered_off;
static uint16_t *power_asset;
static unsigned power_views, phase_mask, theme, next_view;
static bool esc_pressed;

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
    assert(grid_frame[18*W+581]!=0 && grid_frame[18*W+581]==grid_frame[34*W+616]);
    ((void (*)(uint16_t *,unsigned))target(0x13fc0))(grid_frame,W);
    assert(!adc_calls);
    if(next_view) {
        enum { X=77,Y=153,PANEL_W=486,PANEL_H=174 };
        const unsigned view=next_view-1;
        const uint16_t *panel=power_asset+(theme*6+view)*PANEL_W*PANEL_H;
        for(unsigned y=0;y<PANEL_H;++y)
            for(unsigned x=0;x<PANEL_W;++x)
                if(panel[y*PANEL_W+x])
                    assert(grid_frame[(Y+y)*W+X+x]==panel[y*PANEL_W+x]);
        phase_mask|=1u<<view;
        ++power_views;
        next_view=0;
    }
}
static unsigned grid_joy(void)
{
    assert(next_event<count);
    unsigned event=events[next_event++];
    if(event==0x10000) { power_regs[0x68/4]=8; next_view=1; event=0; }
    if(event==0x20000) { power_regs[0x68/4]=0; event=0; }
    if(power_case && event==0x2000) next_view=2;
    return event;
}
static int grid_gpio(unsigned pin)
{ assert(pin==0x206); return !esc_pressed; }
static void grid_cue(unsigned channel,const struct sound *cue)
{
    assert(channel==1 && cue->data && cue->type==2 && cue->rate==44100 &&
           !cue->loop && (const char *)cue->end>(const char *)cue->begin);
    ++cue_calls;
}
static void grid_adc(uint16_t *frame,unsigned width)
{ assert(frame==grid_frame && width==W); ++adc_calls; }
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
        next_view=5;
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
    assert(argc==3 || (argc==4 && !strcmp(argv[3],"classic")));
    theme=argc==4;
    work=argv[2];
    map_vendor(argv[1]);
    patch(0x11ce0,(uintptr_t)fopen); patch(0x11f20,(uintptr_t)fclose);
    patch(0x11b84,(uintptr_t)fseek); patch(0x11e84,(uintptr_t)ftell);
    patch(0x11ed8,(uintptr_t)malloc); patch(0x11ddc,(uintptr_t)fread);
    patch(0x11b6c,(uintptr_t)free); patch(0x11ecc,(uintptr_t)memcpy);
    patch(0x11fc8,(uintptr_t)memcmp);
    patch(0x80bec,(uintptr_t)path); patch(0x12010,(uintptr_t)grid_find);
    patch(0x86368,(uintptr_t)grid_joy); patch(0x11f08,(uintptr_t)grid_delay);
    patch(0x11e0c,(uintptr_t)grid_access); patch(0x8750c,(uintptr_t)grid_cue);
    patch(0x157c8,(uintptr_t)grid_gpio); patch(0x13e30,(uintptr_t)grid_adc);
    patch(0x164abc,(uintptr_t)grid_alloc); patch(0x164d58,(uintptr_t)grid_free);
    patch(0xa6658,(uintptr_t)grid_draw); patch(0x11da0,(uintptr_t)grid_open);
    patch(0x11d70,(uintptr_t)grid_map); patch(0x11cd4,(uintptr_t)grid_close);
    patch(0x11efc,(uintptr_t)grid_unmap); patch(0x11d4c,(uintptr_t)grid_command);
    patch(0x81da0,(uintptr_t)load_stock_settings);
    *(void **)0x1b81a8=&driver;
    *(unsigned *)0x1998d8=1;
    *(unsigned *)0x199914=W;
    *(unsigned *)0x199918=H;
    *(int *)0x1b9b28=1;
    ((void (*)(void))target(0x98174))();
    char asset_path[4096];
    assert(snprintf(asset_path,sizeof(asset_path),"%s/d35-launcher1/power-dialog.rgb565",work)
           <(int)sizeof(asset_path));
    size_t asset_bytes;
    power_asset=(uint16_t *)read_data(asset_path,&asset_bytes);
    assert(asset_bytes==2*6*486*174*2);

    const unsigned shortcuts[]={8,1,0x1000,0x8000,0x400,0x800};
    const unsigned modes[]={5,3,4,2,0,6};
    for(unsigned i=0;i<6;++i) {
        unsigned keys[]={0,shortcuts[i]};
        sequence(keys,2);
        assert(dispatch(target(0x9846c))==modes[i] && next_event==2 && !grid_frame);
    }
    const unsigned types[]={3,2,1,7,5,6,4,0,8,9,10,11};
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
    assert(dispatch(target(0x9846c))==1 && *(unsigned *)0x199990==3 && draws==23);
    assert(cue_calls==4);
    unsigned (*menu_key)(void)=(void *)target(0x884ec);
    unsigned chord[]={9,9};
    sequence(chord,2);
    assert(menu_key()==9);
    esc_pressed=true;
    assert(menu_key()==0x4000);
    esc_pressed=false;
    ((void (*)(uint16_t *,unsigned))target(0x13fc0))(NULL,W);
    assert(adc_calls==1);
    adc_calls=0;
    *(unsigned *)0x1998d8=3;
    *(unsigned *)0x1998e0=7;
    assert(dispatch(target(0x9846c))==7 && next_event==2);
    *(unsigned *)0x1998d8=1;

    power_case=true;
    unsigned cancel[]={0,0x10000,0x20000,0x4000,8};
    sequence(cancel,5);
    assert(dispatch(target(0x9846c))==5 && !confirms && unmaps==1 && !grid_frame);
    unsigned esc_cancel[]={0,9,0,9,8};
    esc_pressed=true;
    sequence(esc_cancel,5);
    assert(dispatch(target(0x9846c))==5 && !confirms && unmaps==2 && !grid_frame);
    esc_pressed=false;
    unsigned confirm[]={0,0x10000,0x20000,0x2000};
    sequence(confirm,4);
    if(!setjmp(powered_off)) {
        dispatch(target(0x9846c));
        abort();
    }
    assert(confirms==1 && next_event==4);
    assert(power_views==4 && phase_mask==((1u<<0)|(1u<<1)|(1u<<4)));
    free(grid_frame);
    free(power_asset);
    puts("PASS ARM home dispatch, 12 ordered stock type IDs, six shortcuts, arrows and locale fallback");
    printf("PASS physical-key cancel/confirm and %s RGB565 confirmation, working and secured frames\n",
           theme?"Classic":"New");
    return 0;
}
