/* Exact single-A7 kernel only. Capture the original entry status read, then
 * resume the original ISR body. Never patch kernel text or read extra status.
 * A module reference prevents unloading until the owned hook is detached.
 */
#include <linux/module.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <linux/uaccess.h>
#include <linux/irqflags.h>
#include <linux/kallsyms.h>
#include <linux/interrupt.h>
#include "uart-status-guards.h"

#define PORT 0xc072961cu
#define ISR 0xc01177dcu
#define CAP 200000u
#define SLOTS 32
struct bucket { u32 status, count; };
struct capture {
    u32 total, rx, tx_only, neither, rx_then_tx, handled, other_return;
    u32 bypass, unique, overflow, first, last, bits_or, bits_and;
    struct bucket bucket[SLOTS];
};
static struct capture stats;
static void *(*irq_desc)(unsigned int);
static u32 *owned_action;
static bool hooked;
static u32 word(const unsigned char *p, unsigned int off)
{ u32 v; memcpy(&v, p + off, 4); return v; }
static u32 crc(const unsigned char *p, unsigned int n)
{
    u32 c = ~0u; unsigned int i, j;
    for (i = 0; i < n; ++i) {
        c ^= p[i];
        for (j = 0; j < 8; ++j) c = (c >> 1) ^ (0xedb88320u & (0u - (c & 1u)));
    }
    return ~c;
}

/* r0 is the value just returned by the original gpHalUartGetIntSts.
 * The untouched ISR subsequently tests precisely these bits, retaining r5
 * through its RX loop and selecting TX after RX when initial bit0x80 is set.
 * No MMIO, allocation, clocks, printk, locks or SD I/O occur here.
 */
void __used d35_capture_status(u32 value)
{
    unsigned int i;
    if (!stats.total) { stats.first = value; stats.bits_and = value; }
    stats.total++; stats.last = value; stats.bits_or |= value; stats.bits_and &= value;
    if (value & 0xa000) { stats.rx++; if (value & 0x80) stats.rx_then_tx++; }
    else if (value & 0x80) stats.tx_only++;
    else stats.neither++;
    for (i = 0; i < stats.unique; ++i)
        if (stats.bucket[i].status == value) { stats.bucket[i].count++; return; }
    if (stats.unique == SLOTS) { stats.overflow++; return; }
    stats.bucket[stats.unique].status = value;
    stats.bucket[stats.unique++].count = 1;
}

/* Verified original six-instruction prologue, same frame and callee-save
 * layout. Original status getter runs exactly once. Save all caller-clobbered
 * registers around the RAM-only callback. Original TST and all later vendor
 * instructions execute in place at c01177f8. No runtime executable writes.
 */
extern int d35_status_bridge(int, void *);
asm(".text\n.align 2\n.global d35_status_bridge\n.type d35_status_bridge,%function\n"
    "d35_status_bridge:\n"
    "mov ip, sp\n"
    "push {r4,r5,r6,r7,r8,fp,ip,lr,pc}\n"
    "sub fp, ip, #4\n"
    "sub sp, sp, #12\n"
    "ldr r0, [r1, #4]\n"
    "mov r4, r1\n"
    "ldr ip, =0xc0117314\nblx ip\n"
    "push {r0,r1,r2,r3,ip,lr}\n"
    "bl d35_capture_status\n"
    "pop {r0,r1,r2,r3,ip,lr}\n"
    "ldr pc, =0xc01177f8\n"
    ".size d35_status_bridge, .-d35_status_bridge\n.ltorg\n");

static int intercept(int irq, void *dev)
{
    int result;
    if (irq != 19 || dev != (void *)PORT || stats.total >= CAP) {
        stats.bypass++;
        return ((int (*)(int, void *))ISR)(irq, dev);
    }
    result = d35_status_bridge(irq, dev);
    if (result == IRQ_HANDLED) stats.handled++; else stats.other_return++;
    return result;
}

static int ownership(u32 expected, u32 **action)
{
    unsigned char port[0x118], a[8]; void *desc, *act;
    desc = irq_desc(19);
    if (!desc || probe_kernel_read(&act, (char *)desc + 0x3c, sizeof(act)) || !act ||
        probe_kernel_read(a, act, sizeof(a)) || word(a, 0) != expected || word(a, 4) != PORT)
        return -ENODEV;
    if (probe_kernel_read(port, (void *)PORT, sizeof(port)) || word(port, 0x48) != 19 ||
        word(port, 0xb4) != 0x76 || !word(port, 4) || !word(port, 0x64)) return -ENODEV;
    *action = act; return 0;
}

static int detach(void)
{
    unsigned long flags; u32 *action = NULL; int result;
    local_irq_save(flags);
    if (!hooked) { local_irq_restore(flags); return 0; }
    result = ownership((u32)intercept, &action);
    if (!result && action != owned_action) result = -ENODEV;
    if (!result) { WRITE_ONCE(*action, ISR); hooked = false; }
    local_irq_restore(flags);
    if (result) return result; /* Keep the reference on any ownership conflict. */
    synchronize_irq(19);
    module_put(THIS_MODULE);
    return 0;
}

static int show(struct seq_file *m, void *unused)
{
    struct capture s; unsigned long flags; unsigned int i; bool attached;
    local_irq_save(flags); s = stats; attached = hooked; local_irq_restore(flags);
    seq_printf(m, "version=2 result=0 irq=19 attached=%u total=%u rx=%u tx_only=%u neither=%u "
        "rx_then_tx=%u handled=%u other_return=%u bypass=%u unique=%u overflow=%u "
        "first=%08x last=%08x bits_or=%08x bits_and=%08x cap=%u\n",
        attached, s.total, s.rx, s.tx_only, s.neither, s.rx_then_tx, s.handled,
        s.other_return, s.bypass, s.unique, s.overflow, s.first, s.last, s.bits_or, s.bits_and, CAP);
    for (i = 0; i < s.unique; ++i)
        seq_printf(m, "status=%08x count=%u\n", s.bucket[i].status, s.bucket[i].count);
    return 0;
}
static int stop_show(struct seq_file *m, void *unused)
{
    int result = detach();
    seq_printf(m, "version=2 stop_result=%d restored=%u attached=%u\n", result, !hooked, hooked);
    return 0;
}

static int __init start(void)
{
    unsigned char code[D35_GUARD_MAX]; unsigned int i; unsigned long flags; int result;
    BUILD_BUG_ON(sizeof(struct module) != 448);
    BUILD_BUG_ON(offsetof(struct module, init) != 0xe8);
    BUILD_BUG_ON(offsetof(struct module, exit) != 0x1a0);
    BUILD_BUG_ON(offsetof(struct module, refcnt) != 0x1a4);
    if (kallsyms_lookup_name("gp_uart_isr") != ISR ||
        kallsyms_lookup_name("gpHalUartGetIntSts") != 0xc0117314u ||
        kallsyms_lookup_name("irq_to_desc") != 0xc015e158u) return -ENODEV;
    for (i = 0; i < ARRAY_SIZE(d35_guards); ++i) {
        const struct d35_guard *g = &d35_guards[i];
        if (g->size > sizeof(code) || probe_kernel_read(code, (void *)g->address, g->size) ||
            crc(code, g->size) != g->crc) return -ENODEV;
    }
    irq_desc = (void *)0xc015e158u;
    if (!proc_create_single_data("d35_uart_status", 0400, NULL, show, NULL)) return -ENOMEM;
    if (!proc_create_single_data("d35_uart_status_stop", 0400, NULL, stop_show, NULL)) {
        remove_proc_entry("d35_uart_status", NULL); return -ENOMEM;
    }
    if (!try_module_get(THIS_MODULE)) { result = -ENODEV; goto remove; }
    local_irq_save(flags);
    result = ownership(ISR, &owned_action);
    if (!result) { WRITE_ONCE(*owned_action, (u32)intercept); hooked = true; }
    local_irq_restore(flags);
    if (!result) return 0;
    module_put(THIS_MODULE);
remove:
    remove_proc_entry("d35_uart_status_stop", NULL);
    remove_proc_entry("d35_uart_status", NULL);
    return result;
}
static void __exit stop(void)
{
    /* A still-attached hook pins this module, so ordinary unload cannot reach
     * this point. Proc teardown drains in-flight reads before code is freed. */
    remove_proc_entry("d35_uart_status_stop", NULL);
    remove_proc_entry("d35_uart_status", NULL);
}
module_init(start);
module_exit(stop);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Exact-kernel UART entry-status and branch aggregate probe");
