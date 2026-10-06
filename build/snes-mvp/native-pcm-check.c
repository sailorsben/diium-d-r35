/* Independent constrained PCM provider; executes the actual ARM client. */
#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <time.h>
#include <unistd.h>
#include <sound/asound.h>
#include "board.h"
static unsigned buffer,queued,starts,writes,accepted,minimum,prepares;
static int stream_state,start_error,manual_start,start_race,early_start,bad_sw;
static int write_error,hwsync_fault,pointer_override;
static unsigned boundary,pointer_appl,pointer_hw;
static unsigned capture_syncs;
static int capture_sync_error;
static int provider_fsync(int fd)
{ ++capture_syncs; if(capture_sync_error) { errno=capture_sync_error; return -1; } return fsync(fd); }
static int16_t expected[4096*2];
static int provider_open(const char *name,int flags,...)
{ assert(!strcmp(name,"/dev/snd/pcmC0D0p") && flags&O_NONBLOCK); return 42; }
static int provider_close(int fd) { assert(fd==42); return 0; }
static int provider_poll(struct pollfd *fds,nfds_t n,int timeout)
{ assert(n==1 && fds[0].fd==42 && timeout==100); queued=0; stream_state=SNDRV_PCM_STATE_SETUP; return 1; }
static int provider_ioctl(int fd,unsigned long command,...)
{
    va_list ap; void *arg=NULL; assert(fd==42);
    if(command!=SNDRV_PCM_IOCTL_PREPARE && command!=SNDRV_PCM_IOCTL_START &&
       command!=SNDRV_PCM_IOCTL_DROP && command!=SNDRV_PCM_IOCTL_DRAIN && command!=SNDRV_PCM_IOCTL_HW_FREE) {
        va_start(ap,command); arg=va_arg(ap,void *); va_end(ap);
    }
    switch(command) {
    case SNDRV_PCM_IOCTL_PVERSION: *(int *)arg=SNDRV_PROTOCOL_VERSION(2,0,14); return 0;
    case SNDRV_PCM_IOCTL_INFO: memset(arg,0,sizeof(struct snd_pcm_info)); return 0;
    case SNDRV_PCM_IOCTL_HW_REFINE:
    case SNDRV_PCM_IOCTL_HW_PARAMS: {
        struct snd_pcm_hw_params *h=arg;
        unsigned rate=h->intervals[SNDRV_PCM_HW_PARAM_RATE-SNDRV_PCM_HW_PARAM_FIRST_INTERVAL].min;
        unsigned period=h->intervals[SNDRV_PCM_HW_PARAM_PERIOD_SIZE-SNDRV_PCM_HW_PARAM_FIRST_INTERVAL].min;
        assert(h->masks[SNDRV_PCM_HW_PARAM_ACCESS].bits[0]==1u<<SNDRV_PCM_ACCESS_RW_INTERLEAVED);
        assert(h->masks[SNDRV_PCM_HW_PARAM_FORMAT].bits[0]==1u<<SNDRV_PCM_FORMAT_S16_LE);
        assert(h->flags&SNDRV_PCM_HW_PARAMS_NORESAMPLE);
        if(rate!=44100 || period!=128) { errno=EINVAL; return -1; }
        buffer=h->intervals[SNDRV_PCM_HW_PARAM_BUFFER_SIZE-SNDRV_PCM_HW_PARAM_FIRST_INTERVAL].min;
        assert(buffer==3712); return 0;
    }
    case SNDRV_PCM_IOCTL_SW_PARAMS: {
        struct snd_pcm_sw_params *s=arg;
        assert(s->avail_min==128 && s->start_threshold==2823 && s->stop_threshold==buffer);
        assert(s->tstamp_type==SNDRV_PCM_TSTAMP_TYPE_MONOTONIC && !s->silence_size);
        if(bad_sw) s->start_threshold=1;
        boundary=(unsigned)s->boundary;
        return 0;
    }
    case SNDRV_PCM_IOCTL_PREPARE: queued=accepted=0; ++prepares; stream_state=SNDRV_PCM_STATE_PREPARED; return 0;
    case SNDRV_PCM_IOCTL_START:
        ++starts;
        if(stream_state!=SNDRV_PCM_STATE_PREPARED) { errno=EBADFD; return -1; }
        assert(queued>=2823);
        if(start_race) { stream_state=SNDRV_PCM_STATE_RUNNING; errno=EBADFD; return -1; }
        if(start_error) { errno=start_error; return -1; }
        stream_state=SNDRV_PCM_STATE_RUNNING; return 0;
    case SNDRV_PCM_IOCTL_WRITEI_FRAMES: {
        struct snd_xferi *x=arg; unsigned n=(unsigned)x->frames;
        if(write_error) { stream_state=SNDRV_PCM_STATE_SETUP; errno=write_error; return -1; }
        if(!(++writes%7)) { errno=EAGAIN; return -1; }
        if(n>137) n=137;
        assert(accepted+n<=4096 && !memcmp(x->buf,expected+accepted*2,n*4));
        queued+=n; accepted+=n; x->result=n;
        /* Linux can START inside WRITEI; a second START is EBADFD. */
        if((!manual_start && queued>=2823) || early_start) stream_state=SNDRV_PCM_STATE_RUNNING;
        return 0;
    }
    case SNDRV_PCM_IOCTL_STATUS: {
        struct snd_pcm_status *s=arg; memset(s,0,sizeof(*s));
        s->state=stream_state; s->avail=buffer-queued; s->appl_ptr=accepted; return 0;
    }
    case SNDRV_PCM_IOCTL_SYNC_PTR: {
        struct snd_pcm_sync_ptr *s=arg;
        assert(s->flags&SNDRV_PCM_SYNC_PTR_APPL); /* never overwrite the writer's application pointer */
        if(s->flags&SNDRV_PCM_SYNC_PTR_HWSYNC) {
            if(hwsync_fault) { stream_state=SNDRV_PCM_STATE_XRUN; errno=EPIPE; return -1; }
            if(stream_state==SNDRV_PCM_STATE_SETUP) { errno=EBADFD; return -1; }
        }
        if(s->flags&SNDRV_PCM_SYNC_PTR_AVAIL_MIN) s->c.control.avail_min=minimum;
        else minimum=(unsigned)s->c.control.avail_min;
        s->c.control.appl_ptr=pointer_override?pointer_appl:accepted;
        s->s.status.hw_ptr=pointer_override?pointer_hw:accepted-queued;
        s->s.status.state=stream_state; return 0;
    }
    case SNDRV_PCM_IOCTL_DRAIN: stream_state=SNDRV_PCM_STATE_DRAINING; errno=EAGAIN; return -1;
    case SNDRV_PCM_IOCTL_DROP: queued=0; stream_state=SNDRV_PCM_STATE_SETUP; return 0;
    case SNDRV_PCM_IOCTL_HW_FREE: return 0;
    default: assert(!"unexpected native PCM command"); return -1;
    }
}
#define open provider_open
#define close provider_close
#define ioctl provider_ioctl
#define poll provider_poll
#define fsync provider_fsync
#include "native-pcm.c"
#undef open
#undef close
#undef ioctl
#undef poll
#undef fsync
uint64_t board_now_ns(void) { static uint64_t now; return now+=10000; }
int main(void)
{
    unsigned i,offset=0; struct board_audio_state state;
    /* Independent Linux 4.19 ARM32 ioctl values, not generated by our client. */
    assert(SNDRV_PCM_IOCTL_HW_PARAMS==0xc25c4111u);
    assert(SNDRV_PCM_IOCTL_SW_PARAMS==0xc0684113u);
    assert(SNDRV_PCM_IOCTL_STATUS==0x806c4120u);
    assert(SNDRV_PCM_IOCTL_SYNC_PTR==0xc0844123u);
    assert(SNDRV_PCM_IOCTL_WRITEI_FRAMES==0x400c4150u);
    for(i=0;i<8192;i++) expected[i]=(int16_t)(i*97u+13u);
    assert(pcm_open(32040)==44100); assert(!pcm_observe(&state));
    assert(state.period==128 && state.buffer==3712 && state.prime==2823 && !state.started);
    while(offset<3500) {
        ssize_t n=pcm_write(expected+offset*2,3500-offset);
        if(n<0) assert(errno==EAGAIN); else offset+=(unsigned)n;
    }
    assert(accepted==3500 && starts==0 && !pcm_observe(&state) && state.started);
    assert(state.prime_transferred>=2823 && state.state==SNDRV_PCM_STATE_RUNNING);
    assert(!pcm_avail_min(1273) && minimum==1273);
    assert(!pcm_observe(&state) && minimum==1273); /* a GET cannot reset the poll threshold */
    pointer_override=1; pointer_appl=40; pointer_hw=boundary-90;
    assert(!pcm_observe(&state) && state.queued==130 && state.avail==3582);
    pointer_override=0;
    hwsync_fault=1;
    assert(pcm_observe(&state)<0 && errno==EPIPE && state.state==SNDRV_PCM_STATE_XRUN);
    hwsync_fault=0; assert(!pcm_reset() && minimum==128); offset=0;
    while(offset<2823) {
        ssize_t n=pcm_write(expected+offset*2,2823-offset);
        if(n<0) assert(errno==EAGAIN); else offset+=(unsigned)n;
    }
    write_error=EBADFD;
    assert(pcm_write(expected+offset*2,16)<0 && errno==EBADFD);
    assert(pcm_observe(&state)<0 && state.state==SNDRV_PCM_STATE_SETUP);
    assert(strstr(pcm_error(),"WRITEI_FRAMES errno=77 state=1"));
    write_error=0; assert(!pcm_reset()); offset=0;
    while(offset<2823) {
        ssize_t n=pcm_write(expected+offset*2,2823-offset);
        if(n<0) assert(errno==EAGAIN); else offset+=(unsigned)n;
    }
    assert(!pcm_finish() && !queued && !pcm_observe(&state) && !state.queued);
    assert(!pcm_reset()); manual_start=1; start_error=EIO; offset=0;
    while(offset<2823) {
        ssize_t n=pcm_write(expected+offset*2,2823-offset);
        if(n<0) assert(errno==EAGAIN); else offset+=(unsigned)n;
    }
    assert(accepted==2823 && pcm_observe(&state)<0 && errno==EIO);
    assert(state.state==SNDRV_PCM_STATE_PREPARED && state.prime_transferred==2823 && state.start_calls==1);
    assert(strstr(pcm_error(),"START errno=5") && strstr(pcm_error(),"prime_written=2823"));
    start_error=EBADFD; assert(!pcm_reset()); offset=0;
    while(offset<2823) {
        ssize_t n=pcm_write(expected+offset*2,2823-offset);
        if(n<0) assert(errno==EAGAIN); else offset+=(unsigned)n;
    }
    assert(pcm_observe(&state)<0 && errno==EBADFD && !state.started);
    start_error=0; assert(!pcm_reset()); offset=0;
    while(offset<2823) {
        ssize_t n=pcm_write(expected+offset*2,2823-offset);
        if(n<0) assert(errno==EAGAIN); else offset+=(unsigned)n;
    }
    assert(!pcm_observe(&state) && state.started && state.start_calls==1 && !state.start_races);
    start_race=1; assert(!pcm_reset()); offset=0;
    while(offset<2823) {
        ssize_t n=pcm_write(expected+offset*2,2823-offset);
        if(n<0) assert(errno==EAGAIN); else offset+=(unsigned)n;
    }
    assert(!pcm_observe(&state) && state.started && state.start_races==1);
    start_race=0; manual_start=0; early_start=1; assert(!pcm_reset());
    while(pcm_write(expected,137)<0) assert(errno==EAGAIN);
    assert(pcm_observe(&state)<0 && errno==EPROTO && !state.started && accepted==137);
    early_start=0; assert(!pcm_reset());
    i=prepares;
    {
        const char *trace_path="build/snes-mvp/out/native-pcm-fault-fixture.txt";
        char history[32768]; FILE *trace; unsigned j; size_t bytes;
        unlink(trace_path); capture_syncs=0; assert(!setenv("D35_MVP_PCM_TRACE_FILE",trace_path,1));
        for(j=0;j<200;j++) assert(!pcm_observe(&state));
        assert(access(trace_path,F_OK)<0); /* RAM records never print/write healthy transfers */
        stream_state=SNDRV_PCM_STATE_XRUN;
        assert(pcm_observe(&state)<0 && errno==EPIPE);
        trace=fopen(trace_path,"r"); assert(trace);
        bytes=fread(history,1,sizeof(history)-1,trace); history[bytes]=0; fclose(trace);
        assert(strstr(history,"D35 PCM fault history 1.13") && strstr(history,"op=SYNC_XRUN"));
        assert(strstr(history,"kernel_read_all_bytes=") && strstr(history,"epoch="));
        assert(!strstr(history,"seq=0 ") && !strstr(history,"RESET_DROP"));
        assert(capture_syncs==2 && strstr(pcm_error(),"trace_errno=0 trace_synced=1 trace_bytes="));
        assert(!pcm_reset()); stream_state=SNDRV_PCM_STATE_XRUN; capture_sync_error=EIO;
        assert(pcm_observe(&state)<0 && errno==EPIPE);
        assert(strstr(pcm_error(),"trace_errno=5 trace_synced=0"));
        capture_sync_error=0;
        unsetenv("D35_MVP_PCM_TRACE_FILE");
        puts("PASS: bounded PCM flight history writes only on fault before cleanup; kernel read result is explicit");
        puts("PASS: PCM fault capture fsyncs file and directory before error return; injected persistence failure reported without changing PCM errno");
    }
    i=prepares; /* explicit reset above is allowed; fault handling must not prepare */
    stream_state=SNDRV_PCM_STATE_XRUN;
    assert(pcm_observe(&state)<0 && errno==EPIPE);
    assert(prepares==i); /* no automatic recovery discarding samples */
    pcm_close();
    bad_sw=1;
    assert(pcm_open(32040)<0 && errno==EPROTO && strstr(pcm_error(),"SW_PARAMS_READBACK"));
    puts("PASS: actual ARM32 PCM ABI, device-shaped 44100/128/3712 fallback, exact partial/EAGAIN frames, kernel WRITEI auto-start without duplicate START, prepared-only explicit START, verified EBADFD race, rejected early start/nonrunning EBADFD/software-threshold mismatch, post-HWSYNC state/pointers, boundary wrap, GET flags preserve control, fresh WRITEI fault state, DRAIN threshold reset, asynchronous DRAIN, accepted START-failure state/pointer accounting and visible XRUN without restart");
    return 0;
}
