/* Execute the patched ARM environment callback against the pinned launcher. */
#define main stock_audit_main
#include "check-stock-snes-loader.c"
#undef main
#include <stdbool.h>

struct variable { const char *key, *value; };

int main(int argc, char **argv)
{
    assert(argc==2);
    map_vendor(argv[1]);
    patch(0x11f74,(uintptr_t)strcmp);
    bool (*environment)(unsigned,void *)=(void *)0xa2fc8;
    struct variable overscan={"fceumm_overscan",NULL};
    assert(environment(15,&overscan)); /* libretro GET_VARIABLE */
    assert(overscan.value && !strcmp(overscan.value,"disabled"));
    puts("PASS NES core receives full-frame overscan setting");
    return 0;
}
