/* Mode1 Window2 snapshots for every affected background. Unsupported window
 * combinations retain the original flush/clip path. No game/effect IDs here. */
#ifndef D35_PLUS_A7_WINDOW_H
#define D35_PLUS_A7_WINDOW_H
struct d35_window_clip { unsigned count,left[2],right[2]; };
void d35_window_reset(void);
void d35_window_capture(unsigned);
unsigned d35_window_defer(void);
unsigned d35_window_fetch(unsigned,unsigned,unsigned,struct d35_window_clip *);
unsigned d35_window_is_target(unsigned);
unsigned d35_window_same(unsigned,unsigned);
#ifdef D35_WINDOW_IMPLEMENTATION
#ifdef D35_EFFECT_COUNTS
extern unsigned long long d35_conf[128],d35_hyp[128];
#define D35_WCOUNT(n) (++d35_conf[n])
#else
#define D35_WCOUNT(n) ((void)0)
#endif
struct d35_window_row { unsigned char valid,left,right,inside,main_mask,sub_mask,targets; };
static struct d35_window_row d35_window_rows[256];
static unsigned d35_invalid_prefix[257],d35_captured_until,d35_capture_ordered;
static unsigned d35_window_targets(void)
{
    unsigned mask=0,i;
    for(i=0;i<3;i++) if(PPU.ClipWindow2Enable[i]) mask|=1u<<i;
    return mask;
}
unsigned d35_window_is_target(unsigned bg)
{ return bg<3 && (d35_window_targets()&(1u<<bg)); }
static unsigned d35_window_eligible(void)
{
    unsigned mask,i;
    if(PPU.BGMode!=1) { D35_WCOUNT(4);return 0; }
    if(PPU.ForcedBlanking || (Memory.FillRAM[0x2133]&15u)) { D35_WCOUNT(5);return 0; }
    if(PPU.ClipWindow2Enable[4] || PPU.ClipWindow2Enable[5]) { D35_WCOUNT(9);return 0; }
    mask=d35_window_targets();
    /* With no rendered layer using Window2, its edges cannot change output.
     * Enable/mask/control changes still flush before altering that premise. */
    if(!mask) return 1;
    if(Memory.FillRAM[0x2130]&0xf0u) { D35_WCOUNT(7);return 0; }
    for(i=0;i<3;i++) if(mask&(1u<<i)) {
        if(PPU.BGMosaic[i] && PPU.Mosaic>1) { D35_WCOUNT(6);return 0; }
        if(PPU.ClipWindow1Enable[i]) { D35_WCOUNT(8);return 0; }
    }
    /* Mode1 has no BG4; it cannot depend on either Window2 edge. */
    return 1;
}
static void d35_window_record_validity(unsigned row,unsigned valid)
{
    if(row==d35_captured_until || row+1==d35_captured_until) {
        d35_invalid_prefix[row+1]=d35_invalid_prefix[row]+!valid;
        if(row==d35_captured_until) ++d35_captured_until;
    } else d35_capture_ordered=0;
}
void d35_window_reset(void)
{
    memset(d35_window_rows,0,sizeof(d35_window_rows));
    d35_captured_until=0;d35_capture_ordered=1;d35_invalid_prefix[0]=0;
}
void d35_window_capture(unsigned row)
{
    unsigned i;
    struct d35_window_row *r=&d35_window_rows[row&255u];
    memset(r,0,sizeof(*r));
    if(!d35_window_eligible()) { D35_WCOUNT(14);d35_window_record_validity(row&255u,0);return; }
    D35_WCOUNT(13);r->valid=1;r->left=PPU.Window2Left;r->right=PPU.Window2Right;
    r->targets=d35_window_targets();
    for(i=0;i<3;i++) if(PPU.ClipWindow2Inside[i]) r->inside|=1u<<i;
    r->main_mask=Memory.FillRAM[0x212c]&Memory.FillRAM[0x212e]&r->targets;
    r->sub_mask=Memory.FillRAM[0x212d]&Memory.FillRAM[0x212f]&r->targets;
    d35_window_record_validity(row&255u,1);
}
unsigned d35_window_defer(void)
{
    unsigned row;
    D35_WCOUNT(1);
    if(!IPPU.RenderThisFrame || !d35_window_eligible()) return 0;
    if(d35_capture_ordered && (unsigned)IPPU.PreviousLine<=(unsigned)IPPU.CurrentLine &&
       (unsigned)IPPU.CurrentLine<=d35_captured_until)
        return d35_invalid_prefix[IPPU.PreviousLine]==d35_invalid_prefix[IPPU.CurrentLine];
    for(row=IPPU.PreviousLine;row<(unsigned)IPPU.CurrentLine;row++)
        if(row>=256 || !d35_window_rows[row].valid) return 0;
    return 1;
}
unsigned d35_window_same(unsigned a,unsigned b)
{
    if(a>=256 || b>=256) return 0;
    return !memcmp(&d35_window_rows[a],&d35_window_rows[b],sizeof(struct d35_window_row));
}
unsigned d35_window_fetch(unsigned bg,unsigned row,unsigned sub,struct d35_window_clip *clip)
{
    const struct d35_window_row *r;
    unsigned bit;
    if(bg>=3 || row>=256) return 0;
    r=&d35_window_rows[row];bit=1u<<bg;
    if(!r->valid || !(r->targets&bit)) return 0;
    memset(clip,0,sizeof(*clip));
    if(!((sub?r->sub_mask:r->main_mask)&bit)) { clip->count=1;clip->right[0]=256;return 1; }
    if(!(r->inside&bit)) { clip->count=1;clip->left[0]=r->left;clip->right[0]=r->right+1u;return 1; }
    if(r->left>r->right) { clip->count=1;clip->right[0]=256;return 1; }
    if(r->left) clip->right[clip->count++]=r->left;
    if(r->right<255) { unsigned at=clip->count++;clip->left[at]=r->right+1u;clip->right[at]=256; }
    if(!clip->count) { clip->count=1;clip->left[0]=1; }
    return 1;
}
#undef D35_WCOUNT
#endif
#endif
