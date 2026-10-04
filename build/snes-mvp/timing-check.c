/* Reproduce a libc clock 26 seconds ahead of kernel timers. */
#define syscall fixture_syscall
#define nanosleep fixture_nanosleep
#define clock_gettime fixture_clock_gettime
#include "timing.c"
#undef syscall
#undef nanosleep
#undef clock_gettime
/* The first header read declared the fixture names; retain real calls for
 * the separate integration mode without changing the compiled implementation. */
extern long syscall(long number,...);
extern int clock_gettime(clockid_t clock,struct timespec *value);
extern int nanosleep(const struct timespec *request,struct timespec *remaining);
#include <assert.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
static uint64_t kernel_ns=9000000000ull;
static unsigned sleeps;
static int interrupt_once,real_mode;
long fixture_syscall(long number,...)
{
    va_list args; int clock; struct timespec *t;
    assert(number==SYS_clock_gettime);
    va_start(args,number); clock=va_arg(args,int); t=va_arg(args,struct timespec *); va_end(args);
    if(real_mode) return syscall(number,clock,t);
    assert(clock==CLOCK_MONOTONIC || clock==CLOCK_BOOTTIME);
    t->tv_sec=(time_t)(kernel_ns/1000000000ull); t->tv_nsec=(long)(kernel_ns%1000000000ull);
    return 0;
}
int fixture_clock_gettime(clockid_t clock,struct timespec *t)
{
    uint64_t bad=kernel_ns+26000000000ull;
    assert(clock==CLOCK_MONOTONIC);
    if(real_mode) return clock_gettime(clock,t);
    t->tv_sec=(time_t)(bad/1000000000ull); t->tv_nsec=(long)(bad%1000000000ull);
    return 0;
}
int fixture_nanosleep(const struct timespec *request,struct timespec *left)
{
    uint64_t ns=to_ns(request);
    if(real_mode) return nanosleep(request,left);
    assert(ns>0 && ns<=8000000ull); /* Never the 26-second clock offset. */
    ++sleeps;
    if(interrupt_once) { interrupt_once=0; kernel_ns+=ns/2; errno=EINTR; return -1; }
    kernel_ns+=ns; return 0;
}
void startup_note(const char *format,...) { (void)format; }
int main(int argc,char **argv)
{
    uint64_t start,elapsed; unsigned i;
    if(argc==2 && !strcmp(argv[1],"--real")) {
        real_mode=1; assert(!timing_prepare()); start=timing_now_ns();
        for(i=0;i<25;i++) timing_sleep_until(timing_now_ns()+8000000ull);
        elapsed=timing_now_ns()-start;
        assert(elapsed>=200000000ull && elapsed<3000000000ull);
        printf("PASS: real ARM kernel-clock/relative-sleep loop completed 25 polls in %llu ms\n",(unsigned long long)(elapsed/1000000));
        return 0;
    }
    assert(!timing_prepare()); assert(timing_now_ns()==9000000000ull);
    start=timing_now_ns(); interrupt_once=1;
    timing_sleep_until(start+8000000ull);
    assert(kernel_ns==start+8000000ull && sleeps==2);
    timing_sleep_until(start); assert(sleeps==2); /* Late deadlines do not sleep. */
    for(i=0;i<100;i++) timing_sleep_until(timing_now_ns()+8000000ull);
    assert(kernel_ns==start+808000000ull && sleeps==102);
    puts("PASS: 26-second libc/kernel clock skew cannot stall 8 ms input waits; signals retain deadline");
    return 0;
}
