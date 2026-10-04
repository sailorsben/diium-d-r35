#include <libretro.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <dlfcn.h>
static FILE *pcm, *batches;
static unsigned frame, video_count;
static size_t total;
static void (*get_info)(struct retro_system_info *);
static void (*get_av)(struct retro_system_av_info *);
static void (*run)(void);
static void (*finish)(void);
static void (*init)(void);
static bool (*load)(const struct retro_game_info *);
static bool environment(unsigned cmd, void *data)
{
   if (cmd == RETRO_ENVIRONMENT_SET_PIXEL_FORMAT)
      return *(enum retro_pixel_format *)data == RETRO_PIXEL_FORMAT_RGB565;
   if (cmd == RETRO_ENVIRONMENT_GET_VARIABLE) { ((struct retro_variable *)data)->value=NULL; return false; }
   if (cmd == RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE) { *(bool *)data=false; return true; }
   if (cmd == RETRO_ENVIRONMENT_GET_AUDIO_VIDEO_ENABLE) { *(int *)data=3; return true; }
   if (cmd == RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY || cmd == RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY) { *(const char **)data="."; return true; }
   return false;
}
static void video(const void *data, unsigned w, unsigned h, size_t pitch)
{
   unsigned x,y; FILE *f;
   ++video_count;
   if (!data || (frame!=1799 && frame!=3599 && frame!=7199 && frame!=8999)) return;
   assert(w && h && w<=512 && h<=512 && pitch>=w*2);
   char name[64]; snprintf(name,sizeof(name),"frame-%u.ppm",frame);
   f=fopen(name,"wb"); assert(f); fprintf(f,"P6\n%u %u\n255\n",w,h);
   for(y=0;y<h;++y) for(x=0;x<w;++x) {
      uint16_t p=((const uint16_t *)((const uint8_t *)data+y*pitch))[x];
      unsigned char rgb[3]={((p>>11)&31)*255/31,((p>>5)&63)*255/63,(p&31)*255/31};
      fwrite(rgb,1,3,f);
   }
   fclose(f);
}
static size_t audio(const int16_t *data,size_t n)
{
   assert(data && n<65536);
   fprintf(batches,"%u,%u,%u\n",frame,(unsigned)total,(unsigned)n);
   assert(fwrite(data,4,n,pcm)==n); total+=n; return n;
}
static void sample(int16_t l,int16_t r) { int16_t p[2]={l,r}; audio(p,1); }
static void poll(void) { }
static int16_t input(unsigned a,unsigned b,unsigned c,unsigned d) { (void)a;(void)b;(void)c;(void)d;return 0; }
int main(int argc,char **argv)
{
   void *core; FILE *rom; long n; struct retro_game_info game;
   struct retro_system_info info; struct retro_system_av_info av;
   assert(argc==4); core=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);
   if(!core) { fprintf(stderr,"%s\n",dlerror()); return 2; }
#define GET(ptr,name) *(void **)(&(ptr))=dlsym(core,name); assert(ptr)
   void (*set_env)(retro_environment_t); void (*set_video)(retro_video_refresh_t);
   void (*set_audio)(retro_audio_sample_t); void (*set_batch)(retro_audio_sample_batch_t);
   void (*set_poll)(retro_input_poll_t); void (*set_input)(retro_input_state_t);
   GET(set_env,"retro_set_environment"); GET(set_video,"retro_set_video_refresh");
   GET(set_audio,"retro_set_audio_sample"); GET(set_batch,"retro_set_audio_sample_batch");
   GET(set_poll,"retro_set_input_poll"); GET(set_input,"retro_set_input_state");
   GET(get_info,"retro_get_system_info");GET(get_av,"retro_get_system_av_info");
   GET(init,"retro_init");GET(finish,"retro_deinit");GET(load,"retro_load_game");GET(run,"retro_run");
   set_env(environment);set_video(video);set_audio(sample);set_batch(audio);set_poll(poll);set_input(input);
   get_info(&info);init();rom=fopen(argv[2],"rb");assert(rom);
   fseek(rom,0,SEEK_END);n=ftell(rom);rewind(rom);memset(&game,0,sizeof(game));
   game.path=argv[2];game.size=n;game.data=malloc(n);assert(game.data);
   assert(fread((void *)game.data,1,n,rom)==(size_t)n);fclose(rom);assert(load(&game));free((void *)game.data);
   get_av(&av);printf("%s %s rate=%.0f fps=%.9f\n",info.library_name,info.library_version,av.timing.sample_rate,av.timing.fps);
   pcm=fopen("native.s16le","wb");batches=fopen("batches.csv","w");assert(pcm&&batches);
   fprintf(batches,"frame,start_sample,frames\n");
   unsigned count=(unsigned)strtoul(argv[3],NULL,10);
   for(frame=0;frame<count;++frame) run();
   fclose(pcm);fclose(batches);printf("Captured frames=%u video=%u stereo_samples=%u\n",count,video_count,(unsigned)total);
   finish();dlclose(core);return 0;
}
