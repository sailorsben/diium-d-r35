/* Optional owned-core ABI. Sampling is requested by the runner, never per
 * opcode. Regions include callbacks and timer overhead; residual work also
 * includes port-driven SPC work outside S9xAPUExecute. */
#ifndef D35_PLUS_A7_PROFILE_H
#define D35_PLUS_A7_PROFILE_H
#include <stdint.h>
struct d35_core_profile {
    uint32_t abi,bytes,sampled,reserved;
    uint64_t ppu_cpu_ns,apu_cpu_ns;
};
#ifdef D35_PROFILE_CORE
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
static struct d35_core_profile d35_frame_profile;
static inline uint64_t d35_profile_clock(void)
{
    struct timespec t;
    if(syscall(SYS_clock_gettime,CLOCK_THREAD_CPUTIME_ID,&t)) return 0;
    return (uint64_t)t.tv_sec*1000000000u+t.tv_nsec;
}
/* LTO must see one shared state, so this header is included only in libretro.c.
 * Other core translation units use the declarations in the companion header. */
__attribute__((visibility("default"))) void d35_profile_begin(unsigned enabled)
{
    d35_frame_profile=(struct d35_core_profile){1,sizeof(d35_frame_profile),enabled,0,0,0};
    d35_profile_active=enabled;
}
__attribute__((visibility("default"))) void d35_profile_end(struct d35_core_profile *out)
{ *out=d35_frame_profile; d35_profile_active=0; }
void d35_profile_leave(unsigned region,uint64_t began)
{
    uint64_t end=d35_profile_clock(),elapsed=end>=began?end-began:0;
    if(region==0) d35_frame_profile.ppu_cpu_ns+=elapsed;
    else d35_frame_profile.apu_cpu_ns+=elapsed;
}
uint64_t d35_profile_enter(void) { return d35_profile_clock(); }
#endif
#endif
