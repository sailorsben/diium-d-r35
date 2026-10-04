#ifndef D35_MVP_BOARD_H
#define D35_MVP_BOARD_H
#include <stddef.h>
#include <stdint.h>
#include <sys/types.h>

/* Low 16 bits use RETRO_DEVICE_ID_JOYPAD_* bit positions. */
#define BOARD_MENU (1u << 16)
int board_open(int null_backend);
void board_close(void);
int board_is_null(void);
const char *board_last_error(void);
int board_video_submit(const void *rgb565, unsigned width, unsigned height, size_t pitch);
void board_wait_display(void);
uint32_t board_poll_input(void);
void board_set_input_trace(int enabled);
/* Stereo signed 16-bit little endian. Open returns the accepted rate or -1. */
int board_audio_open(unsigned requested_rate);
ssize_t board_audio_write(const int16_t *samples, size_t frames);
int board_audio_queued_frames(void);
int board_audio_reset(void);
void board_audio_close(void);
uint64_t board_now_ns(void);
void board_sleep_until(uint64_t deadline_ns);
#endif
