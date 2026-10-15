/* Mode1's high BG3 is uniquely above every OBJ/BG depth. Two disjoint
 * priority passes retain transparent holes, original low-BG3 order and all
 * original depth/math/window consumers. Derived state is scoped to one call. */
#ifndef D35_DRAW_ORDER_H
#define D35_DRAW_ORDER_H
#ifdef D35_DRAW_ORDER
extern unsigned d35_bg_priority_filter;
#define D35_PRIORITY_ACCEPT (!d35_bg_priority_filter || GFX.Z2 == d35_bg_priority_filter)
#else
#define D35_PRIORITY_ACCEPT 1
#endif
#endif
