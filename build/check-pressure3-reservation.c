/* Exercise the actual patched board state machine; no hardware calls. */
#include "render-pressure3-private/runner/board.c"
#include <assert.h>
int main(void)
{
    unsigned a,c,d,q,cases=0;
    for(a=0;a<4;a++)for(c=0;c<4;c++)for(d=0;d<4;d++)for(q=0;q<=READY_LIMIT;q++) {
        memset(&b,0,sizeof(b));b.opened=1;b.reserved=-1;b.queue_count=q;
        b.slots[0].owner=(enum slot_owner)a;b.slots[1].owner=(enum slot_owner)c;b.slots[2].owner=(enum slot_owner)d;
        b.queue[0]=1;b.queue[1]=2;
        unsigned char before[sizeof(b)];memcpy(before,&b,sizeof(b));
        unsigned first=0;while(first<SOURCE_SLOTS && b.slots[first].owner!=FREE)first++;
        int expected=first<SOURCE_SLOTS && q<READY_LIMIT;
        assert(board_video_try_reserve()==expected);
        if(!expected)assert(!memcmp(before,&b,sizeof(b)));
        else {
            assert(b.reserved==(int)first && b.slots[first].owner==RESERVED);
            assert(b.queue_count==q && b.queue[0]==1 && b.queue[1]==2);
            assert(board_video_try_reserve()==1); /* idempotent owned credit */
            board_video_cancel();assert(b.reserved==-1 && b.slots[first].owner==FREE);
            assert(!memcmp(before,&b,sizeof(b)));
        }
        cases++;
    }
    memset(&b,0,sizeof(b));b.reserved=-1;assert(board_video_try_reserve()==-1);
    b.opened=1;b.stopping=1;assert(board_video_try_reserve()==-1);
    b.stopping=0;b.null_backend=1;assert(board_video_try_reserve()==1 && b.reserved==-1);
    printf("PASS actual board atomic reservation: %u ownership/credit cases; closed/stopping/null guards\n",cases);
    return 0;
}
