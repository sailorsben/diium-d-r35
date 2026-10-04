"""Generate a separate passive console/IRQ follow-up using the proven collector."""
from pathlib import Path

base = Path(__file__).resolve().parent
src = (base / 'hardware-inventory.c').read_text()
src = src.replace('#include <linux/perf_event.h>', '#include <linux/perf_event.h>\n#include <sys/klog.h>')
helper = r'''
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
    char real[1024], path[256], target[1024]; DIR *d; struct dirent *ent;
    unsigned count = 0;
    snprintf(path, sizeof(path), "/proc/%.20s/fd", pid);
    if (!fullpath(real, sizeof(real), path)) return;
    d = opendir(real); if (!d) return;
    while ((ent = readdir(d)) && count < 32 && !capped) {
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
'''
src = src.replace('static void tasks(int details) {', helper + '\nstatic void tasks(int details) {')
src = src.replace('if (details) {\n            const char *fields', 'if (details) {\n            fd_links(ent->d_name);\n            const char *fields')
src = src.replace('"/proc/driver/galcore/version", NULL', '"/proc/driver/galcore/version", "/proc/consoles", "/proc/tty/drivers",\n        "/proc/sys/kernel/printk", "/sys/kernel/irq/19/actions",\n        "/sys/kernel/irq/19/hwirq", "/sys/kernel/irq/19/name", NULL')
src = src.replace('tasks(i % 15 == 0 || i == 44);', '''pattern("/proc/tty/driver/*", 8192, 8);
    file("/proc/interrupts", 0, 8192);
    tasks(i % 15 == 0 || i == 44);
    if (i == 44) kernel_log();''')
src = src.replace('inventory();\n    if (!quick)', '''inventory();
    pattern("/proc/tty/driver/*", 8192, 8);
    pattern("/lib/modules/*/modules.builtin", 32768, 4);
    file("/proc/mtd", 0, 8192);
    pattern("/sys/class/mtd/*/name", 256, 8);
    pattern("/sys/class/mtd/*/size", 256, 8);
    file("/sys/class/misc/pscaler_a/dev", 0, 256);
    file("/sys/class/misc/pscaler_a/device/uevent", 0, 1024);
    kernel_symbols();
    kernel_log();
    if (!quick)''')
src = src.replace('\\\"version\\\":1', '\\\"version\\\":2')
src = src.replace('struct dirent *', 'struct dirent64 *').replace('readdir(', 'readdir64(')
(base / 'hardware-runtime-probe.c').write_text(src, newline='\n')
build = (base / 'build-hardware-inventory.sh').read_text().replace('hardware-inventory', 'hardware-runtime-probe')
build = build.replace('hardware-runtime-probe.c', 'hardware-runtime-probe.c')
(base / 'build-hardware-runtime-probe.sh').write_text(build, newline='\n')
verify = (base / 'verify-hardware-inventory.py').read_text().replace("base = workspace / 'build/hardware-inventory'", "base = workspace / 'build/hardware-runtime-probe'")
verify = verify.replace("put('/proc/cpuinfo'", "put('/fixture/kernel-log.txt', b'fixture only: no host kernel read\\n')\n    put('/proc/cpuinfo'")
verify = verify.replace("put('/dev/dsp'", "put('/proc/kallsyms', b'c0001234 T gp_pscaler_probe\\nc0005678 T unrelated_symbol\\n')\n    put('/dev/dsp'")
verify = verify.replace("results['unarmed'] =", """sparse_records = [json.loads(line) for line in (base / 'sparse/hardware-probe-test.jsonl').read_bytes().splitlines()]
symbols = next(r for r in sparse_records if r['kind'] == 'kernel_symbols')
assert 'gp_pscaler_probe' in symbols['data'] and 'unrelated_symbol' not in symbols['data']
assert symbols['errno'] == 0 and not symbols['limited']
assert sparse_records[0]['version'] == 2
assert not any(r['kind'] == 'kernel_log' for r in sparse_records)
results['kernel_symbol_filter'] = {'verified': True, 'host_log_not_read_in_fixture': True}
links = [r for r in sparse_records if r['kind'] == 'fd_link']
if links:
    assert links[0]['target'] == '/dev/console' and links[0]['errno'] == 0
    results['fd_symlink'] = {'verified': True, 'target': '/dev/console', 'no_device_open': True}
results['unarmed'] =""")
(base / 'verify-hardware-runtime-probe.py').write_text(verify, newline='\n')
install = (base / 'install-hardware-inventory.py').read_text().replace('Hardware-Inventory-v1', 'Hardware-Runtime-v2')
install = install.replace('hardware_probe_v1', 'hardware_probe_v2').replace('build/hardware-inventory/', 'build/hardware-runtime-probe/')
install = install.replace('one-shot passive hardware inventory', 'one-shot passive console and IRQ inventory')
(base / 'install-hardware-runtime-probe.py').write_text(install, newline='\n')
print('Prepared separate v2 source, build, verification and installation scripts')
