"""Qualify restricted sharing against the measured core, using original inputs.
No QEMU duration, instruction count or host frequency is performance evidence.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json,os,statistics,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/shared-geometry-private-v1'
FIELDS={0:'eligible_sub_draws',1:'recorded_commands',2:'reused_main_draws',3:'edge_rejections',4:'capacity_rejections',5:'replayed_commands',6:'replayed_tile_rows'}
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 assert not (OUT/'qualification.json').exists();(OUT/'exact').mkdir()
 plan=json.loads((ROOT/'build/ability-regression-private-v1/plan.json').read_text())
 selected=[c for c in plan['cases'] if c['seq'] in (0,1,3,5,6,7,8,10)]
 env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')}
 def run(c):
  log=OUT/f"exact/{c['seq']:03d}.log"
  args=['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(OUT/'compare'),str(ROOT/'build/common-band-private-v3/plus-a7.so'),str(OUT/'core/snes9x2005_plus_libretro.so'),str(ROOT/'build/plus-a7-out/ff6.sfc'),str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/scene.state"),str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/input.txt"),str(c['observed_effect_id']),'1200']
  with log.open('x') as f:subprocess.run(args,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=240)
  text=log.read_text();assert 'PASS 1200 calls' in text
  rows=[list(map(int,l[7:].split(','))) for l in text.splitlines() if l.startswith('SHARED ')]
  assert [r[0] for r in rows]==list(range(1200))
  layout=[list(map(int,l.split()[1:])) for l in text.splitlines() if l.startswith('LAYOUT ')];assert len(layout)==1
  groups={'all_calls':range(1200)}
  if c['seq']==1:groups['Meteor_peak']=range(384,416)
  if c['seq']==8:groups['Quasar_peak']=range(496,530)
  means={group:{name:statistics.mean(rows[i][j+1] for i in indices) for j,name in FIELDS.items()} for group,indices in groups.items()}
  print('PASS',c['seq'],c['name'],means.get('Meteor_peak',means.get('Quasar_peak',means['all_calls'])),flush=True)
  return {'fixture':c['seq'],'name':c['name'],'exact_calls':1200,'log_sha256':digest(log),'totals':{name:sum(r[j+1] for r in rows) for j,name in FIELDS.items()},'means':means,'ARM_QEMU_layout':dict(zip(('tile2_pointer','tile4_pointer','tile8_pointer','palette_table_bytes','palette_table_alignment','palette_entry_bytes','palette_table_member_offset','palette_entries_pointer'),layout[0]))}
 with ThreadPoolExecutor(max_workers=2) as pool:cases=list(pool.map(run,selected))
 data={'passed':True,'exact_original_command_calls':9600,'oracle_core_sha256':digest(ROOT/'build/common-band-private-v3/plus-a7.so'),'candidate_core_sha256':digest(OUT/'core/snes9x2005_plus_libretro.so'),'command_bytes':8,'command_capacity':8192,'command_storage_bytes':65536,'cases':cases,'A7_measurements':False,'QEMU_timing_used':False,'card_access':False,'production_gate_passed':False,'limits':['Only mode1 BG0, 8x8 tiles, both planes enabled, full equal clips, no special window target, no horizontal partial tile, eligible original batch color family.','Records geometry, not decoded/RGB pixels. It does not remove the second depth test, palette lookup or blend.','One redraw lifetime; main/sub order, palette/register/VRAM timing and original fallback remain.','Captured command writes, rereads, guards, cache footprint, instrumentation and changed code layout all need complete A7 pricing.','Layout addresses are from this ARM/QEMU process, not returned A7 heap addresses.']}
 (OUT/'qualification.json').write_text(json.dumps(data,indent=2)+'\n')
 print('PASS 9600 exact graphics/PCM/geometry calls and normalized state every30 calls; no A7 saving inferred')
if __name__=='__main__':main()
