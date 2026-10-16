/* Owner-backed-up ROMs, cold-boot cross-core regression. QEMU is correctness only. */
#define main existing_equivalence_main
#include "demand-private-v1/demand-equivalence.c"
#undef main
static unsigned scenario;
static int16_t controls(unsigned port,unsigned device,unsigned index,unsigned id)
{
 (void)index;unsigned mask=0;
 if(port || device!=RETRO_DEVICE_JOYPAD)return 0;
 /* Short separated menu impulses, followed by deterministic gameplay controls.
  * Preserve the resulting screenshots: input execution is not scene coverage. */
 if(frame>=600 && frame<2400 && frame%180<8)mask=1u<<RETRO_DEVICE_ID_JOYPAD_START;
 if(frame>=900 && frame<2400 && frame%180>=90 && frame%180<98)mask=1u<<RETRO_DEVICE_ID_JOYPAD_A;
 if(frame>=2400){
  if(scenario==2) mask=(1u<<RETRO_DEVICE_ID_JOYPAD_B); /* F-Zero throttle */
  else if(scenario==3)mask=(1u<<RETRO_DEVICE_ID_JOYPAD_B); /* Star Fox fire */
  else {mask=1u<<RETRO_DEVICE_ID_JOYPAD_RIGHT;if(frame%120<60)mask|=1u<<RETRO_DEVICE_ID_JOYPAD_B;if(frame%90<45)mask|=1u<<RETRO_DEVICE_ID_JOYPAD_Y;}
 }
 return id==RETRO_DEVICE_ID_JOYPAD_MASK?(int16_t)mask:id<16?(int)((mask>>id)&1):0;
}
static void image(const char *dir,unsigned at,struct core *c)
{
 char path[1024];snprintf(path,sizeof(path),"%s/frame-%05u.ppm",dir,at);FILE *f=fopen(path,"wb");assert(f);
 fprintf(f,"P6\n%u %u\n255\n",c->w,c->h);
 for(unsigned i=0;i<c->w*c->h;i++){unsigned p=c->frame_pixels[i];unsigned char rgb[3]={(p>>11)*255/31,((p>>5)&63)*255/63,(p&31)*255/31};assert(fwrite(rgb,1,3,f)==3);}assert(!fclose(f));
}
int main(int argc,char **argv)
{
 assert(argc==7);assert(argv[5][0]>='0' && argv[5][0]<='4' && !argv[5][1]);scenario=(unsigned)(argv[5][0]-'0');unsigned calls=6000;
 struct sigaction handler={0};handler.sa_sigaction=fault;handler.sa_flags=SA_SIGINFO;assert(!sigaction(SIGSEGV,&handler,NULL));
 size_t rom_n;unsigned char *rom=read_all(argv[3],&rom_n);struct core ref={0},test={0};
 open_core(&ref,argv[1],rom,rom_n);open_core(&test,argv[2],rom,rom_n);ref.set_input_state(controls);test.set_input_state(controls);
 void (*avinfo)(struct retro_system_av_info *);*(void **)(&avinfo)=dlsym(test.handle,"retro_get_system_av_info");assert(avinfo);struct retro_system_av_info av={0};avinfo(&av);printf("AV fps=%.9f sample_rate=%.3f\n",av.timing.fps,av.timing.sample_rate);
 size_t size=ref.serialize_size();assert(size==test.serialize_size());unsigned char *a=calloc(1,size),*b=calloc(1,size);assert(a&&b);
 /* Independent cold boots, as in the established equivalence oracle. */
 unsigned (*acquire)(void *,size_t);*(void **)(&acquire)=dlsym(test.handle,"d35_output_acquire");assert(acquire);
 void *allocation=NULL;assert(!posix_memalign(&allocation,64,512*240+256));unsigned char *target=allocation;
 memset(target,0xa5,512*240+256);unsigned changed=0,previous=0,routes[3]={0};unsigned long long samples=0;
 FILE *csv=fopen(argv[4],"w");assert(csv);fputs("frame,pixels_crc,pcm_crc,samples,width,height,route,changed\n",csv);
 for(frame=0;frame<calls;frame++){
  ref.pixels=ref.pcm=ref.videos=ref.samples=ref.batches=0;test.pixels=test.pcm=test.videos=test.samples=test.batches=0;
  active=&ref;ref.run();active=&test;unsigned route=frame%3;
  if(route==2)assert(!acquire(NULL,0));else assert(acquire(target+64,512*240+64));test.run();routes[route]++;
  if(ref.w!=test.w || ref.h!=test.h || ref.samples!=test.samples || ref.videos!=1 || test.videos!=1 || memcmp(ref.frame_pixels,test.frame_pixels,ref.w*ref.h*2) || memcmp(ref.frame_pcm,test.frame_pcm,ref.samples*4)){
   printf("FAIL output frame=%u geometry=%ux%u/%ux%u PCM=%08x/%08x pixels=%08x/%08x\n",frame,ref.w,ref.h,test.w,test.h,ref.pcm,test.pcm,ref.pixels,test.pixels);return 2;}
  for(unsigned i=0;i<32;i++)assert(target[i]==0xa5 && target[512*240+128+i]==0xa5);
  if(frame%30==0){active=&ref;assert(ref.serialize(a,size));active=&test;assert(test.serialize(b,size));normalize_pointers(a);normalize_pointers(b);if(memcmp(a,b,size)){for(size_t j=0,n=0;j<size && n<12;j++)if(a[j]!=b[j]){printf("DIFF offset=%u ref=%02x candidate=%02x\n",(unsigned)j,a[j],b[j]);n++;}printf("FAIL state frame=%u\n",frame);return 3;}}
  unsigned change=frame && previous!=test.pixels;changed+=change;previous=test.pixels;samples+=test.samples;
  fprintf(csv,"%u,%08x,%08x,%u,%u,%u,%u,%u\n",frame,test.pixels,test.pcm,(unsigned)test.samples,test.w,test.h,route,change);
  if(frame%600==599){image(argv[6],frame,&test);printf("CHECK frame=%u changed=%u samples=%llu\n",frame,changed,samples);fflush(stdout);}
 }
 fclose(csv);active=&ref;ref.unload_game();ref.deinit();active=&test;test.unload_game();test.deinit();
 dlclose(ref.handle);dlclose(test.handle);free(rom);free(a);free(b);free(allocation);
 printf("PASS calls=%u exact_pixels_PCM_geometry=1 normalized_state_checks=%u routes=%u,%u,%u changes=%u samples=%llu physical=0\n",calls,calls/30,routes[0],routes[1],routes[2],changed,samples);return 0;
}
