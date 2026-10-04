#ifndef D35_MVP_TIMING_H
#define D35_MVP_TIMING_H
#include <stdint.h>
int timing_prepare(void);
uint64_t timing_now_ns(void);
void timing_sleep_until(uint64_t deadline_ns);
#endif
