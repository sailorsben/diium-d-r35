#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <stdarg.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
#include <glob.h>
#include <dirent.h>
#include <sys/stat.h>
#include <sys/utsname.h>
#include <time.h>
#include <sys/syscall.h>
#include <linux/perf_event.h>
#include <sys/klog.h>

/* Passive, bounded one-boot collector. No device opens, ioctls, sysfs writes,
 * direct register access, module loading, or emulator changes. Optional Linux
 * perf capability checks own this collector's counters only, never the game. */
#define REPORT_CAP (512u * 1024u)
#define FILE_CAP (64u * 1024u)
static char report[REPORT_CAP], scratch[FILE_CAP + 1];
static size_t used;
static int capped;
static const char *root = "";
static double started;
static int probe_nice_result;
extern int __xstat64(int, const char *, struct stat64 *);
static double now(void) {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t)) return 0;
    return t.tv_sec + t.tv_nsec / 1000000000.0;
}
static void add(const char *fmt, ...) {
    va_list ap;
    int n;
    if (capped) return;
    va_start(ap, fmt);
    n = vsnprintf(report + used, REPORT_CAP - used - 512, fmt, ap);
    va_end(ap);
    if (n < 0 || (size_t)n >= REPORT_CAP - used - 512) { capped = 1; return; }
    used += (size_t)n;
}
static void escaped(const char *s, size_t n) {
    size_t i;
    add("\"");
    for (i = 0; i < n && !capped; ++i) {
        unsigned char c = (unsigned char)s[i];
        if (c == '"' || c == '\\') add("\\%c", c);
        else if (c == '\n') add("\\n");
        else if (c == '\r') add("\\r");
        else if (c == '\t') add("\\t");
        else if (c < 32 || c > 126) add("\\u%04x", c);
        else add("%c", c);
    }
    add("\"");
}
static int fullpath(char *out, size_t cap, const char *path) {
    int n = snprintf(out, cap, "%s%s", root, path);
    return n >= 0 && (size_t)n < cap;
}
static void file(const char *path, int hex, size_t limit) {
    char real[1024];
    size_t begin = used, total = 0, i;
    int fd, saved = 0, truncated = 0;
    ssize_t n;
    if (capped || !fullpath(real, sizeof(real), path)) return;
    if (limit > FILE_CAP) limit = FILE_CAP;
    fd = open(real, O_RDONLY | O_CLOEXEC | O_NONBLOCK);
    if (fd < 0) saved = errno;
    else {
        while (total < limit) {
            char chunk[1024];
            size_t remaining = limit - total;
            if (total >= FILE_CAP || remaining > FILE_CAP - total) { saved = EOVERFLOW; break; }
            if (remaining > sizeof(chunk)) remaining = sizeof(chunk);
            n = read(fd, chunk, remaining);
            if (n < 0) { if (errno == EINTR) continue; saved = errno; break; }
            if (!n) break;
            if ((size_t)n > remaining) { saved = EOVERFLOW; break; }
            memcpy(scratch + total, chunk, (size_t)n);
            total += (size_t)n;
        }
        if (total == limit) {
            char extra;
            n = read(fd, &extra, 1);
            truncated = n > 0;
        }
        close(fd);
    }
    add("{\"kind\":\"file\",\"elapsed\":%.6f,\"path\":", now() - started);
    escaped(path, strlen(path));
    add(",\"errno\":%d,\"truncated\":%s,\"encoding\":\"%s\",\"data\":", saved,
        truncated ? "true" : "false", hex ? "hex" : "text");
    if (hex) {
        add("\"");
        for (i = 0; i < total && !capped; ++i) add("%02x", (unsigned char)scratch[i]);
        add("\"");
    } else escaped(scratch, total);
    add("}\n");
    /* Never leave a partial JSON record on the report size boundary. */
    if (capped) used = begin;
}
static void pattern(const char *pat, size_t limit, unsigned maximum) {
    char real[1024]; glob_t g; size_t i;
    if (capped || !fullpath(real, sizeof(real), pat)) return;
    memset(&g, 0, sizeof(g));
    if (!glob(real, 0, NULL, &g))
        for (i = 0; i < g.gl_pathc && i < maximum && !capped; ++i)
            file(g.gl_pathv[i] + strlen(root), 0, limit);
    globfree(&g);
}
static void node(const char *path) {
    char real[1024]; struct stat64 st; size_t begin = used;
    int rc, saved;
    if (capped || !fullpath(real, sizeof(real), path)) return;
    rc = __xstat64(3, real, &st); saved = rc ? errno : 0;
    add("{\"kind\":\"node\",\"path\":"); escaped(path, strlen(path));
    add(",\"errno\":%d,\"mode\":%u,\"rdev\":%llu}\n", saved,
        rc ? 0 : (unsigned)st.st_mode, rc ? 0 : (unsigned long long)st.st_rdev);
    if (capped) used = begin;
}
static void perf_capability(void) {
    const struct { const char *name; uint32_t type; uint64_t config; } events[] = {
        {"task_clock", PERF_TYPE_SOFTWARE, PERF_COUNT_SW_TASK_CLOCK},
        {"cycles", PERF_TYPE_HARDWARE, PERF_COUNT_HW_CPU_CYCLES},
        {"instructions", PERF_TYPE_HARDWARE, PERF_COUNT_HW_INSTRUCTIONS},
        {"branch_misses", PERF_TYPE_HARDWARE, PERF_COUNT_HW_BRANCH_MISSES},
        {"l1d_read_misses", PERF_TYPE_HW_CACHE, PERF_COUNT_HW_CACHE_L1D |
          ((uint64_t)PERF_COUNT_HW_CACHE_OP_READ << 8) |
          ((uint64_t)PERF_COUNT_HW_CACHE_RESULT_MISS << 16)},
        {"l2_refill_raw_0x17", PERF_TYPE_RAW, 0x17}
    };
    unsigned i;
    for (i = 0; i < sizeof(events)/sizeof(events[0]) && !capped; ++i) {
        struct perf_event_attr attr;
        uint64_t values[3] = {0,0,0};
        int fd, saved; ssize_t n = -1; size_t begin = used;
        memset(&attr, 0, sizeof(attr));
        attr.size = PERF_ATTR_SIZE_VER0; /* stable Linux >= 2.6.31 ABI */
        attr.type = events[i].type; attr.config = events[i].config;
        attr.exclude_kernel = 1; attr.exclude_hv = 1;
        attr.read_format = PERF_FORMAT_TOTAL_TIME_ENABLED | PERF_FORMAT_TOTAL_TIME_RUNNING;
        /* Count this helper only. No attach, sampling interrupt or mmap. */
        fd = (int)syscall(__NR_perf_event_open, &attr, 0, -1, -1, 0);
        saved = fd < 0 ? errno : 0;
        if (fd >= 0) {
            struct timespec t;
            (void)clock_gettime(CLOCK_MONOTONIC, &t);
            n = read(fd, values, sizeof(values));
            if (n < 0) saved = errno;
            close(fd);
        }
        add("{\"kind\":\"perf_capability\",\"event\":");
        escaped(events[i].name, strlen(events[i].name));
        add(",\"errno\":%d,\"read_bytes\":%ld,\"count\":%llu,\"enabled_ns\":%llu,\"running_ns\":%llu,\"scope\":\"collector_only\"}\n",
            saved, (long)n, (unsigned long long)values[0],
            (unsigned long long)values[1], (unsigned long long)values[2]);
        if (capped) used = begin;
    }
}
static void inventory(void) {
    const char *text[] = {
        "/proc/cpuinfo", "/proc/meminfo", "/proc/cmdline", "/proc/version",
        "/proc/modules", "/proc/mounts", "/proc/iomem", "/proc/interrupts",
        "/proc/swaps", "/proc/partitions", "/proc/devices", "/proc/fb",
        "/proc/asound/cards", "/proc/asound/pcm", "/proc/asound/version",
        "/proc/asound/oss/sndstat", "/proc/asound/card0/pcm0p/info",
        "/proc/asound/card0/pcm0p/oss", "/proc/sys/kernel/perf_event_paranoid",
        "/sys/devices/system/cpu/online", "/sys/devices/system/cpu/possible",
        "/sys/devices/system/cpu/present", "/sys/kernel/debug/clk/clk_summary",
        "/proc/driver/galcore/version", "/proc/consoles", "/proc/tty/drivers",
        "/proc/sys/kernel/printk", "/sys/kernel/irq/19/actions",
        "/sys/kernel/irq/19/hwirq", "/sys/kernel/irq/19/name", NULL
    };
    const char *nodes[] = { "/dev/dsp", "/dev/snd/pcmC0D0p", "/dev/galcore",
        "/dev/chunkmem", "/dev/scale", "/dev/pscaler", "/dev/disp1", NULL };
    const char *cache[] = {"type", "level", "size", "coherency_line_size",
        "ways_of_associativity", "number_of_sets", NULL};
    unsigned i; char pat[256];
    for (i = 0; text[i]; ++i) file(text[i], 0, 8192);
    for (i = 0; nodes[i]; ++i) node(nodes[i]);
    for (i = 0; cache[i]; ++i) {
        snprintf(pat, sizeof(pat), "/sys/devices/system/cpu/cpu*/cache/index*/%s", cache[i]);
        pattern(pat, 128, 16);
    }
    pattern("/sys/devices/system/cpu/cpufreq/policy*/*freq*", 1024, 24);
    pattern("/sys/devices/system/cpu/cpu*/cpufreq/*freq*", 1024, 24);
    pattern("/sys/devices/system/cpu/cpufreq/policy*/scaling_governor", 128, 8);
    pattern("/sys/devices/system/cpu/cpufreq/policy*/scaling_available_governors", 1024, 8);
    pattern("/sys/devices/platform/*/uevent", 1024, 48);
    pattern("/sys/bus/event_source/devices/*/type", 128, 16);
    file("/proc/device-tree/model", 1, 1024);
    file("/proc/device-tree/compatible", 1, 1024);
    file("/proc/device-tree/cpus/cpu@0/compatible", 1, 1024);
    file("/proc/device-tree/cpus/cpu@0/clock-frequency", 1, 128);
    file("/proc/device-tree/cpus/cpu@0/clocks", 1, 128);
    pattern("/proc/device-tree/memory*/reg", 1024, 8);
    file("/sys/firmware/fdt", 1, FILE_CAP);
    file("/proc/config.gz", 1, 16384);
    pattern("/sys/class/graphics/fb*/virtual_size", 128, 4);
    pattern("/sys/class/graphics/fb*/bits_per_pixel", 128, 4);
    pattern("/sys/class/graphics/fb*/modes", 1024, 4);
}

/* SYSLOG_ACTION_READ_ALL (3) leaves the kernel log intact. Never use READ,
 * READ_CLEAR or /proc/kmsg, which would consume another reader's messages. */
static void kernel_log(void) {
    int n, saved = 0; size_t begin = used;
    if (capped) return;
    if (root[0]) { file("/fixture/kernel-log.txt", 0, 16384); return; }
    n = klogctl(3, scratch, 16384);
    if (n < 0) { saved = errno; n = 0; }
    add("{\"kind\":\"kernel_log\",\"elapsed\":%.6f,\"errno\":%d,\"at_capacity\":%s,\"data\":",
        now()-started, saved, n == 16384 ? "true" : "false");
    escaped(scratch, (size_t)n); add("}\n");
    if (capped) used = begin;
}
static void fd_links(const char *pid) {
    char real[1024], path[256], target[1024]; DIR *d; struct dirent64 *ent;
    unsigned count = 0;
    snprintf(path, sizeof(path), "/proc/%.20s/fd", pid);
    if (!fullpath(real, sizeof(real), path)) return;
    d = opendir(real); if (!d) return;
    while ((ent = readdir64(d)) && count < 32 && !capped) {
        ssize_t n; int saved; size_t begin = used;
        if (ent->d_name[0] < '0' || ent->d_name[0] > '9') continue;
        ++count;
        snprintf(path, sizeof(path), "/proc/%.20s/fd/%.20s", pid, ent->d_name);
        if (!fullpath(real, sizeof(real), path)) continue;
        n = readlink(real, target, sizeof(target)); saved = n < 0 ? errno : 0;
        add("{\"kind\":\"fd_link\",\"elapsed\":%.6f,\"path\":", now()-started);
        escaped(path, strlen(path)); add(",\"errno\":%d,\"at_capacity\":%s,\"target\":",
            saved, n >= 0 && (size_t)n == sizeof(target) ? "true" : "false");
        escaped(target, n < 0 ? 0 : (size_t)n); add("}\n");
        if (capped) used = begin;
    }
    closedir(d);
}
static void kernel_symbols(void) {
    char real[1024], line[1024], matches[16385];
    size_t scan = 0, count = 0, begin = used; int saved = 0, limited = 0; FILE *f;
    if (capped || !fullpath(real, sizeof(real), "/proc/kallsyms")) return;
    f = fopen(real, "r");
    if (!f) saved = errno;
    else {
        while (fgets(line, sizeof(line), f)) {
            size_t n = strlen(line); scan += n;
            if (scan > 4u*1024u*1024u) { limited = 1; break; }
            if (strcasestr(line, "pscaler") || strcasestr(line, "gp_scale") ||
                strcasestr(line, "gphalscale") || strcasestr(line, "gp_dac") ||
                strcasestr(line, "gphaldac") || strcasestr(line, "gp_uart") ||
                strcasestr(line, "gphaluart") || strcasestr(line, "gpa7xxxa")) {
                if (n > sizeof(matches)-1-count) { limited = 1; break; }
                memcpy(matches+count, line, n); count += n;
            }
        }
        if (ferror(f)) saved = errno ? errno : EIO;
        fclose(f);
    }
    add("{\"kind\":\"kernel_symbols\",\"elapsed\":%.6f,\"errno\":%d,\"limited\":%s,\"scanned_bytes\":%u,\"data\":",
        now()-started, saved, limited ? "true" : "false", (unsigned)scan);
    escaped(matches, count); add("}\n");
    if (capped) used = begin;
}

static void tasks(int details) {
    char real[1024], path[256], comm[64]; DIR *d; struct dirent64 *ent;
    unsigned count = 0;
    if (!fullpath(real, sizeof(real), "/proc")) return;
    d = opendir(real); if (!d) return;
    while ((ent = readdir64(d)) && !capped && count < 8) {
        int fd; ssize_t n; DIR *td; struct dirent64 *te; unsigned threads = 0;
        if (ent->d_name[0] < '0' || ent->d_name[0] > '9') continue;
        snprintf(path, sizeof(path), "/proc/%.20s/comm", ent->d_name);
        if (!fullpath(real, sizeof(real), path)) continue;
        fd = open(real, O_RDONLY | O_CLOEXEC); if (fd < 0) continue;
        n = read(fd, comm, sizeof(comm)-1); close(fd); if (n <= 0) continue;
        comm[n] = 0;
        if (strncmp(comm, "vrtemu\n", 7) && strncmp(comm, "main\n", 5)) continue;
        ++count;
        if (details) {
            fd_links(ent->d_name);
            const char *fields[] = {"status", "maps", "io", NULL}; unsigned i;
            for (i = 0; fields[i]; ++i) {
                snprintf(path, sizeof(path), "/proc/%.20s/%s", ent->d_name, fields[i]);
                file(path, 0, 16384);
            }
        }
        snprintf(path, sizeof(path), "/proc/%.20s/task", ent->d_name);
        if (!fullpath(real, sizeof(real), path)) continue;
        td = opendir(real); if (!td) continue;
        while ((te = readdir64(td)) && threads < 24 && !capped) {
            if (te->d_name[0] < '0' || te->d_name[0] > '9') continue;
            ++threads;
            snprintf(path, sizeof(path), "/proc/%.20s/task/%.20s/stat", ent->d_name, te->d_name);
            file(path, 0, 2048);
            snprintf(path, sizeof(path), "/proc/%.20s/task/%.20s/schedstat", ent->d_name, te->d_name);
            file(path, 0, 256);
            if (details) {
                snprintf(path, sizeof(path), "/proc/%.20s/task/%.20s/status", ent->d_name, te->d_name);
                file(path, 0, 2048);
                snprintf(path, sizeof(path), "/proc/%.20s/task/%.20s/wchan", ent->d_name, te->d_name);
                file(path, 0, 256);
            }
        }
        closedir(td);
    }
    closedir(d);
}
static void sample(unsigned i) {
    size_t begin = used;
    add("{\"kind\":\"sample\",\"number\":%u,\"elapsed\":%.6f}\n", i, now()-started);
    if (capped) used = begin;
    file("/proc/stat", 0, 4096);
    file("/proc/uptime", 0, 128);
    file("/proc/meminfo", 0, 2048);
    pattern("/sys/devices/system/cpu/cpufreq/policy*/scaling_cur_freq", 128, 8);
    pattern("/sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq", 128, 8);
    pattern("/sys/class/thermal/thermal_zone*/temp", 128, 8);
    pattern("/sys/class/thermal/thermal_zone*/type", 128, 8);
    pattern("/proc/asound/card*/pcm*p/sub*/hw_params", 1024, 8);
    pattern("/proc/asound/card*/pcm*p/sub*/status", 2048, 8);
    pattern("/proc/asound/card*/pcm*p/oss", 2048, 8);
    pattern("/proc/tty/driver/*", 8192, 8);
    file("/proc/interrupts", 0, 8192);
    tasks(i % 15 == 0 || i == 44);
    if (i == 44) kernel_log();
    if (i == 0 || i == 44) file("/proc/interrupts", 0, 8192);
}
int main(int argc, char **argv) {
    unsigned i, samples = 45; int quick = 0; FILE *f; struct utsname u;
    const char *output;
    if (argc == 2 && !strcmp(argv[1], "--quick")) {
        quick = 1; samples = 1; output = "hardware-probe-test.jsonl";
        root = getenv("D35_PROBE_ROOT"); if (!root) root = "";
    } else if (argc == 4 && !strcmp(argv[1], "--once")) {
        char claimed[1024];
        int n = snprintf(claimed, sizeof(claimed), "%s.started", argv[2]);
        if (n < 0 || (size_t)n >= sizeof(claimed)) return 2;
        if (rename(argv[2], claimed)) return 0; /* not armed => no repeated run */
        output = argv[3];
        probe_nice_result = nice(10); /* lower priority of this collector only */
    } else { fprintf(stderr, "usage: hardware_probe --once marker output | --quick\n"); return 2; }
    started = now();
    add("{\"kind\":\"header\",\"version\":2,\"samples\":%u,\"interval_seconds\":2,\"clk_tck\":%ld,\"max_report_bytes\":%u,\"passive\":true,\"collector_nice_result\":%d}\n",
        samples, sysconf(_SC_CLK_TCK), REPORT_CAP, probe_nice_result);
    if (!uname(&u)) { add("{\"kind\":\"uname\",\"machine\":"); escaped(u.machine, strlen(u.machine)); add("}\n"); }
    perf_capability();
    inventory();
    pattern("/proc/tty/driver/*", 8192, 8);
    pattern("/lib/modules/*/modules.builtin", 32768, 4);
    file("/proc/mtd", 0, 8192);
    pattern("/sys/class/mtd/*/name", 256, 8);
    pattern("/sys/class/mtd/*/size", 256, 8);
    file("/sys/class/misc/pscaler_a/dev", 0, 256);
    file("/sys/class/misc/pscaler_a/device/uevent", 0, 1024);
    kernel_symbols();
    kernel_log();
    if (!quick) sleep(15);
    for (i = 0; i < samples && !capped; ++i) {
        sample(i);
        if (!quick && i+1 < samples) {
            struct timespec remaining = {2, 0};
            while (nanosleep(&remaining, &remaining) && errno == EINTR) {}
        }
    }
    /* Use reserved tail even if capped. */
    {
        int n = snprintf(report + used, REPORT_CAP-used,
            "{\"kind\":\"complete\",\"elapsed\":%.6f,\"report_capped\":%s}\n",
            now()-started, capped ? "true" : "false");
        if (n > 0 && (size_t)n < REPORT_CAP-used) used += (size_t)n;
    }
    f = fopen(output, "wb"); if (!f) return 3;
    if (fwrite(report, 1, used, f) != used) { fclose(f); return 4; }
    return fclose(f) ? 5 : 0;
}
