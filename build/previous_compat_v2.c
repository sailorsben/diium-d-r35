/*
 * emu_sfc_compat_v2.c
 * DIIUM D-R35 / vrtemu libretro compatibility shim for trying newer SNES cores.
 *
 * Layout:
 *   retro/libs/emu_sfc.so      <- this shim
 *   retro/libs/emu_sfc_new.so  <- newer SNES/Snes9x core to test
 *
 * Purpose:
 *   - Load a newer libretro SNES core.
 *   - Force vrtemu-facing video to RGB565.
 *   - Optionally normalize geometry to a fixed size.
 *   - Log core AV info, pixel format requests, and video callback dimensions.
 *   - v2: if vrtemu passes only a ROM path, load the ROM into memory for newer cores.
 *   - v2: if vrtemu passes a .zip, extract the first SNES ROM inside using libz.
 *
 * Build variants:
 *   FORCE_GEOM=0                       : RGB565 conversion only; pass dimensions through
 *   FORCE_GEOM=1 TARGET_W=256 TARGET_H=224 : RGB565 + nearest-neighbor normalize to 256x224
 *   FORCE_GEOM=1 TARGET_W=256 TARGET_H=240 : RGB565 + nearest-neighbor normalize to 256x240
 *   FORCE_GEOM=1 TARGET_W=320 TARGET_H=240 : RGB565 + nearest-neighbor normalize to 320x240
 */
#ifndef VARIANT_NAME
#define VARIANT_NAME "passthrough_rgb565"
#endif
#ifndef FORCE_GEOM
#define FORCE_GEOM 0
#endif
#ifndef TARGET_W
#define TARGET_W 256
#endif
#ifndef TARGET_H
#define TARGET_H 224
#endif

#ifndef __cplusplus
typedef unsigned char bool;
#define true 1
#define false 0
#endif

typedef signed short int16_t;
typedef unsigned short uint16_t;
typedef unsigned int uint32_t;
typedef unsigned int size_t;
typedef unsigned long long uint64_t;
typedef unsigned char uint8_t;
#define NULL ((void*)0)
#define RETRO_API __attribute__((visibility("default")))
#define RETRO_CALLCONV

#define RTLD_NOW 2
#define RTLD_GLOBAL 0x100
#define O_WRONLY 1
#define O_CREAT 0100
#define O_APPEND 02000

extern void *dlopen(const char *filename, int flags);
extern void *dlsym(void *handle, const char *symbol);
extern char *dlerror(void);
extern int open(const char *pathname, int flags, ...);
extern int write(int fd, const void *buf, unsigned int count);
extern int close(int fd);
extern int read(int fd, void *buf, unsigned int count);
extern long lseek(int fd, long offset, int whence);
extern void *malloc(size_t size);
extern void free(void *ptr);
extern int fsync(int fd);
extern void *memcpy(void *dest, const void *src, size_t n);
extern void *memset(void *s, int c, size_t n);

#define RETRO_API_VERSION 1
#define RETRO_ENVIRONMENT_SET_PIXEL_FORMAT 10
#define RETRO_ENVIRONMENT_GET_VARIABLE 15
#define RETRO_ENVIRONMENT_SET_VARIABLES 16
#define RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE 17
#define RETRO_ENVIRONMENT_SET_SYSTEM_AV_INFO 32
#define RETRO_ENVIRONMENT_SET_GEOMETRY 37
#define RETRO_ENVIRONMENT_GET_CORE_OPTIONS_VERSION 52
#define RETRO_ENVIRONMENT_SET_CORE_OPTIONS 53
#define RETRO_ENVIRONMENT_SET_CORE_OPTIONS_INTL 54
#define RETRO_ENVIRONMENT_SET_CORE_OPTIONS_V2 67
#define RETRO_ENVIRONMENT_SET_CORE_OPTIONS_V2_INTL 68

#define RETRO_PIXEL_FORMAT_0RGB1555 0
#define RETRO_PIXEL_FORMAT_XRGB8888 1
#define RETRO_PIXEL_FORMAT_RGB565 2

#define RETRO_REGION_NTSC 0
#define RETRO_REGION_PAL 1

struct retro_game_info { const char *path; const void *data; size_t size; const char *meta; };
struct retro_system_info { const char *library_name; const char *library_version; const char *valid_extensions; bool need_fullpath; bool block_extract; };
struct retro_game_geometry { unsigned base_width; unsigned base_height; unsigned max_width; unsigned max_height; float aspect_ratio; };
struct retro_system_timing { double fps; double sample_rate; };
struct retro_system_av_info { struct retro_game_geometry geometry; struct retro_system_timing timing; };
struct retro_variable { const char *key; const char *value; };

/* Callback types. */
typedef bool (*retro_environment_t)(unsigned cmd, void *data);
typedef void (*retro_video_refresh_t)(const void *data, unsigned width, unsigned height, size_t pitch);
typedef void (*retro_audio_sample_t)(int16_t left, int16_t right);
typedef size_t (*retro_audio_sample_batch_t)(const int16_t *data, size_t frames);
typedef void (*retro_input_poll_t)(void);
typedef int16_t (*retro_input_state_t)(unsigned port, unsigned device, unsigned index, unsigned id);

/* Original core function pointers. */
static void *core_handle = NULL;
static unsigned (*p_retro_api_version)(void) = NULL;
static void (*p_retro_set_environment)(retro_environment_t) = NULL;
static void (*p_retro_set_video_refresh)(retro_video_refresh_t) = NULL;
static void (*p_retro_set_audio_sample)(retro_audio_sample_t) = NULL;
static void (*p_retro_set_audio_sample_batch)(retro_audio_sample_batch_t) = NULL;
static void (*p_retro_set_input_poll)(retro_input_poll_t) = NULL;
static void (*p_retro_set_input_state)(retro_input_state_t) = NULL;
static void (*p_retro_init)(void) = NULL;
static void (*p_retro_deinit)(void) = NULL;
static void (*p_retro_get_system_info)(struct retro_system_info*) = NULL;
static void (*p_retro_get_system_av_info)(struct retro_system_av_info*) = NULL;
static void (*p_retro_set_controller_port_device)(unsigned, unsigned) = NULL;
static void (*p_retro_reset)(void) = NULL;
static void (*p_retro_run)(void) = NULL;
static size_t (*p_retro_serialize_size)(void) = NULL;
static bool (*p_retro_serialize)(void*, size_t) = NULL;
static bool (*p_retro_unserialize)(const void*, size_t) = NULL;
static void (*p_retro_cheat_reset)(void) = NULL;
static void (*p_retro_cheat_set)(unsigned, bool, const char*) = NULL;
static bool (*p_retro_load_game)(const struct retro_game_info*) = NULL;
static bool (*p_retro_load_game_special)(unsigned, const struct retro_game_info*, size_t) = NULL;
static void (*p_retro_unload_game)(void) = NULL;
static unsigned (*p_retro_get_region)(void) = NULL;
static void *(*p_retro_get_memory_data)(unsigned) = NULL;
static size_t (*p_retro_get_memory_size)(unsigned) = NULL;

/* Frontend callbacks. */
static retro_environment_t fe_env = NULL;
static retro_video_refresh_t fe_video = NULL;
static retro_audio_sample_t fe_audio = NULL;
static retro_audio_sample_batch_t fe_audio_batch = NULL;
static retro_input_poll_t fe_input_poll = NULL;
static retro_input_state_t fe_input_state = NULL;

static int log_fd = -1;
static unsigned core_pixfmt = RETRO_PIXEL_FORMAT_0RGB1555;
static unsigned video_calls = 0;
static unsigned video_nulls = 0;
static unsigned audio_calls = 0;
static unsigned audio_min = 0xffffffffu;
static unsigned audio_max = 0;
static unsigned last_w = 0, last_h = 0, last_pitch = 0;
static unsigned warned_big = 0;

#define MAX_OUT_W 640
#define MAX_OUT_H 480
static uint16_t framebuf[MAX_OUT_W * MAX_OUT_H];

static unsigned cstrlen(const char *s) { unsigned n = 0; if (!s) return 0; while (s[n]) n++; return n; }
static void log_raw(const char *s) { if (log_fd >= 0 && s) write(log_fd, s, cstrlen(s)); }
static void log_ch(char c) { if (log_fd >= 0) write(log_fd, &c, 1); }
static void log_u64(uint64_t v) {
    char tmp[32]; unsigned n = 0; if (v == 0) { log_ch('0'); return; }
    while (v && n < sizeof(tmp)) { tmp[n++] = (char)('0' + (v % 10)); v /= 10; }
    while (n) log_ch(tmp[--n]);
}
static void log_i64(long long v) { if (v < 0) { log_ch('-'); log_u64((uint64_t)(-v)); } else log_u64((uint64_t)v); }
static void log_open_once(void) {
    if (log_fd >= 0) return;
    const char *paths[] = {
        "/media/sdcarda1/retro/emu_sfc_compat_v2.log",
        "/media/sdcardb1/retro/emu_sfc_compat_v2.log",
        "/usr/retro/emu_sfc_compat_v2.log",
        "/retro/emu_sfc_compat_v2.log",
        "./emu_sfc_compat_v2.log",
        NULL
    };
    for (int i = 0; paths[i]; i++) {
        int fd = open(paths[i], O_WRONLY|O_CREAT|O_APPEND, 0666);
        if (fd >= 0) { log_fd = fd; break; }
    }
}
static void log_line(const char *s) { log_open_once(); log_raw(s); log_ch('\n'); if (log_fd >= 0) fsync(log_fd); }
static void log_kv_u(const char *k, uint64_t v) { log_raw(k); log_u64(v); }

static void *sym(const char *name) { if (!core_handle) return NULL; return dlsym(core_handle, name); }

static void load_core(void) {
    if (core_handle) return;
    log_open_once();
    log_raw("[emu_sfc_compat_v2] constructor/load variant="); log_raw(VARIANT_NAME);
    log_raw(" force_geom="); log_u64(FORCE_GEOM); log_raw(" target="); log_u64(TARGET_W); log_raw("x"); log_u64(TARGET_H); log_ch('\n');

    const char *paths[] = {
        "/usr/retro/libs/emu_sfc_new.so",
        "/media/sdcarda1/retro/libs/emu_sfc_new.so",
        "/media/sdcardb1/retro/libs/emu_sfc_new.so",
        "/retro/libs/emu_sfc_new.so",
        "./emu_sfc_new.so",
        "emu_sfc_new.so",
        NULL
    };
    for (int i = 0; paths[i]; i++) {
        core_handle = dlopen(paths[i], RTLD_NOW | RTLD_GLOBAL);
        if (core_handle) { log_raw("[emu_sfc_compat_v2] loaded "); log_raw(paths[i]); log_ch('\n'); break; }
    }
    if (!core_handle) {
        log_raw("[emu_sfc_compat_v2] ERROR failed to load emu_sfc_new.so");
        char *e = dlerror(); if (e) { log_raw(" dlerror="); log_raw(e); }
        log_ch('\n'); if (log_fd >= 0) fsync(log_fd); return;
    }

    p_retro_api_version = (unsigned (*)(void))sym("retro_api_version");
    p_retro_set_environment = (void (*)(retro_environment_t))sym("retro_set_environment");
    p_retro_set_video_refresh = (void (*)(retro_video_refresh_t))sym("retro_set_video_refresh");
    p_retro_set_audio_sample = (void (*)(retro_audio_sample_t))sym("retro_set_audio_sample");
    p_retro_set_audio_sample_batch = (void (*)(retro_audio_sample_batch_t))sym("retro_set_audio_sample_batch");
    p_retro_set_input_poll = (void (*)(retro_input_poll_t))sym("retro_set_input_poll");
    p_retro_set_input_state = (void (*)(retro_input_state_t))sym("retro_set_input_state");
    p_retro_init = (void (*)(void))sym("retro_init");
    p_retro_deinit = (void (*)(void))sym("retro_deinit");
    p_retro_get_system_info = (void (*)(struct retro_system_info*))sym("retro_get_system_info");
    p_retro_get_system_av_info = (void (*)(struct retro_system_av_info*))sym("retro_get_system_av_info");
    p_retro_set_controller_port_device = (void (*)(unsigned,unsigned))sym("retro_set_controller_port_device");
    p_retro_reset = (void (*)(void))sym("retro_reset");
    p_retro_run = (void (*)(void))sym("retro_run");
    p_retro_serialize_size = (size_t (*)(void))sym("retro_serialize_size");
    p_retro_serialize = (bool (*)(void*, size_t))sym("retro_serialize");
    p_retro_unserialize = (bool (*)(const void*, size_t))sym("retro_unserialize");
    p_retro_cheat_reset = (void (*)(void))sym("retro_cheat_reset");
    p_retro_cheat_set = (void (*)(unsigned,bool,const char*))sym("retro_cheat_set");
    p_retro_load_game = (bool (*)(const struct retro_game_info*))sym("retro_load_game");
    p_retro_load_game_special = (bool (*)(unsigned,const struct retro_game_info*,size_t))sym("retro_load_game_special");
    p_retro_unload_game = (void (*)(void))sym("retro_unload_game");
    p_retro_get_region = (unsigned (*)(void))sym("retro_get_region");
    p_retro_get_memory_data = (void *(*)(unsigned))sym("retro_get_memory_data");
    p_retro_get_memory_size = (size_t (*)(unsigned))sym("retro_get_memory_size");
}

__attribute__((constructor)) static void ctor(void) {
    log_open_once();
    log_raw("[emu_sfc_compat_v2] constructor variant="); log_raw(VARIANT_NAME);
    log_raw(" force_geom="); log_u64(FORCE_GEOM); log_raw(" target="); log_u64(TARGET_W); log_raw("x"); log_u64(TARGET_H); log_ch('\n');
    if (log_fd >= 0) fsync(log_fd);
}

static uint16_t convert_pixel(const void *row, unsigned x) {
    if (core_pixfmt == RETRO_PIXEL_FORMAT_RGB565) {
        const uint16_t *p = (const uint16_t*)row;
        return p[x];
    } else if (core_pixfmt == RETRO_PIXEL_FORMAT_XRGB8888) {
        const uint32_t *p = (const uint32_t*)row;
        uint32_t v = p[x];
        uint32_t r = (v >> 16) & 0xff;
        uint32_t g = (v >> 8) & 0xff;
        uint32_t b = v & 0xff;
        return (uint16_t)(((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3));
    } else {
        /* 0RGB1555 -> RGB565 */
        const uint16_t *p = (const uint16_t*)row;
        uint16_t v = p[x];
        uint16_t r = (v >> 10) & 0x1f;
        uint16_t g = (v >> 5) & 0x1f;
        uint16_t b = v & 0x1f;
        return (uint16_t)((r << 11) | ((g << 1) << 5) | b);
    }
}

static void log_video(unsigned w, unsigned h, unsigned pitch, unsigned outw, unsigned outh, int nulldata) {
    log_raw("[emu_sfc_compat_v2] video calls="); log_u64(video_calls);
    log_raw(" nulls="); log_u64(video_nulls);
    log_raw(" fmt="); log_u64(core_pixfmt);
    log_raw(" in="); log_u64(w); log_raw("x"); log_u64(h);
    log_raw(" pitch="); log_u64(pitch);
    log_raw(" out="); log_u64(outw); log_raw("x"); log_u64(outh);
    log_raw(" null="); log_u64((unsigned)nulldata);
    log_ch('\n'); if (log_fd >= 0) fsync(log_fd);
}

static void compat_video_cb(const void *data, unsigned width, unsigned height, size_t pitch) {
    video_calls++;
    if (!fe_video) return;
    unsigned outw = FORCE_GEOM ? TARGET_W : width;
    unsigned outh = FORCE_GEOM ? TARGET_H : height;
    if (outw == 0 || outh == 0) { fe_video(data, width, height, pitch); return; }

    if (!data) {
        video_nulls++;
        fe_video(NULL, outw, outh, outw * 2);
        if (video_calls <= 20 || (video_calls % 300) == 0 || width != last_w || height != last_h || pitch != last_pitch) {
            log_video(width, height, (unsigned)pitch, outw, outh, 1);
            last_w = width; last_h = height; last_pitch = (unsigned)pitch;
        }
        return;
    }

    if (outw > MAX_OUT_W || outh > MAX_OUT_H) {
        if (!warned_big) { log_line("[emu_sfc_compat_v2] WARNING output target too large; passing through"); warned_big = 1; }
        fe_video(data, width, height, pitch);
        return;
    }

    unsigned src_bpp = (core_pixfmt == RETRO_PIXEL_FORMAT_XRGB8888) ? 4 : 2;
    if (!FORCE_GEOM && core_pixfmt == RETRO_PIXEL_FORMAT_RGB565 && pitch == width * 2) {
        /* Already the safest format; pass through without copy. */
        fe_video(data, width, height, pitch);
    } else {
        for (unsigned y = 0; y < outh; y++) {
            unsigned sy = FORCE_GEOM ? ((uint64_t)y * height / outh) : y;
            const char *srcrow = (const char*)data + ((size_t)sy * pitch);
            uint16_t *dstrow = framebuf + ((size_t)y * outw);
            if (!FORCE_GEOM && core_pixfmt == RETRO_PIXEL_FORMAT_RGB565) {
                unsigned bytes = width * 2;
                if (bytes > outw * 2) bytes = outw * 2;
                memcpy(dstrow, srcrow, bytes);
            } else {
                for (unsigned x = 0; x < outw; x++) {
                    unsigned sx = FORCE_GEOM ? ((uint64_t)x * width / outw) : x;
                    dstrow[x] = convert_pixel(srcrow, sx);
                }
            }
        }
        fe_video(framebuf, outw, outh, outw * 2);
    }

    if (video_calls <= 20 || (video_calls % 300) == 0 || width != last_w || height != last_h || pitch != last_pitch) {
        log_video(width, height, (unsigned)pitch, outw, outh, 0);
        last_w = width; last_h = height; last_pitch = (unsigned)pitch;
    }
}

static size_t compat_audio_batch_cb(const int16_t *data, size_t frames) {
    audio_calls++;
    if ((unsigned)frames < audio_min) audio_min = (unsigned)frames;
    if ((unsigned)frames > audio_max) audio_max = (unsigned)frames;
    if (audio_calls <= 20 || (audio_calls % 300) == 0) {
        log_raw("[emu_sfc_compat_v2] audio calls="); log_u64(audio_calls);
        log_raw(" frames="); log_u64((uint64_t)frames);
        log_raw(" min="); log_u64(audio_min); log_raw(" max="); log_u64(audio_max); log_ch('\n');
        if (log_fd >= 0) fsync(log_fd);
    }
    if (fe_audio_batch) return fe_audio_batch(data, frames);
    return 0;
}

static void compat_audio_sample_cb(int16_t l, int16_t r) { if (fe_audio) fe_audio(l, r); }

static void sanitize_av(struct retro_system_av_info *info) {
    if (!info) return;
#if FORCE_GEOM
    info->geometry.base_width = TARGET_W;
    info->geometry.base_height = TARGET_H;
    info->geometry.max_width = TARGET_W;
    info->geometry.max_height = TARGET_H;
    if (info->geometry.aspect_ratio <= 0.01f) info->geometry.aspect_ratio = 4.0f / 3.0f;
#endif
    if (info->timing.sample_rate < 1.0) info->timing.sample_rate = 44100.0;
    if (info->timing.fps < 1.0) info->timing.fps = 59.922743;
}

static void log_av(const char *prefix, const struct retro_system_av_info *info) {
    if (!info) return;
    log_raw(prefix);
    log_raw(" geom="); log_u64(info->geometry.base_width); log_raw("x"); log_u64(info->geometry.base_height);
    log_raw(" max="); log_u64(info->geometry.max_width); log_raw("x"); log_u64(info->geometry.max_height);
    log_raw(" fps_set=1");
    log_raw(" sr_set=1");
    log_ch('\n'); if (log_fd >= 0) fsync(log_fd);
}

static bool compat_env_cb(unsigned cmd, void *data) {
    if (cmd == RETRO_ENVIRONMENT_SET_PIXEL_FORMAT) {
        unsigned requested = data ? *((unsigned*)data) : RETRO_PIXEL_FORMAT_0RGB1555;
        core_pixfmt = requested;
        log_raw("[emu_sfc_compat_v2] SET_PIXEL_FORMAT core_requested="); log_u64(requested); log_raw(" frontend_forced=2\n");
        if (fe_env) {
            unsigned fmt = RETRO_PIXEL_FORMAT_RGB565;
            fe_env(RETRO_ENVIRONMENT_SET_PIXEL_FORMAT, &fmt);
        }
        if (log_fd >= 0) fsync(log_fd);
        return true;
    }
    if (cmd == RETRO_ENVIRONMENT_SET_SYSTEM_AV_INFO) {
        struct retro_system_av_info copy;
        if (data) { copy = *((struct retro_system_av_info*)data); log_av("[emu_sfc_compat_v2] SET_SYSTEM_AV_INFO core", &copy); sanitize_av(&copy); log_av("[emu_sfc_compat_v2] SET_SYSTEM_AV_INFO frontend", &copy); if (fe_env) return fe_env(cmd, &copy); return true; }
    }
    if (cmd == RETRO_ENVIRONMENT_SET_GEOMETRY) {
        struct retro_game_geometry copy;
        if (data) {
            copy = *((struct retro_game_geometry*)data);
            log_raw("[emu_sfc_compat_v2] SET_GEOMETRY core="); log_u64(copy.base_width); log_raw("x"); log_u64(copy.base_height); log_ch('\n');
#if FORCE_GEOM
            copy.base_width = TARGET_W; copy.base_height = TARGET_H; copy.max_width = TARGET_W; copy.max_height = TARGET_H;
#endif
            if (log_fd >= 0) fsync(log_fd);
            if (fe_env) return fe_env(cmd, &copy); return true;
        }
    }
    if (cmd == RETRO_ENVIRONMENT_SET_VARIABLES) {
        log_line("[emu_sfc_compat_v2] SET_VARIABLES");
    }
    if (cmd == RETRO_ENVIRONMENT_GET_CORE_OPTIONS_VERSION || cmd == RETRO_ENVIRONMENT_SET_CORE_OPTIONS || cmd == RETRO_ENVIRONMENT_SET_CORE_OPTIONS_INTL || cmd == RETRO_ENVIRONMENT_SET_CORE_OPTIONS_V2 || cmd == RETRO_ENVIRONMENT_SET_CORE_OPTIONS_V2_INTL) {
        log_raw("[emu_sfc_compat_v2] env core_options cmd="); log_u64(cmd); log_ch('\n'); if (log_fd >= 0) fsync(log_fd);
    }
    if (fe_env) return fe_env(cmd, data);
    return false;
}


/* v2 ROM loader: newer Snes9x2010 expects game->data/game->size. vrtemu passes only a path. */
#define SEEK_SET 0
#define SEEK_END 2
#define ZIP_LOCAL_SIG 0x04034b50u
#define ZIP_CENTRAL_SIG 0x02014b50u
#define ZIP_EOCD_SIG 0x06054b50u
#define Z_FINISH 4
#define Z_STREAM_END 1
#define MAX_ROM_BYTES (16u * 1024u * 1024u)

static void *loaded_rom_data = NULL;
static size_t loaded_rom_size = 0;
static char loaded_rom_name[256];
static char loaded_rom_meta[64];

typedef void *(*alloc_func)(void *opaque, unsigned int items, unsigned int size);
typedef void (*free_func)(void *opaque, void *address);
typedef struct z_stream_s {
    unsigned char *next_in;
    unsigned int avail_in;
    unsigned long total_in;
    unsigned char *next_out;
    unsigned int avail_out;
    unsigned long total_out;
    char *msg;
    void *state;
    alloc_func zalloc;
    free_func zfree;
    void *opaque;
    int data_type;
    unsigned long adler;
    unsigned long reserved;
} z_stream;

static void *zlib_handle = NULL;
static const char *(*p_zlibVersion)(void) = NULL;
static int (*p_inflateInit2_)(z_stream*, int, const char*, int) = NULL;
static int (*p_inflate)(z_stream*, int) = NULL;
static int (*p_inflateEnd)(z_stream*) = NULL;

static unsigned rd16(const uint8_t *p) { return (unsigned)p[0] | ((unsigned)p[1] << 8); }
static uint32_t rd32(const uint8_t *p) { return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24); }
static char lower_c(char c) { if (c >= 'A' && c <= 'Z') return (char)(c + 32); return c; }
static int str_ends_rom(const char *s, unsigned n) {
    if (!s || n < 4) return 0;
    char a = lower_c(s[n-4]); char b = lower_c(s[n-3]); char c = lower_c(s[n-2]); char d = lower_c(s[n-1]);
    if (a != '.') return 0;
    if (b=='s' && c=='f' && d=='c') return 1;
    if (b=='s' && c=='m' && d=='c') return 1;
    if (b=='f' && c=='i' && d=='g') return 1;
    if (b=='s' && c=='w' && d=='c') return 1;
    if (b=='b' && c=='s' && d=='x') return 1;
    return 0;
}
static int path_ends_zip(const char *s) {
    unsigned n = cstrlen(s); if (n < 4) return 0;
    return lower_c(s[n-4])=='.' && lower_c(s[n-3])=='z' && lower_c(s[n-2])=='i' && lower_c(s[n-1])=='p';
}
static void set_loaded_name(const char *name, unsigned n) {
    if (!name || n == 0) { const char *d = "loaded.sfc"; n = cstrlen(d); name = d; }
    if (n >= sizeof(loaded_rom_name)) n = sizeof(loaded_rom_name)-1;
    for (unsigned i=0; i<n; i++) loaded_rom_name[i] = name[i];
    loaded_rom_name[n] = 0;
}
static void clear_loaded_rom(void) {
    if (loaded_rom_data) { free(loaded_rom_data); loaded_rom_data = NULL; }
    loaded_rom_size = 0; loaded_rom_name[0] = 0; loaded_rom_meta[0] = 0;
}
static void log_loader(const char *msg) { log_raw("[emu_sfc_compat_v2] loader "); log_raw(msg); log_ch('\n'); if (log_fd >= 0) fsync(log_fd); }

static void *read_entire_file(const char *path, size_t *out_size) {
    if (out_size) *out_size = 0;
    if (!path) return NULL;
    int fd = open(path, 0, 0);
    if (fd < 0) { log_loader("open failed"); return NULL; }
    long end = lseek(fd, 0, SEEK_END);
    if (end <= 0 || (unsigned long)end > MAX_ROM_BYTES) { close(fd); log_loader("bad file size"); return NULL; }
    lseek(fd, 0, SEEK_SET);
    uint8_t *buf = (uint8_t*)malloc((size_t)end);
    if (!buf) { close(fd); log_loader("malloc failed"); return NULL; }
    unsigned done = 0;
    while (done < (unsigned)end) {
        int r = read(fd, buf + done, (unsigned)end - done);
        if (r <= 0) { free(buf); close(fd); log_loader("read failed"); return NULL; }
        done += (unsigned)r;
    }
    close(fd);
    if (out_size) *out_size = (size_t)end;
    return buf;
}

static int load_zlib(void) {
    if (p_inflateInit2_ && p_inflate && p_inflateEnd) return 1;
    const char *paths[] = { "libz.so.1", "/lib/libz.so.1", "/usr/lib/libz.so.1", "/system/lib/libz.so.1", "libz.so", NULL };
    for (int i=0; paths[i]; i++) {
        zlib_handle = dlopen(paths[i], RTLD_NOW | RTLD_GLOBAL);
        if (zlib_handle) break;
    }
    if (!zlib_handle) { log_loader("libz dlopen failed"); return 0; }
    p_zlibVersion = (const char *(*)(void))dlsym(zlib_handle, "zlibVersion");
    p_inflateInit2_ = (int (*)(z_stream*, int, const char*, int))dlsym(zlib_handle, "inflateInit2_");
    p_inflate = (int (*)(z_stream*, int))dlsym(zlib_handle, "inflate");
    p_inflateEnd = (int (*)(z_stream*))dlsym(zlib_handle, "inflateEnd");
    if (!p_inflateInit2_ || !p_inflate || !p_inflateEnd) { log_loader("libz symbols missing"); return 0; }
    return 1;
}

static void *inflate_raw_entry(const uint8_t *src, unsigned comp_size, unsigned uncomp_size) {
    if (!src || comp_size == 0 || uncomp_size == 0 || uncomp_size > MAX_ROM_BYTES) return NULL;
    uint8_t *out = (uint8_t*)malloc(uncomp_size);
    if (!out) { log_loader("inflate malloc failed"); return NULL; }
    if (!load_zlib()) { free(out); return NULL; }
    z_stream zs;
    memset(&zs, 0, sizeof(zs));
    zs.next_in = (unsigned char*)src; zs.avail_in = comp_size;
    zs.next_out = out; zs.avail_out = uncomp_size;
    const char *ver = p_zlibVersion ? p_zlibVersion() : "1.2.8";
    int r = p_inflateInit2_(&zs, -15, ver, sizeof(zs));
    if (r != 0) { free(out); log_loader("inflateInit2 failed"); return NULL; }
    r = p_inflate(&zs, Z_FINISH);
    p_inflateEnd(&zs);
    if (r != Z_STREAM_END || zs.total_out != uncomp_size) { free(out); log_loader("inflate failed"); return NULL; }
    return out;
}

static int extract_zip_rom(const char *path) {
    size_t zsize = 0; uint8_t *zip = (uint8_t*)read_entire_file(path, &zsize);
    if (!zip) return 0;
    log_raw("[emu_sfc_compat_v2] loader zip_size="); log_u64(zsize); log_ch('\n');
    unsigned eocd_pos = 0xffffffffu;
    unsigned max_back = (zsize > 66000u) ? 66000u : (unsigned)zsize;
    for (unsigned back = 22; back <= max_back; back++) {
        unsigned pos = (unsigned)zsize - back;
        if (rd32(zip + pos) == ZIP_EOCD_SIG) { eocd_pos = pos; break; }
    }
    if (eocd_pos == 0xffffffffu) { free(zip); log_loader("EOCD not found"); return 0; }
    unsigned total = rd16(zip + eocd_pos + 10);
    unsigned cd_off = rd32(zip + eocd_pos + 16);
    log_raw("[emu_sfc_compat_v2] loader entries="); log_u64(total); log_raw(" cd_off="); log_u64(cd_off); log_ch('\n');
    if (cd_off >= zsize) { free(zip); log_loader("bad central offset"); return 0; }
    unsigned p = cd_off;
    for (unsigned i=0; i<total && p + 46 <= zsize; i++) {
        if (rd32(zip+p) != ZIP_CENTRAL_SIG) break;
        unsigned method = rd16(zip+p+10);
        unsigned comp_size = rd32(zip+p+20);
        unsigned uncomp_size = rd32(zip+p+24);
        unsigned namelen = rd16(zip+p+28);
        unsigned extralen = rd16(zip+p+30);
        unsigned commentlen = rd16(zip+p+32);
        unsigned lhoff = rd32(zip+p+42);
        const char *name = (const char*)(zip+p+46);
        if (p + 46 + namelen + extralen + commentlen > zsize) break;
        if (str_ends_rom(name, namelen) && uncomp_size > 0 && uncomp_size <= MAX_ROM_BYTES && lhoff + 30 <= zsize && rd32(zip+lhoff) == ZIP_LOCAL_SIG) {
            unsigned l_namelen = rd16(zip+lhoff+26);
            unsigned l_extralen = rd16(zip+lhoff+28);
            unsigned data_off = lhoff + 30 + l_namelen + l_extralen;
            if (data_off + comp_size <= zsize) {
                void *out = NULL;
                if (method == 0) {
                    out = malloc(uncomp_size);
                    if (out) memcpy(out, zip + data_off, uncomp_size);
                } else if (method == 8) {
                    out = inflate_raw_entry(zip + data_off, comp_size, uncomp_size);
                } else {
                    log_loader("unsupported zip method");
                }
                if (out) {
                    clear_loaded_rom();
                    loaded_rom_data = out; loaded_rom_size = uncomp_size; set_loaded_name(name, namelen);
                    log_raw("[emu_sfc_compat_v2] loader extracted name="); log_raw(loaded_rom_name);
                    log_raw(" size="); log_u64(loaded_rom_size); log_raw(" method="); log_u64(method); log_ch('\n'); if (log_fd >= 0) fsync(log_fd);
                    free(zip); return 1;
                }
            }
        }
        p += 46 + namelen + extralen + commentlen;
    }
    free(zip); log_loader("no ROM entry extracted"); return 0;
}

static int load_game_data_from_path(const char *path) {
    clear_loaded_rom();
    if (!path) return 0;
    if (path_ends_zip(path)) return extract_zip_rom(path);
    size_t sz = 0; void *buf = read_entire_file(path, &sz);
    if (!buf) return 0;
    loaded_rom_data = buf; loaded_rom_size = sz;
    unsigned n = cstrlen(path); unsigned start = n;
    while (start > 0 && path[start-1] != '/') start--;
    set_loaded_name(path + start, n - start);
    log_raw("[emu_sfc_compat_v2] loader loaded raw name="); log_raw(loaded_rom_name); log_raw(" size="); log_u64(loaded_rom_size); log_ch('\n'); if (log_fd >= 0) fsync(log_fd);
    return 1;
}

RETRO_API unsigned retro_api_version(void) { load_core(); return p_retro_api_version ? p_retro_api_version() : RETRO_API_VERSION; }
RETRO_API void retro_set_environment(retro_environment_t cb) {
    fe_env = cb; load_core();
    log_line("[emu_sfc_compat_v2] retro_set_environment");
    if (fe_env) { unsigned fmt = RETRO_PIXEL_FORMAT_RGB565; fe_env(RETRO_ENVIRONMENT_SET_PIXEL_FORMAT, &fmt); }
    if (p_retro_set_environment) p_retro_set_environment(compat_env_cb);
}
RETRO_API void retro_set_video_refresh(retro_video_refresh_t cb) { fe_video = cb; load_core(); log_line("[emu_sfc_compat_v2] retro_set_video_refresh wrapped"); if (p_retro_set_video_refresh) p_retro_set_video_refresh(compat_video_cb); }
RETRO_API void retro_set_audio_sample(retro_audio_sample_t cb) { fe_audio = cb; load_core(); if (p_retro_set_audio_sample) p_retro_set_audio_sample(compat_audio_sample_cb); }
RETRO_API void retro_set_audio_sample_batch(retro_audio_sample_batch_t cb) { fe_audio_batch = cb; load_core(); log_line("[emu_sfc_compat_v2] retro_set_audio_sample_batch wrapped"); if (p_retro_set_audio_sample_batch) p_retro_set_audio_sample_batch(compat_audio_batch_cb); }
RETRO_API void retro_set_input_poll(retro_input_poll_t cb) { fe_input_poll = cb; load_core(); if (p_retro_set_input_poll) p_retro_set_input_poll(cb); }
RETRO_API void retro_set_input_state(retro_input_state_t cb) { fe_input_state = cb; load_core(); if (p_retro_set_input_state) p_retro_set_input_state(cb); }
RETRO_API void retro_init(void) { load_core(); log_line("[emu_sfc_compat_v2] retro_init"); if (p_retro_init) p_retro_init(); }
RETRO_API void retro_deinit(void) { log_line("[emu_sfc_compat_v2] retro_deinit"); if (p_retro_deinit) p_retro_deinit(); if (log_fd >= 0) { fsync(log_fd); close(log_fd); log_fd = -1; } }
RETRO_API void retro_get_system_info(struct retro_system_info *info) { load_core(); if (p_retro_get_system_info) p_retro_get_system_info(info); }
RETRO_API void retro_get_system_av_info(struct retro_system_av_info *info) { load_core(); if (p_retro_get_system_av_info) p_retro_get_system_av_info(info); log_av("[emu_sfc_compat_v2] get_av core", info); sanitize_av(info); log_av("[emu_sfc_compat_v2] get_av frontend", info); }
RETRO_API void retro_set_controller_port_device(unsigned port, unsigned device) { load_core(); if (p_retro_set_controller_port_device) p_retro_set_controller_port_device(port, device); }
RETRO_API void retro_reset(void) { load_core(); if (p_retro_reset) p_retro_reset(); }
RETRO_API void retro_run(void) { load_core(); if (p_retro_run) p_retro_run(); }
RETRO_API size_t retro_serialize_size(void) { load_core(); return p_retro_serialize_size ? p_retro_serialize_size() : 0; }
RETRO_API bool retro_serialize(void *data, size_t size) { load_core(); return p_retro_serialize ? p_retro_serialize(data, size) : false; }
RETRO_API bool retro_unserialize(const void *data, size_t size) { load_core(); return p_retro_unserialize ? p_retro_unserialize(data, size) : false; }
RETRO_API void retro_cheat_reset(void) { load_core(); if (p_retro_cheat_reset) p_retro_cheat_reset(); }
RETRO_API void retro_cheat_set(unsigned index, bool enabled, const char *code) { load_core(); if (p_retro_cheat_set) p_retro_cheat_set(index, enabled, code); }
RETRO_API bool retro_load_game(const struct retro_game_info *game) {
    load_core();
    log_raw("[emu_sfc_compat_v2] retro_load_game path="); log_raw(game ? game->path : "(null)");
    log_raw(" data="); log_u64(game && game->data ? 1 : 0); log_raw(" size="); log_u64(game ? game->size : 0); log_ch('\n');
    if (log_fd >= 0) fsync(log_fd);

    struct retro_game_info fixed;
    const struct retro_game_info *use_game = game;
    if (game && !game->data && game->path) {
        if (load_game_data_from_path(game->path)) {
            fixed = *game;
            fixed.path = loaded_rom_name[0] ? loaded_rom_name : game->path;
            fixed.data = loaded_rom_data;
            fixed.size = loaded_rom_size;
            fixed.meta = loaded_rom_meta;
            use_game = &fixed;
            log_raw("[emu_sfc_compat_v2] retro_load_game using memory path="); log_raw(fixed.path);
            log_raw(" size="); log_u64(fixed.size); log_ch('\n'); if (log_fd >= 0) fsync(log_fd);
        } else {
            log_line("[emu_sfc_compat_v2] retro_load_game memory load failed; passing original");
        }
    }

    bool ok = p_retro_load_game ? p_retro_load_game(use_game) : false;
    log_raw("[emu_sfc_compat_v2] retro_load_game result="); log_u64(ok ? 1 : 0); log_ch('\n'); if (log_fd >= 0) fsync(log_fd);
    struct retro_system_av_info av; if (p_retro_get_system_av_info) { p_retro_get_system_av_info(&av); log_av("[emu_sfc_compat_v2] post-load av core", &av); }
    return ok;
}
RETRO_API bool retro_load_game_special(unsigned type, const struct retro_game_info *info, size_t num) { load_core(); return p_retro_load_game_special ? p_retro_load_game_special(type, info, num) : false; }
RETRO_API void retro_unload_game(void) { load_core(); if (p_retro_unload_game) p_retro_unload_game(); clear_loaded_rom(); }
RETRO_API unsigned retro_get_region(void) { load_core(); return p_retro_get_region ? p_retro_get_region() : RETRO_REGION_NTSC; }
RETRO_API void *retro_get_memory_data(unsigned id) { load_core(); return p_retro_get_memory_data ? p_retro_get_memory_data(id) : NULL; }
RETRO_API size_t retro_get_memory_size(unsigned id) { load_core(); return p_retro_get_memory_size ? p_retro_get_memory_size(id) : 0; }
