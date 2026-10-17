/* Execute the actual original/patched kernel instructions in anonymous RAM.
 * Reuse the independent board/ABI fixture, not the module implementation.
 */
#define main unused_module_fixture_main
#include "check-uart-tx-observer.c"
#undef main
static unsigned char *original_image,*corrected_image;
static void kernel_put(void *base,unsigned value){
 if(model){assert(occupancy<8);model_writes++;fifo[occupancy++]=(unsigned char)value;}
 ((void (*)(void *,unsigned))(REGS+4160))(base,value);
}
static void setup(const unsigned char *image){
 memcpy((void *)KBASE,image,7476028);
 memcpy((void *)(REGS+4096),(void *)0xc0117314,20);
 memcpy((void *)(REGS+4160),(void *)0xc01172fc,24);
 jump(0xc0117314,get_status);jump(0xc01172fc,kernel_put);
 jump(0xc0335ca0,insertion);jump(0xc031f418,push);jump(0xc0335f58,wakeup);
 __builtin___clear_cache((void *)KBASE,(void *)(KBASE+KSIZE));__builtin___clear_cache((void *)REGS,(void *)(REGS+8192));
}
static void read_image(const char *path,unsigned char **out){
 *out=malloc(7476028);assert(*out);FILE *f=fopen(path,"rb");assert(f && fread(*out,1,7476028,f)==7476028 && fgetc(f)==EOF);assert(!fclose(f));
}
int main(int argc,char **argv){
 setbuf(stdout,NULL);
 assert(argc==3);mapping(KBASE,KSIZE);mapping(REGS,8192);read_image(argv[1],&original_image);read_image(argv[2],&corrected_image);
 /* Actual old-code control demonstrates both faults before correction. */
 setup(original_image);reset_hw(0x531f,2,1);assert(call_checked((void *)ISR,19,(void *)PORT)==1 && !word(state,0xbc));
 ((void (*)(void *,unsigned))(REGS+4160))((void *)REGS,0x5a);assert(word((void *)REGS,0)==0);
 puts("PASS old kernel control reproduces ignored TX-pending and literal-zero data");
 unsigned statuses[]={0,0x10,0x2000,0x8000,0xa000,0xa010};unsigned rx_cases=0;
 for(unsigned i=0;i<sizeof(statuses)/sizeof(*statuses);i++)for(unsigned flags=0;flags<4;flags++){
  unsigned char p[0x118],s[512],r[32],q[4096];unsigned c[4];
  setup(original_image);reset_hw(statuses[i],flags,1);assert(call_checked((void *)ISR,19,(void *)PORT)==1);
  memcpy(p,(void *)PORT,sizeof(p));memcpy(s,state,sizeof(s));memcpy(r,(void *)REGS,sizeof(r));memcpy(q,ring,sizeof(q));c[0]=reads;c[1]=inserts;c[2]=pushes;c[3]=wakeups;
  setup(corrected_image);reset_hw(statuses[i],flags,1);assert(call_checked((void *)ISR,19,(void *)PORT)==1);
  assert(!memcmp(p,(void *)PORT,sizeof(p)) && !memcmp(s,state,sizeof(s)) && !memcmp(r,(void *)REGS,sizeof(r)) && !memcmp(q,ring,sizeof(q)));
  assert(c[0]==reads && c[1]==inserts && c[2]==pushes && c[3]==wakeups);rx_cases++;
 }
 printf("PASS %u original-vs-corrected RX/no-TX snapshots including callee registers\n",rx_cases);
 setup(corrected_image);
 for(unsigned value=0;value<256;value++){
  reset_hw(0,0,0);((void (*)(void *,unsigned))(REGS+4160))((void *)REGS,value);assert(word((void *)REGS,0)==value);
 }
 puts("PASS actual corrected PutChar preserves all256 byte values");
 unsigned cases=0;unsigned char tty[512];
 for(unsigned occ=0;occ<=8;occ++)for(unsigned length=0;length<=16;length++)for(unsigned urgent=0;urgent<2;urgent++)for(unsigned hw=0;hw<2;hw++)for(unsigned sw=0;sw<2;sw++)for(unsigned flow=0;flow<3;flow++)for(unsigned wrap=0;wrap<2;wrap++){
  reset_hw(0x531f,sw?2:0,0);put((void *)REGS,8,0xb070|(hw?0x4000:0));unsigned tail=wrap?4095:0;put(state,0xbc,tail);put(state,0xb8,(tail+length)&4095);ring[tail]=0xa5;
  if(urgent)*(unsigned char *)(PORT+0x58)=0x5a;
  memset(tty,0,sizeof(tty));if(flow==1){tty[0x124]=1;put(state,0x4c,(uintptr_t)tty);}if(flow==2)put((void *)PORT,0xa8,1);
  occupancy=occ;model_writes=0;model=1;
  assert(call_checked((void *)ISR,19,(void *)PORT)==1);model=0;
  unsigned sent=hw && sw && occ<8 && (urgent || (length && !flow));
  unsigned stopped=hw && sw && !urgent && (!length || flow || (sent && length==1));
  assert(model_writes==sent && occupancy==occ+sent && word((void *)PORT,0x7c)==sent);
  if(word(state,0xbc)!=((tail+(!urgent?sent:0))&4095))fprintf(stderr,"queue mismatch occ=%u length=%u urgent=%u hw=%u sw=%u flow=%u wrap=%u got=%u want=%u\n",occ,length,urgent,hw,sw,flow,wrap,word(state,0xbc),((tail+(!urgent?sent:0))&4095));
  assert(word(state,0xbc)==((tail+(!urgent?sent:0))&4095));
  assert(*(unsigned char *)(PORT+0x58)==(urgent && !sent?0x5a:0));
  if(sent)assert(fifo[occ]==(urgent?0x5a:0xa5) && word((void *)REGS,0)==(urgent?0x5a:0xa5));
  assert(!!(word((void *)REGS,8)&0x4000)==(hw && !stopped));
  assert(wakeups==(!urgent && sent && length-1<256));assert(reads==1);cases++;
 }
 printf("PASS %u independent FIFO/queue/enable/flow/urgent/wrap cases; one status read and at most one byte\n",cases);
 reset_hw(0x531f,2,0);put(state,0xb8,300);memset(ring,0x6d,sizeof(ring));occupancy=8;model_writes=0;model=1;
 for(unsigned i=0;i<300;i++){if(occupancy)occupancy--;assert(call_checked((void *)ISR,19,(void *)PORT)==1 && occupancy<=8);}
 model=0;assert(model_writes==300 && word(state,0xbc)==300 && !(word((void *)REGS,8)&0x4000) && !(*(unsigned char *)(PORT+0x108)&2));
 puts("PASS full-to-draining retries deliver300 real-valued bytes and stop TX at empty queue");
 reset_hw(0xd31f,2,1);occupancy=7;model_writes=0;model=1;assert(call_checked((void *)ISR,19,(void *)PORT)==1);model=0;assert(inserts==1 && pushes==1 && model_writes==1 && word(state,0xbc)==1);
 puts("PASS mixed RX/TX delivers RX before bounded TX service");
 puts("PASS direct kernel driver checks; no module, IRQ action replacement, hardware timing or wire proof");return 0;
}
