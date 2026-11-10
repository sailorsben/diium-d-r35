/* Include the generated interpreter to check the actual fast paths and
 * reference opcode table at every instruction-budget boundary. */
#include "fxinst.c"
#include <assert.h>
#include <stdio.h>

static uint8_t ram[65536], program[65536], registers[0x300];
static uint8_t initial_ram[65536], expected_ram[65536];
static FxRegs_s initial_state, expected_state;

static uint32_t reference_run(uint32_t budget)
{
   GSU.vCounter = budget;
   READR14;
   while (TF(G) && (GSU.vCounter-- > 0))
      FX_STEP;
   return budget - GSU.vInstCount;
}

static void init(bool plot, unsigned mode, bool ram_code, uint32_t pc, uint32_t x,
                 uint32_t count, unsigned color, unsigned options, unsigned y)
{
   memset(&GSU, 0, sizeof(GSU));
   memset(ram, 0xa5, sizeof(ram));
   memset(program, 0, sizeof(program));
   memset(registers, 0, sizeof(registers));
   GSU.pvRegisters = registers;
   GSU.pvRam = GSU.pvRamBank = GSU.apvRamBank[0] = ram;
   GSU.nRamBanks = 1;
   GSU.pvRomBank = program;
   GSU.pvPrgBank = ram_code ? ram : program;
   PBR = ram_code ? 0x70 : 1;
   GSU.vStatusReg = FLG_G | FLG_B | FLG_ALT2 | FLG_CY;
   GSU.pvSreg = &R8;
   GSU.pvDreg = &R9;
   GSU.vInstCount = 7;
   GSU.vLastRamAdr = 81;
   GSU.vCarry = 1;
   GSU.vOverflow = -300;
   GSU.vColorReg = color;
   GSU.vPlotOptionReg = options;
   GSU.vMode = mode;
   GSU.vScreenHeight = 128;
   GSU.pvScreenBase = ram;
   fx_computeScreenPointers();
   GSU.pfPlot = fx_apfPlotTable[mode];
   fx_apfOpcodeTable[0x04c] = GSU.pfPlot;
   fx_apfOpcodeTable[0x24c] = GSU.pfPlot;
   PIPE = 0x3c;
   R0 = color;
   R1 = x;
   R2 = y;
   R12 = count;
   R13 = pc;
   R15 = pc + (plot ? 1 : 3);
   if (plot) {
      PRGBANK(pc) = 0x3c;
      PRGBANK(pc+1) = 0x4c;
      PRGBANK(pc+2) = 0;
   } else {
      PRGBANK(pc) = 0x31;
      PRGBANK(pc+1) = 0xd1;
      PRGBANK(pc+2) = 0x3c;
      PRGBANK(pc+3) = 0xd1;
      PRGBANK(pc+4) = 0;
   }
}

static void compare(uint32_t budget)
{
   memcpy(&initial_state, &GSU, sizeof(GSU));
   memcpy(initial_ram, ram, sizeof(ram));
   uint32_t expected = reference_run(budget);
   memcpy(&expected_state, &GSU, sizeof(GSU));
   memcpy(expected_ram, ram, sizeof(ram));
   memcpy(&GSU, &initial_state, sizeof(GSU));
   memcpy(ram, initial_ram, sizeof(ram));
   assert(fx_run(budget) == expected);
   assert(!memcmp(&GSU, &expected_state, sizeof(GSU)));
   assert(!memcmp(ram, expected_ram, sizeof(ram)));
}

int main(void)
{
   const unsigned offsets[] = {0, 1, 7, 8, 250, 253, 255, 65517, 65535, 0xfffffff1u};
   const unsigned colors[] = {0, 0x0505, 0x00a0, 0x00b1, 0x1201, 0x807f};
   const unsigned counts[] = {0, 1, 4, 5, 9, 0x1000c};
   unsigned comparisons = 0;
   init(false, 1, false, 0x4000, 1, 9, 0, 0, 0);
   assert(d35_try_fill(32) == 32);
   init(true, 1, false, 0x4000, 1, 9, 0xf3, 2, 7);
   assert(d35_try_plot(16) == 16);
   for (unsigned plot = 0; plot <= 1; ++plot) {
      for (unsigned i = 0; i < sizeof(offsets)/sizeof(*offsets); ++i) {
         for (unsigned j = 0; j < sizeof(colors)/sizeof(*colors); ++j) {
            for (unsigned budget = 0; budget <= 44; ++budget) {
               init(plot, 1, false, j & 1 ? 0xfffcu : 0x4000, offsets[i],
                    counts[(i+j)%6], colors[j], (i+j+budget)%4, i*23+j);
               compare(budget);
               ++comparisons;
            }
         }
      }
      for (unsigned budget = 0; budget <= 44; ++budget) {
         init(plot, 1, true, 0x4000, plot ? 0 : 0x3fff, 17, 0x0101, 1, 0);
         compare(budget);
         init(plot, 0, false, 0x4000, 2, 17, 0xf3, 3, 7);
         compare(budget);
         comparisons += 2;
      }
   }
   printf("Super FX batch matches reference GSU and RAM in %u cases\n", comparisons);
}
