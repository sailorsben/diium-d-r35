/* Exercise the generated board queue with the actual producer and worker. */
#include "board.c"
#include <assert.h>

static unsigned draws, flips;
static uint8_t source[1024*224];

void startup_note(const char *format, ...)
{
    (void)format;
}

static void draw(uint16_t *pixels, int width, int height)
{
    assert(width==256 && height==224);
    for (unsigned i=0; i<256*224-1; ++i)
        assert(pixels[i]==0);
    assert(pixels[256*224-1]==draws+1);
    ++draws;
}

static void flip(void)
{
    assert(draws==flips+1);
    ++flips;
}

int main(void)
{
    b.opened=1;
    assert(!setenv("D35_MEASURE_DISPLAY","1",1));
    assert(board_audio_open(32040)==44100 && board_audio_fd()==-1);
    struct board_audio_state pcm;
    assert(!board_audio_observe(&pcm) && pcm.rate==44100);
    assert(board_audio_write((const int16_t *)source,128)==128 && !board_audio_finish());
    assert(!strcmp(board_audio_error(),"measurement_sink"));
    board_audio_close();
    assert(!unsetenv("D35_MEASURE_DISPLAY"));
    b.reserved=b.previous=-1;
    b.draw_vfb=draw;
    b.flip_vfb=flip;
    b.pixels=calloc(SOURCE_SLOTS,SLOT_BYTES);
    assert(b.pixels);
    assert(!pthread_create(&b.worker,NULL,display_worker,NULL));
    b.worker_started=1;
    board_video_reuse_identical(1);
    for (unsigned frame=0; frame<1200; ++frame) {
        unsigned value=frame/3+1;
        uint8_t *last=source+223*1024+255*2;
        last[0]=(uint8_t)value;
        last[1]=(uint8_t)(value>>8);
        memset(source+512,(int)frame,512); /* Padding differs on each frame. */
        assert(board_video_reserve()==0);
        size_t size;
        uint8_t *target=board_video_target(&size);
        assert(size>=256*224*2 && (b.previous<0 || b.reserved!=b.previous));
        if (frame&1) {
            for (unsigned y=0;y<224;++y) memcpy(target+y*512,source+y*1024,512);
            assert(board_video_submit(target,256,224,512)==(frame%3!=0));
        } else {
            assert(board_video_submit(source,256,224,1024)==(frame%3!=0));
        }
    }
    board_wait_display();
    struct board_video_metrics metrics;
    board_video_metrics(&metrics,0);
    assert(draws==400 && flips==400 && metrics.flipped==400 && metrics.submitted==400);
    assert(metrics.reused_identical==800 && metrics.compare_ns>0);
    assert(metrics.direct_submitted==200 && metrics.copied_payload_bytes==200*256*224*2u);
    board_video_reuse_identical(0);
    uint8_t *last=source+223*1024+255*2;
    last[0]=(uint8_t)401;
    last[1]=(uint8_t)(401>>8);
    assert(board_video_submit(source,256,224,1024)==0);
    board_wait_display();
    assert(draws==401 && flips==401);
    pthread_mutex_lock(&display_lock);
    b.stopping=1;
    pthread_cond_broadcast(&display_condition);
    pthread_mutex_unlock(&display_lock);
    assert(!pthread_join(b.worker,NULL));
    free(b.pixels);
    puts("PASS board ownership, 800 byte-exact reuses, 400 ordered flips, direct and pitched input");
    return 0;
}
