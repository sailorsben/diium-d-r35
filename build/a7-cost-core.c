#include "a7_cost.h"
#include <string.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
static struct d35_cost_frame f;
static unsigned current=D35_COST_PHASES, used[D35_B_KINDS];
static unsigned row_sequence,row_selected;
static uint64_t checkpoint;
static uint64_t clock_ns(int clock)
{
    struct timespec t={0,0}; ++f.clock_calls;
    if(syscall(SYS_clock_gettime,clock,&t)) { ++f.clock_errors;return 0; }
    return (uint64_t)t.tv_sec*1000000000ull+(uint64_t)t.tv_nsec;
}
uint64_t d35_cost_cpu(void) { return clock_ns(CLOCK_THREAD_CPUTIME_ID); }
uint64_t d35_cost_wall(void) { return clock_ns(CLOCK_MONOTONIC); }
__attribute__((visibility("default"))) void d35_cost_begin(unsigned mode)
{
    memset(&f,0,sizeof(f));memset(used,0,sizeof(used));
    f.abi=1;f.bytes=sizeof(f);f.mode=mode&255u;current=D35_COST_PHASES;
    row_sequence=mode>>8;row_selected=0;
    checkpoint=(f.mode==1||f.mode==3)?d35_cost_cpu():0;
}
static void charge(void)
{
    uint64_t now=d35_cost_cpu();
    if(current<D35_COST_PHASES && now>=checkpoint) f.cpu_ns[current]+=now-checkpoint;
    checkpoint=now;
}
__attribute__((visibility("default"))) void d35_cost_end(struct d35_cost_frame *out)
{
    if(f.mode==1||f.mode==3) charge();
    if(f.mode) {
        uint64_t w=d35_cost_wall(),c=d35_cost_cpu();
        for(unsigned i=0;i<64;i++)(void)d35_cost_cpu();
        f.clock_loop_cpu_ns=d35_cost_cpu()-c;f.clock_loop_wall_ns=d35_cost_wall()-w;
    }
    if(f.mode==2) for(unsigned i=0;i<4;i++)
        D35_COST_BENCH(D35_B_EMPTY,0,{__asm__ volatile("" ::: "memory");});
    *out=f;f.mode=0;current=D35_COST_PHASES;
}
unsigned d35_cost_push(unsigned phase)
{
    unsigned old=current;
    if(f.mode==1||f.mode==3) { charge();current=phase;++f.phase_entries[phase]; }
    return old;
}
void d35_cost_pop(unsigned old)
{ if(f.mode==1||f.mode==3) { charge();current=old; } }
void d35_cost_switch(unsigned phase)
{ if(f.mode==1||f.mode==3) { charge();current=phase;++f.phase_entries[phase]; } }
void d35_cost_ppu_entry(void) { ++f.ppu_entries; }
void d35_cost_row(unsigned miss)
{
    if(miss) { ++f.row_misses;if(row_selected)++f.sampled_misses; }
    else { ++f.row_hits;if(row_selected)++f.sampled_hits; }
}
unsigned d35_cost_row_gate(void)
{ row_selected=f.mode==3 || (f.mode==1 && row_sequence++%64u==0);return row_selected; }
unsigned d35_cost_bench(unsigned kind,unsigned shape)
{
    (void)shape;
    if(kind<D35_B_KINDS) ++f.path_calls[kind];
    if(f.mode!=2 || kind>=D35_B_KINDS || used[kind]>=4) return 0;
    return used[kind]++?32:1;
}
unsigned d35_cost_bench_active(unsigned kind)
{ return f.mode==2 && kind<D35_B_KINDS && used[kind]<4; }
void d35_cost_record(unsigned kind,unsigned n,unsigned shape,uint64_t cpu,uint64_t wall)
{
    if(f.samples>=D35_COST_SAMPLES) { ++f.overflow;return; }
    f.sample[f.samples++]=(struct d35_cost_sample){kind,n,shape,16,cpu,wall};
    f.bench_cpu_ns+=cpu;f.bench_wall_ns+=wall;
}
