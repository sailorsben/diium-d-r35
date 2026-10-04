#include "emu_sfc_plus_v9_render.c"
#include <assert.h>
static unsigned enabled, disabled;
static void mock_run(void)
{
   int mask = 0;
   assert(environment(RETRO_ENVIRONMENT_GET_AUDIO_VIDEO_ENABLE, &mask));
   assert(mask == 2 || mask == 3);
   if (mask == 2) ++disabled; else ++enabled;
   int16_t samples[1070] = {0};
   assert(audio_batch(samples, 535) == 535);
}
static bool mock_restore(const void *d, size_t n) { (void)d; return n == 4; }
static size_t mock_size(void) { return 4; }
static void mock_reset(void) { }
int main(void)
{
   loaded = ready = true; p_retro_run = mock_run;
   p_retro_unserialize = mock_restore; p_retro_serialize_size = mock_size; p_retro_reset = mock_reset;
   rt9_reset();
   for (unsigned i=0; i<4200; ++i) retro_run();
   assert(enabled == 3000 && disabled == 1200);
   assert(rt9_runs == 4200);
   assert(rt9_bins[14].calls == 120 && rt9_bins[15].calls == 120 && rt9_bins[24].calls == 120);
   unsigned char state[20] = {0};
   memcpy(state, "D35PLUS1", 8); uint32_t n=4; memcpy(state+8,&n,4); memcpy(state+12,"a79d",4);
   assert(retro_unserialize(state, sizeof(state)) && rt9_runs == 0 && rt9_mode == 0);
   retro_run(); assert(rt9_runs == 1);
   retro_reset(); assert(rt9_runs == 0);
   setenv("D35_V9_DISABLE", "1", 1); rt9_reset(); rt9_runs = 1800;
   assert(rt9_select_mode() == 0);
   puts("PASS: exact 1800/1200/remainder schedule; audio remains enabled; state load/reset restart schedule; control disables test");
}
