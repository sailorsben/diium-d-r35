#define _GNU_SOURCE
#include "snes-mvp/board.h"
#include "snes-mvp/timing.h"
#include "snes-mvp/startup.h"
#include "snes-mvp/platform.h"
#include "snes-mvp/ui.h"
#include "platform-lab-kernels.h"
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <sched.h>
#include <pthread.h>
#include <signal.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/ioctl.h>
#include <sys/soundcard.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define NS 1000000000ull
#define PERIOD 16688155ull
#define AUDIO_SAMPLES 2048u
static volatile sig_atomic_t stopped;
static int journal=-1, null_backend, quick, fixture_stall;
static uint64_t deadline_ns=60*NS;
static const char *output;
static volatile uint32_t sink;
static struct lab_tile tiles[LAB_TILES];
static struct lab_palette palettes[8];
static struct lab_cache cache;
static uint16_t canvas[UI_WIDTH*UI_HEIGHT], image[256*224];
static uint16_t screens[64*64];
static uint8_t depths[64*64];
static void stop_signal(int sig) { (void)sig; stopped=1; }
static uint64_t cpu_now(void)
{
    struct timespec t={0,0};
    if(syscall(SYS_clock_gettime,CLOCK_THREAD_CPUTIME_ID,&t)<0) return 0;
    return (uint64_t)t.tv_sec*NS+t.tv_nsec;
}
static void path(char *dst,size_t size,const char *name)
{ snprintf(dst,size,"%s/%s",output,name); }
static void record(const char *format,...)
{
    char line[4096]; int n; size_t done=0; va_list args;
    va_start(args,format); n=vsnprintf(line,sizeof(line)-2,format,args); va_end(args);
    if(n<0 || n>=(int)sizeof(line)-2) _exit(90);
    line[n++]='\n';
    while(done<(size_t)n) {
        ssize_t r=write(journal,line+done,(size_t)n-done);
        if(r<0 && errno==EINTR) continue;
        if(r<=0) _exit(90);
        done+=(size_t)r;
    }
    if(fsync(journal)<0) _exit(90);
}
static void copy_file(FILE *f,const char *name,size_t limit)
{
    char buf[1024]; int fd=open(name,O_RDONLY|O_NONBLOCK|O_CLOEXEC);
    fprintf(f,"\n--- %s ---\n",name);
    if(fd<0) { fprintf(f,"unavailable errno=%d\n",errno); return; }
    while(limit) {
        ssize_t n=read(fd,buf,limit<sizeof(buf)?limit:sizeof(buf));
        if(n<0 && errno==EINTR) continue;
        if(n<=0) { if(n<0) fprintf(f,"read_errno=%d\n",errno); break; }
        fwrite(buf,1,(size_t)n,f); limit-=(size_t)n;
    }
    close(fd);
}
static void snapshot(const char *name,int inventory)
{
    char dest[512],src[256],kernel[32768]; unsigned i,j; FILE *f;
    path(dest,sizeof(dest),name); f=fopen(dest,"w");
    if(!f) { record("event=snapshot_error name=%s errno=%d",name,errno); return; }
    fprintf(f,"version=lab1 kernel_ns=%llu\n",(unsigned long long)timing_now_ns());
    copy_file(f,"/proc/sys/kernel/random/boot_id",128);
    copy_file(f,"/proc/uptime",128); copy_file(f,"/proc/stat",4096);
    copy_file(f,"/proc/meminfo",4096); copy_file(f,"/proc/interrupts",8192);
    copy_file(f,"/proc/self/status",4096);
    if(inventory) {
        const char *fields[]={"level","type","size","coherency_line_size","ways_of_associativity"};
        copy_file(f,"/proc/cpuinfo",4096); copy_file(f,"/proc/cmdline",4096);
        copy_file(f,"/proc/version",4096);
        copy_file(f,"/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq",128);
        copy_file(f,"/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_cur_freq",128);
        copy_file(f,"/sys/kernel/debug/clk/clk_summary",16384);
        for(i=0;i<4;++i) for(j=0;j<sizeof(fields)/sizeof(fields[0]);++j) {
            snprintf(src,sizeof(src),"/sys/devices/system/cpu/cpu0/cache/index%u/%s",i,fields[j]);
            copy_file(f,src,128);
        }
        /* Existence/format discovery only; never enable tracefs events. */
        copy_file(f,"/sys/kernel/tracing/trace_clock",1024);
        copy_file(f,"/sys/kernel/debug/tracing/trace_clock",1024);
    }
    {
        int n=(int)syscall(SYS_syslog,3,kernel,sizeof(kernel));
        fprintf(f,"\n--- kernel ring read-only ---\n");
        if(n>0) fwrite(kernel,1,(size_t)n,f); else fprintf(f,"unavailable errno=%d\n",errno);
    }
    if(fflush(f)<0 || fsync(fileno(f))<0) { fclose(f); _exit(90); }
    fclose(f);
}
static int notice(const char *title,const char *message)
{
    unsigned x,y;
    ui_draw_notice(canvas,UI_WIDTH,title,message);
    for(y=0;y<224;++y) for(x=0;x<256;++x)
        image[y*256+x]=canvas[(y*UI_HEIGHT/224)*UI_WIDTH+x*UI_WIDTH/256];
    if(board_video_submit(image,256,224,512)<0) return -1;
    board_wait_display(); return 0;
}
static void fixture(void)
{
    unsigned t,i,p;
    for(t=0;t<LAB_TILES;++t) {
        tiles[t].generation=1;
        for(i=0;i<64;++i) tiles[t].index[i]=(uint8_t)((i*7+t*3+(i>>3))&15);
    }
    for(p=0;p<8;++p) {
        palettes[p].generation=1;
        for(i=0;i<16;++i) palettes[p].color[i]=(uint16_t)((i*3917+p*1877)&65535);
    }
}
static int kernel_check(void)
{
    uint16_t a[64],b[64],c[64]; uint8_t da[64],db[64],dc[64]; unsigned n,i;
    fixture(); memset(&cache,0,sizeof(cache));
    for(n=0;n<12000;++n) {
        unsigned t=(n*17)&1023,p=(n>>2)&7; int flip=n&1;
        if(n%17==0) { tiles[t].index[n&63]^=3; ++tiles[t].generation; }
        if(n%23==0) { palettes[p].color[n&15]^=0x528a; ++palettes[p].generation; }
        if(n%997==0) memset(&cache,0,sizeof(cache)); /* load/reset flush */
        for(i=0;i<64;++i) { a[i]=(uint16_t)(n+i*129); da[i]=(uint8_t)((n+i)%9); }
        memcpy(b,a,sizeof(a)); memcpy(c,a,sizeof(a));
        memcpy(db,da,sizeof(da)); memcpy(dc,da,sizeof(da));
        lab_scalar(&tiles[t],&palettes[p],flip,a,da);
        lab_neon(&tiles[t],&palettes[p],flip,b,db);
        lab_cached(&cache,&tiles[t],t,&palettes[p],p,flip,c,dc);
        if(memcmp(a,b,sizeof(a)) || memcmp(a,c,sizeof(a)) ||
           memcmp(da,db,sizeof(da)) || memcmp(da,dc,sizeof(da))) return -1;
    }
    /* Force genuine hits, and independently dirty a tile then a palette. */
    for(n=0;n<300;++n) {
        if(n==100) { tiles[0].index[7]^=15; ++tiles[0].generation; }
        if(n==200) { palettes[0].color[1]^=65535; ++palettes[0].generation; }
        memset(a,0,sizeof(a)); memset(da,0,sizeof(da));
        memcpy(c,a,sizeof(a)); memcpy(dc,da,sizeof(da));
        lab_scalar(&tiles[0],&palettes[0],n&1,a,da);
        lab_cached(&cache,&tiles[0],0,&palettes[0],0,n&1,c,dc);
        if(memcmp(a,c,sizeof(a)) || memcmp(da,dc,sizeof(da))) return -1;
    }
    return 0;
}
static void kernel_bench(void)
{
    unsigned scenario,mode,n; const char *names[]={"scalar","neon","color_cache"};
    fixture();
    for(scenario=0;scenario<3 && !stopped;++scenario) for(mode=0;mode<3;++mode) {
        uint64_t start,cpustart,elapsed,cpu; uint32_t checksum=0;
        fixture(); memset(&cache,0,sizeof(cache)); memset(screens,0,sizeof(screens));
        memset(depths,0,sizeof(depths));
        start=timing_now_ns(); cpustart=cpu_now();
        for(n=0;n<1048576;++n) {
            unsigned t=scenario==1?(n&1023):(n&7),p=(n>>3)&7,slot=n&63;
            uint16_t *s=screens+slot*64; uint8_t *d=depths+slot*64;
            if(scenario==2 && !(n&31)) { palettes[p].color[1]^=0x528a; ++palettes[p].generation; }
            /* Vary current priority every draw, including occluded rows. */
            memset(d,(n>>6)%9,64);
            if(mode==0) lab_scalar(&tiles[t],&palettes[p],n&1,s,d);
            else if(mode==1) lab_neon(&tiles[t],&palettes[p],n&1,s,d);
            else lab_cached(&cache,&tiles[t],t,&palettes[p],p,n&1,s,d);
            checksum+=s[n&63];
            if(!(n&255)) {
                platform_heartbeat_tick();
                if(stopped || timing_now_ns()-start>=(quick?20000000ull:200000000ull)) { ++n; break; }
            }
        }
        elapsed=timing_now_ns()-start; cpu=cpu_now()-cpustart; sink^=checksum;
        record("event=kernel mode=%s scenario=%u draws=%u wall_ns=%llu cpu_ns=%llu hits=%llu misses=%llu cache_bytes=%zu checksum=%u",
            names[mode],scenario,n,(unsigned long long)elapsed,(unsigned long long)cpu,
            (unsigned long long)cache.hits,(unsigned long long)cache.misses,sizeof(cache),checksum);
    }
}
/* Byte offsets survive arbitrary short writes and EAGAIN. Used by real OSS
 * service and a hostile transport fixture; no rounding into stereo frames. */
typedef ssize_t (*writer_fn)(int,const void *,size_t);
static int send_pending(int fd,const unsigned char *data,size_t length,size_t *offset,writer_fn writer)
{
    ssize_t n=writer(fd,data+*offset,length-*offset);
    if(n<0 && (errno==EAGAIN || errno==EINTR)) return 0;
    if(n<=0 || (size_t)n>length-*offset) { if(n>=0) errno=EIO; return -1; }
    *offset+=(size_t)n; return 1;
}
static unsigned char fake_output[4096]; static size_t fake_count; static unsigned fake_calls;
static ssize_t fake_writer(int fd,const void *p,size_t n)
{
    size_t take; (void)fd;
    if(++fake_calls%3==0) { errno=EAGAIN; return -1; }
    if(fake_calls%7==0) { errno=EINTR; return -1; }
    take=(fake_calls%19)+1; if(take>n) take=n;
    memcpy(fake_output+fake_count,p,take); fake_count+=take; return (ssize_t)take;
}
static int transport_check(void)
{
    unsigned char input[4096]; unsigned i; size_t off=0;
    fake_count=fake_calls=0;
    for(i=0;i<sizeof(input);++i) input[i]=(unsigned char)(i*13+17);
    while(off<sizeof(input)) if(send_pending(0,input,sizeof(input),&off,fake_writer)<0) return -1;
    return fake_count==sizeof(input) && !memcmp(input,fake_output,sizeof(input))?0:-1;
}
struct audio_sample {
    uint64_t begin,end,accepted;
    int delay_rc,delay_errno,delay,space_rc,space_errno,free_bytes;
    int ptr_rc,ptr_errno,ptr_bytes,ptr,blocks;
};
struct audio_run {
    int fd,rate,fragment,capacity; volatile int stop;
    pthread_t thread; int started,failed;
    uint64_t accepted,cpu_ns,max_gap,shorts,eagain,polls,zero_samples;
    unsigned samples,phase;
    struct audio_sample sample[AUDIO_SAMPLES];
};
static void sample_audio(struct audio_run *a)
{
    audio_buf_info space; count_info ptr; struct audio_sample *s;
    if(a->samples==AUDIO_SAMPLES) return;
    s=&a->sample[a->samples++]; memset(s,0,sizeof(*s));
    s->begin=timing_now_ns(); s->accepted=a->accepted;
    s->delay_rc=ioctl(a->fd,SNDCTL_DSP_GETODELAY,&s->delay); s->delay_errno=s->delay_rc<0?errno:0;
    s->space_rc=ioctl(a->fd,SNDCTL_DSP_GETOSPACE,&space); s->space_errno=s->space_rc<0?errno:0;
    if(!s->space_rc) s->free_bytes=space.bytes;
    s->ptr_rc=ioctl(a->fd,SNDCTL_DSP_GETOPTR,&ptr); s->ptr_errno=s->ptr_rc<0?errno:0;
    if(!s->ptr_rc) { s->ptr_bytes=ptr.bytes; s->ptr=ptr.ptr; s->blocks=ptr.blocks; }
    s->end=timing_now_ns();
    if(a->accepted && s->delay_rc==0 && s->delay==0) ++a->zero_samples;
}
static void *audio_worker(void *arg)
{
    struct audio_run *a=arg; int16_t tone[256]; size_t off=sizeof(tone);
    uint64_t cpu=cpu_now(),last=0,next=0; unsigned i;
    while(!__atomic_load_n(&a->stop,__ATOMIC_ACQUIRE) && !stopped) {
        uint64_t now=timing_now_ns(); int r;
        if(now>=next) { sample_audio(a); next=now+5000000ull; }
        if(off==sizeof(tone)) {
            for(i=0;i<128;++i) {
                int v; a->phase=(a->phase+400u)%((unsigned)a->rate);
                v=(int)(a->phase*2400u/(unsigned)a->rate);
                if(v>1200) v=2400-v;
                tone[i*2]=tone[i*2+1]=(int16_t)(v-600);
            }
            off=0;
        }
        {
            size_t before=off;
            r=send_pending(a->fd,(unsigned char *)tone,sizeof(tone),&off,write);
            if(r>0) {
                now=timing_now_ns(); a->accepted+=off-before;
                if(off<sizeof(tone)) ++a->shorts;
                if(last && now-last>a->max_gap) a->max_gap=now-last;
                last=now;
            }
        }
        if(r<0) { a->failed=errno?errno:EIO; break; }
        if(!r) {
            struct pollfd p={a->fd,POLLOUT,0}; uint64_t began=timing_now_ns();
            if(errno==EINTR) continue;
            ++a->eagain; ++a->polls;
            r=poll(&p,1,2);
            if(r<0 && errno!=EINTR) { a->failed=errno; break; }
            if(r>0 && (p.revents&(POLLERR|POLLHUP|POLLNVAL))) { a->failed=EIO; break; }
            /* POLLOUT can be immediate while a tiny write still gets EAGAIN. */
            if(timing_now_ns()-began<1000000ull) timing_sleep_until(began+1000000ull);
        }
    }
    sample_audio(a); a->cpu_ns=cpu_now()-cpu; return NULL;
}
static int audio_open(struct audio_run *a,unsigned requested,int service)
{
    int fmt=AFMT_S16_LE,channels=2,fragments=(4<<16)|11,rc;
    audio_buf_info info;
    memset(a,0,sizeof(*a)); a->fd=-1; a->rate=(int)requested;
    if(null_backend) { record("event=audio_skipped reason=null_backend requested=%u",requested); return 1; }
    a->fd=open("/dev/dsp",O_WRONLY|O_NONBLOCK|O_CLOEXEC);
    if(a->fd<0) { record("event=audio_open_error requested=%u errno=%d",requested,errno); return -1; }
    rc=ioctl(a->fd,SNDCTL_DSP_SETFRAGMENT,&fragments);
    record("event=audio_hint requested=%u rc=%d errno=%d",requested,rc,rc<0?errno:0);
    if(ioctl(a->fd,SNDCTL_DSP_SETFMT,&fmt)<0 || fmt!=AFMT_S16_LE ||
       ioctl(a->fd,SNDCTL_DSP_CHANNELS,&channels)<0 || channels!=2 ||
       ioctl(a->fd,SNDCTL_DSP_SPEED,&a->rate)<0 || a->rate<8000 || a->rate>96000) {
        record("event=audio_config_error requested=%u errno=%d format=%d channels=%d rate=%d",requested,errno,fmt,channels,a->rate);
        close(a->fd); a->fd=-1; return -1;
    }
    rc=ioctl(a->fd,SNDCTL_DSP_GETOSPACE,&info);
    if(!rc) { a->fragment=info.fragsize; a->capacity=info.fragstotal*info.fragsize; }
    record("event=audio_config requested=%u accepted_rate=%d space_rc=%d errno=%d fragment_bytes=%d capacity_bytes=%d",requested,a->rate,rc,rc<0?errno:0,a->fragment,a->capacity);
    if(service) {
        rc=pthread_create(&a->thread,NULL,audio_worker,a);
        if(rc) { close(a->fd); a->fd=-1; return -1; }
        a->started=1;
    }
    return 0;
}
static void audio_close(struct audio_run *a,const char *name)
{
    char dest[512],leaf[128]; FILE *f; unsigned i;
    if(a->started) { __atomic_store_n(&a->stop,1,__ATOMIC_RELEASE); pthread_join(a->thread,NULL); }
    if(a->fd<0) return;
    ioctl(a->fd,SNDCTL_DSP_RESET,0); close(a->fd); a->fd=-1;
    record("event=audio_end name=\"%s\" accepted_bytes=%llu worker_cpu_ns=%llu max_write_gap_ns=%llu short_writes=%llu eagain=%llu zero_delay_samples=%llu error=%d samples=%u",
        name,(unsigned long long)a->accepted,(unsigned long long)a->cpu_ns,(unsigned long long)a->max_gap,
        (unsigned long long)a->shorts,(unsigned long long)a->eagain,(unsigned long long)a->zero_samples,a->failed,a->samples);
    snprintf(leaf,sizeof(leaf),"audio-%s.csv",name); path(dest,sizeof(dest),leaf); f=fopen(dest,"w");
    if(!f) _exit(90);
    fputs("begin_ns,end_ns,accepted_bytes,delay_rc,delay_errno,delay_bytes,space_rc,space_errno,free_bytes,ptr_rc,ptr_errno,ptr_bytes,ptr,blocks\n",f);
    for(i=0;i<a->samples;++i) {
        struct audio_sample *s=&a->sample[i];
        fprintf(f,"%llu,%llu,%llu,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n",
            (unsigned long long)s->begin,(unsigned long long)s->end,(unsigned long long)s->accepted,
            s->delay_rc,s->delay_errno,s->delay,s->space_rc,s->space_errno,s->free_bytes,
            s->ptr_rc,s->ptr_errno,s->ptr_bytes,s->ptr,s->blocks);
    }
    if(fflush(f)<0 || fsync(fileno(f))<0) _exit(90);
    fclose(f);
}
static void wake_test(void)
{
    unsigned i,n=quick?10:200; uint64_t start=timing_now_ns(),sum=0,max=0;
    for(i=1;i<=n && !stopped;++i) {
        uint64_t deadline=start+i*5000000ull,now,late;
        timing_sleep_until(deadline); now=timing_now_ns(); late=now>deadline?now-deadline:0;
        sum+=late; if(late>max) max=late; platform_heartbeat_tick();
    }
    record("event=wake requested_ns=5000000 samples=%u sum_late_ns=%llu max_late_ns=%llu",i-1,(unsigned long long)sum,(unsigned long long)max);
}
static void cpu_work(uint64_t duration,int sliced)
{
    uint64_t start=cpu_now(),next=start+1000000ull,now; uint32_t v=sink; unsigned i;
    do {
        for(i=0;i<4096;++i) v=(v*1664525u+1013904223u)^i;
        now=cpu_now();
        if(sliced && now>=next) { sched_yield(); next=now+1000000ull; }
    } while(now-start<duration && !stopped);
    sink=v;
}
static int pipeline(const char *name,int sound,int display,int load,int sliced)
{
    struct audio_run a; struct board_video_metrics m;
    uint64_t start,deadline,end,cpu,late_max=0,wall_max=0,late=0;
    unsigned frames=0; uint32_t previous=board_poll_input();
    int audio_rc=1;
    if(notice(name,"AUTO TEST / MENU TO STOP")<0) return -1;
    record("event=phase_begin name=\"%s\" kernel_ns=%llu",name,(unsigned long long)timing_now_ns());
    if(sound) { audio_rc=audio_open(&a,44100,1); if(audio_rc<0) return -1; }
    board_video_metrics(&m,1); start=timing_now_ns(); deadline=start; cpu=cpu_now();
    while(!stopped && timing_now_ns()-start<(quick?150000000ull:4*NS)) {
        uint64_t frame_start=timing_now_ns(),over;
        uint32_t keys=board_poll_input();
        if((keys&BOARD_MENU) && !(previous&BOARD_MENU)) { stopped=1; break; }
        previous=keys; platform_heartbeat_tick();
        if(frame_start>deadline) { over=frame_start-deadline; ++late; if(over>late_max) late_max=over; }
        if(load) cpu_work(12000000ull,sliced);
        if(display) {
            unsigned x,y;
            for(y=198;y<216;++y) for(x=0;x<256;++x)
                image[y*256+x]=x<frames%256?0x571b:0x0843;
            image[220*256+(frames%256)]=0xffff;
            if(board_video_submit(image,256,224,512)<0) { stopped=1; break; }
        }
        over=timing_now_ns()-frame_start; if(over>wall_max) wall_max=over;
        ++frames; deadline+=PERIOD; timing_sleep_until(deadline);
    }
    end=timing_now_ns(); cpu=cpu_now()-cpu;
    board_wait_display(); board_video_metrics(&m,0);
    {
    uint64_t drained=timing_now_ns();
    if(sound && !audio_rc) audio_close(&a,name);
    record("event=pipeline name=\"%s\" frames=%u active_ns=%llu producer_cpu_ns=%llu frame_wall_max_ns=%llu late_samples=%llu max_late_ns=%llu submitted=%llu scaled=%llu flipped=%llu reserve_ns=%llu copy_ns=%llu scale_ns=%llu flip_ns=%llu worker_cpu_ns=%llu max_scale_ns=%llu max_flip_ns=%llu queue_high=%u drain_ns=%llu",
        name,frames,(unsigned long long)(end-start),(unsigned long long)cpu,(unsigned long long)wall_max,
        (unsigned long long)late,(unsigned long long)late_max,(unsigned long long)m.submitted,
        (unsigned long long)m.scaled,(unsigned long long)m.flipped,(unsigned long long)m.reserve_wait_ns,
        (unsigned long long)m.copy_ns,(unsigned long long)m.scale_ns,(unsigned long long)m.flip_ns,
        (unsigned long long)m.worker_cpu_ns,(unsigned long long)m.max_scale_ns,(unsigned long long)m.max_flip_ns,
        m.queue_high,(unsigned long long)(drained-end));
    }
    snapshot("latest-platform.txt",0);
    record("event=phase_end name=\"%s\" kernel_ns=%llu",name,(unsigned long long)timing_now_ns());
    if(sound && !audio_rc && a.failed) return -1;
    return 0;
}
static int run_suite(void)
{
    char startup[512]; struct audio_run a; unsigned i;
    const unsigned rates[]={32000,32040,44100,48000};
    signal(SIGTERM,stop_signal); signal(SIGINT,stop_signal);
    path(startup,sizeof(startup),"startup.log"); setenv("D35_MVP_STARTUP_LOG",startup,1); startup_begin();
    record("event=run_begin version=lab1 pid=%ld null=%d kernel_ns=%llu",(long)getpid(),null_backend,(unsigned long long)timing_now_ns());
    if(fixture_stall) for(;;) pause();
    snapshot("inventory.txt",1);
    if(kernel_check()<0 || transport_check()<0) { record("event=selftest status=failed"); return 2; }
    record("event=selftest status=passed cases=12300 transport_bytes=4096");
    if(board_open(null_backend)<0) { record("event=board_error message=%s",board_last_error()); return 3; }
    board_set_input_trace(0);
    if(notice("D-R35 HARDWARE LAB","AUTO TEST / ABOUT 30 SECONDS")<0) goto fail;
    record("event=phase_begin name=kernels"); kernel_bench(); record("event=phase_end name=kernels");
    if(stopped) goto done;
    notice("CLOCK AND AUDIO","CHECKING NEGOTIATED RATES"); wake_test();
    for(i=0;i<sizeof(rates)/sizeof(rates[0]) && !stopped;++i)
        if(!audio_open(&a,rates[i],0)) audio_close(&a,"rate_probe");
    if(!stopped && pipeline("DISPLAY ONLY",0,1,0,0)<0) goto fail;
    if(!stopped && pipeline("AUDIO ONLY",1,0,0,0)<0) goto fail;
    if(!stopped && pipeline("AUDIO AND DISPLAY",1,1,0,0)<0) goto fail;
    if(!stopped && pipeline("CPU BURST",1,1,1,0)<0) goto fail;
    if(!stopped && pipeline("CPU SLICES",1,1,1,1)<0) goto fail;
done:
    record("event=cleanup_begin cancelled=%d",!!stopped);
    notice(stopped?"TEST STOPPED":"TEST COMPLETE","RESULTS SAVED / RETURNING TO STOCK");
    board_close(); snapshot("final-platform.txt",0);
    record("event=run_end status=%s kernel_ns=%llu",stopped?"cancelled":"complete",(unsigned long long)timing_now_ns());
    return 0;
fail:
    record("event=run_error message=%s",board_last_error()); board_close(); return 4;
}
static int supervise(void)
{
    pid_t child; int status; uint64_t start=timing_now_ns(); int term=0,killed=0;
    record("event=supervisor_begin deadline_ns=%llu",(unsigned long long)deadline_ns); child=fork();
    if(child<0) return 5;
    if(!child) { int result=run_suite(); close(journal); _exit(result); }
    for(;;) {
        pid_t r=waitpid(child,&status,WNOHANG); uint64_t elapsed=timing_now_ns()-start;
        if(r==child) {
            record("event=supervisor_end child=%ld status=%d term=%d killed=%d",(long)child,status,term,killed);
            return term?72:(WIFEXITED(status)?WEXITSTATUS(status):6);
        }
        if(r<0 && errno!=EINTR) return 6;
        if(!term && elapsed>=deadline_ns) {
            char src[256],dest[512]; FILE *f;
            path(dest,sizeof(dest),"timeout-child.txt"); f=fopen(dest,"w");
            if(f) {
                snprintf(src,sizeof(src),"/proc/%ld/status",(long)child); copy_file(f,src,4096);
                snprintf(src,sizeof(src),"/proc/%ld/wchan",(long)child); copy_file(f,src,512);
                snprintf(src,sizeof(src),"/proc/%ld/stack",(long)child); copy_file(f,src,4096);
                fflush(f); fsync(fileno(f)); fclose(f);
            }
            snapshot("timeout-platform.txt",0);
            record("event=deadline child=%ld action=term",(long)child); kill(child,SIGTERM); term=1;
        }
        if(!killed && elapsed>=deadline_ns+(null_backend?100000000ull:3*NS)) {
            record("event=deadline child=%ld action=kill",(long)child); kill(child,SIGKILL); killed=1;
        }
        /* Never return to another display owner while a D-state child lives.
         * Once forced termination was needed, wrapper requests a reboot. */
        timing_sleep_until(timing_now_ns()+100000000ull);
    }
}
int main(int argc,char **argv)
{
    char dest[512]; int i,mode=0;
    for(i=1;i<argc;++i) {
        if(!strcmp(argv[i],"--selftest")) mode=1;
        else if(!strcmp(argv[i],"--null")) null_backend=1;
        else if(!strcmp(argv[i],"--quick")) quick=1;
        else if(!strcmp(argv[i],"--supervise")) mode=2;
        else if(!strcmp(argv[i],"--fixture-stall")) fixture_stall=1;
        else if(!strcmp(argv[i],"--deadline-ms") && i+1<argc) {
            const char *p=argv[++i]; unsigned value=0;
            if(!*p) return 1;
            for(;*p;++p) {
                if(*p<'0' || *p>'9' || value>60000) return 1;
                value=value*10u+(unsigned)(*p-'0');
            }
            if(value<20 || value>60000) return 1;
            deadline_ns=(uint64_t)value*1000000ull;
        }
        else if(!strcmp(argv[i],"--output") && i+1<argc) output=argv[++i];
        else { fprintf(stderr,"Unknown option: %s\n",argv[i]); return 1; }
    }
    if((fixture_stall || deadline_ns!=60*NS) && (!null_backend || mode!=2)) return 1;
    if(mode==1) {
        if(kernel_check()<0 || transport_check()<0) return 2;
        puts("PASS: 12300 tile/depth/flip/invalidation cases and byte-exact hostile transport"); return 0;
    }
    if(!output || strlen(output)>350 || (!null_backend && mode!=2)) return 1;
    path(dest,sizeof(dest),"results.log"); journal=open(dest,O_WRONLY|O_CREAT|O_APPEND|O_CLOEXEC,0644);
    if(journal<0 || !timing_now_ns() || !cpu_now()) return 1;
    i=mode==2?supervise():run_suite(); close(journal); return i;
}
