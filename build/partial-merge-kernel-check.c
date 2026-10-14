/* Owned independent scalar oracle: canonical masks, flips, both index depths. */
#include <stdint.h>
#include <arm_neon.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "partial-merge-kernels.h"
__attribute__((noinline)) uint16x8_t mask_new(uint8x8_t m){return d35_boolean_mask16(m);}
__attribute__((noinline)) uint16x8_t mask_old(uint8x8_t m){uint8x8x2_t z=vzip_u8(m,m);return vreinterpretq_u16_u8(vcombine_u8(z.val[0],z.val[1]));}
int main(void){
 unsigned tests=0,hits=0;
 for(unsigned bits=2;bits<=4;bits+=2)for(unsigned seed=0;seed<32;seed++)for(unsigned flip=0;flip<2;flip++)for(unsigned shape=0;shape<256;shape++){
  uint16_t out[20],expected[20],colors[16],wide[8],oldwide[8];uint8_t depth[24],expected_depth[24],indices[8],mask[8];unsigned n=0;
  for(unsigned i=0;i<20;i++)out[i]=expected[i]=(uint16_t)(i*1777+seed*19);
  for(unsigned i=0;i<24;i++)depth[i]=expected_depth[i]=(uint8_t)(i+seed);
  for(unsigned i=0;i<16;i++)colors[i]=(uint16_t)(i*3199+seed*67);
  for(unsigned i=0;i<8;i++){
   mask[i]=(shape&(1u<<i))?255:0;n+=!!mask[i];
   unsigned ix=(seed+i)%((1u<<bits)-1)+1;indices[flip?7-i:i]=(uint8_t)ix;
   if(mask[i]){expected[4+i]=colors[ix];expected_depth[5+i]=(uint8_t)(seed+65);}
  }
  uint8x8_t m=vld1_u8(mask);vst1q_u16(wide,mask_new(m));vst1q_u16(oldwide,mask_old(m));assert(!memcmp(wide,oldwide,sizeof(wide)));
  unsigned done=d35_sparse_plain(out+4,depth+5,indices,colors,vget_lane_u64(vreinterpret_u64_u8(m),0),flip,(uint8_t)(seed+65));
  assert(done==(n>0&&n<=2));
  if(done){assert(!memcmp(out,expected,sizeof(out)));assert(!memcmp(depth,expected_depth,sizeof(depth)));hits++;}
  else{for(unsigned i=0;i<20;i++)assert(out[i]==(uint16_t)(i*1777+seed*19));for(unsigned i=0;i<24;i++)assert(depth[i]==(uint8_t)(i+seed));}
  tests++;
 }
 printf("PASS %u scalar-oracle mask/flip/index-depth/canary cases; %u sparse hits; exact sign expansion; no timings\n",tests,hits);return 0;
}
