/* Linux native PCM, ARM32/time32 UAPI. No OSS staging or implicit restart. */
#define _GNU_SOURCE
#include "native-pcm.h"
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <time.h>
#include <sound/asound.h>

static struct { int fd,started,error; char failure[256]; struct board_audio_state config; } pcm={.fd=-1};
/* No per-transfer printing or SD writes. Preserve the last transactions only
 * when a stream fails, before DROP/close can erase the causal state. */
#define PCM_TRACE_COUNT 96u
static struct pcm_trace_entry {
    uint64_t ns,xfer;
    const char *op;
    unsigned state,queued,appl,hw,epoch,argument;
    int result;
} pcm_trace[PCM_TRACE_COUNT];
static uint64_t pcm_trace_count;
static void pcm_record(const char *op,unsigned argument,int result)
{
    struct pcm_trace_entry *t=&pcm_trace[pcm_trace_count++%PCM_TRACE_COUNT];
    t->ns=board_now_ns(); t->xfer=pcm.config.epoch_transferred; t->op=op;
    t->state=pcm.config.state; t->queued=pcm.config.queued;
    t->appl=pcm.config.appl_ptr; t->hw=pcm.config.hw_ptr;
    t->epoch=pcm.config.epoch; t->argument=argument; t->result=result;
}
static void pcm_dump_fault(void)
{
    const char *path=getenv("D35_MVP_PCM_TRACE_FILE");
    char temporary[512],kernel[16384]; FILE *f;
    uint64_t first=pcm_trace_count>PCM_TRACE_COUNT?pcm_trace_count-PCM_TRACE_COUNT:0,i;
    int bytes,saved;
    if(!path || !*path) return;
    if(snprintf(temporary,sizeof(temporary),"%s.tmp",path)>=(int)sizeof(temporary)) return;
    f=fopen(temporary,"w"); if(!f) return;
    fprintf(f,"D35 PCM fault history 1.12\nfailure=%s\nentries_total=%llu\n",pcm.failure,(unsigned long long)pcm_trace_count);
    fprintf(f,"Each sample is after the named operation; WRITE_OK retains the preceding pointer observation.\n");
    for(i=first;i<pcm_trace_count;i++) {
        const struct pcm_trace_entry *t=&pcm_trace[i%PCM_TRACE_COUNT];
        fprintf(f,"seq=%llu ns=%llu op=%s arg=%u result=%d state=%u queued=%u appl=%u hw=%u epoch=%u xfer=%llu\n",
            (unsigned long long)i,(unsigned long long)t->ns,t->op,t->argument,t->result,
            t->state,t->queued,t->appl,t->hw,t->epoch,(unsigned long long)t->xfer);
    }
    /* READ_ALL does not clear the kernel ring and needs no firmware dmesg tool.
     * Permission/unsupported errors remain evidence, never fake an empty ring. */
    bytes=(int)syscall(SYS_syslog,3,kernel,sizeof(kernel)); saved=errno;
    fprintf(f,"kernel_read_all_bytes=%d errno=%d\n",bytes,bytes<0?saved:0);
    if(bytes>0 && bytes<=(int)sizeof(kernel)) fwrite(kernel,1,(size_t)bytes,f);
    if(fclose(f)==0) (void)rename(temporary,path);
}
#if defined(__arm__)
typedef char pcm_time32[(sizeof(struct timespec)==8)?1:-1];
typedef char pcm_hw_abi[(sizeof(struct snd_pcm_hw_params)==604)?1:-1];
typedef char pcm_sw_abi[(sizeof(struct snd_pcm_sw_params)==104)?1:-1];
typedef char pcm_status_abi[(sizeof(struct snd_pcm_status)==108)?1:-1];
typedef char pcm_sync_abi[(sizeof(struct snd_pcm_sync_ptr)==132)?1:-1];
#endif
static int pcm_fail(const char *operation,int value)
{
    snprintf(pcm.failure,sizeof(pcm.failure),"%s errno=%d state=%u queued=%u avail=%u appl=%u hw=%u prime_written=%u start_calls=%u epoch=%u xfer=%llu",
             operation,value,pcm.config.state,pcm.config.queued,pcm.config.avail,
             pcm.config.appl_ptr,pcm.config.hw_ptr,pcm.config.prime_transferred,pcm.config.start_calls,
             pcm.config.epoch,(unsigned long long)pcm.config.epoch_transferred);
    fprintf(stderr,"native PCM failure: %s\n",pcm.failure);
    if(!pcm.error && pcm.fd>=0) { pcm_record(operation,0,-value); pcm_dump_fault(); }
    pcm.error=value; errno=value; return -1;
}
const char *pcm_error(void) { return pcm.failure; }
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
    const char *operation="OPEN";
    struct snd_pcm_info info;
    pcm_close();
    pcm_trace_count=0;
    pcm.fd=open("/dev/snd/pcmC0D0p",O_WRONLY|O_NONBLOCK|O_CLOEXEC);
    if(pcm.fd<0) return pcm_fail(operation,errno);
    memset(&info,0,sizeof(info));
    operation="PVERSION";
    if(ioctl(pcm.fd,SNDRV_PCM_IOCTL_PVERSION,&version)<0) goto failed;
    operation="INFO";
    if(ioctl(pcm.fd,SNDRV_PCM_IOCTL_INFO,&info)<0) goto failed;
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
            sw.start_threshold=prime; /* kernel may START inside WRITEI at this reserve */
            sw.tstamp_mode=SNDRV_PCM_TSTAMP_ENABLE;
            sw.tstamp_type=SNDRV_PCM_TSTAMP_TYPE_MONOTONIC;
            sw.proto=(unsigned)version;
            operation="SW_PARAMS";
            if(ioctl(pcm.fd,SNDRV_PCM_IOCTL_SW_PARAMS,&sw)<0) goto failed;
            if(sw.start_threshold!=prime || sw.stop_threshold!=size || sw.avail_min!=periods[p] ||
               sw.boundary<=size || sw.boundary>LONG_MAX) {
                operation="SW_PARAMS_READBACK"; errno=EPROTO; goto failed;
            }
            operation="PREPARE";
            if(ioctl(pcm.fd,SNDRV_PCM_IOCTL_PREPARE,0)<0) goto failed;
            pcm.config.rate=rates[r]; pcm.config.period=periods[p];
            pcm.config.buffer=size; pcm.config.prime=prime; pcm.started=0;
            pcm.config.boundary=(unsigned)sw.boundary; pcm.config.epoch=1;
            pcm.config.start_threshold=(unsigned)sw.start_threshold;
            pcm_record("OPEN_READY",0,0);
            fprintf(stderr,"native PCM rate=%u period=%u buffer=%u prime=%u access=RW_INTERLEAVED start_threshold=%lu boundary=%lu\n",
                    rates[r],periods[p],size,prime,(unsigned long)sw.start_threshold,(unsigned long)sw.boundary);
            return (int)rates[r];
        }
    }
    operation="HW_REFINE/HW_PARAMS"; errno=last;
failed:
    { char failure[256];
      last=errno; pcm_fail(operation,last); memcpy(failure,pcm.failure,sizeof(failure));
      pcm_close(); memcpy(pcm.failure,failure,sizeof(failure)); errno=last; return -1; }
}
static int pcm_snapshot(struct board_audio_state *out,unsigned flags)
{
    struct snd_pcm_sync_ptr sync;
    uint64_t queued;
    memset(&sync,0,sizeof(sync)); sync.flags=flags|SNDRV_PCM_SYNC_PTR_APPL|SNDRV_PCM_SYNC_PTR_AVAIL_MIN;
    if(ioctl(pcm.fd,SNDRV_PCM_IOCTL_SYNC_PTR,&sync)<0) {
        int saved=errno; pcm_record("SYNC_FAIL",sync.flags,-saved); errno=saved; return -1;
    }
    *out=pcm.config; out->started=pcm.started;
    out->state=sync.s.status.state; out->observed_ns=board_now_ns();
    out->appl_ptr=(unsigned)sync.c.control.appl_ptr; out->hw_ptr=(unsigned)sync.s.status.hw_ptr;
    queued=((uint64_t)out->appl_ptr+pcm.config.boundary-out->hw_ptr)%pcm.config.boundary;
    out->queued=out->state==SNDRV_PCM_STATE_SETUP || out->state==SNDRV_PCM_STATE_XRUN || queued>out->buffer?0:(unsigned)queued;
    out->avail=out->buffer-out->queued;
    pcm.config=*out;
    pcm_record("SYNC_OK",sync.flags,0);
    if(out->appl_ptr>=out->boundary || out->hw_ptr>=out->boundary ||
       (queued>out->buffer && out->state!=SNDRV_PCM_STATE_SETUP && out->state!=SNDRV_PCM_STATE_XRUN)) {
        errno=EPROTO; return -1;
    }
    return 0;
}
int pcm_observe(struct board_audio_state *out)
{
    *out=pcm.config; out->started=pcm.started;
    if(pcm.fd<0) { errno=EBADF; return -1; }
    if(pcm.error) { errno=pcm.error; return -1; }
    /* STATUS copies state before updating hw_ptr in Linux4.19. SYNC_PTR reads
     * state/control after HWSYNC, under the kernel stream lock. Both GET flags
     * preserve appl_ptr and avail_min; an observation must never commit either. */
    if(pcm_snapshot(out,pcm.started?SNDRV_PCM_SYNC_PTR_HWSYNC:0)<0) {
        int saved=errno;
        (void)pcm_snapshot(out,0); /* retain the post-fault state without another HWSYNC */
        return pcm_fail("SYNC_OBSERVE",saved);
    }
    if(out->state==SNDRV_PCM_STATE_XRUN) return pcm_fail("SYNC_XRUN",EPIPE);
    if(out->state==SNDRV_PCM_STATE_SUSPENDED) return pcm_fail("SYNC_SUSPENDED",ESTRPIPE);
    if(pcm.started && out->state!=SNDRV_PCM_STATE_RUNNING) return pcm_fail("STREAM_STATE",EBADFD);
    return 0;
}
ssize_t pcm_write(const int16_t *data,size_t frames)
{
    struct snd_xferi x;
    struct board_audio_state state;
    if(pcm.error) { errno=pcm.error; return -1; }
    memset(&x,0,sizeof(x)); x.buf=(void *)data; x.frames=frames;
    if(ioctl(pcm.fd,SNDRV_PCM_IOCTL_WRITEI_FRAMES,&x)<0) {
        int saved=errno;
        pcm_record("WRITE_FAIL",(unsigned)frames,-saved);
        if(saved==EAGAIN || saved==EINTR) { errno=saved; return -1; }
        (void)pcm_snapshot(&state,0);
        return pcm_fail("WRITEI_FRAMES",saved);
    }
    if(x.result<0) {
        int saved=(int)-x.result;
        if(saved==EAGAIN || saved==EINTR) { errno=saved; return -1; }
        (void)pcm_snapshot(&state,0); return pcm_fail("WRITEI_RESULT",saved);
    }
    if((size_t)x.result>frames) return pcm_fail("WRITEI_RESULT",EPROTO);
    pcm.config.epoch_transferred+=(unsigned)x.result;
    pcm_record("WRITE_OK",(unsigned)frames,(int)x.result);
    if(!pcm.started) {
        pcm.config.prime_transferred+=(unsigned)x.result;
        if(pcm_observe(&state)<0) { /* accepted frames are still returned below */ }
        else if(state.state==SNDRV_PCM_STATE_RUNNING) {
            if(pcm.config.prime_transferred<pcm.config.prime) pcm_fail("EARLY_AUTO_START",EPROTO);
            else pcm.started=1;
        } else if(state.state==SNDRV_PCM_STATE_PREPARED && state.queued>=pcm.config.prime) {
            int rc,saved;
            ++pcm.config.start_calls;
            rc=ioctl(pcm.fd,SNDRV_PCM_IOCTL_START,0); saved=errno;
            /* START is legal only in PREPARED. A race/already-running result
             * needs a fresh state check, never a blind EBADFD exemption. */
            if(pcm_observe(&state)<0) { }
            else if(state.state==SNDRV_PCM_STATE_RUNNING && (!rc || saved==EBADFD)) {
                if(rc<0) ++pcm.config.start_races;
                pcm.started=1;
            } else pcm_fail(rc<0?"START":"START_STATE",rc<0?saved:EPROTO);
        } else if(state.state!=SNDRV_PCM_STATE_PREPARED) {
            pcm_fail("PRIMING_STATE",EBADFD);
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
    if(ioctl(pcm.fd,SNDRV_PCM_IOCTL_SYNC_PTR,&sync)<0) {
        int saved=errno; struct board_audio_state state;
        (void)pcm_snapshot(&state,0); return pcm_fail("SYNC_AVAIL_MIN",saved);
    }
    pcm_record("AVAIL_MIN",frames,0);
    return 0;
}
int pcm_reset(void)
{
    if(pcm.fd<0) return 0;
    pcm_record("RESET_DROP",0,0);
    if(ioctl(pcm.fd,SNDRV_PCM_IOCTL_DROP,0)<0) return pcm_fail("DROP",errno);
    pcm.started=pcm.error=0; pcm.failure[0]=0;
    pcm.config.prime_transferred=pcm.config.start_calls=pcm.config.start_races=0;
    pcm.config.epoch_transferred=0; ++pcm.config.epoch;
    if(ioctl(pcm.fd,SNDRV_PCM_IOCTL_PREPARE,0)<0) return pcm_fail("PREPARE",errno);
    pcm_record("RESET_PREPARE",0,0);
    return pcm_avail_min(pcm.config.period); /* DRAIN's buffer threshold must not survive resume */
}
int pcm_finish(void)
{
    uint64_t until=board_now_ns()+1000000000u;
    struct pollfd fd={pcm.fd,POLLOUT,0};
    int rc;
    /* Ordinary write readiness must not turn draining into a busy loop. */
    if(pcm_avail_min(pcm.config.buffer)<0) return -1;
    pcm_record("DRAIN_REQUEST",0,0);
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
