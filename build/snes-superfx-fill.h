/* Collapse taken iterations of STW (R1), INC R1, LOOP, INC R1.
 * At LOOP entry, R15 points to the delay slot and R13 to STW. */
static __attribute__((noinline)) uint32_t d35_fill_iterations(uint32_t budget, uint32_t taken)
{
   uint32_t iterations = budget / 4;
   uint32_t first = R1 + 1;
   uint32_t offset = USEX16(first) & ~1u;
   uint32_t until_wrap = (65536u - offset) / 2;
   if (iterations > taken) iterations = taken;
   if (iterations > until_wrap) iterations = until_wrap;
   if (iterations < 4) return 0;

   uint8_t *dest = GSU.pvRamBank + offset;
   uint32_t word = USEX16(R0);
   uint8_t low = USEX8(word), high = USEX8(word >> 8);
   if (low == high) {
      memset(dest, low, 2 * iterations);
   } else {
      if (first & 1) {
         uint8_t swap = low;
         low = high;
         high = swap;
      }
      for (uint32_t i = 0; i < iterations; ++i) {
         dest[2*i] = low;
         dest[2*i+1] = high;
      }
   }

   R12 -= iterations;
   R1 += 2 * iterations;
   GSU.vLastRamAdr = R1 - 1;
   GSU.vSign = GSU.vZero = R1;
   CLRFLAGS;
   /* R15 and PIPE are back at the same LOOP boundary. */
   return 4 * iterations;
}

static INLINE uint32_t d35_try_fill(uint32_t budget)
{
   uint32_t remaining_loops = USEX16(R12);
   if (budget < 16 || remaining_loops < 5 || PBR >= 0x60)
      return 0;
   /* The core maps program banks below $60 to ROM. RAM-backed code can
    * modify its own instruction bytes and must retain the interpreter. */
   uint32_t target = R13;
   if (target > 0xfffcu || R15 != target + 3 ||
       PRGBANK(target) != 0x31 || PRGBANK(target+1) != 0xd1 ||
       PRGBANK(target+2) != 0x3c || PRGBANK(target+3) != 0xd1)
      return 0;
   return d35_fill_iterations(budget, remaining_loops - 1);
}
