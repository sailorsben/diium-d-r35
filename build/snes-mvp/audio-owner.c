#define _GNU_SOURCE
#include "audio-pipe.h"
#include "board.h"
#include <errno.h>
#include <limits.h>
#include <pthread.h>
#include <poll.h>
#include <stdio.h>
#include <string.h>
#include <sys/eventfd.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
#define AUDIO_CAPACITY 8192u
static struct {
    int16_t pcm[AUDIO_CAPACITY*2];
    unsigned read,count;
    int started,stop,drain,running,wake,refresh,admitting;
    pthread_t thread;
    uint64_t cpu_base,drain_deadline;
    struct board_audio_state device;
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
static void notify(void)
{ uint64_t one=1; ssize_t rc;
  if(pipe_state.wake<0) return;
  do { rc=write(pipe_state.wake,&one,sizeof(one)); } while(rc<0 && errno==EINTR);
}
static int condition_deadline(struct timespec *until)
{
    if(syscall(SYS_clock_gettime,CLOCK_REALTIME,until)<0) return -1;
    until->tv_sec+=2; return 0;
}
static int changed(const struct timespec *until)
{
    int rc=pthread_cond_timedwait(&pipe_condition,&pipe_lock,until);
    if(rc) { errno=rc; return -1; } return 0;
}
static void error(int value)
{
    if(!pipe_state.stats.error) {
        pipe_state.stats.error=value?value:EIO; ++pipe_state.stats.errors;
        snprintf(pipe_state.stats.error_detail,sizeof(pipe_state.stats.error_detail),"%s",board_audio_error());
        if(value==EPIPE) ++pipe_state.stats.xruns;
    }
    pthread_cond_broadcast(&pipe_condition);
}
static int observe(void)
{
    struct board_audio_state *d=&pipe_state.device;
    int rc=board_audio_observe(d),saved=errno;
    pipe_state.stats.playable=d->queued; pipe_state.stats.state=d->state;
    pipe_state.stats.avail=d->avail; pipe_state.stats.appl_ptr=d->appl_ptr; pipe_state.stats.hw_ptr=d->hw_ptr;
    pipe_state.stats.start_threshold=d->start_threshold; pipe_state.stats.prime_transferred=d->prime_transferred;
    pipe_state.stats.start_calls=d->start_calls; pipe_state.stats.start_races=d->start_races;
    pipe_state.stats.observed_ns=d->observed_ns;
    if(rc<0) { error(saved); return -1; }
    if(d->started) {
        if(d->queued<pipe_state.stats.playable_min) pipe_state.stats.playable_min=d->queued;
        if(d->queued>pipe_state.stats.playable_max) pipe_state.stats.playable_max=d->queued;
    }
    pthread_cond_broadcast(&pipe_condition); return 0;
}
static void *audio_service(void *unused)
{
    uint64_t began=audio_cpu(),last_write=0;
    unsigned stalled_ready=0;
    (void)unused;
    pthread_mutex_lock(&pipe_lock);
    pipe_state.running=1; pipe_state.cpu_base=began;
    while(!pipe_state.stats.error) {
        int need_pcm=0;
        if(pipe_state.stop && (!pipe_state.drain || !pipe_state.count)) break;
        if(pipe_state.stop && pipe_state.drain && board_now_ns()>=pipe_state.drain_deadline) {
            error(ETIMEDOUT); break;
        }
        if(observe()<0) break;
        pipe_state.refresh=0;
        if(pipe_state.count) {
            unsigned count=pipe_state.count;
            ssize_t accepted;
            if(count>AUDIO_CAPACITY-pipe_state.read) count=AUDIO_CAPACITY-pipe_state.read;
            /* Nonblocking transfer + ring update + observation are one owned
             * transaction. Kernel consumption may advance; another writer may not. */
            accepted=board_audio_write(pipe_state.pcm+pipe_state.read*2,count);
            ++pipe_state.stats.writes;
            if(accepted>0 && (size_t)accepted<=count) {
                uint64_t now=board_now_ns();
                if(last_write && now-last_write>pipe_state.stats.max_write_gap_ns)
                    pipe_state.stats.max_write_gap_ns=now-last_write;
                last_write=now;
                stalled_ready=0;
                if((unsigned)accepted<count) ++pipe_state.stats.partial;
                pipe_state.read=(pipe_state.read+(unsigned)accepted)%AUDIO_CAPACITY;
                pipe_state.count-=(unsigned)accepted;
                pipe_state.stats.accepted+=(unsigned)accepted;
                if(observe()<0) break;
                continue;
            }
            if(accepted<0 && errno!=EAGAIN && errno!=EINTR) { error(errno); break; }
            if(accepted>0) { error(EPROTO); break; }
            ++pipe_state.stats.again; need_pcm=1;
        } else if(pipe_state.admitting && pipe_state.device.queued>pipe_state.device.prime) need_pcm=1;
        if(need_pcm && board_audio_fd()>=0) {
            unsigned minimum=pipe_state.count?pipe_state.device.period:
                pipe_state.device.buffer-pipe_state.device.prime;
            if(board_audio_avail_min(minimum)<0) { error(errno); break; }
        }
        {
            struct pollfd fds[2]={{pipe_state.wake,POLLIN,0},{board_audio_fd(),POLLOUT,0}};
            int rc,device=need_pcm && fds[1].fd>=0;
            pthread_mutex_unlock(&pipe_lock);
            rc=poll(fds,device?2:1,500);
            if(fds[0].revents&POLLIN) {
                uint64_t value; ssize_t got;
                do { got=read(fds[0].fd,&value,sizeof(value)); } while(got<0 && errno==EINTR);
            }
            pthread_mutex_lock(&pipe_lock);
            if(rc<0 && errno!=EINTR) { error(errno); break; }
            if(!rc) ++pipe_state.stats.poll_timeouts;
            else ++pipe_state.stats.wakes;
            if(device && pipe_state.count && (fds[1].revents&POLLOUT) && ++stalled_ready>32) {
                error(EPROTO); break; /* readiness without progress is a fault, not a spin */
            }
            if(fds[0].revents&(POLLERR|POLLHUP|POLLNVAL) ||
               (device && fds[1].revents&(POLLHUP|POLLNVAL))) { error(EIO); break; }
            /* POLLERR is interpreted through PCM state on the next observe. */
        }
    }
    if(pipe_state.drain && !pipe_state.stats.error) {
        if(board_audio_finish()<0) error(errno);
        else { pipe_state.device.queued=0; pipe_state.device.started=0;
               pipe_state.stats.playable=0; pipe_state.stats.state=1; }
    }
    pipe_state.stats.worker_cpu_ns+=audio_cpu()-began;
    pipe_state.running=0; pthread_cond_broadcast(&pipe_condition);
    pthread_mutex_unlock(&pipe_lock); return NULL;
}
void audio_pipe_init(void)
{ memset(&pipe_state,0,sizeof(pipe_state)); pipe_state.wake=-1; pipe_state.stats.playable_min=UINT_MAX; }
unsigned audio_pipe_prime_frames(void)
{ struct board_audio_state d; return board_audio_observe(&d)<0?0:d.prime; }
int audio_pipe_start(void)
{
    int rc;
    if(pipe_state.started) return 0;
    if(board_audio_observe(&pipe_state.device)<0) return -1;
    pipe_state.stats.period=pipe_state.device.period; pipe_state.stats.buffer=pipe_state.device.buffer;
    pipe_state.stats.prime=pipe_state.device.prime; pipe_state.stats.rate=pipe_state.device.rate;
    pipe_state.stop=pipe_state.drain=0;
    pipe_state.wake=eventfd(0,EFD_NONBLOCK|EFD_CLOEXEC);
    if(pipe_state.wake<0) return -1;
    rc=pthread_create(&pipe_state.thread,NULL,audio_service,NULL);
    if(rc) { close(pipe_state.wake); pipe_state.wake=-1; errno=rc; return -1; }
    pipe_state.started=1; return 0;
}
int audio_pipe_admit(unsigned frames,int paced)
{
    int rc=0;
    struct timespec until;
    if(frames>AUDIO_CAPACITY) { errno=EINVAL; return -1; }
    if(condition_deadline(&until)<0) return -1;
    pthread_mutex_lock(&pipe_lock);
    pipe_state.admitting=paced; pipe_state.refresh=1; notify();
    while(!pipe_state.stats.error && !pipe_state.stop && (pipe_state.count>AUDIO_CAPACITY-frames ||
          (paced && pipe_state.count+pipe_state.device.queued>pipe_state.device.prime))) {
        if(changed(&until)<0) { rc=-1; break; }
    }
    if(pipe_state.stats.error) { errno=pipe_state.stats.error; rc=-1; }
    else if(pipe_state.stop) { errno=ECANCELED; rc=-1; }
    pipe_state.admitting=0;
    pthread_mutex_unlock(&pipe_lock); return rc;
}
int audio_pipe_space(unsigned frames) { return audio_pipe_admit(frames,0); }
int audio_pipe_primed(void)
{
    int rc=0;
    struct timespec until;
    if(condition_deadline(&until)<0) return -1;
    pthread_mutex_lock(&pipe_lock);
    while(!pipe_state.stats.error && (pipe_state.count || !pipe_state.device.started)) {
        if(changed(&until)<0) { rc=-1; break; }
    }
    if(pipe_state.stats.error) { errno=pipe_state.stats.error; rc=-1; }
    pthread_mutex_unlock(&pipe_lock); return rc;
}
int audio_pipe_push(const int16_t *data,size_t frames)
{
    unsigned write_at,first;
    pthread_mutex_lock(&pipe_lock);
    if(pipe_state.stats.error || frames>AUDIO_CAPACITY-pipe_state.count) {
        errno=pipe_state.stats.error?pipe_state.stats.error:ENOBUFS;
        pthread_mutex_unlock(&pipe_lock); return -1;
    }
    write_at=(pipe_state.read+pipe_state.count)%AUDIO_CAPACITY;
    first=AUDIO_CAPACITY-write_at; if(first>frames) first=(unsigned)frames;
    memcpy(pipe_state.pcm+write_at*2,data,first*4);
    if(frames>first) memcpy(pipe_state.pcm,data+first*2,(frames-first)*4);
    pipe_state.count+=(unsigned)frames; pipe_state.stats.enqueued+=frames;
    if(pipe_state.count>pipe_state.stats.high) pipe_state.stats.high=pipe_state.count;
    notify(); pthread_mutex_unlock(&pipe_lock); return 0;
}
void audio_pipe_stop(int drain)
{
    if(!pipe_state.started) return;
    pthread_mutex_lock(&pipe_lock); pipe_state.stop=1; pipe_state.drain=drain;
    pipe_state.drain_deadline=board_now_ns()+2000000000u; notify();
    pthread_mutex_unlock(&pipe_lock); pthread_join(pipe_state.thread,NULL);
    close(pipe_state.wake); pipe_state.wake=-1; pipe_state.started=0;
}
void audio_pipe_clear(void)
{
    audio_pipe_stop(0);
    pthread_mutex_lock(&pipe_lock); pipe_state.stats.cleared+=pipe_state.count;
    pipe_state.read=pipe_state.count=0; pthread_mutex_unlock(&pipe_lock);
}
void audio_pipe_stats(struct audio_pipe_stats *out)
{
    pthread_mutex_lock(&pipe_lock); *out=pipe_state.stats;
    out->remaining=pipe_state.count; pthread_mutex_unlock(&pipe_lock);
}
uint64_t audio_pipe_live_cpu(void)
{
    uint64_t result; clockid_t clock; struct timespec now;
    pthread_mutex_lock(&pipe_lock); result=pipe_state.stats.worker_cpu_ns;
    if(pipe_state.running && !pthread_getcpuclockid(pipe_state.thread,&clock) &&
       !syscall(SYS_clock_gettime,clock,&now)) {
        uint64_t value=(uint64_t)now.tv_sec*1000000000u+now.tv_nsec;
        if(value>=pipe_state.cpu_base) result+=value-pipe_state.cpu_base;
    }
    pthread_mutex_unlock(&pipe_lock); return result;
}
