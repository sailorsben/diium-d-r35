/* Offline only: original ARM instructions and an explicitly labeled one-word
 * comparison in anonymous RAM. Never writes device/kernel/firmware memory. */
#define main previous_fixture_main
#include "check-uart-kernel.c"
#undef main

static unsigned char irqdata[64], gicdata[256];
static uint32_t dist[1024], cpu[32];

int main(int argc,char **argv)
{
    assert(argc==2);FILE *f=fopen(argv[1],"rb");assert(f);
    void *mapped=mmap((void *)RELOCATED,0x800000,PROT_READ|PROT_WRITE|PROT_EXEC,
        MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
    assert(mapped==(void *)RELOCATED && fread(mapped,1,7476028,f)==7476028);fclose(f);
    stub(0xc0335ca0,insertion);stub(0xc031f418,push);stub(0xc0335f58,wakeup);
    __builtin___clear_cache(mapped,(char *)mapped+0x800000);
    reset(0x531f,0xf070,7);store(state,0xb8,1);ring[0]='A';
    assert(isr()==1 && !load(port,0x7c) && !load(state,0xbc));
    assert(regs[2]==0xf070);
    puts("original TX-empty test ignores captured status0x531f even with TX enabled and a queued byte");

    /* Comparison only, not a deployment candidate: TST r5,#0x80 -> #0x4000.
     * The Python checker independently decodes both instruction words. */
    uint32_t *test=AT(0xc0117804),original=*test;
    assert(original==0xe3150080u);*test=0xe3150901u;
    __builtin___clear_cache(test,(char *)test+4);
    reset(0x531f,0xf070,7);store(state,0xb8,1);ring[0]='A';
    assert(isr()==1 && load(port,0x7c)==1 && load(state,0xbc)==1);
    assert(regs[2]==0xb070 && !(port[0x108]&2) && wakeups==1);
    puts("TX-pending comparison reaches original transmit service and stop-TX for enabled/queued fixture");
    reset(0x531f,0xb070,5);
    assert(isr()==1 && regs[2]==0xb070 && !load(port,0x7c));
    puts("same comparison cannot establish a clear when software/hardware TX are already disabled; no standalone fix claim");
    *test=original;__builtin___clear_cache(test,(char *)test+4);

    store(irqdata,8,69);store(irqdata,0x1c,(uintptr_t)gicdata);
    store(gicdata,0x88,(uintptr_t)dist);store(gicdata,0x8c,(uintptr_t)cpu);
    int (*get)(void *,int,unsigned char *)=AT(0xc0303d5c);
    for(unsigned mask=0;mask<8;mask++) {
        memset(dist,0,sizeof(dist));dist[0x208/4]=(mask&1)?32:0;
        dist[0x308/4]=(mask&2)?32:0;dist[0x108/4]=(mask&4)?32:0;
        uint32_t saved[1024];memcpy(saved,dist,sizeof(saved));unsigned char b=99;
        assert(!get(irqdata,0,&b) && b==!!(mask&1));
        assert(!get(irqdata,1,&b) && b==!!(mask&2));
        assert(!get(irqdata,2,&b) && b==!(mask&4));
        assert(!memcmp(saved,dist,sizeof(saved)));
    }
    puts("actual GIC getter reads SPI69 pending/active/masked state without changing register RAM for all8 combinations");
    unsigned char b=99;assert(get(irqdata,3,&b)==-22 && b==99);
    puts("actual GIC getter refuses unsupported state without a result write");
    ((void (*)(void *))AT(0xc03033a0))(irqdata);
    assert(cpu[0x10/4]==69);
    puts("actual ordinary GIC EOI function writes hardware IRQ69 to CPU-interface EOI register");
    return 0;
}
