from pathlib import Path
import os, sys
sys.path.insert(0,str(Path(os.environ['TEMP'])/'d35-inspection-tools'))
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB
requests={
 'retro/driver.so':['video_driver_disp_frame','video_driver_disp_frame0','video_driver_getframe','video_driver_setmode','video_drivers_init','video_driver_setting','sound_driver_init','sound_driver_playframe','sound_driver_settrigger','gpChunkMemAlloc','gpChunkMemVA2PA','dispCreate0','dispCreate1','DrawVFB','InitVFB','FreeVFB','PScaleRun','ScaleDisplayThread','dispFlip'],
 'retro/vrtemu':['DrawFrame','DispFrame','InitDisplay','InitDoubleFrame','getframe','frame_extend','InitEmulateFrame.constprop.0','Load_Proc2','PlayFrame','AudioProcess','PlaySound','InitSound','RetroInitSound','ScaleDisplay3','ScaleDisplay3_2'],
 'retro/libs/emu_sfc_orig.so':['S9xInitDisplay','retro_init','retro_run','ChunkMemAlloc','ChunkMemFree'],
}
lines=[]
for rel, names in requests.items():
 with (Path(r'H:\DIIUM D-R35')/rel).open('rb') as f:
  e=ELFFile(f); symbols={}; targets={}
  for sn in ['.dynsym','.symtab']:
   sec=e.get_section_by_name(sn)
   if sec:
    for s in sec.iter_symbols():
     if s['st_shndx']!='SHN_UNDEF': symbols[s.name]=s;targets[s['st_value']&~1]=s.name
  plt=e.get_section_by_name('.plt'); reloc=e.get_section_by_name('.rel.plt')
  if plt and reloc:
   symsec=e.get_section(reloc['sh_link'])
   for i,r in enumerate(reloc.iter_relocations()):
    targets[plt['sh_addr']+20+i*12]=symsec.get_symbol(r['r_info_sym']).name+'@plt'
  for name in names:
   s=symbols.get(name)
   if not s or not s['st_size']:continue
   addr=s['st_value']; sec=e.get_section(s['st_shndx']);off=(addr&~1)-sec['sh_addr']
   cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB if addr&1 else CS_MODE_ARM)
   lines.append(f'\n{rel} {name} {addr:08x} size={s["st_size"]}')
   for x in cs.disasm(sec.data()[off:off+s['st_size']],addr&~1):
    extra=''
    if x.mnemonic.startswith('b') and x.op_str.startswith('#0x'):
     extra=' ; '+targets.get(int(x.op_str[1:],16),'')
    lines.append(f'{x.address:08x} {x.mnemonic:8} {x.op_str}{extra}')
Path('build/hardware-disassembly.txt').write_text('\n'.join(lines))
print('Saved hardware-disassembly.txt')
