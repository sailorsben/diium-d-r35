"""Integrate the adaptive decoder in a scratch copy of the current SNES core."""
import hashlib
from pathlib import Path
import shutil
import sys


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f'Unexpected source for BRR patch: {old!r}')
    return text.replace(old, new)


def apply(core):
    apu = core / 'source/apu_blargg.c'
    text = apu.read_text()
    start = text.index('static INLINE void dsp_decode_brr( dsp_voice_t* v )')
    stop = text.index('\n/* Misc */', start)
    original = text[start:stop]
    split = original.index('   /* Decode four samples */')
    arithmetic = original[split:original.rindex('\n}')]
    if hashlib.sha256(original.encode()).hexdigest() != '028dda6afb9c3365beab6d5dda0e25b2179c8876f4858bafc20722b72c0393c1':
        raise ValueError('Unqualified original BRR decoder')

    # Keep the same shifts and truncation. Multiplication avoids signed-left-
    # shift UB for the negative 4-bit input and invalid-range correction.
    arithmetic = replace_once(arithmetic, 's = (s << shift) >> 1;',
                              's = (s * (1 << shift)) >> 1;')
    arithmetic = replace_once(arithmetic, 's = (s >> 25) << 11;',
                              's = (s >> 25) * 0x800;')
    scalar = ('static INLINE void brr_decode_samples(int32_t *pos, uint32_t nybbles, int32_t header)\n'
              '{\n   int32_t *end;\n' + arithmetic + '\n}\n\n')
    dispatch = original[:split].replace('int32_t nybbles, *pos, *end, header;',
                                        'int32_t nybbles, *pos, header;') + '''   if (brr_intercept)
   {
      if (brr_capture_left)
         brr_decode_observed(pos, nybbles, header);
      else
         brr_decode_cached(pos, nybbles, header);
   }
   else
      brr_decode_samples(pos, nybbles, header);
}

'''
    header = 'snes-brr-adaptive.h'
    apu.write_text(text[:start] + scalar + f'#include "{header}"\n\n' + dispatch + text[stop:],
                   newline='\n')
    shutil.copyfile(Path(__file__).with_name(header), apu.with_name(header))

    libretro = core / 'libretro.c'
    text = replace_once(libretro.read_text(), 'void retro_run(void)\n{',
                        'void d35_brr_frame(void);\nvoid d35_brr_reset(void);\n'
                        'void d35_brr_begin_run(void);\nvoid d35_brr_end_run(void);\n\n'
                        'void retro_run(void)\n{\n   d35_brr_frame();')
    text = replace_once(text, '   S9xMainLoop();',
                        '   d35_brr_begin_run();\n   S9xMainLoop();\n   d35_brr_end_run();')
    for signature in ('void retro_reset(void)',
                      'bool retro_load_game(const struct retro_game_info* game)',
                      'void retro_unload_game(void)'):
        anchor = signature + '\n{'
        text = replace_once(text, anchor, anchor + '\n   d35_brr_reset();')
    start = text.index('bool retro_unserialize(const void* data, size_t size)')
    # A rejected state load must leave the current decoder policy intact.
    anchor = '   if (size != retro_serialize_size())\n      return false;\n\n   S9xReset();'
    text = text[:start] + replace_once(text[start:], anchor, anchor + '\n   d35_brr_reset();')
    libretro.write_text(text, newline='\n')
    link = core / 'link.T'
    link.write_text(replace_once(link.read_text(), 'retro_*;',
                                 'retro_*; d35_brr_set_enabled; d35_brr_read;'), newline='\n')


if __name__ == '__main__':
    apply(Path(sys.argv[1]))
