"""Recover ABI types from the preserved vendor debug data, not original source."""
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(os.environ['TEMP']) / 'd35-inspection-tools'))
from elftools.elf.elffile import ELFFile

out = Path(__file__).resolve().parent.parent / 'device-evidence/hardware-architecture-review'
def value(die, key):
    attr = die.attributes.get(key)
    if not attr: return None
    v = attr.value
    return v.decode(errors='replace') if isinstance(v, bytes) else v
def typename(die, seen=None):
    seen = set() if seen is None else seen
    if die.offset in seen: return '<recursive>'
    seen.add(die.offset)
    name = value(die, 'DW_AT_name')
    if name: return name
    ref = die.get_DIE_from_attribute('DW_AT_type') if 'DW_AT_type' in die.attributes else None
    inner = typename(ref, seen) if ref else 'void'
    if die.tag == 'DW_TAG_pointer_type': return inner + ' *'
    if die.tag == 'DW_TAG_const_type': return 'const ' + inner
    if die.tag == 'DW_TAG_array_type':
        bounds = [value(c, 'DW_AT_upper_bound') for c in die.iter_children() if c.tag == 'DW_TAG_subrange_type']
        return inner + ''.join('[' + (str(n+1) if isinstance(n,int) else '') + ']' for n in bounds)
    return inner

units, types, functions = [], [], []
with (out / 'driver.so').open('rb') as f:
    elf = ELFFile(f)
    assert elf.has_dwarf_info()
    for cu in elf.get_dwarf_info().iter_CUs():
        top = cu.get_top_DIE()
        units.append({k: value(top,k) for k in ['DW_AT_name','DW_AT_comp_dir','DW_AT_producer']})
        for die in cu.iter_DIEs():
            name = value(die, 'DW_AT_name')
            if die.tag in ['DW_TAG_structure_type','DW_TAG_enumeration_type']:
                row = {'name': name, 'die_offset': die.offset, 'tag': die.tag,
                       'byte_size': value(die, 'DW_AT_byte_size'), 'members': []}
                for child in die.iter_children():
                    if child.tag == 'DW_TAG_member':
                        row['members'].append({'name': value(child,'DW_AT_name'),
                            'offset': value(child,'DW_AT_data_member_location'),
                            'type': typename(child.get_DIE_from_attribute('DW_AT_type'))})
                    elif child.tag == 'DW_TAG_enumerator':
                        row['members'].append({'name': value(child,'DW_AT_name'), 'value': value(child,'DW_AT_const_value')})
                if name or row['members']: types.append(row)
            if die.tag == 'DW_TAG_subprogram' and name and 'DW_AT_low_pc' in die.attributes:
                functions.append({'name':name, 'address':value(die,'DW_AT_low_pc'),
                    'return_type':typename(die.get_DIE_from_attribute('DW_AT_type')) if 'DW_AT_type' in die.attributes else 'void',
                    'parameters':[{'name':value(c,'DW_AT_name'),
                        'type':typename(c.get_DIE_from_attribute('DW_AT_type')) if 'DW_AT_type' in c.attributes else 'unknown'}
                        for c in die.iter_children() if c.tag == 'DW_TAG_formal_parameter']})
scaler = next(t for t in types if t['name'] == 'gpPScalerPara_s')
assert scaler['byte_size'] == 228
offsets = {m['name']:m['offset'] for m in scaler['members']}
assert offsets['frame_queue_enable'] == 72 and offsets['bypass_frame_queue_enable'] == 84
assert offsets['drop_frame_div'] == 98 and offsets['drop_frame_fra'] == 99
enums = {m['name']:m['value'] for t in types if t['tag']=='DW_TAG_enumeration_type' for m in t['members']}
assert enums['PIPELINE_SCALER_STATUS_FRAME_DONE'] == 2
result = {'compilation_units': units, 'types': types, 'functions': functions,
          'evidence_boundary': 'DWARF types and compiler metadata; not recovered original source or kernel implementation.'}
(out / 'driver-dwarf.json').write_text(json.dumps(result,indent=2) + '\n')
print(json.dumps({'compilation_units': len(units), 'types':len(types), 'functions':len(functions),
                  'scaler_bytes':scaler['byte_size'], 'queue_offsets':offsets['frame_queue_enable'],
                  'frame_done_status':enums['PIPELINE_SCALER_STATUS_FRAME_DONE']},indent=2))
