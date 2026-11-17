/* Verify only the visible NES platform label changes; the FC identity stays. */
#define main stock_audit_main
#include "check-stock-snes-loader.c"
#undef main

static const char *last_label;
static int capture_text(void *frame,int x,int y,int size,unsigned ink,const char *label)
{
    (void)frame; (void)x; (void)y; (void)size; (void)ink;
    last_label=label;
    return 42;
}

int main(int argc,char **argv)
{
    assert(argc==4);
    map_vendor(argv[1]);
    uintptr_t trampoline=strtoul(argv[2],NULL,16);
    uintptr_t hook=strtoul(argv[3],NULL,16);
    patch(trampoline,(uintptr_t)capture_text);
    int (*text)(void *,int,int,int,unsigned,const char *)=(void *)hook;
    *(int *)0x199990=7;
    *(unsigned char *)0x1c4304=1;
    assert(text(NULL,0,0,0,0,"FC")==42 && !strcmp(last_label,"NES"));
    *(int *)0x199990=6;
    assert(text(NULL,0,0,0,0,"FC")==42 && !strcmp(last_label,"FC"));
    *(int *)0x199990=7;
    assert(text(NULL,0,0,0,0,"FC Classic")==42 && !strcmp(last_label,"FC Classic"));
    puts("PASS NES label changes only in the opened NES platform view");
}
