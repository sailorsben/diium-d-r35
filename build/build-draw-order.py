"""Compile one immutable non-LTO APU object and reuse it in both variants."""
from pathlib import Path
from hashlib import sha256
import json, shutil, subprocess

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'build/draw-order-private-v1'
FLAGS = '-DD35_PLUS_A7 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -D_TIME_BITS=32 -D_FILE_OFFSET_BITS=32'

def digest(p):
    return sha256(p.read_bytes()).hexdigest()

def main():
    args = ['make', '-j3', 'platform=unix', 'USE_BLARGG_APU=1', 'LOAD_FROM_MEMORY=1', 'GIT_VERSION=" 7f3528e"',
            'CC=arm-linux-gnueabihf-gcc ' + FLAGS,
            'SHARED=-shared -nostdlib -flto=4 -O3 -Wl,-Bsymbolic-functions -Wl,--no-undefined -Wl,--version-script=link.T',
            'LDFLAGS=-L../../sysroot/lib -Wl,--no-as-needed -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1']
    boundary = OUT / 'boundary'
    with (OUT / 'apu-build.log').open('x') as f:
        subprocess.run([*args[:1], 'source/apu_blargg.o', *args[1:]], cwd=boundary, stdout=f, stderr=subprocess.STDOUT, check=True)
    apu = boundary / 'source/apu_blargg.o'
    pinned = digest(apu)
    assert '-fno-lto' in (OUT / 'apu-build.log').read_text()
    shutil.copy2(apu, OUT / 'priority/source/apu_blargg.o')
    cores = {}
    for label in ('boundary', 'priority'):
        core = OUT / label
        with (OUT / (label + '-build.log')).open('x') as f:
            subprocess.run(args, cwd=core, stdout=f, stderr=subprocess.STDOUT, check=True)
        assert digest(core / 'source/apu_blargg.o') == pinned, label
        cores[label] = digest(core / 'snes9x2005_plus_libretro.so')
        print('Built', label, cores[label], 'fixed APU', pinned, flush=True)
    libs = ['-Lbuild/sysroot/lib', '-Wl,--no-as-needed', '-l:libdl-2.30.so', '-l:libz.so.1', '-l:libpthread-2.30.so',
            '-l:librt-2.30.so', '-l:libm-2.30.so', '-l:libc-2.30.so', '-l:libgcc_s.so.1', '-l:ld-2.30.so']
    command = ['arm-linux-gnueabihf-gcc', *FLAGS.split(), '-DUSE_BLARGG_APU', '-O2', '-std=gnu99', '-Wall', '-Wextra', '-Werror',
               '-no-pie', '-nostdlib', '-Ibuild', '-I' + str(OUT), '-Ibuild/snes9x2005/libretro-common/include',
               '/usr/arm-linux-gnueabihf/lib/crt1.o', str(OUT / 'compare.c'), *libs, '-o', str(OUT / 'compare')]
    subprocess.run(command, cwd=ROOT, check=True)
    for n, h in json.loads((OUT / 'frozen.json').read_text()).items():
        assert digest(ROOT / n) == h, n
    (OUT / 'build-identity.json').write_text(json.dumps({'APU_object_sha256': pinned, 'cores': cores,
        'APU_object_byte_identical': True, 'APU_source_unchanged': True, 'ordinary_no_work_observers': True}, indent=2) + '\n')

if __name__ == '__main__':
    main()
