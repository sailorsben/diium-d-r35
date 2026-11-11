#define main stock_audit_main
#include "check-stock-snes-loader.c"
#undef main
#include <ctype.h>

static unsigned route;
static const char *expected_path;
static int core_nes(const char *p,unsigned flags) { (void)flags; assert(!strcmp(p,expected_path)); route=1; return 0; }
static int core_snes(const char *p,unsigned flags) { (void)flags; assert(!strcmp(p,expected_path)); route=2; return 0; }
static int core_gba(const char *p,unsigned flags) { (void)flags; assert(!strcmp(p,expected_path)); route=3; return 0; }
static int core_gb(const char *p,unsigned flags) { (void)flags; assert(!strcmp(p,expected_path)); route=4; return 0; }
static int core_md(const char *p,unsigned flags) { (void)flags; assert(!strcmp(p,expected_path)); route=5; return 0; }
static int core_psx(const char *p,unsigned flags) { (void)flags; assert(!strcmp(p,expected_path)); route=6; return 0; }
static int core_other(const char *p,unsigned flags) { (void)flags; assert(!strcmp(p,expected_path)); route=7; return 0; }
static int core_arcade(const char *p,unsigned flags) { (void)flags; assert(!strcmp(p,expected_path)); route=8; return 0; }
static void stop_sound(void) {}
static int zip_token;
static void *zip_open(const char *p,unsigned flags,unsigned type)
{ assert(!strcmp(p,expected_path) && !flags && type==2); return &zip_token; }
static unsigned zip_item(void *zip,int index,void *entry)
{
    assert(zip==&zip_token);
    memset(entry,0,304);
    if(index==-1) { *(int *)entry=2; return 0; }
    if(index==0 || index==1) { strcpy((char *)entry+4,"unrecognized.chip"); return 0; }
    return 1;
}
static unsigned zip_close(void *zip) { assert(zip==&zip_token); return 0; }

int main(int argc,char **argv)
{
    assert(argc==2);
    map_vendor(argv[1]);
    patch(0x11d64,(uintptr_t)strcpy); patch(0x11f74,(uintptr_t)strcmp);
    patch(0x11be4,(uintptr_t)quiet); patch(0x11c20,(uintptr_t)puts);
    patch(0x11c8c,(uintptr_t)memset); patch(0x11e3c,(uintptr_t)strstr);
    patch(0x11ee4,(uintptr_t)strlen); patch(0x12028,(uintptr_t)islower);
    patch(0x11d1c,(uintptr_t)__ctype_toupper_loc);
    patch(0xa6988,(uintptr_t)stop_sound);
    patch(0xa5058,(uintptr_t)core_nes); patch(0xa4f54,(uintptr_t)core_snes);
    patch(0xa4c9c,(uintptr_t)core_gba); patch(0xa4b78,(uintptr_t)core_gb);
    patch(0xa4e34,(uintptr_t)core_md); patch(0xa56f4,(uintptr_t)core_psx);
    patch(0xa514c,(uintptr_t)core_other); patch(0xa5844,(uintptr_t)core_other);
    patch(0xa5200,(uintptr_t)core_arcade); patch(0xa2730,(uintptr_t)zip_open);
    patch(0xa2824,(uintptr_t)zip_item); patch(0xa2bec,(uintptr_t)zip_close);
    ((void (*)(void))INIT_CORE_SETTING)();
    const char *extensions[]={"nes","sfc","smc","fig","gba","gb","gbc","bin","smd","gen","md","iso","img","cue","pbp","vrt"};
    unsigned tested=0;
    for(unsigned i=0;i<sizeof(extensions)/sizeof(*extensions);++i) {
        char path[128],upper[16];
        snprintf(path,sizeof(path),"/usr/fixture.%s",extensions[i]);
        strcpy(upper,extensions[i]); for(char *p=upper;*p;++p) *p=toupper(*p);
        int index=((int (*)(const char *))GET_CORE_INDEX)(upper);
        if(index<0) continue;
        expected_path=path; route=0;
        assert(((int (*)(const char *,unsigned))0xa5c68)(path,0)>=0);
        printf("%s index=%d route=%u\n",extensions[i],index,route);
        assert(route);
        ++tested;
    }
    assert(tested>=10);
    expected_path="/usr/arcade.gma"; route=0;
    assert(((int (*)(const char *,unsigned))0xa5c68)(expected_path,0)==1 && route==8);
    puts("gma route=8");
    expected_path="/usr/arcade.zip"; route=0;
    assert(((int (*)(const char *,unsigned))0xa5c68)(expected_path,0)==1 && route==8);
    puts("arcade zip route=8 (archive boundary stubbed)");
    puts("PASS exact stock run_game dispatch to emulator entry points");
    return 0;
}
