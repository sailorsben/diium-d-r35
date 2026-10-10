/* Experimental single-layer window batching. General PPU states fall back.
 * Capture the window with the scroll line; never let future edge writes alter
 * an earlier row. This header is not part of the installed1.19 core. */
#ifndef D35_PLUS_A7_WINDOW_H
#define D35_PLUS_A7_WINDOW_H
struct d35_window_clip { unsigned count,left[2],right[2]; };
void d35_window_reset(void);
void d35_window_capture(unsigned);
unsigned d35_window_defer(void);
unsigned d35_window_fetch(unsigned,unsigned,struct d35_window_clip *);
unsigned d35_window_same(unsigned,unsigned);
#ifdef D35_WINDOW_IMPLEMENTATION
struct d35_window_row { unsigned char valid,left,right,inside,main_mask,sub_mask; };
static struct d35_window_row d35_window_rows[256];
static unsigned d35_window_eligible(void)
{
    unsigned i;
    if(PPU.BGMode!=1 || PPU.ForcedBlanking || (Memory.FillRAM[0x2133]&15u) ||
       (PPU.BGMosaic[0] && PPU.Mosaic>1) || (Memory.FillRAM[0x2130]&0xf0u) ||
       PPU.ClipWindow1Enable[0] || !PPU.ClipWindow2Enable[0]) return 0;
    for(i=1;i<6;i++) if(PPU.ClipWindow2Enable[i]) return 0;
    return 1;
}
void d35_window_reset(void) { memset(d35_window_rows,0,sizeof(d35_window_rows)); }
void d35_window_capture(unsigned row)
{
    struct d35_window_row *r=&d35_window_rows[row&255u];
    memset(r,0,sizeof(*r));
    if(!d35_window_eligible()) return;
    r->valid=1;r->left=PPU.Window2Left;r->right=PPU.Window2Right;
    r->inside=PPU.ClipWindow2Inside[0];
    r->main_mask=(Memory.FillRAM[0x212c]&Memory.FillRAM[0x212e]&1u)!=0;
    r->sub_mask=(Memory.FillRAM[0x212d]&Memory.FillRAM[0x212f]&1u)!=0;
}
unsigned d35_window_defer(void)
{
    unsigned row;
    if(!IPPU.RenderThisFrame || !d35_window_eligible()) return 0;
    for(row=IPPU.PreviousLine;row<(unsigned)IPPU.CurrentLine;row++)
        if(row>=256 || !d35_window_rows[row].valid) return 0;
    return 1;
}
unsigned d35_window_same(unsigned a,unsigned b)
{
    if(a>=256 || b>=256) return 0;
    return !memcmp(&d35_window_rows[a],&d35_window_rows[b],sizeof(struct d35_window_row));
}
unsigned d35_window_fetch(unsigned row,unsigned sub,struct d35_window_clip *clip)
{
    const struct d35_window_row *r;
    if(row>=256 || !(r=&d35_window_rows[row])->valid) return 0;
    memset(clip,0,sizeof(*clip));
    if(!(sub?r->sub_mask:r->main_mask)) {
        clip->count=1;clip->right[0]=256;return 1;
    }
    if(!r->inside) {
        clip->count=1;clip->left[0]=r->left;clip->right[0]=r->right+1u;return 1;
    }
    if(r->left>r->right) {
        clip->count=1;clip->right[0]=256;return 1;
    }
    if(r->left) { clip->right[clip->count++]=r->left; }
    if(r->right<255) {
        unsigned at=clip->count++;clip->left[at]=r->right+1u;clip->right[at]=256;
    }
    if(!clip->count) { clip->count=1;clip->left[0]=1; }
    return 1;
}
#endif
#endif
