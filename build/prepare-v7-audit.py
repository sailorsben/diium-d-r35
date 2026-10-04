from pathlib import Path
import json
base=Path(__file__).resolve().parent
evidence=base.parent/'device-evidence/card-D-v6-return/analysis.json'
report=json.loads(evidence.read_text())
report['user_listening_result']='The recorded audio sounds clean on the PC; clicks were audible on handheld.'
evidence.write_text(json.dumps(report,indent=2)+'\n')
names=['emu_sfc_plus_v6_capture.c','device_audio_capture_v6.h','audio_diagnostics_v6_capture.h',
       'build-v6-capture.sh','run-v6-capture-checks.sh','adapter-check-v6-capture.c',
       'video-contract-check-v6-capture.c','harness-v6-capture.c','audio-diagnostics-check-v6.c']
for name in names:
    text=(base/name).read_text().replace('v6','v7')
    if name=='emu_sfc_plus_v6_capture.c':
        text=text.replace('#include "audio_diagnostics_v7_capture.h"',
                          '#include "audio_diagnostics_v7_capture.h"\n#include "audio_write_audit.h"')
        text=text.replace('   if (frontend_batch) frontend_batch(output, output_count);\n'
                          '   else if (frontend_audio)\n'
                          '      for (i = 0; i < output_count; ++i)\n'
                          '         frontend_audio(output[i * 2], output[i * 2 + 1]);',
                          '   if (!audit_deliver(output,output_count,(uint32_t)runs+1)) {\n'
                          '      if (frontend_batch) frontend_batch(output, output_count);\n'
                          '      else if (frontend_audio)\n'
                          '         for (i = 0; i < output_count; ++i)\n'
                          '            frontend_audio(output[i * 2], output[i * 2 + 1]);\n'
                          '   }')
        assert 'audit_deliver(output' in text
        text=text.replace('      capture_reset();','      capture_reset(); audit_reset();')
        text=text.replace('   bool recorded = capture_write();',
                          '   bool audit_recorded = audit_save();\n'
                          '   message("Write audit saved=%d driver_calls=%llu errors=%u short=%u zero=%u fallback=%llu\\n",\n'
                          '      audit_recorded,(unsigned long long)audited_calls,audited_errors,audited_short,\n'
                          '      audited_zero,(unsigned long long)audited_fallback);\n'
                          '   bool recorded = capture_write();')
    (base/name.replace('v6','v7')).write_text(text,newline='\n')
# The standalone mock exercises the actual driver branch; FF3/QEMU uses fallback.
path=base/'build-v7-capture.sh'
text=path.read_text()+'''arm-linux-gnueabihf-gcc $flags -O2 -Wall -Wextra -Werror -no-pie -nostdlib \\
 /usr/arm-linux-gnueabihf/lib/crt1.o audio-write-audit-check.c -L./sysroot/lib -Wl,--no-as-needed \\
 -l:libdl-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1 -o v7-capture/audio-write-audit-check-arm
'''
path.write_text(text,newline='\n')
path=base/'run-v7-capture-checks.sh'
path.write_text(path.read_text()+'''qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/sysroot/lib" \\
 "$base/v7-capture/audio-write-audit-check-arm"
''',newline='\n')
print('Prepared v7 write-return diagnostic without PCM/rate changes.')
