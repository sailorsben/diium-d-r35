/* Private offline scene inspection. Shares callbacks/loader with the qualified
 * equivalence harness; never install this capture path on the device. */
#define main d35_equivalence_main
#include "plus-a7-equivalence.c"
#undef main

static const char *capture_directory;
static FILE *capture_pcm;
static uint64_t captured_samples;
static void capture_video(const void *pixels,unsigned w,unsigned h,size_t pitch)
{
    video_cb(pixels,w,h,pitch);
    if(frame%30) return;
    char path[1024];
    assert(snprintf(path,sizeof(path),"%s/frame-%04u.ppm",capture_directory,frame)>0);
    FILE *out=fopen(path,"wb");assert(out);
    fprintf(out,"P6\n%u %u\n255\n",w,h);
    for(unsigned y=0;y<h;y++) {
        const uint16_t *row=(const uint16_t *)((const unsigned char *)pixels+y*pitch);
        for(unsigned x=0;x<w;x++) {
            uint16_t p=row[x];unsigned char rgb[3];
            rgb[0]=((p>>11)&31)*255/31;rgb[1]=((p>>5)&63)*255/63;rgb[2]=(p&31)*255/31;
            assert(fwrite(rgb,1,3,out)==3);
        }
    }
    assert(!fclose(out));
}
static size_t capture_audio(const int16_t *p,size_t n)
{
    assert(fwrite(p,4,n,capture_pcm)==n);
    captured_samples+=n;return audio_cb(p,n);
}
static int16_t no_input(unsigned port,unsigned device,unsigned index,unsigned id)
{ (void)port;(void)device;(void)index;(void)id;return 0; }
int main(int argc,char **argv)
{
    assert(argc==6);
    unsigned count=0;const char *digit=argv[5];assert(*digit);
    while(*digit){assert(*digit>='0' && *digit<='9' && count<=6000);count=count*10u+(unsigned)(*digit++-'0');}
    assert(count>=120 && count<=6000);
    capture_directory=argv[4];size_t n,state_n;
    unsigned char *rom=read_all(argv[2],&n),*state=read_all(argv[3],&state_n);
    struct core c={0};open_core(&c,argv[1],rom,n);
    assert(state_n==c.serialize_size()+40 && !memcmp(state,"D35MVP01",8));
    assert(c.unserialize(state+40,state_n-40));
    char path[1024];assert(snprintf(path,sizeof(path),"%s/native-s16le-stereo.pcm",capture_directory)>0);
    capture_pcm=fopen(path,"wb");assert(capture_pcm);
    c.set_video_refresh(capture_video);c.set_audio_sample_batch(capture_audio);c.set_input_state(no_input);
    for(frame=0;frame<count;frame++)c.run();
    assert(!fclose(capture_pcm));
    printf("PASS: offline private scene capture %u full frames, %llu native stereo PCM frames; no gameplay input\n",count,(unsigned long long)captured_samples);
    c.unload_game();c.deinit();dlclose(c.handle);free(rom);free(state);return 0;
}
