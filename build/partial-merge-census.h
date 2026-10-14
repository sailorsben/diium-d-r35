/* Offline-only exact row/mask census; never A7 timing evidence. */
#ifndef D35_PARTIAL_MERGE_CENSUS_H
#define D35_PARTIAL_MERGE_CENSUS_H
#define D35_PM_BUCKET 24u
#define D35_PM_BASE (2u*6u*7u*D35_PM_BUCKET)
#define D35_PM_SIZE (D35_PM_BASE+7u*256u)
extern unsigned long long d35_pm[D35_PM_SIZE];
#ifdef D35_PARTIAL_IMPLEMENTATION
unsigned long long d35_pm[D35_PM_SIZE];
__attribute__((visibility("default"))) void d35_partial_read(unsigned long long *out){memcpy(out,d35_pm,sizeof(d35_pm));memset(d35_pm,0,sizeof(d35_pm));}
#endif
static inline unsigned long long *d35_pm_bucket(unsigned mode){return d35_pm+((d35_pearl_plane*6+d35_pearl_layer)*7+mode)*D35_PM_BUCKET;}
static inline void d35_partial_observe(unsigned mode,uint8x8_t idx,uint8x8_t old,uint8x8_t mask,uint8x8_t dm){
 uint8_t i[8],z[8],m[8],d[8];vst1_u8(i,idx);vst1_u8(z,old);vst1_u8(m,mask);vst1_u8(d,dm);
 unsigned bits=0,lanes=0,trans=0,covered=0,noop=1,direct=1,runs=0;
 unsigned long long *c=d35_pm_bucket(mode);c[0]++;
 for(unsigned j=0;j<8;j++){
  if(m[j]){bits|=1u<<j;lanes++;if(!j||!m[j-1])runs++;if(z[j]!=GFX.Z2)noop=0;}
  else if(z[j]!=GFX.Z2)direct=0;
  trans+=!i[j];covered+=!d[j];
 }
 if(!bits)return;c[1]++;c[4]+=lanes;c[12]+=runs;
 if(bits==255){c[2]++;return;}c[3]++;c[8]+=noop;c[9]+=direct;
 d35_pm[D35_PM_BASE+mode*256u+bits]++;
 c[5]+=!covered;c[6]+=!trans;c[7]+=(covered&&trans);
 c[10]+=(bits==15||bits==240);
 unsigned pair_ok=1;
 for(unsigned j=0;j<4;j++){unsigned p=(bits>>(j*2))&3;c[14]+=p==3;if(p&&p!=3)pair_ok=0;}
 c[11]+=pair_ok;
 c[13]+=((bits&15)==15)+((bits&240)==240);

}
static inline void d35_partial_colors(unsigned mode,uint8x8_t mask,uint16x8_t color,const uint16_t *out,unsigned offset){
 uint8_t m[8],sd[8];uint16_t col[8];vst1_u8(m,mask);vst1q_u16(col,color);vst1_u8(sd,vld1_u8(GFX.SubZBuffer+offset));
 unsigned bits=0,same=1,enabled=1,fixed=1;
 for(unsigned j=0;j<8;j++)if(m[j]){bits|=1u<<j;same&=out[j]==col[j];enabled&=mode>=5?sd[j]==1:sd[j]>0;fixed&=sd[j]==1;}
 if(!bits||bits==255)return;
 unsigned long long *c=d35_pm_bucket(mode);c[15]+=mode&&enabled;c[16]+=mode&&fixed;c[17]+=same;
}
#endif
