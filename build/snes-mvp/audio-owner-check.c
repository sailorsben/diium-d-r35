#define _GNU_SOURCE
#include "audio-owner.c"
#include <assert.h>
#include <stdio.h>
static pthread_mutex_t device_lock=PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t device_condition=PTHREAD_COND_INITIALIZER;
static unsigned queued,minimum,blocked,started,draining,done,fault,stop_consumer,false_ready;
static int ready_fd;
static int16_t expected[4096*2];
static unsigned accepted,attempts;
uint64_t board_now_ns(void)
{ struct timespec t; assert(!syscall(SYS_clock_gettime,CLOCK_MONOTONIC,&t)); return (uint64_t)t.tv_sec*1000000000u+t.tv_nsec; }
static void readiness(void)
{
    uint64_t value; ssize_t rc;
    if(256-queued>=minimum && blocked) {
        rc=read(ready_fd,&value,sizeof(value)); assert(rc==(ssize_t)sizeof(value)); blocked=0;
    }
}
int board_audio_observe(struct board_audio_state *out)
{
    unsigned failed;
    pthread_mutex_lock(&device_lock);
    memset(out,0,sizeof(*out)); out->rate=1000; out->period=5; out->buffer=256; out->prime=64;
    out->queued=queued; out->started=started; out->observed_ns=board_now_ns();
    out->state=fault?4:started?3:2;
    failed=fault;
    pthread_mutex_unlock(&device_lock);
    if(failed) { errno=EPIPE; return -1; } return 0;
}
int board_audio_fd(void) { return ready_fd; }
int board_audio_avail_min(unsigned frames)
{
    uint64_t value; ssize_t rc;
    pthread_mutex_lock(&device_lock); minimum=frames;
    if(blocked) { rc=read(ready_fd,&value,sizeof(value)); assert(rc==(ssize_t)sizeof(value)); blocked=0; }
    if(256-queued<minimum) {
        value=UINT64_MAX-1; rc=write(ready_fd,&value,sizeof(value));
        assert(rc==(ssize_t)sizeof(value)); blocked=1;
    }
    pthread_mutex_unlock(&device_lock); return 0;
}
ssize_t board_audio_write(const int16_t *data,size_t frames)
{
    unsigned n=(unsigned)frames;
    pthread_mutex_lock(&device_lock);
    ++attempts;
    if(false_ready || !(attempts%7) || ! (256-queued)) { pthread_mutex_unlock(&device_lock); errno=EAGAIN; return -1; }
    if(n>13) n=13;
    if(n>256-queued) n=256-queued;
    assert(accepted+n<=4096 && !memcmp(data,expected+accepted*2,n*4));
    accepted+=n; queued+=n; if(queued>=64) started=1;
    pthread_mutex_unlock(&device_lock); return n;
}
int board_audio_finish(void)
{
    pthread_mutex_lock(&device_lock); draining=1;
    while(queued) pthread_cond_wait(&device_condition,&device_lock);
    started=0; done=1; pthread_mutex_unlock(&device_lock); return 0;
}
static void *consume(void *unused)
{
    (void)unused;
    for(;;) {
        usleep(5000);
        pthread_mutex_lock(&device_lock);
        if(stop_consumer) { pthread_mutex_unlock(&device_lock); break; }
        if(started && !done) {
            if(queued>=5) queued-=5;
            else if(draining) queued=0;
            else { fault=1; queued=0; }
        }
        readiness(); pthread_cond_broadcast(&device_condition);
        pthread_mutex_unlock(&device_lock);
    }
    return NULL;
}
static void setup(void)
{
    queued=minimum=blocked=started=draining=done=fault=stop_consumer=accepted=attempts=false_ready=0;
    ready_fd=eventfd(0,EFD_NONBLOCK|EFD_CLOEXEC); assert(ready_fd>=0);
    audio_pipe_init();
}
int main(void)
{
    unsigned i; pthread_t consumer; struct audio_pipe_stats stats; uint64_t began;
    memset(expected,0,64*4);
    for(i=64*2;i<(64+96*16)*2;i++) expected[i]=(int16_t)(i*97+13);
    setup(); assert(!pthread_create(&consumer,NULL,consume,NULL));
    assert(!audio_pipe_start() && !audio_pipe_push(expected,64) && !audio_pipe_primed());
    for(i=0;i<96;i++) {
        assert(!audio_pipe_admit(16,1));
        usleep(i%10?1000:30000);
        assert(!audio_pipe_push(expected+(64+i*16)*2,16));
    }
    audio_pipe_stop(1); audio_pipe_stats(&stats);
    assert(!stats.error && !stats.xruns && !stats.remaining && stats.accepted==64+96*16);
    assert(accepted==stats.enqueued && stats.partial && stats.again && stats.wakes && done);
    assert(stats.playable==0);
    pthread_mutex_lock(&device_lock); stop_consumer=1; pthread_mutex_unlock(&device_lock);
    pthread_join(consumer,NULL); close(ready_fd);
    setup(); queued=256; started=1;
    assert(!audio_pipe_start() && !audio_pipe_push(expected,16));
    usleep(20000); began=board_now_ns(); audio_pipe_stop(0);
    assert(board_now_ns()-began<200000000u);
    audio_pipe_clear(); audio_pipe_stats(&stats);
    assert(stats.cleared==16 && !stats.remaining); close(ready_fd);
    setup(); assert(!audio_pipe_start());
    pthread_mutex_lock(&device_lock); fault=1; pthread_mutex_unlock(&device_lock);
    if(audio_pipe_push(expected,16)<0) assert(errno==EPIPE);
    audio_pipe_stop(1); audio_pipe_stats(&stats);
    assert(stats.error==EPIPE && stats.xruns==1 && !stats.accepted); close(ready_fd);
    setup(); false_ready=1;
    assert(!audio_pipe_start() && !audio_pipe_push(expected,16)); audio_pipe_stop(1);
    audio_pipe_stats(&stats); assert(stats.error==EPROTO && stats.writes<=34 && !stats.accepted);
    close(ready_fd);
    setup(); queued=256; started=1; assert(!audio_pipe_start()); began=board_now_ns();
    assert(audio_pipe_admit(16,1)<0 && errno==ETIMEDOUT);
    assert(board_now_ns()-began>=1500000000u && board_now_ns()-began<3500000000u);
    audio_pipe_stop(0); close(ready_fd);
    setup(); queued=256; started=1;
    assert(!audio_pipe_start() && !audio_pipe_push(expected,16)); began=board_now_ns();
    audio_pipe_stop(1); audio_pipe_stats(&stats);
    assert(stats.error==ETIMEDOUT && stats.remaining==16 && !stats.accepted);
    assert(board_now_ns()-began>=1500000000u && board_now_ns()-began<3500000000u);
    close(ready_fd);
    puts("PASS: actual audio owner preserves independent PCM under partial/EAGAIN writes; consumption admission tolerates 30ms bursts; playable priming/drain; event cancellation of blocked device; visible fatal XRUN; bounded false readiness, fixed admission deadline and bounded blocked flush without silent recovery");
    return 0;
}
