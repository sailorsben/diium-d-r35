/* Offline experiment: reuse BG0 geometry, never main/sub pixels or depth.
 * The command lifetime is one synchronous S9xUpdateScreen. No CPU, DMA,
 * palette or register writer can run between its sub and main consumers. */
#ifndef D35_SHARED_BG_GEOMETRY_H
#define D35_SHARED_BG_GEOMETRY_H
struct d35_shared_command {uint32_t offset;uint16_t tile;uint8_t line,lines;};
static struct d35_shared_command d35_shared_commands[8192];
static unsigned d35_shared_count,d35_shared_valid,d35_shared_capture;
static unsigned long long d35_shared_stats[16];
__attribute__((visibility("default"))) void d35_shared_read(unsigned long long *out)
{memcpy(out,d35_shared_stats,sizeof(d35_shared_stats));memset(d35_shared_stats,0,sizeof(d35_shared_stats));}
static void d35_shared_region(void)
{d35_shared_count=d35_shared_valid=d35_shared_capture=0;}
static void d35_shared_edge(void)
{
 if(d35_shared_capture){d35_shared_stats[3]++;d35_shared_capture=d35_shared_valid=0;}
}
static inline void d35_shared_record(unsigned tile,unsigned offset,unsigned line,unsigned lines)
{
 if(!d35_shared_capture)return;
 if(d35_shared_count==8192){d35_shared_stats[4]++;d35_shared_capture=d35_shared_valid=0;return;}
 d35_shared_commands[d35_shared_count++]=(struct d35_shared_command){offset,(uint16_t)tile,(uint8_t)line,(uint8_t)lines};
 d35_shared_stats[1]++;
}
#define D35_SHARED_REPLAY(MODE) \
static __attribute__((noinline)) void d35_shared_replay_##MODE(struct d35_batch_context *ctx,unsigned low,unsigned high) \
{ \
 for(unsigned i=0;i<d35_shared_count;i++){ \
  const struct d35_shared_command *c=&d35_shared_commands[i]; \
  GFX.Z1=GFX.Z2=(c->tile&0x2000)?high:low; \
  if(!d35_batch_tile_mode(ctx,c->tile,c->offset,c->line,c->lines,MODE)) \
   (*DrawTilePtr)(c->tile,c->offset,c->line,c->lines); \
  d35_shared_stats[5]++;d35_shared_stats[6]+=c->lines; \
 } \
}
D35_SHARED_REPLAY(0)
D35_SHARED_REPLAY(1)
D35_SHARED_REPLAY(3)
#undef D35_SHARED_REPLAY
static unsigned d35_shared_begin(unsigned mode,unsigned bg,unsigned batch_ok,
 struct d35_batch_context *ctx,unsigned low,unsigned high)
{
 d35_shared_capture=0;
 if(bg!=0)return 0;
 /* Full-width equal clips, 8x8 mode1 only. Scroll edges invalidate the
  * recorded list at the original edge site. Never scan all tiles to guard. */
 if(mode!=1||BG.TileSize!=8||!batch_ok||GFX.Pseudo||
    !(GFX.r212c&1)||!(GFX.r212d&1)||IPPU.Clip[0].Count[0]||
    IPPU.Clip[1].Count[0]||d35_window_is_target(0)){
  d35_shared_valid=0;return 0;
 }
 if(GFX.S==GFX.SubScreen){
  d35_shared_valid=d35_shared_capture=1;d35_shared_count=0;d35_shared_stats[0]++;return 0;
 }
 if(GFX.S!=GFX.Screen||!d35_shared_valid)return 0;
 d35_shared_valid=0;d35_shared_stats[2]++;
 if(ctx->mode==0)d35_shared_replay_0(ctx,low,high);
 else if(ctx->mode==1)d35_shared_replay_1(ctx,low,high);
 else d35_shared_replay_3(ctx,low,high);
 return 1;
}
#endif
