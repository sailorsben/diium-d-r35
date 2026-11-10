#ifndef D35_RGB565_REUSE_H
#define D35_RGB565_REUSE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

/* The retained surface has packed rows and is immutable. Ignore source row
 * padding. A sample mismatch can reject a frame, and a hit requires all bytes. */
static inline bool d35_same_rgb565(const void *source, size_t pitch,
                                   const void *previous, unsigned width, unsigned height)
{
    const uint8_t *src=source, *ref=previous;
    size_t bytes=(size_t)width*2, center=(size_t)(width/2)*2;
    unsigned middle=height/2, bottom=height-1;
    if (memcmp(src+middle*pitch+center, ref+middle*bytes+center, 2) ||
        memcmp(src+bottom*pitch+center, ref+bottom*bytes+center, 2))
        return false;
    if (pitch==bytes)
        return memcmp(src, ref, bytes*height)==0;
    for (unsigned row=0; row<height; ++row)
        if (memcmp(src+row*pitch, ref+row*bytes, bytes))
            return false;
    return true;
}

#endif
