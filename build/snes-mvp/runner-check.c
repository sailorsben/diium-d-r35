/* Local ARM/QEMU contract checks; no hardware evidence. */
#include "runner.c"
#include "audio-owner.c"
#include <assert.h>

static uLong sink_crc;
static uint64_t sink_frames;
static unsigned sink_calls;
static int fragmented, reject_once;
static uint8_t machine[64];

int board_open(int mode) { (void)mode; return 0; }
void board_close(void) {}
int board_is_null(void) { return 1; }
const char *board_last_error(void) { return "fixture"; }
int board_video_submit(const void *p,unsigned w,unsigned h,size_t pitch)
{ (void)p; (void)w; (void)h; (void)pitch; return 0; }
void board_wait_display(void) {}
int board_video_reserve(void) { return 0; }
void board_video_cancel(void) {}
void board_video_metrics(struct board_video_metrics *out,int reset)
{ (void)reset; if(out) memset(out,0,sizeof(*out)); }
#ifndef RUNNER_CHECK_CUSTOM_POLL
uint32_t board_poll_input(void) { return 0; }
#endif
int board_audio_open(unsigned rate) { return (int)rate; }
ssize_t board_audio_write(const int16_t *p,size_t frames)
{
    ++sink_calls;
    if(fragmented&&!(sink_calls%5)) { errno=EAGAIN; return -1; }
    if(fragmented&&frames>37) frames=37;
    sink_crc=crc32(sink_crc,(const uint8_t *)p,(uInt)(frames*4));
    sink_frames+=frames; return (ssize_t)frames;
}
int board_audio_queued_frames(void) { return 0; }
int board_audio_reset(void) { return 0; }
int board_audio_wait(unsigned ms) { (void)ms; return 1; }
void board_audio_close(void) {}
int board_audio_observe(struct board_audio_state *out)
{ memset(out,0,sizeof(*out)); out->rate=44100; out->period=128; out->buffer=8192;
  out->prime=2048; out->started=1; out->observed_ns=board_now_ns(); return 0; }
int board_audio_avail_min(unsigned frames) { (void)frames; return 0; }
int board_audio_fd(void) { static int fd=-1; if(fd<0) fd=eventfd(0,EFD_NONBLOCK); return fd; }
int board_audio_finish(void) { return 0; }
uint64_t board_now_ns(void)
{
    struct timespec t; clock_gettime(CLOCK_MONOTONIC,&t);
    return (uint64_t)t.tv_sec*1000000000u+t.tv_nsec;
}
void board_sleep_until(uint64_t ns)
{
    uint64_t now=board_now_ns(); struct timespec t;
    if(now>=ns) return;
    t.tv_sec=(ns-now)/1000000000u; t.tv_nsec=(ns-now)%1000000000u;
    (void)nanosleep(&t,NULL);
}
static size_t fake_state_size(void) { return sizeof(machine); }
static bool fake_serialize(void *p,size_t n)
{ if(n!=sizeof(machine)) return false; memcpy(p,machine,n); return true; }
static bool fake_unserialize(const void *p,size_t n)
{
    if(n!=sizeof(machine)) return false;
    memcpy(machine,p,n);
    if(reject_once) { reject_once=0; return false; }
    return true;
}
static size_t fake_memory_size(unsigned kind)
{ return kind==RETRO_MEMORY_SAVE_RAM?sizeof(machine):0; }
static void *fake_memory(unsigned kind)
{ return kind==RETRO_MEMORY_SAVE_RAM?machine:NULL; }

static void transport_test(int mode,uLong *crc,uint64_t *frames)
{
    int16_t samples[535*2]; unsigned i,j;
    memset(&s,0,sizeof(s)); s.audio_ready=true; s.input_rate=32040;
    audio_pipe_init(); assert(!audio_pipe_start());
    fragmented=mode; sink_calls=0; sink_frames=0; sink_crc=crc32(0,NULL,0);
    for(i=0;i<80;i++) {
        assert(!audio_pipe_space(2048));
        for(j=0;j<ARRAY_SIZE(samples);j++) samples[j]=(int16_t)((i*37+j*97)%65536-32768);
        assert(audio_batch(samples,535)==535);
        pump_audio(); assert(!s.failed);
    }
    audio_pipe_stop(1);pump_audio();
    assert(!s.ring_count&&!s.failed);
    assert(s.enqueued==s.accepted&&s.accepted==sink_frames);
    if(mode) assert(s.partial_writes&&s.again);
    *crc=sink_crc; *frames=sink_frames;
}
int main(int argc,char **argv)
{
    uLong baseline,fragmented_crc; uint64_t baseline_frames,fragmented_frames;
    uint8_t expected[64],*file; size_t n; unsigned i;
    assert(argc==2);
    transport_test(0,&baseline,&baseline_frames);
    transport_test(1,&fragmented_crc,&fragmented_frames);
    assert(baseline==fragmented_crc&&baseline_frames==fragmented_frames);
    {
        uint8_t silence[2048*4]={0}; unsigned phase=s.phase;
        uLong expected_crc=crc32(sink_crc,silence,sizeof(silence));
        fragmented=0; assert(prime_audio());
        audio_pipe_stop(1);pump_audio();
        assert(s.primed==2048&&s.phase==phase&&s.enqueued==baseline_frames);
        assert(s.accepted==baseline_frames+2048&&sink_crc==expected_crc);
    }
    memset(&s,0,sizeof(s)); error_text[0]=0;
    snprintf(s.save_dir,sizeof(s.save_dir),"%s",argv[1]); assert(ensure_directory(s.save_dir));
    snprintf(s.state_path,sizeof(s.state_path),"%s/fixture.state",argv[1]);
    snprintf(s.sram_path,sizeof(s.sram_path),"%s/fixture.srm",argv[1]);
    s.rom_crc=0x12345678;s.core_crc=0x87654321;s.rom_bytes=32768;s.core_bytes=65536;
    p_retro_serialize_size=fake_state_size;p_retro_serialize=fake_serialize;p_retro_unserialize=fake_unserialize;
    p_retro_get_memory_size=fake_memory_size;p_retro_get_memory_data=fake_memory;
    for(i=0;i<sizeof(machine);i++) machine[i]=(uint8_t)(i*13);
    memcpy(expected,machine,sizeof(machine));
    assert(save_state()); memset(machine,0x7f,sizeof(machine));
    assert(load_state()); assert(!memcmp(machine,expected,sizeof(machine)));
    memset(machine,0x5a,sizeof(machine)); memcpy(expected,machine,sizeof(machine)); reject_once=1;
    assert(!load_state()); assert(!memcmp(machine,expected,sizeof(machine))); assert(!s.failed);
    file=read_file(s.state_path,STATE_LIMIT,&n); assert(file&&n==STATE_HEADER+64);
    file[12]^=1; assert(save_file(s.state_path,file,n)); free(file);
    assert(!load_state()); assert(!memcmp(machine,expected,sizeof(machine)));
    assert(save_sram()); memset(machine,0,sizeof(machine)); assert(load_sram());
    assert(!memcmp(machine,expected,sizeof(machine)));
    puts("PASS: partial/EAGAIN transport preserves all PCM; priming independent; snapshot roundtrip; mismatched state rejection; live-state rollback; SRAM roundtrip");
    printf("audio_frames=%llu crc32=%08lx\n",(unsigned long long)baseline_frames,(unsigned long)baseline);
    return 0;
}
