#define main d35_existing_main
#include "demand-equivalence.c"
#undef main
int main(int argc,char **argv){
 assert(argc==4);size_t length;unsigned char *rom=read_all(argv[3],&length);
 struct core a={0},b={0};open_core(&a,argv[1],rom,length);open_core(&b,argv[2],rom,length);
 unsigned (*pa)(unsigned,unsigned,unsigned,unsigned char *,unsigned),(*pb)(unsigned,unsigned,unsigned,unsigned char *,unsigned),(*hits)(void);
 *(void **)(&pa)=dlsym(a.handle,"d35_order_probe");*(void **)(&pb)=dlsym(b.handle,"d35_order_probe");
 *(void **)(&hits)=dlsym(b.handle,"d35_order_probe_hits_read");assert(pa&&pb&&hits);
 unsigned char *x=malloc(100000),*y=malloc(100000);assert(x&&y);unsigned tests=0,positive=0,fallback=0,limited=0;
 for(unsigned flags=0;flags<=128;flags=flags?flags*2:1)for(unsigned seed=0;seed<1024;seed+=flags?32:1)for(unsigned warm=0;warm<2;warm++){
  unsigned na=pa(seed,flags,warm,x,100000),nb=pb(seed,flags,warm,y,100000);assert(na&&na==nb);
  if(memcmp(x,y,na)){for(unsigned i=0;i<na;i++)if(x[i]!=y[i]){fprintf(stderr,"DIFF seed=%u flags=%u warm=%u byte=%u ref=%u new=%u\n",seed,flags,warm,i,x[i],y[i]);break;}return 1;}
  if(hits())positive++;else fallback++;
  for(unsigned i=na-32;i<na;i++)if(x[i]&0xc0){limited++;break;}
  tests++;
 }
 assert(positive&&fallback&&limited);printf("PASS original RenderScreen pixel/depth/OBJ-limit oracle: %u fixtures, %u positive, %u fallback, %u limited; cold/warm, flips,8/16,math,clips,Window2,OBJ rotation/limits,pitch/hires/mosaic guards\n",tests,positive,fallback,limited);
 return 0;
}
