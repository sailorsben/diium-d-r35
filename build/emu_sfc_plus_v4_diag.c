#define _GNU_SOURCE
#include <libretro.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <dlfcn.h>
#include <zlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <errno.h>

/* D-R35 v4 diagnostic. v2 video and PCM conversion remain unchanged. */
#define API RETRO_API
#define OUT_RATE 44100u
#define ROM_LIMIT (8u * 1024u * 1024u)
#define ZIP_LIMIT (16u * 1024u * 1024u)
static retro_environment_t frontend_env;
static retro_video_refresh_t frontend_video;
static retro_audio_sample_t frontend_audio;
static retro_audio_sample_batch_t frontend_batch;
static retro_input_poll_t frontend_poll;
static retro_input_state_t frontend_input;
static void *core;
static bool ready, initialized, loaded;
static FILE *logfile;
static uint64_t runs, native_frames, output_frames;
#define VIDEO_SLOT_BYTES (512u * 512u * 2u)
static uint8_t *video_pool;
static unsigned video_slot, video_calls;
static int chunk_fd = -1;
static bool video_allocation_failed, test_heap_video;
static void *display_driver;
static void (*wait_display)(void);
/* Recovered from original ChunkMemAlloc/Free and driver's gpChunkMemAlloc:
 * /dev/chunkmem ioctl: physical address, mapped virtual address, byte count.
 * Buffers survive close and require an explicit free ioctl. */
struct chunk_block { uint32_t physical, mapped, bytes; };
static struct chunk_block chunk_video;
static int16_t output[2048 * 2], previous[2];
static unsigned output_count, phase, input_rate = 32040;
static bool have_previous;
static struct retro_system_av_info native_av;
#include "audio_diagnostics_v4.h"

#define FUNCTIONS(X) \
 X(void, retro_set_environment, (retro_environment_t)) \
 X(void, retro_set_video_refresh, (retro_video_refresh_t)) \
 X(void, retro_set_audio_sample, (retro_audio_sample_t)) \
 X(void, retro_set_audio_sample_batch, (retro_audio_sample_batch_t)) \
 X(void, retro_set_input_poll, (retro_input_poll_t)) \
 X(void, retro_set_input_state, (retro_input_state_t)) \
 X(void, retro_init, (void)) X(void, retro_deinit, (void)) \
 X(void, retro_get_system_info, (struct retro_system_info *)) \
 X(void, retro_get_system_av_info, (struct retro_system_av_info *)) \
 X(void, retro_set_controller_port_device, (unsigned, unsigned)) \
 X(void, retro_reset, (void)) X(void, retro_run, (void)) \
 X(size_t, retro_serialize_size, (void)) \
 X(bool, retro_serialize, (void *, size_t)) \
 X(bool, retro_unserialize, (const void *, size_t)) \
 X(void, retro_cheat_reset, (void)) \
 X(void, retro_cheat_set, (unsigned, bool, const char *)) \
 X(bool, retro_load_game, (const struct retro_game_info *)) \
 X(void, retro_unload_game, (void)) \
 X(unsigned, retro_get_region, (void)) \
 X(void *, retro_get_memory_data, (unsigned)) \
 X(size_t, retro_get_memory_size, (unsigned))
#define DECLARE(type, name, args) static type (*p_##name) args;
FUNCTIONS(DECLARE)

static void message(const char *fmt, ...)
{
   va_list ap;
   if (!logfile) {
      const char *path = getenv("D35_PLUS_LOG");
      logfile = fopen(path ? path : "/usr/retro/emu_sfc_plus_v4.log", "w");
      if (logfile) setvbuf(logfile, NULL, _IOLBF, 0);
   }
   if (!logfile) return;
   va_start(ap, fmt); vfprintf(logfile, fmt, ap); va_end(ap);
}

static void core_log(enum retro_log_level level, const char *fmt, ...)
{
   /* Core logs occur at load/reset; avoid SD writes in the audio loop. */
   va_list ap;
   if (!logfile) message("D-R35 Plus adapter v4 diagnostic\n");
   if (!logfile) return;
   fprintf(logfile, "core[%d] ", (int)level);
   va_start(ap, fmt); vfprintf(logfile, fmt, ap); va_end(ap);
}

static void audio_reset(void)
{ phase = output_count = 0; have_previous = false; }

static void audio_flush(void)
{
   unsigned i;
   struct diag_audio_mark mark;
   if (!output_count) return;
   mark = diag_audio_before();
   if (frontend_batch) frontend_batch(output, output_count);
   else if (frontend_audio)
      for (i = 0; i < output_count; ++i)
         frontend_audio(output[i * 2], output[i * 2 + 1]);
   diag_audio_after(mark, (uint32_t)runs + 1, output_count);
   output_frames += output_count;
   output_count = 0;
}

/* Continuous fractional position survives libretro callback boundaries.
 * There is one input sample of interpolation latency, never a per-frame reset.
 * The vendor consumes batch data but returns zero; ignore that broken return. */
static size_t audio_batch(const int16_t *data, size_t frames)
{
   size_t i;
   if (!data) return 0;
   native_frames += frames;
   for (i = 0; i < frames; ++i) {
      const int16_t *now = data + i * 2;
      if (!have_previous) {
         previous[0] = now[0]; previous[1] = now[1];
         have_previous = true; continue;
      }
      while (phase < OUT_RATE) {
         unsigned ch;
         for (ch = 0; ch < 2; ++ch)
            output[output_count * 2 + ch] =
               ((int32_t)previous[ch] * (int32_t)(OUT_RATE - phase) +
                (int32_t)now[ch] * (int32_t)phase) / (int32_t)OUT_RATE;
         ++output_count;
         phase += input_rate;
         if (output_count == 2048) audio_flush();
      }
      phase -= OUT_RATE;
      previous[0] = now[0]; previous[1] = now[1];
   }
   audio_flush();
   return frames;
}
static void audio_sample(int16_t l, int16_t r)
{ int16_t data[2] = {l, r}; audio_batch(data, 1); }

static bool video_allocate(void)
{
   const char *test_mode;
   if (video_pool) return true;
   if (video_allocation_failed) return false;
   test_mode = getenv("D35_TEST_HEAP_VIDEO");
   test_heap_video = test_mode && !strcmp(test_mode, "1");
   if (test_heap_video) {
      /* Explicit harness mode only. Hardware never falls back to heap memory. */
      video_pool = malloc(VIDEO_SLOT_BYTES * 2);
      if (video_pool) memset(video_pool, 0, VIDEO_SLOT_BYTES * 2);
      message("TEST ONLY: heap video pool; this does not prove hardware DMA\n");
   } else {
      chunk_fd = open("/dev/chunkmem", O_RDWR);
      memset(&chunk_video, 0, sizeof(chunk_video));
      chunk_video.bytes = VIDEO_SLOT_BYTES * 2;
      if (chunk_fd >= 0 && ioctl(chunk_fd, 0xc00c4301u, &chunk_video) == 0 && chunk_video.mapped) {
         video_pool = (uint8_t *)(uintptr_t)chunk_video.mapped;
         memset(video_pool, 0, chunk_video.bytes);
         display_driver = dlopen("/usr/retro/driver.so", RTLD_NOW | RTLD_LOCAL);
         if (display_driver) *(void **)(&wait_display) = dlsym(display_driver, "WaitDisp");
         message("VIDEO chunk pool: mapped=%08x physical=%08x bytes=%u slots=2 wait=%u\n",
            chunk_video.mapped, chunk_video.physical, chunk_video.bytes, wait_display != NULL);
      } else {
         message("VIDEO ERROR: chunk allocation failed fd=%d errno=%d mapped=%08x; refusing ordinary RAM\n",
            chunk_fd, errno, chunk_video.mapped);
      }
   }
   if (!video_pool) { video_allocation_failed = true; return false; }
   video_slot = video_calls = 0;
   return true;
}

static void video_release(void)
{
   if (video_pool) {
      if (wait_display) wait_display();
      if (test_heap_video) free(video_pool);
      else if (chunk_fd >= 0 && ioctl(chunk_fd, 0x400c4303u, &chunk_video) < 0)
         message("VIDEO ERROR: chunk free failed errno=%d\n", errno);
   }
   video_pool = NULL;
   if (chunk_fd >= 0) close(chunk_fd);
   chunk_fd = -1;
   if (display_driver) dlclose(display_driver);
   display_driver = NULL; wait_display = NULL;
   video_allocation_failed = false;
}

static void video(const void *data, unsigned w, unsigned h, size_t pitch)
{
   unsigned y;
   uint16_t *pixels;
   uint64_t began;
   if (!frontend_video) return;
   if (!data) { frontend_video(NULL, w, h, (size_t)w * 2); return; }
   if (!w || !h || w > 512 || h > 512 || pitch < (size_t)w * 2) {
      message("Rejected video: %ux%u pitch=%u\n", w, h, (unsigned)pitch);
      return;
   }
   if (!video_allocate()) return;
   began = diag_now();
   /* Always copy, even an already compact native image. The scaler requires
    * chunk-backed memory. Alternating slots keep the previous image intact
    * while the driver's one-outstanding-job worker consumes it. */
   pixels = (uint16_t *)(video_pool + video_slot * VIDEO_SLOT_BYTES);
   for (y = 0; y < h; ++y)
      memcpy(pixels + y * w, (const uint8_t *)data + y * pitch, w * 2);
   frontend_video(pixels, w, h, (size_t)w * 2);
   diag_video_done((uint32_t)runs + 1, began);
   ++video_calls;
   if (video_calls <= 3) message("video %u: in=%ux%u pitch=%u out_pitch=%u slot=%u\n",
      video_calls, w, h, (unsigned)pitch, w * 2, video_slot);
   video_slot ^= 1;
}
static void poll(void) { if (frontend_poll) frontend_poll(); }
static int16_t input(unsigned port, unsigned device, unsigned index, unsigned id)
{ return frontend_input ? frontend_input(port, device, index, id) : 0; }

static bool environment(unsigned cmd, void *data)
{
   switch (cmd) {
   case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT:
      return data && *(enum retro_pixel_format *)data == RETRO_PIXEL_FORMAT_RGB565;
   case RETRO_ENVIRONMENT_SET_GEOMETRY:
      /* Vendor cmd 37 writes a double at offset 32 into a 20-byte geometry.
       * Never forward this request, including a copied geometry object. */
      if (data) native_av.geometry = *(const struct retro_game_geometry *)data;
      return true;
   case RETRO_ENVIRONMENT_SET_SYSTEM_AV_INFO:
      if (!data) return false;
      native_av = *(const struct retro_system_av_info *)data;
      if (native_av.timing.sample_rate < 8000 || native_av.timing.sample_rate > 96000)
         return false;
      input_rate = (unsigned)native_av.timing.sample_rate;
      audio_reset(); return true;
   case RETRO_ENVIRONMENT_GET_LOG_INTERFACE:
      ((struct retro_log_callback *)data)->log = core_log; return true;
   case RETRO_ENVIRONMENT_GET_CORE_OPTIONS_VERSION:
      *(unsigned *)data = 0; return true;
   case RETRO_ENVIRONMENT_SET_VARIABLES:
   case RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS:
      return true;
   case RETRO_ENVIRONMENT_GET_VARIABLE:
      /* Core handles an absent value using its upstream defaults:
       * automatic region, no frameskip, no overclock or sprite hacks. */
      ((struct retro_variable *)data)->value = NULL; return false;
   case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE:
      *(bool *)data = false; return true;
   case RETRO_ENVIRONMENT_GET_AUDIO_VIDEO_ENABLE:
      *(int *)data = 3; return true;
   case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
   case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY:
   case RETRO_ENVIRONMENT_GET_LIBRETRO_PATH:
      return frontend_env ? frontend_env(cmd, data) : false;
   default:
      return false;
   }
}

static bool ensure_core(void)
{
   const char *path;
   char sibling[1024];
   Dl_info where;
   if (ready) return true;
   if (core) return false;
   message("D-R35 Plus adapter v4 diagnostic; output audio 44100 Hz\n");
   path = getenv("D35_PLUS_CORE");
   if (!path && dladdr((void *)ensure_core, &where) && where.dli_fname) {
      const char *slash = strrchr(where.dli_fname, '/');
      size_t n = slash ? (size_t)(slash - where.dli_fname + 1) : 0;
      if (n + sizeof("emu_sfc_plus.so") < sizeof(sibling)) {
         memcpy(sibling, where.dli_fname, n);
         strcpy(sibling + n, "emu_sfc_plus.so"); path = sibling;
      }
   }
   if (!path) path = "/usr/retro/libs/emu_sfc_plus.so";
   core = dlopen(path, RTLD_NOW | RTLD_LOCAL);
   if (!core) { message("Core load failed: %s\n", dlerror()); return false; }
#define RESOLVE(type, name, args) \
   *(void **)(&p_##name) = dlsym(core, #name); \
   if (!p_##name) { message("Missing symbol %s\n", #name); return false; }
   FUNCTIONS(RESOLVE)
   p_retro_set_environment(environment);
   p_retro_set_video_refresh(video);
   p_retro_set_audio_sample(audio_sample);
   p_retro_set_audio_sample_batch(audio_batch);
   p_retro_set_input_poll(poll);
   p_retro_set_input_state(input);
   ready = true;
   return true;
}

static uint16_t u16(const uint8_t *p) { return p[0] | (uint16_t)p[1] << 8; }
static uint32_t u32(const uint8_t *p)
{ return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24; }
static bool snes_name(const uint8_t *name, unsigned len)
{
   char ext[5]; unsigned i;
   if (len < 4 || name[len - 4] != '.') return false;
   for (i = 0; i < 4; ++i) {
      char c = (char)name[len - 4 + i];
      ext[i] = c >= 'A' && c <= 'Z' ? c + 32 : c;
   }
   ext[4] = 0;
   return !strcmp(ext, ".smc") || !strcmp(ext, ".sfc") || !strcmp(ext, ".fig") || !strcmp(ext, ".swc");
}

static void *unzip(const uint8_t *zip, size_t size, size_t *rom_size)
{
   size_t end, cd, limit;
   unsigned count, i;
   if (size < 22) return NULL;
   limit = size > 65557 ? size - 65557 : 0;
   end = size - 22;
   while (u32(zip + end) != 0x06054b50 || end + 22 + u16(zip + end + 20) != size) {
      if (end == limit) return NULL;
      --end;
   }
   if (u16(zip + end + 4) || u16(zip + end + 6)) return NULL;
   count = u16(zip + end + 10); cd = u32(zip + end + 16);
   if (cd > end || u32(zip + end + 12) > end - cd) return NULL;
   for (i = 0; i < count; ++i) {
      size_t next, local, start;
      unsigned names, method;
      uint32_t packed, unpacked, crc;
      void *result;
      if (cd > end || end - cd < 46 || u32(zip + cd) != 0x02014b50) return NULL;
      names = u16(zip + cd + 28);
      next = cd + 46 + names + u16(zip + cd + 30) + u16(zip + cd + 32);
      if (next > end) return NULL;
      if (!snes_name(zip + cd + 46, names)) { cd = next; continue; }
      if (u16(zip + cd + 8) & 1) return NULL;
      method = u16(zip + cd + 10); crc = u32(zip + cd + 16);
      packed = u32(zip + cd + 20); unpacked = u32(zip + cd + 24);
      local = u32(zip + cd + 42);
      if (!unpacked || unpacked > ROM_LIMIT || local > size || size - local < 30 ||
          u32(zip + local) != 0x04034b50) return NULL;
      start = local + 30 + u16(zip + local + 26) + u16(zip + local + 28);
      if (start > size || packed > size - start) return NULL;
      result = malloc(unpacked);
      if (!result) return NULL;
      if (method == 0 && packed == unpacked) memcpy(result, zip + start, unpacked);
      else if (method == 8) {
         z_stream stream; int status;
         memset(&stream, 0, sizeof(stream));
         stream.next_in = (Bytef *)(zip + start); stream.avail_in = packed;
         stream.next_out = result; stream.avail_out = unpacked;
         if (inflateInit2(&stream, -MAX_WBITS) != Z_OK) { free(result); return NULL; }
         status = inflate(&stream, Z_FINISH);
         inflateEnd(&stream);
         if (status != Z_STREAM_END || stream.total_out != unpacked || stream.total_in != packed) {
            free(result); return NULL;
         }
      } else { free(result); return NULL; }
      if ((uint32_t)crc32(0, result, unpacked) != crc) { free(result); return NULL; }
      *rom_size = unpacked; return result;
   }
   return NULL;
}

API unsigned retro_api_version(void) { return RETRO_API_VERSION; }
API void retro_set_environment(retro_environment_t cb) { frontend_env = cb; }
API void retro_set_video_refresh(retro_video_refresh_t cb) { frontend_video = cb; }
API void retro_set_audio_sample(retro_audio_sample_t cb) { frontend_audio = cb; }
API void retro_set_audio_sample_batch(retro_audio_sample_batch_t cb) { frontend_batch = cb; }
API void retro_set_input_poll(retro_input_poll_t cb) { frontend_poll = cb; }
API void retro_set_input_state(retro_input_state_t cb) { frontend_input = cb; }
API void retro_init(void)
{
   if (!ensure_core() || initialized) return;
   if (frontend_env) {
      enum retro_pixel_format format = RETRO_PIXEL_FORMAT_RGB565;
      if (!frontend_env(RETRO_ENVIRONMENT_SET_PIXEL_FORMAT, &format)) {
         message("Frontend rejected RGB565\n"); return;
      }
   }
   p_retro_init(); initialized = true;
   message("Initialized\n");
}
API void retro_get_system_info(struct retro_system_info *info)
{
   memset(info, 0, sizeof(*info));
   if (ensure_core()) p_retro_get_system_info(info);
   else { info->library_name = "D35 Plus load failure"; info->library_version = "v4 diagnostic"; }
   info->valid_extensions = "smc|sfc|fig|swc|zip";
   /* Handle both vendor path-only requests and ordinary libretro memory input. */
   info->need_fullpath = false; info->block_extract = false;
}
API void retro_get_system_av_info(struct retro_system_av_info *info)
{
   if (ensure_core()) p_retro_get_system_av_info(&native_av);
   if (!native_av.geometry.base_width) {
      native_av.geometry = (struct retro_game_geometry){256,224,512,512,4.0f/3.0f};
      native_av.timing.fps = 60; native_av.timing.sample_rate = 32040;
   }
   input_rate = (unsigned)native_av.timing.sample_rate;
   *info = native_av; info->timing.sample_rate = OUT_RATE;
}
API bool retro_load_game(const struct retro_game_info *game)
{
   struct retro_game_info memory;
   void *file_data = NULL, *rom_data = NULL;
   bool success = false;
   if (!game || !ensure_core()) return false;
   if (!initialized) retro_init();
   if (!initialized) return false;
   memory = *game;
   if (!memory.data || !memory.size) {
      FILE *f; long len;
      if (!game->path || !(f = fopen(game->path, "rb"))) {
         message("Cannot open ROM path\n"); return false;
      }
      if (fseek(f, 0, SEEK_END) || (len = ftell(f)) <= 0 || (unsigned long)len > ZIP_LIMIT ||
          fseek(f, 0, SEEK_SET) || !(file_data = malloc(len))) { fclose(f); return false; }
      if (fread(file_data, 1, len, f) != (size_t)len) { free(file_data); fclose(f); return false; }
      fclose(f); memory.data = file_data; memory.size = len;
   }
   if (memory.size >= 4 && u32(memory.data) == 0x04034b50) {
      rom_data = unzip(memory.data, memory.size, &memory.size);
      if (!rom_data) { message("Invalid/unsupported SNES ZIP\n"); goto finish; }
      memory.data = rom_data;
   }
   if (memory.size > ROM_LIMIT || memory.size < 32768) goto finish;
   message("Loading %u ROM bytes\n", (unsigned)memory.size);
   success = p_retro_load_game(&memory);
   if (success) {
      p_retro_get_system_av_info(&native_av);
      input_rate = (unsigned)native_av.timing.sample_rate;
      loaded = true; audio_reset(); runs = native_frames = output_frames = 0;
      diag_reset();
      diag_worker_start();
      message("Periodic timing reporter: worker_error=%d interval=10s stack=128KiB\n", diag_worker_error);
      message("Loaded: fps=%.9f native_audio=%u output_audio=%u; region=%u\n",
         native_av.timing.fps, input_rate, OUT_RATE, p_retro_get_region());
   } else message("Core rejected ROM\n");
finish:
   free(rom_data); free(file_data); return success;
}
API void retro_run(void)
{
   uint64_t began;
   if (!loaded) return;
   began = diag_now();
   p_retro_run(); ++runs;
   diag_frame_done((uint32_t)runs, began);
}
API void retro_reset(void) { if (loaded) { p_retro_reset(); audio_reset(); } }
API void retro_unload_game(void)
{
   diag_worker_stop();
   diag_dump();
   if (loaded) message("Stopped at run %llu: native=%llu output=%llu\n",
      (unsigned long long)runs, (unsigned long long)native_frames, (unsigned long long)output_frames);
   if (loaded) p_retro_unload_game();
   loaded = false; audio_reset(); diag_dsp_pointer = NULL; video_release();
}

/* The vendor may dlclose without calling the libretro lifecycle callbacks. */
__attribute__((destructor)) static void diag_library_unload(void)
{ diag_worker_stop(); diag_dump(); }
API void retro_deinit(void)
{
   retro_unload_game();
   if (initialized) p_retro_deinit();
   initialized = false;
   if (core) dlclose(core);
   core = NULL; ready = false;
   if (logfile) fclose(logfile);
   logfile = NULL;
}
API size_t retro_serialize_size(void)
{ return ready ? p_retro_serialize_size() + 16 : 0; }
API bool retro_serialize(void *data, size_t size)
{
   uint8_t *p = data; uint32_t bytes;
   diag_dump();
   if (!loaded || !data || size != retro_serialize_size()) return false;
   bytes = (uint32_t)p_retro_serialize_size();
   memcpy(p, "D35PLUS1", 8); memcpy(p + 8, &bytes, 4); memcpy(p + 12, "a79d", 4);
   return p_retro_serialize(p + 16, bytes);
}
API bool retro_unserialize(const void *data, size_t size)
{
   const uint8_t *p = data;
   if (!loaded || !data || size != retro_serialize_size() || memcmp(p, "D35PLUS1", 8) ||
       u32(p + 8) != p_retro_serialize_size() || memcmp(p + 12, "a79d", 4)) {
      message("Rejected incompatible save state (old core states are not compatible)\n"); return false;
   }
   if (!p_retro_unserialize(p + 16, size - 16)) return false;
   audio_reset(); return true;
}
API void retro_set_controller_port_device(unsigned port, unsigned device)
{ if (ensure_core()) p_retro_set_controller_port_device(port, device); }
API unsigned retro_get_region(void) { return ready ? p_retro_get_region() : RETRO_REGION_NTSC; }
API void *retro_get_memory_data(unsigned type) { return ready ? p_retro_get_memory_data(type) : NULL; }
API size_t retro_get_memory_size(unsigned type) { return ready ? p_retro_get_memory_size(type) : 0; }
API void retro_cheat_reset(void) { if (ready) p_retro_cheat_reset(); }
API void retro_cheat_set(unsigned index, bool enabled, const char *code)
{ if (ready) p_retro_cheat_set(index, enabled, code); }
API bool retro_load_game_special(unsigned type, const struct retro_game_info *info, size_t n)
{ (void)type; (void)info; (void)n; return false; }
