/* Independent renderer/platform pressure lab. No ROM/core loading. */
#define _GNU_SOURCE
#include "render-pressure-kernels.h"
#include "board.h"
#include "audio-pipe.h"
#include "native-pcm.h"
#include "startup.h"
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
#define PERIOD 16688153ull
#define MAX_FRAMES 1200u
SGFX GFX;
static struct rp_image image,oracle;
static uint16_t verification_pixels[RP_MAX];
static volatile sig_atomic_t stopped;
static volatile uint32_t sink;
static const char *output;
static unsigned phase_id,frames=180,mock;
int main(int argc,char **argv);
static uint64_t overall_deadline;
static struct {uint64_t begin,end,cpu,render,reserve,admit,submit,join,playable;unsigned pointer_valid;} samples[MAX_FRAMES];
static void cancel(int s){(void)s;stopped=1;}
static uint64_t clock_ns(clockid_t id){struct timespec t;if(syscall(SYS_clock_gettime,id,&t))return 0;return (uint64_t)t.tv_sec*1000000000u+t.tv_nsec;}
static uint64_t now(void){return clock_ns(CLOCK_MONOTONIC);}
static uint64_t cpu(void){return clock_ns(CLOCK_THREAD_CPUTIME_ID);}
static int expired(void){return stopped || !now() || now()>overall_deadline;}
static int durable(FILE *f){int r=fflush(f);if(!r)r=fsync(fileno(f));if(fclose(f))r=-1;return r;}
static int snapshot(const char *dir,const char *name){
 static const char *files[]={"/proc/uptime","/proc/stat","/proc/meminfo","/proc/interrupts","/proc/modules","/proc/d35_uart_tx","/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq","/sys/devices/system/clocksource/clocksource0/current_clocksource"};
 char p[1024],buf[2048];unsigned i;snprintf(p,sizeof(p),"%s/%s",dir,name);FILE *f=fopen(p,"w");if(!f)return -1;
 fprintf(f,"version=render-pressure2 mock=%u kernel_ns=%llu\n",mock,(unsigned long long)now());
 for(i=0;i<sizeof(files)/sizeof(files[0]);i++){
  fprintf(f,"\n--- %s ---\n",files[i]);int fd=open(files[i],O_RDONLY|O_NONBLOCK);if(fd<0){fprintf(f,"unavailable_errno=%d\n",errno);continue;}
  size_t left=32768;while(left){ssize_t n=read(fd,buf,left<sizeof(buf)?left:sizeof(buf));if(n<0&&errno==EINTR)continue;if(n<=0)break;fwrite(buf,1,(size_t)n,f);left-=(size_t)n;}close(fd);
 }
 return durable(f);
}
static int verify(const struct rp_scene *s,unsigned frame,const uint16_t *actual,const uint8_t *depth){
 rp_invalidate();rp_render(&oracle,oracle.pixels,s,frame,0);
 return memcmp(actual,oracle.pixels,s->w*s->h*2u) || memcmp(depth,oracle.depth,s->w*s->h);
}
static int self_test(void){
 unsigned s,v,f,cases=0;uint16_t *guarded=malloc((RP_MAX+32)*2);if(!guarded)return 1;
 for(s=0;s<6;s++)for(f=0;f<5;f++)for(v=1;v<3;v++){
  unsigned i;for(i=0;i<RP_MAX+32;i++)guarded[i]=0xa55a;
  rp_invalidate();rp_render(&image,guarded+16,&rp_scenes[s],f,v);
  if(verify(&rp_scenes[s],f,guarded+16,image.depth))return 2;
  for(i=0;i<16;i++)if(guarded[i]!=0xa55a || guarded[16+rp_scenes[s].w*rp_scenes[s].h+i]!=0xa55a)return 3;
  cases++;
 }
 free(guarded);printf("PASS scalar oracle / NEON / cached rows: %u full-frame cases; palette/tile churn, depth, windows, flips, geometry and guards\n",cases);return 0;
}
static void burn(unsigned ms){uint64_t end=cpu()+(uint64_t)ms*1000000u;while(cpu()<end){sink=sink*1664525u+1013904223u;}}
static int supervise(char **argv,int simulated){
 signal(SIGTERM,cancel);signal(SIGINT,cancel);
 pid_t child=fork();int status=0,forced=0,reaped=0;uint64_t deadline=now()+300000000000ull;
 if(child<0)return 71;
 if(!child){char *args[]={argv[0],argv[3],simulated?"--mock":NULL,NULL};exit(main(simulated?3:2,args));}
 for(;;){pid_t r=waitpid(child,&status,WNOHANG);if(r==child){reaped=1;break;}if(r<0&&errno!=EINTR)break;
  if(now()>=deadline||(!forced&&stopped)){if(!forced){kill(child,SIGTERM);forced=1;deadline=now()+3000000000ull;}else {kill(child,SIGKILL);break;}}
  struct timespec delay={0,100000000};syscall(SYS_nanosleep,&delay,NULL);
 }
 if(!reaped&&forced){uint64_t until=now()+3000000000ull;do{if(waitpid(child,&status,WNOHANG)==child){reaped=1;break;}struct timespec d={0,100000000};syscall(SYS_nanosleep,&d,NULL);}while(now()<until);}
 char p[1024];snprintf(p,sizeof(p),"%s/supervisor.txt",argv[3]);FILE *f=fopen(p,"w");if(f){fprintf(f,"forced=%d\nreaped=%d\nraw_status=%d\n",forced,reaped,status);durable(f);}
 if(forced||!reaped||!WIFEXITED(status))return 72;return WEXITSTATUS(status);
}
/* kind0=CPU,1=memory fill,2=copy,3=fill+copy,4=prebuilt display,
 * 5=render/display,6=audio-only. Every submitted drawing is retained. */
static int phase(unsigned scene,unsigned variant,unsigned kind,unsigned direct,unsigned serial,unsigned audio,int load,unsigned detailed,unsigned count){
 const struct rp_scene *s=&rp_scenes[scene];char dir[1024],path[1100];unsigned i,done=0,rate=0,prime=0,load_events=0;int failed=0,audio_started=0;
 size_t bytes=s->w*s->h*2u,capacity=0;uint64_t generated=0,remainder=0,begin,ended,cb,ce;uint32_t hash=0;
 struct board_video_metrics video={0};struct audio_pipe_stats astats={0};
 static int16_t silence[4096*2],tone[4096*2];snprintf(dir,sizeof(dir),"%s/phase-%03u",output,phase_id++);
 if(expired()||mkdir(dir,0700))return -1;
 snprintf(path,sizeof(path),"%s/begin.txt",dir);FILE *f=fopen(path,"w");if(!f)return -1;
 fprintf(f,"version=render-pressure2\nmock=%u\nscene=%s\nwidth=%u\nheight=%u\nlayers=%u\nworking_rows=%u\nvariant=%u\nkind=%u\ndirect=%u\nserial=%u\naudio=%u\nload_ms=%u\nload_every=%u\ndetailed=%u\nrequested_frames=%u\n",mock,s->name,s->w,s->h,s->layers,s->working_rows,variant,kind,direct,serial,audio,(unsigned)abs(load),load<0?30:1,detailed,count);if(durable(f))return -1;
 if(snapshot(dir,"before.txt"))return -1;
 memset(samples,0,sizeof(samples));rp_invalidate();rp_render(&image,image.pixels,s,0,variant);
 if(kind>=1&&kind<=3)memset(oracle.pixels,0x3c,bytes);
 if(kind>=4 && kind!=6)board_video_metrics(NULL,1);
 begin=now();cb=cpu();
 if(audio && !mock){
  audio_pipe_init();int r=board_audio_open(32040);if(r<0){failed=1;goto completed;}rate=(unsigned)r;
  prime=audio_pipe_prime_frames();if(!prime||prime>4096||audio_pipe_start()<0){failed=1;goto completed;}
  audio_started=1;if(audio_pipe_push(silence,prime)<0||audio_pipe_primed()<0){failed=1;goto completed;}
 }
 begin=now();cb=cpu();
 for(i=0;i<count && !expired();i++){
  uint16_t *target=image.pixels;uint64_t t,c,t0;unsigned n=0;
  /* Service the stock heartbeat even through CPU-only/memory cells. Input and
   * heartbeat run outside the detailed operation bracket, inside phase totals. */
  if(board_poll_input()&BOARD_MENU){stopped=1;break;}
  t=detailed?now():0;c=detailed?cpu():0;
  if(audio_started){
   remainder+=(uint64_t)rate*PERIOD;n=(unsigned)(remainder/1000000000u);remainder%=1000000000u;
   t0=detailed?now():0;if(n>4096 || audio_pipe_admit(n,1)<0){failed=1;break;}
   if(detailed)samples[i].admit=now()-t0;
  }
  if((kind>=4 && kind!=6) || (kind>=1 && kind<=3 && direct)){
   t0=detailed?now():0;if(board_video_reserve()<0){failed=1;break;}
   if(detailed)samples[i].reserve=now()-t0;
   if(direct&&!mock){target=board_video_target(&capacity);if(!target||capacity<bytes){failed=1;board_video_cancel();break;}}
  }
  t0=detailed?now():0;
  if(kind==0 || kind==5)rp_render(&image,target,s,i,variant);
  else if(kind==1)memset(target,(int)(i&255),bytes);
  else if(kind==2)memcpy(target,oracle.pixels,bytes);
  else if(kind==3){memset(oracle.pixels,(int)(i&255),bytes);memcpy(target,oracle.pixels,bytes);}
  else if(kind==4 && direct)memcpy(target,image.pixels,bytes);
  if(load>0 || (load<0 && i%30==29)){burn((unsigned)abs(load));load_events++;}
  if(detailed)samples[i].render=now()-t0;
  /* Last-frame validation copy is explicit overhead, included in total time
   * and excluded by the analyzer from per-frame performance distributions. */
  if(i+1==count)memcpy(verification_pixels,target,bytes);
  sink^=target[(i*97u)%(s->w*s->h)];
  if(kind>=4 && kind!=6){t0=detailed?now():0;if(board_video_submit(target,s->w,s->h,s->w*2u)<0){failed=1;board_video_cancel();break;}if(detailed)samples[i].submit=now()-t0;}
  else if(kind>=1 && kind<=3 && direct)board_video_cancel();
  if(audio_started){
   unsigned j,ramp=rate/50;uint64_t total=(uint64_t)rate*PERIOD*count/1000000000u;
   for(j=0;j<n;j++){uint64_t at=generated+j;unsigned p=(unsigned)(at&127);int value=((int)(p<64?p:127-p)-32)*32;
    if(at<ramp)value=(int)((int64_t)value*(int64_t)at/ramp);
    if(total-at-1<ramp)value=(int)((int64_t)value*(int64_t)(total-at-1)/ramp);
    tone[j*2]=tone[j*2+1]=(int16_t)value;
   }
   if(audio_pipe_push(tone,n)<0){failed=1;break;}generated+=n;
   struct audio_pipe_stats a;audio_pipe_stats(&a);
   if(detailed){samples[i].playable=a.playable;samples[i].pointer_valid=a.boundary>0 && a.appl_ptr%a.boundary==a.epoch_transferred%a.boundary && (a.appl_ptr-a.hw_ptr)%a.boundary==a.playable && a.playable<=a.buffer;}
   if(a.error){failed=1;break;}
  }
  if(serial && kind>=4 && kind!=6){t0=detailed?now():0;board_wait_display();if(detailed)samples[i].join=now()-t0;}
  if(detailed){samples[i].begin=t;samples[i].end=now();samples[i].cpu=cpu()-c;}
  done++;
 }
completed:
 if(done<count)failed=1;
 /* Completion time includes worker drain; per-frame overlapping work is never summed as wall time. */
 if(kind>=4 && kind!=6)board_wait_display();ended=now();ce=cpu();
 if(kind==0 || kind==5){
  if(done==count){hash=rp_hash(verification_pixels,bytes);if(verify(s,done-1,verification_pixels,image.depth))failed=1;}
 }
 else if(done==count){hash=rp_hash(verification_pixels,bytes);
  if(kind>=1&&kind<=3){unsigned j;uint8_t expected=kind==2?0x3c:(uint8_t)((count-1)&255);for(j=0;j<bytes;j++)if(((uint8_t *)verification_pixels)[j]!=expected){failed=1;break;}}
 }
 if(audio_started){audio_pipe_stop(!failed&&!stopped);if(failed||stopped)audio_pipe_clear();audio_pipe_stats(&astats);if(astats.error || astats.enqueued!=prime+generated || astats.accepted+astats.remaining+astats.cleared!=astats.enqueued)failed=1;/* audio_pipe_stop(1) drains in the joined audio owner; never finish twice. */pcm_cost_flush(dir);}
 if(kind>=4&&kind!=6){board_video_metrics(&video,0);if(!mock && (video.submitted!=done || video.scaled!=done || video.flipped!=done))failed=1;}
 snprintf(path,sizeof(path),"%s/samples.csv",dir);f=fopen(path,"w");if(!f)return -1;
 fprintf(f,"#version=render-pressure2\n#mock=%u\n#detailed=%u\nframe,begin_ns,end_ns,cpu_ns,render_ns,reserve_ns,admit_ns,submit_ns,join_ns,playable,pointer_valid\n",mock,detailed);
 if(detailed)for(i=0;i<done;i++)fprintf(f,"%u,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%u\n",i,(unsigned long long)samples[i].begin,(unsigned long long)samples[i].end,(unsigned long long)samples[i].cpu,(unsigned long long)samples[i].render,(unsigned long long)samples[i].reserve,(unsigned long long)samples[i].admit,(unsigned long long)samples[i].submit,(unsigned long long)samples[i].join,(unsigned long long)samples[i].playable,samples[i].pointer_valid);
 if(durable(f))return -1;
 snprintf(path,sizeof(path),"%s/result.txt",dir);f=fopen(path,"w");if(!f)return -1;
 fprintf(f,"version=render-pressure2\nmock=%u\ncompleted=%u\nfailed=%d\nstopped=%d\nwall_ns=%llu\nmain_cpu_ns=%llu\nhash=%08x\nsubmitted=%llu\nscaled=%llu\nflipped=%llu\ndirect_submitted=%llu\ncopied_bytes=%llu\nscale_ns=%llu\nflip_ns=%llu\nworker_cpu_ns=%llu\nreserve_wait_ns=%llu\nrate=%u\nprimed_frames=%u\ngenerated_frames=%llu\naudio_enqueued=%llu\naudio_accepted=%llu\naudio_remaining=%u\naudio_cleared=%llu\naudio_error=%d\naudio_cpu_ns=%llu\nplayable_min=%u\nxruns=%llu\n",
 mock,done,failed,(int)stopped,(unsigned long long)(ended-begin),(unsigned long long)(ce-cb),hash,(unsigned long long)video.submitted,(unsigned long long)video.scaled,(unsigned long long)video.flipped,(unsigned long long)video.direct_submitted,(unsigned long long)video.copied_payload_bytes,(unsigned long long)video.scale_ns,(unsigned long long)video.flip_ns,(unsigned long long)video.worker_cpu_ns,(unsigned long long)video.reserve_wait_ns,rate,prime,(unsigned long long)generated,(unsigned long long)astats.enqueued,(unsigned long long)astats.accepted,astats.remaining,(unsigned long long)astats.cleared,astats.error,(unsigned long long)astats.worker_cpu_ns,astats.playable_min,(unsigned long long)astats.xruns);
 fprintf(f,"board_error=%s\naudio_detail=%s\nvalidation_copy_bytes=%zu\n",board_last_error(),board_audio_error(),done==count?bytes:0);
 fprintf(f,"pcm_boundary=%u\npcm_buffer=%u\npcm_epoch=%u\npcm_trace_required=%u\n",astats.boundary,astats.buffer,astats.epoch,audio_started?1:0);
 fprintf(f,"load_events=%u\n",load_events);
 fprintf(f,"begin_ns=%llu\nend_ns=%llu\n",(unsigned long long)begin,(unsigned long long)ended);
 if(durable(f))return -1;
 if(audio&&!mock)board_audio_close();
 if(snapshot(dir,"after.txt"))return -1;
 return failed?-1:0;
}
int main(int argc,char **argv){
 if(argc==4&&(!strcmp(argv[1],"--supervise")||!strcmp(argv[1],"--supervise-mock"))&&!strcmp(argv[2],"--output"))return supervise(argv,!strcmp(argv[1],"--supervise-mock"));
 unsigned s,v,k,d,q,a,issues=0;GFX.ZERO=calloc(65536,2);if(!GFX.ZERO)return 2;rp_zero_table();
 if(argc==2&&!strcmp(argv[1],"--self-test")){int r=self_test();free(GFX.ZERO);return r;}
 if(argc<2||argc>3)return 2;output=argv[1];mock=argc==3&&!strcmp(argv[2],"--mock");if(argc==3&&!mock)return 2;
 if(mock)frames=2;signal(SIGTERM,cancel);signal(SIGINT,cancel);overall_deadline=now()+240000000000ull;
 startup_begin();if(board_open(mock)<0){startup_end();free(GFX.ZERO);return 3;}
 /* Establish a real first paint before any held-input abort or CPU-only cell. */
 rp_invalidate();rp_render(&image,image.pixels,&rp_scenes[0],0,1);
 if(board_video_submit(image.pixels,256,224,512)<0){board_close();startup_end();free(GFX.ZERO);return 3;}
 board_wait_display();startup_ready();
 for(s=0;s<6&&!expired();s++)for(v=0;v<3&&!expired();v++)issues+=phase(s,v,0,0,0,0,0,1,mock?2:32)!=0;
 for(s=0;s<6&&!expired();s+=s==0?4:1)for(k=1;k<=3;k++)for(d=0;d<2;d++)issues+=phase(s,1,k,d,0,0,0,1,mock?2:32)!=0;
 for(s=0;s<6&&!expired();s+=s==0?4:1)for(q=0;q<2;q++)issues+=phase(s,1,4,0,q,0,0,1,frames)!=0;
 issues+=phase(0,1,6,0,0,1,0,1,frames)!=0;
 for(v=1;v<3&&!expired();v++)for(d=0;d<2;d++)for(q=0;q<2;q++)for(a=0;a<2;a++)issues+=phase(1,v,5,d,q,a,0,1,frames)!=0;
 for(k=4;k<=16&&!expired();k+=4)issues+=phase(0,2,5,1,0,1,k,1,frames)!=0;
 for(k=0;k<3&&!expired();k++)issues+=phase(0,2,5,1,0,1,-(int)(k==0?24:k==1?48:80),1,frames)!=0;
 /* Matched instrumentation controls, detailed/aggregate then reversed. */
 for(k=0;k<4&&!expired();k++)issues+=phase(0,2,5,1,0,1,0,k==0||k==3,frames)!=0;
 board_wait_display();board_close();startup_end();char p[1024];snprintf(p,sizeof(p),"%s/summary.txt",output);FILE *f=fopen(p,"w");if(!f)return 4;
 fprintf(f,"version=render-pressure2\nmock=%u\nphases=%u\nplanned_phases=70\nissues=%u\nstopped=%d\nexpired=%d\n",mock,phase_id,issues,(int)stopped,expired());int r=durable(f);free(GFX.ZERO);return r?4:stopped||expired()?5:issues?1:0;
}
