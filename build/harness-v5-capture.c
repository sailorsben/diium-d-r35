#include <libretro.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <sys/resource.h>
static unsigned videos, polls, bad_geometry, nonblack;
static unsigned run_number;
static uint64_t frames;
static size_t amin = (size_t)-1, amax;
static FILE *pcm;
static bool env(unsigned cmd, void *data)
{
   if (cmd == RETRO_ENVIRONMENT_SET_PIXEL_FORMAT)
      return *(enum retro_pixel_format *)data == RETRO_PIXEL_FORMAT_RGB565;
   if (cmd == RETRO_ENVIRONMENT_SET_GEOMETRY || cmd == RETRO_ENVIRONMENT_SET_SYSTEM_AV_INFO) {
      ++bad_geometry; return true;
   }
   if (cmd == RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY || cmd == RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY) {
      *(const char **)data = "."; return true;
   }
   return false;
}
static void video(const void *data, unsigned w, unsigned h, size_t pitch)
{
   unsigned i;
   ++videos;
   assert(w && h && w <= 512 && h <= 512 && pitch == w * 2);
   if (!data) return;
   for (i = 0; i < w * h; ++i) if (((const uint16_t *)data)[i]) { ++nonblack; break; }
   if (run_number == 1799) {
      FILE *f = fopen("frame.ppm", "wb");
      assert(f); fprintf(f, "P6\n%u %u\n255\n", w, h);
      for (i = 0; i < w * h; ++i) {
         uint16_t p = ((const uint16_t *)data)[i];
         unsigned char rgb[3] = {((p >> 11) & 31) * 255 / 31, ((p >> 5) & 63) * 255 / 63, (p & 31) * 255 / 31};
         fwrite(rgb, 1, 3, f);
      }
      fclose(f);
   }
}
static size_t audio(const int16_t *data, size_t n)
{
   assert(n && n <= 2048);
   frames += n;
   if (n < amin) amin = n;
   if (n > amax) amax = n;
   if (pcm) assert(fwrite(data, 4, n, pcm) == n);
   return 0; /* Actual vrtemu behavior: consumed data, zero return. */
}
static void poll(void) { ++polls; }
static int16_t input(unsigned port, unsigned device, unsigned index, unsigned id)
{ (void)port; (void)device; (void)index; (void)id; return 0; }
int main(int argc, char **argv)
{
   struct retro_system_info info;
   struct retro_system_av_info av;
   struct retro_game_info game;
   size_t bytes; void *state;
   struct rusage usage;
   assert(argc >= 2);
   retro_set_environment(env); retro_set_video_refresh(video);
   retro_set_audio_sample_batch(audio); retro_set_input_poll(poll); retro_set_input_state(input);
   retro_get_system_info(&info);
   assert(info.library_name && strstr(info.library_name, "Plus"));
   printf("core=%s version=%s\n", info.library_name, info.library_version);
   retro_init();
   memset(&game, 0, sizeof(game)); game.path = argv[1];
   if (argc > 2 && !strcmp(argv[2], "memory")) {
      FILE *f = fopen(argv[1], "rb"); long n;
      assert(f); fseek(f, 0, SEEK_END); n = ftell(f); rewind(f);
      game.data = malloc(n); game.size = n;
      assert(game.data && fread((void *)game.data, 1, n, f) == (size_t)n); fclose(f);
   }
   assert(retro_load_game(&game)); free((void *)game.data);
   retro_get_system_av_info(&av);
   assert(av.timing.sample_rate == 44100);
   printf("AV=%ux%u fps=%.9f output_rate=%.0f\n", av.geometry.base_width, av.geometry.base_height, av.timing.fps, av.timing.sample_rate);
   pcm = fopen("audio.s16le", "wb"); assert(pcm);
   for (run_number = 0; run_number < 1800; ++run_number) {
      retro_run();
      if (run_number==899) {
         const char *name=getenv("D35_TIMING_LOG");
         FILE *report=name ? fopen(name,"r") : NULL;
         char line[512]; assert(report && fgets(line,sizeof(line),report));
         assert(strstr(line,"v5 diagnostic") && !strstr(line,"run=0;"));
         fclose(report);
         const char *directory=getenv("D35_CAPTURE_DIRECTORY");
         char name_buffer[1100]; assert(directory);
         snprintf(name_buffer,sizeof(name_buffer),"%s/emu_sfc_plus_v5_audio.wav",directory);
         FILE *capture=fopen(name_buffer,"rb"); assert(capture);
         unsigned char header[44]; assert(fread(header,1,44,capture)==44);
         assert(!memcmp(header,"RIFF",4) && !memcmp(header+8,"WAVEfmt ",8));
         fseek(capture,0,SEEK_END); assert(ftell(capture)==44+44100*6*4);
         fclose(capture);
         puts("PASS complete six-second WAV saved during play before unload");
         puts("PASS periodic FF3 timing log exists at frame 900, before serialization/unload");
      }
   }
   fclose(pcm); pcm = NULL;
   assert(videos == 1800 && polls == 1800 && nonblack > 1000 && bad_geometry == 0);
   assert(frames > 1300000 && frames < 1350000);
   bytes = retro_serialize_size(); state = malloc(bytes); assert(state);
   assert(retro_serialize(state, bytes));
   for (run_number = 0; run_number < 10; ++run_number) retro_run();
   assert(retro_unserialize(state, bytes));
   memset(state, 0, 8); assert(!retro_unserialize(state, bytes));
   free(state);
   assert(retro_get_memory_data(RETRO_MEMORY_SAVE_RAM) && retro_get_memory_size(RETRO_MEMORY_SAVE_RAM));
   retro_reset(); retro_run();
   getrusage(RUSAGE_SELF, &usage);
   printf("PASS frames=1800 video=%u nonblack=%u polls=%u audio_frames=%llu batch_min=%u batch_max=%u unsafe_env_calls=%u state_bytes=%u maxrss_kib=%ld\n",
      videos, nonblack, polls, (unsigned long long)frames, (unsigned)amin, (unsigned)amax, bad_geometry, (unsigned)bytes, usage.ru_maxrss);
   retro_deinit(); return 0;
}
