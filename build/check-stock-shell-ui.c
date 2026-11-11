/* Execute the pinned search worker and the patched artwork load call sites. */
#define main stock_audit_main
#include "check-stock-snes-loader.c"
#undef main
#include <unistd.h>

enum {
    LANGUAGE=0x1998d8, SEARCH_FLAGS=0x19bab8, SEARCH_QUERY=0x19bab4,
    SEARCH_INDEX=0x199920, SEARCH_RESULTS=0x199930, SEARCH_COUNT=0x199ee4,
    SEARCH_PAGE_OFFSET=0x19bc14, SEARCH_PAGE_SIZE=0x199a14,
    SEARCH_LIST=0x1aded8, SEARCH_THREAD=0x832bc, RESOURCE_SIZE=0x19bc0c
};

static unsigned clock_reads;
static int ticks(void)
{
    if(++clock_reads==2) *(unsigned *)SEARCH_FLAGS &= ~1u;
    return (int)clock_reads;
}

static unsigned self(void) { return 1; }
static int detach(unsigned thread) { assert(thread==1); return 0; }
static unsigned favorites(const char *name) { (void)name; return 0; }

static void verify_search(const char *index, char *query, unsigned offset,
                          unsigned page_size, unsigned count, const char *first)
{
    char output[8192];
    static uint8_t english[80];
    memset(output,0xcc,sizeof(output));
    *(unsigned *)LANGUAGE=1;
    *(void **)(LANGUAGE+25*4)=english; /* English gamelist mode 0 */
    *(const char **)SEARCH_INDEX=index;
    *(char **)SEARCH_RESULTS=output;
    *(char ***)SEARCH_QUERY=&query;
    *(unsigned *)SEARCH_PAGE_OFFSET=offset;
    *(unsigned *)SEARCH_PAGE_SIZE=page_size;
    *(unsigned *)SEARCH_FLAGS=3;
    clock_reads=0;
    ((void (*)(void))SEARCH_THREAD)();
    assert(clock_reads==2 && *(unsigned *)SEARCH_FLAGS==0);
    assert(*(unsigned *)SEARCH_COUNT==count);
    if(first) assert(!strcmp((const char *)SEARCH_LIST,first));
    else assert(!*(const char *)SEARCH_LIST);
}

static const char *art_dir;
static unsigned char *read_art(const char *member, size_t *size)
{
    char path[1024];
    int n=snprintf(path,sizeof(path),"%s/%s",art_dir,member);
    assert(n>0 && (size_t)n<sizeof(path));
    FILE *file=fopen(path,"rb");
    assert(file && !fseek(file,0,SEEK_END));
    long len=ftell(file);
    assert(len>0 && !fseek(file,0,SEEK_SET));
    unsigned char *p=malloc((size_t)len);
    assert(p && fread(p,1,(size_t)len,file)==(size_t)len && !fclose(file));
    *size=(size_t)len;
    return p;
}

static int load_art(void **buffer, const char *member)
{
    size_t size;
    free(*buffer);
    *buffer=read_art(member,&size);
    *(unsigned *)RESOURCE_SIZE=(unsigned)size;
    return 1;
}

static uintptr_t branch_target(uintptr_t pc)
{
    return pc+8+((int32_t)(*(uint32_t *)pc<<8)>>6);
}

static void verify_art(uintptr_t call, const char *member, unsigned index,
                       unsigned x, unsigned y, unsigned right, unsigned bottom)
{
    size_t size;
    unsigned char *reference=read_art(member,&size);
    void *rendered=NULL;
    int (*load)(void **,const char *)=(void *)branch_target(call);
    assert(load(&rendered,member)==1);
    assert(*(unsigned *)RESOURCE_SIZE==size);
    const unsigned char *pixels=rendered;
    size_t offset=((const uint32_t *)reference)[index*4];
    unsigned changes=0;
    for(size_t i=0;i<size;++i) {
        if(reference[i]==pixels[i]) continue;
        assert(i>=offset && i<offset+640u*480u*2u);
        size_t p=(i-offset)/2u;
        assert(p%640u>=x && p%640u<right && p/640u>=y && p/640u<bottom);
        ++changes;
    }
    assert(changes>80);
    char output[1024];
    int n=snprintf(output,sizeof(output),"%s/verified-%s",art_dir,member);
    assert(n>0 && (size_t)n<sizeof(output));
    FILE *file=fopen(output,"wb");
    assert(file && fwrite(pixels,1,size,file)==size && !fclose(file));
    free(rendered);
    free(reference);
}

static void verify_pack(const char *path)
{
    void *(*open_zip)(const char *, unsigned, unsigned)=(void *)0xa2730;
    unsigned (*find_item)(void *, const char *, int, int *, void *)=(void *)0xa29b8;
    unsigned (*extract)(void *, int, void *, size_t, unsigned)=(void *)0xa2b5c;
    unsigned (*close_zip)(void *)=(void *)0xa2bec;
    void *zip=open_zip(path,0,2);
    assert(zip);
    const char *members[]={"game.raw","menu.raw","search.raw","setting.raw","type.raw",
                          "img_filetype0.raw","img_filetype6.raw","img_language1.raw",
                          "img_language2.raw","img_language3.raw","ui.cfg"};
    for(unsigned i=0;i<sizeof(members)/sizeof(*members);++i) {
        size_t size;
        void *expected=read_art(members[i],&size), *pixels=malloc(size);
        uint32_t metadata[256]={0};
        int index=-1;
        assert(pixels && !find_item(zip,members[i],1,&index,metadata) && index>=0);
        assert(!extract(zip,index,pixels,size,3));
        assert(!memcmp(expected,pixels,size));
        free(pixels);
        free(expected);
    }
    assert(!close_zip(zip));
}

static void verify_refreshed_art(uintptr_t call, const char *member)
{
    size_t size;
    void *reference=read_art(member,&size), *rendered=NULL;
    int (*load)(void **,const char *)=(void *)branch_target(call);
    assert(load(&rendered,member)==1 && *(unsigned *)RESOURCE_SIZE==size);
    assert(!memcmp(reference,rendered,size));
    free(rendered);
    free(reference);
}

int main(int argc,char **argv)
{
    assert(argc==4 || argc==7);
    art_dir=argv[2];
    size_t bytes;
    unsigned char *file=read_art(argv[3],&bytes);
    char *index=calloc(bytes+1,1);
    assert(index);
    memcpy(index,file,bytes);
    free(file);
    map_vendor(argv[1]);
    patch(0x8327c,(uintptr_t)ticks);
    patch(0x11c98,(uintptr_t)self);
    patch(0x11b24,(uintptr_t)detach);
    patch(0x11ecc,(uintptr_t)memcpy);
    patch(0x11d64,(uintptr_t)strcpy);
    patch(0x11f98,(uintptr_t)strncpy);
    patch(0x11fe0,(uintptr_t)strrchr);
    patch(0x11b60,(uintptr_t)strtol);
    patch(0x80c08,(uintptr_t)favorites);
    verify_search(index,"star fox",0,9,1,"002/Star Fox.sfc");
    verify_search(index,"fOx",0,9,1,"002/Star Fox.sfc");
    verify_search(index,"STAR-FOX",0,9,1,"002/Star Fox.sfc");
    verify_search(index,"ninja",0,9,1,"003/Ninja Gaiden (USA).zip");
    verify_search(index,"RZLJC",0,9,1,"003/Ninja Gaiden (USA).zip");
    verify_search(index,"chrono trigger",0,9,1,"002/Chrono Trigger.zip");
    verify_search(index,"FINAL FANTASY",1,1,3,"002/Final Fantasy VI (Rev 1).zip");
    verify_search(index,"no match",0,9,0,NULL);
    verify_search(index,"sfc",0,9,0,NULL);
    verify_search(index,"",0,9,6,"002/Final Fantasy VI.zip");
    puts("PASS actual firmware search worker, displayed paths, paging and empty results");
    patch(0x11f74,(uintptr_t)strcmp);
    if(argc==7) {
        patch(0x11b6c,(uintptr_t)free);
        patch(0x11b84,(uintptr_t)fseek);
        patch(0x11be4,(uintptr_t)quiet);
        patch(0x11c8c,(uintptr_t)memset);
        patch(0x11ce0,(uintptr_t)fopen);
        patch(0x11ddc,(uintptr_t)fread);
        patch(0x11e78,(uintptr_t)calloc);
        patch(0x11e84,(uintptr_t)ftell);
        patch(0x11eb4,(uintptr_t)fwrite);
        patch(0x11ed8,(uintptr_t)malloc);
        patch(0x11ee4,(uintptr_t)strlen);
        patch(0x11f08,(uintptr_t)usleep);
        patch(0x11f20,(uintptr_t)fclose);
        verify_pack(argv[4]);
        art_dir=argv[5];
        verify_pack(argv[6]);
        puts("PASS actual firmware opens and decodes all stock and refreshed pack entries");
        art_dir=argv[2];
    }
    patch(0x82aa8,(uintptr_t)load_art);
    verify_art(0x8a79c,"type.raw",17,291,103,327,151);
    verify_art(0x8e3a0,"setting.raw",0,144,20,159,37);
    puts("PASS Settings artwork at both firmware load sites");
    if(argc==7) {
        art_dir=argv[5];
        verify_refreshed_art(0x8a79c,"type.raw");
        verify_refreshed_art(0x8e3a0,"setting.raw");
        puts("PASS refreshed Settings assets are preserved at both firmware load sites");
    }
    free(index);
    return 0;
}
