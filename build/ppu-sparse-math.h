/* Exact scalar arithmetic for at most two visible lanes; hidden lanes untouched.
 * This is a host kernel choice, with no changes to SNES cycles or DSP/audio. */
#ifndef D35_PPU_SPARSE_MATH_H
#define D35_PPU_SPARSE_MATH_H
static inline uint16_t d35_scalar_add(uint16_t a,uint16_t b){
 unsigned r=(a>>11)+(b>>11),g=((a>>6)&31)+((b>>6)&31),bl=(a&31)+(b&31);
 if(r>31)r=31;if(g>31)g=31;if(bl>31)bl=31;
 return (uint16_t)((r<<11)|(g<<6)|((g>>4)<<5)|bl);
}
static inline uint16_t d35_scalar_sub(uint16_t a,uint16_t b){
 unsigned ar=a>>11,br=b>>11,ag=(a>>5)&63,bg=(b>>5)&63,ab=a&31,bb=b&31;
 unsigned r=ar>br?ar-br:0,g=ag>bg?ag-bg:0,bl=ab>bb?ab-bb:0;
 g=(g&62)|(g>>5);return (uint16_t)((r<<11)|(g<<5)|bl);
}
static inline uint16_t d35_scalar_add_half(uint16_t a,uint16_t b){return (uint16_t)((((unsigned)(a&~0x0821u)+(b&~0x0821u))>>1)+(a&b&0x0821));}
static inline uint16_t d35_scalar_sub_half(uint16_t a,uint16_t b){
 unsigned x=a|0x0820,y=b&~0x0821u;unsigned i=((uint16_t)(x-y)>>1)|(x>=y?0x8000:0);
 return (uint16_t)((i&0x8000?i&0x7800:0)|(i&0x0400?i&0x03e0:0)|(i&0x0010?i&0x000f:0));
}
static inline unsigned d35_sparse_math(uint16_t *out,uint8_t *depth,const uint8_t *indices,const uint16_t *colors,
 uint64_t active,unsigned flip,uint8_t z2,const uint8_t *sd,const uint16_t *sub,uint16_t fixed,unsigned mode){
 unsigned n=((((uint32_t)active&0x01010101u)+((uint32_t)(active>>32)&0x01010101u))*0x01010101u)>>24;
 PP_ADD(17,1);if(!n||n>2)return 0;PP_ADD(18,n);
 while(active){unsigned lane=(unsigned)__builtin_ctzll(active)>>3;active&=~(UINT64_C(255)<<(lane*8));
  unsigned source=flip?7-lane:lane;uint16_t color=colors[indices[source]];unsigned d=sd[lane];
  if(mode>=5){if(d==1)color=mode==5?d35_scalar_add_half(color,fixed):d35_scalar_sub_half(color,fixed);}
  else if(d){uint16_t b=d==1?fixed:sub[lane];
   if(mode==1||(mode==2&&d==1))color=d35_scalar_add(color,b);
   else if(mode==3||(mode==4&&d==1))color=d35_scalar_sub(color,b);
   else if(mode==2)color=d35_scalar_add_half(color,b);
   else if(mode==4)color=d35_scalar_sub_half(color,b);
  }
  out[lane]=color;depth[lane]=z2;
 }
 return 1;
}
#endif
