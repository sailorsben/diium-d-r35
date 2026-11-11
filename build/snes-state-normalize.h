#ifndef D35_SNES_STATE_NORMALIZE_H
#define D35_SNES_STATE_NORMALIZE_H
#include "snes9x2005/source/sa1.h"
#include "snes9x2005/source/apu_blargg.h"

/* Keep these fields aligned with the pinned Plus equivalence harness. */
static void normalize_pointers(unsigned char *bytes)
{
    SCPUState *cpu = (SCPUState *)bytes;
    SICPU *icpu = (SICPU *)(bytes + sizeof(SCPUState));
    size_t offset = sizeof(SCPUState) + sizeof(SICPU) + sizeof(SPPU) + sizeof(SDMA) * 8 +
                    0x10000 + 0x20000 + 0x20000 + 0x8000 + SPC_SAVE_STATE_BLOCK_SIZE;
    SSA1 *sa1 = (SSA1 *)(bytes + offset);
    uintptr_t base = (uintptr_t)cpu->PCBase;
    /* The save contains raw host pointers. Keep logical CPU offsets and
     * clear only the named host fields rebuilt when a state loads. */
    cpu->PC = (uint8_t *)((uintptr_t)cpu->PC - base);
    if (cpu->PCAtOpcodeStart) cpu->PCAtOpcodeStart = (uint8_t *)((uintptr_t)cpu->PCAtOpcodeStart - base);
    if (cpu->WaitAddress) cpu->WaitAddress = (uint8_t *)((uintptr_t)cpu->WaitAddress - base);
    cpu->PCBase = NULL;
    icpu->UNUSED1 = NULL;
    icpu->S9xOpcodes = NULL;
    sa1->S9xOpcodes = NULL;
    sa1->PC = sa1->PCBase = sa1->BWRAM = sa1->PCAtOpcodeStart = NULL;
    sa1->WaitAddress = sa1->WaitByteAddress1 = sa1->WaitByteAddress2 = NULL;
    for (unsigned i = 0; i < MEMMAP_NUM_BLOCKS; ++i) {
        if ((uintptr_t)sa1->Map[i] >= 4096) sa1->Map[i] = NULL;
        if ((uintptr_t)sa1->WriteMap[i] >= 4096) sa1->WriteMap[i] = NULL;
    }
}
#endif
