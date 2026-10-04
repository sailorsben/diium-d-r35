from pathlib import Path

p = Path(__file__).resolve().parent
s = (p/'build-v2.sh').read_text().replace('v2', 'v3-diagnostic')
s = s.replace('emu_sfc_plus_v3-diagnostic.c', 'emu_sfc_plus_v3_diag.c')
s = s.replace('adapter-check-v3-diagnostic.c', 'adapter-check-v3-diag.c')
s = s.replace('video-contract-check.c', 'video-contract-check-v3-diag.c')
s += '''arm-linux-gnueabihf-gcc $flags -O2 -Wall -Wextra -Werror -no-pie -nostdlib \\
 /usr/arm-linux-gnueabihf/lib/crt1.o audio-diagnostics-check.c -L./sysroot/lib -Wl,--no-as-needed \\
 -l:libdl-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1 -o v3-diagnostic/audio-diagnostics-check-arm
'''
(p/'build-v3-diag.sh').write_bytes(s.encode())
for old, new in [('adapter-check-v2.c', 'adapter-check-v3-diag.c'),
                 ('video-contract-check.c', 'video-contract-check-v3-diag.c')]:
    (p/new).write_text((p/old).read_text().replace('emu_sfc_plus_v2.c', 'emu_sfc_plus_v3_diag.c'))
s = (p/'run-v2-checks.sh').read_text().replace('v2', 'v3-diagnostic')
s = s.replace('export D35_PLUS_LOG=',
              'export D35_TIMING_LOG="$base/v3-diagnostic/verification/timing.log"\nexport D35_PLUS_LOG=')
s += '''qemu-arm -cpu cortex-a7 -L "$base/sysroot" -E LD_LIBRARY_PATH="$base/sysroot/lib" \\
 "$base/v3-diagnostic/audio-diagnostics-check-arm"
'''
(p/'run-v3-diag-checks.sh').write_bytes(s.encode())
