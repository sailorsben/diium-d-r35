#define _GNU_SOURCE
#include "board.h"
#include "startup.h"
#include "platform.h"
#include "timing.h"
#ifdef D35_NATIVE_PCM
#include "native-pcm.h"
#endif
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <pthread.h>
#include <poll.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/soundcard.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>

/* These two private ABIs come from the shipped binaries, not generic Linux:
 * driver.so gpChunkMemAlloc/Free and vrtemu gpio_read_io/set_port_attribute.
 * The scaler requires chunk memory, including for an already compact frame. */
#define CHUNK_ALLOC 0xc00c4301u
#define CHUNK_FREE  0x400c4303u
#define GPIO_READ 0x800c4701u
#define GPIO_WRITE 0x400c4700u
#define GPIO_ATTRIBUTE 0x400c4702u
#define SLOT_BYTES (640u * 512u * 2u)
#define SOURCE_SLOTS 3u
#define READY_LIMIT 2u
enum slot_owner { FREE, RESERVED, READY, SCALER };
struct chunk_block { uint32_t physical, mapped, bytes; };
struct gpio_request { uint32_t pin, reserved, value; };
struct button_pin { uint32_t pin, mask; };
static const struct button_pin buttons[] = {
    /* ReadJoystick yields native 10/40/80/20 hex. Stock joystick_input's
     * libretro mask table identifies these as UP/DOWN/LEFT/RIGHT respectively.
     * Native bit positions alone do not identify libretro directions. */
    {0x200,1u<<4}, {0x201,1u<<5}, {0x202,1u<<6}, {0x203,1u<<7},
    {0x204,1u<<8}, {0x205,1u<<0}, {0x30b,1u<<1}, {0x30d,1u<<9},
    {0x30f,1u<<2}, {0x30c,1u<<3}, {0x30a,1u<<10}, {0x208,1u<<11},
    {0x207,1u<<12}, {0x30e,1u<<13}, {0x206,BOARD_MENU}
};
/* Remaining attributes in the original InitJoystick, in its original order.
 * 20f is read by detect_hdmi; 209/20a are volume buttons. The board roles of
 * 20b and 20e are not established. Preserve the observed vendor startup values
 * without inventing output writes or touching /dev/mem. */
static const struct gpio_request startup_attributes[] = {
    {0x20f,0,0}, {0x20b,0,0}, {0x20e,0,1}, {0x209,0,1}, {0x20a,0,1}
};
static struct {
    int opened, null_backend, gpio_fd, chunk_fd, audio_fd, mixer_fd;
    int volume_value;
    int trace_input;
    unsigned input_trace_count;
    uint32_t last_input_pins,last_input_errors;
    unsigned volume_keys;
    unsigned audio_rate;
    unsigned char audio_tail[4];
    size_t audio_tail_bytes;
    struct chunk_block chunk;
    uint8_t *pixels;
    void *driver;
    void **display_handle;
    void (*init_vfb)(int);
    void (*draw_vfb)(uint16_t *, int, int);
    void (*flip_vfb)(void);
    void (*free_vfb)(void);
    void (*video_size)(int *, int *);
    int (*detect_hdmi)(void);
    int *hdmi_output;
    pthread_t worker;
    int worker_started, stopping, busy, first_frame;
    int reserved;
    struct { enum slot_owner owner; unsigned width, height; } slots[SOURCE_SLOTS];
    unsigned queue[READY_LIMIT], queue_head, queue_count;
    struct board_video_metrics metrics;
} b = {.gpio_fd=-1, .chunk_fd=-1, .audio_fd=-1, .mixer_fd=-1};
static pthread_mutex_t display_lock = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t display_condition = PTHREAD_COND_INITIALIZER;
static char error_text[256];

static int failure(const char *format, ...)
{
    va_list args;
    va_start(args, format);
    vsnprintf(error_text, sizeof(error_text), format, args);
    va_end(args);
    return -1;
}

const char *board_last_error(void) { return error_text; }
int board_is_null(void) { return b.null_backend; }

uint64_t board_now_ns(void)
{
    return timing_now_ns();
}

void board_sleep_until(uint64_t deadline_ns)
{
    timing_sleep_until(deadline_ns);
}

static void *display_worker(void *unused)
{
    (void)unused;
    pthread_mutex_lock(&display_lock);
    for (;;) {
        unsigned slot, width, height;
        uint64_t start, duration, cpu_start, cpu_end;
        struct timespec cpu;
        while (!b.queue_count && !b.stopping)
            pthread_cond_wait(&display_condition,&display_lock);
        if (!b.queue_count && b.stopping) break;
        slot=b.queue[b.queue_head]; b.queue_head=(b.queue_head+1)%READY_LIMIT;
        --b.queue_count; b.slots[slot].owner=SCALER; b.busy=1;
        width=b.slots[slot].width; height=b.slots[slot].height;
        pthread_cond_broadcast(&display_condition);
        pthread_mutex_unlock(&display_lock);
        cpu_start=0;
        if(!syscall(SYS_clock_gettime,CLOCK_THREAD_CPUTIME_ID,&cpu))
            cpu_start=(uint64_t)cpu.tv_sec*1000000000u+cpu.tv_nsec;
        start=board_now_ns();
        if(b.first_frame) startup_note("first DrawVFB enter size=%ux%u",width,height);
        b.draw_vfb((uint16_t *)(b.pixels+slot*SLOT_BYTES),(int)width,(int)height);
        duration=board_now_ns()-start;
        pthread_mutex_lock(&display_lock);
        b.slots[slot].owner=FREE; ++b.metrics.scaled;
        b.metrics.scale_ns+=duration;
        if(duration>b.metrics.max_scale_ns) b.metrics.max_scale_ns=duration;
        /* DrawVFB has stopped/completed the scaler's source read. Stock also
         * releases at this boundary; scanout still owns its output buffer. */
        pthread_cond_broadcast(&display_condition);
        pthread_mutex_unlock(&display_lock);
        if(b.first_frame) startup_note("first DrawVFB returned; FlipVFB enter");
        start=board_now_ns();
        b.flip_vfb();
        duration=board_now_ns()-start;
        cpu_end=cpu_start;
        if(!syscall(SYS_clock_gettime,CLOCK_THREAD_CPUTIME_ID,&cpu))
            cpu_end=(uint64_t)cpu.tv_sec*1000000000u+cpu.tv_nsec;
        if(b.first_frame) { startup_note("first FlipVFB returned"); b.first_frame=0; }
        pthread_mutex_lock(&display_lock);
        b.busy=0;
        ++b.metrics.flipped; b.metrics.flip_ns+=duration;
        if(duration>b.metrics.max_flip_ns) b.metrics.max_flip_ns=duration;
        if(cpu_end>=cpu_start) b.metrics.worker_cpu_ns+=cpu_end-cpu_start;
        pthread_cond_broadcast(&display_condition);
    }
    pthread_mutex_unlock(&display_lock);
    return NULL;
}

void board_wait_display(void)
{
    pthread_mutex_lock(&display_lock);
    while (b.busy || b.queue_count) pthread_cond_wait(&display_condition,&display_lock);
    pthread_mutex_unlock(&display_lock);
}

static void mixer_open(void)
{
    int volume=0;
    b.volume_keys=0;
    b.mixer_fd=open("/dev/mixer",O_RDWR|O_CLOEXEC);
    if(b.mixer_fd<0) {
        fprintf(stderr,"board: mixer unavailable: %s\n",strerror(errno));
        return;
    }
    if(ioctl(b.mixer_fd,SOUND_MIXER_READ_PCM,&volume)<0 ||
       !(volume&0xffff) || (volume&~0xffff) ||
       (volume&255)>100 || ((volume>>8)&255)>100) {
        volume=50|(50<<8);
        if(ioctl(b.mixer_fd,SOUND_MIXER_WRITE_PCM,&volume)<0)
            fprintf(stderr,"board: set initial PCM volume: %s\n",strerror(errno));
    }
    b.volume_value=volume;
}

static void poll_volume(void)
{
    struct gpio_request up={0x209,0,1}, down={0x20a,0,1};
    unsigned keys=0, edges;
    int delta=0, left, right, value;
    if(ioctl(b.gpio_fd,GPIO_READ,&up)==0 && up.value==0) keys|=1u;
    if(ioctl(b.gpio_fd,GPIO_READ,&down)==0 && down.value==0) keys|=2u;
    edges=keys&~b.volume_keys;
    b.volume_keys=keys;
    if(edges==1u) delta=10;
    else if(edges==2u) delta=-10;
    if(!delta || b.mixer_fd<0) return;
    left=(b.volume_value&255)+delta;
    right=((b.volume_value>>8)&255)+delta;
    if(left<0) left=0;
    if(left>100) left=100;
    if(right<0) right=0;
    if(right>100) right=100;
    value=left|(right<<8);
    if(ioctl(b.mixer_fd,SOUND_MIXER_WRITE_PCM,&value)==0) b.volume_value=value;
}

int board_open(int null_backend)
{
    size_t i;
    int width=0, height=0, rc;
    const char *driver_path;
    if (b.opened) return failure("Board is already open");
    error_text[0]=0;
    b.null_backend=!!null_backend;
    b.stopping=b.busy=0;
    b.first_frame=1;
    b.reserved=-1; b.queue_head=b.queue_count=0;
    memset(b.slots,0,sizeof(b.slots)); memset(&b.metrics,0,sizeof(b.metrics));
    if (b.null_backend) { b.opened=1; return 0; }
    if (sizeof(void *)!=4) return failure("Device backend requires a 32-bit ARM executable; use explicit --null for host tests");
    if(timing_prepare()<0) { failure("Read kernel monotonic clock: %s",strerror(errno)); goto fail; }
    startup_note("platform heartbeat attach enter");
    if(platform_heartbeat_open()<0) { failure("Attach platform heartbeat: %s",strerror(errno)); goto fail; }
    board_set_input_trace(1);
    startup_note("GPIO open enter");
    b.gpio_fd=open("/dev/gpio",O_RDWR|O_CLOEXEC);
    if (b.gpio_fd<0) { failure("Open /dev/gpio: %s",strerror(errno)); goto fail; }
    for(i=0;i<sizeof(buttons)/sizeof(buttons[0]);++i) {
        struct gpio_request r={buttons[i].pin,0,1};
        startup_note("GPIO input attribute pin=0x%x",r.pin);
        if(ioctl(b.gpio_fd,GPIO_ATTRIBUTE,&r)<0) {
            failure("Configure input pin 0x%x: %s",r.pin,strerror(errno)); goto fail;
        }
    }
    for(i=0;i<sizeof(startup_attributes)/sizeof(startup_attributes[0]);++i) {
        struct gpio_request r=startup_attributes[i];
        startup_note("GPIO vendor attribute pin=0x%x value=%u",r.pin,r.value);
        if(ioctl(b.gpio_fd,GPIO_ATTRIBUTE,&r)<0) {
            failure("Configure vendor startup pin 0x%x: %s",r.pin,strerror(errno)); goto fail;
        }
    }
    startup_note("chunkmem open enter");
    b.chunk_fd=open("/dev/chunkmem",O_RDWR|O_CLOEXEC);
    if (b.chunk_fd<0) { failure("Open /dev/chunkmem: %s",strerror(errno)); goto fail; }
    memset(&b.chunk,0,sizeof(b.chunk));
    b.chunk.bytes=SLOT_BYTES*SOURCE_SLOTS;
    startup_note("chunk allocation enter bytes=%u",b.chunk.bytes);
    if(ioctl(b.chunk_fd,CHUNK_ALLOC,&b.chunk)<0 || !b.chunk.mapped) {
        failure("Allocate display chunk buffers: %s",strerror(errno)); goto fail;
    }
    b.pixels=(uint8_t *)(uintptr_t)b.chunk.mapped;
    memset(b.pixels,0,SLOT_BYTES*SOURCE_SLOTS);
    startup_note("chunk allocation complete");
    driver_path=getenv("D35_MVP_DRIVER");
    if(!driver_path || !*driver_path) driver_path="/usr/retro/driver.so";
    startup_note("display driver load enter path=%s",driver_path);
    b.driver=dlopen(driver_path,RTLD_NOW|RTLD_LOCAL);
    if(!b.driver) { failure("Load display driver: %s",dlerror()); goto fail; }
#define SYMBOL(field,name) do { \
    *(void **)(&b.field)=dlsym(b.driver,name); \
    if(!b.field) { failure("Display driver lacks %s",name); goto fail; } \
} while(0)
    SYMBOL(init_vfb,"InitVFB");
    SYMBOL(draw_vfb,"DrawVFB");
    SYMBOL(flip_vfb,"FlipVFB");
    SYMBOL(free_vfb,"FreeVFB");
    SYMBOL(video_size,"video_driver_get_size");
    SYMBOL(detect_hdmi,"detect_hdmi");
    SYMBOL(display_handle,"hDisp");
    SYMBOL(hdmi_output,"USE_HDMI_OUT");
#undef SYMBOL
    /* The vendor video_drivers_init loses its pthread ID and its deinit only
     * frees the display. Own the worker so shutdown has an actual join. */
    startup_note("display driver symbols resolved; HDMI detection enter");
    *b.hdmi_output=b.detect_hdmi();
    startup_note("HDMI detection complete output=%d; InitVFB enter",*b.hdmi_output);
    *b.display_handle=NULL;
    b.init_vfb(*b.hdmi_output);
    startup_note("InitVFB returned display=%p",*b.display_handle);
    if(!*b.display_handle) { failure("Vendor display initialization failed"); goto fail; }
    b.video_size(&width,&height);
    startup_note("display size=%dx%d",width,height);
    if(width<=0 || height<=0 || width>4096 || height>4096) {
        failure("Invalid display size %dx%d",width,height); goto fail;
    }
    {
        /* vrtemu main -> LCM_LED(1) -> gpio_write_io(0x108,...).
         * LCD backlight is enabled for handheld output, disabled for HDMI. */
        struct gpio_request r={0x108,1,*b.hdmi_output==1?0u:1u};
        startup_note("LCD backlight write enter value=%u",r.value);
        if(ioctl(b.gpio_fd,GPIO_WRITE,&r)<0) {
            failure("Enable LCD backlight: %s",strerror(errno)); goto fail;
        }
    }
    startup_note("display worker create enter");
    rc=pthread_create(&b.worker,NULL,display_worker,NULL);
    if(rc) { failure("Start display worker: %s",strerror(rc)); goto fail; }
    b.worker_started=1;
    startup_note("display worker created; mixer open enter");
    mixer_open();
    startup_note("mixer open complete");
    b.opened=1;
    return 0;
fail:
    startup_note("board error: %s; cleanup enter",error_text);
    board_close();
    return -1;
}

int board_video_reserve(void)
{
    unsigned slot;
    uint64_t began=board_now_ns();
    struct timespec timeout;
    int rc=0;
    if(!b.opened) return failure("Board is closed");
    if(b.null_backend) return 0;
    if(syscall(SYS_clock_gettime,CLOCK_REALTIME,&timeout)<0)
        return failure("Read kernel display timeout clock: %s",strerror(errno));
    timeout.tv_sec+=5;
    pthread_mutex_lock(&display_lock);
    if(b.reserved>=0) { pthread_mutex_unlock(&display_lock); return 0; }
    for(;;) {
        for(slot=0;slot<SOURCE_SLOTS;++slot) if(b.slots[slot].owner==FREE) break;
        if(rc || b.stopping || (slot<SOURCE_SLOTS && b.queue_count<READY_LIMIT)) break;
        rc=pthread_cond_timedwait(&display_condition,&display_lock,&timeout);
    }
    if(rc || b.stopping) {
        pthread_mutex_unlock(&display_lock);
        return failure("Display worker unavailable: %s",rc?strerror(rc):"stopping");
    }
    b.reserved=(int)slot; b.slots[slot].owner=RESERVED;
    b.metrics.reserve_wait_ns+=board_now_ns()-began;
    pthread_mutex_unlock(&display_lock);
    return 0;
}

void board_video_cancel(void)
{
    pthread_mutex_lock(&display_lock);
    if(b.reserved>=0) b.slots[b.reserved].owner=FREE;
    b.reserved=-1;
    pthread_cond_broadcast(&display_condition);
    pthread_mutex_unlock(&display_lock);
}

void board_video_metrics(struct board_video_metrics *out,int reset)
{
    if(reset) board_wait_display();
    pthread_mutex_lock(&display_lock);
    if(out) *out=b.metrics;
    if(reset) memset(&b.metrics,0,sizeof(b.metrics));
    pthread_mutex_unlock(&display_lock);
}

int board_video_submit(const void *rgb565,unsigned width,unsigned height,size_t pitch)
{
    unsigned y,slot;
    uint8_t *target;
    uint64_t start;
    if(!rgb565) { board_video_cancel(); return 0; }
    if(!width || !height || width>640 || height>512 || pitch<(size_t)width*2u)
        return failure("Unsupported RGB565 frame %ux%u pitch %zu",width,height,pitch);
    if(board_video_reserve()<0) return -1;
    if(b.null_backend) return 0;
    slot=(unsigned)b.reserved; target=b.pixels+slot*SLOT_BYTES;
    start=board_now_ns();
    for(y=0;y<height;++y)
        memcpy(target+(size_t)y*width*2u,(const uint8_t *)rgb565+(size_t)y*pitch,(size_t)width*2u);
    pthread_mutex_lock(&display_lock);
    b.metrics.copy_ns+=board_now_ns()-start;
    b.slots[slot].width=width; b.slots[slot].height=height;
    b.slots[slot].owner=READY;
    b.queue[(b.queue_head+b.queue_count)%READY_LIMIT]=slot;
    ++b.queue_count; ++b.metrics.submitted;
    if(b.queue_count>b.metrics.queue_high) b.metrics.queue_high=b.queue_count;
    b.reserved=-1;
    pthread_cond_broadcast(&display_condition);
    pthread_mutex_unlock(&display_lock);
    return 0;
}

uint32_t board_poll_input(void)
{
    size_t i;
    uint32_t result=0, pins_low=0, errors=0;
    if(b.null_backend || b.gpio_fd<0) return 0;
    platform_heartbeat_tick();
    poll_volume();
    for(i=0;i<sizeof(buttons)/sizeof(buttons[0]);++i) {
        struct gpio_request r={buttons[i].pin,0,1};
        if(ioctl(b.gpio_fd,GPIO_READ,&r)!=0) errors|=1u<<i;
        else if(r.value==0) { result|=buttons[i].mask; pins_low|=1u<<i; }
    }
    if((result&((1u<<2)|(1u<<3)))==((1u<<2)|(1u<<3))) {
        result&=~((1u<<2)|(1u<<3));
        result|=BOARD_MENU;
    }
    if(b.trace_input && b.input_trace_count<24 &&
       (pins_low!=b.last_input_pins || errors!=b.last_input_errors)) {
        startup_note("input GPIO low_index_bits=0x%04x keys=0x%05x read_error_bits=0x%04x",pins_low,result,errors);
        b.last_input_pins=pins_low; b.last_input_errors=errors; ++b.input_trace_count;
    }
    return result;
}

void board_set_input_trace(int enabled)
{
    b.trace_input=!!enabled;
    b.input_trace_count=0;
    b.last_input_pins=b.last_input_errors=UINT32_MAX;
}

#ifndef D35_NATIVE_PCM
int board_audio_open(unsigned requested_rate)
{
    int format=AFMT_S16_LE, channels=2, rate, fragments=(4<<16)|11;
    int fragment_hint_result;
    audio_buf_info info;
    if(!b.opened || requested_rate<8000 || requested_rate>96000)
        return failure("Invalid audio open request");
    board_audio_close();
    if(b.null_backend) { b.audio_rate=requested_rate; return (int)requested_rate; }
    rate=(int)requested_rate;
    b.audio_fd=open("/dev/dsp",O_WRONLY|O_NONBLOCK|O_CLOEXEC);
    if(b.audio_fd<0) return failure("Open /dev/dsp: %s",strerror(errno));
    /* A standard OSS request; hardware may round/ignore the fragment hint.
     * Queue reporting below uses the driver's actual byte count. */
    fragment_hint_result=ioctl(b.audio_fd,SNDCTL_DSP_SETFRAGMENT,&fragments);
    if(ioctl(b.audio_fd,SNDCTL_DSP_SETFMT,&format)<0 || format!=AFMT_S16_LE ||
       ioctl(b.audio_fd,SNDCTL_DSP_CHANNELS,&channels)<0 || channels!=2 ||
       ioctl(b.audio_fd,SNDCTL_DSP_SPEED,&rate)<0 || rate<=0) {
        failure("Configure stereo S16_LE OSS audio: %s",strerror(errno));
        board_audio_close(); return -1;
    }
    b.audio_rate=(unsigned)rate;
    if(ioctl(b.audio_fd,SNDCTL_DSP_GETOSPACE,&info)==0)
        fprintf(stderr,"board: OSS %d Hz stereo S16_LE; fragment hint 4x2048 result=%d; actual fragments=%d fragment_bytes=%d capacity_bytes=%lld free_bytes=%d\n",
                rate,fragment_hint_result,info.fragstotal,info.fragsize,
                (long long)info.fragstotal*info.fragsize,info.bytes);
    else
        fprintf(stderr,"board: OSS %d Hz stereo S16_LE; fragment hint 4x2048 result=%d; actual buffer size unavailable: %s\n",
                rate,fragment_hint_result,strerror(errno));
    return rate;
}

ssize_t board_audio_write(const int16_t *samples,size_t frames)
{
    const unsigned char *bytes=(const unsigned char *)samples;
    ssize_t n;
    size_t complete, remainder;
    if(!b.audio_rate) { errno=EBADF; return -1; }
    if(!frames) return 0;
    if(!samples || frames>(size_t)SSIZE_MAX/4u) { errno=EINVAL; return -1; }
    if(b.null_backend) return (ssize_t)frames;
    /* In the unusual case of a byte-granular short write, retain the remainder
     * of the accepted final stereo frame. Caller sees only whole frames. */
    while(b.audio_tail_bytes) {
        n=write(b.audio_fd,b.audio_tail,b.audio_tail_bytes);
        if(n<0 && errno==EINTR) continue;
        if(n<=0) return n;
        b.audio_tail_bytes-=(size_t)n;
        memmove(b.audio_tail,b.audio_tail+n,b.audio_tail_bytes);
    }
    do { n=write(b.audio_fd,bytes,frames*4u); } while(n<0 && errno==EINTR);
    if(n<=0) return n;
    complete=(size_t)n/4u;
    remainder=(size_t)n%4u;
    if(remainder) {
        b.audio_tail_bytes=4u-remainder;
        memcpy(b.audio_tail,bytes+n,b.audio_tail_bytes);
        ++complete;
    }
    return (ssize_t)complete;
}

int board_audio_queued_frames(void)
{
    int queued=0;
    audio_buf_info info;
    if(b.null_backend) return 0;
    if(b.audio_fd<0) return -1;
    if(ioctl(b.audio_fd,SNDCTL_DSP_GETODELAY,&queued)<0) {
        if(ioctl(b.audio_fd,SNDCTL_DSP_GETOSPACE,&info)<0) return -1;
        queued=info.fragstotal*info.fragsize-info.bytes;
    }
    if(queued<0) queued=0;
    /* Main may query while the sole writer retains a partial-byte tail.
     * This is kernel occupancy only, avoiding a race on writer-owned state. */
    return (queued+3)/4;
}

int board_audio_reset(void)
{
    b.audio_tail_bytes=0;
    if(b.null_backend || b.audio_fd<0) return 0;
    if(ioctl(b.audio_fd,SNDCTL_DSP_RESET,0)<0)
        return failure("Reset OSS audio: %s",strerror(errno));
    return 0;
}

int board_audio_wait(unsigned milliseconds)
{
    struct pollfd fd={b.audio_fd,POLLOUT,0};
    int rc;
    if(b.null_backend) return 1;
    do { rc=poll(&fd,1,(int)milliseconds); } while(rc<0 && errno==EINTR);
    if(rc>0 && (fd.revents&(POLLERR|POLLHUP|POLLNVAL))) { errno=EIO; return -1; }
    return rc;
}

void board_audio_close(void)
{
    if(b.audio_fd>=0) {
        (void)ioctl(b.audio_fd,SNDCTL_DSP_RESET,0);
        close(b.audio_fd);
    }
    b.audio_fd=-1;
    b.audio_rate=0;
    b.audio_tail_bytes=0;
}

#else
int board_audio_open(unsigned requested_rate)
{
    int rate;
    if(!b.opened) return failure("Board is not open");
    board_audio_close();
    if(b.null_backend) { b.audio_rate=requested_rate; return (int)requested_rate; }
    rate=pcm_open(requested_rate);
    if(rate<0) return failure("Native PCM configuration: %s",strerror(errno));
    b.audio_rate=(unsigned)rate; return rate;
}
ssize_t board_audio_write(const int16_t *p,size_t frames)
{ return b.null_backend?(ssize_t)frames:pcm_write(p,frames); }
int board_audio_queued_frames(void)
{ struct board_audio_state state; return board_audio_observe(&state)<0?-1:(int)state.queued; }
int board_audio_reset(void) { return b.null_backend?0:pcm_reset(); }
int board_audio_wait(unsigned ms)
{ struct pollfd fd={pcm_fd(),POLLOUT,0}; return b.null_backend?1:poll(&fd,1,(int)ms); }
void board_audio_close(void) { pcm_close(); b.audio_rate=0; }
#endif

int board_audio_observe(struct board_audio_state *out)
{
    memset(out,0,sizeof(*out));
    if(b.null_backend) {
        out->rate=b.audio_rate?b.audio_rate:44100; out->period=128;
        out->buffer=8192; out->prime=2048; out->started=1;
        out->observed_ns=board_now_ns(); return 0;
    }
#ifdef D35_NATIVE_PCM
    return pcm_observe(out);
#else
    { int q=board_audio_queued_frames(); if(q<0) return -1;
      out->rate=b.audio_rate; out->period=512; out->buffer=8192;
      out->prime=2048; out->queued=(unsigned)q; out->started=1;
      out->observed_ns=board_now_ns(); return 0; }
#endif
}
int board_audio_fd(void)
{
#ifdef D35_NATIVE_PCM
    return b.null_backend?-1:pcm_fd();
#else
    return b.null_backend?-1:b.audio_fd;
#endif
}
int board_audio_avail_min(unsigned frames)
{
    if(b.null_backend) return 0;
#ifdef D35_NATIVE_PCM
    return pcm_avail_min(frames);
#else
    (void)frames; return 0;
#endif
}
int board_audio_finish(void)
{
    if(b.null_backend) return 0;
#ifdef D35_NATIVE_PCM
    return pcm_finish();
#else
    return ioctl(b.audio_fd,SNDCTL_DSP_SYNC,0);
#endif
}

void board_close(void)
{
    startup_note("board close enter");
    board_audio_close();
    if(b.mixer_fd>=0) close(b.mixer_fd);
    b.mixer_fd=-1;
    if(b.worker_started) {
        pthread_mutex_lock(&display_lock);
        b.stopping=1;
        pthread_cond_broadcast(&display_condition);
        pthread_mutex_unlock(&display_lock);
        /* Join before freeing any source or scanout buffers. A stuck vendor
         * ioctl must be handled by the process watchdog, never by a UAF. */
        startup_note("display worker join enter busy=%d",b.busy);
        pthread_join(b.worker,NULL);
        startup_note("display worker joined");
        b.worker_started=0;
    }
    if(b.display_handle && *b.display_handle && b.free_vfb) {
        startup_note("FreeVFB enter");
        b.free_vfb();
        startup_note("FreeVFB returned");
        *b.display_handle=NULL;
    }
    if(b.driver) dlclose(b.driver);
    b.driver=NULL;
    b.display_handle=NULL;
    if(b.chunk_fd>=0) {
        if(b.chunk.mapped) (void)ioctl(b.chunk_fd,CHUNK_FREE,&b.chunk);
        close(b.chunk_fd);
    }
    b.chunk_fd=-1;
    memset(&b.chunk,0,sizeof(b.chunk));
    b.pixels=NULL;
    if(b.gpio_fd>=0) close(b.gpio_fd);
    b.gpio_fd=-1;
    b.opened=0;
    b.busy=b.stopping=0;
    platform_heartbeat_close();
    startup_note("board close complete");
}
