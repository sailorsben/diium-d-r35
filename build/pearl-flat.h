/* Exact flat 2bpp band expansion. Pure eligibility/data checks precede writes.
 * No effect identifiers. Original renderer handles every unsupported shape. */
#ifndef D35_PEARL_FLAT_H
#define D35_PEARL_FLAT_H
static inline unsigned d35_flat_band(unsigned y,unsigned lines,unsigned h,
 unsigned v,const uint16_t *left,const uint16_t *right,unsigned low,unsigned high)
{
 if(!lines||lines>8)return 0;
 unsigned q=(h&511)>>3,n=((h&7)+256+7)>>3;
 unsigned tile=READ_2BYTES(q>31?right+(q&31):left+q);
 for(unsigned i=1;i<n;i++){
  unsigned k=(q+i)&63;
  if(READ_2BYTES(k>31?right+(k&31):left+k)!=tile)return 0;
 }
 unsigned addr=(BG.TileAddress+((tile&1023)<<BG.TileShift)+
    (((tile&511)>=256)?BG.NameSelect:0))&65535;
 unsigned palette=(((tile>>10)&BG.PaletteMask)<<BG.PaletteShift)+BG.StartPalette;
 uint16_t colors[8];uint8_t indices[8];
 for(unsigned i=0;i<lines;i++){
  unsigned row=(y+i+v)&7;if(tile&V_FLIP)row=7-row;
  unsigned a=Memory.VRAM[(addr+row*2)&65535],b=Memory.VRAM[(addr+row*2+1)&65535];
  if((a&&a!=255)||(b&&b!=255))return 0;
  indices[i]=(a?1:0)|(b?2:0);colors[i]=IPPU.ScreenColors[palette+indices[i]];
 }
 unsigned z=(tile&0x2000)?high:low;GFX.Z1=GFX.Z2=z;
 for(unsigned i=0;i<lines;i++)if(indices[i]){
  uint16_t *out=(uint16_t *)GFX.S+(y+i)*GFX.PPL;
  uint8_t *depth=GFX.DB+(y+i)*GFX.PPL;
  uint16x8_t color=vdupq_n_u16(colors[i]);uint8x16_t zz=vdupq_n_u8(z);
  for(unsigned x=0;x<256;x+=16){vst1q_u16(out+x,color);vst1q_u16(out+x+8,color);vst1q_u8(depth+x,zz);}
 }
 return 1;
}
#endif
