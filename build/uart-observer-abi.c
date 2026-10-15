/* Offline ABI reconstruction only. This module refuses initialization.
 * No device access, proc creation or UART changes occur in this artifact.
 */
#include <linux/module.h>
#include <linux/console.h>
/* The vendor's observed uart_port includes the two console/sysrq words.
 * This selects that header layout without claiming a recovered full .config.
 */
#define SUPPORT_SYSRQ
#include <linux/serial_core.h>
#include <linux/stddef.h>

const unsigned int d35_abi_layout[] __used = {
    sizeof(struct module), offsetof(struct module, name),
    offsetof(struct module, init), offsetof(struct module, exit),
    offsetof(struct module, core_layout), offsetof(struct module, init_layout),
    offsetof(struct module, arch), offsetof(struct module, kallsyms),
    offsetof(struct module, args), offsetof(struct module, refcnt),
    sizeof(struct uart_port), offsetof(struct uart_port, membase),
    offsetof(struct uart_port, irq), offsetof(struct uart_port, state),
    offsetof(struct uart_port, icount.rx), offsetof(struct uart_port, icount.tx),
    offsetof(struct uart_port, ops), offsetof(struct uart_port, line),
};

static int __init d35_abi_init(void) { return -EAGAIN; }
static void __exit d35_abi_exit(void) { }
module_init(d35_abi_init);
module_exit(d35_abi_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Offline D-R35 ABI layout artifact; initialization refused");
