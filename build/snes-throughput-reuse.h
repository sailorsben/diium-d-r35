/* Census only: a conservative whole-frame equality key. It never bypasses a
 * render, and incomplete/multi-entry/hires frames invalidate its predecessor. */
static struct {
    SPPU ppu;
    SLineData lines[240];
    struct d35_window_row windows[256];
    uint16_t fixed[256];
    uint16_t colors[256];
    uint8_t regs[0x34], vram[65536];
    bool flicker;
    unsigned pending, valid, eligible, match;
} reuse;

static void d35_reuse_candidate(unsigned start, unsigned end) {
    reuse.eligible = reuse.match = 0;
    if(start || end+1!=PPU.ScreenHeight || !PPU.ScreenHeight || PPU.ScreenHeight>239 ||
       PPU.BGMode>=5 || IPPU.DoubleHeightPixels || IPPU.DoubleWidthPixels ||
       IPPU.HalfWidthPixels || IPPU.Interlace || GFX.Pseudo) {
        reuse.valid=0;
        return;
    }
    /* This key includes several PPU latches that are irrelevant to the final
     * image. Measure hit coverage before considering a smaller dependency key. */
    size_t line_bytes=PPU.ScreenHeight*sizeof(*LineData);
    reuse.eligible=1;
    reuse.match=reuse.valid && reuse.flicker==reduce_sprite_flicker && reuse.pending==d35_fixed_pending &&
        !memcmp(&reuse.ppu,&PPU,sizeof(PPU)) && !memcmp(reuse.regs,Memory.FillRAM+0x2100,sizeof(reuse.regs)) &&
        !memcmp(reuse.lines,LineData,line_bytes) && !memcmp(reuse.windows,d35_window_rows,sizeof(reuse.windows)) &&
        !memcmp(reuse.fixed,d35_fixed_rows,sizeof(reuse.fixed)) &&
        !memcmp(reuse.colors,IPPU.ScreenColors,sizeof(reuse.colors)) && !memcmp(reuse.vram,Memory.VRAM,sizeof(reuse.vram));
    reuse.valid=1;
    if(reuse.match) return;
    reuse.flicker=reduce_sprite_flicker;reuse.pending=d35_fixed_pending;
    memcpy(&reuse.ppu,&PPU,sizeof(PPU));memcpy(reuse.regs,Memory.FillRAM+0x2100,sizeof(reuse.regs));
    memcpy(reuse.lines,LineData,line_bytes);memcpy(reuse.windows,d35_window_rows,sizeof(reuse.windows));
    memcpy(reuse.fixed,d35_fixed_rows,sizeof(reuse.fixed));memcpy(reuse.colors,IPPU.ScreenColors,sizeof(reuse.colors));
    memcpy(reuse.vram,Memory.VRAM,sizeof(reuse.vram));
}

__attribute__((visibility("default"))) unsigned d35_reuse_read(void) {
    unsigned flags=reuse.eligible|(reuse.match<<1);
    reuse.eligible=reuse.match=0;
    return flags;
}
