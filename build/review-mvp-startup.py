import os, sys, struct
from pathlib import Path
sys.path.insert(0,str(Path(os.environ['TEMP'])/'d35-inspection-tools'))
from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
root=Path(__file__).resolve().parent.parent
requests={root/'device-evidence/hardware-architecture-review/driver.so':['detect_hdmi','video_drivers_init','InitVFB','dispCreate1','video_driver_get_size'],
          root/'build/launcher-clock/vrtemu.original':['InitJoystick','gpio_read_io','gpio_write_io','set_port_attribute']}
lines=[]
for path,names in requests.items():
 with path.open('rb') as f:
  elf=ELFFile(f); symbols={}; targets={}; relocs={}
  for sectionname in ('.dynsym','.symtab'):
   section=elf.get_section_by_name(sectionname)
   if section:
    for s in section.iter_symbols():
     if s['st_shndx']!='SHN_UNDEF': symbols[s.name]=s;targets[s['st_value']&~1]=s.name
  plt=elf.get_section_by_name('.plt');relplt=elf.get_section_by_name('.rel.plt')
  if plt and relplt:
   symtab=elf.get_section(relplt['sh_link'])
   for i,r in enumerate(relplt.iter_relocations()):targets[plt['sh_addr']+20+i*12]=symtab.get_symbol(r['r_info_sym']).name+'@plt'
  for section in elf.iter_sections():
   if section['sh_type']=='SHT_REL':
    symtab=elf.get_section(section['sh_link'])
    for r in section.iter_relocations():relocs[r['r_offset']]=symtab.get_symbol(r['r_info_sym']).name
  def word(addr):
   for section in elf.iter_sections():
    if section['sh_type']!='SHT_NOBITS' and section['sh_addr']<=addr<=section['sh_addr']+section['sh_size']-4:
     return struct.unpack_from('<I',section.data(),addr-section['sh_addr'])[0]
  for name in names:
   s=symbols.get(name)
   if not s:continue
   section=elf.get_section(s['st_shndx']);addr=s['st_value'];start=addr-section['sh_addr']
   lines.append(f'\n{path.name} {name} {addr:x} size={s["st_size"]}')
   for ins in Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(section.data()[start:start+s['st_size']],addr):
    annotation=''
    if ins.mnemonic in ('b','bl') and ins.op_str.startswith('#0x'):annotation=targets.get(int(ins.op_str[1:],16),'')
    if '[pc,' in ins.op_str:
     offset=int(ins.op_str.split('[pc, #')[1].split(']')[0],0);value=word(ins.address+8+offset)
     annotation+=f' literal={value:#x}' if value is not None else ''
    lines.append(f'{ins.address:08x} {ins.mnemonic:8} {ins.op_str} {annotation}')
out=root/'device-evidence/platform-redesign-review/mvp-startup-disassembly.txt'
out.write_text('\n'.join(lines)+'\n');print(out.read_text())
