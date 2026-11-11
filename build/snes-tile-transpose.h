/* Two independent 8 by 8 bit transposes per NEON register. Each input
 * byte is a plane and each output byte is a palette index. SNES pixels
 * run from the high bit of each plane to the low bit. */
static inline uint8x16_t d35_transpose_two_rows(uint64x2_t rows)
{
    uint64x2_t move;
    move = vandq_u64(veorq_u64(rows, vshrq_n_u64(rows, 7)),
                    vdupq_n_u64(UINT64_C(0x00aa00aa00aa00aa)));
    rows = veorq_u64(rows, veorq_u64(move, vshlq_n_u64(move, 7)));
    move = vandq_u64(veorq_u64(rows, vshrq_n_u64(rows, 14)),
                    vdupq_n_u64(UINT64_C(0x0000cccc0000cccc)));
    rows = veorq_u64(rows, veorq_u64(move, vshlq_n_u64(move, 14)));
    move = vandq_u64(veorq_u64(rows, vshrq_n_u64(rows, 28)),
                    vdupq_n_u64(UINT64_C(0x00000000f0f0f0f0)));
    rows = veorq_u64(rows, veorq_u64(move, vshlq_n_u64(move, 28)));
    return vrev64q_u8(vreinterpretq_u8_u64(rows));
}

static inline unsigned d35_transpose_tile(uint8_t *cache, const uint8_t *planes, unsigned bits)
{
    uint16x8_t low = vreinterpretq_u16_u8(vld1q_u8(planes));
    uint16x8_t high = bits == 4 ? vreinterpretq_u16_u8(vld1q_u8(planes + 16)) : vdupq_n_u16(0);
    uint64x2_t nonzero = vreinterpretq_u64_u16(vorrq_u16(low, high));
    if (!(vgetq_lane_u64(nonzero, 0) | vgetq_lane_u64(nonzero, 1))) {
        memset(cache, 0, 64);
        return 0;
    }

    uint16x8x2_t rows = vzipq_u16(low, high);
    uint32x4_t first = vreinterpretq_u32_u16(rows.val[0]);
    uint32x4_t second = vreinterpretq_u32_u16(rows.val[1]);
    vst1q_u8(cache, d35_transpose_two_rows(vmovl_u32(vget_low_u32(first))));
    vst1q_u8(cache + 16, d35_transpose_two_rows(vmovl_u32(vget_high_u32(first))));
    vst1q_u8(cache + 32, d35_transpose_two_rows(vmovl_u32(vget_low_u32(second))));
    vst1q_u8(cache + 48, d35_transpose_two_rows(vmovl_u32(vget_high_u32(second))));
    return 1;
}
