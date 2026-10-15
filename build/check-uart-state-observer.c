/* Offline QEMU harness for the compiled module. Kernel APIs are fixtures;
 * actual archived irq_to_desc/GetCtrl execute against anonymous RAM only.
 * No device nodes or real MMIO. Timings are artificial, never A7 measurements.
 */
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
static unsigned char pristine[7476028], state[512], desc[128], action[64];
static unsigned char expected_module[0x100000];
static char line[1024];
static unsigned creates, removes;
static int corrupt_code, fail_code, fail_queue, fail_lookup, fail_create;
static int (*show_cb)(void *,void *);
static void put(void *p,unsigned off,uint32_t v) { memcpy((char *)p+off,&v,4); }
static void mapping(uint32_t address,size_t size) {
    void *p=mmap((void *)address,size,PROT_READ|PROT_WRITE|PROT_EXEC,
                 MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
    assert(p==(void *)address);
}
unsigned long fixture_lookup(const char *name) {
    if(!strcmp(name,"gp_uart_isr"))return fail_lookup?0:0xc01177dc;
    if(!strcmp(name,"gpHalUartGetCtrl"))return 0xc0117364;
    if(!strcmp(name,"irq_to_desc"))return 0xc015e158;
    abort();
}
long fixture_read(void *to,const void *from,size_t size) {
    uintptr_t p=(uintptr_t)from;
    if(p>=KBASE && p+size<=KBASE+sizeof(pristine)) {
        if(fail_code)return -14;
        memcpy(to,pristine+p-KBASE,size);
        if(corrupt_code && p==0xc01177dc)((unsigned char *)to)[0]^=1;
        return 0;
    }
    if(from==(void *)(state+0xb8) && fail_queue)return -14;
    assert((p>=PORT && p+size<=PORT+0x118) ||
           (p>=(uintptr_t)desc && p+size<=(uintptr_t)desc+sizeof(desc)) ||
           (p>=(uintptr_t)action && p+size<=(uintptr_t)action+sizeof(action)) ||
           (p>=(uintptr_t)state && p+size<=(uintptr_t)state+sizeof(state)));
    memcpy(to,from,size);return 0;
}
void *fixture_proc(const char *name,unsigned short mode,void *parent,void *show,void *data) {
    assert(!strcmp(name,"d35_uart_state") && mode==0400 && !parent && !data);
    if(fail_create)return NULL;
    creates++;show_cb=show;return desc;
}
void fixture_remove(const char *name,void *parent) {
    assert(!strcmp(name,"d35_uart_state") && !parent);removes++;show_cb=NULL;
}
void fixture_printf(void *seq,const char *fmt,...) {
    assert(seq==desc);va_list ap;va_start(ap,fmt);vsnprintf(line,sizeof(line),fmt,ap);va_end(ap);
}
uint64_t fixture_clock(void) { static uint64_t n;return n+=1000; }
void *fixture_radix(const void *root,unsigned long key) { (void)root;assert(key==19);return desc; }
static void jump(uint32_t address,void *fn) {
    uint32_t data[]={0xe51ff004,(uint32_t)(uintptr_t)fn};memcpy((void *)address,data,sizeof(data));
}
static void reset(void) {
    memset((void *)PORT,0,0x118);memset(state,0,sizeof(state));memset(desc,0,sizeof(desc));memset(action,0,sizeof(action));
    put((void *)PORT,4,REGS);put((void *)PORT,0x48,19);put((void *)PORT,0xb4,0x76);
    put((void *)PORT,0x64,(uintptr_t)state);put(desc,0x3c,(uintptr_t)action);
    put(action,0,0xc01177dc);put(action,4,PORT);put((void *)REGS,8,0x4000);
    fail_queue=0;
}
static void check_show(const char *needle,int hardware_allowed) {
    unsigned char before[0x118], registers[32], saved_state[512], saved_action[64], saved_desc[128];
    memcpy(before,(void *)PORT,sizeof(before));memcpy(registers,(void *)REGS,sizeof(registers));
    memcpy(saved_state,state,sizeof(state));memcpy(saved_action,action,sizeof(action));memcpy(saved_desc,desc,sizeof(desc));
    if(!hardware_allowed)assert(!mprotect((void *)REGS,4096,PROT_NONE));
    assert(show_cb && show_cb(desc,NULL)==0);assert(strstr(line,needle));
    if(!hardware_allowed)assert(!mprotect((void *)REGS,4096,PROT_READ|PROT_WRITE));
    assert(!memcmp(before,(void *)PORT,sizeof(before)) && !memcmp(registers,(void *)REGS,sizeof(registers)));
    assert(!memcmp(saved_state,state,sizeof(state)) && !memcmp(saved_action,action,sizeof(action)) && !memcmp(saved_desc,desc,sizeof(desc)));
}
int main(int argc,char **argv) {
    assert(argc==7);mapping(KBASE,KSIZE);mapping(MBASE,0x100000);mapping(REGS,4096);mapping(0x03000000,0x100000);
    FILE *f=fopen(argv[1],"rb");assert(f && fread(pristine,1,sizeof(pristine),f)==sizeof(pristine));fclose(f);
    memcpy((void *)KBASE,pristine,sizeof(pristine));jump(0xc0445890,fixture_radix);
    f=fopen(argv[2],"rb");assert(f);size_t bytes=fread(expected_module,1,sizeof(expected_module),f);assert(bytes>0 && feof(f));fclose(f);
    f=fopen(argv[5],"rb");assert(f);assert(fread((void *)MBASE,1,0x100000,f)==bytes);fclose(f);
    f=fopen(argv[6],"rb");assert(f);uint32_t count,symindex,relcount,relindices[128];
    assert(fread(&count,4,1,f)==1 && fread(&symindex,4,1,f)==1 && fread(&relcount,4,1,f)==1);
    assert(relcount<128 && count<256 && fread(relindices,4,relcount,f)==relcount);
    assert(fread((void *)0x03000000,1,0x100000,f)>count*40);fclose(f);
    __builtin___clear_cache((void *)KBASE,(char *)KBASE+KSIZE);
    int (*relocate)(void *,const char *,unsigned int,unsigned int,void *)=(void *)0xc010de00;
    for(unsigned i=0;i<relcount;i++)assert(relocate((void *)0x03000000,"",symindex,relindices[i],NULL)==0);
    assert(!memcmp((void *)MBASE,expected_module,bytes));
    puts("actual archived ARM module relocator matches the independent ELF fixture byte-for-byte");
    __builtin___clear_cache((void *)KBASE,(char *)KBASE+KSIZE);__builtin___clear_cache((void *)MBASE,(char *)MBASE+0x100000);
    int (*start)(void)=(void *)(uintptr_t)strtoul(argv[3],NULL,0);
    void (*stop)(void)=(void *)(uintptr_t)strtoul(argv[4],NULL,0);
    reset();assert(start()==0 && creates==1 && !removes);puts("exact identity creates only the owned 0400 proc entry");
    check_show("empty=1 mismatch=1",1);puts("hardware TX enabled/software disabled mismatch is reported without state changes");
    *(unsigned char *)(PORT+0x108)=2;check_show("empty=1 mismatch=0",1);puts("coherent TX state is reported without state changes");
    put((void *)REGS,8,0);check_show("empty=1 mismatch=1",1);puts("opposite enable mismatch is distinguished");
    put(action,0,0xc01177e0);check_show("result=-19",0);puts("wrong handler refuses control-register access");
    reset();put(action,4,PORT+4);check_show("result=-19",0);puts("wrong handler owner refuses control-register access");
    reset();put((void *)PORT,0x48,18);check_show("result=-19",0);puts("wrong port IRQ refuses control-register access");
    reset();put((void *)PORT,0x64,0);check_show("result=-19",0);puts("absent serial state refuses control-register access");
    reset();fail_queue=1;check_show("result=-19",0);puts("unreadable queue refuses control-register access");
    stop();assert(removes==1 && !show_cb);puts("cleanup removes only the owned entry");
    fail_lookup=1;assert(start()==-19 && creates==1);fail_lookup=0;puts("wrong symbol identity refuses initialization");
    corrupt_code=1;assert(start()==-19 && creates==1);corrupt_code=0;puts("changed UART code refuses initialization");
    fail_code=1;assert(start()==-19 && creates==1);fail_code=0;puts("unreadable code refuses initialization");
    fail_create=1;assert(start()==-12 && creates==1);puts("proc creation failure propagates without an owned entry");
    puts("15 compiled-module checks passed; kernel APIs are fixtures and no A7 cost is measured");
    return 0;
}
