/* Exact alternatives for canonical 00/ff visibility masks; no timing claim. */
#ifndef D35_PARTIAL_KERNELS_H
#define D35_PARTIAL_KERNELS_H
static inline uint16x8_t d35_boolean_mask16(uint8x8_t mask)
{return vreinterpretq_u16_s16(vmovl_s8(vreinterpret_s8_u8(mask)));}
/* Plain indexed rows only. Never touch hidden color/depth lanes. */
static inline __attribute__((always_inline)) unsigned d35_sparse_plain(
 uint16_t *out,uint8_t *depth,const uint8_t *indices,const uint16_t *colors,
 uint64_t active,unsigned flip,uint8_t z2)
{
 uint32_t lo=(uint32_t)active,hi=(uint32_t)(active>>32);
 unsigned count=(((lo&0x01010101u)+(hi&0x01010101u))*0x01010101u)>>24;
 if(!count||count>2)return 0;
 while(count--){
  unsigned lane;
  if(lo){lane=(unsigned)__builtin_ctz(lo)>>3;lo&=~(255u<<(lane*8));}
  else{lane=(unsigned)__builtin_ctz(hi)>>3;hi&=~(255u<<(lane*8));lane+=4;}
  out[lane]=colors[indices[flip?7-lane:lane]];depth[lane]=z2;
 }
 return 1;
}
#endif
