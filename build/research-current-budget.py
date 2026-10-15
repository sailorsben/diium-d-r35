"""Disjoint measured CPU owners from returned v3 controls, no inferred inner time."""
from pathlib import Path
from hashlib import sha256
import csv,json,statistics
ROOT=Path(__file__).resolve().parent.parent
ARCH=ROOT/'device-evidence/a7-pair-before-20261014T231531Z'
def main():
 out=ROOT/'build/compiler-research-private-v1/current-budget.json';assert not out.exists()
 base=ARCH/'retro/snes-ppu-test1';plan=json.loads((base/'plan.json').read_text());results=[];inputs={}
 for run in plan['runs']:
  if run['variant']!='reference':continue
  p=base/f"run-{run['run']:03d}/frames.csv";inputs[p.relative_to(ROOT).as_posix()]=sha256(p.read_bytes()).hexdigest()
  rows=list(csv.DictReader(l for l in p.read_text().splitlines() if not l.startswith('#')));valid={};pa=pv=0
  for r in rows:
   a,v=int(r['audio_worker_cpu_ns']),int(r['video_worker_cpu_ns'])
   if r['pointer_valid']!='1' or a<pa or v<pv:break
   core=int(r['cpu_ns']);main=int(r['main_step_cpu_ns'])
   valid[int(r['frame'])]={'core_including_callbacks_ms':core/1e6,'other_main_ms':(main-core)/1e6,'audio_worker_ms':(a-pa)/1e6,'display_worker_ms':(v-pv)/1e6,'total_recorded_CPU_ms':(main+a-pa+v-pv)/1e6};pa,pv=a,v
  windows=[list(range(i,i+16)) for i in range(120,max(valid,default=-1)-14) if all(j in valid for j in range(i,i+16))]
  heavy=max(windows,key=lambda w:statistics.mean(valid[j]['total_recorded_CPU_ms'] for j in w)) if windows else []
  groups={'early':list(range(120,240)),'heaviest_valid16':heavy}
  groups['fixed_heavy']=list(range(384,416)) if run['fixture']==1 else list(range(496,542))
  result={}
  for name,frames in groups.items():
   result[name]={'frames':frames,'all_valid':bool(frames) and all(j in valid for j in frames)}
   if result[name]['all_valid']:result[name]['mean_ms']={k:statistics.mean(valid[j][k] for j in frames) for k in valid[frames[0]]}
  results.append({**run,'valid_prefix_calls':len(valid),'groups':result})
 packet={'current_v3_control_core_sha256':plan['cores']['reference']['sha256'],'measured_on_A7':True,'inward_PPU_CPU_SPC_DSP_time_available':False,'controls':results,'inputs':inputs,'limits':['Core CPU includes callbacks, main dispatch and all emulated engines.','Other-main difference is measured timing regions, not a pure subsystem price.','Worker CPU increments are disjoint; other OS/kernel work is not fully counted.','Only valid pointer prefix is used; no full Meteor recovery or sustained frequency claim.']}
 out.write_text(json.dumps(packet,indent=2)+'\n')
 for r in results:print(r['name'],r['repeat'],r['groups']['heaviest_valid16']['mean_ms'])
if __name__=='__main__':main()
