/* Census for reuse at the existing raster flush boundary. It never elides a
 * render. Exact snapshots are intentionally expensive; no benchmark claims. */
enum { D35_SPANS=16 };
struct d35_span_sample {
    unsigned y0,y1,pending;
    SPPU ppu;
    SLineData lines[240];
    SLineMatrixData matrix[240];
    struct d35_window_row windows[256];
    uint16_t fixed[256],colors[256];
    uint8_t regs[0x34],vram[65536];
    bool flicker;
};
static struct d35_span_sample d35_spans[2][D35_SPANS];
static unsigned d35_span_bank,d35_span_counts[2];
static unsigned d35_span_calls,d35_span_eligible,d35_span_rows,d35_span_hits,d35_span_hit_rows;
static unsigned d35_span_mode_mask,d35_span_complete,d35_span_height;

static void d35_span_begin(void) {
    d35_span_bank^=1;
    d35_span_counts[d35_span_bank]=0;
    d35_span_calls=d35_span_eligible=d35_span_rows=d35_span_hits=d35_span_hit_rows=d35_span_mode_mask=0;
    d35_span_complete=1;
    d35_span_height=PPU.ScreenHeight;
}

static void d35_span_candidate(unsigned start,unsigned end) {
    ++d35_span_calls;
    d35_span_mode_mask|=1u<<PPU.BGMode;
    if(start>end || end>=240 || d35_span_height!=PPU.ScreenHeight ||
       PPU.BGMode==5 || PPU.BGMode==6 || IPPU.DoubleHeightPixels || IPPU.DoubleWidthPixels ||
       IPPU.HalfWidthPixels || IPPU.Interlace || GFX.Pseudo || d35_span_counts[d35_span_bank]==D35_SPANS) {
        d35_span_complete=0;
        return;
    }
    unsigned n=end-start+1;
    ++d35_span_eligible;d35_span_rows+=n;
    struct d35_span_sample *p=d35_spans[d35_span_bank^1];
    for(unsigned i=0;i<d35_span_counts[d35_span_bank^1];++i,++p) {
        if(p->y0!=start || p->y1!=end || p->flicker!=reduce_sprite_flicker || p->pending!=d35_fixed_pending) continue;
        if(memcmp(&p->ppu,&PPU,sizeof(PPU)) || memcmp(p->regs,Memory.FillRAM+0x2100,sizeof(p->regs)) ||
           memcmp(p->lines,LineData+start,n*sizeof(*LineData)) ||
           (PPU.BGMode==7 && memcmp(p->matrix,LineMatrixData+start,n*sizeof(*LineMatrixData))) ||
           memcmp(p->windows,d35_window_rows+start,n*sizeof(*p->windows)) ||
           memcmp(p->fixed,d35_fixed_rows+start,n*sizeof(*p->fixed)) ||
           memcmp(p->colors,IPPU.ScreenColors,sizeof(p->colors)) || memcmp(p->vram,Memory.VRAM,sizeof(p->vram))) continue;
        ++d35_span_hits;d35_span_hit_rows+=n;
        break;
    }
    p=&d35_spans[d35_span_bank][d35_span_counts[d35_span_bank]++];
    p->y0=start;p->y1=end;p->flicker=reduce_sprite_flicker;p->pending=d35_fixed_pending;
    memcpy(&p->ppu,&PPU,sizeof(PPU));memcpy(p->regs,Memory.FillRAM+0x2100,sizeof(p->regs));
    memcpy(p->lines,LineData+start,n*sizeof(*LineData));
    if(PPU.BGMode==7)memcpy(p->matrix,LineMatrixData+start,n*sizeof(*LineMatrixData));
    memcpy(p->windows,d35_window_rows+start,n*sizeof(*p->windows));memcpy(p->fixed,d35_fixed_rows+start,n*sizeof(*p->fixed));
    memcpy(p->colors,IPPU.ScreenColors,sizeof(p->colors));memcpy(p->vram,Memory.VRAM,sizeof(p->vram));
}

__attribute__((visibility("default"))) void d35_span_read(unsigned *out) {
    out[0]=d35_span_calls;out[1]=d35_span_eligible;out[2]=d35_span_rows;out[3]=d35_span_hits;out[4]=d35_span_hit_rows;
    out[5]=d35_span_mode_mask;
    out[6]=d35_span_complete && d35_span_height && d35_span_hit_rows==d35_span_height;
}
