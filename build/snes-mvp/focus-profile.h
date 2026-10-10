/* Diagnostic policy only. No pacing, audio admission or emulated-time control. */
#ifndef D35_FOCUS_PROFILE_H
#define D35_FOCUS_PROFILE_H
#include <stdint.h>
struct d35_focus_policy { unsigned sequence,hot_remaining,triggers; };
static inline unsigned d35_focus_next(struct d35_focus_policy *p)
{
    unsigned sequence=p->sequence++,reason=0;
    if(p->hot_remaining && sequence%8u==3u) reason=2;
    else if(sequence%64u==3u) reason=1;
    if(p->hot_remaining) --p->hot_remaining;
    return reason;
}
static inline void d35_focus_observe(struct d35_focus_policy *p,unsigned sampled,
                                    uint64_t wall,uint64_t cpu)
{
    /* Instrumented costs never extend the burst that requested them. */
    if(!sampled && (wall>=16000000u || cpu>=15000000u)) {
        if(!p->hot_remaining) ++p->triggers;
        p->hot_remaining=96;
    }
}
#endif
