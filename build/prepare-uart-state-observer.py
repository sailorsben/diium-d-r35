"""Generate private exact-kernel guards and recovered export metadata.

No device access. Recovered CRCs identify existing code; they are not a
cryptographic attestation of a live kernel or a substitute for ABI checks.
"""
from pathlib import Path
import hashlib
import json
import re
import struct
import zlib

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'build/uart-kernel-private'
BASE = 0xc0008000


def main():
    data = (ROOT / 'device-evidence/uart-kernel-offline/kernel.bin').read_bytes()
    assert hashlib.sha256(data).hexdigest() == '21cc93e3f621c410ebe4174c0ab00aa4f0b21887c1698bbe974ffbeead2f0321'
    symbols = [(int(a, 16), t, n) for a, t, n in re.findall(r'^([0-9a-f]{8}) (.) (.+)$',
               (ROOT / 'device-evidence/uart-kernel-offline/symbols.txt').read_text(), re.M)]
    by_name = {n: (i, a) for i, (a, _, n) in enumerate(symbols)}
    guards = []
    for name in ['gp_uart_isr', 'gp_uart_start_tx', 'gp_uart_stop_tx', 'gp_uart_probe',
                 'gp_uart_console_write', 'gpHalUartGetCtrl', 'irq_to_desc']:
        i, address = by_name[name]
        end = next(a for a, _, _ in symbols[i + 1:] if a > address)
        block = data[address - BASE:end - BASE]
        guards.append({'name': name, 'address': address, 'bytes': len(block),
                       'crc32': zlib.crc32(block), 'sha256': hashlib.sha256(block).hexdigest()})
    assert max(g['bytes'] for g in guards) <= 1024
    header = ['/* Generated exact-image metadata; no vendor instruction bytes. */',
              '#define D35_GUARD_MAX 1024',
              'struct d35_guard { unsigned int address, size, crc; };',
              'static const struct d35_guard d35_guards[] = {']
    header += [f'    {{ 0x{g["address"]:08x}u, {g["bytes"]}u, 0x{g["crc32"]:08x}u }}, /* {g["name"]} */' for g in guards]
    header += ['};', '']
    OUT.mkdir(exist_ok=True)
    (OUT / 'uart-state-guards.h').write_text('\n'.join(header))
    # This ARM kernel stores absolute value/name pairs, including export tables.
    # Require both a valid identifier and a matching decoded text symbol value.
    known = {n: a for a, _, n in symbols}
    exports = {}
    for off in range(0x5d0000, 0x5d9000, 4):
        value, ptr = struct.unpack_from('<II', data, off)
        pos = ptr - BASE
        if not 0 <= pos < len(data):
            continue
        end = data.find(b'\0', pos, pos + 160)
        if end < pos:
            continue
        name = data[pos:end].decode('ascii', errors='replace')
        if re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', name) and known.get(name) == value:
            exports[name] = value
    required = ['kallsyms_lookup_name', 'probe_kernel_read', 'proc_create_single_data',
                'remove_proc_entry', 'seq_printf', 'ktime_get']
    assert all(n in exports for n in required)
    # Modversions is absent. GPL classification is conservative for this GPL module.
    (OUT / 'Module.symvers').write_text(''.join(f'0x00000000\t{n}\tvmlinux\tEXPORT_SYMBOL_GPL\n' for n in sorted(exports)))
    result = {'kernel_sha256': hashlib.sha256(data).hexdigest(), 'guards': guards,
              'recovered_text_exports': len(exports),
              'required_exports': {n: hex(exports[n]) for n in required},
              'abi_source_sha256': hashlib.sha256((ROOT / 'build/uart-observer-abi.c').read_bytes()).hexdigest(),
              'observer_source_sha256': hashlib.sha256((ROOT / 'build/uart-state-observer.c').read_bytes()).hexdigest(),
              'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'card_access': False, 'live_qualification': False}
    (OUT / 'prepared.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
