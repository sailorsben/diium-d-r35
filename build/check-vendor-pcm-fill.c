/* Execute preserved ARM vendor instructions with RAM-only dependencies.
 * The IRQ/DMA/hardware DROP side effects are deliberately intercepted. */
#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>

enum {BASE=0xc0008000, FILL=0xc03e25e8, KERNEL_IOCTL=0xc03bdda0,
      DROP=0xc03bceb4, HWSYNC=0xc03bb374, CLOCK=0xc016c91c,
      LOCK=0xc0453154, UNLOCK=0xc0452cb8, COPY=0xc043b9c0,
      FILL_EPOCH=0xc074f678, PERIOD=128, BUFFER=3712, FRAME_BYTES=4};
static uint32_t sub[64],runtime[256],status[8],control[8];
static uint8_t ring[BUFFER*FRAME_BYTES];
static int64_t ns;
static unsigned copies,drops,locks,unlocks;
static uint8_t *expect_dest,*expect_source;

static void clock_stub(int64_t *t) {t[0]=ns/1000000000;t[1]=ns%1000000000;}
static int drop_stub(void *s) {
    assert(s==sub && status[0]==3); ++drops; status[0]=1; return 0;
}
static void lock_stub(void *m) {assert(m==(char *)runtime+640); ++locks;}
static void unlock_stub(void *m) {assert(m==(char *)runtime+640); ++unlocks;}
static void *copy_stub(void *dest,const void *src,size_t bytes) {
    assert(dest==expect_dest && src==expect_source && bytes==PERIOD*FRAME_BYTES);
    ++copies; return memcpy(dest,src,bytes);
}
static void patch(uint32_t at,void *handler) {
    uint32_t *p=(void *)(uintptr_t)at;
    p[0]=0xe51ff004; p[1]=(uintptr_t)handler;
    __builtin___clear_cache((void *)p,(void *)(p+2));
}

int main(int argc,char **argv) {
    assert(argc==2);
    void *code=mmap((void *)BASE,0x500000,PROT_READ|PROT_WRITE|PROT_EXEC,
                    MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
    assert(code==(void *)BASE);
    void *data=mmap((void *)0xc05d0000,0x190000,PROT_READ|PROT_WRITE,
                    MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
    assert(data==(void *)0xc05d0000);
    FILE *f=fopen(argv[1],"rb"); assert(f);
    assert(fread(code,1,0x500000,f)==0x500000 && !fclose(f));
    patch(CLOCK,clock_stub); patch(COPY,copy_stub); patch(DROP,drop_stub);
    patch(LOCK,lock_stub);patch(UNLOCK,unlock_stub);
    int (*fill)(void *,int,unsigned,unsigned)=(void *)FILL;
    int (*hwsync)(void *)=(void *)HWSYNC;
    uint32_t *epoch=(void *)FILL_EPOCH;
    sub[0x9c/4]=(uintptr_t)runtime;
    runtime[0x4c/4]=PERIOD;runtime[0x54/4]=BUFFER;runtime[0x60/4]=FRAME_BYTES*8;
    runtime[0x90/4]=1u<<29;runtime[0xac/4]=(uintptr_t)status;
    runtime[0xb0/4]=(uintptr_t)control;runtime[0x21c/4]=(uintptr_t)ring;
    status[0]=3;control[0]=5030;
    ns=3000000000;
    for(unsigned j=0;j<PERIOD*FRAME_BYTES;j++) ring[(BUFFER-PERIOD)*FRAME_BYTES+j]=(uint8_t)(j*71+9);
    for(unsigned i=0;i<4;i++) {
        expect_dest=ring+i*PERIOD*FRAME_BYTES;
        expect_source=i?expect_dest-PERIOD*FRAME_BYTES:ring+(BUFFER-PERIOD)*FRAME_BYTES;
        assert(!fill(sub,-1,(uintptr_t)(expect_dest-ring),PERIOD*FRAME_BYTES));
        ns+=3000000;
        assert(control[0]==5030+PERIOD*(i<3?i+1:3));
        if(i<3) assert(!memcmp(expect_dest,expect_source,PERIOD*FRAME_BYTES));
    }
    assert(epoch[2]==4 && copies==3 && drops==1 && locks==1 && unlocks==1);
    assert(status[0]==1 && hwsync(sub)==-EBADFD && control[0]==5414);
    /* Confirm reset of the fill counter and pointer wrap without new DROP. */
    ns+=501000000;status[0]=3;control[0]=runtime[0x90/4]-64;
    expect_dest=ring;expect_source=ring+(BUFFER-PERIOD)*FRAME_BYTES;
    assert(!fill(sub,-1,0,PERIOD*FRAME_BYTES));
    assert(epoch[2]==1 && copies==4 && drops==1 && status[0]==3 && control[0]==64);
    puts("PASS exact ARM vendor fill and ioctl dispatch: three previous-period copies, appl_ptr 5030 -> 5414, fourth DROP request; exact SETUP HWSYNC -77, timed reset and boundary wrap");
    return 0;
}
