/* Linux native PCM, ARM32/time32 UAPI. No OSS staging or implicit restart. */
#define _GNU_SOURCE
#include "native-pcm.h"
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <poll.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <time.h>
#include <sound/asound.h>

static struct { int fd,started,error; struct board_audio_state config; } pcm={.fd=-1};
#if defined(__arm__)
typedef char pcm_time32[(sizeof(struct timespec)==8)?1:-1];
typedef char pcm_hw_abi[(sizeof(struct snd_pcm_hw_params)==604)?1:-1];
typedef char pcm_sw_abi[(sizeof(struct snd_pcm_sw_params)==104)?1:-1];
typedef char pcm_status_abi[(sizeof(struct snd_pcm_status)==108)?1:-1];
typedef char pcm_sync_abi[(sizeof(struct snd_pcm_sync_ptr)==132)?1:-1];
#endif
static void interval(struct snd_pcm_hw_params *p,unsigned key,unsigned value)
{
    struct snd_interval *v=&p->intervals[key-SNDRV_PCM_HW_PARAM_FIRST_INTERVAL];
    memset(v,0,sizeof(*v)); v->min=v->max=value; v->integer=1;
}
static void mask(struct snd_pcm_hw_params *p,unsigned key,unsigned value)
{
    struct snd_mask *m=&p->masks[key-SNDRV_PCM_HW_PARAM_FIRST_MASK];
    memset(m,0,sizeof(*m)); m->bits[value/32]=1u<<(value%32);
}
static void params(struct snd_pcm_hw_params *p,unsigned rate,unsigned period,unsigned buffer)
{
    unsigned i;
    memset(p,0,sizeof(*p));
    for(i=0;i<3;i++) memset(p->masks[i].bits,255,sizeof(p->masks[i].bits));
    for(i=0;i<=SNDRV_PCM_HW_PARAM_LAST_INTERVAL-SNDRV_PCM_HW_PARAM_FIRST_INTERVAL;i++) {
        p->intervals[i].max=UINT_MAX;
    }
    p->rmask=~0u; p->flags=SNDRV_PCM_HW_PARAMS_NORESAMPLE;
    mask(p,SNDRV_PCM_HW_PARAM_ACCESS,SNDRV_PCM_ACCESS_RW_INTERLEAVED);
    mask(p,SNDRV_PCM_HW_PARAM_FORMAT,SNDRV_PCM_FORMAT_S16_LE);
    mask(p,SNDRV_PCM_HW_PARAM_SUBFORMAT,SNDRV_PCM_SUBFORMAT_STD);
    interval(p,SNDRV_PCM_HW_PARAM_CHANNELS,2);
    interval(p,SNDRV_PCM_HW_PARAM_RATE,rate);
    interval(p,SNDRV_PCM_HW_PARAM_PERIOD_SIZE,period);
    interval(p,SNDRV_PCM_HW_PARAM_BUFFER_SIZE,buffer);
}
int pcm_open(unsigned requested)
{
    static const unsigned periods[]={128,256,512,1024};
    unsigned rates[]={requested,44100,48000},r,p,b;
    int version,last=EINVAL;
    struct snd_pcm_info info;
    pcm_close();
    pcm.fd=open("/dev/snd/pcmC0D0p",O_WRONLY|O_NONBLOCK|O_CLOEXEC);
    if(pcm.fd<0) return -1;
    memset(&info,0,sizeof(info));
    if(ioctl(pcm.fd,SNDRV_PCM_IOCTL_PVERSION,&version)<0 ||
       ioctl(pcm.fd,SNDRV_PCM_IOCTL_INFO,&info)<0) goto failed;
    fprintf(stderr,"native PCM protocol=%x card=%d device=%u subdevice=%u id=%.64s\n",
            version,info.card,info.device,info.subdevice,info.id);
    for(r=0;r<3;r++) for(p=0;p<4;p++) {
        unsigned prime=(rates[r]*64u+999u)/1000u;
        unsigned need=prime+(rates[r]*20u+999u)/1000u;
        unsigned choices[2],power=1;
        choices[0]=(need+periods[p]-1)/periods[p]*periods[p];
        while(power<need) power*=2;
        choices[1]=power;
        for(b=0;b<2;b++) {
            struct snd_pcm_hw_params hw;
            struct snd_pcm_sw_params sw;
            unsigned size=choices[b];
            if(b && size==choices[0]) continue;
            params(&hw,rates[r],periods[p],size);
            if(ioctl(pcm.fd,SNDRV_PCM_IOCTL_HW_REFINE,&hw)<0 ||
               ioctl(pcm.fd,SNDRV_PCM_IOCTL_HW_PARAMS,&hw)<0) { last=errno; continue; }
            /* The exact constraints must survive negotiation; no rate guess. */
            if(hw.intervals[SNDRV_PCM_HW_PARAM_RATE-SNDRV_PCM_HW_PARAM_FIRST_INTERVAL].min!=rates[r] ||
               hw.intervals[SNDRV_PCM_HW_PARAM_BUFFER_SIZE-SNDRV_PCM_HW_PARAM_FIRST_INTERVAL].min!=size) {
                last=EPROTO; ioctl(pcm.fd,SNDRV_PCM_IOCTL_HW_FREE,0); continue;
            }
            memset(&sw,0,sizeof(sw)); sw.period_step=1; sw.avail_min=periods[p];
            sw.xfer_align=1; sw.stop_threshold=size; sw.boundary=size;
            while(sw.boundary*2u <= (unsigned long)LONG_MAX-size) sw.boundary*=2u;
            sw.start_threshold=sw.boundary; /* explicit START after real priming */
            sw.tstamp_mode=SNDRV_PCM_TSTAMP_ENABLE;
            sw.tstamp_type=SNDRV_PCM_TSTAMP_TYPE_MONOTONIC;
            sw.proto=(unsigned)version;
            if(ioctl(pcm.fd,SNDRV_PCM_IOCTL_SW_PARAMS,&sw)<0 ||
               ioctl(pcm.fd,SNDRV_PCM_IOCTL_PREPARE,0)<0) goto failed;
            pcm.config.rate=rates[r]; pcm.config.period=periods[p];
            pcm.config.buffer=size; pcm.config.prime=prime; pcm.started=0;
            fprintf(stderr,"native PCM rate=%u period=%u buffer=%u prime=%u access=RW_INTERLEAVED explicit_start=1\n",
                    rates[r],periods[p],size,prime);
            return (int)rates[r];
        }
    }
    errno=last;
failed:
    last=errno; pcm_close(); errno=last; return -1;
}
int pcm_observe(struct board_audio_state *out)
{
    struct snd_pcm_status status;
    memset(&status,0,sizeof(status));
    if(pcm.fd<0) { errno=EBADF; return -1; }
    if(pcm.error) { errno=pcm.error; return -1; }
    if(ioctl(pcm.fd,SNDRV_PCM_IOCTL_STATUS,&status)<0) return -1;
    *out=pcm.config; out->state=status.state; out->started=pcm.started;
    out->observed_ns=board_now_ns();
    if(status.state==SNDRV_PCM_STATE_XRUN) { errno=EPIPE; return -1; }
    if(status.state==SNDRV_PCM_STATE_SUSPENDED) { errno=ESTRPIPE; return -1; }
    if(status.avail>pcm.config.buffer) { errno=EPROTO; return -1; }
    out->queued=status.state==SNDRV_PCM_STATE_SETUP?0:pcm.config.buffer-(unsigned)status.avail;
    return 0;
}
ssize_t pcm_write(const int16_t *data,size_t frames)
{
    struct snd_xferi x;
    struct board_audio_state state;
    memset(&x,0,sizeof(x)); x.buf=(void *)data; x.frames=frames;
    if(ioctl(pcm.fd,SNDRV_PCM_IOCTL_WRITEI_FRAMES,&x)<0) return -1;
    if(x.result<0) { errno=(int)-x.result; return -1; }
    if((size_t)x.result>frames) { errno=EPROTO; return -1; }
    if(!pcm.started) {
        if(pcm_observe(&state)<0) pcm.error=errno;
        else if(state.queued>=pcm.config.prime) {
            if(ioctl(pcm.fd,SNDRV_PCM_IOCTL_START,0)<0) pcm.error=errno;
            else pcm.started=1;
        }
    }
    return x.result;
}
int pcm_avail_min(unsigned frames)
{
    struct snd_pcm_sync_ptr sync;
    memset(&sync,0,sizeof(sync));
    sync.flags=SNDRV_PCM_SYNC_PTR_HWSYNC|SNDRV_PCM_SYNC_PTR_APPL;
    sync.c.control.avail_min=frames?frames:1;
    return ioctl(pcm.fd,SNDRV_PCM_IOCTL_SYNC_PTR,&sync);
}
int pcm_reset(void)
{
    if(pcm.fd<0) return 0;
    if(ioctl(pcm.fd,SNDRV_PCM_IOCTL_DROP,0)<0) return -1;
    pcm.started=pcm.error=0;
    return ioctl(pcm.fd,SNDRV_PCM_IOCTL_PREPARE,0);
}
int pcm_finish(void)
{
    uint64_t until=board_now_ns()+1000000000u;
    struct pollfd fd={pcm.fd,POLLOUT,0};
    int rc;
    /* Ordinary write readiness must not turn draining into a busy loop. */
    if(pcm_avail_min(pcm.config.buffer)<0) return -1;
    rc=ioctl(pcm.fd,SNDRV_PCM_IOCTL_DRAIN,0);
    if(rc<0 && errno!=EAGAIN) return -1;
    while(rc<0) {
        struct snd_pcm_status status;
        memset(&status,0,sizeof(status));
        if(ioctl(pcm.fd,SNDRV_PCM_IOCTL_STATUS,&status)<0) return -1;
        if(status.state==SNDRV_PCM_STATE_SETUP) break;
        if(status.state!=SNDRV_PCM_STATE_DRAINING) {
            errno=status.state==SNDRV_PCM_STATE_XRUN?EPIPE:EPROTO; return -1;
        }
        if(board_now_ns()>=until) { errno=ETIMEDOUT; return -1; }
        rc=poll(&fd,1,100);
        if(rc<0 && errno!=EINTR) return -1;
        rc=-1;
    }
    pcm.started=0; return 0;
}
int pcm_fd(void) { return pcm.fd; }
void pcm_close(void)
{
    if(pcm.fd>=0) { ioctl(pcm.fd,SNDRV_PCM_IOCTL_DROP,0); close(pcm.fd); }
    memset(&pcm,0,sizeof(pcm)); pcm.fd=-1;
}
