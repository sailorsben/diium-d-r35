"""Hash-pinned offline scaler/display contract extraction; never executes vendor code."""
from pathlib import Path
from hashlib import sha256
import json
import re
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'build/lab2-inspection-tools'))
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB

SOURCE = ROOT / 'device-evidence/hardware-architecture-review/driver.so'
TARGET = ROOT / 'evidence/2026-10-05/lab2-driver-contract'
PIN = '2c0134b3fc425f5b65c271c014e291824590c773190014f4e50c3ed33c2f13f9'

def extract():
    assert sha256(SOURCE.read_bytes()).hexdigest() == PIN
    TARGET.mkdir(parents=True, exist_ok=True)
    with SOURCE.open('rb') as f:
        elf = ELFFile(f); symbols = {}; calls = {}
        for name in ('.dynsym', '.symtab'):
            section = elf.get_section_by_name(name)
            if section:
                for s in section.iter_symbols():
                    if s['st_shndx'] != 'SHN_UNDEF':
                        symbols[s.name] = s; calls[s['st_value'] & ~1] = s.name
        plt, rel = elf.get_section_by_name('.plt'), elf.get_section_by_name('.rel.plt')
        syms = elf.get_section(rel['sh_link'])
        for i, r in enumerate(rel.iter_relocations()):
            calls[plt['sh_addr'] + 20 + i * 12] = syms.get_symbol(r['r_info_sym']).name + '@plt'
        def word(address):
            for section in elf.iter_sections():
                begin = section['sh_addr']; size = section['sh_size']
                if section['sh_type'] != 'SHT_NOBITS' and begin <= address and address + 4 <= begin + size:
                    return int.from_bytes(section.data()[address-begin:address-begin+4], 'little')
            return None
        names = ('PScaleRun', 'DrawVFB', 'FlipVFB', 'dispFlip', 'FreeVFB', 'WaitDisp', 'ScaleDisplayThread',
                 'gpChunkMemAlloc', 'gpChunkMemFree', 'gpChunkMemVA2PA')
        text = []; found = []
        for name in names:
            s = symbols.get(name)
            if not s or not s['st_size']: continue
            addr = s['st_value']; section = elf.get_section(s['st_shndx']); off = (addr & ~1)-section['sh_addr']
            cs = Cs(CS_ARCH_ARM, CS_MODE_THUMB if addr & 1 else CS_MODE_ARM)
            text.append(f'\n{name} address=0x{addr:08x} bytes={s["st_size"]}')
            registers = {}
            for ins in cs.disasm(section.data()[off:off+s['st_size']], addr & ~1):
                note = ''
                immediate = re.fullmatch(r'(r\d+), #(-?0x[0-9a-f]+|\d+)', ins.op_str)
                literal = re.fullmatch(r'(r\d+), \[pc(?:, #(-?0x[0-9a-f]+|\d+))?\]', ins.op_str)
                if immediate and ins.mnemonic in ('mov', 'movw', 'movt'):
                    reg, value = immediate.groups(); value = int(value, 0)
                    registers[reg] = ((registers.get(reg, 0) & 0xffff) | value << 16) if ins.mnemonic == 'movt' else value
                elif literal and ins.mnemonic == 'ldr':
                    reg, displacement = literal.groups(); value = word(ins.address+8+int(displacement or '0', 0))
                    if value is not None: registers[reg] = value; note = f' ; literal=0x{value:08x}'
                elif ins.mnemonic.startswith('b') and ins.op_str.startswith('#0x'):
                    target = calls.get(int(ins.op_str[1:], 16), '')
                    if target:
                        note = ' ; ' + target
                        if target == 'ioctl@plt':
                            found.append({'function': name, 'call_address': f'0x{ins.address:08x}',
                                          'last_constant_r1': f'0x{registers["r1"]:08x}' if 'r1' in registers else None,
                                          'qualification': 'Local straight-line constant recovery; inspect control flow and argument type before live use.'})
                    if ins.mnemonic in ('bl', 'blx'):
                        for reg in ('r0', 'r1', 'r2', 'r3'): registers.pop(reg, None)
                    elif not target:
                        registers.clear()  # Never carry constants across an unmodeled branch.
                else:
                    destination = ins.op_str.split(',')[0]
                    if re.fullmatch(r'r\d+', destination) and ins.mnemonic.startswith(('ldr', 'add', 'sub', 'mov')):
                        registers.pop(destination, None)
                text.append(f'{ins.address:08x} {ins.mnemonic:8} {ins.op_str}{note}')
    dwarf = json.loads((ROOT / 'evidence/2026-10-04/hardware-architecture-review/driver-dwarf.json').read_text())
    scaler = next(t for t in dwarf['types'] if t['name'] == 'gpPScalerPara_s')
    result = {'driver_sha256': PIN, 'scaler_type': scaler, 'ioctl_sites': found,
              'boundary': 'Exact userspace binary and DWARF. No kernel implementation, cache policy, continuous queue or output completion contract inferred from field names.'}
    (TARGET / 'contract.json').write_text(json.dumps(result, indent=2)+'\n')
    (TARGET / 'disassembly.txt').write_text('\n'.join(text)+'\n')
    print(json.dumps({'driver_sha256': PIN, 'functions': len(names), 'ioctl_sites': found}, indent=2))

if __name__ == '__main__': extract()
