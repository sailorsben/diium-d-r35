#ifndef D35_AUDIO_PIPE_H
#define D35_AUDIO_PIPE_H
#include <stdint.h>
#include <stddef.h>
struct audio_pipe_stats {
    uint64_t enqueued, accepted, cleared, writes, partial, again, errors;
    uint64_t worker_cpu_ns, max_write_gap_ns;
    unsigned remaining, high;
    int error;
};
void audio_pipe_init(void);
int audio_pipe_start(void);
int audio_pipe_space(unsigned frames);
int audio_pipe_push(const int16_t *pcm,size_t frames);
void audio_pipe_stop(int drain);
void audio_pipe_clear(void);
void audio_pipe_stats(struct audio_pipe_stats *out);
#endif
