"""Prove the changed-device counterexample rejects immutable shipped1.10."""
from pathlib import Path
from hashlib import sha256
import json, resource, subprocess

root=Path(__file__).resolve().parent.parent
out=root/'build/snes-mvp/out'
old=subprocess.check_output(['git','show','724bc253e74d7d7d98a05ed97ce2c35b6da8d938:build/snes-mvp/audio-owner.c'],cwd=root)
release=json.loads((root/'releases/snes-mvp-1.10/manifest.json').read_text())
assert sha256(old).hexdigest()==release['source_hashes']['build/snes-mvp/audio-owner.c']
(out/'audio-owner-1.10.c').write_bytes(old)
fixture=(root/'build/snes-mvp/audio-owner-check.c').read_text().replace('#include "audio-owner.c"','#include "audio-owner-1.10.c"')
(out/'old-owner-regression.c').write_text(fixture)
flags='-mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -U_TIME_BITS -D_TIME_BITS=32 -U_FILE_OFFSET_BITS -D_FILE_OFFSET_BITS=32 -O2 -std=gnu99 -Wall -Wextra -Werror -no-pie -nostdlib'.split()
subprocess.run(['arm-linux-gnueabihf-gcc',*flags,'-Ibuild/snes-mvp','/usr/arm-linux-gnueabihf/lib/crt1.o',
    'build/snes-mvp/out/old-owner-regression.c','-Lbuild/sysroot/lib','-Wl,--no-as-needed',
    '-l:libpthread-2.30.so','-l:libc-2.30.so','-l:libgcc_s.so.1','-l:ld-2.30.so',
    '-o','build/snes-mvp/out/old-owner-regression'],cwd=root,check=True)
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
result=subprocess.run(['timeout','12','qemu-arm','-cpu','cortex-a7','-L','build/sysroot',
    '-E','LD_LIBRARY_PATH=build/sysroot/lib','build/snes-mvp/out/old-owner-regression'],cwd=root,
    stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
assert result.returncode!=0 and b'!admission_done' in result.stdout,result.stdout.decode()
proof='PASS: shipped1.10 admits on cached32 despite actual128 frames; repaired owner waits for a fresh sample\n'
(out/'old-owner-regression.log').write_bytes(result.stdout+proof.encode())
print(proof,end='')
