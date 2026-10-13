/* S9xUpdateScreen only consumes fixed color in its color-math branch.
 * Pseudo-hires overrides that branch's registers, so it always falls back. */
#ifndef D35_FIXED_UNUSED_H
#define D35_FIXED_UNUSED_H
static inline unsigned d35_fixed_color_used(unsigned r2130,unsigned r2131,unsigned r2133)
{
    return (r2133&8u) || ((r2131&63u) && (r2130&48u)!=48u);
}
#endif
