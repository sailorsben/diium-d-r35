"""Verify compiled APU object identity and emitted SPC/DSP function sizes."""
from pathlib import Path
from hashlib import sha256
import json, subprocess

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/draw-order-private-v1'
PIN='a3baec4aabbbb539858fb7fc59b5b96bddf7e7e6bb7a51c6e6fa394f8b542097'

def digest(p):return sha256(p.read_bytes()).hexdigest()
def symbols(path):
 result={}
 for line in subprocess.check_output(['arm-linux-gnueabihf-nm','-S','--defined-only',str(path)],text=True).splitlines():
  p=line.split()
  if len(p)==4 and p[2] in ('t','T'):result[p[3]]={'address':int(p[0],16),'bytes':int(p[1],16)}
 return result

def main():
 raw=ROOT/'build/demand-visible-private-v3/core/source/apu_blargg.c'
 assert digest(raw)==digest(OUT/'boundary/source/apu_blargg.c')==digest(OUT/'priority/source/apu_blargg.c')
 assert digest(OUT/'boundary/source/apu_blargg.o')==digest(OUT/'priority/source/apu_blargg.o')==PIN
 obj=symbols(OUT/'boundary/source/apu_blargg.o')
 a=symbols(OUT/'boundary/snes9x2005_plus_libretro.so');b=symbols(OUT/'priority/snes9x2005_plus_libretro.so')
 selected={n:s for n,s in obj.items() if n.startswith(('spc_','dsp_','S9xAPU','rb_'))}
 assert len(selected)>20
 for n,s in selected.items():assert a[n]['bytes']==b[n]['bytes']==s['bytes'],n
 for label in ('boundary','priority'):
  text=subprocess.check_output(['arm-linux-gnueabihf-nm','--defined-only',str(OUT/label/'snes9x2005_plus_libretro.so')],text=True)
  assert 'd35_work' not in text and 'pc_sample' not in text and 'd35_order_probe' not in text
 result={'passed':True,'APU_source_unchanged':True,'APU_object_byte_identical':True,'APU_object_sha256':PIN,
  'SPC_DSP_functions':{n:{'bytes':s['bytes'],'boundary_address':a[n]['address'],'priority_address':b[n]['address']} for n,s in selected.items()},
  'SPC_DSP_function_sizes_identical':True,'ordinary_observers_absent':True,
  'limits':['Compiled object bytes are fixed; linked addresses/layout and relocation values can differ.','This audit establishes code-generation stability, not boundary speed or A7 savings.']}
 (OUT/'APU-audit.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS fixed APU object/source and',len(selected),'linked SPC/DSP function sizes; no work/probe/sampler symbols')

if __name__=='__main__':main()
