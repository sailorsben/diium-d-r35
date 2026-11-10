"""Build exact Super FX and DSP experiments over the measured combined core."""
from importlib import import_module
from pathlib import Path
import re
import sys


base = import_module('prepare-snes-superfx')
replace_once = base.replace_once


def fx_budget(path, inline):
    source = path.read_text()
    entries = re.findall(r'&(fx_\w+)', source.split('void (*fx_apfOpcodeTable[])(void) =', 1)[1])
    assert len(entries) == 1024
    assert {i for i, fn in enumerate(entries) if fn == 'fx_stop'} == {0, 256, 512, 768}
    start = source.index('uint32_t fx_run(uint32_t nInstructions)')
    end = source.index('\n/*** Special table', start)
    original = source[start:end]
    # In the pinned interpreter, STOP is the sole instruction changing G or
    # inspecting the instruction budget. The fast loop helpers use arguments.
    assert re.findall(r'(?:CF|SF)\(G\)', source) == ['CF(G)']
    assert source.count('GSU.vCounter') == original.count('GSU.vCounter') + 2
    hot = ''
    if inline:
        for opcode in (0xd1, 0x3c, 0x31, 0x3d, 0x01):
            hot += f'         if (index == {opcode:#05x}) {entries[opcode]}(); else\n'
    body = '''uint32_t fx_run(uint32_t nInstructions)
{
   uint32_t remaining = nInstructions;
   READR14;
   if (TF(G)) {
      while (remaining-- > 0) {
         uint32_t opcode = PIPE;
         if (opcode == 0x3c) {
            uint32_t consumed = d35_try_fill(remaining + 1);
            if (!consumed) consumed = d35_try_plot(remaining + 1);
            if (consumed) {
               remaining -= consumed - 1;
               continue;
            }
         }
         FETCHPIPE;
         if (!opcode) {
            GSU.vCounter = remaining;
            fx_stop();
            return nInstructions - GSU.vInstCount;
         }
         uint32_t index = (GSU.vStatusReg & 0x300) | opcode;
HOT         fx_apfOpcodeTable[index]();
      }
   }
   GSU.vCounter = remaining;
   return nInstructions - GSU.vInstCount;
}
'''
    path.write_text(source[:start] + body.replace('HOT', hot) + source[end:], newline='\n')


def gaussian(path, neon):
    source = path.read_text()
    declaration = re.search(r'static int16_t gauss \[512\] =\s*\{([^}]+)\};', source)
    assert declaration
    coeff = [int(n) for n in re.findall(r'\d+', declaration[1])]
    assert len(coeff) == 512 and min(coeff) >= 0 and max(coeff) == 1305
    table = 'static const int16_t gauss_phase[256][4] __attribute__((aligned(8))) = {\n'
    for i in range(256):
        taps = [coeff[j] for j in (255-i, 511-i, 256+i, i)]
        table += '   {' + ', '.join(map(str, taps)) + '},\n'
    source = source[:declaration.start()] + table + '};' + source[declaration.end():]
    start = source.index('static INLINE int32_t dsp_interpolate(')
    end = source.index('\n/* Counters */', start)
    assert 'out = (int16_t) out;' in source[start:end]
    if neon:
        source = replace_once(source, '#include <retro_inline.h>', '#include <retro_inline.h>\n#include <arm_neon.h>')
        start = source.index('static INLINE int32_t dsp_interpolate(')
        end = source.index('\n/* Counters */', start)
        interpolate = '''   /* BRR decode and state load both sign-extend 16-bit samples. Shift
    * each product before summing, wrap after tap 3 and saturate after tap 4. */
   int16x4_t input = vmovn_s32(vld1q_s32(in));
   int16x4_t tap = vshrn_n_s32(vmull_s16(input, vld1_s16(coeff)), 11);
   int16x4_t sum = vadd_s16(vpadd_s16(tap, tap), vext_s16(tap, tap, 2));
   return vget_lane_s16(vqadd_s16(sum, vdup_lane_s16(tap, 3)), 0) & ~1;
'''
    else:
        interpolate = '''   int32_t out = (coeff[0] * in[0]) >> 11;
   out += (coeff[1] * in[1]) >> 11;
   out += (coeff[2] * in[2]) >> 11;
   out = (int16_t)out;
   out += (coeff[3] * in[3]) >> 11;
   CLAMP16(out);
   return out & ~1;
'''
    header = '''static INLINE int32_t dsp_interpolate(dsp_voice_t *v)
{
   const int16_t *coeff = gauss_phase[(v->interp_pos >> 4) & 255];
   const int32_t *in = &v->buf[(v->interp_pos >> 12) + v->buf_pos];
'''
    path.write_text(source[:start] + header + interpolate + '}\n' + source[end:], newline='\n')


def prepare(core, mode):
    assert mode in ('fx-budget', 'fx-budget-hot', 'dsp-table', 'dsp-neon', 'hotpaths-combined', 'fx-compact')
    base.prepare(core, 'fx-batch')
    if mode in ('fx-budget', 'fx-budget-hot', 'hotpaths-combined'):
        fx_budget(core/'source/fxinst.c', mode != 'fx-budget')
    if mode in ('dsp-table', 'dsp-neon', 'hotpaths-combined'):
        gaussian(core/'source/apu_blargg.c', mode != 'dsp-table')
    if mode == 'fx-compact':
        path = core/'source/a7_demand_output.h'
        path.write_text(replace_once(path.read_text(), 'admit=!Settings.SuperFX&&d35_pending',
                                     'admit=d35_pending'), newline='\n')


if __name__ == '__main__':
    prepare(Path(sys.argv[1]), sys.argv[2])
