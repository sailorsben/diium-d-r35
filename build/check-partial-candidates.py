"""Independent scalar tile and mask oracles for isolated alternatives; no timing."""
from pathlib import Path
import subprocess,json,sys
from hashlib import sha256
ROOT=Path(__file__).resolve().parent.parent
SELECTIVE=sys.argv[1:]==['--selective']
assert sys.argv[1:] in ([],['--selective'])
OUT=ROOT/('build/partial-selective-private-v1' if SELECTIVE else 'build/partial-candidates-private-v1')
NAMES=('selective',) if SELECTIVE else ('local','sparse')
def main():
 assert not (OUT/'kernel-check.log').exists()
 flags='-DUSE_BLARGG_APU -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
 libs='-Lbuild/sysroot/lib -Wl,--no-as-needed -l:libz.so.1 -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1'
 sh='#!/bin/sh\nset -eu\nulimit -c 0\ncd "$(dirname "$0")/../.."\n'
 if SELECTIVE:
  old=ROOT/'build/partial-candidates-private-v1';assert json.loads((old/'oracles.json').read_text())['passed']
  (OUT/'kernel-check.log').write_bytes((old/'kernel-check.log').read_bytes())
 else:
  sh+=f'arm-linux-gnueabihf-gcc {flags} -std=gnu99 -O3 -Wall -Wextra -Werror -no-pie -nostdlib -Ibuild /usr/arm-linux-gnueabihf/lib/crt1.o build/partial-merge-kernel-check.c {libs} -o "{OUT.relative_to(ROOT)}/kernel-check"\n'
  sh+=f'LD_LIBRARY_PATH=build/sysroot/lib qemu-arm -cpu cortex-a7 -L build/sysroot "{OUT.relative_to(ROOT)}/kernel-check" > "{OUT.relative_to(ROOT)}/kernel-check.log"\n'
 for name in NAMES:
  src=(ROOT/'build/common-band-private-v3/tile-check.c').read_text().replace('common-band-private-v3/core/source/',f'{OUT.name}/{name}/source/');(OUT/f'{name}-tile-check.c').write_text(src,newline='\n')
  sh+=f'arm-linux-gnueabihf-gcc {flags} -DD35_CLIPPING_CANDIDATE -std=gnu99 -O3 -Wall -Wextra -Werror -Wno-sign-compare -Wno-implicit-fallthrough -no-pie -nostdlib -Ibuild -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o "{OUT.relative_to(ROOT)}/{name}-tile-check.c" {libs} -o "{OUT.relative_to(ROOT)}/{name}-tile-check"\n'
  sh+=f'LD_LIBRARY_PATH=build/sysroot/lib qemu-arm -cpu cortex-a7 -L build/sysroot "{OUT.relative_to(ROOT)}/{name}-tile-check" > "{OUT.relative_to(ROOT)}/{name}-tile.crc" 2> "{OUT.relative_to(ROOT)}/{name}-tile.log"\n'
  sh+=f'cmp build/common-band-private-v3/clipping-original.crc "{OUT.relative_to(ROOT)}/{name}-tile.crc"\n'
 (OUT/'check.sh').write_text(sh,newline='\n');subprocess.run(['sh',str(OUT/'check.sh')],cwd=ROOT,check=True)
 print((OUT/'kernel-check.log').read_text().strip())
 for name in NAMES:print(name,(OUT/f'{name}-tile.log').read_text().strip())
 result={'passed':True,'mask_cases':32768,'candidate_scalar_tile_cases':len(NAMES)*129024,'unchanged_mask_kernel_proof_reused':SELECTIVE,'QEMU_timing_used':False,'unchanged_original_scalar_reference_sha256':sha256((ROOT/'build/common-band-private-v3/clipping-original.crc').read_bytes()).hexdigest()};(OUT/'oracles.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
