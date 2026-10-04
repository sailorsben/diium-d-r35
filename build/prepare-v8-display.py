from pathlib import Path
import json
base=Path(__file__).resolve().parent
evidence=base.parent/'device-evidence/card-D-v7-return/analysis.json'
d=json.loads(evidence.read_text())
d['user_v7_result']='Sounds the same; clicking persisted despite full byte acceptance.'
evidence.write_text(json.dumps(d,indent=2)+'\n')
names=['emu_sfc_plus_v7_capture.c','device_audio_capture_v7.h','audio_diagnostics_v7_capture.h',
       'build-v7-capture.sh','run-v7-capture-checks.sh','adapter-check-v7-capture.c',
       'video-contract-check-v7-capture.c','harness-v7-capture.c','audio-diagnostics-check-v7.c']
for name in names:
    text=(base/name).read_text().replace('v7','v8')
    if name=='emu_sfc_plus_v7_capture.c':
        text=text.replace('#include "audio_write_audit.h"',
                          '#include "audio_write_audit_v8.h"\n#include "display_audio_test.h"')
        text=text.replace('      capture_reset(); audit_reset();',
                          '      capture_reset(); audit_reset(); display_test_reset();')
        text=text.replace('   began = diag_now();\n   /* Always copy',
                          '   unsigned mode=display_test_mode(runs);\n'
                          '   ++display_test_counts[mode];\n'
                          '   if (mode==1) {\n'
                          '      if (display_test_last!=1 && wait_display) wait_display();\n'
                          '      display_test_last=1;\n'
                          '      frontend_video(NULL,w,h,(size_t)w*2); return;\n'
                          '   }\n'
                          '   display_test_last=mode;\n'
                          '   began = diag_now();\n   /* Always copy')
        text=text.replace('   for (y = 0; y < h; ++y)\n'
                          '      memcpy(pixels + y * w, (const uint8_t *)data + y * pitch, w * 2);',
                          '   if (mode==2) memset(pixels,0,(size_t)w*h*2);\n'
                          '   else for (y = 0; y < h; ++y)\n'
                          '      memcpy(pixels + y * w, (const uint8_t *)data + y * pitch, w * 2);')
        assert 'unsigned mode=display_test_mode(runs)' in text
        text=text.replace('   bool audit_recorded = audit_save();',
                          '   bool display_saved=display_test_save();\n'
                          '   message("Display test report saved=%d normal=%u hold=%u black=%u\\n",\n'
                          '      display_saved,display_test_counts[0],display_test_counts[1],display_test_counts[2]);\n'
                          '   bool audit_recorded = audit_save();')
    if name=='harness-v7-capture.c':
        text=text.replace('   assert(retro_load_game(&game));',
                          '   setenv("D35_DISPLAY_TEST_DISABLE","1",1);\n   assert(retro_load_game(&game));')
    if name=='build-v7-capture.sh':
        text=text.replace('audio-write-audit-check.c','audio-write-audit-check-v8.c')
    (base/name.replace('v7','v8')).write_text(text,newline='\n')
(base/'audio_write_audit_v8.h').write_text((base/'audio_write_audit.h').read_text().replace('v7','v8'),newline='\n')
(base/'audio-write-audit-check-v8.c').write_text((base/'audio-write-audit-check.c').read_text().replace('v7','v8').replace('"audio_write_audit.h"','"audio_write_audit_v8.h"'),newline='\n')
print('Prepared bounded v8 display comparison, production audio unchanged.')
