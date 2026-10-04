#include "ui.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv)
{
    static const char *const games[] = {
      "Chrono Trigger", "Donkey Kong Country", "EarthBound",
      "Final Fantasy VI", "F-Zero", "Kirby Super Star",
      "Mega Man X", "Secret of Mana", "Star Fox", "Super Mario Kart",
      "Super Mario World", "Super Metroid", "The Legend of Zelda - A Link to the Past"
    };
    const unsigned pitch = UI_WIDTH+16;
    const size_t n = (size_t)pitch*UI_HEIGHT;
    uint16_t *storage = malloc((n+2)*sizeof(*storage));
    uint16_t *pixels;
    FILE *f;
    unsigned x,y;
    if (!storage || argc < 3) return 2;
    for (size_t i=0;i<n+2;++i) storage[i]=0xf81f;
    pixels=storage+1;
    if (!strcmp(argv[1],"pause"))
        ui_draw_pause(pixels,pitch,"Final Fantasy VI",1,"Snapshot saved.");
    else if (!strcmp(argv[1],"notice"))
        ui_draw_notice(pixels,pitch,"Starting game","Final Fantasy VI");
    else if (!strcmp(argv[1],"empty"))
        ui_draw_library(pixels,pitch,NULL,0,0,"Copy games onto your SD card.");
    else
        ui_draw_library(pixels,pitch,games,sizeof(games)/sizeof(games[0]),3,
                        "Choose a game and press A.");
    if(storage[0]!=0xf81f || storage[n+1]!=0xf81f) return 3;
    for(y=0;y<UI_HEIGHT;++y)
        for(x=UI_WIDTH;x<pitch;++x)
            if(pixels[(size_t)y*pitch+x]!=0xf81f) return 4;
    f=fopen(argv[2],"wb");
    if(!f) return 5;
    fprintf(f,"P6\n%u %u\n255\n",UI_WIDTH,UI_HEIGHT);
    for(y=0;y<UI_HEIGHT;++y) for(x=0;x<UI_WIDTH;++x) {
        unsigned p=pixels[(size_t)y*pitch+x];
        unsigned char rgb[3]={
          (unsigned char)(((p>>11)&31)*255/31),
          (unsigned char)(((p>>5)&63)*255/63),
          (unsigned char)((p&31)*255/31)};
        if(fwrite(rgb,1,3,f)!=3) return 6;
    }
    fclose(f); free(storage); return 0;
}
