/* Sole producer: claim FREE source and FIFO credit together, or leave all
 * ownership/queue state untouched. Never replace READY or SCALER data. */
int board_video_try_reserve(void)
{
    unsigned slot;
    int result;
    pthread_mutex_lock(&display_lock);
    if(!b.opened || b.stopping) result=-1;
    else if(b.null_backend || b.reserved>=0) result=1;
    else {
        for(slot=0;slot<SOURCE_SLOTS;++slot) if(b.slots[slot].owner==FREE) break;
        result=0;
        if(slot<SOURCE_SLOTS && b.queue_count<READY_LIMIT) {
            b.reserved=(int)slot;
            b.slots[slot].owner=RESERVED;
            result=1;
        }
    }
    pthread_mutex_unlock(&display_lock);
    if(result<0) return failure("Display unavailable for nonblocking reservation");
    return result;
}
