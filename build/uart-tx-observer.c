/* Exact-kernel, single-A7 reversible TX service test. No kernel text patch.
 * New pending/nonempty path writes at most one byte, only with !TX_FULL.
 * RX and original FIFO-empty cases execute unchanged vendor instructions.
 */
#include <linux/module.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <linux/uaccess.h>
#include <linux/irqflags.h>
#include <linux/kallsyms.h>
#include <linux/interrupt.h>
#include "uart-tx-guards.h"
#define PORT 0xc072961cu
#define ISR 0xc01177dcu
#define CAP 200000u
struct capture { u32 calls, added, writes, full, empty_stop, stopped, urgent, fallback, fault, bypass; };
static struct capture stats;
static void *(*irq_desc)(unsigned int);
static u32 *owned_action;
static bool hooked;
static u32 word(const unsigned char *p, unsigned int off) { u32 v; memcpy(&v,p+off,4);return v; }
static u32 rd(void *p,unsigned int off) { return READ_ONCE(*(u32 *)((char *)p+off)); }
static void wr(void *p,unsigned int off,u32 v) { WRITE_ONCE(*(u32 *)((char *)p+off),v); }
static u32 crc(const unsigned char *p,unsigned int n) {
 u32 c=~0u;unsigned int i,j;
 for(i=0;i<n;i++){c^=p[i];for(j=0;j<8;j++)c=(c>>1)^(0xedb88320u&(0u-(c&1u)));}return ~c;
}
/* Retain the original stack frame and original entry value without a second
 * status read. Caller-clobbered register contents are not semantic inputs. */
extern int d35_vendor_entry(int,void *,u32);
asm(".text\n.align 2\n.global d35_vendor_entry\n.type d35_vendor_entry,%function\n"
 "d35_vendor_entry:\nmov ip,sp\npush {r4,r5,r6,r7,r8,fp,ip,lr,pc}\n"
 "sub fp,ip,#4\nsub sp,sp,#12\nmov r0,r2\nmov r4,r1\nldr pc,=0xc01177f8\n"
 ".size d35_vendor_entry,.-d35_vendor_entry\n.ltorg\n");
static void stop_tx(void *p) { ((void (*)(void *))0xc011755cu)(p); }
static void wakeup(void *p) { ((void (*)(void *))0xc0335f58u)(p); }
static int intercept(int irq,void *dev) {
 void *state,*ring,*tty,*base;u32 status,head,tail,ctrl;u8 urgent;
 if(irq!=19 || dev!=(void *)PORT || stats.calls>=CAP){stats.bypass++;return ((int (*)(int,void *))ISR)(irq,dev);}
 stats.calls++;base=(void *)(unsigned long)rd(dev,4);
 status=((u32 (*)(void *))0xc0117314u)(base);
 /* Exact original RX priority and original empty-FIFO TX branch. */
 if((status&0xa000) || (status&0x80) || !(status&0x4000)) {
  stats.fallback++;return d35_vendor_entry(irq,dev,status);
 }
 ctrl=((u32 (*)(void *))0xc0117364u)(base);
 if(!(ctrl&0x4000) || !(READ_ONCE(*(u8 *)((char *)dev+0x108))&2)) {
  stats.fallback++;return d35_vendor_entry(irq,dev,status);
 }
 state=(void *)(unsigned long)rd(dev,0x64);
 if(rd(dev,0x54)!=8 || !state){stats.fault++;return d35_vendor_entry(irq,dev,status);}
 head=rd(state,0xb8);tail=rd(state,0xbc);ring=(void *)(unsigned long)rd(state,0xb4);
 if(head>=4096 || tail>=4096 || !ring){stats.fault++;return d35_vendor_entry(irq,dev,status);}
 stats.added++;urgent=READ_ONCE(*(u8 *)((char *)dev+0x58));
 if(!urgent) {
  if(head==tail){stats.empty_stop++;stop_tx(dev);return IRQ_HANDLED;}
  tty=(void *)(unsigned long)rd(state,0x4c);
  if((tty && (READ_ONCE(*(u8 *)((char *)tty+0x124))&1)) || rd(dev,0xa8)) {
   stats.stopped++;stop_tx(dev);return IRQ_HANDLED;
  }
 }
 /* No concurrent normal producer on this UP IRQ-disabled path; hardware can
  * drain after the entry read, increasing room. Never assume four free slots.
  * Bit0x20 is TX_FULL in three matching UART-IP primary headers. Physical flag
  * semantics remain a qualification boundary, not a simulated-board claim. */
 if(status&0x20){stats.full++;return IRQ_HANDLED;}
 ((void (*)(void *,u32))0xc01172fcu)(base,urgent?urgent:READ_ONCE(*((u8 *)ring+tail)));
 wr(dev,0x7c,rd(dev,0x7c)+1);stats.writes++;
 if(urgent){WRITE_ONCE(*(u8 *)((char *)dev+0x58),0);stats.urgent++;return IRQ_HANDLED;}
 tail=(tail+1)&4095;wr(state,0xbc,tail);
 if(!((rd(state,0xb8)-tail)&0xf00))wakeup(dev);
 if(rd(state,0xb8)==rd(state,0xbc))stop_tx(dev);
 return IRQ_HANDLED;
}
static int ownership(u32 expected, u32 **action)
{
    unsigned char port[0x118], a[8]; void *desc, *act; u32 hwirq;
    desc = irq_desc(19);
    if (!desc || probe_kernel_read(&act, (char *)desc + 0x3c, sizeof(act)) || !act ||
        probe_kernel_read(a, act, sizeof(a)) || word(a, 0) != expected || word(a, 4) != PORT)
        return -ENODEV;
    if (probe_kernel_read(port, (void *)PORT, sizeof(port)) || word(port, 0x48) != 19 ||
        word(port, 0xb4) != 0x76 || !word(port, 4) || !word(port, 0x64)) return -ENODEV;
    if ((expected == ISR && word(port, 0x54) != 8) || !word(port, 0x64) ||
        probe_kernel_read(&hwirq, (char *)desc + 0x1c, 4) || hwirq != 69)
        return -ENODEV;
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

static int show(struct seq_file *m,void *unused) {
 struct capture s;unsigned char p[0x118],state[0xc0];unsigned long flags;bool attached;int result;u32 ctrl=0,head=0,tail=0;
 local_irq_save(flags);s=stats;attached=hooked;
 result=probe_kernel_read(p,(void *)PORT,sizeof(p));
 if(!result)result=probe_kernel_read(state,(void *)(unsigned long)word(p,0x64),sizeof(state));
 if(!result){head=word(state,0xb8);tail=word(state,0xbc);ctrl=((u32 (*)(void *))0xc0117364u)((void *)(unsigned long)word(p,4));}
 local_irq_restore(flags);
 seq_printf(m,"version=4 result=%d irq=19 attached=%u calls=%u added=%u writes=%u full=%u empty_stop=%u stopped=%u urgent=%u fallback=%u fault=%u bypass=%u ctrl=%08x flags=%02x fifo=%u head=%u tail=%u rx=%u tx=%u frame=%u parity=%u overrun=%u brk=%u cap=%u\n",
 result,attached,s.calls,s.added,s.writes,s.full,s.empty_stop,s.stopped,s.urgent,s.fallback,s.fault,s.bypass,ctrl,result?0:p[0x108],result?0:word(p,0x54),head,tail,result?0:word(p,0x78),result?0:word(p,0x7c),result?0:word(p,0x84),result?0:word(p,0x88),result?0:word(p,0x80),result?0:word(p,0x8c),CAP);
 return 0;
}
static int on_show(struct seq_file *m,void *unused) {
 unsigned long flags;u32 *action=NULL;int result=0;
 if(!hooked) {
  if(!try_module_get(THIS_MODULE))result=-ENODEV;
  else {
   local_irq_save(flags);result=ownership(ISR,&action);
   if(!result){owned_action=action;WRITE_ONCE(*action,(u32)intercept);hooked=true;}
   local_irq_restore(flags);if(result)module_put(THIS_MODULE);
  }
 }
 seq_printf(m,"version=4 start_result=%d attached=%u\n",result,hooked);return 0;
}
static int off_show(struct seq_file *m,void *unused) {
 int result=detach();seq_printf(m,"version=4 stop_result=%d restored=%u attached=%u\n",result,!hooked,hooked);return 0;
}
static int __init start(void) {
 unsigned char code[D35_GUARD_MAX];unsigned int i;u32 *action;int result;
 BUILD_BUG_ON(sizeof(struct module)!=448);BUILD_BUG_ON(offsetof(struct module,init)!=0xe8);
 BUILD_BUG_ON(offsetof(struct module,exit)!=0x1a0);BUILD_BUG_ON(offsetof(struct module,refcnt)!=0x1a4);
 if(kallsyms_lookup_name("gp_uart_isr")!=ISR || kallsyms_lookup_name("gpHalUartGetIntSts")!=0xc0117314u || kallsyms_lookup_name("irq_to_desc")!=0xc015e158u)return -ENODEV;
 for(i=0;i<ARRAY_SIZE(d35_guards);i++) {
  const struct d35_guard *g=&d35_guards[i];
  if(g->size>sizeof(code) || probe_kernel_read(code,(void *)g->address,g->size) || crc(code,g->size)!=g->crc)return -ENODEV;
 }
 irq_desc=(void *)0xc015e158u;result=ownership(ISR,&action);if(result)return result;
 if(!proc_create_single_data("d35_uart_tx",0400,NULL,show,NULL))return -ENOMEM;
 if(!proc_create_single_data("d35_uart_tx_on",0400,NULL,on_show,NULL))goto remove_first;
 if(!proc_create_single_data("d35_uart_tx_off",0400,NULL,off_show,NULL))goto remove_second;
 return 0;
remove_second:remove_proc_entry("d35_uart_tx_on",NULL);
remove_first:remove_proc_entry("d35_uart_tx",NULL);return -ENOMEM;
}
static void __exit stop(void) {
 remove_proc_entry("d35_uart_tx_off",NULL);remove_proc_entry("d35_uart_tx_on",NULL);remove_proc_entry("d35_uart_tx",NULL);
}
module_init(start);module_exit(stop);
MODULE_LICENSE("GPL");MODULE_DESCRIPTION("Exact-kernel reversible one-byte TX-pending correction test");
