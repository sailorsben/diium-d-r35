"""Attribute sampled PCs to exact ELF symbols; mock data never physical time."""
from pathlib import Path
from hashlib import sha256
from collections import Counter
import bisect,csv,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
def kv(p):return dict(l.split('=',1) for l in p.read_text().splitlines() if '=' in l)
def rows(p):return list(csv.DictReader(l for l in p.read_text().splitlines() if not l.startswith('#')))
def group(name):
 if name=='OUTSIDE_CORE':return 'main_host_or_libraries'
 if name.startswith('dsp_'):return 'DSP'
 if name.startswith(('spc_','S9xAPU','rb_')):return 'SPC_APU_other'
 if name.startswith(('Op','S9xGetByte','S9xSetByte','S9xGetWord','S9xSetWord')):return '65C816_ops_memory'
 if name.startswith(('S9xDoDMA','S9xDoHDMA','d35_dma')):return 'DMA'
 if name.startswith(('Draw','d35_fused_band','d35_geometry_draw','d35_band','S9xUpdateScreen','S9xComputeClip','S9xSetupOBJ','ConvertTile','d35_palette','d35_color')):return 'PPU_render'
 if name.startswith(('S9xSetPPU','S9xGetPPU','S9xFixColour')):return 'PPU_registers'
 if name.startswith(('retro_run','S9xMainLoop','S9xDoHBlank')):return 'mixed_core_scheduler'
 if name.startswith(('audio_','sa_callback','resampler_')):return 'core_audio_delivery'
 return 'core_other'
def analyze(base,allow_mock=False):
 base=base.resolve()
 plan=json.loads((base/'plan.json').read_text());assert plan['version']=='1.19-pc-profile1'
 core=base/'cores/demand.so';assert sha256(core.read_bytes()).hexdigest()=='1eaf05f36adcbc8286de5777cc47f1cf24a588856a2b0a85e48a9bfa0984e6f8'
 command=['arm-linux-gnueabihf-nm','-S','--defined-only',str(core)]
 if os.name=='nt':command=['wsl','arm-linux-gnueabihf-nm','-S','--defined-only',subprocess.check_output(['wsl','wslpath','-a',core.as_posix()],text=True).strip()]
 nm=subprocess.check_output(command,text=True);symbols=[]
 for l in nm.splitlines():
  p=l.split()
  if len(p)==4 and p[2] in ('t','T') and int(p[1],16):symbols.append((int(p[0],16),int(p[1],16),p[3]))
 symbols.sort();starts=[x[0] for x in symbols]
 def owner(offset):
  if offset==0xffffffff:return 'OUTSIDE_CORE'
  i=bisect.bisect_right(starts,offset)-1
  return symbols[i][2] if i>=0 and offset<symbols[i][0]+symbols[i][1] else 'UNMAPPED_CORE'
 result=[]
 for run in plan['runs']:
  d=base/f"run-{run['run']:03d}";frames=rows(d/'frames.csv');meta=kv(d/'frames.csv');mock=meta['#mock']=='1'
  assert allow_mock or not mock,'Mock PC samples are not physical evidence'
  if not run['PC_sampling']:
   assert not (d/'main-pc.csv').exists();continue
  p=d/'main-pc.csv';data=rows(p);info=kv(p);assert int(info['#error'])==0 and int(info['#dropped'])==0 and int(info['#samples'])==len(data)>0
  valid=[]
  for r in frames:
   if r['pointer_valid']!='1':break
   valid.append(int(r['frame']))
  selected=set(int(r['frame']) for r in frames) if mock else set(valid)
  counted=Counter();functions=Counter();spans={}
  for r in data:
   if int(r['frame']) not in selected:continue
   name=owner(int(r['ELF_offset'],16));functions[name]+=1;counted[group(name)]+=1
  for label,span in [('early',range(120,240)),('earlier_heavy',range(384,416)),('late_heavy',range(496,536))]:
   hits=Counter(group(owner(int(r['ELF_offset'],16))) for r in data if int(r['frame']) in span and int(r['frame']) in selected)
   spans[label]={'samples':sum(hits.values()),'owners':dict(hits),'all_frames_pointer_valid':all(i in valid for i in span),'sparse_below100':sum(hits.values())<100}
  result.append({**run,'physical':not mock,'metadata':info,'valid_prefix_frames':len(valid),'selected_samples':sum(counted.values()),'selection':'mock_frames_without_physical_validity' if mock else 'valid_frame_pointer_prefix','owners':dict(counted),'top_functions':functions.most_common(20),'spans':spans})
 return {'physical':not allow_mock,'runs':result,'estimated_A7_ms':None,'limits':['Symbol ownership includes inlined work; scheduler remains explicitly mixed.','Outside-core samples include host callbacks/libraries, not workers.','Requested1ms is not delivered sample resolution; timer overruns are retained and never turned into invented samples.','No QEMU/host timing or sample distribution is an A7 price.','Only the valid frame-pointer prefix is counted; full PCM trace must independently qualify reserve.','No assumed independent/random sampling or confidence interval; short spans may be too sparse.']}
if __name__=='__main__':
 base=Path(sys.argv[1]);r=analyze(base,'--mock' in sys.argv);p=base/'main-pc-analysis.json';p.write_text(json.dumps(r,indent=2)+'\n');print(p)
