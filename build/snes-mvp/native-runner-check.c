/* Real Plus core and runner/owner/native client; independently consuming PCM.
 * This qualifies lifecycle/accounting, not vendor timing or handheld output. */
#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <pthread.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <sys/eventfd.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
#include <sound/asound.h>
#include "board.h"
static pthread_mutex_t kernel_lock=PTHREAD_MUTEX_INITIALIZER;
static unsigned capacity,queued,minimum,threshold,boundary,appl,hw,write_count;
static int device_fd=-1,device_blocked,stream_state,consumer_stop,inject_write;
static uint64_t tick_ns,frame_fraction,device_accepted,device_resets,device_opens;
uint64_t board_now_ns(void)
{ struct timespec t; assert(!syscall(SYS_clock_gettime,CLOCK_MONOTONIC,&t)); return (uint64_t)t.tv_sec*1000000000u+t.tv_nsec; }
static void readiness(void)
{
    uint64_t v; ssize_t rc;
    if(device_fd<0) return;
    if(device_blocked && capacity-queued>=minimum) {
        rc=read(device_fd,&v,sizeof(v)); assert(rc==(ssize_t)sizeof(v)); device_blocked=0;
    } else if(!device_blocked && capacity-queued<minimum) {
        v=UINT64_MAX-1; rc=write(device_fd,&v,sizeof(v)); assert(rc==(ssize_t)sizeof(v)); device_blocked=1;
    }
}
static void consume_at(uint64_t now)
{
    uint64_t count;
    if(stream_state!=SNDRV_PCM_STATE_RUNNING && stream_state!=SNDRV_PCM_STATE_DRAINING) { tick_ns=now; return; }
    frame_fraction+=(now-tick_ns)*44100u; tick_ns=now;
    count=frame_fraction/1000000000u; frame_fraction%=1000000000u;
    if(count>=queued) {
        hw=(hw+queued)%boundary; queued=0;
        stream_state=stream_state==SNDRV_PCM_STATE_DRAINING?SNDRV_PCM_STATE_SETUP:SNDRV_PCM_STATE_XRUN;
    } else { queued-=(unsigned)count; hw=(hw+(unsigned)count)%boundary; }
    readiness();
}
static void *consume_pcm(void *unused)
{
    (void)unused;
    for(;;) {
        usleep(1000); pthread_mutex_lock(&kernel_lock);
        if(consumer_stop) { pthread_mutex_unlock(&kernel_lock); return NULL; }
        if(device_fd>=0) consume_at(board_now_ns());
        pthread_mutex_unlock(&kernel_lock);
    }
}
static int provider_open(const char *name,int flags,...)
{
    assert(!strcmp(name,"/dev/snd/pcmC0D0p") && flags&O_NONBLOCK);
    pthread_mutex_lock(&kernel_lock); assert(device_fd<0);
    device_fd=eventfd(0,EFD_NONBLOCK|EFD_CLOEXEC); assert(device_fd>=0);
    queued=appl=hw=write_count=device_blocked=0; minimum=128; stream_state=SNDRV_PCM_STATE_OPEN;
    tick_ns=board_now_ns(); frame_fraction=0; ++device_opens;
    pthread_mutex_unlock(&kernel_lock); return device_fd;
}
static int provider_close(int fd)
{
    pthread_mutex_lock(&kernel_lock); assert(fd==device_fd);
    close(fd); device_fd=-1; pthread_mutex_unlock(&kernel_lock); return 0;
}
static int provider_ioctl(int fd,unsigned long command,...)
{
    va_list ap; void *arg=NULL; int rc=0;
    if(command!=SNDRV_PCM_IOCTL_PREPARE && command!=SNDRV_PCM_IOCTL_START &&
       command!=SNDRV_PCM_IOCTL_DROP && command!=SNDRV_PCM_IOCTL_DRAIN && command!=SNDRV_PCM_IOCTL_HW_FREE) {
        va_start(ap,command); arg=va_arg(ap,void *); va_end(ap);
    }
    pthread_mutex_lock(&kernel_lock); assert(fd==device_fd);
    consume_at(board_now_ns());
    switch(command) {
    case SNDRV_PCM_IOCTL_PVERSION: *(int *)arg=SNDRV_PROTOCOL_VERSION(2,0,14); break;
    case SNDRV_PCM_IOCTL_INFO: memset(arg,0,sizeof(struct snd_pcm_info)); break;
    case SNDRV_PCM_IOCTL_HW_REFINE:
    case SNDRV_PCM_IOCTL_HW_PARAMS: {
        struct snd_pcm_hw_params *h=arg;
        if(h->intervals[SNDRV_PCM_HW_PARAM_RATE-SNDRV_PCM_HW_PARAM_FIRST_INTERVAL].min!=44100 ||
           h->intervals[SNDRV_PCM_HW_PARAM_PERIOD_SIZE-SNDRV_PCM_HW_PARAM_FIRST_INTERVAL].min!=128) {
            errno=EINVAL; rc=-1; break;
        }
        capacity=h->intervals[SNDRV_PCM_HW_PARAM_BUFFER_SIZE-SNDRV_PCM_HW_PARAM_FIRST_INTERVAL].min;
        assert(capacity==3712); stream_state=SNDRV_PCM_STATE_SETUP; break;
    }
    case SNDRV_PCM_IOCTL_SW_PARAMS: {
        struct snd_pcm_sw_params *s=arg; threshold=(unsigned)s->start_threshold;
        minimum=(unsigned)s->avail_min; boundary=(unsigned)s->boundary;
        assert(threshold==2823 && minimum==128 && s->stop_threshold==3712); break;
    }
    case SNDRV_PCM_IOCTL_PREPARE:
        queued=appl=hw=0; stream_state=SNDRV_PCM_STATE_PREPARED; frame_fraction=0; ++device_resets; break;
    case SNDRV_PCM_IOCTL_START:
        if(stream_state!=SNDRV_PCM_STATE_PREPARED) { errno=EBADFD; rc=-1; break; }
        assert(queued>=threshold); stream_state=SNDRV_PCM_STATE_RUNNING; tick_ns=board_now_ns(); break;
    case SNDRV_PCM_IOCTL_WRITEI_FRAMES: {
        struct snd_xferi *x=arg; unsigned count=(unsigned)x->frames;
        if(inject_write && ++write_count==100) { stream_state=SNDRV_PCM_STATE_SETUP; errno=EBADFD; rc=-1; break; }
        if(stream_state!=SNDRV_PCM_STATE_PREPARED && stream_state!=SNDRV_PCM_STATE_RUNNING) {
            errno=stream_state==SNDRV_PCM_STATE_XRUN?EPIPE:EBADFD; rc=-1; break;
        }
        if(stream_state==SNDRV_PCM_STATE_PREPARED && !queued) assert(minimum==128);
        if(! (capacity-queued)) { errno=EAGAIN; rc=-1; break; }
        if(count>capacity-queued) count=capacity-queued;
        if(count>137) count=137;
        queued+=count; appl=(appl+count)%boundary; device_accepted+=count; x->result=count;
        if(stream_state==SNDRV_PCM_STATE_PREPARED && queued>=threshold) {
            stream_state=SNDRV_PCM_STATE_RUNNING; tick_ns=board_now_ns();
        }
        break;
    }
    case SNDRV_PCM_IOCTL_STATUS: {
        struct snd_pcm_status *s=arg; memset(s,0,sizeof(*s));
        s->state=stream_state; s->appl_ptr=appl; s->hw_ptr=hw; s->avail=capacity-queued; break;
    }
    case SNDRV_PCM_IOCTL_SYNC_PTR: {
        struct snd_pcm_sync_ptr *s=arg; assert(s->flags&SNDRV_PCM_SYNC_PTR_APPL);
        if(s->flags&SNDRV_PCM_SYNC_PTR_HWSYNC) {
            if(stream_state==SNDRV_PCM_STATE_XRUN) { errno=EPIPE; rc=-1; break; }
            if(stream_state==SNDRV_PCM_STATE_SETUP) { errno=EBADFD; rc=-1; break; }
        }
        if(s->flags&SNDRV_PCM_SYNC_PTR_AVAIL_MIN) s->c.control.avail_min=minimum;
        else minimum=(unsigned)s->c.control.avail_min;
        s->s.status.state=stream_state; s->s.status.hw_ptr=hw; s->c.control.appl_ptr=appl; break;
    }
    case SNDRV_PCM_IOCTL_DRAIN:
        stream_state=queued?SNDRV_PCM_STATE_DRAINING:SNDRV_PCM_STATE_SETUP;
        if(queued) { errno=EAGAIN; rc=-1; } break;
    case SNDRV_PCM_IOCTL_DROP: queued=0; stream_state=SNDRV_PCM_STATE_SETUP; break;
    case SNDRV_PCM_IOCTL_HW_FREE: break;
    default: assert(!"unexpected PCM ioctl");
    }
    readiness(); pthread_mutex_unlock(&kernel_lock); return rc;
}
#define open provider_open
#define close provider_close
#define ioctl provider_ioctl
#include "native-pcm.c"
#undef open
#undef close
#undef ioctl
#include "runner.c"
#include "audio-owner.c"
static unsigned menu_visits,menu_action,next_menu,deficit_mode;
static uint64_t production_deadline;
int board_is_null(void) { return 0; }
const char *board_last_error(void) { return pcm_error(); }
const char *board_audio_error(void) { return pcm_error(); }
int board_audio_open(unsigned rate) { return pcm_open(rate); }
int board_audio_observe(struct board_audio_state *out) { return pcm_observe(out); }
ssize_t board_audio_write(const int16_t *data,size_t frames) { return pcm_write(data,frames); }
int board_audio_reset(void) { return pcm_reset(); }
int board_audio_finish(void) { return pcm_finish(); }
int board_audio_queued_frames(void) { struct board_audio_state out; return pcm_observe(&out)<0?-1:(int)out.queued; }
int board_audio_avail_min(unsigned frames) { return pcm_avail_min(frames); }
int board_audio_fd(void) { return pcm_fd(); }
void board_audio_close(void) { pcm_close(); }
int board_video_reserve(void) { production_deadline=board_now_ns()+19880500u; return 0; }
void board_video_cancel(void) { }
void board_wait_display(void) { }
void board_video_metrics(struct board_video_metrics *out,int reset)
{ (void)reset; if(out) memset(out,0,sizeof(*out)); }
int board_video_submit(const void *data,unsigned w,unsigned h,size_t pitch)
{
    assert(data && w && h && pitch>=w*2);
    if(deficit_mode) {
        while(board_now_ns()<production_deadline) {
            uint64_t remaining=production_deadline-board_now_ns();
            if(remaining>19880500u) break;
            struct timespec delay={0,(long)remaining}; nanosleep(&delay,NULL);
        }
    } else if(!(s.runs%40)) usleep(25000);
    return 0;
}
uint32_t board_poll_input(void)
{
    if(!inject_write && s.runs>=120) runner_request_stop();
    if(!inject_write && s.runs>=next_menu && menu_visits<2) { ++menu_visits; next_menu+=48; return BOARD_MENU; }
    return 0;
}
static int native_menu(void *unused,const char *text)
{
    (void)unused;
    if(!(menu_action++%2)) {
        pthread_mutex_lock(&kernel_lock); assert(stream_state==SNDRV_PCM_STATE_PREPARED && !queued);
        pthread_mutex_unlock(&kernel_lock); usleep(120000); return RUNNER_LOAD_STATE;
    }
    assert(!strcmp(text,"Snapshot loaded")); return RUNNER_RESUME;
}
int main(int argc,char **argv)
{
    pthread_t consumer; struct audio_pipe_stats out; uint64_t before; int rc;
    const char *trace_path="build/snes-mvp/out/native-runner-fault-fixture.txt";
    char history[32768]; FILE *trace; size_t bytes;
    assert(argc==4); assert(!pthread_create(&consumer,NULL,consume_pcm,NULL));
    unlink(trace_path); assert(!setenv("D35_MVP_PCM_TRACE_FILE",trace_path,1));
    runner_set_menu_callback(native_menu,NULL); inject_write=1;
    assert(runner_run(argv[1],argv[2],argv[3])<0);
    assert(strstr(runner_last_error(),"Audio publication failed") && !strstr(runner_last_error(),"queue"));
    audio_pipe_stats(&out); assert(out.error==EBADFD && out.epoch==1 && out.high<8192);
    assert(strstr(out.error_detail,"WRITEI_FRAMES errno=77 state=1"));
    assert(strstr(out.error_detail,"trace_errno=0 trace_synced=1"));
    trace=fopen(trace_path,"r"); assert(trace);
    bytes=fread(history,1,sizeof(history)-1,trace); history[bytes]=0; fclose(trace);
    assert(strstr(history,"D35 PCM fault history 1.13") && strstr(history,"WRITEI_FRAMES errno=77"));
    unsetenv("D35_MVP_PCM_TRACE_FILE");
    assert(device_opens==1 && device_fd<0); inject_write=0; next_menu=8; before=device_accepted;
    rc=runner_run(argv[1],argv[2],argv[3]);
    if(rc) fprintf(stderr,"native runner: %s\n",runner_last_error());
    assert(!rc); audio_pipe_stats(&out);
    assert(s.runs==120 && s.videos==120 && !s.held && s.pauses==2 && menu_action==4 && s.snapshot_loads==2);
    assert(s.primed==8469 && out.epoch==3 && !out.errors && !out.remaining && !out.cleared);
    assert(out.accepted==out.enqueued && out.accepted==device_accepted-before);
    assert(out.admissions>=120 && out.admissions<=121 && out.admission_max<=2823 && device_opens==2 && device_fd<0);
    /* Replay the measured sustained rate deficit, not just isolated jitter.
     * A consuming 44.1k provider must starve when full frames repeat at 19.88ms;
     * the controller must expose it without secretly re-priming or retrying. */
    deficit_mode=1; next_menu=UINT_MAX;
    assert(runner_run(argv[1],argv[2],argv[3])<0);
    audio_pipe_stats(&out);
    assert(out.error==EPIPE && out.xruns==1 && out.epoch==1 && s.primed==2823);
    assert(s.runs<120 && !s.held && !s.pauses && out.accepted+out.remaining==out.enqueued);
    pthread_mutex_lock(&kernel_lock); consumer_stop=1; pthread_mutex_unlock(&kernel_lock); pthread_join(consumer,NULL);
    puts("PASS: real FF6 core with actual runner/owner/native PCM client, consuming 44100/128/3712 provider, truthful WRITEI failure then clean retry, two snapshot loads and re-primed resumes, restored drain threshold, 25ms producer stalls, 120 full drawings, zero lost/cleared PCM");
    puts("PASS: sustained 19.8805ms production against 44100Hz consumption exposes starvation without hidden re-prime, frame suppression or accounting loss");
    return 0;
}
