/* Included after the original BRR arithmetic in apu_blargg.c. */
#include <sys/syscall.h>
#include <time.h>
#include <arm_neon.h>

extern long syscall(long, ...);

enum {
   BRR_CACHE_ENTRIES = 256,
   BRR_PROFILE_BLOCKS = 1024,
   BRR_CAPTURE_FRAMES = 8,
   BRR_ACTIVE_INTERVAL = 120,
   BRR_FIRST_RETRY = 240,
   BRR_MAX_RETRY = 960
};

struct brr_input {
   uint32_t code;
   uint32_t history;
};

struct brr_entry {
   struct brr_input input;
   int32_t output[4];
};

static struct brr_entry brr_cache[BRR_CACHE_ENTRIES];
static struct brr_input brr_trace[BRR_PROFILE_BLOCKS];
static bool brr_allowed = true;
static bool brr_enabled;
static unsigned brr_samples, brr_capture_left, brr_wait, brr_retry;
static unsigned brr_probes, brr_passes, brr_active_frames, brr_last_hits;
static uint64_t brr_probe_cpu, brr_max_probe_cpu;
static volatile uint32_t brr_profile_output;

static INLINE struct brr_input brr_read_input(const int32_t *pos, unsigned word, unsigned header)
{
   /* Bit 24 distinguishes a valid key from an empty entry. End/loop bits
    * affect the caller's address progression, but not these four samples. */
   struct brr_input input = {
      (1u << 24) | ((header & 0xfcu) << 16) | word,
      ((uint32_t)(uint16_t)pos[BRR_BUF_SIZE - 1] << 16) |
         (uint16_t)pos[BRR_BUF_SIZE - 2]
   };
   return input;
}

/* Use the same callable cache path in gameplay and the timing probe. */
static __attribute__((noipa)) bool brr_decode_cached(int32_t *pos, unsigned word, unsigned header)
{
   struct brr_input input = brr_read_input(pos, word, header);
   uint32_t hash = (input.code ^ input.history ^ (input.history >> 15)) * UINT32_C(0x9e3779b9);
   struct brr_entry *entry = &brr_cache[hash >> 24];
   if (entry->input.code == input.code && entry->input.history == input.history)
   {
      int32x4_t samples = vld1q_s32(entry->output);
      vst1q_s32(pos, samples);
      vst1q_s32(pos + BRR_BUF_SIZE, samples);
      return true;
   }

   brr_decode_samples(pos, word, header);
   entry->input = input;
   vst1q_s32(entry->output, vld1q_s32(pos));
   return false;
}

/* The DSP's common path has one predictable branch when profiling is dormant.
 * Keep the sampling and cache lookup out of the original decode loop. */
static bool brr_intercept;

static __attribute__((noinline)) void brr_decode_observed(int32_t *pos, unsigned word,
                                                         unsigned header)
{
   if (brr_samples < BRR_PROFILE_BLOCKS)
      brr_trace[brr_samples++] = brr_read_input(pos, word, header);
   if (brr_enabled)
      brr_decode_cached(pos, word, header);
   else
      brr_decode_samples(pos, word, header);
}

static uint64_t brr_thread_cpu(void)
{
   struct timespec ts;
   if (syscall(SYS_clock_gettime, CLOCK_THREAD_CPUTIME_ID, &ts))
      return 0;
   return (uint64_t)ts.tv_sec * 1000000000u + (unsigned)ts.tv_nsec;
}

/* Run both paths on identical captured inputs. The previous samples occupy
 * the same locations as in the DSP's mirrored buffer. All writes here are
 * scratch writes. The checksum keeps the outputs observable to the compiler. */
static __attribute__((noipa)) unsigned brr_run_trace(bool cached)
{
   int32_t pos[BRR_BUF_SIZE + 4];
   uint32_t output = 0;
   unsigned hits = 0;
   unsigned i;
   for (i = 0; i < BRR_PROFILE_BLOCKS; ++i)
   {
      struct brr_input input = brr_trace[i];
      unsigned word = (uint16_t)input.code;
      unsigned header = (input.code >> 16) & 0xfcu;
      pos[BRR_BUF_SIZE - 1] = (int16_t)(input.history >> 16);
      pos[BRR_BUF_SIZE - 2] = (int16_t)input.history;
      if (cached)
         hits += brr_decode_cached(pos, word, header);
      else
         brr_decode_samples(pos, word, header);
      output += (uint32_t)pos[0] + (uint32_t)pos[1] + (uint32_t)pos[2] + (uint32_t)pos[3];
   }
   brr_profile_output = output;
   return hits;
}

static uint64_t brr_time_trace(bool cached)
{
   uint64_t start, end;
   unsigned hits;
   if (cached)
      memset(brr_cache, 0, sizeof(brr_cache));
   start = brr_thread_cpu();
   if (!start)
      return 0;
   hits = brr_run_trace(cached);
   end = brr_thread_cpu();
   if (cached)
      brr_last_hits = hits;
   return end > start ? end - start : 0;
}

static bool brr_profile_pass(void)
{
   uint64_t start = brr_thread_cpu();
   uint64_t plain1, cached1, cached2, plain2, end;
   ++brr_probes;
   if (!start)
      return false;
   plain1 = brr_time_trace(false);
   cached1 = brr_time_trace(true);
   cached2 = brr_time_trace(true);
   plain2 = brr_time_trace(false);
   end = brr_thread_cpu();
   if (end > start)
   {
      uint64_t cost = end - start;
      brr_probe_cpu += cost;
      if (cost > brr_max_probe_cpu)
         brr_max_probe_cpu = cost;
   }
   /* Demand a margin in both orders. This covers dispatch and real cache
    * pressure omitted by the scratch replay and rejects noisy ties. */
   return brr_last_hits >= BRR_PROFILE_BLOCKS / 4 && plain1 && plain2 && cached1 && cached2 &&
      cached1 < plain1 - plain1 / 8 && cached2 < plain2 - plain2 / 8;
}

void d35_brr_reset(void)
{
   brr_enabled = brr_intercept = false;
   brr_samples = brr_capture_left = brr_wait = 0;
   brr_retry = BRR_FIRST_RETRY;
   brr_probes = brr_passes = brr_active_frames = brr_last_hits = 0;
   brr_probe_cpu = brr_max_probe_cpu = 0;
   /* A cache entry is a pure decode result. The first profile pass clears
    * the table before a new session can use it. */
}

void d35_brr_frame(void)
{
   if (!brr_allowed)
      return;
   if (brr_samples == BRR_PROFILE_BLOCKS)
   {
      brr_enabled = brr_profile_pass();
      brr_samples = brr_capture_left = 0;
      if (brr_enabled)
      {
         ++brr_passes;
         brr_wait = BRR_ACTIVE_INTERVAL;
         brr_retry = BRR_FIRST_RETRY;
      }
      else
      {
         brr_wait = brr_retry;
         if (brr_retry < BRR_MAX_RETRY)
            brr_retry *= 2;
      }
   }
   else if (brr_capture_left)
   {
      if (--brr_capture_left == 0)
      {
         /* Very sparse decode cannot justify keeping the lookup active. */
         brr_samples = 0;
         brr_enabled = false;
         brr_wait = BRR_FIRST_RETRY;
      }
   }
   else if (brr_wait)
      --brr_wait;
   else
      brr_capture_left = BRR_CAPTURE_FRAMES;

   brr_intercept = brr_enabled || brr_capture_left;
   brr_active_frames += brr_enabled;
}

/* The offline replay pair uses these exports to compare identical ELFs. */
__attribute__((visibility("default"))) void d35_brr_set_enabled(bool allowed)
{
   brr_allowed = allowed;
   d35_brr_reset();
}

__attribute__((visibility("default"))) void d35_brr_read(uint64_t *stats)
{
   stats[0] = brr_probes;
   stats[1] = brr_passes;
   stats[2] = brr_active_frames;
   stats[3] = brr_last_hits;
   stats[4] = brr_probe_cpu;
   stats[5] = brr_max_probe_cpu;
}
