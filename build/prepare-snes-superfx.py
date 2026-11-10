"""Apply Super FX experiments on top of the verified full-tile raster build."""
from hashlib import sha256
from importlib import import_module
from pathlib import Path
import sys

replace_once = import_module('prepare-snes-throughput').replace_once
prepare_raster = import_module('prepare-snes-raster').prepare
SOURCE = '171833443fb47fdb99e169fbceeaaaeaacce33f9a2f13f16951b854084f2eb65'


def prepare(core, mode):
    prepare_raster(core, 'raster-offset-full')
    path = core/'source/fxinst.c'
    text = path.read_text()
    if sha256(text.encode()).hexdigest() != SOURCE:
        raise ValueError('Use the exact multigame-fixes-private-v1/core source')
    anchor = 'uint32_t fx_run(uint32_t nInstructions)'
    step = '   while (TF(G) && (GSU.vCounter-- > 0))\n      FX_STEP;'
    if mode == 'fx-profile':
        include = Path(__file__).with_name('snes-superfx-profile.h').read_text()
        text = replace_once(text, anchor, include + '\n' + anchor)
        text = replace_once(text, step,
                            '   while (TF(G) && (GSU.vCounter-- > 0)) {\n'
                            '      if (PIPE == 0x3c) d35_record_loop();\n'
                            '      FX_STEP;\n   }')
        link = core/'link.T'
        link.write_text(replace_once(link.read_text(), 'retro_*;', 'retro_*; d35_fx_loops;'), newline='\n')
    elif mode in ('fx-fill', 'fx-plot', 'fx-batch', 'fx-batch-toggle', 'fx-batch-count'):
        kernels = ('fill', 'plot') if mode.startswith('fx-batch') else (mode.removeprefix('fx-'),)
        include = '\n'.join(Path(__file__).with_name(f'snes-superfx-{n}.h').read_text() for n in kernels)
        toggle = mode.endswith('-toggle')
        counted = mode.endswith('-count')
        if toggle:
            include += '''
static bool d35_fx_enabled;
__attribute__((visibility("default"))) void d35_fx_set_enabled(bool enabled)
{
   d35_fx_enabled = enabled;
}
'''
            link = core/'link.T'
            link.write_text(replace_once(link.read_text(), 'retro_*;', 'retro_*; d35_fx_set_enabled;'), newline='\n')
        if counted:
            include += '''
static uint64_t d35_fx_counts[4];
__attribute__((visibility("default"))) void d35_fx_batch_counts(uint64_t *out)
{
   memcpy(out, d35_fx_counts, sizeof(d35_fx_counts));
   memset(d35_fx_counts, 0, sizeof(d35_fx_counts));
}
'''
            link = core/'link.T'
            link.write_text(replace_once(link.read_text(), 'retro_*;', 'retro_*; d35_fx_batch_counts;'), newline='\n')
        text = replace_once(text, anchor, include + '\n' + anchor)
        attempts = ''
        for i, kernel in enumerate(kernels):
            if counted:
                attempts += f'''         if (!consumed) {{
            consumed = d35_try_{kernel}(GSU.vCounter + 1);
            if (consumed) {{
               ++d35_fx_counts[{2*i}];
               d35_fx_counts[{2*i+1}] += consumed;
            }}
         }}
'''
            else:
                attempts += f'         if (!consumed) consumed = d35_try_{kernel}(GSU.vCounter + 1);\n'
        gate = ' && d35_fx_enabled' if toggle else ''
        text = replace_once(text, step, '''   while (TF(G) && (GSU.vCounter-- > 0)) {
      if (PIPE == 0x3cGATE) {
         uint32_t consumed = 0;
ATTEMPTS
         if (consumed) {
            GSU.vCounter -= consumed - 1;
            continue;
         }
      }
      FX_STEP;
   }'''.replace('GATE', gate).replace('ATTEMPTS\n', attempts))
    else:
        raise ValueError(mode)
    path.write_text(text, newline='\n')


if __name__ == '__main__':
    prepare(Path(sys.argv[1]), sys.argv[2])
