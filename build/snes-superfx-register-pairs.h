/* Fold adjacent, register-only Super FX instructions. This recognizes ISA
 * patterns in the live instruction stream and preserves both instruction
 * slots, including when a slice ends between the two operations. */
static bool d35_register_pairs_enabled;

__attribute__((visibility("default"))) void d35_raster_set_enabled(bool enabled)
{
    d35_register_pairs_enabled = enabled;
}

static inline bool d35_fx_register_pair(unsigned opcode)
{
    unsigned with = opcode - 0x20u;
    unsigned following = PRGBANK(R15);
    unsigned to = following - 0x10u;
    unsigned from = following - 0xb0u;

    if (with < 14 && (to < 14 || from < 14)) {
        if (to < 14) {
            GSU.avReg[to] = GSU.avReg[with];
        } else {
            uint32_t value = GSU.avReg[from];
            GSU.avReg[with] = value;
            GSU.vOverflow = (value & 0x80u) << 16;
            GSU.vSign = GSU.vZero = value;
        }
        CLRFLAGS;
    } else if (opcode - 0xb0u < 14 && to < 14 && !TF(B)) {
        GSU.pvSreg = &GSU.avReg[opcode - 0xb0u];
        GSU.pvDreg = &GSU.avReg[to];
    } else {
        return false;
    }

    /* Neither operation modifies PC, program bank, executable RAM or R14. */
    ++R15;
    FETCHPIPE;
    ++R15;
    return true;
}

static __attribute__((noipa)) uint32_t d35_fx_run_register_pairs(uint32_t nInstructions)
{
    GSU.vCounter = nInstructions;
    READR14;
    while (TF(G) && (GSU.vCounter-- > 0)) {
        unsigned opcode = PIPE;
        if (opcode == 0x3c) {
            unsigned consumed = d35_try_fill(GSU.vCounter + 1);
            if (!consumed) consumed = d35_try_plot(GSU.vCounter + 1);
            if (consumed) {
                GSU.vCounter -= consumed - 1;
                continue;
            }
        } else if (GSU.vCounter && (opcode - 0x20u < 14 || opcode - 0xb0u < 14) &&
                   d35_fx_register_pair(opcode)) {
            --GSU.vCounter;
            continue;
        }
        FX_STEP;
    }
    return nInstructions - GSU.vInstCount;
}
