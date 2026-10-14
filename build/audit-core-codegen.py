"""Read existing ELF codegen and source identities; no builds or device access."""
from pathlib import Path
from hashlib import sha256
from collections import Counter
import json,re,subprocess
ROOT=Path(__file__).resolve().parent.parent
VARIANTS={'baseline':'build/demand-visible-private-v3/core','obj':'build/ppu-refinements-private-v4/obj','shapes':'build/ppu-refinements-private-v4/shapes','bulk':'build/ppu-refinements-private-v4/bulk','combined':'build/ppu-refinements-private-v5/combined'}
def run(tool,*args):return subprocess.check_output(['wsl',tool,*args],cwd=ROOT,text=True)
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 out=ROOT/'evidence/2026-10-14/core-codegen-review/analysis.json';assert not out.exists()
 result={'read_only':True,'card_access':False,'emulator_changes':False,'A7_prices_from_assembly':False,'variants':{}}
 for label,folder in VARIANTS.items():
  base=ROOT/folder;p=base/'snes9x2005_plus_libretro.so';rel=p.relative_to(ROOT).as_posix()
  size=run('arm-linux-gnueabihf-size',rel).splitlines()[1].split()
  sections=run('arm-linux-gnueabihf-objdump','-h',rel)
  text=next(int(l.split()[2],16) for l in sections.splitlines() if len(l.split())>2 and l.split()[1]=='.text')
  nm=run('arm-linux-gnueabihf-nm','-S','--size-sort',rel);functions={}
  for line in nm.splitlines():
   parts=line.split()
   if len(parts)==4 and parts[2].lower()=='t' and any(parts[3].startswith(n) for n in ('spc_run_until_','dsp_run','dsp_voice_','DrawOBJS','DrawBackground.','S9xUpdateScreen')):functions[parts[3]]=int(parts[1],16)
  calls={}
  for name in functions:
   if name.startswith(('spc_run_until_','dsp_run')):
    asm=run('arm-linux-gnueabihf-objdump','-d','--disassemble='+name,rel)
    calls[name]=dict(Counter(re.findall(r'\sblx?\s+\S+\s+<([^>]+)>',asm)))
  result['variants'][label]={'core_sha256':digest(p),'text_section_bytes':text,'gnu_size_code_plus_readonly_bytes':int(size[0]),'data_bytes':int(size[1]),'bss_bytes':int(size[2]),'functions_bytes':functions,'static_call_sites':calls,
   'source_hashes':{n:digest(base/'source'/n) for n in ('apu_blargg.c','cpuexec.c','cpuops.c','cpuops.h')}}
 old=result['variants']['baseline']
 for label,v in result['variants'].items():
  v['same_selected_CPU_APU_sources_as_baseline']=v['source_hashes']==old['source_hashes']
  assert v['same_selected_CPU_APU_sources_as_baseline']
 result['limits']=['Static call sites are not dynamic frequencies or cycles.','Code size is not instruction-cache miss rate.','LTO differences across unchanged source establish a confound, not causation of physical regression.','Baseline phase attribution predates demand-v3; current inner PPU/CPU/SPC costs remain unpriced.']
 out.parent.mkdir(parents=True);out.write_text(json.dumps(result,indent=2)+'\n');print(out.relative_to(ROOT))
 for label,v in result['variants'].items():print(label,v['text_section_bytes'],v['functions_bytes'].get('spc_run_until_.lto_priv.0'),v['static_call_sites'].get('spc_run_until_.lto_priv.0'))
if __name__=='__main__':main()
