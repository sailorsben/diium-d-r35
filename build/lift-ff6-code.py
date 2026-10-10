"""Generate a private C analysis map from ROM-verified assembler debug spans.

This is low-level C with hardware/flags/control helpers, not recovered original
C source or a runnable port. Preserve native code/data distinctions and report
coverage rather than interpreting graphics, script bytes or unknown spans as CPU.
"""
from pathlib import Path
from hashlib import sha256
from collections import defaultdict
import json
import re
import zlib

ROOT = Path(__file__).resolve().parent.parent
DISASM = ROOT / 'build/ff6-disasm'
OUT = ROOT / 'build/ff6-cause-private/c-map'
OP_ROWS = '''
brk ora cop ora tsb ora asl ora php ora asl phd tsb ora asl ora
bpl ora ora ora trb ora asl ora clc ora inc tcs trb ora asl ora
jsr and jsl and bit and rol and plp and rol pld bit and rol and
bmi and and and bit and rol and sec and dec tsc bit and rol and
rti eor wdm eor mvp eor lsr eor pha eor lsr phk jmp eor lsr eor
bvc eor eor eor mvn eor lsr eor cli eor phy tcd jml eor lsr eor
rts adc per adc stz adc ror adc pla adc ror rtl jmp adc ror adc
bvs adc adc adc stz adc ror adc sei adc ply tdc jmp adc ror adc
bra sta brl sta sty sta stx sta dey bit txa phb sty sta stx sta
bcc sta sta sta sty sta stx sta tya sta txs txy stz sta stz sta
ldy lda ldx lda ldy lda ldx lda tay lda tax plb ldy lda ldx lda
bcs lda lda lda ldy lda ldx lda clv lda tsx tyx ldy lda ldx lda
cpy cmp rep cmp cpy cmp dec cmp iny cmp dex wai cpy cmp dec cmp
bne cmp cmp cmp pei cmp dec cmp cld cmp phx stp jmp cmp dec cmp
cpx sbc sep sbc cpx sbc inc sbc inx sbc nop xba cpx sbc inc sbc
beq sbc sbc sbc pea sbc inc sbc sed sbc plx xce jsr sbc inc sbc
'''.split()
assert len(OP_ROWS) == 256
MNEMONICS = set(OP_ROWS)


def parse(line):
    return {key: value.strip('"') for key, value in re.findall(r'(\w+)=("[^"]*"|[^,]+)', line)}


def statement(opcode, mnemonic, operand, size, pc):
    ea = f'cpu_ea(c,0x{opcode:02x},0x{operand:x})'
    value = f'cpu_operand(c,0x{opcode:02x},0x{operand:x})'
    register = {'lda': 'a', 'ldx': 'x', 'ldy': 'y'}
    if mnemonic in register:
        reg = register[mnemonic]
        return f'c->{reg}=cpu_nz(c,{value},\'{reg}\');'
    if mnemonic in ('sta', 'stx', 'sty', 'stz'):
        reg = {'sta': 'a', 'stx': 'x', 'sty': 'y', 'stz': 'a'}[mnemonic]
        stored = '0' if mnemonic == 'stz' else f'c->{reg}'
        return f'cpu_write(c,{ea},{stored},\'{reg}\');'
    if mnemonic in ('and', 'ora', 'eor'):
        operation = {'and': '&', 'ora': '|', 'eor': '^'}[mnemonic]
        return f'c->a=cpu_nz(c,c->a {operation} {value},\'a\');'
    if mnemonic in ('adc', 'sbc'):
        return f'c->a=cpu_{mnemonic}(c,c->a,{value});'
    if mnemonic in ('cmp', 'cpx', 'cpy'):
        reg = {'cmp': 'a', 'cpx': 'x', 'cpy': 'y'}[mnemonic]
        return f'cpu_compare(c,c->{reg},{value},\'{reg}\');'
    flag_ops = {'clc': (1, False), 'sec': (1, True), 'cli': (4, False),
                'sei': (4, True), 'cld': (8, False), 'sed': (8, True), 'clv': (64, False)}
    if mnemonic in flag_ops:
        flag, set_flag = flag_ops[mnemonic]
        return f'c->p {"|=" if set_flag else "&="} {flag if set_flag else "~" + str(flag)};'
    if mnemonic in ('rep', 'sep'):
        return f'cpu_status(c,0x{operand:x},{1 if mnemonic == "sep" else 0});'
    branch = {'bpl': '!(c->p&128)', 'bmi': '(c->p&128)', 'bvc': '!(c->p&64)',
              'bvs': '(c->p&64)', 'bcc': '!(c->p&1)', 'bcs': '(c->p&1)',
              'bne': '!(c->p&2)', 'beq': '(c->p&2)', 'bra': '1', 'brl': '1'}
    if mnemonic in branch:
        bits = 16 if mnemonic == 'brl' else 8
        displacement = operand - (1 << bits) if operand & (1 << (bits - 1)) else operand
        target = (pc & 0xff0000) | ((pc + size + displacement) & 0xffff)
        return f'if({branch[mnemonic]}) c->pc=0x{target:06x};'
    if mnemonic == 'nop':
        return '(void)c;'
    return f'cpu_{mnemonic}(c,0x{opcode:02x},0x{operand:x});'


def lift():
    owner = (ROOT / 'build/plus-a7-out/ff6.sfc').read_bytes()
    rebuilt = (DISASM / 'build/en/rom/ff6-en.sfc').read_bytes()
    assert owner == rebuilt and len(owner) == 3145728 and zlib.crc32(owner) & 0xffffffff == 0xa27f1c7a
    files, segments, spans, lines, symbols = {}, {}, {}, [], []
    dbg = DISASM / 'build/en/rom/ff6-en.dbg'
    for line in dbg.open(encoding='utf-8'):
        kind = line.split()[0]
        if kind not in ('file', 'seg', 'span', 'line', 'sym'):
            continue
        record = parse(line)
        if kind == 'file':
            files[int(record['id'])] = record['name']
        elif kind == 'seg':
            segments[int(record['id'])] = record
        elif kind == 'span':
            spans[int(record['id'])] = (int(record['seg']), int(record['start']), int(record['size']))
        elif kind == 'line' and 'span' in record:
            lines.append(record)
        elif kind == 'sym' and record.get('type') == 'lab' and 'val' in record:
            symbols.append(record)
    source_cache, nodes = {}, {}
    rejected = defaultdict(int)
    for record in lines:
        name = files[int(record['file'])]
        if not name.endswith(('.asm', '.mac', '.inc')):
            continue
        if name not in source_cache:
            path = DISASM / name
            if not path.is_file():
                source_cache[name] = []
            else:
                source_cache[name] = path.read_text(encoding='utf-8', errors='replace').splitlines()
        source = source_cache[name]
        number = int(record['line'])
        if number > len(source):
            continue
        text = source[number - 1].split(';')[0].strip()
        text = re.sub(r'^(?:[\w@.:]+:)\s*', '', text)
        if not text:
            continue
        mnemonic = text.split()[0].lower()
        if mnemonic not in MNEMONICS:
            continue
        for span_id in record['span'].split('+'):
            seg_id, offset, size = spans[int(span_id)]
            seg = segments[seg_id]
            pc = int(seg['start'], 0) + offset
            if not 0xc00000 <= pc < 0xf00000 or not 1 <= size <= 4:
                rejected['non_rom_or_non_instruction_span'] += 1
                continue
            raw = owner[pc - 0xc00000:pc - 0xc00000 + size]
            opcode = raw[0]
            if OP_ROWS[opcode] != mnemonic and not (mnemonic == 'jmp' and OP_ROWS[opcode] == 'jml'):
                rejected['source_opcode_mismatch'] += 1
                continue
            node = {'pc': pc, 'opcode': opcode, 'operand': int.from_bytes(raw[1:], 'little'),
                    'size': size, 'mnemonic': OP_ROWS[opcode], 'source': name,
                    'line': number, 'assembly': text}
            if pc in nodes:
                assert nodes[pc]['opcode'] == opcode and nodes[pc]['size'] == size, hex(pc)
                if '/common/' in nodes[pc]['source'] and '/common/' not in name:
                    nodes[pc] = node
            else:
                nodes[pc] = node
    by_bank = defaultdict(list)
    for pc, node in sorted(nodes.items()):
        by_bank[pc >> 16].append(node)
    OUT.mkdir(parents=True, exist_ok=True)
    basic = '''#include <stdint.h>
typedef struct { uint16_t a,x,y,d,s; uint8_t p,pb,db; uint32_t pc; } FF6CPU;
uint32_t cpu_ea(FF6CPU*,unsigned,unsigned);
uint16_t cpu_operand(FF6CPU*,unsigned,unsigned);
uint16_t cpu_nz(FF6CPU*,uint16_t,char);
void cpu_write(FF6CPU*,uint32_t,uint16_t,char);
uint16_t cpu_adc(FF6CPU*,uint16_t,uint16_t);
uint16_t cpu_sbc(FF6CPU*,uint16_t,uint16_t);
void cpu_compare(FF6CPU*,uint16_t,uint16_t,char);
void cpu_status(FF6CPU*,unsigned,unsigned);
'''
    special = {name for name in MNEMONICS if name not in ('adc', 'sbc')}
    basic += '\n'.join(f'void cpu_{name}(FF6CPU*,unsigned,unsigned);' for name in sorted(special)) + '\n'
    (OUT / 'ff6-cpu-analysis.h').write_text(basic, encoding='utf-8')
    outputs = []
    for bank, bank_nodes in by_bank.items():
        text = ['/* ROM-verified low-level C analysis map. Helper semantics and timing',
                ' * require implementation/verification before native execution. */',
                '#include "ff6-cpu-analysis.h"', f'int ff6_bank_{bank:02x}_step(FF6CPU *c)', '{', '  switch(c->pc) {']
        for node in bank_nodes:
            pc = node['pc']
            text += [f'  case 0x{pc:06x}: /* {node["source"]}:{node["line"]} {node["assembly"]} */',
                     f'    c->pc=0x{((pc & 0xff0000) | ((pc+node["size"])&0xffff)):06x};',
                     '    ' + statement(node['opcode'], node['mnemonic'], node['operand'], node['size'], pc),
                     '    return 1;']
        text += ['  default: return 0; /* unlifted/code-data boundary */', '  }', '}']
        path = OUT / f'bank-{bank:02x}.c'
        path.write_text('\n'.join(text) + '\n', encoding='utf-8')
        outputs.append(path)
    (OUT / 'instructions.json').write_text(json.dumps(list(nodes.values()), indent=2) + '\n', encoding='utf-8')
    selected = [symbol for symbol in symbols if int(symbol['val'], 0) in nodes or
                symbol['name'] in ('UpdateCircle', 'UpdateCircleShape', 'UpdateCircle_near',
                                   'UpdateCircle_far', 'BGScrollHDMATbl', 'wBG1ScrollData', 'zAnimScriptPtr')]
    (OUT / 'symbols.json').write_text(json.dumps(selected, indent=2) + '\n', encoding='utf-8')
    summary = {'owner_rom_sha256': sha256(owner).hexdigest(), 'rebuilt_rom_byte_equal': True,
               'rom_bytes': len(owner), 'rom_crc32': 'a27f1c7a', 'debug_sha256': sha256(dbg.read_bytes()).hexdigest(),
               'native_instruction_addresses_lifted': len(nodes), 'native_instruction_bytes_lifted': sum(n['size'] for n in nodes.values()),
               'banks': {f'{bank:02x}': len(rows) for bank, rows in sorted(by_bank.items())},
               'rejected_span_reasons': dict(rejected), 'generated_c_files': len(outputs),
               'limits': ['Not original C source or a runnable native game.',
                          'Static compiler-visible native ROM instructions only; RAM overlays, script/data payloads and unsupported spans require separate lifts.',
                          'Generated helpers expose hardware/flags/control boundaries; only the focused semantic model is execution-checked.'],
               'generated_c_sha256': {p.name: sha256(p.read_bytes()).hexdigest() for p in outputs}}
    (OUT / 'verification.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: summary[key] for key in ('rebuilt_rom_byte_equal', 'native_instruction_addresses_lifted',
                                                   'native_instruction_bytes_lifted', 'banks', 'generated_c_files')}, indent=2))


if __name__ == '__main__':
    lift()
