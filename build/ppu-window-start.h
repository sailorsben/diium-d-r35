/* Capture only immutable window lookup results during one DrawOBJS call. */
#ifndef D35_PPU_WINDOW_START_H
#define D35_PPU_WINDOW_START_H
struct d35_obj_start {unsigned short next;unsigned char index,visible;};
struct d35_obj_lookup {unsigned kind,ready;struct d35_obj_start start[263];};
/* W has the stock seven-position layout. Never read its uninitialized tail:
 * positions below256 and the first sentinel completely determine these starts. */
#define D35_OBJ_PREPARE(Q,W) do { \
 (Q).ready=0; \
 (Q).kind=((W)[0].Pos==0&&(W)[0].Value&&(W)[1].Pos==256)?1:((W)[0].Pos>255?2:0); \
} while(0)
#define D35_OBJ_START(Q,W,X,I,V,N) do { \
 if((Q).kind==1){(I)=(X)<0?0:1;(V)=(X)>=0;(N)=(X)<0?0:256;PP_ADD(8,1);} \
 else if((Q).kind==2){(I)=0;(V)=false;(N)=(W)[0].Pos;PP_ADD(9,1);} \
 else { \
  if(!(Q).ready){unsigned wi=0;for(int sx=-7;sx<256;sx++){ \
   while(wi<7&&(W)[wi].Pos<=sx)wi++; \
   (Q).start[sx+7]=(struct d35_obj_start){wi<7?(W)[wi].Pos:1000,wi,wi?(W)[wi-1].Value:false}; \
  }(Q).ready=1;PP_ADD(10,263);} \
  struct d35_obj_start st=(Q).start[(X)+7];(I)=st.index;(V)=st.visible;(N)=st.next;PP_ADD(11,1); \
 } \
} while(0)
#endif
