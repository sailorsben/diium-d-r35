#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#include <errno.h>
#include <stdarg.h>
#include <assert.h>
#include <time.h>
#include <dlfcn.h>
#include <sys/ioctl.h>
#include <linux/soundcard.h>
static void *display_driver = (void *)0x35;
static int fake_dsp = 9;
static unsigned queries, delay_queries, space_queries;
static int queue_value = 512;
static bool unsupported;
static int probe_ioctl(int fd, unsigned long cmd, ...)
{
   va_list ap; void *p;
   assert(fd == 9); ++queries;
   va_start(ap, cmd); p = va_arg(ap, void *); va_end(ap);
   assert(cmd == SOUND_PCM_READ_RATE || cmd == SOUND_PCM_READ_CHANNELS ||
          cmd == SOUND_PCM_READ_BITS || cmd == SNDCTL_DSP_GETOSPACE ||
          cmd == SNDCTL_DSP_GETODELAY);
   if (cmd == SNDCTL_DSP_GETODELAY) ++delay_queries;
   if (cmd == SNDCTL_DSP_GETOSPACE) ++space_queries;
   if (unsupported) { errno = ENOTTY; return -1; }
   if (cmd == SOUND_PCM_READ_RATE) *(int *)p = 44100;
   if (cmd == SOUND_PCM_READ_CHANNELS) *(int *)p = 2;
   if (cmd == SOUND_PCM_READ_BITS) *(int *)p = 16;
   if (cmd == SNDCTL_DSP_GETODELAY) *(int *)p = queue_value;
   if (cmd == SNDCTL_DSP_GETOSPACE)
      *(audio_buf_info *)p = (audio_buf_info){3,4,2048,7168};
   return 0;
}
static void *probe_dlsym(void *handle, const char *name)
{ assert(handle == (void *)0x35 && !strcmp(name,"DSP")); return &fake_dsp; }
#define ioctl probe_ioctl
#define dlsym probe_dlsym
#include "device_audio_capture_v6.h"
#include "audio_diagnostics_v6_capture.h"
#undef ioctl
#undef dlsym
int main(void)
{
   struct diag_audio_mark m;
   capture_reset();
   int16_t chunk[16];
   uint64_t sent=0;
   for (unsigned block=0; block<34000; ++block) {
      for (unsigned i=0; i<8; ++i) {
         chunk[2*i]=(int16_t)(sent+i); chunk[2*i+1]=(int16_t)(-(int)(sent+i));
      }
      capture_feed(chunk,8,block+1,sent); sent+=8;
   }
   assert(capture_count==CAPTURE_FRAMES);
   assert(capture_first_output_frame==sent-CAPTURE_FRAMES);
   setenv("D35_CAPTURE_DIRECTORY",".",1);
   assert(capture_write());
   FILE *wav=fopen("emu_sfc_plus_v6_audio.wav","rb"); assert(wav);
   assert(!fseek(wav,44,SEEK_SET));
   for (uint64_t i=sent-CAPTURE_FRAMES; i<sent; ++i) {
      int16_t pair[2]; assert(fread(pair,4,1,wav)==1);
      assert(pair[0]==(int16_t)i && pair[1]==(int16_t)(-(int)i));
   }
   assert(fgetc(wav)==EOF); fclose(wav);
   capture_reset();
   capture_feed(chunk,8,1,0); assert(capture_count==8 && capture_write());
   setenv("D35_CAPTURE_DIRECTORY","/missing-d35-directory",1);
   assert(!capture_write() && capture_error!=0);
   capture_reset();
   puts("PASS rolling capture preserves exact latest samples across wrap; partial save and write errors verified");
   diag_reset(); errno = EAGAIN;
   m = diag_audio_before();
   assert(m.queue == 512 && errno == EAGAIN && queries == 5);
   queue_value = 4096; diag_audio_after(m, 30, 736);
   assert(diag_rate == 44100 && diag_channels == 2 && diag_bits == 16);
   assert(diag_fragment_size == 2048 && diag_buffer_bytes == 8192);
   assert(diag_bins[0].calls == 1 && diag_bins[0].frames == 736);
   assert(diag_bins[0].low == 1 && diag_bins[0].empty == 0);
   assert(diag_event_count == 1 && diag_events[0].before == 512 && diag_events[0].after == 4096);
   /* Unknown queries never change device configuration and are not retried. */
   unsupported = true; queries = delay_queries = space_queries = 0;
   diag_reset(); assert(diag_queue() == -1 && diag_queue() == -1);
   assert(queries == 5 && delay_queries == 1 && space_queries == 1);
   assert(diag_rate == -1 && diag_delay_support == -1 && diag_space_support == -1);
   /* Preserve the first anomalies and the chronological rolling tail. */
   unsupported = false; diag_reset(); queue_value = 0;
   for (unsigned i=1; i<=3000; ++i) {
      m = diag_audio_before(); m.gap = 30000;
      diag_audio_after(m, i, 736);
   }
   assert(diag_event_count == 3000 && diag_events[0].run == 1);
   assert(diag_events[1023].run == 1024);
   assert(diag_events[1024 + ((3000-2048)%1024)].run == 1977);
   diag_frame_done(3000, diag_now()); diag_video_done(3000, diag_now());
   assert(sizeof(diag_bins)+sizeof(diag_events) < 100000);
   setenv("D35_TIMING_LOG", "diagnostics-mock.log", 1); diag_dump();
   assert(!diag_dirty);
   /* Periodic output must happen without serialize, deinit or exit. */
   diag_reset(); queue_value=512;
   setenv("D35_DIAG_INTERVAL_MS","100",1);
   setenv("D35_TIMING_LOG","periodic-mock.log",1);
   int original_priority=getpriority(PRIO_PROCESS,0);
   diag_worker_start(); assert(!diag_worker_error);
   m=diag_audio_before(); diag_audio_after(m,30,736);
   bool found=false;
   for (unsigned i=0; i<100; ++i) {
      FILE *report=fopen("periodic-mock.log","r");
      if (report) { char line[512]; assert(fgets(line,sizeof(line),report)); fclose(report);
         if (strstr(line,"run=30;")) { found=true; break; } }
      usleep(10000);
   }
   assert(found && getpriority(PRIO_PROCESS,0)==original_priority);
   /* A busy snapshot lock drops measurements; it never blocks gameplay. */
   pthread_mutex_lock(&diag_mutex);
   uint64_t began=diag_now();
   diag_frame_done(30,began); diag_video_done(30,began);
   assert(diag_now()-began<10000);
   pthread_mutex_unlock(&diag_mutex);
   assert(__atomic_load_n(&diag_skipped,__ATOMIC_RELAXED)>=2);
   began=diag_now(); diag_worker_stop();
   assert(diag_now()-began<1000000);
   puts("PASS periodic report before exit/save; no gameplay wait; worker joins promptly");
   puts("PASS diagnostic: read-only queries, unsupported fallback, queue measurements, bounded ordered event retention");
   return 0;
}
