"""Original scalar oracle for fused policy states, sole layer, and palette ownership."""
from pathlib import Path
from hashlib import sha256
import json,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
V2=sys.argv[1:]==['--v2']
assert sys.argv[1:] in ([],['--v2'])
OUT=ROOT/('build/fused-toolbox-private-v2' if V2 else 'build/fused-toolbox-private-v1')
def main():
 assert not (OUT/'oracles.json').exists();src=(ROOT/'build/common-band-private-v3/tile-check.c').read_text().replace('common-band-private-v3/core/source/',OUT.name+'/core/source/')
 src=src.replace('c.mode=', 'c.depth_policy=D35_TEST_POLICY;c.mode=')
 (OUT/'tile-check.c').write_text(src,newline='\n')
 sole=src.replace('bits<=4','bits<=2').replace('mode<7','mode<1').replace('GFX.S=GFX.Screen;','GFX.S=GFX.SubScreen;').replace('GFX.DB=GFX.ZBuffer;','GFX.DB=GFX.SubZBuffer;')
 sole=sole.replace('assert(d35_batch_tile(&c,t,o,l,n))','assert(d35_fused_sole(&c,t,o,l,n))')
 (OUT/'sole-check.c').write_text(sole,newline='\n')
 flags='-DUSE_BLARGG_APU -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32'
 libs='-Lbuild/sysroot/lib -Wl,--no-as-needed -l:libz.so.1 -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1'
 sh='#!/bin/sh\nset -eu\nulimit -c 0\ncd "$(dirname "$0")/../.."\n'
 jobs=[('tile-check.c','tile-policy'+str(n),f'-DD35_CLIPPING_CANDIDATE -DD35_TEST_POLICY={n}') for n in range(3)]+[('sole-check.c','sole-original','-DD35_TEST_POLICY=0'),('sole-check.c','sole-candidate','-DD35_CLIPPING_CANDIDATE -DD35_TEST_POLICY=0')]
 for file,label,define in jobs:
  sh+=f'arm-linux-gnueabihf-gcc {flags} {define} -std=gnu99 -O3 -Wall -Wextra -Werror -Wno-sign-compare -Wno-implicit-fallthrough -no-pie -nostdlib -Ibuild -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o "{OUT.relative_to(ROOT)}/{file}" {libs} -o "{OUT.relative_to(ROOT)}/{label}"\n'
  sh+=f'LD_LIBRARY_PATH=build/sysroot/lib qemu-arm -cpu cortex-a7 -L build/sysroot "{OUT.relative_to(ROOT)}/{label}" > "{OUT.relative_to(ROOT)}/{label}.crc" 2> "{OUT.relative_to(ROOT)}/{label}.log"\n'
  if label.startswith('tile-'):sh+=f'cmp build/common-band-private-v3/clipping-original.crc "{OUT.relative_to(ROOT)}/{label}.crc"\n'
 sh+=f'cmp "{OUT.relative_to(ROOT)}/sole-original.crc" "{OUT.relative_to(ROOT)}/sole-candidate.crc"\n'
 (OUT/'check.sh').write_text(sh,newline='\n');subprocess.run(['sh',str(OUT/'check.sh')],cwd=ROOT,check=True)
 for _,label,_ in jobs:print(label,(OUT/f'{label}.log').read_text().strip())
 q={'passed':True,'policy_scalar_cases':3*129024,'sole_scalar_cases':9216,'prior_scalar_reference_sha256':sha256((ROOT/'build/common-band-private-v3/clipping-original.crc').read_bytes()).hexdigest(),'QEMU_timings_used':False,'production_gate_passed':False}
 (OUT/'oracles.json').write_text(json.dumps(q,indent=2)+'\n')
if __name__=='__main__':main()
