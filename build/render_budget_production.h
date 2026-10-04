/* Adaptive rendering from the successful v10 handheld test.
 * Two monotonic reads per core frame; no OSS queries, report bins or file writes.
 * Audio/game CPU remain enabled. Test controls are unset on the handheld. */
#include <time.h>
static unsigned rt9_mode;
static bool rt9_disabled;
static inline uint64_t rt9_now(void)
{
   struct timespec t;
   if (clock_gettime(CLOCK_MONOTONIC, &t)) return 0;
   return (uint64_t)t.tv_sec * 1000000u + t.tv_nsec / 1000u;
}
static uint32_t rb10_draw_us, rb10_skip_us, rb10_credit, rb10_fraction;
static unsigned rb10_forced;
static uint32_t rb10_budget(void)
{
   double fps = native_av.timing.fps;
   return fps > 40 && fps < 70 ? (uint32_t)(920000.0 / fps) : 15333;
}
static void rb10_reset(void)
{
   rb10_draw_us = rb10_skip_us = rb10_credit = rb10_fraction = rb10_forced = 0;
   const char *v = getenv("D35_V10_FORCE_HALF_RENDER");
   if (v && !strcmp(v,"1")) rb10_forced = 512;
}
static unsigned rt9_select_mode(void)
{
   if (rt9_disabled) return 0;
   rb10_credit += rb10_forced ? rb10_forced : rb10_fraction;
   if (rb10_credit >= 1024) { rb10_credit -= 1024; return 1; }
   return 0;
}
static void rb10_observe(unsigned skipped, uint64_t elapsed)
{
   /* Discard exceptional stalls; never adapt the sample rate or game clock. */
   if (!elapsed || elapsed > 100000) return;
   uint32_t *mean = skipped ? &rb10_skip_us : &rb10_draw_us;
   *mean = *mean ? (uint32_t)(((uint64_t)*mean * 7 + elapsed) / 8) : (uint32_t)elapsed;
   uint32_t budget = rb10_budget();
   uint32_t cheap = rb10_skip_us ? rb10_skip_us : rb10_draw_us / 2;
   if (rb10_draw_us <= budget || rb10_draw_us <= cheap) rb10_fraction = 0;
   else {
      rb10_fraction = (uint32_t)(((uint64_t)(rb10_draw_us - budget) * 1024) / (rb10_draw_us - cheap));
      if (rb10_fraction > 512) rb10_fraction = 512;
   }
}
static void rt9_reset(void)
{
   const char *v = getenv("D35_V10_DISABLE");
   rt9_disabled = v && !strcmp(v, "1");
   rt9_mode = 0; rb10_reset();
}
