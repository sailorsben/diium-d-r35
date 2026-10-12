/* Readable analysis of the byte-matched ROM's D0/3C89 and D0/3CC1 scripts.
 * Engine calls document semantics; this is not a native game runtime. Each
 * frame(0) yields to the game's animation scheduler, not a host-clock sleep. */
typedef struct FF6Animation FF6Animation;
void frame(FF6Animation *,unsigned);
void zoom_circle(FF6Animation *,int);
void update_circle(FF6Animation *);
void cycle_bg3_palette(FF6Animation *,unsigned,unsigned,unsigned);
void wait_scanline(FF6Animation *,unsigned);
void init_scroll_wave(FF6Animation *,unsigned,unsigned,unsigned);
void update_scroll_wave(FF6Animation *);

/* Initialization selects Window2 on BG3/BG4 ($2124=cc), and half-adds BG1/BG3
 * into the affected BG2/sprite layers. BG4 is not rendered in SNES Mode1. */
void ff6_confuser_circle_loops(FF6Animation *a)
{
    const unsigned lengths[3]={41,65,40};
    const int zoom[3]={1,0,-1};
    for(unsigned phase=0;phase<3;phase++)for(unsigned i=0;i<lengths[phase];i++) {
        if(zoom[phase])zoom_circle(a,zoom[phase]);
        cycle_bg3_palette(a,4,1,3);
        wait_scanline(a,216);
        update_circle(a);
        frame(a,0);
    }
}
/* BG1 temporarily points at the battle background tilemap ($6100) and graphics
 * ($1000), with the battle background's scroll base. BG3 owns the circle. */
void ff6_confuser_wave_loops(FF6Animation *a)
{
    const unsigned amplitudes[11]={1,3,5,7,9,7,5,4,3,2,1};
    for(unsigned phase=0;phase<11;phase++) {
        unsigned axes=(phase==3 || phase==4 || phase==5)?1:3;
        init_scroll_wave(a,amplitudes[phase],1,axes);
        for(unsigned i=0;i<4;i++) { update_scroll_wave(a);frame(a,0); }
        if(phase==4)for(unsigned i=0;i<97;i++) { update_scroll_wave(a);frame(a,0); }
    }
}
