from pathlib import Path
import sys
root=Path(sys.argv[1]); p=root/'source/apu_blargg.c'; s=p.read_text()
start=s.index('static INLINE void dsp_decode_brr('); end=s.index('\n/* Misc */',start)
fn=s[start:end]
assert 'pos = &v->buf [v->buf_pos];' in fn
prefix='''
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
static struct { uint64_t key; int32_t out[4]; int valid; } d35_brr_memo[256];
static unsigned long long d35_brr_calls, d35_brr_hits, d35_brr_bad, d35_brr_zero;
static unsigned d35_brr_frames;
static int d35_brr_active, d35_brr_reuse;
void d35_brr_census_frame(void) {
 const char *skip=getenv("D35_BRR_CENSUS_SKIP");
 d35_brr_reuse=getenv("D35_BRR_REUSE") != NULL;
 d35_brr_active=(d35_brr_frames++ >= (unsigned)(skip?atoi(skip):0));
}
__attribute__((destructor)) static void d35_brr_report(void) {
 fprintf(stderr,"BRR_CENSUS calls=%llu hits=%llu bad=%llu zero=%llu frames=%u entries=256 bytes=%zu\\n",d35_brr_calls,d35_brr_hits,d35_brr_bad,d35_brr_zero,d35_brr_frames,sizeof d35_brr_memo);
}
'''
fn=fn.replace('   /* Decode four samples */','''   int32_t *d35_original_pos = pos;
   uint64_t d35_key = (uint64_t)(header & 0xfc) | ((uint64_t)(uint16_t)nybbles << 8) | ((uint64_t)(uint16_t)pos[BRR_BUF_SIZE-1] << 24) | ((uint64_t)(uint16_t)pos[BRR_BUF_SIZE-2] << 40);
   uint64_t d35_hash = d35_key ^ (d35_key >> 23) ^ (d35_key >> 41);
   unsigned d35_slot = (unsigned)(d35_hash * UINT64_C(11400714819323198485) >> 56);
   if(d35_brr_active && d35_brr_reuse && d35_brr_memo[d35_slot].valid && d35_brr_memo[d35_slot].key==d35_key) {
      unsigned i;
      ++d35_brr_calls; ++d35_brr_hits;
      if ((d35_key >> 8) == 0) ++d35_brr_zero;
      for(i=0;i<4;i++) pos[i+BRR_BUF_SIZE]=pos[i]=d35_brr_memo[d35_slot].out[i];
      return;
   }
   /* Decode four samples */''')
last=fn.rfind('\n}')
fn=fn[:last]+'''
   if (d35_brr_active) {
      unsigned i;
      ++d35_brr_calls;
      if ((d35_key >> 8) == 0) ++d35_brr_zero;
      if(d35_brr_memo[d35_slot].valid && d35_brr_memo[d35_slot].key==d35_key) {
         ++d35_brr_hits;
         for(i=0;i<4;i++) if(d35_brr_memo[d35_slot].out[i]!=d35_original_pos[i]) ++d35_brr_bad;
      }
      d35_brr_memo[d35_slot].valid=1;
      d35_brr_memo[d35_slot].key=d35_key;
      for(i=0;i<4;i++) d35_brr_memo[d35_slot].out[i]=d35_original_pos[i];
   }
'''+fn[last:]
s=s[:start]+prefix+fn+s[end:]; p.write_text(s)
p=root/'libretro/libretro.c'
if not p.exists(): p=root/'libretro.c'
s=p.read_text(); import re
s,n=re.subn(r'(void retro_run\s*\(\s*void\s*\)\s*\{)',r'\1\n   extern void d35_brr_census_frame(void);\n   d35_brr_census_frame();',s,count=1)
assert n==1
p.write_text(s)
print('BRR census patched',root)
