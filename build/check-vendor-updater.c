/* Offline QEMU only. Invoke exact UpdateROM/UpdateROMProc, with every device,
 * display, chunk allocation, erase/program and process-control seam intercepted.
 * Flash operations affect a malloc buffer only. Unexpected imports abort.
 * Never runs vendor main; never distributes vendor code or stages an SD update.
 */
#define _GNU_SOURCE
#include <assert.h>
#include <dlfcn.h>
#include <elf.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <signal.h>
#include <unistd.h>
#include <ucontext.h>

#define CAPACITY 8388608u
static uint8_t *flash,*expected;
static unsigned reads,erases,pages,updates,configs,program_mode;
static unsigned erased[128];
static uint32_t crc_metadata,date_metadata;
static int (*real_program)(void *,unsigned);
static void expected_fault(int signal,siginfo_t *info,void *context)
{
    (void)signal;
    const ucontext_t *state=context;
    if((uintptr_t)info->si_addr==0x108 && state->uc_mcontext.arm_pc==0x13920 &&
       !updates && !erases && !pages && configs==6){
        const char message[]="OBSERVED vendor fault at 0x13920: NULL image+0x108; configuration_calls=6 erase/program_calls=0\n";
        if(write(1,message,sizeof(message)-1)<0)_exit(91);
        _exit(89);
    }
    _exit(90);
}
static void forbidden(void){fputs("Unexpected vendor import/hardware seam\n",stderr);abort();}
static int quiet(const char *s,...){(void)s;return 0;}
static int character(int c){return c;}
static int fake_open(const char *path,int flags,...)
{assert(!strcmp(path,"/dev/spidev0.0") && flags==2);return 777;}
static int fake_close(int fd){assert(fd==777);return 0;}
static int fake_ioctl(int fd,unsigned request,void *arg)
{
    assert(fd==777 && arg);
    assert(request==0x40046b05 || request==0x80046b05 ||
           request==0x40016b03 || request==0x80016b03 ||
           request==0x40046b04 || request==0x80046b04);
    configs++;return 0;
}
static int flash_read(unsigned address,void *dest,unsigned length)
{assert((uint64_t)address+length<=CAPACITY);memcpy(dest,flash+address,length);reads++;return 0;}
static int flash_erase(unsigned address)
{
    assert(program_mode && !(address&0xffff) && address<CAPACITY);
    memset(flash+address,0xff,65536);erased[address>>16]++;erases++;return 0;
}
static int flash_page(unsigned address,const void *data,unsigned length)
{
    assert(program_mode && !(address&255) && length==256 && address+length<=CAPACITY);
    const uint8_t *bytes=data;
    for(unsigned i=0;i<length;i++) {assert((flash[address+i]&bytes[i])==bytes[i]);flash[address+i]=bytes[i];}
    pages++;return 0;
}
static void frame(void *p,unsigned w,unsigned h,unsigned stride)
{(void)p;(void)w;(void)h;(void)stride;}
static int capture(void *image,unsigned bytes)
{
    assert(bytes==CAPACITY && !program_mode);updates++;
    uint8_t *data=image;
    memcpy(&crc_metadata,data+0x100,4);memcpy(&date_metadata,data+0x104,4);
    assert(crc_metadata && date_metadata);
    assert(!memcmp(data,expected,0x100) && !memcmp(data+0x108,expected+0x108,CAPACITY-0x108));
    /* Exercise the unmodified programming algorithm against RAM flash only. */
    program_mode=1;assert(real_program(image,bytes)==1);program_mode=0;
    assert(!memcmp(flash,data,CAPACITY));
    return 0; /* Deliberate failure prevents the vendor sync/reboot success path. */
}
static void patch(uint32_t address,void *callback)
{
    uint32_t instruction=0xe51ff004; /* ARM ldr pc,[pc,#-4], preserving all arguments */
    memcpy((void *)(uintptr_t)address,&instruction,4);
    uint32_t pointer=(uint32_t)(uintptr_t)callback;
    memcpy((void *)(uintptr_t)(address+4),&pointer,4);
    __builtin___clear_cache((void *)(uintptr_t)address,(void *)(uintptr_t)(address+8));
}
static uint8_t *read_all(const char *path,size_t *size)
{
    FILE *f=fopen(path,"rb");assert(f && !fseek(f,0,SEEK_END));
    long n=ftell(f);assert(n>0);rewind(f);uint8_t *data=malloc((size_t)n);
    assert(data && fread(data,1,(size_t)n,f)==(size_t)n && !fclose(f));*size=(size_t)n;return data;
}
static uintptr_t symbol(const uint8_t *file,const char *name)
{
    const Elf32_Ehdr *h=(const void *)file;const Elf32_Shdr *s=(const void *)(file+h->e_shoff);
    for(unsigned i=0;i<h->e_shnum;i++)if(s[i].sh_type==SHT_SYMTAB){
        const Elf32_Sym *symbols=(const void *)(file+s[i].sh_offset);
        const char *strings=(const void *)(file+s[s[i].sh_link].sh_offset);
        for(unsigned j=0;j<s[i].sh_size/sizeof(*symbols);j++)
            if(!strcmp(strings+symbols[j].st_name,name))return symbols[j].st_value;
    }
    forbidden();return 0;
}
static void *import(const char *name)
{
    if(!strcmp(name,"__gmon_start__"))return NULL;
    if(!strcmp(name,"open"))return fake_open;
    if(!strcmp(name,"close"))return fake_close;
    if(!strcmp(name,"ioctl"))return fake_ioctl;
    if(!strcmp(name,"printf") || !strcmp(name,"puts"))return quiet;
    if(!strcmp(name,"putchar"))return character;
    const char *allowed[]={"malloc","calloc","realloc","free","memcpy","memmove",
        "memset","memcmp","memchr","strlen","strcpy","strncpy","strcmp","strncmp",
        "strcat","strrchr","strchr","strstr","strdup","stpcpy","sprintf","vsnprintf",
        "fopen","fclose","fread","fseek","ftell","rewind","fileno","__xstat",
        "__errno_location","strerror","__ctype_b_loc","__ctype_toupper_loc","__ctype_tolower_loc",
        "gettimeofday","stderr"};
    for(unsigned i=0;i<sizeof(allowed)/sizeof(*allowed);i++)if(!strcmp(name,allowed[i])){
        void *p=dlsym(RTLD_DEFAULT,name);assert(p);return p;
    }
    return forbidden;
}
int main(int argc,char **argv)
{
    assert(argc==6);size_t size,n;uint8_t *file=read_all(argv[1],&size);
    flash=read_all(argv[2],&n);assert(n==CAPACITY);expected=read_all(argv[3],&n);assert(n==CAPACITY);
    unsigned want=(unsigned)strtoul(argv[5],NULL,10);assert(want<=2);
    if(want==2){struct sigaction action={0};action.sa_sigaction=expected_fault;
        action.sa_flags=SA_SIGINFO;assert(!sigaction(SIGSEGV,&action,NULL));}
    const Elf32_Ehdr *h=(const void *)file;
    assert(size==1660140 && !memcmp(h->e_ident,ELFMAG,4) && h->e_machine==EM_ARM && h->e_type==ET_EXEC);
    void *mapped=mmap((void *)0x10000,0x200000,PROT_READ|PROT_WRITE|PROT_EXEC,
                     MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);assert(mapped==(void *)0x10000);
    const Elf32_Phdr *ph=(const void *)(file+h->e_phoff);
    for(unsigned i=0;i<h->e_phnum;i++)if(ph[i].p_type==PT_LOAD){
        assert(ph[i].p_vaddr>=0x10000 && ph[i].p_vaddr+ph[i].p_memsz<=0x210000);
        assert(ph[i].p_offset+ph[i].p_filesz<=size);
        memcpy((void *)(uintptr_t)ph[i].p_vaddr,file+ph[i].p_offset,ph[i].p_filesz);
    }
    const Elf32_Shdr *sh=(const void *)(file+h->e_shoff);
    for(unsigned i=0;i<h->e_shnum;i++)if(sh[i].sh_type==SHT_REL){
        const Elf32_Rel *r=(const void *)(file+sh[i].sh_offset);
        const Elf32_Shdr *st=&sh[sh[i].sh_link];const Elf32_Sym *sy=(const void *)(file+st->sh_offset);
        const char *strings=(const void *)(file+sh[st->sh_link].sh_offset);
        for(unsigned j=0;j<sh[i].sh_size/sizeof(*r);j++){
            unsigned type=ELF32_R_TYPE(r[j].r_info);const Elf32_Sym *s=&sy[ELF32_R_SYM(r[j].r_info)];
            const char *name=strings+s->st_name;void *value=import(name);
            assert(r[j].r_offset>=0x10000 && r[j].r_offset+4<=0x210000);
            if(type==R_ARM_COPY){assert(!strcmp(name,"stderr") && s->st_size==4);memcpy((void *)(uintptr_t)r[j].r_offset,value,4);}
            else {assert(type==R_ARM_GLOB_DAT || type==R_ARM_JUMP_SLOT);*(uintptr_t *)(uintptr_t)r[j].r_offset=(uintptr_t)value;}
        }
    }
    assert(symbol(file,"UpdateROM")==0x133fc && symbol(file,"UpdateROMProc")==0x130a0);
    real_program=(void *)symbol(file,"UpdateROMProc");
    /* Replace the CALL to UpdateROMProc with a branch to our capture trampoline,
     * leaving the original function intact for the RAM-only programming test. */
    uintptr_t trampoline=0x200000;patch(trampoline,capture);
    int32_t displacement=(int32_t)trampoline-(0x13950+8);assert(!(displacement&3));
    *(uint32_t *)0x13950=0xeb000000|(((uint32_t)(displacement>>2))&0xffffff);
    patch(symbol(file,"spi_read"),flash_read);patch(symbol(file,"erase_sector"),flash_erase);
    patch(symbol(file,"spi_write"),flash_page);patch(symbol(file,"spi_printf"),quiet);
    patch(symbol(file,"DispFrame"),frame);patch(symbol(file,"gpChunkMemAlloc"),malloc);
    patch(symbol(file,"gpChunkMemFree"),free);
    __builtin___clear_cache((void *)0x10000,(void *)0x210000);
    /* UpdateROM has no stable status return; observe the actual program seam. */
    void (*update)(const char *)=(void *)symbol(file,"UpdateROM");
    update(argv[4]);assert(updates==want && configs==6);
    if(want){assert(erases && pages==erases*256 && erased[0]==1);}
    else assert(!erases && !pages);
    printf("PASS updater container/validation and RAM-only programming: accepted=%u config_calls=%u reads=%u erases=%u pages=%u metadata=%08x/%08x\n",
           updates,configs,reads,erases,pages,crc_metadata,date_metadata);
    printf("erased_blocks=");for(unsigned i=0;i<128;i++)if(erased[i])printf("%s%06x",i?",":"",i*65536);puts("");
    return 0;
}
