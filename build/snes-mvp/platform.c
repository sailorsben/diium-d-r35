#define _GNU_SOURCE
#include "platform.h"
#include "startup.h"
#include "timing.h"
#include <stdint.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <time.h>

/* Stock main/vrtemu ShareMemCreat: key 1234, 460 bytes, IPC_CREAT|0666.
 * xintiao increments word 1 and publishes a 60-tick budget in word 0.
 * Preserve the platform's existing liveness contract without another worker,
 * disabling a watchdog, or changing the other shared control fields. */
static volatile uint32_t *heartbeat;
static int heartbeat_id=-1;
static uint64_t next_heartbeat;
static int heartbeat_open_for_key(key_t key)
{
    void *mapped;
    heartbeat_id=shmget(key,460,IPC_CREAT|0666);
    if(heartbeat_id<0) return -1;
    mapped=shmat(heartbeat_id,NULL,0);
    if(mapped==(void *)-1) return -1;
    heartbeat=mapped;
    next_heartbeat=0;
    platform_heartbeat_tick();
    return 0;
}
int platform_heartbeat_open(void)
{
    if(heartbeat) return 0;
    if(heartbeat_open_for_key((key_t)1234)<0) return -1;
    startup_note("platform heartbeat attached key=1234 bytes=460 budget=60 counter=%u",heartbeat[1]);
    return 0;
}
void platform_heartbeat_tick(void)
{
    uint64_t now;
    if(!heartbeat) return;
    now=timing_now_ns();
    if(now<next_heartbeat) return;
    heartbeat[0]=60;
    heartbeat[1]=heartbeat[1]+1u;
    next_heartbeat=now+15000000ull;
}
void platform_heartbeat_close(void)
{
    if(heartbeat) shmdt((const void *)heartbeat);
    heartbeat=NULL;
    heartbeat_id=-1;
    /* Stock helpers may still own this segment. Never IPC_RMID it here. */
}
