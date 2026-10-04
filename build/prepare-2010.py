from pathlib import Path

base = Path(__file__).resolve().parent
source = (base / 'emu_sfc_plus_clean.c').read_text()
source = source.replace('D-R35 stable adapter: v2 playback; diagnostic logging is opt-in only.',
                        'D-R35 Snes9x 2010 comparison: clean v2 transport, distinct core/state identity.')
source = source.replace('emu_sfc_plus.so', 'emu_sfc_2010.so')
source = source.replace('D35_PLUS_CORE', 'D35_2010_CORE')
source = source.replace('D-R35 Plus adapter v2', 'D-R35 Snes9x 2010 comparison adapter')
source = source.replace('D35 Plus load failure', 'D35 2010 load failure')
source = source.replace('D35PLUS1', 'D3520101').replace('"a79d"', '"fe69"')
(base / 'emu_sfc_2010.c').write_text(source, newline='\n')
for old, new in [('adapter-check-clean.c', 'adapter-check-2010.c'),
                 ('video-contract-check-clean.c', 'video-contract-check-2010.c')]:
    text = (base / old).read_text().replace('emu_sfc_plus_clean.c', 'emu_sfc_2010.c')
    (base / new).write_text(text, newline='\n')
harness = (base / 'harness.c').read_text().replace('"Plus"', '"2010"')
(base / 'harness-2010.c').write_text(harness, newline='\n')
print('Prepared 2010 adapter with unchanged clean Plus audio/video transport.')
