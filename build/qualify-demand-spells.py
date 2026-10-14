"""Actual40-epoch ARM controller and native acquired-output qualification."""
from pathlib import Path
from hashlib import sha256
import csv,json,os,re,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/demand-spells-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def kv(p):return dict(l.split('=',1) for l in p.read_text().splitlines() if '=' in l)
def rows(p):return list(csv.DictReader(l for l in p.read_text().splitlines() if not l.startswith('#')))
def main():
 assert not (OUT/'verification.json').exists();plan=json.loads((OUT/'plan.json').read_text())
 assert len(plan['runs'])==40 and len(plan['cases'])==18
 q=json.loads((ROOT/'build/demand-visible-private-v3/qualification.json').read_text())
 assert q['passed'] and len([r for r in q['comparisons'] if r['label']=='core'])==18
 assert all(r['core_sha256']==plan['cores']['demand']['sha256'] for r in q['comparisons'] if r['label']=='core')
 ref=json.loads((ROOT/'build/common-band-private-v3/qualification.json').read_text())
 assert ref['passed'] and len([r for r in ref['exact'] if r['label']=='ordinary'])==18
 assert all(r['core_sha256']==plan['cores']['reference']['sha256'] for r in ref['exact'] if r['label']=='ordinary')
 env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib'),'D35_FULL_HOST_FIXTURE':'1'}
 rom=ROOT/'build/plus-a7-out/ff6.sfc'
 def qemu(args,name,extra=None,timeout=900):
  with (OUT/name).open('x') as f:subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),*map(str,args)],env={**env,**(extra or {})},stdout=f,stderr=subprocess.STDOUT,check=True,timeout=timeout)
 mock=OUT/'mock';mock.mkdir();shutil.copytree(OUT/'cores',mock/'cores');shutil.copytree(OUT/'cases',mock/'cases')
 qemu([OUT/'ability-suite',mock,rom],'mock.log',{'D35_ABILITY_MOCK':'1','D35_MVP_NO_PACING':'1'})
 checked=[]
 for run in plan['runs']:
  d=mock/f"run-{run['run']:03d}";s=kv(d/'last-session.txt');a=rows(d/'animation.csv');f=rows(d/'frames.csv');h=kv(d/'headroom.txt');r=kv(d/'result.txt');b=kv(d/'begin.txt')
  assert s['runs']==s['video_submitted']=='1200' and s['held']==s['video_dupes']=='0' and not s['error']
  assert len(a)==len(f)==1200 and int(kv(d/'animation.csv')['#matching_property_samples'])>0
  assert b['spell']==run['name'] and b['variant']==r['variant']==run['variant'] and int(r['fixture'])==run['fixture']
  assert s['core_crc32']==plan['cores'][run['variant']]['crc32'] and s['build_version']==plan['version'] and r['runner_rc']=='0'
  assert s['phase_profile_available']==s['phase_profile_samples']=='0'
  assert s['audio_remaining_frames']==s['audio_cleared_frames']=='0'
  assert int(s['output_accepted_frames_including_priming'])-int(s['priming_silence_frames'])==int(s['resampled_enqueued_frames'])
  assert h['final_PCM_software_accounting_exact']=='1' and h['final_remaining']==h['final_cleared']=='0'
  assert h['physical']=='0' and h['sampled_warm_20_percent_headroom']=='NOT_PHYSICAL'
  assert all(int(x['pace_wait_ns'])<=int(x['step_ns']) for x in f)
  assert all(x['direct_submitted']=='0' and x['copied_payload_bytes']=='0' for x in f) # null display
  pcm=kv(d/'pcm-full.txt');assert pcm['retained_from']=='0' and not pcm['failure']
  checked.append({**run,'calls':1200,'all_frames_and_PCM':True,'expected_effect_properties_observed':True})
 assert kv(mock/'suite-result.txt')['runs']=='40'
 print('PASS actual40 epochs/48000 calls,18 expected effects, lossless PCM and nonphysical labels',flush=True)
 native=OUT/'native';native.mkdir()
 qemu([OUT/'native-check',rom,OUT/'cores/demand.so',OUT/'cases/000/demand.state',native],'native.log',{'D35_ABILITY_INPUT':str(OUT/'cases/000/input.txt'),'D35_ABILITY_EXPECTED':str(OUT/'cases/000/expected.bin')},timeout=120)
 assert 'PASS: consuming native provider' in (OUT/'native.log').read_text() and 'direct-output callbacks in actual spell measurement runner' in (OUT/'native.log').read_text()
 fixture=OUT/'fixture-launch.sh';fixture.write_text((OUT/'launch.sh').read_text().replace('BASE=/usr/retro/snes-demand-spells1','BASE=$D35_MVP_BASE').replace('TRIGGER=/usr/retro/snes-mvp','TRIGGER=$D35_MVP_BASE'),newline='\n')
 with (OUT/'wrapper.log').open('x') as f:subprocess.run([sys.executable,str(ROOT/'build/ability-suite-private-v1/wrapper-check.py'),str(OUT/'wrapper-fixtures')],env={**env,'D35_WRAPPER_UNDER_TEST':str(fixture)},stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
 assert 'zero diagnostic card writes or global sync during ready child' in (OUT/'wrapper.log').read_text()
 assert max(tuple(map(int,m)) for m in re.findall(r'GLIBC_(\d+)\.(\d+)',(OUT/'abi.txt').read_text()))<=(2,30)
 for n,h in json.loads((ROOT/'build/demand-visible-private-v3/frozen.json').read_text()).items():assert digest(ROOT/n)==h,n
 sources=[ROOT/'build'/n for n in ('prepare-demand-spells.py','build-demand-spells.sh','qualify-demand-spells.py')]
 sources+=list((OUT/'runner').glob('*.[ch]'))+[OUT/'main.c',OUT/'combined-identity.h']
 payload=[OUT/n for n in ('ability-suite','launch.sh','dispatch.sh','ROM-PATH.txt','plan.json')]
 payload+=[p for folder in ('cores','cases') for p in (OUT/folder).rglob('*') if p.is_file()]
 proofs=[OUT/n for n in ('mock.log','native.log','wrapper.log','abi.txt')]
 result={'version':plan['version'],'passed':True,'card_writes':0,'installed':False,'armed':False,
 'measurement_only':True,'production_gate_passed':False,'frameskip':False,'physical_result':'PENDING','QEMU_timing_used':False,
 'actual_epochs':checked,'native_client_qualified':True,'acquired_output_exercised':True,'wrapper_qualified':True,
 'core_exactness_reused_by_hash':['18 raw original-command v3 contexts','18 reference contexts'],
 'source_hashes':{p.relative_to(ROOT).as_posix():digest(p) for p in sources},
 'payload_hashes':{p.relative_to(OUT).as_posix():digest(p) for p in payload},'proof_hashes':{p.name:digest(p) for p in proofs},
 'limits':plan['limits']}
 (OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS new spell controller, native failure/retry/deficit/acquired output, wrapper and ABI; no card writes',flush=True)
if __name__=='__main__':main()
