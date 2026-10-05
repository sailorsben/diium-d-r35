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
int board_video_reserve(void);
void board_video_cancel(void);
struct board_video_metrics {
    uint64_t submitted, scaled, flipped, reserve_wait_ns, copy_ns;
    uint64_t scale_ns, flip_ns, worker_cpu_ns, max_scale_ns, max_flip_ns;
    unsigned queue_high;
};
void board_video_metrics(struct board_video_metrics *out, int reset);
void board_wait_display(void);
uint32_t board_poll_input(void);
void board_set_input_trace(int enabled);
/* Stereo signed 16-bit little endian. Open returns the accepted rate or -1. */
int board_audio_open(unsigned requested_rate);
ssize_t board_audio_write(const int16_t *samples, size_t frames);
int board_audio_queued_frames(void);
int board_audio_reset(void);
int board_audio_wait(unsigned milliseconds);
void board_audio_close(void);
struct board_audio_state {
    unsigned rate,period,buffer,prime,queued,state;
    unsigned avail,appl_ptr,hw_ptr,start_threshold,prime_transferred,start_calls,start_races;
    uint64_t observed_ns;
    int started;
};
int board_audio_observe(struct board_audio_state *out);
int board_audio_avail_min(unsigned frames);
int board_audio_fd(void);
int board_audio_finish(void);
const char *board_audio_error(void);
uint64_t board_now_ns(void);
void board_sleep_until(uint64_t deadline_ns);
#endif
