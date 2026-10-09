/* Offline only: invoke the exact returned ARM ZIP loader and ShowSprite.
 * This is not a replacement implementation of either seam. Never runs main,
 * opens device nodes, or calls initialization/flip/cleanup. No vendor code is
 * distributed; load the owner's hash-qualified ELF locally under QEMU. */
#define _GNU_SOURCE
#include <assert.h>
#include <dlfcn.h>
#include <elf.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>

static uint8_t *read_all(const char *path,size_t *size)
{
    FILE *f=fopen(path,"rb"); assert(f); assert(!fseek(f,0,SEEK_END));
    long n=ftell(f); assert(n>0); rewind(f); uint8_t *p=malloc((size_t)n);
    assert(p && fread(p,1,(size_t)n,f)==(size_t)n && !fclose(f)); *size=(size_t)n;return p;
}
static Elf32_Sym *find(const uint8_t *file,const char *name)
{
    const Elf32_Ehdr *h=(const void *)file;
    const Elf32_Shdr *sections=(const void *)(file+h->e_shoff);
    for(unsigned i=0;i<h->e_shnum;i++) if(sections[i].sh_type==SHT_SYMTAB) {
        const Elf32_Sym *symbols=(const void *)(file+sections[i].sh_offset);
        const char *strings=(const void *)(file+sections[sections[i].sh_link].sh_offset);
        for(unsigned j=0;j<sections[i].sh_size/sizeof(*symbols);j++)
            if(!strcmp(strings+symbols[j].st_name,name)) return (Elf32_Sym *)&symbols[j];
    }
    fprintf(stderr,"Missing stock symbol: %s\n",name); assert(!"Missing stock symbol"); return NULL;
}
int main(int argc,char **argv)
{
    assert(argc==3);size_t size,raw_size; uint8_t *file=read_all(argv[1],&size);
    uint8_t *expected=read_all(argv[2],&raw_size);
    const Elf32_Ehdr *h=(const void *)file;
    assert(!memcmp(h->e_ident,ELFMAG,4) && h->e_machine==EM_ARM && h->e_type==ET_EXEC);
    assert(h->e_phoff+h->e_phnum*sizeof(Elf32_Phdr)<=size);
    void *mapped=mmap((void *)0x10000,0x40000,PROT_READ|PROT_WRITE|PROT_EXEC,
                     MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
    assert(mapped==(void *)0x10000);
    const Elf32_Phdr *ph=(const void *)(file+h->e_phoff);
    for(unsigned i=0;i<h->e_phnum;i++) if(ph[i].p_type==PT_LOAD) {
        assert(ph[i].p_vaddr>=0x10000 && ph[i].p_vaddr+ph[i].p_memsz<=0x50000);
        assert(ph[i].p_offset+ph[i].p_filesz<=size);
        memcpy((void *)(uintptr_t)ph[i].p_vaddr,file+ph[i].p_offset,ph[i].p_filesz);
    }
    const Elf32_Shdr *sh=(const void *)(file+h->e_shoff);
    for(unsigned i=0;i<h->e_shnum;i++) if(sh[i].sh_type==SHT_REL) {
        const Elf32_Rel *rel=(const void *)(file+sh[i].sh_offset);
        const Elf32_Shdr *symtab=&sh[sh[i].sh_link];
        const Elf32_Sym *symbols=(const void *)(file+symtab->sh_offset);
        const char *strings=(const void *)(file+sh[symtab->sh_link].sh_offset);
        for(unsigned j=0;j<sh[i].sh_size/sizeof(*rel);j++) {
            unsigned type=ELF32_R_TYPE(rel[j].r_info);assert(type==R_ARM_GLOB_DAT || type==R_ARM_JUMP_SLOT);
            const Elf32_Sym *s=&symbols[ELF32_R_SYM(rel[j].r_info)];const char *name=strings+s->st_name;
            void *value=dlsym(RTLD_DEFAULT,name);assert(value || !strcmp(name,"__gmon_start__"));
            assert(rel[j].r_offset>=0x10000 && rel[j].r_offset<0x50000);
            *(uintptr_t *)(uintptr_t)rel[j].r_offset=(uintptr_t)value;
        }
    }
    void *(*open_zip)(void *,unsigned,unsigned)=(void *)(uintptr_t)find(file,"OpenZipU")->st_value;
    unsigned (*unzip)(void *,int,void *,unsigned,unsigned)=(void *)(uintptr_t)find(file,"UnzipItem")->st_value;
    unsigned (*close_zip)(void *)=(void *)(uintptr_t)find(file,"CloseZipU")->st_value;
    void (*show)(int)=(void *)(uintptr_t)find(file,"ShowSprite")->st_value;
    uintptr_t start=find(file,"__LogoData")->st_value,end=find(file,"__LogoDataEnd")->st_value;
    assert(start==0x17180 && end==0x39bf4);
    uint8_t *decoded=malloc(raw_size+32);assert(decoded);memset(decoded,0xa5,raw_size+32);
    void *zip=open_zip((void *)start,(unsigned)(end-start),3);assert(zip);
    assert(unzip(zip,0,decoded+16,0,3)==0 && close_zip(zip)==0);
    assert(!memcmp(decoded+16,expected,raw_size));
    for(unsigned i=0;i<16;i++)assert(decoded[i]==0xa5 && decoded[raw_size+16+i]==0xa5);
    uint8_t display[108]={0}; *(uint16_t *)(display+8)=640;*(uint16_t *)(display+10)=480;
    uint8_t *fb=malloc(640*480*2+32),*reference=malloc(640*480*2);assert(fb && reference);
    *(uintptr_t *)(display+24)=(uintptr_t)(fb+16);
    *(uintptr_t *)(uintptr_t)find(file,"main_hDisp")->st_value=(uintptr_t)display;
    *(uintptr_t *)(uintptr_t)find(file,"menu_pic")->st_value=(uintptr_t)(decoded+16);
    for(unsigned frame=0;frame<18;frame++) {
        memset(fb,0xa5,640*480*2+32);memset(reference,0xa5,640*480*2);
        for(unsigned which=0;which<2;which++) {
            uint8_t *record=expected+(which?frame+1:0)*16;
            unsigned offset=*(uint32_t *)record;uint16_t *rect=(void *)(record+8);
            assert(rect[0]<rect[2] && rect[1]<rect[3] && rect[2]<=640 && rect[3]<=480);
            for(unsigned y=rect[1];y<rect[3];y++)
                memcpy(reference+(y*640+rect[0])*2,expected+offset+(y-rect[1])*(rect[2]-rect[0])*2,
                       (rect[2]-rect[0])*2);
        }
        show((int)frame);assert(!memcmp(fb+16,reference,640*480*2));
        for(unsigned i=0;i<16;i++)assert(fb[i]==0xa5 && fb[640*480*2+16+i]==0xa5);
    }
    puts("PASS exact stock OpenZipU/UnzipItem decode, 18 ShowSprite frames, pixel equality and buffer canaries; no hardware calls");
    return 0;
}
