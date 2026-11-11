from pathlib import Path
s=Path('build/snes9x2005/source/apu_blargg.c').read_text()
a=s.index('static INLINE void dsp_decode_brr('); b=s.index('\n/* Misc */',a)
fn=s[a:b]
prefix='''#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define INLINE inline
#define BRR_BUF_SIZE 12
#define CLAMP16(io) do { if ((io)>32767) (io)=32767; else if ((io)<-32768) (io)=-32768; } while(0)
typedef struct { int32_t buf[24]; int buf_pos,brr_addr,brr_offset; } dsp_voice_t;
static struct { int t_brr_byte,t_brr_header; uint8_t ram[65536]; } dsp_m;
'''
suffix='''
static uint32_t rnd=12345678;
static uint32_t random_word(void) { rnd^=rnd<<13; rnd^=rnd>>17; rnd^=rnd<<5; return rnd; }
int main(void) {
  unsigned test,i; unsigned checks=0;
  for(test=0;test<1000000;test++) {
    dsp_voice_t a,b; int pos=(test%3)*4;
    for(i=0;i<24;i++) { a.buf[i]=(int16_t)random_word(); b.buf[i]=(int16_t)random_word(); }
    a.buf_pos=b.buf_pos=pos;
    a.brr_addr=65535; a.brr_offset=1;
    b.brr_addr=1000; b.brr_offset=3;
    b.buf[pos+11]=a.buf[pos+11]; b.buf[pos+10]=a.buf[pos+10];
    dsp_m.t_brr_byte=random_word()&255;
    dsp_m.t_brr_header=random_word()&255;
    dsp_m.ram[1]=random_word()&255; dsp_m.ram[1004]=dsp_m.ram[1];
    dsp_decode_brr(&a);
    dsp_m.t_brr_header^=3; /* End/loop bits are not decoder inputs. */
    dsp_decode_brr(&b);
    if(a.buf_pos!=b.buf_pos) return 1;
    for(i=0;i<4;i++) if(a.buf[pos+i]!=b.buf[pos+i] || a.buf[pos+i+12]!=b.buf[pos+i+12]) return 2;
    checks++;
  }
  printf("PASS %u original-decoder pairs: same proposed key with different unrelated buffers, addresses, end/loop flags; all four outputs and mirrored copies exact\\n",checks);
  return 0;
}
'''
Path('build/check-brr-key.c').write_text(prefix+fn+suffix)
