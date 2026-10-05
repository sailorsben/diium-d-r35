/* Exercise the real board queue with independently gated scaler/scanout. */
#include "board.c"
#include <assert.h>
static pthread_mutex_t gate=PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t gate_condition=PTHREAD_COND_INITIALIZER;
static unsigned drawn,flipped,permit,producer_started,producer_done,close_started,close_done;
static uint8_t *owned;
void startup_note(const char *format,...) { (void)format; }
int platform_heartbeat_open(void) { return 0; }
void platform_heartbeat_tick(void) {}
void platform_heartbeat_close(void) {}
static void draw(uint16_t *pixels,int w,int h)
{
    unsigned i;
    pthread_mutex_lock(&gate);
    ++drawn;assert(w==8 && h==8);
    for(i=0;i<64;i++) assert(pixels[i]==drawn);
    pthread_cond_broadcast(&gate_condition);pthread_mutex_unlock(&gate);
}
static void flip(void)
{
    pthread_mutex_lock(&gate);
    while(!permit) pthread_cond_wait(&gate_condition,&gate);
    ++flipped;pthread_cond_broadcast(&gate_condition);pthread_mutex_unlock(&gate);
}
static void submit(unsigned value)
{
    uint16_t pixels[64]; unsigned i;
    for(i=0;i<64;i++) pixels[i]=(uint16_t)value;
    assert(!board_video_submit(pixels,8,8,16));
    memset(pixels,0xee,sizeof(pixels)); /* Queue must retain its owned copy. */
}
static void *fourth(void *unused)
{
    (void)unused;
    pthread_mutex_lock(&gate);producer_started=1;pthread_cond_broadcast(&gate_condition);pthread_mutex_unlock(&gate);
    assert(!board_video_reserve()); submit(4);
    pthread_mutex_lock(&gate);producer_done=1;pthread_mutex_unlock(&gate);
    return NULL;
}
static void *close_board(void *unused)
{
    (void)unused;
    pthread_mutex_lock(&gate);close_started=1;pthread_cond_broadcast(&gate_condition);pthread_mutex_unlock(&gate);
    board_close();
    pthread_mutex_lock(&gate);close_done=1;pthread_mutex_unlock(&gate);
    return NULL;
}
int main(void)
{
    pthread_t producer,closer;struct board_video_metrics stats;
    owned=calloc(SOURCE_SLOTS,SLOT_BYTES);assert(owned);
    b.opened=1;b.reserved=-1;b.pixels=owned;b.first_frame=0;b.draw_vfb=draw;b.flip_vfb=flip;
    assert(!pthread_create(&b.worker,NULL,display_worker,NULL));b.worker_started=1;
    submit(1);
    pthread_mutex_lock(&gate);while(drawn<1) pthread_cond_wait(&gate_condition,&gate);pthread_mutex_unlock(&gate);
    submit(2);submit(3); /* Both publish while first scanout is blocked. */
    assert(!pthread_create(&producer,NULL,fourth,NULL));
    pthread_mutex_lock(&gate);while(!producer_started) pthread_cond_wait(&gate_condition,&gate);pthread_mutex_unlock(&gate);
    board_sleep_until(board_now_ns()+20000000u);
    pthread_mutex_lock(&gate);assert(!producer_done);permit=1;pthread_cond_broadcast(&gate_condition);pthread_mutex_unlock(&gate);
    pthread_join(producer,NULL);board_wait_display();board_video_metrics(&stats,0);
    assert(drawn==4 && flipped==4 && stats.submitted==4 && stats.scaled==4 && stats.flipped==4 && stats.queue_high==2);
    pthread_mutex_lock(&gate);permit=0;pthread_mutex_unlock(&gate);submit(5);
    pthread_mutex_lock(&gate);while(drawn<5) pthread_cond_wait(&gate_condition,&gate);pthread_mutex_unlock(&gate);
    assert(!pthread_create(&closer,NULL,close_board,NULL));
    pthread_mutex_lock(&gate);while(!close_started) pthread_cond_wait(&gate_condition,&gate);pthread_mutex_unlock(&gate);
    board_sleep_until(board_now_ns()+20000000u);
    pthread_mutex_lock(&gate);assert(!close_done);permit=1;pthread_cond_broadcast(&gate_condition);pthread_mutex_unlock(&gate);
    pthread_join(closer,NULL);assert(flipped==5);free(owned);
    puts("PASS: real display FIFO releases source before scanout, reserves queue credit, preserves pixels/order and joins before teardown");
    return 0;
}
