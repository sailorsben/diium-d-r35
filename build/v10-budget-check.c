#include "emu_sfc_plus_v10_budget.c"
#include <assert.h>
static size_t mock_size(void) { return 4; }
static bool mock_restore(const void *d, size_t n) { (void)d; return n == 4; }
int main(void)
{
   native_av.timing.fps = 59.922743404;
   rt9_reset();
   unsigned skips = 0; uint64_t work = 0;
   for (unsigned i=0; i<2400; ++i) {
      unsigned skip = rt9_select_mode(); int mask;
      rt9_mode = skip;
      assert(environment(RETRO_ENVIRONMENT_GET_AUDIO_VIDEO_ENABLE,&mask) && (mask & 2));
      uint32_t duration = skip ? 6752 : 19958;
      rb10_observe(skip,duration); ++rt9_runs;
      if (i>=400) { skips += skip; work += duration; }
   }
   assert(skips > 600 && skips < 800 && work/2000 < 15500);
   assert(rb10_fraction <= 512);
   for (unsigned i=0; i<120; ++i) { unsigned skip=rt9_select_mode(); rb10_observe(skip,6000); }
   assert(rb10_fraction == 0);
   for (unsigned i=0;i<120;++i) assert(!rt9_select_mode());
   rt9_disabled = true; rb10_fraction = 512;
   for (unsigned i=0;i<120;++i) assert(!rt9_select_mode());
   loaded = ready = true; p_retro_unserialize = mock_restore; p_retro_serialize_size = mock_size;
   unsigned char state[20]={0}; uint32_t n=4;
   memcpy(state,"D35PLUS1",8); memcpy(state+8,&n,4); memcpy(state+12,"a79d",4);
   assert(retro_unserialize(state,sizeof(state)));
   assert(rt9_runs==0 && rb10_fraction==0 && rb10_credit==0);
   printf("PASS: heavy map predicts %u/2000 skipped frames, average work %llu us; light menu restores all draws; audio always enabled; compatible state reset\\n",skips,(unsigned long long)(work/2000));
}
