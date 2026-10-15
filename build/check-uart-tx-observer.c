/* Offline ARM execution, anonymous RAM only. No hardware or A7 timing. */
#define _GNU_SOURCE
#include <assert.h>
#include <stdint.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#define KBASE 0xc0008000u
#define KSIZE 0x800000u
#define MBASE 0x01000000u
#define REGS 0x02000000u
#define PORT 0xc072961cu
#define ISR 0xc01177dcu
static unsigned char pristine[7476028], state[512], desc[128], action[64], ring[4096];
static unsigned char expected_module[0x100000];
void *fixture_copy(void *to,const void *from,size_t n) { return memcpy(to,from,n); }
static char line[8192];
static unsigned creates, removes, refs, syncs, reads, inserts, pushes, wakeups;
static int corrupt_code, fail_code, fail_lookup, fail_create, fail_pin;
static int (*show_cb)(void *,void *), (*stop_cb)(void *,void *), (*on_cb)(void *,void *);
static void put(void *p,unsigned off,uint32_t v) { memcpy((char *)p+off,&v,4); }
static uint32_t word(const void *p,unsigned off) { uint32_t v;memcpy(&v,(char *)p+off,4);return v; }
static void mapping(uint32_t address,size_t size) {
    void *p=mmap((void *)address,size,PROT_READ|PROT_WRITE|PROT_EXEC,
        MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);assert(p==(void *)address);
}
unsigned long fixture_lookup(const char *name) {
    if(!strcmp(name,"gp_uart_isr"))return fail_lookup?0:ISR;
    if(!strcmp(name,"gpHalUartGetIntSts"))return 0xc0117314;
    if(!strcmp(name,"irq_to_desc"))return 0xc015e158;
    if(!strcmp(name,"irq_get_irqchip_state"))return 0xc015f444;
    abort();
}
long fixture_read(void *to,const void *from,size_t size) {
    uintptr_t p=(uintptr_t)from;
    if(p>=KBASE && p+size<=KBASE+sizeof(pristine)) {
        if(fail_code)return -14;
        memcpy(to,pristine+p-KBASE,size);
        if(corrupt_code && p==ISR)((unsigned char *)to)[0]^=1;
        return 0;
    }
    assert((p>=PORT && p+size<=PORT+0x118) ||
        (p>=(uintptr_t)desc && p+size<=(uintptr_t)desc+sizeof(desc)) ||
        (p>=(uintptr_t)action && p+size<=(uintptr_t)action+sizeof(action)) ||
        (p>=(uintptr_t)state && p+size<=(uintptr_t)state+sizeof(state)));
    memcpy(to,from,size);return 0;
}
void *fixture_proc(const char *name,unsigned short mode,void *parent,void *show,void *data) {
    assert(mode==0400 && !parent && !data);
    if(fail_create==1 || (fail_create==2 && !strcmp(name,"d35_uart_tx_on")) || (fail_create==3 && !strcmp(name,"d35_uart_tx_off")))return NULL;
    if(!strcmp(name,"d35_uart_tx"))show_cb=show;
    else if(!strcmp(name,"d35_uart_tx_on"))on_cb=show;
    else {assert(!strcmp(name,"d35_uart_tx_off"));stop_cb=show;}
    creates++;return desc;
}
void fixture_remove(const char *name,void *parent) {
    assert(!parent);removes++;
    if(!strcmp(name,"d35_uart_tx"))show_cb=NULL;
    else if(!strcmp(name,"d35_uart_tx_on"))on_cb=NULL;
    else {assert(!strcmp(name,"d35_uart_tx_off"));stop_cb=NULL;}
}
void fixture_printf(void *seq,const char *fmt,...) {
    assert(seq==desc);va_list ap;va_start(ap,fmt);
    size_t used=strlen(line);int n=vsnprintf(line+used,sizeof(line)-used,fmt,ap);va_end(ap);
    assert(n>=0 && (size_t)n<sizeof(line)-used);
}
int fixture_get(void *module) { assert(module);if(fail_pin)return 0;refs++;return 1; }
void fixture_put(void *module) { assert(module && refs);refs--; }
void fixture_sync(unsigned irq) { assert(irq==19 && word(action,0)==ISR);syncs++; }
void *fixture_radix(const void *root,unsigned long key) { (void)root;assert(key==19);return desc; }
static void jump(uint32_t address,void *fn) {
    uint32_t data[]={0xe51ff004,(uint32_t)(uintptr_t)fn};memcpy((void *)address,data,sizeof(data));
}
static int model;static unsigned occupancy,model_writes;static unsigned char fifo[8];
static unsigned get_status(void *base) {
    reads++;
    if(model) {
        unsigned value=word(base,16)&~0xa0u;
        if(!occupancy)value|=0x80;
        if(occupancy==8)value|=0x20;
        put(base,16,value);
    }
    return ((unsigned (*)(void *))(REGS+4096))(base);
}
static void put_character(void *base,unsigned value) {
    if(model){assert(occupancy<8);model_writes++;fifo[occupancy++]=0;}
    ((void (*)(void *,unsigned))(REGS+4160))(base,value);
}
static void insertion(void) { inserts++;put((void *)REGS,16,0x10); }
static void push(void) { pushes++; }
static void wakeup(void) { wakeups++; }
static void reset_hw(unsigned status,unsigned flags,int queued) {
    memset((void *)PORT,0,0x118);memset(state,0,sizeof(state));memset(ring,0,sizeof(ring));memset((void *)REGS,0,32);
    put((void *)PORT,4,REGS);put((void *)PORT,0x48,19);put((void *)PORT,0xb4,0x76);
    put((void *)PORT,0x64,(uintptr_t)state);put((void *)PORT,0x54,8);
    *(unsigned char *)(PORT+0x108)=flags;
    put(state,0xb4,(uintptr_t)ring);if(queued){put(state,0xb8,1);ring[0]='A';}
    put((void *)REGS,8,0xb070 | ((flags&2)?0x4000:0));put((void *)REGS,16,status);
    reads=inserts=pushes=wakeups=0;
}
static void reset_owner(void) {
    memset(desc,0,sizeof(desc));memset(action,0,sizeof(action));
    put(desc,0x3c,(uintptr_t)action);put(action,0,ISR);put(action,4,PORT);
    put(desc,0x1c,69);
    reset_hw(0,0,0);
}
static void attach(void) { line[0]=0;assert(on_cb && !on_cb(desc,NULL)); }
static void show(void) { line[0]=0;assert(show_cb && !show_cb(desc,NULL)); }
static void detach(void) { line[0]=0;assert(stop_cb && !stop_cb(desc,NULL)); }
static unsigned field(const char *name) {
    char key[64];snprintf(key,sizeof(key),"%s=",name);char *p=strstr(line,key);assert(p);return (unsigned)strtoul(p+strlen(key),NULL,10);
}
/* Exercise the caller's preserved r4-r11 as well as the ISR return value. */
extern int call_checked(void *,int,void *);
asm(".text\n.align 2\n.global call_checked\ncall_checked:\n"
    "push {r4-r11,lr}\nsub sp,sp,#4\nmov ip,r0\nmov r0,r1\nmov r1,r2\n"
    "mov r4,#0x44\nmov r5,#0x55\nmov r6,#0x66\nmov r7,#0x77\n"
    "mov r8,#0x88\nmov r9,#0x99\nmov r10,#0xaa\nmov r11,#0xbb\nblx ip\n"
    "cmp r4,#0x44\nmovne r0,#99\ncmp r5,#0x55\nmovne r0,#99\n"
    "cmp r6,#0x66\nmovne r0,#99\ncmp r7,#0x77\nmovne r0,#99\n"
    "cmp r8,#0x88\nmovne r0,#99\ncmp r9,#0x99\nmovne r0,#99\n"
    "cmp r10,#0xaa\nmovne r0,#99\ncmp r11,#0xbb\nmovne r0,#99\n"
    "add sp,sp,#4\npop {r4-r11,pc}\n");
static void compare(unsigned status,unsigned flags,int queued) {
    unsigned char p[0x118], s[512], r[32], q[4096];unsigned counts[4];
    reset_hw(status,flags,queued);assert(call_checked((void *)ISR,19,(void *)PORT)==1);
    memcpy(p,(void *)PORT,sizeof(p));memcpy(s,state,sizeof(s));memcpy(r,(void *)REGS,sizeof(r));memcpy(q,ring,sizeof(q));
    counts[0]=reads;counts[1]=inserts;counts[2]=pushes;counts[3]=wakeups;
    reset_hw(status,flags,queued);assert(call_checked((void *)(uintptr_t)word(action,0),19,(void *)PORT)==1);
    assert(!memcmp(p,(void *)PORT,sizeof(p)) && !memcmp(s,state,sizeof(s)) && !memcmp(r,(void *)REGS,sizeof(r)) && !memcmp(q,ring,sizeof(q)));
    assert(counts[0]==reads && counts[1]==inserts && counts[2]==pushes && counts[3]==wakeups);
}
int main(int argc,char **argv) {
    assert(argc==7);mapping(KBASE,KSIZE);mapping(MBASE,0x100000);mapping(REGS,8192);mapping(0x03000000,0x100000);
    FILE *f=fopen(argv[1],"rb");assert(f && fread(pristine,1,sizeof(pristine),f)==sizeof(pristine));fclose(f);
    memcpy((void *)KBASE,pristine,sizeof(pristine));jump(0xc0445890,fixture_radix);
    memcpy((void *)(REGS+4096),(void *)0xc0117314,20);jump(0xc0117314,get_status);
    memcpy((void *)(REGS+4160),(void *)0xc01172fc,24);jump(0xc01172fc,put_character);
    jump(0xc0335ca0,insertion);jump(0xc031f418,push);jump(0xc0335f58,wakeup);
    f=fopen(argv[2],"rb");assert(f);size_t bytes=fread(expected_module,1,sizeof(expected_module),f);assert(bytes>0 && feof(f));fclose(f);
    f=fopen(argv[5],"rb");assert(f && fread((void *)MBASE,1,0x100000,f)==bytes);fclose(f);
    f=fopen(argv[6],"rb");assert(f);uint32_t count,symindex,relcount,relindices[128];
    assert(fread(&count,4,1,f)==1 && fread(&symindex,4,1,f)==1 && fread(&relcount,4,1,f)==1);
    assert(relcount<128 && count<256 && fread(relindices,4,relcount,f)==relcount);
    assert(fread((void *)0x03000000,1,0x100000,f)>count*40);fclose(f);
    __builtin___clear_cache((void *)KBASE,(char *)KBASE+KSIZE);
    int (*relocate)(void *,const char *,unsigned int,unsigned int,void *)=(void *)0xc010de00;
    for(unsigned i=0;i<relcount;i++)assert(!relocate((void *)0x03000000,"",symindex,relindices[i],NULL));
    assert(!memcmp((void *)MBASE,expected_module,bytes));
    puts("actual ARM relocator matches independent ELF relocation byte-for-byte");
    __builtin___clear_cache((void *)MBASE,(char *)MBASE+0x100000);__builtin___clear_cache((void *)REGS,(char *)REGS+8192);
    int (*start)(void)=(void *)(uintptr_t)strtoul(argv[3],NULL,0);
    void (*stop)(void)=(void *)(uintptr_t)strtoul(argv[4],NULL,0);
    reset_owner();assert(!start() && !refs && creates==3 && word(action,0)==ISR);
    puts("default load preserves the original IRQ handler; three private control endpoints");
    attach();assert(refs==1 && word(action,0)!=ISR && strstr(line,"start_result=0 attached=1"));
    puts("explicit attach verifies ownership/FIFO8 and pins exactly one live module reference");
    unsigned cases[]={0,0x10,0x80,0x90,0x2000,0x8000,0xa000,0xa080,0x20080,0xb070};
    for(unsigned i=0;i<10;i++)for(unsigned flags=0;flags<4;flags+=2)for(int queued=0;queued<2;queued++)compare(cases[i],flags,queued);
    puts("40 actual vendor-vs-bridge cases preserve RX/TX side effects, status reads, returns and r4-r11");
    unsigned hook=word(action,0);
    for(unsigned occ=0;occ<=8;occ++)for(unsigned length=0;length<=16;length++) {
        reset_hw(0x531f,2,0);put(state,0xb8,length);memset(ring,'Q',sizeof(ring));
        occupancy=occ;model_writes=0;model=1;
        assert(call_checked((void *)(uintptr_t)hook,19,(void *)PORT)==1);
        unsigned sent=occ==0?(length<4?length:4):(occ==8?0:(length?1:0));
        assert(model_writes==sent && occupancy==occ+sent && word(state,0xbc)==sent && word((void *)PORT,0x7c)==sent);
        if(!length || sent==length)assert(!(word((void *)REGS,8)&0x4000));
        model=0;
    }
    puts("153 FIFO occupancy/queue cases bound writes by available slots; full FIFO never receives a write");
    reset_hw(0x531f,2,0);put(state,0xb8,2);put(state,0xbc,4095);ring[4095]='W';occupancy=7;model_writes=0;model=1;
    assert(call_checked((void *)(uintptr_t)hook,19,(void *)PORT)==1 && word(state,0xbc)==0 && occupancy==8 && model_writes==1);model=0;
    puts("ring-tail wrap4095 to0 with one free FIFO slot; exactly one write and one dequeue");
    for(unsigned full=0;full<2;full++) {
        reset_hw(0x531f,2,1);*(unsigned char *)(PORT+0x58)='Z';occupancy=full?8:7;model_writes=0;model=1;
        assert(call_checked((void *)(uintptr_t)hook,19,(void *)PORT)==1);
        assert(model_writes==!full && word(state,0xbc)==0 && *(unsigned char *)(PORT+0x58)==(full?'Z':0));model=0;
    }
    puts("urgent character retains priority, queue tail and retry state when FIFO full");
    reset_hw(0x531f,2,1);put((void *)PORT,0xa8,1);occupancy=5;model_writes=0;model=1;
    assert(call_checked((void *)(uintptr_t)hook,19,(void *)PORT)==1 && !model_writes && !(word((void *)REGS,8)&0x4000));model=0;
    puts("hardware-stopped flow control uses original stop-TX without enqueueing");
    unsigned char tty[512]={0};tty[0x124]=1;
    reset_hw(0x531f,2,1);put(state,0x4c,(uintptr_t)tty);occupancy=4;model_writes=0;model=1;
    assert(call_checked((void *)(uintptr_t)hook,19,(void *)PORT)==1 && !model_writes && !(word((void *)REGS,8)&0x4000));model=0;
    reset_hw(0x531f,2,0);put(state,0xb8,300);occupancy=5;model_writes=0;model=1;
    assert(call_checked((void *)(uintptr_t)hook,19,(void *)PORT)==1 && !wakeups && word(state,0xbc)==1);model=0;
    reset_hw(0x531f,2,0);put(state,0xb8,100);occupancy=8;model_writes=0;model=1;
    assert(call_checked((void *)(uintptr_t)hook,19,(void *)PORT)==1 && !model_writes && !word(state,0xbc));
    for(unsigned i=0;i<100;i++) {
        if(occupancy)occupancy--; /* independent hardware drain between IRQs */
        assert(call_checked((void *)(uintptr_t)hook,19,(void *)PORT)==1 && occupancy<=8);
    }
    assert(model_writes==100 && word(state,0xbc)==100 && !(word((void *)REGS,8)&0x4000));model=0;
    puts("TTY stop and wakeup threshold preserved; full-to-draining FIFO retries deliver100 queued bytes without overflow");
    reset_hw(0x531f,0,1);assert(call_checked((void *)(uintptr_t)hook,19,(void *)PORT)==1 && !word(state,0xbc));
    puts("disabled TX path falls back to original entry without invented transmit service");
    reset_hw(0x531f,2,1);put((void *)PORT,0x54,16);
    assert(call_checked((void *)(uintptr_t)hook,19,(void *)PORT)==1 && !word(state,0xbc));show();assert(field("fault")==1);
    detach();assert(strstr(line,"restored=1 attached=0") && !refs);put((void *)PORT,0x54,8);attach();assert(refs==1);
    puts("runtime FIFO-size drift refuses added service but still restores the original handler and releases its pin");
    put(action,0,ISR+4);detach();assert(strstr(line,"stop_result=-19") && refs==1);
    put(action,0,hook);detach();assert(strstr(line,"restored=1 attached=0") && !refs && syncs==2 && word(action,0)==ISR);
    puts("ownership conflict keeps module pinned; successful restoration drains IRQ before unpin");
    attach();assert(refs==1 && word(action,0)==hook);detach();assert(!refs && syncs==3 && word(action,0)==ISR);
    detach();assert(syncs==3);show();assert(!field("attached"));stop();assert(!show_cb && !on_cb && !stop_cb);
    puts("repeated corrected/restored cycles and idempotent stop leave original handler and no reference leak");
    reset_owner();put((void *)PORT,0x54,16);assert(start()==-19);reset_owner();put(desc,0x1c,68);assert(start()==-19);
    reset_owner();put(action,4,PORT+4);assert(start()==-19);
    puts("wrong FIFO size, hardware IRQ and dev_id refuse before attachment");
    reset_owner();fail_lookup=1;assert(start()==-19);fail_lookup=0;corrupt_code=1;assert(start()==-19);corrupt_code=0;fail_code=1;assert(start()==-19);fail_code=0;
    puts("wrong symbols, changed kernel code and unreadable guards refuse before setup");
    fail_create=1;assert(start()==-12);fail_create=2;assert(start()==-12 && !show_cb);fail_create=3;assert(start()==-12 && !show_cb && !on_cb);fail_create=0;
    assert(!start());fail_pin=1;attach();assert(strstr(line,"start_result=-19") && !refs && word(action,0)==ISR);fail_pin=0;stop();
    puts("all three proc failures unwind; attach pin failure leaves the original handler");
    memcpy((void *)MBASE,expected_module,bytes);__builtin___clear_cache((void *)MBASE,(char *)MBASE+0x100000);reset_owner();assert(!start());attach();
    reset_hw(0,0,0);for(unsigned i=0;i<200010;i++)assert(call_checked((void *)(uintptr_t)word(action,0),19,(void *)PORT)==1);
    show();assert(field("calls")==200000 && field("bypass")==10);detach();stop();assert(!refs && word(action,0)==ISR);
    puts("capture ceiling falls back to original ISR and still permits complete restoration");
    puts("UART TX compiled checks passed; register/occupancy RAM model, no physical timing or silicon FIFO claims");
    return 0;
}
