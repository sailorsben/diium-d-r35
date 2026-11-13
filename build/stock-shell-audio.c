#define _GNU_SOURCE
#include "stock-shell-audio.h"
#include "snes-mvp/audio-pipe.h"
#include "snes-mvp/native-pcm.h"
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>

enum { PRIME_FRAMES = 6615, TRACE_TICKS = 16384 };

static struct {
    char path[512];
    uint64_t opened, admitted, began, generated, ticks, pictures[4];
    unsigned max_display_ns;
    int active, error;
    struct timing {
        uint64_t ns, observed_ns, generated, accepted;
        unsigned admit_ns, run_ns, display_ns, queued, pending, appl, hw, state;
        enum d35_presentation picture;
    } trace[TRACE_TICKS];
} live;

uint64_t board_now_ns(void)
{
    struct timespec ts;
    if(syscall(SYS_clock_gettime,CLOCK_MONOTONIC,&ts)<0) return 0;
    return (uint64_t)ts.tv_sec*1000000000u+ts.tv_nsec;
}

int board_audio_observe(struct board_audio_state *s) { return pcm_observe(s); }
ssize_t board_audio_write(const int16_t *p,size_t n) { return pcm_write(p,n); }
int board_audio_fd(void) { return pcm_fd(); }
int board_audio_avail_min(unsigned n) { return pcm_avail_min(n); }
int board_audio_finish(void) { return pcm_finish(); }
const char *board_audio_error(void) { return pcm_error(); }

static int durable_close(FILE *file)
{
    int failed=ferror(file) || fflush(file)<0 || fsync(fileno(file))<0;
    return fclose(file)<0 || failed ? -1 : 0;
}

static int report(const char *reason,const struct audio_pipe_stats *pcm)
{
    FILE *file=fopen(live.path,"a");
    if(!file) return -1;
    const uint64_t first=live.ticks>TRACE_TICKS ? live.ticks-TRACE_TICKS : 0;
    fprintf(file,"end=%s\nerror=%d\npcm_error=%s\nrate_hz=%u\nperiod_frames=%u\n"
        "buffer_frames=%u\nprime_frames=%u\nprime_accepted=%u\nstart_calls=%u\n"
        "ticks=%llu\nretained_from=%llu\ngenerated_frames=%llu\nenqueued_including_prime=%llu\n"
        "accepted_including_prime=%llu\nsoftware_pending_frames=%u\n"
        "xruns=%llu\npointer_mismatches=%llu\npcm_observations=%llu\nmin_playable_frames=%u\n"
        "max_write_gap_ns=%llu\naudio_worker_cpu_ns=%llu\n"
        "duration_ns=%llu\ndrain_completed=%u\n"
        "presented=%llu\nrepeated=%llu\nbusy_display=%llu\nno_picture=%llu\nmax_display_ns=%u\n",
        reason,live.error,pcm->error_detail[0]?pcm->error_detail:pcm_error(),
        pcm->rate,pcm->period,pcm->buffer,pcm->prime,pcm->prime_transferred,pcm->start_calls,
        (unsigned long long)live.ticks,(unsigned long long)first,(unsigned long long)live.generated,
        (unsigned long long)pcm->enqueued,(unsigned long long)pcm->accepted,pcm->remaining,
        (unsigned long long)pcm->xruns,(unsigned long long)pcm->pointer_mismatches,
        (unsigned long long)pcm->observations,pcm->playable_min,
        (unsigned long long)pcm->max_write_gap_ns,(unsigned long long)pcm->worker_cpu_ns,
        (unsigned long long)(board_now_ns()-live.opened),(unsigned)(!live.error && pcm->state==1),
        (unsigned long long)live.pictures[D35_SUBMITTED_PICTURE],
        (unsigned long long)live.pictures[D35_REPEATED_PICTURE],
        (unsigned long long)live.pictures[D35_BUSY_DISPLAY],
        (unsigned long long)live.pictures[D35_NO_PICTURE],live.max_display_ns);
    fputs("tick,monotonic_ns,observation_ns,admit_ns,run_ns,display_ns,presentation,"
          "generated,accepted_with_prime,playable,software_pending,appl_ptr,hw_ptr,state\n",file);
    for(uint64_t i=first;i<live.ticks;++i) {
        const struct timing *t=&live.trace[i%TRACE_TICKS];
        fprintf(file,"%llu,%llu,%llu,%u,%u,%u,%u,%llu,%llu,%u,%u,%u,%u,%u\n",
            (unsigned long long)(i+1),(unsigned long long)t->ns,(unsigned long long)t->observed_ns,
            t->admit_ns,t->run_ns,t->display_ns,t->picture,(unsigned long long)t->generated,
            (unsigned long long)t->accepted,t->queued,t->pending,t->appl,t->hw,t->state);
    }
    return durable_close(file);
}

static int stop(const char *reason)
{
    if(!live.active) return live.error?-1:0;
    audio_pipe_stop(!live.error);
    struct audio_pipe_stats pcm;
    audio_pipe_stats(&pcm);
    if(!live.error) live.error=pcm.error;
    int result=report(reason,&pcm);
    pcm_close();
    live.active=0;
    return result<0 || live.error ? -1 : 0;
}

static int start(const char *directory)
{
    if(live.active) return 0;
    live.error=live.max_display_ns=0;
    live.generated=live.ticks=0;
    memset(live.pictures,0,sizeof(live.pictures));
    live.opened=board_now_ns();
    if(snprintf(live.path,sizeof(live.path),"%s/starfox-audio-%ld-%llu.log",directory,
                (long)getpid(),(unsigned long long)live.opened)>=(int)sizeof(live.path)) return -1;
    FILE *file=fopen(live.path,"wx");
    if(!file) return -1;
    fprintf(file,"test=starfox_native_150\nclock=kernel_monotonic\nopen_ns=%llu\n"
        "presentation=0:no_picture,1:repeat,2:submit,3:busy\n",(unsigned long long)live.opened);
    if(durable_close(file)<0) return -1;
    int fd=open(directory,O_RDONLY|O_DIRECTORY|O_CLOEXEC);
    if(fd<0) return -1;
    int synced=fsync(fd);
    close(fd);
    if(synced<0) return -1;

    audio_pipe_init();
    live.active=1;
    static const int16_t silence[PRIME_FRAMES*2];
    if(pcm_open_150()!=44100 || audio_pipe_start()<0 ||
       audio_pipe_push(silence,PRIME_FRAMES)<0 || audio_pipe_primed()<0) {
        live.error=errno?errno:EIO;
        (void)stop("start_failed");
        return -1;
    }
    return 0;
}

static int admit(void)
{
    live.began=board_now_ns();
    if(audio_pipe_admit(2048,1)<0) { live.error=errno; return -1; }
    live.admitted=board_now_ns();
    return 0;
}

static int push(const int16_t *samples,size_t frames)
{
    live.generated+=frames;
    if(audio_pipe_push(samples,frames)<0) { live.error=errno; return -1; }
    return 0;
}

static unsigned elapsed(uint64_t end,uint64_t start)
{ return end-start>UINT_MAX ? UINT_MAX : (unsigned)(end-start); }

static int tick(enum d35_presentation picture,unsigned display_ns)
{
    uint64_t now=board_now_ns();
    struct audio_pipe_stats pcm;
    audio_pipe_stats(&pcm);
    if(pcm.error) live.error=pcm.error;
    struct timing *t=&live.trace[live.ticks++%TRACE_TICKS];
    *t=(struct timing){now,pcm.observed_ns,live.generated,pcm.accepted,
        elapsed(live.admitted,live.began),elapsed(now,live.admitted),display_ns,
        pcm.playable,pcm.remaining,pcm.appl_ptr,pcm.hw_ptr,pcm.state,picture};
    ++live.pictures[picture];
    if(display_ns>live.max_display_ns) live.max_display_ns=display_ns;
    return live.error?-1:0;
}

__attribute__((visibility("default"))) const struct d35_live_audio d35_starfox_audio={
    board_now_ns,start,admit,push,tick,stop
};
