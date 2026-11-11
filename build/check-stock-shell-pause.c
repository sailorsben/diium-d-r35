/* Run the real stock pause sprite compositor and controls layout. */
#define main stock_audit_main
#include "check-stock-snes-loader.c"
#undef main
#include <setjmp.h>

enum { UI=0x1998d8, WIDTH=640, HEIGHT=480, STRIDE=1280 };
static uint16_t frame[HEIGHT][WIDTH];
static void *game_art;
static jmp_buf first_frame;
static unsigned texts;
static uint16_t *preview;
static uint32_t keymap[128];

static void no_preview(void) {}

static void text_run(void *target, int x, int y, int height, unsigned color, const char *text)
{
    (void)target;
    (void)color;
    assert(text && *text);
    if (texts==0) {
        assert(x==312 && y==340 && height==42 && !strcmp(text,"P1"));
        /* The stock renderer owns this area. The underlying art is solid. */
        for(int py=341; py<375; ++py)
            for(int px=312; px<356; ++px) assert(frame[py][px]==frame[341][312]);
    } else if (texts<=6) {
        unsigned key=texts-1;
        assert(x==444+112*(int)(key%2) && y==282+54*(int)(key/2) && height==24);
        for(int py=y+11; py<y+29; ++py)
            for(int px=x; px<x+32; ++px) assert(frame[py][px]==frame[y+11][x]);
    } else {
        assert(texts<=8 && x==305 && height==18);
        assert(y==(texts==7?423:441)); /* real baselines are y+29 */
        for(int py=y+17; py<y+33; ++py)
            for(int px=x; px<612; ++px) assert(frame[py][px]==frame[y+17][x]);
    }
    ++texts;
}

static void display(void *buffer, unsigned width, unsigned height, unsigned stride)
{
    assert(buffer==frame && width==WIDTH && height==HEIGHT && stride==STRIDE);
    assert(texts==9);
    longjmp(first_frame,1);
}

static void verify_save_slots(void)
{
    uint32_t *records=game_art;
    uint16_t *pixels=(void *)((char *)game_art+records[0]);
    memcpy(frame,pixels,sizeof(frame));
    ((void (*)(void *, unsigned, const void *, unsigned))0x803a8)(frame,STRIDE,game_art,6);
    const int (*stock_slots)[6]=(const void *)0x19a61c;
    for(int slot=0; slot<6; ++slot) {
        int x=296+104*(slot%3), y=289+75*(slot/3);
        int rim_x=292+stock_slots[slot][0], rim_y=286+stock_slots[slot][1];
        uint16_t center=frame[y+29][x+42];
        uint16_t gutter=frame[y+29][rim_x+96];
        assert(center!=frame[y+18][x+42]);
        ((void (*)(int,int,unsigned))0x90f40)(rim_x,rim_y,0xf800);
        assert(frame[y+29][rim_x+1]==0xf800 && frame[y+29][rim_x+92]==0xf800);
        assert(frame[y+29][x+42]==center && frame[y+29][rim_x+96]==gutter);
    }
    puts("PASS stock slot compositor and selection rim leave all six thumbnail interiors and gutters intact");
}

int main(int argc, char **argv)
{
    assert(argc==3);
    map_vendor(argv[1]);
    FILE *file=fopen(argv[2],"rb");
    assert(file && !fseek(file,0,SEEK_END));
    long size=ftell(file);
    assert(size>0 && !fseek(file,0,SEEK_SET));
    game_art=malloc((size_t)size);
    assert(game_art && fread(game_art,1,(size_t)size,file)==(size_t)size && !fclose(file));
    patch(0x11ecc,(uintptr_t)memcpy);
    patch(0x11d64,(uintptr_t)strcpy);
    patch(0x8f538,(uintptr_t)no_preview);
    patch(0x85c94,(uintptr_t)text_run);
    patch(0xa6658,(uintptr_t)display);
    static uint8_t english[80];
    *(unsigned *)UI=1;
    *(void **)(UI+25*4)=english;
    *(void **)(UI+0x38)=frame;
    *(unsigned *)(UI+0x3c)=WIDTH;
    *(unsigned *)(UI+0x40)=HEIGHT;
    *(void **)(UI+0x5c)=game_art;
    *(void **)(GOT+0x304)=keymap;
    *(void **)(GOT+0x39c)=&preview;
    if(!setjmp(first_frame)) ((void (*)(void))0x8f5c0)();
    assert(texts==9);
    puts("PASS stock controls screen draws P1, six live mappings and both help lines in reserved areas");
    verify_save_slots();
    free(game_art);
    return 0;
}
