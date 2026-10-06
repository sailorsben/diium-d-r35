/* Raster invalidation follows rendered color, not the last write's channel
 * selector. Preserve the pinned register update and byte latch separately. */
#ifndef D35_PLUS_A7_RASTER_H
#define D35_PLUS_A7_RASTER_H
static inline unsigned d35_fixed_color_changes(unsigned byte,unsigned red,
                                               unsigned green,unsigned blue)
{
    unsigned value=byte&31u;
    return ((byte&32u) && red!=value) || ((byte&64u) && green!=value) ||
           ((byte&128u) && blue!=value);
}
#endif
