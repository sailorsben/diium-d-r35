/* Read-only OSS queries; no audio writes or device configuration here.
 * Linux UAPI: https://github.com/torvalds/linux/blob/master/include/uapi/linux/soundcard.h
 * Bounded RAM snapshots are saved by a low-priority worker every 10 seconds.
 */
#include <time.h>
#include <linux/soundcard.h>
#include <pthread.h>
#include <sys/resource.h>
#include <fcntl.h>
#include <unistd.h>
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
static pthread_mutex_t diag_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t diag_dump_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t diag_control_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t diag_control_cond = PTHREAD_COND_INITIALIZER;
static pthread_t diag_worker;
static bool diag_worker_running, diag_stop;
static uint32_t diag_skipped;
static int diag_worker_error;
static void diag_worker_stop(void);

struct diag_snapshot {
   struct diag_bin bins[DIAG_BINS];
   struct diag_event events[DIAG_EVENTS];
   uint32_t event_count, last_run, max_bin, skipped;
   int rate, channels, bits, device_seen, delay_support, space_support;
   int fragment_size, buffer_bytes, worker_error;
};
static struct diag_snapshot diag_saved;
static bool diag_try_lock(void)
{
   if (!pthread_mutex_trylock(&diag_mutex)) return true;
   __atomic_fetch_add(&diag_skipped, 1, __ATOMIC_RELAXED);
   return false; /* Never wait for the reporter in the gameplay callbacks. */
}

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
   diag_worker_stop();
   pthread_mutex_lock(&diag_mutex);
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
   diag_skipped = 0; diag_worker_error = 0;
   pthread_mutex_unlock(&diag_mutex);
}
static int diag_queue(void)
{
   int fd, queued, saved_errno = errno;
   audio_buf_info space;
   if (!diag_try_lock()) return -1;
   if (!diag_dsp_pointer && display_driver)
      *(void **)(&diag_dsp_pointer) = dlsym(display_driver, "DSP");
   if (!diag_dsp_pointer || (fd = *diag_dsp_pointer) < 0) {
      pthread_mutex_unlock(&diag_mutex); errno = saved_errno; return -1;
   }
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
         pthread_mutex_unlock(&diag_mutex); errno = saved_errno; return queued;
      }
      diag_delay_support = -1;
   }
   if (diag_space_support > 0 && !ioctl(fd, SNDCTL_DSP_GETOSPACE, &space) &&
       space.bytes >= 0 && space.bytes <= diag_buffer_bytes) {
      queued = diag_buffer_bytes - space.bytes;
      pthread_mutex_unlock(&diag_mutex); errno = saved_errno; return queued;
   }
   pthread_mutex_unlock(&diag_mutex); errno = saved_errno; return -1;
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
   struct diag_bin *b;
   diag_previous_audio_end = end;
   if (!diag_try_lock()) return;
   b = diag_bin_for(run);
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
   pthread_mutex_unlock(&diag_mutex);
}
static void diag_frame_done(uint32_t run, uint64_t start)
{
   uint32_t us = diag_duration(diag_now(), start);
   if (!diag_try_lock()) return;
   diag_max(&diag_bin_for(run)->max_run_us, us);
   pthread_mutex_unlock(&diag_mutex);
}
static void diag_video_done(uint32_t run, uint64_t start)
{
   uint32_t us = diag_duration(diag_now(), start);
   if (!diag_try_lock()) return;
   diag_max(&diag_bin_for(run)->max_video_us, us);
   pthread_mutex_unlock(&diag_mutex);
}
static void diag_dump(void)
{
   const char *path; char temporary[1100], directory[1100]; FILE *f; unsigned i, count;
   int error = 0;
   struct diag_snapshot *s = &diag_saved;
   pthread_mutex_lock(&diag_dump_mutex);
   pthread_mutex_lock(&diag_mutex);
   if (!diag_dirty) { pthread_mutex_unlock(&diag_mutex); pthread_mutex_unlock(&diag_dump_mutex); return; }
   memcpy(s->bins, diag_bins, sizeof(diag_bins));
   memcpy(s->events, diag_events, sizeof(diag_events));
   s->event_count=diag_event_count; s->last_run=diag_last_run; s->max_bin=diag_max_bin;
   s->skipped=__atomic_load_n(&diag_skipped,__ATOMIC_RELAXED);
   s->rate=diag_rate; s->channels=diag_channels; s->bits=diag_bits;
   s->device_seen=diag_device_seen; s->delay_support=diag_delay_support; s->space_support=diag_space_support;
   s->fragment_size=diag_fragment_size; s->buffer_bytes=diag_buffer_bytes; s->worker_error=diag_worker_error;
   diag_dirty = false;
   pthread_mutex_unlock(&diag_mutex); /* All disk I/O occurs after releasing the gameplay lock. */
   path = getenv("D35_TIMING_LOG");
   if (!path) path = "/usr/retro/emu_sfc_plus_v4_timing.log";
   if (snprintf(temporary,sizeof(temporary),"%s.tmp",path) >= (int)sizeof(temporary)) { error=1; goto done; }
   f = fopen(temporary, "w");
   if (!f) { error=1; goto done; }
   fprintf(f, "D-R35 v4 diagnostic; run=%u; RAM storage bytes=%u; all device queries read-only; skipped_measurements=%u; worker_error=%d\n",
      s->last_run, (unsigned)(sizeof(diag_bins) + sizeof(diag_events) + sizeof(diag_saved)), s->skipped, s->worker_error);
   fprintf(f, "device_seen=%d rate=%d channels=%d bits=%d getodelay=%d getospace=%d fragment=%d capacity_bytes=%d\n",
      s->device_seen, s->rate, s->channels, s->bits, s->delay_support,
      s->space_support, s->fragment_size, s->buffer_bytes);
   fprintf(f, "Unsupported values are -1. Queue zero is an observation, not proof of an underrun. Times include pause/menu gaps. Last bin aggregates beyond run 307200.\n");
   fprintf(f, "bin,first_us,last_us,calls,output_frames,empty_before,under_10ms_before,min_queue_bytes,max_queue_bytes,max_gap_us,max_write_us,max_run_us,max_video_us\n");
   for (i = 0; i <= s->max_bin; ++i) {
      const struct diag_bin *b = &s->bins[i];
      if (!b->calls) continue;
      fprintf(f, "%u,%llu,%llu,%u,%u,%u,%u,%d,%d,%u,%u,%u,%u\n", i,
         (unsigned long long)b->first_us, (unsigned long long)b->last_us,
         b->calls, b->frames, b->empty, b->low,
         b->min_queue == INT32_MAX ? -1 : b->min_queue, b->max_queue,
         b->max_gap_us, b->max_write_us, b->max_run_us, b->max_video_us);
   }
   count = s->event_count < DIAG_EVENTS ? s->event_count : DIAG_EVENTS;
   fprintf(f, "events_total=%u retained=%u\nrun,ms,gap_us,write_us,frames,queue_before_bytes,queue_after_bytes\n", s->event_count, count);
   for (i = 0; i < count; ++i) {
      unsigned slot = i;
      if (i >= 1024 && s->event_count > DIAG_EVENTS)
         slot = 1024 + ((s->event_count - DIAG_EVENTS + i - 1024) % 1024);
      const struct diag_event *e = &s->events[slot];
      fprintf(f, "%u,%u,%u,%u,%u,%d,%d\n", e->run, e->ms, e->gap_us,
         e->write_us, e->frames, e->before, e->after);
   }
   if (fflush(f) || ferror(f) || fsync(fileno(f))) error = 1;
   if (fclose(f)) error = 1;
   if (!error && rename(temporary, path)) error = 1;
   /* Flush the rename when supported. Preserve the preceding complete report
    * until the replacement contents have been flushed successfully. */
   if (!error && strlen(path) < sizeof(directory)) {
      char *slash; int fd;
      strcpy(directory,path); slash=strrchr(directory,'/');
      if (slash) { if (slash == directory) slash[1]=0; else *slash=0; }
      else strcpy(directory,".");
      fd=open(directory,O_RDONLY|O_DIRECTORY);
      if (fd >= 0) { (void)fsync(fd); close(fd); }
   }
done:
   if (error) {
      pthread_mutex_lock(&diag_mutex); diag_dirty=true; pthread_mutex_unlock(&diag_mutex);
   }
   pthread_mutex_unlock(&diag_dump_mutex);
}

static void *diag_worker_main(void *unused)
{
   unsigned interval_ms = 10000;
   const char *test = getenv("D35_DIAG_INTERVAL_MS");
   (void)unused;
   if (test) {
      unsigned n=0; const char *c=test;
      while (*c >= '0' && *c <= '9' && n <= 60000) { n=n*10+(unsigned)(*c-'0'); ++c; }
      if (!*c && n>=100 && n<=60000) interval_ms=n;
   }
   (void)setpriority(PRIO_PROCESS,0,19);
   pthread_mutex_lock(&diag_control_mutex);
   while (!diag_stop) {
      struct timespec deadline; int result=0;
      clock_gettime(CLOCK_REALTIME,&deadline);
      deadline.tv_sec += interval_ms/1000;
      deadline.tv_nsec += (interval_ms%1000)*1000000L;
      if (deadline.tv_nsec>=1000000000L) { ++deadline.tv_sec; deadline.tv_nsec-=1000000000L; }
      while (!diag_stop && result != ETIMEDOUT) {
         result=pthread_cond_timedwait(&diag_control_cond,&diag_control_mutex,&deadline);
         if (result && result != ETIMEDOUT) break;
      }
      if (diag_stop) break;
      pthread_mutex_unlock(&diag_control_mutex);
      if (result && result != ETIMEDOUT) {
         pthread_mutex_lock(&diag_mutex); diag_worker_error=result; pthread_mutex_unlock(&diag_mutex);
         diag_dump(); return NULL;
      }
      diag_dump();
      pthread_mutex_lock(&diag_control_mutex);
   }
   pthread_mutex_unlock(&diag_control_mutex);
   return NULL;
}
static void diag_worker_start(void)
{
   pthread_attr_t attr; int result;
   if (diag_worker_running) return;
   diag_stop=false;
   result=pthread_attr_init(&attr);
   if (!result) {
      result=pthread_attr_setstacksize(&attr,128*1024);
      if (!result) result=pthread_create(&diag_worker,&attr,diag_worker_main,NULL);
      pthread_attr_destroy(&attr);
   }
   pthread_mutex_lock(&diag_mutex); diag_worker_error=result; pthread_mutex_unlock(&diag_mutex);
   diag_worker_running=result==0;
}
static void diag_worker_stop(void)
{
   if (!diag_worker_running) return;
   pthread_mutex_lock(&diag_control_mutex); diag_stop=true;
   pthread_cond_signal(&diag_control_cond); pthread_mutex_unlock(&diag_control_mutex);
   pthread_join(diag_worker,NULL); diag_worker_running=false;
}
