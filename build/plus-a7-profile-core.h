#ifndef D35_PLUS_A7_PROFILE_CORE_H
#define D35_PLUS_A7_PROFILE_CORE_H
#include <stdint.h>
extern unsigned d35_profile_active;
uint64_t d35_profile_enter(void);
void d35_profile_leave(unsigned region,uint64_t began);
#endif
