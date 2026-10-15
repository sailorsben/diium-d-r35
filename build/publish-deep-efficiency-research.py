"""Publish bounded research proofs, never compiler dumps, cores or private states."""
from pathlib import Path
from hashlib import sha256
import json,re,struct,subprocess
ROOT=Path(__file__).resolve().parent.parent
STUDY=ROOT/'build/compiler-research-private-v1'
DEST=ROOT/'evidence/2026-10-14/deep-efficiency-research'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def section(p,wanted):
 b=p.read_bytes();assert b[:6]==b'\x7fELF\x01\x01'
 off=struct.unpack_from('<I',b,32)[0];size,num,strings=struct.unpack_from('<HHH',b,46)
 headers=[struct.unpack_from('<10I',b,off+i*size) for i in range(num)];s=headers[strings];names=b[s[4]:s[4]+s[5]]
 for h in headers:
  name=names[h[0]:].split(b'\0',1)[0].decode()
  if name==wanted:return b[h[4]:h[4]+h[5]]
 raise AssertionError(wanted)
def main():
 assert not DEST.exists();compiler=read(STUDY/'qualification.json');work=read(ROOT/'build/current-work-private-v1/qualification.json');priority=read(ROOT/'build/priority-research-private-v1/qualification.json')
 pc=ROOT/'build/current-pc-profile-private-v1';ready=read(pc/'ready.json');assert compiler['passed'] and work['passed'] and priority['passed'] and ready['ready']
 for n,h in ready['additional_sources'].items():assert digest(ROOT/n)==h,n
 for folder in (STUDY,ROOT/'build/current-work-private-v1',ROOT/'build/priority-research-private-v1'):
  for n,h in read(folder/'frozen.json').items():assert digest(ROOT/n)==h,n
 report={'toolchain':subprocess.check_output(['wsl','arm-linux-gnueabihf-gcc','--version'],text=True).splitlines()[0],'controls':{}}
 inputs={}
 for label in ('baseline','combined','combined-one','combined-flag-local','combined-apu-boundary'):
  base=STUDY/label;binary=base/'snes9x2005_plus_libretro.so';inputs[binary.relative_to(ROOT).as_posix()]=digest(binary)
  passes=[];locations=[]
  for p in base.rglob('*'):
   if not p.is_file() or not p.name.endswith(('.unswitch','.optimized')):continue
   text=p.read_text()
   if 'spc_run_until_' in text or 'allow_time_overflow = 0;' in text:
    inputs[p.relative_to(ROOT).as_posix()]=digest(p)
   for part in text.split(';; Function '):
    if part.startswith('spc_run_until_'):
     locations.append(p.relative_to(base).as_posix())
     passes.extend(l.strip() for l in part.splitlines() if 'optimized: unswitch' in l)
  optimized=[p for p in base.rglob('*.optimized') if 'spc_run_until_' in p.read_text() and 'allow_time_overflow = 0;' in p.read_text()]
  report['controls'][label]={'core_sha256':digest(binary),'text_sha256':sha256(section(binary,'.text')).hexdigest(),'SPC_unswitch_reports':passes,'SPC_report_locations':locations,'SPC_and_APU_init_same_optimized_unit':bool(optimized)}
 report['baseline_byte_exact_reproduction']=digest(STUDY/'baseline/snes9x2005_plus_libretro.so')==digest(ROOT/'build/demand-visible-private-v3/core/snes9x2005_plus_libretro.so')
 report['combined_text_exact_reproduction']=section(STUDY/'combined/snes9x2005_plus_libretro.so','.text')==section(ROOT/'build/ppu-refinements-private-v5/combined/snes9x2005_plus_libretro.so','.text')
 left=STUDY/'baseline-apu-boundary/source/apu_blargg.o';right=STUDY/'combined-apu-boundary/source/apu_blargg.o'
 assert digest(left)==digest(right);report['fixed_APU_object_sha256']=digest(left);report['APU_object_identical_across_PPU_changes']=True
 assert report['baseline_byte_exact_reproduction'] and report['combined_text_exact_reproduction']
 old={c['name']:c for c in work['cases']};deltas={}
 for c in priority['cases']:
  if c['name'] not in old:continue
  deltas[c['name']]={}
  for span,m in c['means'].items():
   before=old[c['name']]['means'][span]
   keys=('main_RGB_writes','overwritten_main_RGB_writes','math_pixel_writes','overwritten_math_writes','plain_batch_row_visits','math_batch_row_visits','batch_RGB_vector_expansions','sparse_plain_pixel_stores','BG_draw_invocations','NEON_palette_preparations','decoded_tiles')
   deltas[c['name']][span]={k:{'before':before[k],'after':m[k],'removed':before[k]-m[k]} for k in keys}
 packets={'compiler.json':report,'compiler-qualification.json':compiler,'current-work.json':work,'current-A7-budget.json':read(STUDY/'current-budget.json'),'priority-hypothesis.json':priority,'priority-deltas.json':deltas,'PC-diagnostic-ready.json':ready,'PC-diagnostic-plan.json':read(pc/'plan.json'),'PC-diagnostic-qualification.json':read(pc/'verification.json')}
 proofs=[STUDY/'qualification.json',STUDY/'current-budget.json',ROOT/'build/current-work-private-v1/qualification.json',ROOT/'build/priority-research-private-v1/qualification.json',pc/'verification.json',pc/'ready.json',pc/'mock/main-pc-analysis.json',STUDY/'pc-arm.log',STUDY/'pc-host3.log']
 for p in proofs:inputs[p.relative_to(ROOT).as_posix()]=digest(p)
 for pattern in ('research-*.py','*current-work*','*priority-research*','*compiler-research*','*main-pc*','*current-pc-profile*','publish-deep-efficiency-research.py'):
  for p in (ROOT/'build').glob(pattern):
   if p.is_file():inputs[p.relative_to(ROOT).as_posix()]=digest(p)
 packets['inputs.json']=inputs
 packets['decision.json']={'strongest_verified_work_removal':'state-based mode1 highest-priority BG3 scheduling','A7_net_saving_ms':None,'current_inner_A7_function_time_measured':False,'optimization_candidate_installed':False,'card_access':False,'exact_graphics_PCM_state_calls':43200,'unchanged_core_controller_calls':4800,'next_step':'Explicitly authorized unchanged-v3 PC/control diagnostic before any optimization install','added_costs':['two extra BG traversals','priority-filter guards and skipped tile visits','codegen/layout/cache interactions','all existing depth, transparency, main/sub and raster work retained'],'falsifier':'Reject if valid full effect/recovery matched net cost or cumulative reserve/pointers do not improve after independently qualified implementation.'}
 mpath=ROOT/'evidence/manifest.json';manifest=read(mpath)
 for e in manifest['entries']:assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
 DEST.mkdir(parents=True)
 for name,obj in packets.items():
  p=DEST/name;p.write_text(json.dumps(obj,indent=2)+'\n')
  manifest['entries'].append({'source':'build/publish-deep-efficiency-research.py','published':p.relative_to(ROOT).as_posix(),'source_sha256':digest(Path(__file__)),'published_sha256':digest(p),'bytes':p.stat().st_size,'normalized':True})
 mpath.write_text(json.dumps(manifest,indent=2)+'\n')
 print('Published pinned compiler controls, current work/budget, priority proof and unchanged-core diagnostic readiness; no card writes')
if __name__=='__main__':main()
