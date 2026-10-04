#include "platform.c"
#include <assert.h>
#include <stdio.h>
#include <string.h>
void startup_note(const char *format,...) { (void)format; }
int main(void)
{
    uint32_t *view; int id; unsigned i;
    assert(!heartbeat_open_for_key(IPC_PRIVATE));
    id=heartbeat_id;
    view=shmat(id,NULL,0); assert(view!=(void *)-1);
    assert(view[0]==60 && view[1]==1);
    for(i=2;i<115;i++) view[i]=0xa5a50000u+i;
    view[1]=400; next_heartbeat=0; platform_heartbeat_tick();
    assert(view[0]==60 && view[1]==401);
    platform_heartbeat_tick(); assert(view[1]==401); /* Throttled, not a busy feed. */
    for(i=2;i<115;i++) assert(view[i]==0xa5a50000u+i);
    platform_heartbeat_close();
    assert(!heartbeat && view[1]==401); /* Other owner/segment remains alive. */
    assert(!shmdt(view)); assert(!shmctl(id,IPC_RMID,NULL));
    puts("PASS: vendor heartbeat layout/counter/rate; other shared control fields and owners preserved");
    return 0;
}
