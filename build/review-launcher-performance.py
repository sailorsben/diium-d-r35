"""Read-only binary review; outputs evidence only on the PC."""
import hashlib, json, os, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(os.environ['TEMP']) / 'd35-inspection-tools'))
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB

root = Path(__file__).resolve().parent.parent
out = root / 'device-evidence/launcher-performance-review'
out.mkdir(exist_ok=True)
requests = {
    'main': ['main'],
    'vrtemu': ['environment', 'InitEmulateFrame.constprop.0', 'Load_Proc2',
               'PlayFrame', 'PlaySound', 'DrawFrame', 'DispFrame', 'InitSound',
               'Snes_Load', 'mui_SoundplayThread', 'mui_PauseMenu', 'SetSound',
               'SoundClose', 'SoundPlay', 'StopSound', 'Snes_Unload'],
    'driver.so': ['sound_driver_init', 'sound_driver_playframe', 'video_driver_disp_frame',
                  'video_driver_disp_frame0', 'DrawVFB', 'PScaleRun', 'ScaleDisplayThread', 'WaitDisp'],
    'libs/emu_sfc_orig.so': ['SetFrameSkip', 'SetDoubleBuffer', 'retro_run'],
    'libs/emu_sfc.so': ['SetFrameSkip', 'SetDoubleBuffer', 'retro_run'],
    'libs/emu_sfc_plus.so': ['SetFrameSkip', 'SetDoubleBuffer', 'retro_run'],
}
census, lines = {}, []
for name, selected in requests.items():
    binary = Path('D:/retro') / name
    if not binary.exists():
        binary = Path('H:/DIIUM D-R35/retro') / name
    before = hashlib.sha256(binary.read_bytes()).hexdigest()
    with binary.open('rb') as f:
        elf = ELFFile(f)
        symbols, targets, relocations = {}, {}, {}
        for sn in ('.dynsym', '.symtab'):
            section = elf.get_section_by_name(sn)
            if section:
                for symbol in section.iter_symbols():
                    if symbol['st_shndx'] != 'SHN_UNDEF':
                        symbols[symbol.name] = symbol
                        targets[symbol['st_value'] & ~1] = symbol.name
        for section in elf.iter_sections():
            if section['sh_type'] == 'SHT_REL':
                symtab = elf.get_section(section['sh_link'])
                for relocation in section.iter_relocations():
                    s = symtab.get_symbol(relocation['r_info_sym'])
                    if s.name: relocations[relocation['r_offset']] = s.name
        plt, relplt = elf.get_section_by_name('.plt'), elf.get_section_by_name('.rel.plt')
        if plt and relplt:
            symtab = elf.get_section(relplt['sh_link'])
            for i, r in enumerate(relplt.iter_relocations()):
                targets[plt['sh_addr'] + 20 + i * 12] = symtab.get_symbol(r['r_info_sym']).name + '@plt'
        funcs = [s for s in symbols.values() if s['st_info']['type'] == 'STT_FUNC' and s['st_size']]
        census[name] = {'path': str(binary), 'sha256': before, 'bytes': binary.stat().st_size,
                        'named_functions': len(funcs), 'named_defined_symbols': len(symbols),
                        'executable_segment_bytes': sum(p['p_memsz'] for p in elf.iter_segments() if p['p_type'] == 'PT_LOAD' and p['p_flags'] & 1),
                        'selected_functions': {n: {'address': hex(symbols[n]['st_value']), 'bytes': symbols[n]['st_size']} for n in selected if n in symbols},
                        'thread_related_functions': sorted(n for n in symbols if 'thread' in n.lower()),
                        'timing_globals': sorted(n for n in symbols if any(q in n.lower() for q in ('fps', 'framecount', 'frame_count', 'emulate', 'skip', 'snd', 'audio', 'sound', 'timebase')))}
        callers = {n: [] for n in ('SetSound', 'SoundClose', 'SoundPlay', 'StopSound', 'Load_Proc2', 'mui_SoundplayThread')}
        for s in funcs:
            section = elf.get_section(s['st_shndx'])
            address = s['st_value']; start = (address & ~1) - section['sh_addr']
            decoder = Cs(CS_ARCH_ARM, CS_MODE_THUMB if address & 1 else CS_MODE_ARM)
            for instruction in decoder.disasm(section.data()[start:start+s['st_size']], address & ~1):
                if instruction.mnemonic in ('bl', 'b') and instruction.op_str.startswith('#0x'):
                    called = targets.get(int(instruction.op_str[1:], 16))
                    if called in callers: callers[called].append(s.name)
        census[name]['selected_callers'] = {n: sorted(set(v)) for n, v in callers.items() if v}
        def word(address):
            for sec in elf.iter_sections():
                if sec['sh_type'] != 'SHT_NOBITS' and sec['sh_addr'] <= address <= sec['sh_addr'] + sec['sh_size'] - 4:
                    return struct.unpack_from('<I', sec.data(), address - sec['sh_addr'])[0]
            return None
        for n in selected:
            if n not in symbols: continue
            s = symbols[n]; addr = s['st_value']; sec = elf.get_section(s['st_shndx'])
            if not s['st_size']: continue
            start = (addr & ~1) - sec['sh_addr']
            cs = Cs(CS_ARCH_ARM, CS_MODE_THUMB if addr & 1 else CS_MODE_ARM)
            cs.detail = True
            lines.append(f'\n{name} {n} {addr:08x} bytes={s["st_size"]}')
            constants = {}
            for ins in cs.disasm(sec.data()[start:start + s['st_size']], addr & ~1):
                annotations = []
                parts = ins.op_str.replace('[', '').replace(']', '').split(', ')
                if ins.mnemonic.startswith('b') and ins.op_str.startswith('#0x'):
                    annotations.append(targets.get(int(ins.op_str[1:], 16), 'branch'))
                new_value = None
                if ins.mnemonic == 'ldr' and len(parts) == 3 and parts[1] == 'pc' and parts[2].startswith('#'):
                    offset = int(parts[2].lstrip('#'), 0)
                    new_value = word(ins.address + 8 + offset)
                    if new_value is not None: annotations.append(f'literal={new_value:#x}')
                elif ins.mnemonic == 'add' and len(parts) == 3 and parts[1] == 'pc' and parts[2] in constants:
                    new_value = (ins.address + 8 + constants[parts[2]]) & 0xffffffff
                    annotations.append(f'base={new_value:#x}')
                elif ins.mnemonic == 'ldr' and len(parts) == 3 and parts[1] in constants and parts[2] in constants:
                    target = (constants[parts[1]] + constants[parts[2]]) & 0xffffffff
                    pointee = word(target)
                    label = relocations.get(target) or targets.get(pointee)
                    if label: annotations.append('GOT -> ' + label)
                _, written = ins.regs_access()
                for r in written: constants.pop(ins.reg_name(r), None)
                if new_value is not None: constants[parts[0]] = new_value
                lines.append(f'{ins.address:08x} {ins.mnemonic:9} {ins.op_str}' + (' ; ' + '; '.join(annotations) if annotations else ''))
    assert hashlib.sha256(binary.read_bytes()).hexdigest() == before
(out / 'binary-census.json').write_text(json.dumps(census, indent=2) + '\n')
(out / 'annotated-paths.txt').write_text('\n'.join(lines) + '\n')
print(json.dumps({n: {k: v for k, v in d.items() if k != 'selected_functions'} for n, d in census.items()}, indent=2))
