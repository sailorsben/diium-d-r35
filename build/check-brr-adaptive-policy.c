#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

/* The policy cases inject CPU readings. The real DSP arithmetic is exercised
 * by the exact-output replay suite. */
#define INLINE inline
#define BRR_BUF_SIZE 12
static void brr_decode_samples(int32_t *pos, uint32_t word, int32_t header)
{
   for (unsigned i = 0; i < 4; ++i)
      pos[i + BRR_BUF_SIZE] = pos[i] = word + header;
}
#include "snes-brr-adaptive.h"

static void finish_trial(unsigned cached, bool valid, bool uneven)
{
   brr_trial_active = true;
   brr_trial_valid = valid;
   brr_trial_tick = BRR_TRIAL_TICKS;
   for (unsigned i = 0; i < BRR_TRIAL_GROUPS; ++i)
   {
      brr_trial_cpu[i][0] = 10000;
      brr_trial_cpu[i][1] = uneven && i == 2 ? 10500 : cached;
   }
   d35_brr_frame();
   assert(!brr_trial_active);
}

int main(void)
{
   int32_t pos[BRR_BUF_SIZE + 4] = {0};
   brr_decode_observed(pos, 1, 0);
   assert(brr_samples == 1 && pos[0] == 1);
   d35_brr_reset();
   brr_trial_active = true;
   for (unsigned group = 0; group < BRR_TRIAL_GROUPS; ++group)
   {
      unsigned cached[2] = {0, 0};
      for (unsigned i = 0; i < BRR_TRIAL_GROUP_TICKS; ++i)
      {
         brr_trial_tick = group * BRR_TRIAL_GROUP_TICKS + i;
         d35_brr_frame();
         cached[i % 2] += brr_enabled;
      }
      assert(cached[0] == 2 && cached[1] == 2);
   }

   finish_trial(9000, true, false);
   assert(brr_enabled && brr_passes == 1 && brr_wait == BRR_ACTIVE_INTERVAL);
   finish_trial(9900, true, false);
   assert(!brr_enabled && brr_passes == 1 && brr_wait == BRR_FIRST_RETRY);
   finish_trial(9000, true, true);
   assert(!brr_enabled && brr_wait == BRR_FIRST_RETRY * 2);
   finish_trial(9000, false, false);
   assert(!brr_enabled && brr_wait == BRR_MAX_RETRY);
   d35_brr_reset();
   assert(!brr_intercept && !brr_trial_active && brr_wait == 0);
   puts("PASS balanced trials, admission, weak and uneven rejection, missing clock, retry and reset");
   return 0;
}
