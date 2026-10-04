#include "emu_sfc_plus_v8_capture.c"
#include <assert.h>
#include <math.h>
static int16_t captured[44100 * 2 + 32];
static int16_t reference[44100 * 2 + 32];
static size_t captured_count;
static unsigned unsafe_calls;
static size_t capture(const int16_t *data, size_t n)
{
   assert(captured_count + n < 44116);
   memcpy(captured + captured_count * 2, data, n * 4);
   captured_count += n; return 0;
}
static bool dangerous_env(unsigned cmd, void *data)
{ (void)cmd; (void)data; ++unsafe_calls; return true; }
int main(void)
{
   static int16_t tone[32040 * 2];
   unsigned i; size_t n, first_count;
   struct { struct retro_game_geometry g; uint8_t sentinel[32]; } geometry;
   struct retro_system_av_info av;
   int16_t low = 32767, high = -32768;
   FILE *f;
   for (i = 0; i < 32040; ++i) {
      tone[i * 2] = (int16_t)(12000 * sin(2 * 3.14159265358979323846 * 1000 * i / 32040));
      tone[i * 2 + 1] = -tone[i * 2];
   }
   frontend_batch = capture; input_rate = 32040;
   assert(audio_batch(tone, 32040) == 32040);
   first_count = captured_count;
   assert(first_count == 44099);
   memcpy(reference, captured, captured_count * 4);
   audio_reset(); captured_count = 0;
   for (i = 0; i < 32040; i += n) {
      n = i % 537 + 1;
      if (n > 32040 - i) n = 32040 - i;
      assert(audio_batch(tone + i * 2, n) == n);
   }
   assert(captured_count == first_count && !memcmp(reference, captured, captured_count * 4));
   for (i = 0; i < captured_count; ++i) {
      if (captured[i * 2] < low) low = captured[i * 2];
      if (captured[i * 2] > high) high = captured[i * 2];
      assert(captured[i * 2] == -captured[i * 2 + 1]);
   }
   assert(low < -11800 && high > 11800);
   f = fopen("tone.s16le", "wb"); assert(f);
   assert(fwrite(captured, 4, captured_count, f) == captured_count); fclose(f);
   memset(&geometry, 0xa5, sizeof(geometry)); geometry.g = (struct retro_game_geometry){256,224,512,512,4.0f/3.0f};
   frontend_env = dangerous_env;
   assert(environment(RETRO_ENVIRONMENT_SET_GEOMETRY, &geometry.g));
   for (i = 0; i < sizeof(geometry.sentinel); ++i) assert(geometry.sentinel[i] == 0xa5);
   memset(&av, 0, sizeof(av)); av.geometry = geometry.g; av.timing.sample_rate = 32040;
   assert(environment(RETRO_ENVIRONMENT_SET_SYSTEM_AV_INFO, &av));
   assert(unsafe_calls == 0);
   printf("PASS resampler: single/chunked identical, output=%u min=%d max=%d, unsafe geometry/AV calls=%u\n",
      (unsigned)first_count, low, high, unsafe_calls);
   return 0;
}
