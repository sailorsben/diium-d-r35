/* Read-only OSS queries; no audio writes or device configuration here.
 * Linux UAPI: https://github.com/torvalds/linux/blob/master/include/uapi/linux/soundcard.h
 * Measurements stay in bounded RAM until serialization/unload/deinit.
 */
#include <time.h>
#include <linux/soundcard.h>
#define DIAG_BINS 512u
#define DIAG_EVENTS 2048u
struct diag_bin {
   uint32_t calls, frames, empty, low;
   uint32_t max_gap_us, max_write_us, max_run_us, max_video_us;
   int32_t min_queue, max_queue;
   uint64_t first_us, last_us;
};
struct diag_event {
   uint32_t run, ms, gap_us, write_us, frames;
   int32_t before, after;
};
struct diag_audio_mark { uint64_t start; uint32_t gap; int32_t queue; };
static struct diag_bin diag_bins[DIAG_BINS];
static struct diag_event diag_events[DIAG_EVENTS];
static uint64_t diag_epoch, diag_previous_audio_end;
static uint32_t diag_event_count, diag_last_run, diag_max_bin;
static int *diag_dsp_pointer;
static int diag_rate = -1, diag_channels = -1, diag_bits = -1;
static int diag_delay_support, diag_space_support, diag_device_seen;
static int diag_fragment_size = -1, diag_buffer_bytes = -1;
static bool diag_dirty;

static uint64_t diag_now(void)
{
   struct timespec ts;
   if (clock_gettime(CLOCK_MONOTONIC, &ts)) return 0;
   return (uint64_t)ts.tv_sec * 1000000u + ts.tv_nsec / 1000u;
}
static uint32_t diag_duration(uint64_t end, uint64_t begin)
{
   uint64_t us = end >= begin ? end - begin : 0;
   return us > UINT32_MAX ? UINT32_MAX : (uint32_t)us;
}
static void diag_max(uint32_t *p, uint32_t value) { if (*p < value) *p = value; }
static struct diag_bin *diag_bin_for(uint32_t run)
{
   unsigned bin = run ? (run - 1) / 600 : 0;
   if (bin >= DIAG_BINS) bin = DIAG_BINS - 1;
   if (diag_max_bin < bin) diag_max_bin = bin;
   return &diag_bins[bin];
}
static void diag_reset(void)
{
   unsigned i;
   memset(diag_bins, 0, sizeof(diag_bins));
   memset(diag_events, 0, sizeof(diag_events));
   for (i = 0; i < DIAG_BINS; ++i) {
      diag_bins[i].min_queue = INT32_MAX;
      diag_bins[i].max_queue = -1;
   }
   diag_epoch = diag_now(); diag_previous_audio_end = 0;
   diag_event_count = diag_last_run = diag_max_bin = 0;
   diag_dsp_pointer = NULL;
   diag_rate = diag_channels = diag_bits = -1;
   diag_delay_support = diag_space_support = diag_device_seen = 0;
   diag_fragment_size = diag_buffer_bytes = -1;
   diag_dirty = false;
}
static int diag_queue(void)
{
   int fd, queued, saved_errno = errno;
   audio_buf_info space;
   if (!diag_dsp_pointer && display_driver)
      *(void **)(&diag_dsp_pointer) = dlsym(display_driver, "DSP");
   if (!diag_dsp_pointer || (fd = *diag_dsp_pointer) < 0) { errno = saved_errno; return -1; }
   if (!diag_device_seen) {
      diag_device_seen = 1;
      if (ioctl(fd, SOUND_PCM_READ_RATE, &diag_rate)) diag_rate = -1;
      if (ioctl(fd, SOUND_PCM_READ_CHANNELS, &diag_channels)) diag_channels = -1;
      if (ioctl(fd, SOUND_PCM_READ_BITS, &diag_bits)) diag_bits = -1;
      if (!ioctl(fd, SNDCTL_DSP_GETOSPACE, &space) &&
          space.fragstotal > 0 && space.fragsize > 0 &&
          space.fragstotal <= INT32_MAX / space.fragsize) {
         diag_space_support = 1;
         diag_fragment_size = space.fragsize;
         diag_buffer_bytes = space.fragstotal * space.fragsize;
      } else diag_space_support = -1;
   }
   if (diag_delay_support >= 0) {
      queued = -1;
      if (!ioctl(fd, SNDCTL_DSP_GETODELAY, &queued) && queued >= 0) {
         diag_delay_support = 1;
         errno = saved_errno; return queued;
      }
      diag_delay_support = -1;
   }
   if (diag_space_support > 0 && !ioctl(fd, SNDCTL_DSP_GETOSPACE, &space) &&
       space.bytes >= 0 && space.bytes <= diag_buffer_bytes) {
      queued = diag_buffer_bytes - space.bytes;
      errno = saved_errno; return queued;
   }
   errno = saved_errno; return -1;
}
static struct diag_audio_mark diag_audio_before(void)
{
   struct diag_audio_mark m;
   m.queue = diag_queue(); m.start = diag_now();
   m.gap = diag_previous_audio_end ? diag_duration(m.start, diag_previous_audio_end) : 0;
   return m;
}
static void diag_audio_after(struct diag_audio_mark m, uint32_t run, uint32_t frames)
{
   uint64_t end = diag_now();
   uint32_t write_us = diag_duration(end, m.start);
   int after = diag_queue();
   struct diag_bin *b = diag_bin_for(run);
   diag_previous_audio_end = end;
   if (!b->calls) b->first_us = m.start - diag_epoch;
   b->last_us = end - diag_epoch; ++b->calls; b->frames += frames;
   diag_max(&b->max_gap_us, m.gap); diag_max(&b->max_write_us, write_us);
   if (m.queue >= 0) {
      if (m.queue < b->min_queue) b->min_queue = m.queue;
      if (m.queue > b->max_queue) b->max_queue = m.queue;
      if (m.queue == 0) ++b->empty;
      if (m.queue < 1764) ++b->low; /* under 10 ms at 44.1 kHz stereo s16 */
   }
   /* Keep initial anomalies and a rolling tail. Empty-queue samples at most
    * twice a second so an unhelpful driver cannot swamp all timing events. */
   if (m.gap > 25000 || write_us > 5000 ||
       (m.queue >= 0 && m.queue < 1764 && !(run % 30))) {
      unsigned n = diag_event_count++;
      unsigned slot = n < 1024 ? n : 1024 + ((n - 1024) % 1024);
      diag_events[slot] = (struct diag_event){run,
         (uint32_t)((end - diag_epoch) / 1000), m.gap, write_us, frames, m.queue, after};
   }
   diag_last_run = run; diag_dirty = true;
}
static void diag_frame_done(uint32_t run, uint64_t start)
{ diag_max(&diag_bin_for(run)->max_run_us, diag_duration(diag_now(), start)); }
static void diag_video_done(uint32_t run, uint64_t start)
{ diag_max(&diag_bin_for(run)->max_video_us, diag_duration(diag_now(), start)); }
static void diag_dump(void)
{
   const char *path; FILE *f; unsigned i, count;
   if (!diag_dirty) return;
   path = getenv("D35_TIMING_LOG");
   f = fopen(path ? path : "/usr/retro/emu_sfc_plus_v3_timing.log", "w");
   if (!f) return;
   fprintf(f, "D-R35 v3 diagnostic; run=%u; RAM bytes=%u; all device queries read-only\n",
      diag_last_run, (unsigned)(sizeof(diag_bins) + sizeof(diag_events)));
   fprintf(f, "device_seen=%d rate=%d channels=%d bits=%d getodelay=%d getospace=%d fragment=%d capacity_bytes=%d\n",
      diag_device_seen, diag_rate, diag_channels, diag_bits, diag_delay_support,
      diag_space_support, diag_fragment_size, diag_buffer_bytes);
   fprintf(f, "Unsupported values are -1. Queue zero is an observation, not proof of an underrun. Times include pause/menu gaps. Last bin aggregates beyond run 307200.\n");
   fprintf(f, "bin,first_us,last_us,calls,output_frames,empty_before,under_10ms_before,min_queue_bytes,max_queue_bytes,max_gap_us,max_write_us,max_run_us,max_video_us\n");
   for (i = 0; i <= diag_max_bin; ++i) {
      const struct diag_bin *b = &diag_bins[i];
      if (!b->calls) continue;
      fprintf(f, "%u,%llu,%llu,%u,%u,%u,%u,%d,%d,%u,%u,%u,%u\n", i,
         (unsigned long long)b->first_us, (unsigned long long)b->last_us,
         b->calls, b->frames, b->empty, b->low,
         b->min_queue == INT32_MAX ? -1 : b->min_queue, b->max_queue,
         b->max_gap_us, b->max_write_us, b->max_run_us, b->max_video_us);
   }
   count = diag_event_count < DIAG_EVENTS ? diag_event_count : DIAG_EVENTS;
   fprintf(f, "events_total=%u retained=%u\nrun,ms,gap_us,write_us,frames,queue_before_bytes,queue_after_bytes\n", diag_event_count, count);
   for (i = 0; i < count; ++i) {
      unsigned slot = i;
      if (i >= 1024 && diag_event_count > DIAG_EVENTS)
         slot = 1024 + ((diag_event_count - DIAG_EVENTS + i - 1024) % 1024);
      const struct diag_event *e = &diag_events[slot];
      fprintf(f, "%u,%u,%u,%u,%u,%d,%d\n", e->run, e->ms, e->gap_us,
         e->write_us, e->frames, e->before, e->after);
   }
   if (fclose(f) == 0) diag_dirty = false;
}
