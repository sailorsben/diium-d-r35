/* Collapse taken iterations of LOOP with PLOT in its delay slot.
 * The last iteration falls through the original interpreter. */
static __attribute__((noinline)) uint32_t d35_plot_iterations(uint32_t budget, uint32_t taken)
{
   uint32_t x = USEX8(R1);
   uint32_t iterations = budget / 2;
   if (iterations > taken) iterations = taken;
   if (iterations > 256 - x) iterations = 256 - x;
   if (iterations < 4) return 0;

   uint32_t y = USEX8(R2);
   uint8_t even = USEX8(GSU.vColorReg), odd = even;
   if (GSU.vPlotOptionReg & 2) {
      odd = USEX8(GSU.vColorReg >> 4);
      if (y & 1) {
         uint8_t swap = even;
         even = odd;
         odd = swap;
      }
   }
   uint8_t opaque = 255;
   if (!(GSU.vPlotOptionReg & 1))
      opaque = ((even & 15) ? 0xaa : 0) | ((odd & 15) ? 0x55 : 0);

   if (opaque) {
      uint8_t plane[4];
      for (unsigned bit = 0; bit < 4; ++bit)
         plane[bit] = ((even & (1u << bit)) ? 0xaa : 0) | ((odd & (1u << bit)) ? 0x55 : 0);
      uint8_t *row = GSU.apvScreen[y >> 3] + ((y & 7) << 1);
      uint32_t end = x + iterations;
      while (x < end) {
         unsigned available = 8 - (x & 7);
         unsigned count = end - x < available ? end - x : available;
         uint8_t mask = opaque & (255u >> (x & 7)) & (255u << (available - count));
         uint8_t *tile = row + GSU.x[x >> 3];
         tile[0x00] = (tile[0x00] & ~mask) | (plane[0] & mask);
         tile[0x01] = (tile[0x01] & ~mask) | (plane[1] & mask);
         tile[0x10] = (tile[0x10] & ~mask) | (plane[2] & mask);
         tile[0x11] = (tile[0x11] & ~mask) | (plane[3] & mask);
         x += count;
      }
   }

   R12 -= iterations;
   R1 += iterations;
   GSU.vSign = GSU.vZero = R12;
   CLRFLAGS;
   /* R15 and PIPE are back at the same LOOP boundary. */
   return 2 * iterations;
}

static INLINE uint32_t d35_try_plot(uint32_t budget)
{
   uint32_t remaining_loops = USEX16(R12);
   if (budget < 8 || remaining_loops < 5 || PBR >= 0x60 ||
       GSU.pfPlot != fx_plot_4bit)
      return 0;
   uint32_t target = R13;
   if (target > 0xfffeu || R15 != target + 1 ||
       PRGBANK(target) != 0x3c || PRGBANK(target+1) != 0x4c)
      return 0;
   return d35_plot_iterations(budget, remaining_loops - 1);
}
