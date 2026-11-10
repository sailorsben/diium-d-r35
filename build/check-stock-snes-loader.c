/* Execute the pinned vendor's selector and SNES loader without its device or UI. */
#define _GNU_SOURCE
#include <assert.h>
#include <elf.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>

enum { INIT_CORE_SETTING=0xa5ab4, GET_CORE_INDEX=0xa5b28, SNES_LOAD=0xa4f54,
       LOAD_PROC2=0xa426c, KEY_MAPPING=0x892c4, FRAME_FLASH=0x12638,
       ENVIRONMENT=0xa2fc8, GOT=0x199000 };
struct game_info { const char *path; const uint8_t *data; size_t size; const char *meta; };
static const uint8_t fixture[] = {0x80, 0, 0xea, 0xff, 0x42};
static const char *names[8];
static unsigned opens, lookups, loads, gameplay, mapping;
static size_t expected_size;
static int reject_rom, hide_load;

static void patch(uintptr_t address, uintptr_t target)
{
    uint32_t *instruction=(uint32_t *)address;
    instruction[0]=0xe51ff004; /* ldr pc,[pc,#-4] */
    instruction[1]=target;
    __builtin___clear_cache((char *)address,(char *)address+8);
}

static void map_vendor(const char *path)
{
    FILE *file=fopen(path,"rb");
    Elf32_Ehdr header;
    assert(file && fread(&header,sizeof(header),1,file)==1);
    assert(!memcmp(header.e_ident,ELFMAG,SELFMAG) && header.e_machine==EM_ARM);
    assert(header.e_type==ET_EXEC && header.e_ident[EI_CLASS]==ELFCLASS32);
    assert(header.e_phnum==9 && header.e_phentsize==sizeof(Elf32_Phdr));
    Elf32_Phdr segments[9];
    assert(!fseek(file,header.e_phoff,SEEK_SET) && fread(segments,sizeof(segments),1,file)==1);
    for (unsigned i=0;i<9;++i) {
        const Elf32_Phdr *p=&segments[i];
        if(p->p_type!=PT_LOAD)continue;
        uintptr_t start=p->p_vaddr&~4095u;
        size_t bytes=((p->p_vaddr-start+p->p_memsz)+4095u)&~4095u;
        assert(mmap((void *)start,bytes,PROT_READ|PROT_WRITE|PROT_EXEC,
                    MAP_FIXED_NOREPLACE|MAP_PRIVATE|MAP_ANONYMOUS,-1,0)==(void *)start);
        assert(!fseek(file,p->p_offset,SEEK_SET));
        assert(fread((void *)p->p_vaddr,1,p->p_filesz,file)==p->p_filesz);
    }
    assert(!fclose(file));
}

static void frame_flash(void) {}
static void key_mapping(void) { ++mapping; }
static void enter_gameplay(void) { ++gameplay; }
static void callback(void) {}
static int quiet(const char *format, ...) { (void)format; return 0; }
static FILE *open_rom(const char *path,const char *mode)
{
    assert(!strcmp(path,"/usr/002/fixture.sfc") && !strcmp(mode,"rb"));
    FILE *file=tmpfile();
    assert(file && fwrite(fixture,sizeof(fixture),1,file)==1);
    rewind(file);
    return file;
}

static void *open_core(const char *path,int mode)
{
    assert(!strcmp(path,"/usr/retro/libs/emu_sfc.so") && mode==2);
    ++opens;
    return (void *)1;
}

static int load_game(const struct game_info *game)
{
    assert(!strcmp(game->path,"/usr/002/fixture.sfc"));
    assert(game->size==expected_size && !memcmp(game->data,fixture,sizeof(fixture)));
    ++loads;
    return !reject_rom;
}

static uintptr_t resolve(void *handle,const char *name)
{
    assert(handle==(void *)1 && lookups<sizeof(names)/sizeof(*names));
    names[lookups++]=name;
    if(!strcmp(name,"retro_load_game"))
        return hide_load?0:(uintptr_t)load_game;
    return (uintptr_t)callback;
}

static void launch(unsigned type,size_t bytes,int rejected,int missing)
{
    opens=lookups=loads=gameplay=mapping=0;
    expected_size=bytes;
    reject_rom=rejected;
    hide_load=missing;
    *(unsigned *)*(uint32_t *)(GOT+0x250)=0; /* handle */
    if(type>=65536) {
        void *memory=malloc(sizeof(fixture));
        assert(memory);
        memcpy(memory,fixture,sizeof(fixture));
        *(void **)*(uint32_t *)(GOT+0x448)=memory;
        *(size_t *)*(uint32_t *)(GOT+0x470)=sizeof(fixture);
    }
    int (*load)(const char *,unsigned)=(void *)SNES_LOAD;
    load("/usr/002/fixture.sfc",type);
    const char *expected[]={"retro_set_video_refresh","retro_set_audio_sample_batch",
        "retro_set_input_state","retro_set_environment","retro_set_input_poll","retro_init",
        "retro_load_game"};
    assert(opens==1 && mapping==1 && lookups==sizeof(expected)/sizeof(*expected));
    for(unsigned i=0;i<lookups;++i)assert(!strcmp(names[i],expected[i]));
    assert(loads==!missing && gameplay==!missing);
}

int main(int argc,char **argv)
{
    assert(argc==2);
    map_vendor(argv[1]);
    patch(FRAME_FLASH,(uintptr_t)frame_flash);
    patch(KEY_MAPPING,(uintptr_t)key_mapping);
    patch(LOAD_PROC2,(uintptr_t)enter_gameplay);
    patch(0x11be4,(uintptr_t)quiet);    /* printf */
    patch(0x11d34,(uintptr_t)open_core);
    patch(0x12010,(uintptr_t)resolve);
    patch(0x11ce0,(uintptr_t)open_rom);
    patch(0x11d64,(uintptr_t)strcpy);
    patch(0x11bfc,(uintptr_t)stpcpy);
    patch(0x11f74,(uintptr_t)strcmp);
    patch(0x11b84,(uintptr_t)fseek);
    patch(0x11e84,(uintptr_t)ftell);
    patch(0x11ed8,(uintptr_t)malloc);
    patch(0x11ddc,(uintptr_t)fread);
    patch(0x11f20,(uintptr_t)fclose);
    patch(0x11b6c,(uintptr_t)free);
    strcpy((char *)*(uint32_t *)(GOT+0x274),"/usr/");
    ((void (*)(void))INIT_CORE_SETTING)();
    int (*select_core)(const char *)=(void *)GET_CORE_INDEX;
    assert(select_core("SMC")==2 && select_core("FIG")==3 && select_core("SFC")==4);
    assert(select_core("NES")==5 && select_core("ZIP")==1 && select_core("D35_TEST")==-1);
    launch(4,8,0,0);                         /* raw file rounds five bytes up to eight */
    launch(0x10004,sizeof(fixture),0,0);      /* upstream-decoded archive payload */
    launch(4,8,1,0);                         /* false callback still enters Load_Proc2 */
    launch(4,8,0,1);                         /* missing symbol never enters Load_Proc2 */
    _Alignas(8) uint8_t guarded_geometry[48];
    memset(guarded_geometry,0xa5,sizeof(guarded_geometry));
    int (*environment)(unsigned,void *)=(void *)ENVIRONMENT;
    assert(environment(37,guarded_geometry)==1);
    double rate;
    memcpy(&rate,guarded_geometry+32,sizeof(rate));
    assert(rate==44100);
    for(unsigned i=0;i<sizeof(guarded_geometry);++i)
        if(i<32 || i>=40)assert(guarded_geometry[i]==0xa5);
    puts("PASS exact vendor selector, SNES path, callback order, raw and archive handoffs, failure behavior and geometry write");
    return 0;
}
