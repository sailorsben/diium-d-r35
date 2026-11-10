"""Bind the vendor fill fixture to the physically read-back kernel (offline only)."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import zlib


ROOT = Path(__file__).resolve().parent.parent
BASE = 0xc0008000


def digest(data):
    return sha256(data).hexdigest()


def main(out):
    proof = json.loads((ROOT/'evidence/2026-10-17/uart-kernel-reflash/verified-return.json').read_text())
    flash = (ROOT/'device-evidence/uart-kernel-firmware1/expected-after-vendor.bin').read_bytes()
    assert digest(flash)=='ef69753afb56c84e4daaf78aa3fad5551d26b7438e49f4f1dbc7312b11e07321'
    kernel = zlib.decompress(flash[0xc0078+0x48b8:0x301d10],31)
    assert digest(kernel)==proof['kernel_sha256']=='b1fe94004b84cbf8ee0ec3367466598bc9c8dd1cbfa9f55ae9373bbc6eefa459'
    before = (ROOT/'device-evidence/uart-kernel-offline/kernel.bin').read_bytes()
    assert digest(before)=='21cc93e3f621c410ebe4174c0ab00aa4f0b21887c1698bbe974ffbeead2f0321'
    functions = {}
    for name, a, b in [('dma_prepare',0xc03e24f4,0xc03e2550),('dma_fill_silence',0xc03e25e8,0xc03e2774),
                       ('kernel_ioctl',0xc03bdda0,0xc03bdf00),('do_pcm_hwsync',0xc03bb374,0xc03bb3e8),
                       ('update_hw_ptr',0xc03c2898,0xc03c2c70),('playback_silence',0xc03c24ac,0xc03c26bc)]:
        body=kernel[a-BASE:b-BASE]
        assert body==before[a-BASE:b-BASE]
        functions[name]=dict(start=hex(a),end_exclusive=hex(b),sha256=digest(body))
    source=ROOT/'build/check-vendor-pcm-fill.c'
    with TemporaryDirectory(prefix='d35-pcm-fill-') as temp:
        d=Path(temp)
        (d/'kernel.bin').write_bytes(kernel)
        subprocess.run(['arm-linux-gnueabihf-gcc','-O2','-marm','-mcpu=cortex-a7','-Wall','-Wextra','-Werror',
                        '-no-pie',str(source),'-o',str(d/'fixture')],check=True)
        result=subprocess.check_output(['qemu-arm','-cpu','cortex-a7','-L','/usr/arm-linux-gnueabihf',
                                        str(d/'fixture'),str(d/'kernel.bin')],text=True).strip()
    assert result.startswith('PASS exact ARM vendor fill and ioctl dispatch:')
    out.write_text(json.dumps(dict(kernel_sha256=digest(kernel),stock_kernel_sha256=digest(before),
                    unchanged_code_ranges=functions,source_sha256=digest(source.read_bytes()),
                    result=result,device_executed=False,stubs=['clock','memcpy','low-level DROP','mutex lock/unlock']),indent=2)+'\n')
    print(result)


if __name__=='__main__':
    main(Path(sys.argv[1]))
