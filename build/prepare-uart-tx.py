"""Derive exact-image guards; publish no vendor instruction bytes."""
from pathlib import Path
from hashlib import sha256
import json
import re
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'build/uart-tx-private'
sys.path.insert(0, str(ROOT / 'build/lab2-inspection-tools'))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM


def main():
    data = (ROOT / 'device-evidence/uart-kernel-offline/kernel.bin').read_bytes()
    assert sha256(data).hexdigest() == '21cc93e3f621c410ebe4174c0ab00aa4f0b21887c1698bbe974ffbeead2f0321'
    symbols = [(int(a, 16), n) for a, _, n in re.findall(r'^([0-9a-f]{8}) (.) (.+)$',
        (ROOT / 'device-evidence/uart-kernel-offline/symbols.txt').read_text(), re.M)]
    names = {name: i for i, (_, name) in enumerate(symbols)}
    old = json.loads((ROOT / 'build/uart-kernel-private/prepared.json').read_text())
    guards = list(old['guards'])
    for name in ['gpHalUartGetIntSts', '__handle_irq_event_percpu', 'synchronize_irq', 'try_module_get', 'module_put', 'gpHalUartPutChar', 'uart_write_wakeup']:
        i = names[name]; address = symbols[i][0]
        end = next(a for a, _ in symbols[i + 1:] if a > address)
        block = data[address - 0xc0008000:end - 0xc0008000]
        guards.append({'name': name, 'address': address, 'bytes': len(block),
            'crc32': zlib.crc32(block), 'sha256': sha256(block).hexdigest()})
    for g in guards:
        block = data[g['address'] - 0xc0008000:g['address'] - 0xc0008000 + g['bytes']]
        assert sha256(block).hexdigest() == g['sha256'] and zlib.crc32(block) == g['crc32']
    decoded = list(Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(data[0x10f7dc:0x10f800], 0xc01177dc))
    assert [(x.mnemonic, x.op_str) for x in decoded[:8]] == [
        ('mov', 'ip, sp'), ('push', '{r4, r5, r6, r7, r8, fp, ip, lr, pc}'),
        ('sub', 'fp, ip, #4'), ('sub', 'sp, sp, #0xc'), ('ldr', 'r0, [r1, #4]'),
        ('mov', 'r4, r1'), ('bl', '#0xc0117314'), ('tst', 'r0, #0xa000')]
    assert decoded[7].address == 0xc01177f8
    research=json.loads((ROOT/'evidence/2026-10-15/uart-source-contract/research.json').read_text())
    headers=[]
    for name in ['freexyz-gpl32-drv_l1_uart.h','davidgiven-gp32-sdk-uart_hw.h','gpm4-drv_l1_uart.h']:
        path=ROOT/'device-evidence/uart-source-research'/name
        raw=path.read_bytes();expected=next(x for x in research['external_sources'] if x['sha256']==sha256(raw).hexdigest())
        assert re.search(rb'C_UART_STATUS_TX_FULL\s*(?:=\s*)?0x00000020',raw)
        headers.append({'name':name,'sha256':expected['sha256'],'url':expected['url']})
    OUT.mkdir(exist_ok=True)
    maximum = max(g['bytes'] for g in guards)
    assert maximum <= 2048
    header = [f'#define D35_GUARD_MAX {maximum}',
        'struct d35_guard { unsigned int address, size, crc; };',
        'static const struct d35_guard d35_guards[] = {']
    header += [f'{{0x{g["address"]:08x}u,{g["bytes"]}u,0x{g["crc32"]:08x}u}}, /* {g["name"]} */' for g in guards]
    header += ['};', '']
    (OUT / 'uart-tx-guards.h').write_bytes('\n'.join(header).encode())
    (OUT / 'Module.symvers').write_bytes((ROOT / 'build/uart-kernel-private/Module.symvers').read_bytes())
    report = {'kernel_sha256': sha256(data).hexdigest(), 'guards': guards,
        'verified_entry_instructions': 8, 'resume_address': '0xc01177f8',
        'extra_status_reads': 0, 'new_path_max_writes_per_irq': 1, 'runtime_fifo_size_required': 8, 'TX_full_mask': 32, 'kernel_text_patches': 0, 'physical_result': 'PENDING', 'FIFO_full_flag_sources':headers, 'physical_FIFO_flag_semantics_proven':False}
    (OUT / 'prepared.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'guards': len(guards), 'max_bytes': maximum, 'entry_verified': True}))


if __name__ == '__main__':
    main()
