"""Offline inspection of the already archived kernel; no device access.

Vendor bytes, symbols and disassembly stay in ignored device-evidence.
Requires the existing private Capstone dependency under build/lab2-inspection-tools.
"""
from pathlib import Path
import hashlib
import json
import re
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'build/lab2-inspection-tools'))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

FLASH = ROOT / 'device-evidence/snes-mvp-return-20261010T003708Z/spi-readback/offline-review/spi-nor.bin'
OUT = ROOT / 'device-evidence/uart-kernel-offline'
BASE = 0xc0008000


def inspect():
    flash = FLASH.read_bytes()
    assert len(flash) == 8388608
    assert hashlib.sha256(flash).hexdigest() == '5c4ea86ca5c497a26136ee9a59d8a31085e15c8d1dc5f063b874a20c400d9e2b'
    packed = flash[0xc0078:0xc0078 + 0x241c98]
    assert hashlib.sha256(packed).hexdigest() == 'c26d37e792948ea8a0de2e06b0bd6fcfc54e20f4d1e6cb643690276c97f271f3'
    decoder = zlib.decompressobj(31)
    data = decoder.decompress(flash[0xc4930:0x301d10], 8 * 1024 * 1024)
    assert decoder.eof and not decoder.unconsumed_tail
    assert len(data) == 7476028
    assert hashlib.sha256(data).hexdigest() == '21cc93e3f621c410ebe4174c0ab00aa4f0b21887c1698bbe974ffbeead2f0321'
    word = lambda p: struct.unpack_from('<I', data, p)[0]
    # Exact base-relative kallsyms layout. Validate every retained runtime symbol.
    start, count, names, tokens = 0x544500, 17533, 0x555720, 0x586080
    assert word(0x555700) == BASE and word(0x555710) == count
    table, cursor = [], tokens
    for _ in range(256):
        end = data.index(0, cursor)
        table.append(data[cursor:end].decode('ascii'))
        cursor = end + 1
    index = (cursor + 15) & ~15
    assert [struct.unpack_from('<H', data, index + i * 2)[0] for i in range(256)] == [sum(len(x) + 1 for x in table[:i]) for i in range(256)]
    symbols, cursor = [], names
    for i in range(count):
        size = data[cursor]
        name = ''.join(table[x] for x in data[cursor + 1:cursor + 1 + size])
        cursor += size + 1
        symbols.append((BASE + word(start + i * 4), name[0], name[1:]))
    assert cursor == 0x585f60
    retained = ROOT / 'evidence/2026-10-04/hardware-runtime-return-20261004T182651Z/kernel_symbols-0.481.txt'
    runtime = [(int(a, 16), t, n) for a, t, n in re.findall(r'^([0-9a-f]{8}) ([a-zA-Z]) (.+)$', retained.read_text(), re.M) if '\t[' not in n]
    assert runtime and all(x in symbols for x in runtime)
    OUT.mkdir(exist_ok=True)
    (OUT / 'kernel.bin').write_bytes(data)
    (OUT / 'symbols.txt').write_text(''.join(f'{a:08x} {t} {n}\n' for a, t, n in symbols))
    selected = [(i, a, n) for i, (a, t, n) in enumerate(symbols) if n.startswith(('gp_uart', 'gpHalUart')) or n in ['__handle_irq_event_percpu', 'handle_irq_event_percpu', 'irqtime_account_irq', 'account_process_tick', 'irq_enter', 'irq_exit', 'timer_init', 'hrtimers_init', 'tracefs_init', 'debugfs_init', '__const_udelay', '__timer_const_udelay', '__loop_const_udelay', 'register_console']]
    disasm, facts = [], {}
    for i, address, name in selected:
        end = next((a for a, _, _ in symbols[i + 1:] if a > address), address)
        if not BASE <= address < end <= BASE + len(data):
            continue
        block = data[address - BASE:end - BASE]
        facts[name] = {'address': hex(address), 'bytes': len(block), 'sha256': hashlib.sha256(block).hexdigest()}
        disasm.append(f'\n{name} {address:08x} size={len(block)}')
        disasm.extend(f'{x.address:08x} {x.mnemonic:9} {x.op_str}' for x in Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(block, address))
    (OUT / 'disassembly.txt').write_text('\n'.join(disasm) + '\n')
    result = {'kernel_sha256': hashlib.sha256(data).hexdigest(), 'symbol_count': count, 'runtime_symbols_matched': len(runtime), 'functions': facts,
              'trace_related_symbols': [n for _, _, n in symbols if any(x in n for x in ['tracefs', 'ftrace', 'irqtime', 'kprobe', 'tracing_', 'perf_trace', 'hrtimer', 'jiffy'])],
              'boundary': 'Offline code inspection only. No measured A7 duration or observed interrupt status register.'}
    (OUT / 'inspection.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    inspect()
