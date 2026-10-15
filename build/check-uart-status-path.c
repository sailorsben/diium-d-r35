/* Reuse the stock-code RAM fixture, not the observer implementation. */
#define main previous_fixture_main
#include "check-uart-kernel.c"
#undef main

int main(int argc,char **argv)
{
    assert(argc==2);
    FILE *f=fopen(argv[1],"rb");assert(f);
    void *mapped=mmap((void *)RELOCATED,0x800000,PROT_READ|PROT_WRITE|PROT_EXEC,
        MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
    assert(mapped==(void *)RELOCATED && fread(mapped,1,7476028,f)==7476028);fclose(f);
    stub(0xc0335ca0,insertion);stub(0xc031f418,push);stub(0xc0335f58,wakeup);
    __builtin___clear_cache(mapped,(char *)mapped+0x800000);
    /* Exact dominant physical status; control/software flags are the earlier
     * state1 snapshots, not asserted simultaneous status1 observations. */
    reset(0x531f,0xb070,5);
    uint8_t saved_port[sizeof(port)],saved_state[sizeof(state)],saved_ring[sizeof(ring)];
    uint32_t saved_regs[sizeof(regs)/sizeof(regs[0])];
    memcpy(saved_port,port,sizeof(port));memcpy(saved_state,state,sizeof(state));
    memcpy(saved_ring,ring,sizeof(ring));memcpy(saved_regs,regs,sizeof(regs));
    for(unsigned i=0;i<1000;i++)assert(isr()==1);
    assert(!memcmp(port,saved_port,sizeof(port)) && !memcmp(state,saved_state,sizeof(state)));
    assert(!memcmp(ring,saved_ring,sizeof(ring)) && !memcmp(regs,saved_regs,sizeof(regs)));
    assert(!insertions && !pushes && !wakeups);
    puts("1000 original ISR calls with captured status0x531f return IRQ_HANDLED without RAM-register/port/queue changes or RX/TX delivery");
    return 0;
}
