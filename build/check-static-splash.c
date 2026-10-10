/* QEMU only: execute the original bitmap-pointer and dimension stores against
 * anonymous RAM in place of display MMIO. No boot main, driver or real device.
 */
#define _GNU_SOURCE
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>

#define BIAS 0x025ffe00u
static uint32_t word(const void *p) { uint32_t v; memcpy(&v,p,4); return v; }
static uint16_t half(const void *p) { uint16_t v; memcpy(&v,p,2); return v; }
static void mapping(uint32_t address, size_t length)
{
    void *p=mmap((void *)(uintptr_t)address,length,PROT_READ|PROT_WRITE|PROT_EXEC,
                 MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
    assert(p==(void *)(uintptr_t)address);
}
__attribute__((naked,noinline)) static void fragment(void *entry __attribute__((unused)))
{
    /* This is a fragment of main, so explicitly retain its callee-saved state. */
    __asm__ volatile("push {r4-r11,lr}\n sub sp,sp,#4\n blx r0\n add sp,sp,#4\n pop {r4-r11,pc}\n");
}
int main(int argc,char **argv)
{
    assert(argc==2); FILE *f=fopen(argv[1],"rb"); assert(f);
    uint8_t *image=malloc(8388608); assert(image && fread(image,1,8388608,f)==8388608);
    assert(fgetc(f)==EOF && !fclose(f));
    assert(half(image+0x54c0)==0x4b58 && half(image+0x54c4)==0x4a58);
    assert(half(image+0x54ca)==0x601a && half(image+0x54f6)==0x601a);
    assert(word(image+0x5624)==0xd05001e0 && word(image+0x5628)==BIAS+0x8854);
    assert(word(image+0x5630)==0xd05002e4 && word(image+0x5634)==0x01e00280);
    mapping(0x02600000,0xc0000); memcpy((void *)0x02600000,image+0x200,0xbfe00);
    mapping(0xd0500000,0x1000);
    /* Stop only the RAM execution copies immediately after each target store. */
    *(uint16_t *)(uintptr_t)(BIAS+0x54cc)=0x4770;
    *(uint16_t *)(uintptr_t)(BIAS+0x54f8)=0x4770;
    __builtin___clear_cache((char *)0x02600000,(char *)0x026c0000);
    fragment((void *)(uintptr_t)(BIAS+0x54c0+1));
    fragment((void *)(uintptr_t)(BIAS+0x54ea+1));
    uint32_t pointer=*(volatile uint32_t *)0xd05001e0;
    uint32_t size=*(volatile uint32_t *)0xd05002e4;
    assert(pointer==BIAS+0x8854 && size==0x01e00280);
    assert(!memcmp((const void *)(uintptr_t)pointer,image+0x8854,614400));
    puts("PASS exact Thumb bitmap pointer/dimension stores and all 614400 referenced bytes; MMIO is RAM, boot ROM and panel not executed");
    free(image);return 0;
}
