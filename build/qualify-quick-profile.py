"""Run the actual ARM controller under QEMU; no emulator timing claims."""
from pathlib import Path
from hashlib import sha256
import csv,json,os,re,shutil,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/quick-profile-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def rows(p):return list(csv.DictReader(s for s in p.read_text().splitlines() if not s.startswith('#')))
def kv(p):return dict(s.split('=',1) for s in p.read_text().splitlines() if '=' in s)
def main():
 assert not (OUT/'qualification.json').exists()
 plan=json.loads((OUT/'plan.json').read_text());proof=ROOT/'build/common-band-private-v3/qualification.json';q=json.loads(proof.read_text())
 assert q['passed'] and len([r for r in q['exact'] if r['label']=='ordinary'])==18
 for c in plan['cores'].values():assert all(r['core_sha256']==c['sha256'] for r in q['exact'] if r['label']=='ordinary')
 attempt=1
 while (OUT/f'mock-{attempt}').exists():attempt+=1
 mock=OUT/f'mock-{attempt}';mock.mkdir();shutil.copytree(OUT/'cores',mock/'cores');shutil.copytree(OUT/'cases',mock/'cases')
 env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib'),'D35_FULL_HOST_FIXTURE':'1'}
 with (OUT/f'mock-{attempt}.log').open('x') as f:
  subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(OUT/'ability-suite'),str(mock),str(ROOT/'build/plus-a7-out/ff6.sfc')],env={**env,'D35_ABILITY_MOCK':'1','D35_MVP_NO_PACING':'1'},stdout=f,stderr=subprocess.STDOUT,check=True,timeout=240)
 actual=[];animations={}
 for r in plan['runs']:
  d=mock/f"run-{r['run']:03d}";s=kv(d/'last-session.txt');p=rows(d/'phases.csv');frames=rows(d/'frames.csv');a=rows(d/'animation.csv');h=kv(d/'headroom.txt')
  assert s['build_version']=='1.19-profile1' and s['runs']==s['video_submitted']=='800' and s['held']=='0' and not s['error']
  assert len(p)==len(frames)==len(a)==800 and int(kv(d/'animation.csv')['#matching_property_samples'])>0
  assert s['core_crc32']==plan['cores'][r['variant']]['crc32']
  assert h['physical']=='0' and h['final_PCM_software_accounting_exact']=='1' and h['final_remaining']=='0' and h['final_cleared']=='0'
  sampled=[x for x in p if int(x['sampled'])]
  assert len(sampled)==(100 if r['variant']=='profile' else 0)
  assert all(int(x['frame'])%8==3 and int(x['ppu_cpu_ns'])>0 and int(x['apu_inclusive_cpu_ns'])>0 and int(x['video_callbacks'])==1 for x in sampled)
  assert all(int(x['ppu_cpu_ns'])==int(x['apu_inclusive_cpu_ns'])==int(x['audio_callback_cpu_ns'])==int(x['video_callback_cpu_ns'])==0 for x in p if not int(x['sampled']))
  animations[r['run']]=[{k:v for k,v in x.items() if k!='observer_ns'} for x in a]
  actual.append({**r,'calls':800,'all_frames_submitted':True,'PCM_accounting_exact':True,'phase_samples':len(sampled),'QEMU_performance_evidence':False})
 assert animations[0]==animations[1] and animations[2]==animations[3]
 assert kv(mock/'suite-result.txt')['runs']=='4'
 wrapper=(OUT/'launch.sh').read_text().replace('BASE=/usr/retro/snes-profile1','BASE=$D35_MVP_BASE').replace('TRIGGER=/usr/retro/snes-mvp','TRIGGER=$D35_MVP_BASE')
 (OUT/'fixture-launch.sh').write_text(wrapper,newline='\n')
 with (OUT/f'wrapper-{attempt}.log').open('x') as f:
  subprocess.run(['python3',str(ROOT/'build/ability-suite-private-v1/wrapper-check.py'),str(OUT/f'wrapper-fixtures-{attempt}')],env={**env,'D35_WRAPPER_UNDER_TEST':str(OUT/'fixture-launch.sh')},stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
 assert 'zero diagnostic card writes or global sync during ready child' in (OUT/f'wrapper-{attempt}.log').read_text()
 assert max(tuple(map(int,m)) for m in re.findall(r'GLIBC_(\d+)\.(\d+)',(OUT/'abi.txt').read_text()))<=(2,30)
 # Provider, worker, native fault handling and headroom implementation unchanged.
 old=ROOT/'build/combined-test-private-v1';oldq=json.loads((old/'qualification.json').read_text());assert oldq['native_client_qualified']
 for name in ('audio-owner.c','native-pcm.c','platform.c','board.c','combined-headroom.h'):
  assert (OUT/'runner'/name).read_text().replace('1.19-profile1','1.19-combined1')==(old/'runner'/name).read_text(),name
 result={'version':plan['version'],'passed':True,'measurement_only':True,'production_gate_passed':False,'frameskip':False,'A7_saving_measured':False,'QEMU_timings_used':False,'card_writes':0,'actual_controller_runs':actual,'phase_ABI_qualified':True,'control_profile_animation_observations_equal':True,'native_client_qualified':True,'native_client_proof_reused_by_source_identity':True,'wrapper_qualified':True,'runner_sha256':digest(OUT/'ability-suite'),'wrapper_sha256':digest(OUT/'launch.sh'),'cores':plan['cores'],'reused_proofs':{proof.relative_to(ROOT).as_posix():digest(proof),(old/'qualification.json').relative_to(ROOT).as_posix():digest(old/'qualification.json')}}
 (OUT/'qualification.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: actual four-epoch ARM controller; 3200 frames; 200 phase samples; same gameplay observations; wrapper and ABI; no A7 timing claim')
if __name__=='__main__':main()
