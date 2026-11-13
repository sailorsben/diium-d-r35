#ifndef D35_STOCK_SHELL_AUDIO_H
#define D35_STOCK_SHELL_AUDIO_H

#include <stddef.h>
#include <stdint.h>

enum d35_presentation {
    D35_NO_PICTURE,
    D35_REPEATED_PICTURE,
    D35_SUBMITTED_PICTURE,
    D35_BUSY_DISPLAY
};

struct d35_live_audio {
    uint64_t (*now)(void);
    int (*start)(const char *directory);
    int (*admit)(void);
    int (*push)(const int16_t *samples, size_t frames);
    int (*tick)(enum d35_presentation presentation, unsigned display_ns);
    int (*stop)(const char *reason);
};

#endif
