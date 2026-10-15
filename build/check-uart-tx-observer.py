"""Execute the compiled observer offline and check independently observed ABI.

The flat ELF relocation fixture is not a replacement kernel module loader and
does not prove insmod/unload on the handheld. Outputs and vendor bytes stay private.
"""
from pathlib import Path
from hashlib import sha256
import json
import os
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'build/uart-tx-private'
sys.path.insert(0, str(ROOT / 'build/lab2-inspection-tools'))
from elftools.elf.elffile import ELFFile


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def inspect_abi():
    with (ROOT / 'build/uart-kernel-private/d35_uart_abi.ko').open('rb') as stream:
        elf = ELFFile(stream)
        symbol = elf.get_section_by_name('.symtab').get_symbol_by_name('d35_abi_layout')[0]
        data = elf.get_section(symbol['st_shndx']).data()[symbol['st_value']:symbol['st_value'] + symbol['st_size']]
        values = struct.unpack('<' + 'I' * (len(data) // 4), data)
        expected = (448, 12, 232, 416, 256, 304, 352, 372, 396, 420, 264, 4, 72, 100, 120, 124, 184, 192)
        assert values == expected, values
        info = elf.get_section_by_name('.modinfo').data().decode().split('\0')
        assert 'vermagic=4.19.128 mod_unload ARMv7 p2v8 ' in info
    return list(values)


def relocate(fixture):
    with fixture.open('rb') as stream:
        harness = ELFFile(stream)
        imported = {s.name: s['st_value'] for s in harness.get_section_by_name('.symtab').iter_symbols() if s['st_shndx'] != 'SHN_UNDEF'}
    aliases = {'kallsyms_lookup_name': 'fixture_lookup', 'probe_kernel_read': 'fixture_read',
               'proc_create_single_data': 'fixture_proc', 'remove_proc_entry': 'fixture_remove',
               'seq_printf': 'fixture_printf', 'ktime_get': 'fixture_clock',
               'try_module_get': 'fixture_get', 'module_put': 'fixture_put', 'synchronize_irq': 'fixture_sync',
               'memcpy': 'fixture_copy'}
    with (OUT / 'd35_uart_tx.ko').open('rb') as stream:
        elf = ELFFile(stream)
        assert elf['e_type'] == 'ET_REL' and elf['e_machine'] == 'EM_ARM'
        image = bytearray(0x100000)
        addresses, cursor = {}, 0
        for index, section in enumerate(elf.iter_sections()):
            if not section['sh_flags'] & 2:
                continue
            align = max(4, section['sh_addralign'])
            cursor = (cursor + align - 1) & ~(align - 1)
            addresses[index] = 0x01000000 + cursor
            if section['sh_type'] != 'SHT_NOBITS':
                image[cursor:cursor + section['sh_size']] = section.data()
            cursor += section['sh_size']
        assert cursor < len(image)
        symbols = elf.get_section_by_name('.symtab')
        unrelocated = bytes(image[:cursor])
        def resolve(symbol):
            section = symbol['st_shndx']
            if section == 'SHN_UNDEF':
                name = aliases.get(symbol.name, symbol.name)
                assert name in imported, symbol.name
                return imported[name]
            if section == 'SHN_ABS':
                return symbol['st_value']
            assert section in addresses, (symbol.name, section)
            return addresses[section] + symbol['st_value']
        kinds, undefined = set(), set()
        for section in elf.iter_sections():
            if section['sh_type'] != 'SHT_REL' or section['sh_info'] not in addresses:
                continue
            for relocation in section.iter_relocations():
                kind = relocation['r_info_type']
                kinds.add(kind)
                if kind in (0, 40):
                    continue
                symbol = symbols.get_symbol(relocation['r_info_sym'])
                if symbol['st_shndx'] == 'SHN_UNDEF':
                    undefined.add(symbol.name)
                target = resolve(symbol)
                place = addresses[section['sh_info']] + relocation['r_offset']
                off = place - 0x01000000
                word = struct.unpack_from('<I', image, off)[0]
                if kind == 2:
                    result = word + target
                elif kind == 3:
                    result = word + target - place
                elif kind in (1, 28, 29):
                    addend = (word & 0xffffff) << 2
                    if addend & 0x2000000:
                        addend -= 0x4000000
                    delta = target + addend - place
                    assert not target & 3 and not delta & 3 and -0x2000000 <= delta < 0x2000000, (symbol.name, hex(target), hex(place), hex(delta))
                    result = (word & 0xff000000) | ((delta >> 2) & 0xffffff)
                elif kind in (43, 44):
                    addend = ((word >> 4) & 0xf000) | (word & 0xfff)
                    value = target + (addend << 16 if kind == 44 else addend)
                    immediate = (value >> 16 if kind == 44 else value) & 0xffff
                    result = (word & ~0xf0fff) | ((immediate & 0xf000) << 4) | (immediate & 0xfff)
                elif kind == 42:
                    addend = word & 0x7fffffff
                    if addend & 0x40000000:
                        addend -= 0x80000000
                    result = (word & 0x80000000) | ((target + addend - place) & 0x7fffffff)
                else:
                    raise AssertionError(('Unsupported relocation', kind))
                struct.pack_into('<I', image, off, result & 0xffffffff)
        exports = {name: resolve(symbols.get_symbol_by_name(name)[0]) for name in ['init_module', 'cleanup_module']}
        # Independent seam: feed the same unrelocated sections/resolved symbols
        # to the actual archived ARM apply_relocate implementation in QEMU.
        raw = (OUT / 'd35_uart_tx.ko').read_bytes()
        meta = bytearray(0x100000)
        section_count = elf['e_shnum']
        meta[:section_count * 40] = raw[elf['e_shoff']:elf['e_shoff'] + section_count * 40]
        pos = (section_count * 40 + 15) & ~15
        all_addresses = dict(addresses)
        for i, section in enumerate(elf.iter_sections()):
            if i not in all_addresses:
                all_addresses[i] = 0x03000000 + pos
                block = section.data() if section['sh_type'] != 'SHT_NOBITS' else bytes(section['sh_size'])
                meta[pos:pos + len(block)] = block
                pos = (pos + len(block) + 15) & ~15
            struct.pack_into('<I', meta, i * 40 + 12, all_addresses[i])
        symindex = next(i for i, s in enumerate(elf.iter_sections()) if s.name == '.symtab')
        symoff = all_addresses[symindex] - 0x03000000
        for i, symbol in enumerate(symbols.iter_symbols()):
            if symbol['st_shndx'] == 'SHN_UNDEF':
                value = imported.get(aliases.get(symbol.name, symbol.name), 0)
            elif symbol['st_shndx'] == 'SHN_ABS':
                value = symbol['st_value']
            else:
                value = all_addresses[symbol['st_shndx']] + symbol['st_value']
            struct.pack_into('<I', meta, symoff + i * 16 + 4, value)
        relindices = [i for i, s in enumerate(elf.iter_sections()) if s['sh_type'] == 'SHT_REL' and s['sh_info'] in addresses]
        (OUT / 'observer-meta.bin').write_bytes(struct.pack('<III', section_count, symindex, len(relindices)) +
                                                  struct.pack('<' + 'I' * len(relindices), *relindices) + meta[:pos])
        (OUT / 'observer-unrelocated.bin').write_bytes(unrelocated)
    (OUT / 'observer-flat.bin').write_bytes(image[:cursor])
    return {'entry_points': exports, 'relocation_types': sorted(kinds), 'undefined_symbols': sorted(undefined),
            'actual_kernel_relocator_address': '0xc010de00'}


def main():
    layout = inspect_abi()
    tool = ['wsl', '--exec'] if os.name == 'nt' else []
    binary = 'build/uart-tx-private/check-observer'
    subprocess.run(tool + ['arm-linux-gnueabihf-gcc', '-O2', '-Wall', '-Wextra', '-Werror', '-marm', '-no-pie', '-static',
                          'build/check-uart-tx-observer.c', '-o', binary], cwd=ROOT, check=True, capture_output=True)
    relocated = relocate(ROOT / binary)
    command = ['qemu-arm', binary, 'device-evidence/uart-kernel-offline/kernel.bin',
               'build/uart-tx-private/observer-flat.bin', hex(relocated['entry_points']['init_module']),
               hex(relocated['entry_points']['cleanup_module']),
               'build/uart-tx-private/observer-unrelocated.bin', 'build/uart-tx-private/observer-meta.bin']
    run = subprocess.run(tool + command, cwd=ROOT, capture_output=True, text=True)
    (OUT / 'execution.txt').write_text(run.stdout + run.stderr)
    assert run.returncode == 0, (run.returncode, run.stdout, run.stderr)
    assert 'UART TX compiled checks passed' in run.stdout
    report = {'kind': 'offline_compiled_uart_tx_observer', 'checks': run.stdout.splitlines()[:-1],
              'observed_abi_values': layout, 'relocations': relocated,
              'observer_module_sha256': digest(OUT / 'd35_uart_tx.ko'),
              'abi_module_sha256': digest(ROOT / 'build/uart-kernel-private/d35_uart_abi.ko'),
              'configuration_sha256': digest(OUT / 'reconstructed.config'),
              'sources': {str(p.relative_to(ROOT)).replace('\\', '/'): digest(p) for p in [
                  ROOT / 'build/uart-tx-observer.c', ROOT / 'build/uart-observer-abi.c',
                  ROOT / 'build/prepare-uart-tx.py', ROOT / 'build/build-uart-tx.sh',
                  ROOT / 'build/check-uart-tx-observer.c', Path(__file__).resolve()]},
              'installed': False, 'live_irq_cause_proven': False, 'live_module_load_unload_qualified': False,
              'reversible_TX_correction': True, 'FIFO_model_capacity': 8, 'new_path_max_writes': 1, 'boundary': 'Compiled module code executes against RAM and fixture kernel APIs; actual archived ISR, status getter, tail, TX/RX helpers and irq_to_desc execute against RAM; FIFO capacity/full flag are modeled, not physical silicon proof; tty APIs and radix lookup are fixtures. No A7 cost or real module-loader lifecycle is measured.'}
    (OUT / 'qualification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(run.stdout)
    print(json.dumps({'module_sha256': report['observer_module_sha256'], 'abi': layout}))


if __name__ == '__main__':
    main()
