"""Verify and analyze an immutable profile1 card archive; no device writes."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,statistics,sys
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main(archive):
 assert archive.is_relative_to(ROOT/'device-evidence')
 raw=json.loads((archive/'archive.json').read_text());assert raw['fat_clean'] and raw['card_writes']==0
 base=archive/'retro/snes-profile1';frozen=ROOT/'build/quick-profile-private-v1/verification.json';q=json.loads(frozen.read_text())
 installed=json.loads((ROOT/'evidence/2026-10-13/quick-profile/installation.json').read_text())
 for n,h in installed['payload_hashes'].items():assert digest(base/n)==h,n
 assert digest(base/'suite-identity.json')==digest(frozen)
 for group in ('source_hashes','payload_hashes','proof_hashes'):
  for n,h in q[group].items():assert digest(ROOT/n)==h,n
 old=ROOT/'device-evidence'/q['archive'];prior=json.loads((old/'archive.json').read_text())
 changes=[]
 for e in prior['all_retro_files']:
  path=archive/e['path']
  if not path.exists() or digest(path)!=e['sha256']:changes.append(e['path'])
 assert set(changes)=={'retro/snes-mvp/launch.sh','retro/swapfile'},changes
 assert not list((archive/'retro').rglob('armed'))
 assert digest(archive/'retro/snes-mvp/launch.sh')==installed['dispatch_sha256']
 installer=module('profile_installer',ROOT/'build/install-quick-profile.py')
 assert (base/'last-launch').read_bytes()==installer.MARKER
 guard=module('profile_guard',ROOT/'build/package-snes-1.19.py')
 for n,h in guard.BOOT_EXPECTED.items():assert digest(archive/n)==h,n
 assert digest(archive/'retro/init')==guard.baseline.HOOK
 assert digest(archive/'retro/snes-mvp/plus-a7.so')=='80b36f61971e4e649843ea23dc051cd185ba699c413ff9023c93f548e2c738b8'
 report=module('profile_report',ROOT/'build/report-quick-profile.py');plan=json.loads((base/'plan.json').read_text())
 assert report.kv(base/'suite-result.txt')['runs']=='4'
 result=report.analyze(base);runs=[];records={};names={1:'Meteor',8:'Quasar'}
 for run in plan['runs']:
  d=base/f"run-{run['run']:03d}";s=report.kv(d/'last-session.txt');h=report.kv(d/'headroom.txt');end=report.kv(d/'result.txt');ph=report.rows(d/'phases.csv');fr=report.rows(d/'frames.csv');anim=report.kv(d/'animation.csv')
  assert s['build_version']==plan['version'] and int(s['runs'])==len(ph)==len(fr)
  assert end['audio_worker_joined']==end['display_idle']=='1' and int(anim['#matching_property_samples'])>0
  assert s['held']==s['video_dupes']=='0' and h['final_PCM_software_accounting_exact']=='1' and h['final_cleared']=='0'
  assert all(int(p['sampled'])==(int(run['variant']=='profile') if p['frame']%8==3 else 0) for p in ph)
  records[run['run']]={'phases':ph,'frames':fr}
  parts=[];pa=pv=0
  for f in fr:
   a,v=f['audio_worker_cpu_ns'],f['video_worker_cpu_ns'];assert a>=pa and v>=pv
   parts.append({'core':f['cpu_ns'],'other_main':f['main_step_cpu_ns']-f['cpu_ns'],'audio_worker':a-pa,'display_worker':v-pv});pa,pv=a,v
  windows=[]
  # The terminal core call is interrupted by a native fault. Do not price it as
  # a complete rendered call, even though its CPU cost is an authentic sample.
  for i in range(120,len(fr)-16):
   sums={k:statistics.mean(p[k] for p in parts[i:i+16]) for k in parts[i]}
   windows.append({'first':i,'last':i+15,'components_us':{k:v/1000 for k,v in sums.items()},'CPU_sum_mean_us':sum(sums.values())/1000,'invalid_PCM_pointer_frames':sum(not f['pointer_valid'] for f in fr[i:i+16])})
  worst=max(windows,key=lambda w:w['CPU_sum_mean_us']);valid=max((w for w in windows if not w['invalid_PCM_pointer_frames']),key=lambda w:w['CPU_sum_mean_us'])
  for w in (worst,valid):w['deadline_deficit_us']=w['CPU_sum_mean_us']-16688.1545;w['saving_for_20_percent_margin_us']=w['CPU_sum_mean_us']-13350.5236
  runs.append({**run,'name':names[run['fixture']],'calls':len(ph),'video_submitted':int(s['video_submitted']),'flipped':int(s['display_flipped']),'sampled_calls':sum(p['sampled'] for p in ph),'error':s['error'],'native_error':s['pcm_error_detail'],'first_invalid_PCM_pointer':next((f['frame'] for f in fr if not f['pointer_valid']),None),'remaining_PCM_frames':int(h['final_remaining']),'cleared_PCM_frames':int(h['final_cleared']),'frequency_khz':sorted({f['freq_before_khz'] for f in fr}|{f['freq_after_khz'] for f in fr}),'frequency_pin':report.kv(d/'frames.csv').get('#pin'),'clock_loop_mean_ns':report.kv(d/'phases.csv').get('#clock_loop_mean_ns'),'worst_nonterminal_16':worst,'worst_pointer_valid_16':valid})
 growth=[]
 for runid,lo,hi in ((1,384,407),(2,496,507)):
  ps=records[runid]['phases'];baseline=[p for p in ps if p['sampled'] and 120<=p['frame']<=239];heavy=[p for p in ps if p['sampled'] and lo<=p['frame']<=hi]
  keys=('core_cpu_ns','ppu_cpu_ns','apu_inclusive_cpu_ns','video_callback_cpu_ns','audio_callback_cpu_ns')
  means=lambda a:{k:statistics.mean(p[k] for p in a)/1000 for k in keys}
  a,b=means(baseline),means(heavy);delta={k:b[k]-a[k] for k in keys}
  # Video callback is after S9xMainLoop in this exact core. Audio callback can
  # run under S9xAPUExecute or outside it; total audio CPU cannot be blindly
  # subtracted again from the residual or the APU region.
  residual=lambda x:x['core_cpu_ns']-x['ppu_cpu_ns']-x['apu_inclusive_cpu_ns']-x['video_callback_cpu_ns']
  growth.append({'run':runid,'name':names[plan['runs'][runid]['fixture']],'reference_frames':[120,239],'heavy_frames':[lo,hi],'reference_samples':len(baseline),'heavy_samples':len(heavy),'reference_means_us':a,'heavy_means_us':b,'growth_us':delta,'PPU_share_of_main_CPU_growth_percent':100*delta['ppu_cpu_ns']/delta['core_cpu_ns'],'residual_excluding_video_us':{'reference':residual(a),'heavy':residual(b)},'heavy_distributions_us':{k:report.distribution([p[k] for p in heavy]) for k in keys},'sampled_frames':[p['frame'] for p in heavy]})
 sensitivity=[]
 for g,c in zip(growth,(runs[0],runs[3])):
  ppu=g['heavy_means_us']['ppu_cpu_ns'];need=c['worst_nonterminal_16']['saving_for_20_percent_margin_us'];gap=c['worst_nonterminal_16']['deadline_deficit_us']
  sensitivity.append({'name':g['name'],'planning_only':'conditional fractions of observer-inclusive sampled PPU scale; not measured candidate savings','control_deadline_deficit_us':gap,'control_20_percent_margin_saving_us':need,'conditional_PPU_savings_us':{str(f):ppu*f for f in (.1,.2,.3,.5)},'PPU_fraction_for_deadline':gap/ppu,'PPU_fraction_for_20_percent_margin':need/ppu})
 out=archive/'quick-profile-analysis';out.mkdir(exist_ok=True)
 live=json.loads((archive/'profile-live-readback.json').read_text());assert live['card_writes']==0 and live['one_shot_unarmed'] and live['original_ROM_zip_sha256']==installed['original_ROM_zip_sha256']
 integrity={'archive':archive.name,'files':len(raw['all_retro_files']),'bytes':sum(e['bytes'] for e in raw['all_retro_files']),'clean_FAT':True,'card_writes':0,'payload_files_verified':len(installed['payload_hashes']),'local_frozen_sources_payload_proofs_verified':True,'previous_retro_changed':changes,'previous_retro_unchanged':len(prior['all_retro_files'])-len(changes),'marker_consumed':True,'production_core_boot_files_unchanged':True,'previous_progress_unchanged':True,'original_ROM_zip_sha256':live['original_ROM_zip_sha256'],'ROM_live_readback_verified':True,'production_gate_passed':False}
 assert all(report.kv(base/f"run-{i:03d}/last-session.txt")['rom_crc32']=='a27f1c7a' and report.kv(base/f"run-{i:03d}/last-session.txt")['rom_bytes']=='3145728' for i in range(4))
 payload={'integrity':integrity,'runs':runs,'growth':growth,'sensitivity':sensitivity,'observer_disturbance':result['aligned_observer_disturbance'],'limits':['Only 3 Meteor / 2 Quasar samples in narrow late intervals; descriptive tails only.','Quasar profile terminates before prior worst508-529 interval; never extrapolate it as a complete peak.','CPU regions include instrumentation; no clock-loop or aligned-control calibration subtraction.','APU includes nested audio publication where invoked, but final audio upload may lie outside it.','Residual excludes measured video CPU, but still includes port-driven SPC, dispatch, final upload and observer work.','Native errno77, nonzero remaining PCM and pointer drift prevent full-effect/headroom acceptance.','Current broad PPU timing cannot price BG/OBJ/partial/clip microkernels individually.']}
 for name,value in (('analysis.json',payload),('integrity.json',integrity),('broad-report.json',result)):(out/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
 inputs=[frozen,base/'suite-identity.json',base/'plan.json',archive/'archive.json',archive/'profile-live-readback.json',ROOT/'build/report-quick-profile.py',Path(__file__).resolve()]
 inputs += [d/n for d in sorted(base.glob('run-*')) if d.is_dir() for n in ('phases.csv','frames.csv','last-session.txt','headroom.txt','result.txt','animation.csv')]
 (out/'inputs.json').write_text(json.dumps({'inputs':{p.relative_to(ROOT).as_posix():digest(p) for p in inputs}},indent=2)+'\n')
 print(json.dumps({'archive':archive.name,'integrity':integrity,'runs':[{k:r[k] for k in ('run','calls','video_submitted','sampled_calls','first_invalid_PCM_pointer')} for r in runs],'growth':[{'name':g['name'],'PPU_growth_percent':g['PPU_share_of_main_CPU_growth_percent']} for g in growth]},indent=2))
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
