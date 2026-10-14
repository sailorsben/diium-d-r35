"""Exact replay observer qualification. Counts do not price A7 performance."""
from pathlib import Path
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor
import json,os,statistics,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/architecture-audit-private-v1'
FIELDS={0:'OBJ_setups',1:'same_geometry_setups',2:'rotating_line_priority_setups',3:'OBJ_renderer_selections',4:'repeated_OBJ_renderer_selections',5:'OBJ_draw_calls',7:'clipped_OBJ_calls',8:'full_width_clipped_OBJ_calls',9:'full_width_plain_OBJ',10:'full_width_add_OBJ',11:'full_width_other_OBJ',16:'direct_ring_reads',17:'actual_ring_copy_calls',18:'minimum_ring_copy_calls',19:'fragmented_ring_reads',20:'max_copies_one_ring_read',21:'ring_bytes_copied',22:'nonidentity_ring_reads',24:'VRAM_byte_invalidations',25:'all_three_cache_flags_already_invalid',28:'same_geometry_output_mismatches'}
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 assert not (OUT/'qualification.json').exists();logs=OUT/'exact';logs.mkdir()
 plan=json.loads((ROOT/'build/ability-regression-private-v1/plan.json').read_text());selected=[c for c in plan['cases'] if c['seq'] in (0,1,3,5,6,7,8,10)]
 env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')}
 def run(c):
  path=logs/f"{c['seq']:03d}.log";args=['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(OUT/'compare'),str(ROOT/'build/common-band-private-v3/plus-a7.so'),str(OUT/'core/snes9x2005_plus_libretro.so'),str(ROOT/'build/plus-a7-out/ff6.sfc'),str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/scene.state"),str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/input.txt"),str(c['observed_effect_id']),'1200']
  with path.open('x') as f:subprocess.run(args,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=240)
  text=path.read_text();assert 'PASS 1200 calls' in text
  rows=[list(map(int,s[5:].split(','))) for s in text.splitlines() if s.startswith('ARCH ')];assert [r[0] for r in rows]==list(range(1200))
  assert all(r[1+28]==0 for r in rows)
  groups={'all_calls':list(range(1200)),'warm':list(range(120,1200))}
  if c['seq']==1:groups.update(Meteor_peak=list(range(384,416)))
  if c['seq']==8:groups.update(Quasar_peak=list(range(496,530)))
  stats={n:{field:statistics.mean(rows[i][1+j] for i in indices) for j,field in FIELDS.items()} for n,indices in groups.items()}
  totals={name:sum(r[1+i] for r in rows) for i,name in FIELDS.items()};totals['max_copies_one_ring_read']=max(r[1+20] for r in rows)
  print('PASS exact replay',c['seq'],c['name'],flush=True)
  return {'fixture':c['seq'],'name':c['name'],'calls':1200,'exact_graphics_PCM_state':True,'log_sha256':digest(path),'totals':totals,'means_per_call':stats}
 with ThreadPoolExecutor(max_workers=2) as pool:cases=list(pool.map(run,selected))
 data={'passed':True,'observer_only':True,'cases':cases,'fields':FIELDS,'A7_timings_used':False,'QEMU_timings_used':False,'card_access':False,'production_gate_passed':False,'core_sha256':digest(OUT/'core/snes9x2005_plus_libretro.so'),'oracle_core_sha256':digest(ROOT/'build/common-band-private-v3/plus-a7.so'),'limits':['Output and counts only. No architectural optimization was installed or timed.','Same geometry is a necessary, not universal sufficient key across unseen external mutation; zero mismatches in these replays.','Renderer selection repeats are within each OBJ draw, before any subsequent state writer.','Full-width clipped call eligibility does not price the scalar-to-NEON replacement.','VRAM flag redundancy may be low cost; a new branch can cost more than the stores.']}
 (OUT/'qualification.json').write_text(json.dumps(data,indent=2)+'\n');print('PASS 9600 exact original-command calls; source opportunities counted, no A7 saving inferred')
if __name__=='__main__':main()
