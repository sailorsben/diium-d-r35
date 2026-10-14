"""Original-output replay and partial-row census for Meteor/Quasar/Pearl; no timings."""
from pathlib import Path
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor
import json,os,subprocess,statistics,sys
ROOT=Path(__file__).resolve().parent.parent
assert sys.argv[1:] in ([],['--preflight'])
OUT=ROOT/('build/partial-preflight-private-v1' if sys.argv[1:] else 'build/partial-merge-private-v1')
FIELDS=('rows','active_rows','opaque_rows','partial_rows','active_pixels','partial_transparency_only','partial_depth_only','partial_mixed','partial_depth_write_noop','partial_direct_depth_legal','partial_single_full_half','partial_all_pairs_aligned','active_runs_all_rows','partial_full_halves','partial_full_pairs','partial_math_enabled_all_active','partial_fixed_all_active','partial_RGB_write_noop','depth4_probe_tiles','depth4_hidden_tiles','depth4_requested_rows','depth4_probe_row_visits','depth4_single_row_tiles','depth4_hidden_single_row_tiles')
def digest(p):return sha256(p.read_bytes()).hexdigest()
def read(p,prefix):return [list(map(int,l[len(prefix):].split(','))) for l in p.read_text().splitlines() if l.startswith(prefix)]
def main():
 assert not (OUT/'analysis.json').exists() and not (OUT/'exact').exists();(OUT/'exact').mkdir()
 plan=json.loads((ROOT/'build/ability-regression-private-v1/plan.json').read_text());pred=json.loads((ROOT/'evidence/2026-10-13/full-fidelity-paths/prediction.json').read_text());tails={c['case']:c['tail_frames'] for c in pred['cases']}
 def run(c):
  tail=tails[c['seq']];env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib'),'D35_MERGE_FIRST':str(tail[0]),'D35_MERGE_LAST':str(tail[-1])};core=OUT/'profile-core/snes9x2005_plus_libretro.so';log=OUT/f"exact/{c['seq']:03d}.log"
  args=['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(OUT/'profile-compare'),str(ROOT/'build/plus-a7-out/plus-a7.so'),str(core),str(ROOT/'build/plus-a7-out/ff6.sfc'),str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/scene.state"),str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/input.txt"),str(c['observed_effect_id']),'1200']
  with log.open('x') as f:subprocess.run(args,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=240)
  assert 'PASS 1200 calls' in log.read_text();original=ROOT/f"build/common-band-private-v3/exact/{c['seq']:03d}-census.log";assert read(log,'PEARL ')==read(original,'PEARL '),'Observer changed original work';data=read(log,'MERGE ');assert [v[0] for v in data]==tail and all(len(v)==3809 for v in data)
  total={k:statistics.mean(sum(v[1+b*24+i] for b in range(84)) for v in data) for i,k in enumerate(FIELDS)}
  buckets=[]
  for plane in range(2):
   for layer in range(6):
    for mode in range(7):
     at=((plane*6+layer)*7+mode)*24;counts={k:statistics.mean(v[1+at+i] for v in data) for i,k in enumerate(FIELDS)}
     if counts['rows']:buckets.append({'plane':plane,'layer':layer,'mode':mode,**counts})
  masks=[]
  for mode in range(7):
   for mask in range(1,255):
    n=statistics.mean(v[1+2016+mode*256+mask] for v in data)
    if n:masks.append({'mode':mode,'mask_hex':'%02x'%mask,'rows_per_call':n})
  result={'case':c['seq'],'name':c['name'],'frames':tail,'original_output_calls':1200,'original_work_unchanged':True,'core_sha256':digest(core),'log_sha256':digest(log),'totals':total,'buckets':buckets,'mask_shapes':sorted(masks,key=lambda m:-m['rows_per_call'])}
  print(c['name'],json.dumps(total),flush=True);return result
 with ThreadPoolExecutor(max_workers=2) as pool:cases=list(pool.map(run,[c for c in plan['cases'] if c['seq'] in (0,1,8)]))
 result={'passed':True,'cases':cases,'calls':3600,'card_access':False,'A7_timings':False,'QEMU_timings_used':False,'production_gate_passed':False,'fields':FIELDS}
 (OUT/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS exact pixels/PCM/state and unchanged original work for all3600 calls; row counts only')
if __name__=='__main__':main()
