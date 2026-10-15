/* Offline QEMU only. Execute archived UART instructions against anonymous RAM.
 * Uniform relocation preserves relative calls. No device nodes or real MMIO.
 * Kernel tty delivery/wakeup calls are replaced by counted fixture stubs.
 */
#define _GNU_SOURCE
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>

#define ORIGINAL 0xc0008000u
#define RELOCATED 0x10008000u
#define AT(x) ((void *)(uintptr_t)((x)-ORIGINAL+RELOCATED))
static unsigned insertions, pushes, wakeups;
static uint8_t port[0x120], state[0x200], ring[4096];
static uint32_t regs[8];
static void store(void *p, unsigned off, uint32_t v) { memcpy((uint8_t *)p+off,&v,4); }
static uint32_t load(void *p, unsigned off) { uint32_t v;memcpy(&v,(uint8_t *)p+off,4);return v; }
static void insertion(void) { insertions++; }
static void push(void) { pushes++; }
static void wakeup(void) { wakeups++; }
static void stub(uint32_t address, void (*fn)(void)) {
    uint32_t words[]={0xe51ff004u,(uint32_t)(uintptr_t)fn};
    memcpy(AT(address),words,sizeof(words));
}
static void reset(unsigned status, unsigned control, unsigned flags) {
    memset(port,0,sizeof(port));memset(state,0,sizeof(state));memset(regs,0,sizeof(regs));
    store(port,4,(uint32_t)(uintptr_t)regs);store(port,0x64,(uint32_t)(uintptr_t)state);
    store(port,0x54,16);store(state,0xb4,(uint32_t)(uintptr_t)ring);
    port[0x108]=flags;regs[4]=status;regs[2]=control;
    insertions=pushes=wakeups=0;
}
static unsigned isr(void) { return ((unsigned (*)(int,void *))AT(0xc01177dc))(19,port); }
int main(int argc, char **argv) {
    assert(argc==2);FILE *f=fopen(argv[1],"rb");assert(f);
    void *mapped=mmap((void *)RELOCATED,0x800000,PROT_READ|PROT_WRITE|PROT_EXEC,
                      MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
    assert(mapped==(void *)RELOCATED);assert(fread(mapped,1,7476028,f)==7476028);fclose(f);
    stub(0xc0335ca0,insertion);stub(0xc031f418,push);stub(0xc0335f58,wakeup);
    __builtin___clear_cache(mapped,(char *)mapped+0x800000);
    reset(0,0x4000,0);assert(isr()==1);assert(regs[2]==0x4000 && !load(port,0x7c));
    puts("no-recognized-status returns IRQ_HANDLED without clearing control");
    reset(0x80,0x4000,2);assert(isr()==1);assert(regs[2]==0 && !(port[0x108]&2));
    puts("empty TX with software-enabled flag clears TX control bit");
    reset(0x80,0x4000,0);
    for(unsigned i=0;i<1000;i++)assert(isr()==1);
    assert(regs[2]==0x4000 && !load(port,0x7c) && !load(port,0x78));
    puts("1000 empty TX calls with clear software flag retain TX control, counters unchanged");
    reset(0x80,0x4000,2);store(state,0xb8,1);ring[0]='A';regs[0]=0xdeadbeef;
    assert(isr()==1);assert(load(port,0x7c)==1 && regs[0]==0 && load(state,0xbc)==1 && wakeups==1);
    puts("queued TX increments counter but actual PutChar stores zero");
    reset(0x8010,0xa000,5);regs[1]=0;
    assert(isr()==1);assert(load(port,0x78)==1 && insertions==1 && pushes==1);
    puts("recognized RX branch increments RX counter and delivers fixture byte");
    reset(0x80,0,0);regs[0]=0xdeadbeef;
    ((void (*)(void *,unsigned))AT(0xc01172fc))(regs,'Z');assert(regs[0]==0);
    puts("direct PutChar ignores supplied nonzero character");
    puts("6 archived-code checks passed; no A7 timing or live-register evidence");
    return 0;
}
