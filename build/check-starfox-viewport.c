/* Exercise the real chunk packing, comparison and worker with padded input. */
#include "board.c"
#include "starfox-viewport.h"
#include <assert.h>

static uint16_t source[224][512];
static unsigned draws, flips;

void startup_note(const char *format, ...)
{
    (void)format;
}

static uint16_t pattern(unsigned x, unsigned y)
{
    return (uint16_t)(y * 257 + x);
}

static void draw(uint16_t *pixels, int width, int height)
{
    assert(width == 226 && height == 190);
    for (unsigned y = 0; y < 190; ++y)
        for (unsigned x = 0; x < 226; ++x) {
            unsigned change = draws == 1 && x == 225 && y == 189;
            assert(pixels[y * 226 + x] == pattern(x + 16, y + 16) + change);
        }
    ++draws;
}

static void flip(void)
{
    assert(draws == ++flips);
}

static int submit(void)
{
    unsigned width = 256, height = 224;
    const void *pixels = d35_starfox_viewport(source, sizeof(source[0]), &width, &height);
    assert(pixels == &source[16][16]);
    return board_video_submit(pixels, width, height, sizeof(source[0]));
}

int main(void)
{
    unsigned width = 512, height = 224;
    assert(d35_starfox_viewport(source, sizeof(source[0]), &width, &height) == source);
    assert(width == 512 && height == 224);
    source[205][241] = source[17][256] = 1;
    assert(d35_starfox_border_is_black(source, sizeof(source[0])));
    source[205][242] = 1;
    assert(!d35_starfox_border_is_black(source, sizeof(source[0])));
    for (unsigned y = 0; y < 224; ++y)
        for (unsigned x = 0; x < 512; ++x)
            source[y][x] = pattern(x, y);

    b.opened = 1;
    b.reserved = b.previous = -1;
    b.draw_vfb = draw;
    b.flip_vfb = flip;
    b.pixels = calloc(SOURCE_SLOTS, SLOT_BYTES);
    assert(b.pixels);
    assert(!pthread_create(&b.worker, NULL, display_worker, NULL));
    b.worker_started = 1;
    board_video_reuse_identical(1);

    assert(submit() == 0);
    ++source[16][15];
    ++source[16][242];
    ++source[15][16];
    ++source[206][16];
    assert(submit() == 1);
    ++source[205][241];
    assert(submit() == 0);
    board_wait_display();

    struct board_video_metrics metrics;
    board_video_metrics(&metrics, 0);
    assert(draws == 2 && flips == 2 && metrics.reused_identical == 1);
    assert(metrics.copied_payload_bytes == 2u * 226u * 190u * 2u);
    pthread_mutex_lock(&display_lock);
    b.stopping = 1;
    pthread_cond_broadcast(&display_condition);
    pthread_mutex_unlock(&display_lock);
    assert(!pthread_join(b.worker, NULL));
    free(b.pixels);
    puts("PASS exact crop packing, boundary pixels, duplicate reuse and worker ownership");
    return 0;
}
