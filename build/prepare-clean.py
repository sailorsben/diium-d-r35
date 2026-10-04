from pathlib import Path
base=Path(__file__).resolve().parent
text=(base/'emu_sfc_plus_v2.c').read_text()
text=text.replace('/* D-R35 adapter, v2. Native core remains unmodified upstream code. */',
                  '/* D-R35 stable adapter: v2 playback; diagnostic logging is opt-in only. */')
text=text.replace('      logfile = fopen(path ? path : "/usr/retro/emu_sfc_plus_v2.log", "w");',
                  '      if (!path || !*path) return;\n      logfile = fopen(path, "w");')
assert '/usr/retro/emu_sfc_plus_v2.log' not in text
(base/'emu_sfc_plus_clean.c').write_text(text,newline='\n')
for src,dest in [('adapter-check-v2.c','adapter-check-clean.c'),
                 ('video-contract-check.c','video-contract-check-clean.c')]:
    text=(base/src).read_text().replace('emu_sfc_plus_v2.c','emu_sfc_plus_clean.c')
    (base/dest).write_text(text,newline='\n')
text=(base/'build-v2.sh').read_text().replace('v2','clean').replace('video-contract-check.c','video-contract-check-clean.c')
(base/'build-clean.sh').write_text(text,newline='\n')
text=(base/'run-v2-checks.sh').read_text().replace('v2','clean')
text=text.replace('export D35_PLUS_LOG="$base/clean/verification/adapter.log"','unset D35_PLUS_LOG')
(base/'run-clean-checks.sh').write_text(text,newline='\n')
print('Prepared stable v2 playback with no automatic diagnostic log.')
