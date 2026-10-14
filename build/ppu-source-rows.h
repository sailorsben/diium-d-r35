/* Bounded pre-math source-span reuse. Visibility/depth/output remain live. */
#ifndef D35_SOURCE_ROWS_H
#define D35_SOURCE_ROWS_H
uint16x8_t d35_source_color(const uint8_t *,const uint16_t *,unsigned,uint8x8_t,d35_palette_t,unsigned);
void d35_source_tile_changed(const uint8_t *);
void d35_source_clear(void);
#endif
#ifdef D35_SOURCE_IMPLEMENTATION
struct d35_source_row {const uint8_t *row;const uint16_t *palette;unsigned bits,epoch;uint16_t rgb[8];};
static struct d35_source_row d35_source_rows[32] __attribute__((aligned(64)));
static inline uint16x8_t d35_reverse_color(uint16x8_t color){uint16x8_t r=vrev64q_u16(color);return vcombine_u16(vget_high_u16(r),vget_low_u16(r));}
uint16x8_t d35_source_color(const uint8_t *row,const uint16_t *palette,unsigned bits,
 uint8x8_t screen_indices,d35_palette_t table,unsigned flip){
 unsigned slot=(((uintptr_t)row>>3)^((uintptr_t)palette>>4))&31;
 struct d35_source_row *e=&d35_source_rows[slot];PP_ADD(24,1);
 if(e->row==row&&e->palette==palette&&e->bits==bits&&e->epoch==d35_palette_epoch){
  PP_ADD(22,1);uint16x8_t color=vld1q_u16(e->rgb);return flip?d35_reverse_color(color):color;
 }
 PP_ADD(23,1);uint8x8x2_t zip=vzip_u8(vtbl2_u8(table.low,screen_indices),vtbl2_u8(table.high,screen_indices));
 uint16x8_t color=vreinterpretq_u16_u8(vcombine_u8(zip.val[0],zip.val[1]));
 vst1q_u16(e->rgb,flip?d35_reverse_color(color):color);e->row=row;e->palette=palette;e->bits=bits;e->epoch=d35_palette_epoch;
 return color;
}
void d35_source_tile_changed(const uint8_t *tile){
 for(unsigned i=0;i<32;i++){PP_ADD(25,1);uintptr_t p=(uintptr_t)d35_source_rows[i].row,t=(uintptr_t)tile;
  if(p>=t&&p-t<64)d35_source_rows[i].epoch=0;
 }
}
void d35_source_clear(void){memset(d35_source_rows,0,sizeof(d35_source_rows));}
#endif
