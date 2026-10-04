#define _GNU_SOURCE
#include "timing.h"
#include "startup.h"
#include <errno.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>

static uint64_t to_ns(const struct timespec *t)
{
    return (uint64_t)t->tv_sec*1000000000ull+(uint64_t)t->tv_nsec;
}
int timing_prepare(void)
{
    struct timespec kernel,libc,boot;
    int libc_rc,boot_rc;
    if(syscall(SYS_clock_gettime,CLOCK_MONOTONIC,&kernel)<0) return -1;
    libc_rc=clock_gettime(CLOCK_MONOTONIC,&libc);
    boot_rc=syscall(SYS_clock_gettime,CLOCK_BOOTTIME,&boot);
    startup_note("clock sources kernel_monotonic_ns=%llu libc_monotonic_ns=%llu kernel_boottime_ns=%llu; using kernel clock and relative waits",
        (unsigned long long)to_ns(&kernel),
        (unsigned long long)(libc_rc==0?to_ns(&libc):0),
        (unsigned long long)(boot_rc==0?to_ns(&boot):0));
    return 0;
}
uint64_t timing_now_ns(void)
{
    struct timespec now={0,0};
    /* On this unit libc monotonic readings and kernel timer deadlines diverge.
     * Bypass the libc/vDSO fast path, keeping all owned timing on the same
     * kernel clock. The device's ARM32 timespec syscall ABI is intentional. */
    if(syscall(SYS_clock_gettime,CLOCK_MONOTONIC,&now)<0) return 0;
    return to_ns(&now);
}
void timing_sleep_until(uint64_t deadline_ns)
{
    struct timespec delay;
    uint64_t now,remaining;
    /* Calculate only the remaining duration. Never pass a userspace absolute
     * timestamp to a kernel sleep; the old 8 ms menu wait stalled for seconds.
     * Recalculate after signals so an interrupted wait keeps its deadline. */
    for(;;) {
        now=timing_now_ns();
        if(now>=deadline_ns) return;
        remaining=deadline_ns-now;
        delay.tv_sec=(time_t)(remaining/1000000000ull);
        delay.tv_nsec=(long)(remaining%1000000000ull);
        if(nanosleep(&delay,NULL)==0 || errno!=EINTR) return;
    }
}
