"""Final paired raw-output checks, alignment assertions and overlap census."""
from pathlib import Path
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor
import runpy,json,os,subprocess,statistics
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/demand-final-private-v2'
FIELDS=list(runpy.run_path(str(ROOT/'build/qualify-demand-v1.py'))['FIELDS'])
FIELDS[30:]=['shared_geometry_hidden_main_cells','shared_geometry_hidden_main_rows']
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 assert not (OUT/'qualification.json').exists();(OUT/'exact').mkdir()
 plan=json.loads((ROOT/'build/ability-regression-private-v1/plan.json').read_text())
 env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')}
 def run(job):
  label,c=job;core=OUT/label/'snes9x2005_plus_libretro.so';log=OUT/f"exact/{label}-{c['seq']:03d}.log"
  args=['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(OUT/'compare'),str(ROOT/'build/common-band-private-v3/plus-a7.so'),str(core),str(ROOT/'build/plus-a7-out/ff6.sfc'),str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/scene.state"),str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/input.txt"),str(c['observed_effect_id']),'1200']
  with log.open('x') as f:subprocess.run(args,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=480)
  txt=log.read_text();assert 'PASS 1200 calls' in txt and 'ALIGNED ' in txt
  rows=[list(map(int,l[7:].split(','))) for l in txt.splitlines() if l.startswith('DEMAND ')];assert len(rows)==1200
  total={k:sum(r[j+1] for r in rows) for j,k in enumerate(FIELDS)};heavy=None;fused=None
  if c['seq'] in (1,8):
   indexes=range(384,416) if c['seq']==1 else range(496,530)
   heavy={k:statistics.mean(rows[i][j+1] for i in indexes) for j,k in enumerate(FIELDS)}
   if label=='counted-core':
    assert heavy['geometry_reused_bands']>0 and heavy['direct_frames']==1
    fr=[list(map(int,l[6:].split(','))) for l in txt.splitlines() if l.startswith('FUSED ')];assert len(fr)==1200
    fused=[statistics.mean(fr[i][j+1] for i in indexes) for j in range(32)]
  print('PASS final',label,c['seq'],c['name'],'1200 raw graphics/PCM/state + 64-byte alignment',flush=True)
  return {'label':label,'case':c['seq'],'name':c['name'],'calls':1200,'core_sha256':digest(core),'log_sha256':digest(log),'work_total':total,'heavy_mean':heavy,'fused_heavy_by_index':fused}
 with ThreadPoolExecutor(max_workers=3) as pool:proof=list(pool.map(run,[(label,c) for label in ('core','counted-core') for c in plan['cases']]))
 frozen=json.loads((OUT/'frozen.json').read_text());assert all(digest(ROOT/p)==h for p,h in frozen.items())
 write={'passed':True,'calls':43200,'comparisons':proof,'every_frame_raw_graphics_PCM_geometry':True,'normalized_state_every':30,'alignment_checked':True,'frozen_files_verified':len(frozen),'A7_savings_measured':False,'card_access':False,'production_gate_passed':False}
 (OUT/'qualification.json').write_text(json.dumps(write,indent=2)+'\n');print('PASS final 43200 calls; all prior frozen files exact')
if __name__=='__main__':main()
