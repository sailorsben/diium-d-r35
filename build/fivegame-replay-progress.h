/* Shared only between the owned supervisor and child, never a core state. */
#ifndef D35_FIVEGAME_REPLAY_PROGRESS_H
#define D35_FIVEGAME_REPLAY_PROGRESS_H
#include <stdint.h>
#ifndef D35_COLD_STALL_NS
#define D35_COLD_STALL_NS 60000000000ull
#endif
struct d35_replay_progress {
    volatile uint32_t active, calls, epoch;
};
extern struct d35_replay_progress *d35_replay_shared;
#endif
