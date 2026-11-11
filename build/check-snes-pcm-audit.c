/* Model the vendor PREPARE overwriting all three runtime settings. Exercise
 * the actual ARM userspace PCM implementation with short transfers. */
#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sound/asound.h>
#include "board.h"

static unsigned prime, period, ring, accepted, start_threshold, boundary;
static unsigned silence_threshold, silence_size, prepares, starts, transfers;
static int state;
static int16_t payload[24576 * 2];

static int fixture_open(const char *name, int flags, ...)
{
    assert(!strcmp(name, "/dev/snd/pcmC0D0p") && (flags & O_NONBLOCK));
    return 43;
}

static int fixture_close(int fd)
{
    assert(fd == 43);
    return 0;
}

static int fixture_ioctl(int fd, unsigned long cmd, ...)
{
    assert(fd == 43);
    if (cmd == SNDRV_PCM_IOCTL_PREPARE) {
        state = SNDRV_PCM_STATE_PREPARED;
        start_threshold = silence_threshold = silence_size = 2 * period;
        accepted = 0;
        ++prepares;
        return 0;
    }
    if (cmd == SNDRV_PCM_IOCTL_START) {
        assert(state == SNDRV_PCM_STATE_PREPARED && accepted == prime);
        assert(start_threshold == boundary && !silence_threshold && !silence_size);
        state = SNDRV_PCM_STATE_RUNNING;
        ++starts;
        return 0;
    }
    if (cmd == SNDRV_PCM_IOCTL_DROP || cmd == SNDRV_PCM_IOCTL_HW_FREE) {
        state = SNDRV_PCM_STATE_SETUP;
        return 0;
    }
    va_list ap;
    va_start(ap, cmd);
    void *arg = va_arg(ap, void *);
    va_end(ap);
    if (cmd == SNDRV_PCM_IOCTL_PVERSION) {
        *(int *)arg = SNDRV_PROTOCOL_VERSION(2, 0, 14);
    } else if (cmd == SNDRV_PCM_IOCTL_INFO) {
        memset(arg, 0, sizeof(struct snd_pcm_info));
    } else if (cmd == SNDRV_PCM_IOCTL_HW_REFINE || cmd == SNDRV_PCM_IOCTL_HW_PARAMS) {
        struct snd_pcm_hw_params *p = arg;
        unsigned rate = p->intervals[SNDRV_PCM_HW_PARAM_RATE - SNDRV_PCM_HW_PARAM_FIRST_INTERVAL].min;
        unsigned step = p->intervals[SNDRV_PCM_HW_PARAM_PERIOD_SIZE - SNDRV_PCM_HW_PARAM_FIRST_INTERVAL].min;
        unsigned frames = p->intervals[SNDRV_PCM_HW_PARAM_BUFFER_SIZE - SNDRV_PCM_HW_PARAM_FIRST_INTERVAL].min;
        if (rate != 44100 || step != period || frames != ring) {
            errno = EINVAL;
            return -1;
        }
    } else if (cmd == SNDRV_PCM_IOCTL_SW_PARAMS) {
        struct snd_pcm_sw_params *sw = arg;
        assert(state == SNDRV_PCM_STATE_PREPARED);
        assert(sw->avail_min == period && sw->stop_threshold == ring);
        start_threshold = sw->start_threshold;
        silence_threshold = sw->silence_threshold;
        silence_size = sw->silence_size;
        boundary = sw->boundary;
    } else if (cmd == SNDRV_PCM_IOCTL_SYNC_PTR) {
        struct snd_pcm_sync_ptr *sync = arg;
        assert(sync->flags & SNDRV_PCM_SYNC_PTR_APPL);
        sync->s.status.state = state;
        sync->s.status.hw_ptr = 0;
        sync->c.control.appl_ptr = accepted;
    } else if (cmd == SNDRV_PCM_IOCTL_WRITEI_FRAMES) {
        struct snd_xferi *transfer = arg;
        unsigned n = transfer->frames > 257 ? 257 : transfer->frames;
        assert(accepted + n <= prime && !memcmp(transfer->buf, payload + accepted * 2, n * 4));
        if (++transfers % 7 == 0) {
            errno = EAGAIN;
            return -1;
        }
        accepted += n;
        if (accepted >= start_threshold) state = SNDRV_PCM_STATE_RUNNING;
        transfer->result = n;
    } else {
        assert(!"unexpected PCM ioctl");
    }
    return 0;
}

#define open fixture_open
#define close fixture_close
#define ioctl fixture_ioctl
#include "native-pcm.c"
#undef open
#undef close
#undef ioctl

uint64_t board_now_ns(void)
{
    static uint64_t clock;
    return clock += 10000;
}

static void write_prime(void)
{
    for (unsigned written = 0; written < prime;) {
        ssize_t n = pcm_write(payload + written * 2, prime - written);
        if (n < 0) assert(errno == EAGAIN);
        else written += (unsigned)n;
        assert(state == (written == prime ? SNDRV_PCM_STATE_RUNNING : SNDRV_PCM_STATE_PREPARED));
    }
    struct board_audio_state actual;
    assert(!pcm_observe(&actual) && actual.started && actual.queued == prime && actual.start_calls == 1);
}

int main(void)
{
    for (unsigned i = 0; i < sizeof(payload) / sizeof(payload[0]); ++i) payload[i] = (int16_t)(i * 97u + 13u);
    assert(!unsetenv("D35_PCM_DIAGNOSTIC_RESERVE"));
    prime = 2823;
    period = 128;
    ring = 3712;
    assert(pcm_open(32040) == 44100);
    write_prime();
    pcm_close();

    assert(!setenv("D35_PCM_DIAGNOSTIC_RESERVE", "150", 1));
    prime = 6615;
    period = 128;
    ring = 7552;
    assert(pcm_open(32040) == 44100);
    write_prime();
    pcm_close();

    assert(!setenv("D35_PCM_DIAGNOSTIC_RESERVE", "1", 1));
    prime = 24576;
    period = 512;
    ring = 25600;
    assert(pcm_open(32040) == 44100);
    write_prime();
    assert(!pcm_reset());
    write_prime();
    assert(prepares == 4 && starts == 4);
    pcm_close();
    puts("PASS exact PCM order across short writes, EAGAIN and reprepare; explicit START at 2823, 6615 and 24576 samples");
    return 0;
}
