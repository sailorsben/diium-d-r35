/* D-R35 snapshot-only kernel observer. No handler replacement, UART writes,
 * status/data reads, polling thread, per-IRQ work or printk. Hardware access
 * is limited to the verified driver's existing control-register getter.
 * Requires the separately qualified, exact-image generated guard header.
 */
#include <linux/module.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <linux/uaccess.h>
#include <linux/ktime.h>
#include <linux/irqflags.h>
#include <linux/kallsyms.h>
#include "uart-state-guards.h"

#define PROC_NAME "d35_uart_state"
#define PORT 0xc072961cu
#define ISR 0xc01177dcu
#define GET_CTRL 0xc0117364u
#define IRQ_DESC 0xc015e158u
static u32 (*get_ctrl)(void *base);
static void *(*irq_desc)(unsigned int irq);
static unsigned long reads;

static u32 word(const unsigned char *p, unsigned int off)
{
    u32 value;
    memcpy(&value, p + off, sizeof(value));
    return value;
}

static u32 code_crc(const unsigned char *data, unsigned int size)
{
    u32 crc = ~0u;
    unsigned int i, j;
    for (i = 0; i < size; i++) {
        crc ^= data[i];
        for (j = 0; j < 8; j++)
            crc = (crc >> 1) ^ (0xedb88320u & (0u - (crc & 1u)));
    }
    return ~crc;
}

/* Every offset below is independently recovered from this kernel's code.
 * Never dereference a guessed generic irq_desc/uart structure layout.
 * local IRQ exclusion prevents this single-core non-preemptible kernel from
 * changing ownership/state during the short validated snapshot.
 */
static int snapshot(u32 *ctrl, u32 *flags, u32 *tx, u32 *rx, u32 *head, u32 *tail)
{
    unsigned char port[0x118], action[8], queue[8];
    unsigned long saved;
    void *desc, *act;
    int result = -ENODEV;
    local_irq_save(saved);
    desc = irq_desc(19);
    if (!desc || probe_kernel_read(&act, (char *)desc + 0x3c, sizeof(act)) || !act)
        goto out;
    if (probe_kernel_read(action, act, sizeof(action)) || word(action, 0) != ISR || word(action, 4) != PORT)
        goto out;
    if (probe_kernel_read(port, (void *)PORT, sizeof(port)) || word(port, 0x48) != 19 ||
        word(port, 0xb4) != 0x76 || !word(port, 4) || !word(port, 0x64))
        goto out;
    if (probe_kernel_read(queue, (void *)(word(port, 0x64) + 0xb8), sizeof(queue)))
        goto out;
    *flags = port[0x108];
    *tx = word(port, 0x7c); *rx = word(port, 0x78);
    *head = word(queue, 0); *tail = word(queue, 4);
    /* This is control, never interrupt status or the receive/transmit FIFO. */
    *ctrl = get_ctrl((void *)word(port, 4));
    result = 0;
out:
    local_irq_restore(saved);
    return result;
}

static int show(struct seq_file *m, void *unused)
{
    u32 ctrl = 0, flags = 0, tx = 0, rx = 0, head = 0, tail = 0;
    u64 start = ktime_get_ns(), stop;
    int result = snapshot(&ctrl, &flags, &tx, &rx, &head, &tail);
    stop = ktime_get_ns();
    seq_printf(m, "version=1 read=%lu result=%d start_ns=%llu stop_ns=%llu irq=19 "
               "ctrl=%08x flags=%02x tx=%u rx=%u head=%u tail=%u "
               "tx_hw=%u tx_sw=%u empty=%u mismatch=%u\n",
               ++reads, result, start, stop, ctrl, flags, tx, rx, head, tail,
               !!(ctrl & 0x4000), !!(flags & 2), head == tail,
               result == 0 && !!(ctrl & 0x4000) != !!(flags & 2));
    return 0;
}

static int __init start_observer(void)
{
    unsigned char bytes[D35_GUARD_MAX];
    unsigned int i;
    BUILD_BUG_ON(sizeof(struct module) != 448);
    BUILD_BUG_ON(offsetof(struct module, init) != 0xe8);
    BUILD_BUG_ON(offsetof(struct module, exit) != 0x1a0);
    BUILD_BUG_ON(offsetof(struct module, core_layout) != 0x100);
    BUILD_BUG_ON(offsetof(struct module, init_layout) != 0x130);
    BUILD_BUG_ON(offsetof(struct module, kallsyms) != 0x174);
    BUILD_BUG_ON(offsetof(struct module, refcnt) != 0x1a4);
    if (kallsyms_lookup_name("gp_uart_isr") != ISR ||
        kallsyms_lookup_name("gpHalUartGetCtrl") != GET_CTRL ||
        kallsyms_lookup_name("irq_to_desc") != IRQ_DESC)
        return -ENODEV;
    for (i = 0; i < ARRAY_SIZE(d35_guards); i++) {
        const struct d35_guard *g = &d35_guards[i];
        if (g->size > sizeof(bytes) || probe_kernel_read(bytes, (void *)g->address, g->size) ||
            code_crc(bytes, g->size) != g->crc)
            return -ENODEV;
    }
    get_ctrl = (void *)GET_CTRL;
    irq_desc = (void *)IRQ_DESC;
    if (!proc_create_single_data(PROC_NAME, 0400, NULL, show, NULL))
        return -ENOMEM;
    return 0;
}

static void __exit stop_observer(void) { remove_proc_entry(PROC_NAME, NULL); }
module_init(start_observer);
module_exit(stop_observer);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Exact-kernel D-R35 UART state snapshot observer; no UART writes");
