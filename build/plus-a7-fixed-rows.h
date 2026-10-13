/* Capture effective fixed colors at the same raster boundary as LineData.
 * First qualification envelope: Mode1, ordinary width/height, no mosaic.
 * Other modes retain their original $2132 flushes. No game/effect identifiers.
 */
#ifndef D35_FIXED_ROWS_H
#define D35_FIXED_ROWS_H
void d35_fixed_reset(void);
void d35_fixed_capture(unsigned row);
unsigned d35_fixed_defer(void);
void d35_fixed_begin(void);
void d35_fixed_end(void);
extern unsigned d35_fixed_active, d35_fixed_shift;
extern unsigned short d35_fixed_rows[256];
#ifdef D35_FIXED_ROWS_USE
static inline unsigned d35_fixed_at_offset(unsigned offset)
{
    return d35_fixed_active ? d35_fixed_rows[offset >> d35_fixed_shift] : GFX.FixedColour;
}
static inline void d35_fixed_select(unsigned row)
{
    if(d35_fixed_active) GFX.FixedColour=d35_fixed_rows[row];
}
static inline void d35_fixed_select_offset(unsigned offset)
{
    if(d35_fixed_active) GFX.FixedColour=d35_fixed_rows[offset >> d35_fixed_shift];
}
#endif
#ifdef D35_FIXED_ROWS_IMPLEMENTATION
unsigned d35_fixed_active, d35_fixed_shift;
unsigned short d35_fixed_rows[256];
static unsigned d35_fixed_prefix[257],d35_fixed_captured,d35_fixed_ordered;
static unsigned d35_fixed_pending,d35_fixed_saved;
#ifdef D35_EFFECT_COUNTS
extern unsigned long long d35_conf[128];
#define D35_FCOUNT(n) (++d35_conf[n])
#else
#define D35_FCOUNT(n) ((void)0)
#endif
static unsigned d35_fixed_eligible(void)
{
    return PPU.BGMode==1 && !PPU.ForcedBlanking && !(Memory.FillRAM[0x2133]&15u) &&
           PPU.Mosaic<=1 && (GFX.PPL==256 || GFX.PPL==512);
}
void d35_fixed_reset(void)
{
    d35_fixed_active=d35_fixed_pending=d35_fixed_captured=0;
    d35_fixed_ordered=1;d35_fixed_prefix[0]=0;
}
void d35_fixed_capture(unsigned row)
{
    if(row>=256) {d35_fixed_ordered=0;return;}
    d35_fixed_rows[row]=BUILD_PIXEL(IPPU.XB[PPU.FixedColourRed],
                                  IPPU.XB[PPU.FixedColourGreen],IPPU.XB[PPU.FixedColourBlue]);
    if(row==d35_fixed_captured || row+1==d35_fixed_captured) {
        d35_fixed_prefix[row+1]=d35_fixed_prefix[row]+!d35_fixed_eligible();
        if(row==d35_fixed_captured) ++d35_fixed_captured;
    } else d35_fixed_ordered=0;
}
unsigned d35_fixed_defer(void)
{
    unsigned first=IPPU.PreviousLine,last=IPPU.CurrentLine;
    if(!IPPU.RenderThisFrame || !d35_fixed_eligible() || !d35_fixed_ordered ||
       first>last || last>d35_fixed_captured || last>256 ||
       d35_fixed_prefix[first]!=d35_fixed_prefix[last]) return 0;
    if(first<last) d35_fixed_pending=1;
    D35_FCOUNT(110);return 1;
}
void d35_fixed_begin(void)
{
    d35_fixed_saved=GFX.FixedColour;
    d35_fixed_active=d35_fixed_pending;
    d35_fixed_shift=GFX.PPL==256?8:9;
    if(d35_fixed_active) D35_FCOUNT(111);
}
void d35_fixed_end(void)
{
    if(d35_fixed_active) GFX.FixedColour=d35_fixed_saved;
    d35_fixed_active=d35_fixed_pending=0;
}
#endif
#endif
