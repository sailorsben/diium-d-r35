"""Conservative static NEON census; not a runtime profile or speed claim."""
from pathlib import Path
import hashlib
import json
import os
import re
import sys
sys.path.insert(0, str(Path(os.environ['TEMP']) / 'd35-inspection-tools'))
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB

root = Path(__file__).resolve().parent.parent
out = root / 'device-evidence/hardware-architecture-review'
result = {}
for name, path in [('plus', Path('D:/retro/libs/emu_sfc_plus.so')),
                   ('2010', root / 'build/comparison-2010/emu_sfc_2010.so')]:
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open('rb') as f:
        elf = ELFFile(f)
        symtab = elf.get_section_by_name('.symtab') or elf.get_section_by_name('.dynsym')
        seen, rows, examples = set(), [], {}
        for symbol in symtab.iter_symbols():
            if symbol['st_info']['type'] != 'STT_FUNC' or not symbol['st_size'] or symbol['st_shndx'] == 'SHN_UNDEF':
                continue
            addr = symbol['st_value']
            signature = (addr, symbol['st_size'])
            if signature in seen:
                continue
            seen.add(signature)
            section = elf.get_section(symbol['st_shndx'])
            start = (addr & ~1) - section['sh_addr']
            cs = Cs(CS_ARCH_ARM, CS_MODE_THUMB if addr & 1 else CS_MODE_ARM)
            count, total, found = 0, 0, []
            for ins in cs.disasm(section.data()[start:start + symbol['st_size']], addr & ~1):
                total += 1
                if not ins.mnemonic.startswith('v'):
                    continue
                # Scalar VFP conversions can have .s32 suffixes. Exclude S
                # registers and double-precision arithmetic before matching.
                if re.search(r'\bs\d+\b', ins.op_str) or '.f64' in ins.mnemonic:
                    continue
                if (re.search(r'\.[iusp]\d+', ins.mnemonic)
                    or re.search(r'\bq\d+\b', ins.op_str)
                    or re.match(r'v(ld[1-4]|st[1-4]|tbl|tbx|ext|zip|uzp|trn|dup|rev)', ins.mnemonic)):
                    count += 1
                    found.append(f'{ins.address:x} {ins.mnemonic} {ins.op_str}')
            if count:
                rows.append({'name': symbol.name, 'neon': count, 'all': total})
                if re.search(r'dsp_run|DrawTile|DrawClippedTile|DrawLargePixel', symbol.name):
                    examples[symbol.name] = found[:60]
        result[name] = {'file': str(path), 'sha256': before,
                        'functions_with_NEON': len(rows),
                        'statically_classified_NEON_instructions': sum(r['neon'] for r in rows),
                        'top': sorted(rows, key=lambda x: x['neon'], reverse=True)[:15],
                        'examples': examples,
                        'limitation': 'Static presence, not runtime execution or timing; conservative classification.'}
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    print(name, result[name]['functions_with_NEON'], result[name]['statically_classified_NEON_instructions'])
(out / 'neon-code-census.json').write_text(json.dumps(result, indent=2))
