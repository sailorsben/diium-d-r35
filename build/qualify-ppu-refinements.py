"""Actual original-command18-context replays for isolated and combined PPU cores."""
from pathlib import Path
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor,as_completed
import json,os,statistics,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ppu-refinements-private-v4'
LABELS=('obj','obj-counted','shapes','shapes-counted','bulk','bulk-counted','combined','combined-counted')
FIELDS=('opaque_depth_rows','clip_plain','clip_add','clip_addhalf','clip_sub','clip_subhalf','clip_fixedaddhalf','clip_fixedsubhalf','OBJ_simple_starts','OBJ_empty_starts','OBJ_table_entries_written','OBJ_table_reads','plain3_rows','plain_half_rows','bulk_original_row_fill_calls','plain_partial_classifier_calls','bulk_depth_bytes','math_partial_classifier_calls','math_scalar_visible_pixels')
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 assert not (OUT/'qualification.json').exists();assert json.loads((OUT/'seams.json').read_text())['passed']
 plan=json.loads((ROOT/'build/ability-regression-private-v1/plan.json').read_text());exact=OUT/'exact';exact.mkdir()
 env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')}
 def run(job):
  label,c=job;core=OUT/label/'snes9x2005_plus_libretro.so';log=exact/f"{label}-{c['seq']:03d}.log"
  args=['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(OUT/'compare'),str(ROOT/'build/demand-visible-private-v3/core/snes9x2005_plus_libretro.so'),str(core),str(ROOT/'build/plus-a7-out/ff6.sfc'),str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/scene.state"),str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/input.txt"),str(c['observed_effect_id']),'1200']
  with log.open('x') as f:subprocess.run(args,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=600)
  txt=log.read_text();assert 'PASS 1200 calls' in txt and 'ALIGNED ' in txt
  ppu=[list(map(int,l[4:].split(','))) for l in txt.splitlines() if l.startswith('PPU ')]
  assert len(ppu)==(1200 if label.endswith('-counted') else 0)
  total={k:sum(r[j+1] for r in ppu) for j,k in enumerate(FIELDS)} if ppu else None
  peaks={}
  if ppu:
   for name,span in [('old_Meteor',range(384,416)),('late_Meteor',range(496,536))] if c['seq']==1 else [('Quasar',range(496,542))] if c['seq']==8 else []:
    peaks[name]={k:statistics.mean(ppu[i][j+1] for i in span) for j,k in enumerate(FIELDS)}
  return {'label':label,'case':c['seq'],'name':c['name'],'calls':1200,'core_sha256':digest(core),'log_sha256':digest(log),'work_counts':total,'peak_mean_requests':peaks}
 jobs=[(label,c) for label in LABELS for c in plan['cases']];results=[]
 with ThreadPoolExecutor(max_workers=4) as pool:
  futures=[pool.submit(run,j) for j in jobs]
  for f in as_completed(futures):
   r=f.result();results.append(r);print('PASS',r['label'],r['name'],len(results),'/',len(jobs),flush=True)
 results.sort(key=lambda r:(LABELS.index(r['label']),r['case']))
 for n,h in json.loads((OUT/'frozen.json').read_text()).items():assert digest(ROOT/n)==h,n
 q={'passed':True,'comparisons':results,'raw_graphics_PCM_geometry_calls':len(results)*1200,'normalized_state_every':30,'ordinary_variants':list(LABELS[::2]),
 'reference':'frozen demand-v3','A7_saving_measured':False,'card_writes':0,'production_gate_passed':False}
 (OUT/'qualification.json').write_text(json.dumps(q,indent=2)+'\n');print('PASS full PPU isolation/combination qualification, prior hashes exact',flush=True)
if __name__=='__main__':main()
