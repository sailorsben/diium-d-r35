#ifndef SNES_MVP_UI_H
#define SNES_MVP_UI_H

#include <stddef.h>
#include <stdint.h>

#define UI_WIDTH 640u
#define UI_HEIGHT 480u
#define UI_LIBRARY_ROWS 9u
#define UI_PAUSE_COUNT 4u

enum ui_pause_action {
    UI_PAUSE_RESUME = 0,
    UI_PAUSE_SAVE = 1,
    UI_PAUSE_LOAD = 2,
    UI_PAUSE_EXIT = 3
};

/* Pixels are native-endian RGB565. Pitch is in uint16_t pixels, not bytes.
 * The caller owns at least pitch_pixels * UI_HEIGHT pixels and all input text.
 * Rendering neither allocates memory nor talks to hardware. */
void ui_draw_library(uint16_t *pixels, unsigned pitch_pixels,
                     const char *const *names, size_t count, size_t selected,
                     const char *status);
void ui_draw_pause(uint16_t *pixels, unsigned pitch_pixels,
                   const char *game_name, unsigned selected, const char *status);
void ui_draw_notice(uint16_t *pixels, unsigned pitch_pixels,
                    const char *title, const char *message);

#endif
