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
static bool percent_case;
static bool stock_case;
static const uint16_t *stock_overlay_frame;

static void capture(const char *name,const uint16_t *frame)
{
    char file[1024];
    assert(snprintf(file,sizeof(file),"%s/%s.rgb565",work,name)<(int)sizeof(file));
    FILE *out=fopen(file,"wb");
    assert(out && fwrite(frame,PIXELS*2,1,out)==1 && !fclose(out));
}

static void check_battery(const uint16_t *frame,int band,bool with_percentage)
{
    uint16_t ink=band==4?0xfb69:theme?0x8f5e:0xb69a;
    bool estimate=with_percentage && band<5;
    unsigned x=estimate?529:581;
    assert(frame[18*W+x]==ink && frame[34*W+x+35]==ink);
    assert((frame[25*W+576]==ink)==estimate);
    if(estimate) assert(frame[19*W+610]==ink);
    if(band==4) assert(frame[23*W+x+6]==ink);
    if(band==5) assert(frame[23*W+599]==0xff8d);
}

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
    if(!power_case) check_battery(grid_frame,*(int *)0x1b9b28,percent_case);
    if(draws==1) capture(percent_case?"home-percent":"home-icon",grid_frame);
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
{ assert((frame==grid_frame || frame==stock_overlay_frame) && width==W); ++adc_calls; }
static void stock_submit(const void *frame,unsigned w,unsigned h,size_t pitch)
{
    assert(frame==stock_overlay_frame && w==W && h==H && pitch==W*2);
    ++draws;
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
    assert(argc==3 || argc==4 || argc==5);
    theme=argc>=4 && !strcmp(argv[3],"classic");
    percent_case=argc==5 && !strcmp(argv[4],"percent");
    stock_case=theme;
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
    *(uintptr_t *)0x1be388=(uintptr_t)(stock_case?stock_submit:grid_draw);
    patch(0x11da0,(uintptr_t)grid_open);
    patch(0x11d70,(uintptr_t)grid_map); patch(0x11cd4,(uintptr_t)grid_close);
    patch(0x11efc,(uintptr_t)grid_unmap); patch(0x11d4c,(uintptr_t)grid_command);
    patch(0x81da0,(uintptr_t)load_stock_settings);
    *(void **)0x1b81a8=&driver;
    *(unsigned *)0x1998d8=1;
    *(unsigned *)0x199914=W;
    *(unsigned *)0x199918=H;
    *(int *)0x1b9b28=1;
    ((void (*)(void))target(0x98174))();
    if(stock_case) {
        unsigned (*key)(void)=(void *)target(0x89dc8);
        unsigned sequence_for_stock[]={0x20};
        sequence(sequence_for_stock,1);
        *(unsigned *)0x1998e0=5;
        assert(dispatch(target(0x9846c))==1 && next_event==0 && !draws);
        assert(key()==0x20);
        assert(dispatch(target(0x9846c))==5 && !draws);
        uint16_t *frame=calloc(PIXELS,sizeof(*frame));
        assert(frame);
        stock_overlay_frame=frame;
        *(void **)0x199910=frame;
        void (*overlay)(uint16_t *,unsigned)=(void *)target(0x13fc0);
        void (*present)(const void *,unsigned,unsigned,size_t)=(void *)0xa6658;
        for(int band=0;band<=5;++band) {
            *(int *)0x1b9b28=band;
            present(frame,W,H,W*2);
            overlay(frame,W);
            assert(*(int *)0x1b9b24==band && !adc_calls);
            check_battery(frame,band,percent_case);
        }
        assert(draws==6);
        assert(frame[10*W+515]==0 && frame[43*W+580]==0);
        char art_path[1024];
        assert(snprintf(art_path,sizeof(art_path),"%s/type.raw",work)<(int)sizeof(art_path));
        size_t art_bytes;
        unsigned char *art=read_data(art_path,&art_bytes);
        unsigned offset;
        memcpy(&offset,art+3*16,sizeof(offset)); /* Original NES carousel panel. */
        assert(offset+PIXELS*2<=art_bytes);
        memcpy(frame,art+offset,PIXELS*2);
        *(int *)0x1b9b28=1;
        present(frame,W,H,W*2);
        check_battery(frame,1,percent_case);
        capture("classic-carousel",frame);
        free(art);
        free(frame);
        puts("PASS Classic hands off to the stock carousel and uses one icon with an optional estimate");
        return 0;
    }
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
    if(percent_case) {
        unsigned keys[]={0,8};
        for(int band=0;band<=5;++band) {
            *(int *)0x1b9b28=band;
            sequence(keys,2);
            assert(dispatch(target(0x9846c))==5);
        }
        *(int *)0x1b9b28=1;
        draws-=6;
        puts("PASS New Home shows an icon beside each estimate and a charging icon when powered");
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
    // Pressing down on the last row keeps the platform selected. The footer
    // is a key legend; the shoulder buttons still dispatch directly above.
    unsigned bottom[]={0,0x40,0x2000};
    *(unsigned *)0x1c4300=8;
    sequence(bottom,3);
    assert(dispatch(target(0x9846c))==1 && *(unsigned *)0x199990==8 && draws==24);
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
    puts("PASS ARM home dispatch, 12 ordered stock type IDs, six direct shortcuts, tile-only arrows and locale fallback");
    printf("PASS physical-key cancel/confirm and %s RGB565 confirmation, working and secured frames\n",
           theme?"Classic":"New");
    return 0;
}
