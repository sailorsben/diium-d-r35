#ifndef D35_NATIVE_PCM_H
#define D35_NATIVE_PCM_H
#include "board.h"
int pcm_open(unsigned requested);
ssize_t pcm_write(const int16_t *data,size_t frames);
int pcm_observe(struct board_audio_state *out);
int pcm_avail_min(unsigned frames);
int pcm_reset(void);
int pcm_finish(void);
int pcm_fd(void);
void pcm_close(void);
const char *pcm_error(void);
#endif
