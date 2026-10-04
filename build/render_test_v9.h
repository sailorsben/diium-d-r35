/* Bounded A/B test. No disk writes or threads during gameplay. */
#include <time.h>
#include <linux/soundcard.h>
#define RT9_BINS 90u
struct rt9_bin {
   uint64_t first_us, last_us, audio_frames, run_us, video_us;
   uint32_t calls, max_run_us, max_write_us, max_gap_us, draws, duplicates;
   int32_t queue_min, queue_max;
   unsigned queue_queries;
};
static struct rt9_bin rt9_bins[RT9_BINS];
static uint64_t rt9_runs, rt9_previous_audio_end;
static unsigned rt9_mode;
static bool rt9_disabled;
static int *rt9_dsp;
static uint64_t rt9_now(void)
{
   struct timespec t;
   if (clock_gettime(CLOCK_MONOTONIC, &t)) return 0;
   return (uint64_t)t.tv_sec * 1000000u + t.tv_nsec / 1000u;
}
static struct rt9_bin *rt9_current(void)
{
   uint64_t n = rt9_runs / 120u;
   return &rt9_bins[n < RT9_BINS ? n : RT9_BINS - 1];
}
static unsigned rt9_select_mode(void)
{ return !rt9_disabled && rt9_runs >= 1800 && rt9_runs < 3000; }
static void rt9_max(uint32_t *p, uint64_t value)
{ if (value > UINT32_MAX) value = UINT32_MAX; if (*p < value) *p = (uint32_t)value; }
static void rt9_reset(void)
{
   unsigned i;
   memset(rt9_bins, 0, sizeof(rt9_bins));
   for (i = 0; i < RT9_BINS; ++i) rt9_bins[i].queue_min = rt9_bins[i].queue_max = -1;
   rt9_runs = rt9_previous_audio_end = 0; rt9_mode = 0; rt9_dsp = NULL;
   const char *v = getenv("D35_V9_DISABLE");
   rt9_disabled = v && !strcmp(v, "1");
}
static uint64_t rt9_audio_before(void)
{
   uint64_t now = rt9_now();
   struct rt9_bin *b = rt9_current();
   if (rt9_previous_audio_end && now >= rt9_previous_audio_end)
      rt9_max(&b->max_gap_us, now - rt9_previous_audio_end);
   /* Query the existing OSS stream once per 60 runs. Never open another stream. */
   if (!(rt9_runs % 60u) && display_driver) {
      int queued = -1;
      if (!rt9_dsp) *(void **)(&rt9_dsp) = dlsym(display_driver, "DSP");
      if (rt9_dsp && *rt9_dsp >= 0 && !ioctl(*rt9_dsp, SNDCTL_DSP_GETODELAY, &queued) && queued >= 0) {
         if (b->queue_min < 0 || queued < b->queue_min) b->queue_min = queued;
         if (queued > b->queue_max) b->queue_max = queued;
         ++b->queue_queries;
      }
   }
   return rt9_now();
}
static void rt9_audio_after(uint64_t start, unsigned frames)
{
   uint64_t end = rt9_now();
   struct rt9_bin *b = rt9_current();
   b->audio_frames += frames;
   if (end >= start) rt9_max(&b->max_write_us, end - start);
   rt9_previous_audio_end = end;
}
static void rt9_save(void)
{
   const char *path = getenv("D35_V9_REPORT");
   char temp[1100]; unsigned i; FILE *f;
   if (!path || !*path) path = "/usr/retro/emu_sfc_plus_v9_render_test.txt";
   if (snprintf(temp, sizeof(temp), "%s.tmp", path) >= (int)sizeof(temp)) return;
   f = fopen(temp, "w"); if (!f) return;
   fprintf(f, "D-R35 v9 core-render A/B; runs=%llu; test_disabled=%u; rate=44100; no playback disk writes\n",
      (unsigned long long)rt9_runs, rt9_disabled);
   fprintf(f, "Runs 0-1799 normal; 1800-2999 core rendering off (audio/game CPU on); 3000+ normal. Schedule restarts after successful state load/reset.\n");
   fprintf(f, "Last bin aggregates beyond run 10800. Queue is sampled, not an underrun counter. Wall times include menus/pauses.\n");
   fprintf(f, "bin,render_off,calls,wall_us,audio_frames,run_total_us,max_run_us,video_total_us,draws,duplicates,max_write_us,max_gap_us,queue_min_bytes,queue_max_bytes,queue_queries\n");
   for (i = 0; i < RT9_BINS; ++i) {
      struct rt9_bin *b = &rt9_bins[i];
      if (!b->calls) continue;
      fprintf(f, "%u,%u,%u,%llu,%llu,%llu,%u,%llu,%u,%u,%u,%u,%d,%d,%u\n",
         i, !rt9_disabled && i >= 15 && i < 25, b->calls,
         (unsigned long long)(b->last_us - b->first_us),
         (unsigned long long)b->audio_frames, (unsigned long long)b->run_us,
         b->max_run_us, (unsigned long long)b->video_us, b->draws, b->duplicates,
         b->max_write_us, b->max_gap_us, b->queue_min, b->queue_max, b->queue_queries);
   }
   bool okay = fflush(f) == 0 && !ferror(f);
   if (okay) okay = fsync(fileno(f)) == 0;
   if (fclose(f)) okay = false;
   if (okay) (void)rename(temp, path);
}
