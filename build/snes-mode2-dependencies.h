/* Compare the actual Mode 2 VRAM read set and the PPU state that determines
 * the walk. The census checks predictions against real draws. The memo arm
 * retains nonoverlapping spans on the core-owned, padded output planes. */
#include <stddef.h>

enum {
#ifdef D35_MODE2_SMALL
    D35_DEP_SPANS = 16, D35_DEP_STORAGE = 24 * 1024,
#elif defined(D35_MODE2_BOUNDED)
    D35_DEP_SPANS = 16, D35_DEP_STORAGE = 65536,
#else
    D35_DEP_SPANS = 64, D35_DEP_STORAGE = 65536,
#endif
    D35_DEP_BLOCK = 32, D35_DEP_BLOCKS = 65536 / D35_DEP_BLOCK
};

struct d35_mode2_key {
    uint16_t map[3], shape[3], size[2], tiles[2], object_base, object_select;
    uint8_t regs[4], fixed[3], blank, mosaic, mosaic_layers;
    uint8_t first_object, object_size, object_rotation, flicker, fixed_pending;
    ClipData clip[2];
};

struct d35_mode2_span {
    struct d35_mode2_key key;
    SOBJ objects[128];
    SLineData lines[240];
    uint16_t fixed[240], colors[256];
    uint16_t start, end, blocks;
#ifdef D35_MODE2_RANGES
    uint16_t read_blocks[D35_DEP_STORAGE / D35_DEP_BLOCK];
    uint16_t block_counts[D35_DEP_STORAGE / D35_DEP_BLOCK];
    uint8_t read_data[D35_DEP_STORAGE];
#else
    uint16_t read_blocks[D35_DEP_BLOCKS];
    uint8_t read_data[D35_DEP_BLOCKS][D35_DEP_BLOCK];
#endif
    bool valid;
};

static uint8_t d35_seen_block[D35_DEP_BLOCKS];
static struct d35_mode2_span *d35_record;
static bool d35_dependency_enabled;
static unsigned d35_dep_stats[7];
static uint8_t d35_object_first, d35_object_size, d35_object_rotated, d35_object_flicker;

static void d35_mode2_object_setup(void)
{
    /* The row schedule uses the values seen at setup. The live OAM latches
     * and the frontend's flicker setting can change between setup and draw. */
    d35_object_first = PPU.FirstSprite;
    d35_object_size = PPU.OBJSizeSelect;
    d35_object_rotated = PPU.OAMPriorityRotation && (PPU.OAMAddr & PPU.OAMFlip & 1);
    d35_object_flicker = reduce_sprite_flicker;
}
#ifdef D35_MODE2_MEMO
static struct d35_mode2_span d35_memo[D35_DEP_SPANS], d35_pending_span;
static unsigned d35_evict_span;

void d35_mode2_clear(void)
{
    for (unsigned i = 0; i < D35_DEP_SPANS; ++i) d35_memo[i].valid = false;
    d35_record = NULL;
}
#else
static struct d35_mode2_span d35_dependency[2][D35_DEP_SPANS];
static uint8_t d35_span_rgb[2][240][512];
static struct d35_mode2_span *d35_prior;
static unsigned d35_dependency_bank, d35_used[2];
#endif

__attribute__((visibility("default"))) void d35_raster_set_enabled(bool enabled)
{
#ifdef D35_MODE2_MEMO
    if (enabled != d35_dependency_enabled) d35_mode2_clear();
#endif
    d35_dependency_enabled = enabled;
}

__attribute__((visibility("default"))) void d35_mode2_read(unsigned *stats)
{
    memcpy(stats, d35_dep_stats, sizeof(d35_dep_stats));
    memset(d35_dep_stats, 0, sizeof(d35_dep_stats));
}

void d35_mode2_vram(unsigned addr, unsigned bytes)
{
    if (!d35_record || !d35_record->valid) return;
    if (!bytes || addr >= 65536u || bytes > 65536u - addr) {
        d35_record->valid = false;
        return;
    }
    unsigned last = (addr + bytes - 1) / D35_DEP_BLOCK;
#ifdef D35_MODE2_RANGES
    d35_seen_block[addr / D35_DEP_BLOCK] = 1;
    d35_seen_block[last] = 1;
    /* Current producers read one 16-bit map cell or one 4bpp tile.
     * An unexpected wider read invalidates this span. */
    if (last > addr / D35_DEP_BLOCK + 1) d35_record->valid = false;
#else
    for (unsigned block = addr / D35_DEP_BLOCK; block <= last; ++block) {
        if (d35_seen_block[block]) continue;
        d35_seen_block[block] = 1;
        d35_record->read_blocks[d35_record->blocks++] = block;
    }
#endif
}

static void d35_dependency_frame(void)
{
    if (!d35_dependency_enabled) return;
#ifndef D35_MODE2_MEMO
    d35_dependency_bank ^= 1;
    d35_used[d35_dependency_bank] = 0;
#endif
}

static void d35_span_key(struct d35_mode2_span *entry, unsigned start, unsigned end)
{
    struct d35_mode2_key *key = &entry->key;
    memset(key, 0, sizeof(*key));
    for (unsigned bg = 0; bg < 3; ++bg) {
        key->map[bg] = PPU.BG[bg].SCBase;
        key->shape[bg] = PPU.BG[bg].SCSize;
    }
    for (unsigned bg = 0; bg < 2; ++bg) {
        key->size[bg] = PPU.BG[bg].BGSize;
        key->tiles[bg] = PPU.BG[bg].NameBase;
        key->mosaic_layers |= PPU.BGMosaic[bg] << bg;
    }
    key->regs[0] = GFX.r212c;
    key->regs[1] = GFX.r212d;
    key->regs[2] = GFX.r2130;
    key->regs[3] = GFX.r2131;
    key->fixed[0] = IPPU.XB[PPU.FixedColourRed];
    key->fixed[1] = IPPU.XB[PPU.FixedColourGreen];
    key->fixed[2] = IPPU.XB[PPU.FixedColourBlue];
    key->blank = PPU.ForcedBlanking;
    key->mosaic = PPU.Mosaic;
    key->fixed_pending = d35_fixed_pending;
    key->first_object = d35_object_first;
    key->object_size = d35_object_size;
    key->object_base = PPU.OBJNameBase;
    key->object_select = PPU.OBJNameSelect;
    key->object_rotation = d35_object_rotated;
    key->flicker = d35_object_flicker;
    memcpy(key->clip, IPPU.Clip, sizeof(key->clip));

    unsigned rows = end - start + 1;
    entry->start = start;
    entry->end = end;
    entry->valid = true;
    entry->blocks = 0;
    memcpy(entry->lines, LineData + start, rows * sizeof(*LineData));
    memcpy(entry->colors, IPPU.ScreenColors, sizeof(entry->colors));
    if (key->fixed_pending)
        memcpy(entry->fixed, d35_fixed_rows + start, rows * sizeof(*entry->fixed));
    bool objects = ((GFX.r212c | GFX.r212d) & 16) && !key->blank;
    if (objects) memcpy(entry->objects, PPU.OBJ, sizeof(entry->objects));
    ++d35_dep_stats[1];
    d35_dep_stats[2] += rows;
}

static bool d35_same_span(const struct d35_mode2_span *prior, const struct d35_mode2_span *entry)
{
    const struct d35_mode2_key *key = &entry->key;
    unsigned rows = entry->end - entry->start + 1;
    bool objects = ((GFX.r212c | GFX.r212d) & 16) && !key->blank;
    if (memcmp(&prior->key, key, sizeof(*key)) ||
        memcmp(prior->lines, entry->lines, rows * sizeof(*entry->lines)) ||
        memcmp(prior->colors, entry->colors, sizeof(entry->colors)) ||
        (key->fixed_pending && memcmp(prior->fixed, entry->fixed, rows * sizeof(*entry->fixed))) ||
        (objects && memcmp(prior->objects, entry->objects, sizeof(entry->objects)))) return false;
    ++d35_dep_stats[5];
#ifdef D35_MODE2_RANGES
    unsigned offset = 0;
#endif
    for (unsigned j = 0; j < prior->blocks; ++j) {
        unsigned block = prior->read_blocks[j];
#ifdef D35_MODE2_RANGES
        unsigned bytes = prior->block_counts[j] * D35_DEP_BLOCK;
        if (memcmp(prior->read_data + offset, Memory.VRAM + block * D35_DEP_BLOCK, bytes)) return false;
        offset += bytes;
#else
        if (memcmp(prior->read_data[j], Memory.VRAM + block * D35_DEP_BLOCK, D35_DEP_BLOCK)) return false;
#endif
    }
    return true;
}

static bool d35_capture_span(unsigned start, unsigned end)
{
    if (!d35_dependency_enabled) return false;
    ++d35_dep_stats[0];
    bool eligible = PPU.BGMode == 2 && !GFX.Pseudo && !IPPU.Interlace && !IPPU.DoubleWidthPixels &&
        !IPPU.DoubleHeightPixels && !IPPU.HalfWidthPixels && end < 240 && end >= start;
#ifdef D35_MODE2_MEMO
    /* Pitched rows keep offscreen sprite and clipped tile lanes away from
     * neighboring visible rows. Only use independently owned backing planes. */
    if (!eligible || !Settings.SuperFX || d35_direct || IPPU.RenderedScreenWidth != 256 ||
        GFX.Screen != GFX.Screen_buffer + 32 || GFX.SubScreen != GFX.SubScreen_buffer + 32 ||
        GFX.ZBuffer != GFX.ZBuffer_buffer + 32 || GFX.SubZBuffer != GFX.SubZBuffer_buffer + 32 ||
        GFX.Pitch2 != 1024 || GFX.PPL != 512 || GFX.ZPitch != 512) {
        d35_mode2_clear();
        return false;
    }
    d35_span_key(&d35_pending_span, start, end);
    struct d35_mode2_span *free_slot = NULL;
    for (unsigned i = 0; i < D35_DEP_SPANS; ++i) {
        struct d35_mode2_span *prior = &d35_memo[i];
        if (prior->valid && prior->start == start && prior->end == end &&
            d35_same_span(prior, &d35_pending_span)) {
            ++d35_dep_stats[3];
            d35_dep_stats[4] += end - start + 1;
            return true;
        }
        if (prior->valid && prior->start <= end && prior->end >= start) prior->valid = false;
        if (!prior->valid && !free_slot) free_slot = prior;
    }
    if (!free_slot) free_slot = &d35_memo[d35_evict_span++ % D35_DEP_SPANS];
    /* Copy only the key and captured line metadata. The read set is built
     * from the miss draw, with no cache or framebuffer copy on a hit. */
    memcpy(free_slot, &d35_pending_span, offsetof(struct d35_mode2_span, read_blocks));
    free_slot->valid = true;
    d35_record = free_slot;
#else
    unsigned bank = d35_dependency_bank;
    if (!eligible || d35_used[bank] == D35_DEP_SPANS) return false;
    struct d35_mode2_span *entry = &d35_dependency[bank][d35_used[bank]++];
    d35_span_key(entry, start, end);
    d35_record = entry;
    for (unsigned i = 0; i < d35_used[bank ^ 1]; ++i) {
        struct d35_mode2_span *prior = &d35_dependency[bank ^ 1][i];
        if (prior->valid && prior->start == start && prior->end == end && d35_same_span(prior, entry)) {
            d35_prior = prior;
            break;
        }
    }
#endif
    memset(d35_seen_block, 0, sizeof(d35_seen_block));
    return false;
}

static void d35_finish_span(void)
{
    struct d35_mode2_span *entry = d35_record;
    if (entry && entry->valid) {
#ifndef D35_MODE2_MEMO
        unsigned bank = d35_dependency_bank;
        bool exact = d35_prior != NULL;
        for (unsigned row = entry->start; row <= entry->end; ++row) {
            uint8_t *pixels = GFX.Screen + row * GFX.Pitch2;
            if (exact && memcmp(pixels, d35_span_rgb[bank ^ 1][row], 512)) exact = false;
            memcpy(d35_span_rgb[bank][row], pixels, 512);
        }
        if (d35_prior && exact) {
            ++d35_dep_stats[3];
            d35_dep_stats[4] += entry->end - entry->start + 1;
        } else if (d35_prior) ++d35_dep_stats[6];
#endif
#ifdef D35_MODE2_RANGES
        unsigned offset = 0;
        for (unsigned block = 0; block < D35_DEP_BLOCKS;) {
            if (!d35_seen_block[block]) {
                ++block;
                continue;
            }
            unsigned first = block;
            do { ++block; } while (block < D35_DEP_BLOCKS && d35_seen_block[block]);
            unsigned bytes = (block - first) * D35_DEP_BLOCK;
            if (bytes > D35_DEP_STORAGE - offset) {
                ++d35_dep_stats[6];
                entry->valid = false;
                break;
            }
            entry->read_blocks[entry->blocks] = first;
            entry->block_counts[entry->blocks++] = block - first;
            memcpy(entry->read_data + offset, Memory.VRAM + first * D35_DEP_BLOCK, bytes);
            offset += bytes;
        }
#else
        for (unsigned i = 0; i < entry->blocks; ++i)
            memcpy(entry->read_data[i], Memory.VRAM + entry->read_blocks[i] * D35_DEP_BLOCK, D35_DEP_BLOCK);
#endif
    }
    d35_record = NULL;
#ifndef D35_MODE2_MEMO
    d35_prior = NULL;
#endif
}
