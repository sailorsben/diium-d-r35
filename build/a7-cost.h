/* Measurement ABI only. No change to emulated clocks, pixels or audio quotas. */
#ifndef D35_A7_COST_H
#define D35_A7_COST_H
#include <stdint.h>
enum { D35_COST_SETUP, D35_COST_PIXEL, D35_COST_ROW, D35_COST_WINDOW,
       D35_COST_CACHE, D35_COST_PHASES };
enum { D35_B_ENTRY, D35_B_SCREEN, D35_B_BACKGROUND, D35_B_OBJECT,
       D35_B_SELECT, D35_B_ROW_MISS, D35_B_ROW_HIT, D35_B_CAPTURE,
       D35_B_DEFER, D35_B_FETCH, D35_B_SAME, D35_B_RESET,
       D35_B_EMPTY, D35_B_KINDS };
#define D35_COST_SAMPLES 128u
struct d35_cost_sample {
    uint32_t kind, iterations, shape, warm_iterations;
    uint64_t cpu_ns, wall_ns;
};
struct d35_cost_frame {
    uint32_t abi, bytes, mode, overflow;
    uint64_t cpu_ns[D35_COST_PHASES], phase_entries[D35_COST_PHASES];
    uint64_t ppu_entries, row_misses, row_hits, clock_calls, clock_errors;
    uint64_t path_calls[D35_B_KINDS];
    uint64_t bench_cpu_ns, bench_wall_ns;
    uint64_t clock_loop_cpu_ns, clock_loop_wall_ns;
    uint64_t sampled_misses,sampled_hits;
    uint32_t samples, reserved;
    struct d35_cost_sample sample[D35_COST_SAMPLES];
};
void d35_cost_begin(unsigned mode); /* 0 counters, 1 disjoint phases, 2 benches */
void d35_cost_end(struct d35_cost_frame *out);
unsigned d35_cost_push(unsigned phase);
void d35_cost_pop(unsigned previous);
void d35_cost_switch(unsigned phase);
void d35_cost_ppu_entry(void);
void d35_cost_row(unsigned miss);
unsigned d35_cost_row_gate(void);
unsigned d35_cost_bench(unsigned kind, unsigned shape);
unsigned d35_cost_bench_active(unsigned kind);
uint64_t d35_cost_cpu(void);
uint64_t d35_cost_wall(void);
void d35_cost_record(unsigned kind,unsigned n,unsigned shape,
                     uint64_t cpu,uint64_t wall);
/* Four batches/path/frame: individual, then three32-operation batches. Timer,
 * loop and compiler barriers stay included. p99 of batch means is explicitly
 * distinct from the p99 of individual observations. No calibration subtraction. */
#define D35_COST_BENCH(KIND,SHAPE,...) do { \
    unsigned d35_n=d35_cost_bench((KIND),(SHAPE)); \
    if(d35_n) { \
        unsigned d35_i; uint64_t d35_c,d35_w; \
        for(d35_i=0;d35_i<16;d35_i++) { __VA_ARGS__; __asm__ volatile("" ::: "memory"); } \
        d35_w=d35_cost_wall();d35_c=d35_cost_cpu(); \
        for(d35_i=0;d35_i<d35_n;d35_i++) { __VA_ARGS__; __asm__ volatile("" ::: "memory"); } \
        d35_c=d35_cost_cpu()-d35_c;d35_w=d35_cost_wall()-d35_w; \
        d35_cost_record((KIND),d35_n,(SHAPE),d35_c,d35_w); \
    } \
} while(0)
#endif
