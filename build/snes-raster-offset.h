/* Prototype Mode 2 strips. Stay inside the current raster flush and
 * transpose only disjoint columns of one clip span on one screen plane. */
#ifdef D35_RASTER_ISOLATED
/* Keep the much larger NEON path out of the common background dispatcher. */
__attribute__((noipa))
#endif
static bool d35_offset_strip(unsigned bg, uint8_t low, uint8_t high)
{
   unsigned clips = GFX.pCurrentClip->Count[bg];
   unsigned left = clips ? GFX.pCurrentClip->Left[0][bg] : 0;
   unsigned right = clips ? GFX.pCurrentClip->Right[0][bg] : 256;
   unsigned size = BG.TileSize, shift = size == 16 ? 4 : 3;
   unsigned mask = size == 16 ? 1023 : 511;
   unsigned base = PPU.BG[2].SCBase << 1, shape = PPU.BG[2].SCSize;
   unsigned bytes = (1 + (shape & 1)) * (1 + ((shape >> 1) & 1)) * 2048;
   unsigned sc[4], offsets[4];
   unsigned mode = DrawClippedTilePtr == DrawClippedTile16 ? 0 :
                   DrawClippedTilePtr == DrawClippedTile16Add ? 1 :
                   DrawClippedTilePtr == DrawClippedTile16Sub ? 3 : 7;
   if (clips > 1 || right > 256 || right <= left || mode == 7 ||
       GFX.EndY <= GFX.StartY || GFX.EndY >= SNES_HEIGHT_EXTENDED ||
       IPPU.HalfWidthPixels || IPPU.DoubleWidthPixels || IPPU.DoubleHeightPixels ||
       IPPU.Interlace || GFX.Pseudo || GFX.PPL < 256 || GFX.ZPitch != GFX.PPL ||
       d35_fixed_active || d35_window_is_target(bg) || base + bytes > 65536)
      return false;

   offsets[0] = base;
   offsets[1] = base + ((shape & 1) ? 2048 : 0);
   offsets[2] = (shape & 2) ? offsets[1] + 2048 : base;
   offsets[3] = offsets[2] + ((shape & 1) ? 2048 : 0);
   shape = PPU.BG[bg].SCSize;
   sc[0] = PPU.BG[bg].SCBase << 1;
   sc[1] = (sc[0] + ((shape & 1) ? 2048 : 0)) & 65535;
   sc[2] = (shape & 2) ? (sc[1] + 2048) & 65535 : sc[0];
   sc[3] = (sc[2] + ((shape & 1) ? 2048 : 0)) & 65535;
   BG.StartPalette = 0;
   D35_RASTER_ADD(0, GFX.EndY - GFX.StartY + 1);
#ifdef D35_RASTER_NEON
   struct d35_batch_context ctx;
   ctx.valid = ctx.depth_policy = 0;
#endif

   for (unsigned y = GFX.StartY; y <= GFX.EndY;)
   {
      unsigned src_h = LineData[y].BG[2].HOffset;
      unsigned src_v = LineData[y].BG[2].VOffset;
      unsigned bg_h = LineData[y].BG[bg].HOffset;
      unsigned bg_v = LineData[y].BG[bg].VOffset;
      unsigned map_row = ((src_v - 1) >> 3) & 63;
      unsigned band = 1, remaining = GFX.EndY - y + 1;
      while (band < remaining &&
             LineData[y + band].BG[2].HOffset == src_h &&
             LineData[y + band].BG[2].VOffset == src_v &&
             LineData[y + band].BG[bg].HOffset == bg_h &&
             LineData[y + band].BG[bg].VOffset == bg_v)
         ++band;
      D35_RASTER_ADD(1, 1);

      for (unsigned x = left; x < right;)
      {
         unsigned h = bg_h, v = bg_v;
         if (x)
         {
            unsigned col = ((src_h + x - 1) & mask) >> 3;
            unsigned page = (col >= 32), word = (col & 31) * 2;
            unsigned next_row = (map_row + 1) & 63, enable = 1u << (bg + 13);
            unsigned addr_h = offsets[(map_row >> 5) * 2 + page] + (map_row & 31) * 64 + word;
            unsigned addr_v = offsets[(next_row >> 5) * 2 + page] + (next_row & 31) * 64 + word;
            unsigned cell_h = READ_2BYTES(Memory.VRAM + addr_h);
            unsigned cell_v = READ_2BYTES(Memory.VRAM + addr_v);
            if (cell_h & enable) h = (cell_h & ~7u) | (bg_h & 7);
            if (cell_v & enable) v = cell_v + 1;
         }
         unsigned pos = (h + x) & mask, start = pos & 7, quotient = pos >> 3;
         unsigned column = size == 16 ? quotient >> 1 : quotient;
         unsigned limit = x == left ? 8 - (left & 7) : 8;
         unsigned count = 8 - start;
         if (count > limit) count = limit;
         if (count > right - x) count = right - x;
         D35_RASTER_ADD(2, 1);
         D35_RASTER_ADD(3, band);

         for (unsigned row = 0; row < band;)
         {
            unsigned world_y = y + row + v, line = world_y & 7, lines = 8 - line;
            unsigned map_y = (world_y >> shift) & 63;
            unsigned addr = sc[(map_y >> 5) * 2 + (column >= 32)] +
                            (map_y & 31) * 64 + (column & 31) * 2;
            unsigned tile = READ_2BYTES(Memory.VRAM + addr);
            GFX.Z1 = GFX.Z2 = tile & 0x2000 ? high : low;
            if (size == 16)
            {
               unsigned vertical = ((world_y & 8) != 0) ^ ((tile & V_FLIP) != 0);
               unsigned horizontal = (quotient & 1) ^ ((tile & H_FLIP) != 0);
               tile += vertical * 16 + horizontal;
            }
            if (lines > band - row) lines = band - row;
            int offset = (int)((y + row) * GFX.PPL + x) - (int)start;
            D35_RASTER_ADD(4, 1);
            D35_RASTER_ADD(5, lines > 1 ? lines : 0);
            D35_RASTER_ADD(6, !start && count == 8 ? lines : 0);
#ifdef D35_RASTER_NEON
            if (!start && count == 8 && d35_batch_tile_mode(&ctx, tile, offset, line * 8, lines, mode))
            {
               row += lines;
               continue;
            }
#elif defined(D35_RASTER_FULL)
            if (!start && count == 8)
            {
               (*DrawTilePtr)(tile, offset, line * 8, lines);
               row += lines;
               continue;
            }
#endif
            (*DrawClippedTilePtr)(tile, offset, start, count, line * 8, lines);
            row += lines;
         }
         x += count;
      }
      y += band;
   }
   return true;
}
