/* Offline work census only. No timers; not a production core or A7 timing. */
#ifndef D35_PEARL_WORK_H
#define D35_PEARL_WORK_H
extern unsigned long long d35_pearl[352];
extern unsigned d35_pearl_plane,d35_pearl_layer;
#define PW(n) (++d35_pearl[(d35_pearl_plane*6+d35_pearl_layer)*24+(n)])
#ifdef D35_PEARL_IMPLEMENTATION
unsigned long long d35_pearl[352];unsigned d35_pearl_plane,d35_pearl_layer;
__attribute__((visibility("default"))) void d35_pearl_read(unsigned long long *out){memcpy(out,d35_pearl,sizeof(d35_pearl));memset(d35_pearl,0,sizeof(d35_pearl));}
#endif
static inline void d35_pearl_row(unsigned mode,uint8x8_t mask,uint8x8_t depth,uint8x8_t depth_mask)
{
 uint8_t m[8],z[8];vst1_u8(m,mask);vst1_u8(z,depth);
 PW(2);if(!vget_lane_u64(vreinterpret_u64_u8(depth_mask),0))PW(3);
 if(vget_lane_u64(vreinterpret_u64_u8(mask),0)){
  PW(4);PW(9+mode);if(mode)PW(8);
  if(vget_lane_u64(vreinterpret_u64_u8(mask),0)==UINT64_MAX)PW(5);
  for(unsigned i=0;i<8;i++)if(m[i]){PW(6);if(z[i]>d35_pearl_plane)PW(7);}
 }
}
#endif
