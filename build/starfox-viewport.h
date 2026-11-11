#ifndef D35_STARFOX_VIEWPORT_H
#define D35_STARFOX_VIEWPORT_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#ifdef __ARM_NEON
#include <arm_neon.h>
#endif

enum {
    D35_STARFOX_WIDTH = 256, D35_STARFOX_HEIGHT = 224,
    D35_STARFOX_LEFT = 16, D35_STARFOX_TOP = 16,
    D35_STARFOX_VIEW_WIDTH = 226, D35_STARFOX_VIEW_HEIGHT = 190,
    D35_STARFOX_FRAME_BYTES = D35_STARFOX_WIDTH * D35_STARFOX_HEIGHT * 2u
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

/* Keep the scaler on its validated 256x224 RGB565 input. Center sampling
 * retains every source pixel when expanding the packed viewport. */
static inline void d35_starfox_expand(uint16_t *output, const uint16_t *view)
{
#ifdef __ARM_NEON
    struct {
        unsigned first;
        uint8x16_t indices;
    } spans[D35_STARFOX_WIDTH / 8u];
    for (unsigned i = 0; i < D35_STARFOX_WIDTH / 8u; ++i) {
        unsigned x = i * 8u;
        unsigned first = (2u * x + 1u) * D35_STARFOX_VIEW_WIDTH / (2u * D35_STARFOX_WIDTH);
        if (first > D35_STARFOX_VIEW_WIDTH - 8u) first = D35_STARFOX_VIEW_WIDTH - 8u;
        uint8_t bytes[16];
        for (unsigned j = 0; j < 8; ++j) {
            unsigned source = (2u * (x + j) + 1u) * D35_STARFOX_VIEW_WIDTH / (2u * D35_STARFOX_WIDTH);
            bytes[2u * j] = 2u * (source - first);
            bytes[2u * j + 1u] = bytes[2u * j] + 1u;
        }
        spans[i].first = first;
        spans[i].indices = vld1q_u8(bytes);
    }
#else
    uint8_t columns[D35_STARFOX_WIDTH];
    for (unsigned x = 0; x < D35_STARFOX_WIDTH; ++x)
        columns[x] = (2u * x + 1u) * D35_STARFOX_VIEW_WIDTH / (2u * D35_STARFOX_WIDTH);
#endif
    unsigned previous = D35_STARFOX_VIEW_HEIGHT;
    for (unsigned y = 0; y < D35_STARFOX_HEIGHT; ++y) {
        unsigned row = (2u * y + 1u) * D35_STARFOX_VIEW_HEIGHT / (2u * D35_STARFOX_HEIGHT);
        if (row == previous) {
            memcpy(output, output - D35_STARFOX_WIDTH, D35_STARFOX_WIDTH * sizeof(*output));
        } else {
            const uint16_t *source = view + row * D35_STARFOX_VIEW_WIDTH;
#ifdef __ARM_NEON
            for (unsigned i = 0; i < D35_STARFOX_WIDTH / 8u; ++i) {
                uint8x16_t pixels = vld1q_u8((const uint8_t *)(source + spans[i].first));
                uint8x8x2_t table = {{vget_low_u8(pixels), vget_high_u8(pixels)}};
                uint8x16_t indices = spans[i].indices;
                uint8x8_t left = vtbl2_u8(table, vget_low_u8(indices));
                uint8x8_t right = vtbl2_u8(table, vget_high_u8(indices));
                vst1q_u8((uint8_t *)(output + i * 8u), vcombine_u8(left, right));
            }
#else
            for (unsigned x = 0; x < D35_STARFOX_WIDTH; ++x)
                output[x] = source[columns[x]];
#endif
        }
        previous = row;
        output += D35_STARFOX_WIDTH;
    }
}
#endif
