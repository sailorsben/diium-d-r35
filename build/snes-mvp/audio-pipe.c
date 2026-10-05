#define _GNU_SOURCE
#include "audio-pipe.h"
#include "board.h"
#include <errno.h>
#include <pthread.h>
#include <string.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
#define AUDIO_CAPACITY 8192u
static struct {
    int16_t pcm[AUDIO_CAPACITY*2];
    unsigned read,count;
    int started,stop;
    pthread_t thread;
    struct audio_pipe_stats stats;
} pipe_state;
static pthread_mutex_t pipe_lock=PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t pipe_condition=PTHREAD_COND_INITIALIZER;

static uint64_t audio_cpu(void)
{
    struct timespec t;
    if(syscall(SYS_clock_gettime,CLOCK_THREAD_CPUTIME_ID,&t)) return 0;
    return (uint64_t)t.tv_sec*1000000000u+t.tv_nsec;
}
static void *audio_service(void *unused)
{
    uint64_t began=audio_cpu(),last_write=0,end;
    (void)unused;
    pthread_mutex_lock(&pipe_lock);
    for(;;) {
        unsigned count,read;
        ssize_t accepted;
        int error;
        while(!pipe_state.count && !pipe_state.stop)
            pthread_cond_wait(&pipe_condition,&pipe_lock);
        if(pipe_state.stop || pipe_state.stats.error) break;
        count=pipe_state.count; read=pipe_state.read;
        if(count>AUDIO_CAPACITY-read) count=AUDIO_CAPACITY-read;
        /* Count includes the in-flight block until write returns, so producer
         * cannot overwrite it. No mutex is held over kernel I/O or poll. */
        pthread_mutex_unlock(&pipe_lock);
        accepted=board_audio_write(pipe_state.pcm+read*2,count); error=errno;
        pthread_mutex_lock(&pipe_lock);
        ++pipe_state.stats.writes;
        if(accepted>0 && (size_t)accepted<=count) {
            uint64_t now=board_now_ns();
            if(last_write && now-last_write>pipe_state.stats.max_write_gap_ns)
                pipe_state.stats.max_write_gap_ns=now-last_write;
            last_write=now;
            if((unsigned)accepted<count) ++pipe_state.stats.partial;
            pipe_state.read=(read+(unsigned)accepted)%AUDIO_CAPACITY;
            pipe_state.count-=(unsigned)accepted;
            pipe_state.stats.accepted+=(unsigned)accepted;
            pthread_cond_broadcast(&pipe_condition);
            continue;
        }
        if(accepted==0 || (accepted<0 && (error==EAGAIN || error==EWOULDBLOCK || error==EINTR))) {
            ++pipe_state.stats.again;
            pthread_mutex_unlock(&pipe_lock);
            /* Some OSS poll implementations report writable before a full
             * fragment is accepted. Minimum backoff prevents a busy loop. */
            {
                uint64_t start=board_now_ns();
                int ready=board_audio_wait(4);
                if(ready<0) error=errno;
                else if(board_now_ns()-start<1000000u)
                    board_sleep_until(start+1000000u);
                pthread_mutex_lock(&pipe_lock);
                if(ready>=0) continue;
            }
        }
        pipe_state.stats.error=error?error:EIO; ++pipe_state.stats.errors;
        break;
    }
    end=audio_cpu();
    if(end>=began) pipe_state.stats.worker_cpu_ns+=end-began;
    pthread_mutex_unlock(&pipe_lock);
    return NULL;
}
void audio_pipe_init(void)
{
    /* Caller has joined the previous session; all state is preallocated. */
    memset(&pipe_state,0,sizeof(pipe_state));
}
int audio_pipe_start(void)
{
    int rc;
    if(pipe_state.started) return 0;
    pipe_state.stop=0;
    rc=pthread_create(&pipe_state.thread,NULL,audio_service,NULL);
    if(rc) { errno=rc; return -1; }
    pipe_state.started=1;
    return 0;
}
int audio_pipe_space(unsigned frames)
{
    uint64_t began=board_now_ns();
    if(frames>AUDIO_CAPACITY) { errno=EINVAL; return -1; }
    for(;;) {
        unsigned count; int error;
        pthread_mutex_lock(&pipe_lock);
        count=pipe_state.count; error=pipe_state.stats.error;
        pthread_mutex_unlock(&pipe_lock);
        if(error) { errno=error; return -1; }
        if(count<=AUDIO_CAPACITY-frames) return 0;
        if(board_now_ns()-began>500000000u) { errno=ETIMEDOUT; return -1; }
        board_sleep_until(board_now_ns()+1000000u);
    }
}
int audio_pipe_push(const int16_t *pcm,size_t frames)
{
    unsigned write,first;
    pthread_mutex_lock(&pipe_lock);
    if(pipe_state.stats.error || frames>AUDIO_CAPACITY-pipe_state.count) {
        errno=pipe_state.stats.error?pipe_state.stats.error:ENOBUFS;
        pthread_mutex_unlock(&pipe_lock); return -1;
    }
    write=(pipe_state.read+pipe_state.count)%AUDIO_CAPACITY;
    first=AUDIO_CAPACITY-write; if(first>frames) first=(unsigned)frames;
    memcpy(pipe_state.pcm+write*2,pcm,first*4);
    if(frames>first) memcpy(pipe_state.pcm,pcm+first*2,(frames-first)*4);
    pipe_state.count+=(unsigned)frames; pipe_state.stats.enqueued+=frames;
    if(pipe_state.count>pipe_state.stats.high) pipe_state.stats.high=pipe_state.count;
    pthread_cond_signal(&pipe_condition);
    pthread_mutex_unlock(&pipe_lock);
    return 0;
}
void audio_pipe_stop(int drain)
{
    int error=0;
    if(!pipe_state.started) return;
    if(drain && audio_pipe_space(AUDIO_CAPACITY)<0) error=errno;
    pthread_mutex_lock(&pipe_lock); pipe_state.stop=1;
    if(error && !pipe_state.stats.error) { pipe_state.stats.error=error; ++pipe_state.stats.errors; }
    pthread_cond_broadcast(&pipe_condition); pthread_mutex_unlock(&pipe_lock);
    pthread_join(pipe_state.thread,NULL); pipe_state.started=0;
}
void audio_pipe_clear(void)
{
    /* Stop/join is the reset acknowledgment: old PCM cannot escape afterward. */
    audio_pipe_stop(0);
    pthread_mutex_lock(&pipe_lock);
    pipe_state.stats.cleared+=pipe_state.count;
    pipe_state.read=pipe_state.count=0;
    pthread_mutex_unlock(&pipe_lock);
}
void audio_pipe_stats(struct audio_pipe_stats *out)
{
    pthread_mutex_lock(&pipe_lock); *out=pipe_state.stats;
    out->remaining=pipe_state.count; pthread_mutex_unlock(&pipe_lock);
}
