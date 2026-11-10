/* Price equality and repacking separately using real replay callbacks. */
#include "snes-rgb565-reuse.h"

static uint8_t packed[512*512*2], retained[512*512*2];
static unsigned prior_width, prior_height, repeats, direct_repeats, copied, copy_avoided;
static uint64_t compare_ns, copy_ns, avoided_copy_ns;

static void display_probe(const void *data,unsigned width,unsigned height,size_t pitch)
{
    assert(width && width<=512 && height && height<=512 && pitch>=width*2);
    bool direct=data==offered_target && pitch==width*2;
    uint64_t began=cpu();
    bool same=prior_width==width && prior_height==height &&
              d35_same_rgb565(data,pitch,retained,width,height);
    compare_ns+=cpu()-began;
    const uint8_t *src=data;
    size_t bytes=width*2;
    began=cpu();
    if (!direct)
        for (unsigned y=0;y<height;y++)
            memcpy(packed+y*bytes,src+y*pitch,bytes);
    uint64_t copy=cpu()-began;
    if (!direct) {
        copy_ns+=copy;
        ++copied;
    }
    const void *current=direct?data:packed;
    bool equal=prior_width==width && prior_height==height &&
               memcmp(current,retained,bytes*height)==0;
    assert(same==equal);
    if (same) {
        ++repeats;
        direct_repeats+=direct;
        if (!direct) {
            ++copy_avoided;
            avoided_copy_ns+=copy;
        }
    } else {
        memcpy(retained,current,bytes*height);
        prior_width=width;
        prior_height=height;
    }
}

static void display_probe_report(void)
{
    printf("display_probe reused=%u direct_reused=%u repacked=%u repacks_avoided=%u "
           "compare_ns=%"PRIu64" repack_ns=%"PRIu64" avoided_repack_ns=%"PRIu64"\n",
           repeats,direct_repeats,copied,copy_avoided,compare_ns,copy_ns,avoided_copy_ns);
}
