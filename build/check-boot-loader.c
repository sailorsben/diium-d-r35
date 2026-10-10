/* Offline QEMU only: exact private Thumb parser/loader, intercepted SPI reads.
 * Never runs boot main or jumps into the kernel. No device nodes or MMIO.
 */
#define _GNU_SOURCE
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>

#define BASE 0x025ffe00u
static uint8_t *flash;
static size_t flash_bytes;
static unsigned calls;
static uint32_t addresses[4], lengths[4], destinations[4];

static void *at(uint32_t off) { return (void *)(uintptr_t)(BASE + off); }
static void *thumb(uint32_t off) { return (void *)(uintptr_t)((BASE + off) | 1u); }
static void mapping(uint32_t address, size_t bytes)
{
    void *p=mmap((void *)(uintptr_t)address,bytes,PROT_READ|PROT_WRITE|PROT_EXEC,
                 MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
    assert(p==(void *)(uintptr_t)address);
}
static uint32_t word(const void *p) { uint32_t v;memcpy(&v,p,4);return v; }
static uint32_t big(const void *p) { return __builtin_bswap32(word(p)); }
static uint32_t dt_property(const uint8_t *dt,const char *name)
{
    assert(big(dt)==0xd00dfeed);
    unsigned cursor=big(dt+8),end=cursor+big(dt+36),strings=big(dt+12);
    assert(end<=0x10000 && strings<0x10000);
    while(cursor+4<=end){
        uint32_t kind=big(dt+cursor);cursor+=4;
        if(kind==1){while(cursor<end && dt[cursor])cursor++;cursor=(cursor+4)&~3u;}
        else if(kind==3){
            assert(cursor+8<=end);unsigned bytes=big(dt+cursor),offset=big(dt+cursor+4);cursor+=8;
            assert(cursor+bytes<=end && strings+offset<0x10000);
            if(!strcmp((const char *)dt+strings+offset,name)){assert(bytes==4);return big(dt+cursor);}
            cursor=(cursor+bytes+3)&~3u;
        }else if(kind==9)break;
        else assert(kind==2 || kind==4);
    }
    assert(!"Missing device-tree property");return 0;
}
static void intercept(uint32_t off, void *callback)
{
    assert((off&3)==0);
    /* LDR.W pc,[pc,#0] preserves all four argument registers and interworks. */
    uint16_t instructions[]={0xf8df,0xf000};
    memcpy(at(off),instructions,4);
    uint32_t pointer=(uint32_t)(uintptr_t)callback;
    memcpy((uint8_t *)at(off)+4,&pointer,4);
    __builtin___clear_cache(at(off),(char *)at(off)+8);
}
static int quiet(const char *format,...){(void)format;return 0;}
static int read_flash(unsigned device,uint32_t address,void *dest,uint32_t bytes,unsigned width)
{
    (void)device;(void)width;
    assert(calls<4 && (uint64_t)address+bytes<=flash_bytes);
    uint32_t output=(uint32_t)(uintptr_t)dest;
    assert((output==0x02000000 && bytes<=0x400000) ||
           (output==0x00a00000 && bytes<=0x400000) ||
           (output==0x100 && bytes<=0x10000));
    addresses[calls]=address;lengths[calls]=bytes;destinations[calls]=output;calls++;
    memcpy(dest,flash+address,bytes);return 0;
}
static uint8_t *read_all(const char *path)
{
    FILE *f=fopen(path,"rb");assert(f);
    assert(!fseek(f,0,SEEK_END));long n=ftell(f);assert(n==8388608);rewind(f);
    uint8_t *data=malloc((size_t)n);assert(data && fread(data,1,n,f)==(size_t)n);
    assert(!fclose(f));flash_bytes=(size_t)n;return data;
}
int main(int argc,char **argv)
{
    assert(argc==2);flash=read_all(argv[1]);
    assert(!memcmp(flash,"PGpssiip",8));
    /* Entry pointers independently establish flash+0x200 -> RAM0x02600000. */
    assert(word(flash+0x220)==0x02600040 && word(flash+0x308)==0x026051ed);
    assert(word(flash+0x5628)==BASE+0x8854);
    assert(word(flash+0x64a8)==0x47f0e92d && word(flash+0x5a1c)==0x4ff0e92d);
    mapping(0x02600000,0xc0000);memcpy((void *)0x02600000,flash+0x200,0xbfe00);
    mapping(0x02800000,0x20000);
    mapping(0x02000000,0x400000);mapping(0x00a00000,0x400000);
    /* QEMU -B relocates guest address zero away from the host mmap_min_addr. */
    mapping(0,0x10000);
    intercept(0x4d3c,quiet);intercept(0x4408,read_flash);
    int (*parse)(void *,unsigned)=thumb(0x64a8);
    int (*get)(unsigned,unsigned *,uint32_t *,uint32_t *,uint32_t *)=thumb(0x6478);
    int (*pick)(void *,void *)=thumb(0x6e8c);
    int (*load)(unsigned,unsigned,uint32_t,uint32_t *)=thumb(0x5a1c);
    uint8_t header[512],backup[512];memcpy(header,flash+0xc0000,512);
    assert(parse(header,512)==1);
    for(unsigned i=0;i<3;i++){
        unsigned count=0;uint32_t off=0,size=0,address=0;
        assert(get(i,&count,&off,&size,&address)==0 && count==3);
        assert(off==word(header+i*36+24) && size==word(header+i*36+28));
        assert(address==word(header+i*36+32));
    }
    uint8_t bad[512];memcpy(bad,header,512);bad[8]='X';assert(parse(bad,512)==0);
    memcpy(bad,header,512);bad[44]='X';assert(parse(bad,512)==0);
    memcpy(bad,header,512);bad[80]='X';assert(parse(bad,512)==0);
    memcpy(bad,header,512);bad[4]=27;assert(parse(bad,512)==0);
    assert(parse(header,512)==1);
    memcpy(header,flash+0xb0000,512);memcpy(backup,flash+0xb1000,512);
    assert(pick(header,backup)==1);
    memcpy(backup,header,512);backup[7]=1;assert(pick(header,backup)==2);
    header[0]='X';backup[0]='X';assert(pick(header,backup)==0);
    assert(parse(flash+0xc0000,512)==1);
    uint32_t entry=0;assert(load(0,0,0xc0000,&entry)==0 && entry==0x02000000);
    assert(calls==3);
    for(unsigned i=0;i<3;i++){
        assert(addresses[i]==0xc0000+word(flash+0xc0000+i*36+24));
        assert(lengths[i]==word(flash+0xc0000+i*36+28));
        if(i<2)assert(!memcmp((void *)(uintptr_t)destinations[i],flash+addresses[i],lengths[i]));
    }
    uint8_t *tree=calloc(1,65536);assert(tree);
    memcpy(tree,(void *)(uintptr_t)destinations[2],65536-destinations[2]);
    assert(dt_property(tree,"linux,initrd-start")==0xa00000);
    assert(dt_property(tree,"linux,initrd-end")==0xa00000+lengths[1]);
    printf("PASS exact Thumb table parser/getter, GPAP selection, three-section load and DT initrd bounds with intercepted SPI; kernel not executed\n");
    printf("reads=%u kernel=%08x/%u rootfs=%08x/%u dt=%08x/%u entry=%08x\n",
           calls,addresses[0],lengths[0],addresses[1],lengths[1],addresses[2],lengths[2],entry);
    return 0;
}
