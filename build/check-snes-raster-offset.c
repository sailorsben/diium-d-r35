/* Compare column/row addressing against the original private walker.
 * The sink expands each draw into its tile, row, pixel and priority. */
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define SNES_HEIGHT_EXTENDED 239
#define H_FLIP 0x4000u
#define V_FLIP 0x8000u
#define D35_RASTER_ADD(i, n) ((void)0)

static struct {
   _Alignas(2) uint8_t VRAM[65536];
} Memory;
static struct { struct { uint16_t SCBase; uint8_t SCSize; } BG[3]; } PPU;
static struct { unsigned TileSize, StartPalette; } BG;
static struct { struct { uint16_t VOffset, HOffset; } BG[3]; } LineData[240];
static struct { unsigned HalfWidthPixels, DoubleWidthPixels, DoubleHeightPixels, Interlace; } IPPU;
static struct {
   unsigned Count[3], Left[2][3], Right[2][3];
} clip;
static struct {
   unsigned StartY, EndY, PPL, PixSize, ZPitch, Pseudo, Z1, Z2;
   __typeof__(clip) *pCurrentClip;
} GFX;
static unsigned d35_fixed_active;
static bool d35_window_is_target(unsigned bg) { (void)bg; return false; }

static unsigned read_word(const void *p)
{
   const uint8_t *b = p;
   return b[0] | ((unsigned)b[1] << 8);
}
#define READ_2BYTES read_word

static uint32_t ref[240 * 256], test[240 * 256], *sink;
static void record(uint32_t tile, int32_t offset, uint32_t start, uint32_t width,
                   uint32_t line, uint32_t rows)
{
   assert((line >> 3) + rows <= 8 && start + width <= 8 && tile < (1u << 17));
   for (unsigned y = 0; y < rows; ++y)
      for (unsigned x = start; x < start + width; ++x)
      {
         unsigned index = offset + y * GFX.PPL + x;
         assert(index < sizeof(ref) / sizeof(*ref) && sink[index] == 0);
         sink[index] = (1u << 31) | tile | (((line >> 3) + y) << 17) |
                       (GFX.Z1 << 20) | (x << 25);
      }
}

static void (*DrawClippedTilePtr)(uint32_t, int32_t, uint32_t, uint32_t, uint32_t, uint32_t) = record;
#define DrawClippedTile16 record
#define DrawClippedTile16Add record
#define DrawClippedTile16Sub record

#include "offset-reference.inc"
#include "snes-raster-offset.h"

static uint32_t rng = 0x3b91875d;
static uint32_t random_word(void)
{
   rng ^= rng << 13;
   rng ^= rng >> 17;
   rng ^= rng << 5;
   return rng;
}

int main(void)
{
   const unsigned cases = 2048;
   GFX.PPL = GFX.ZPitch = 256;
   GFX.PixSize = 1;
   GFX.pCurrentClip = &clip;
   for (unsigned i = 0; i < cases; ++i)
   {
      unsigned bg = (i >> 5) & 1, shape = (i >> 1) & 3;
      unsigned pages = (1 + (shape & 1)) * (1 + (shape >> 1));
      PPU.BG[2].SCSize = shape;
      PPU.BG[2].SCBase = ((i & 64) ? 32 - pages : random_word() % (33 - pages)) * 1024;
      PPU.BG[bg].SCSize = (i >> 3) & 3;
      PPU.BG[bg].SCBase = ((i & 128) ? 31 : random_word() % 32) * 1024;
      BG.TileSize = i & 1 ? 16 : 8;
      clip.Count[bg] = (i >> 8) & 1;
      unsigned left = random_word() % 256;
      clip.Left[0][bg] = left;
      clip.Right[0][bg] = left + 1 + random_word() % (256 - left);
      GFX.StartY = random_word() % 215;
      GFX.EndY = GFX.StartY + 1 + random_word() % 22;
      for (unsigned j = 0; j < sizeof(Memory.VRAM); ++j)
         Memory.VRAM[j] = random_word();
      unsigned run = 0;
      for (unsigned y = GFX.StartY; y <= GFX.EndY; ++y)
      {
         if (run)
         {
            LineData[y] = LineData[y - 1];
            --run;
         }
         else
         {
            static const unsigned wrap_rows[] = {0, 249, 256, 505, 512};
            LineData[y].BG[2].VOffset = (i & 512) ? wrap_rows[i % 5] : random_word() % 1024;
            LineData[y].BG[2].HOffset = random_word() % 1024;
            LineData[y].BG[bg].VOffset = random_word() % 1024;
            LineData[y].BG[bg].HOffset = random_word() % 1024;
            run = random_word() % 11;
         }
      }
      memset(ref, 0, sizeof(ref));
      memset(test, 0, sizeof(test));
      sink = ref;
      DrawBackgroundOffset(2, bg, 5, 13);
      sink = test;
      assert(d35_offset_strip(bg, 5, 13));
      if (memcmp(ref, test, sizeof(ref)) != 0)
      {
         fprintf(stderr, "Mode 2 geometry diverged in case %u\n", i);
         return 1;
      }
   }
   printf("Mode 2 geometry matched in %u generated raster ranges\n", cases);
   return 0;
}
