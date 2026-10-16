/* Scripted inputs and offline oracle. Physical hot path does not CRC pixels. */
#ifndef FIVEGAME_OBSERVER_H
#define FIVEGAME_OBSERVER_H
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <zlib.h>
static uint16_t ability_input[1200];
static uint32_t game_expected[1200][3],game_pixel_crc,game_audio_crc,game_samples;
static unsigned game_oracle,game_oracle_checks,game_input_count;
static unsigned ability_number(const char *s,unsigned base){unsigned n=0;if(!s||!*s)return UINT32_MAX;while(*s){unsigned d=*s>='0'&&*s<='9'?*s-'0':*s>='a'&&*s<='f'?*s-'a'+10:99;if(d>=base||n>100000)return UINT32_MAX;n=n*base+d;s++;}return n;}
static int ability_bind(void *ram,size_t size){(void)ram;(void)size;char line[128];unsigned used=0;FILE *f;const char *input=getenv("D35_ABILITY_INPUT"),*expected=getenv("D35_ABILITY_EXPECTED");if(!input||!expected)return 0;memset(ability_input,0,sizeof(ability_input));game_input_count=game_oracle_checks=0;game_oracle=getenv("D35_FIVE_ORACLE")!=NULL;
 f=fopen(input,"r");if(!f)return 0;while(fgets(line,sizeof(line),f)){char *a=strtok(line," \r\n"),*b=strtok(NULL," \r\n");unsigned n=ability_number(a,10),bits=ability_number(b,16);if(!n||bits>65535||n>1200-used){fclose(f);return 0;}while(n--)ability_input[used++]=(uint16_t)bits;}fclose(f);if(used!=1200)return 0;
 f=fopen(expected,"rb");if(!f)return 0;size_t n=fread(game_expected,1,sizeof(game_expected),f);int extra=fgetc(f);fclose(f);return n==sizeof(game_expected)&&extra==EOF;}
static uint32_t ability_buttons(unsigned frame){return frame<1200?ability_input[frame]:0;}
static void ability_observe(unsigned frame){if(frame<1200)game_input_count=frame+1;}
static uint64_t ability_last_observer_ns(void){return 0;}
static void game_oracle_begin(void){game_pixel_crc=game_audio_crc=game_samples=0;}
static void game_oracle_video(const void *data,unsigned w,unsigned h,size_t pitch){if(game_oracle&&data)for(unsigned y=0;y<h;y++)game_pixel_crc=crc32(game_pixel_crc,(const unsigned char *)data+y*pitch,w*2);}
static void game_oracle_audio(const int16_t *data,size_t frames){if(game_oracle&&data){game_audio_crc=crc32(game_audio_crc,(const unsigned char *)data,frames*4);game_samples+=frames;}}
static int game_oracle_check(unsigned frame){if(!game_oracle)return 1;if(frame>=1200)return 0;game_oracle_checks++;return game_pixel_crc==game_expected[frame][0]&&game_audio_crc==game_expected[frame][1]&&game_samples==game_expected[frame][2];}
static void ability_finish(const char *dir){char path[1300];snprintf(path,sizeof(path),"%s/input.csv",dir);FILE *f=fopen(path,"w");if(!f)return;fprintf(f,"#oracle_enabled=%u\n#oracle_checks=%u\nframe,input\n",game_oracle,game_oracle_checks);for(unsigned i=0;i<game_input_count;i++)fprintf(f,"%u,%04x\n",i,ability_input[i]);fflush(f);fsync(fileno(f));fclose(f);}
#endif
