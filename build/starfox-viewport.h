#ifndef D35_STARFOX_VIEWPORT_H
#define D35_STARFOX_VIEWPORT_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

enum {
    D35_STARFOX_WIDTH = 256, D35_STARFOX_HEIGHT = 224,
    D35_STARFOX_LEFT = 16, D35_STARFOX_TOP = 16,
    D35_STARFOX_VIEW_WIDTH = 226, D35_STARFOX_VIEW_HEIGHT = 190
};

/* The source keeps its pitch. The board compares and packs only this view. */
static inline const void *d35_starfox_viewport(const void *pixels, size_t pitch,
                                               unsigned *width, unsigned *height)
{
    if (*width != D35_STARFOX_WIDTH || *height != D35_STARFOX_HEIGHT)
        return pixels;
    *width = D35_STARFOX_VIEW_WIDTH;
    *height = D35_STARFOX_VIEW_HEIGHT;
    return (const uint8_t *)pixels + D35_STARFOX_TOP * pitch + D35_STARFOX_LEFT * 2u;
}

/* Offline oracle check. These are the pixels the viewport removes. */
static inline bool d35_starfox_border_is_black(const void *pixels, size_t pitch)
{
    static const uint8_t black[D35_STARFOX_WIDTH * 2u];
    const size_t left = D35_STARFOX_LEFT * 2u;
    const size_t right = (D35_STARFOX_LEFT + D35_STARFOX_VIEW_WIDTH) * 2u;
    for (unsigned y = 0; y < D35_STARFOX_HEIGHT; ++y) {
        const uint8_t *row = (const uint8_t *)pixels + y * pitch;
        if (y < D35_STARFOX_TOP || y >= D35_STARFOX_TOP + D35_STARFOX_VIEW_HEIGHT) {
            if (memcmp(row, black, sizeof(black))) return false;
        } else if (memcmp(row, black, left) || memcmp(row + right, black, sizeof(black) - right)) {
            return false;
        }
    }
    return true;
}
#endif
