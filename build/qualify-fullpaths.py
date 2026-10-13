"""New combination exactness and actual 100-run controller qualification.
Unchanged standalone core proof is reused by hash; no QEMU timing is A7 evidence.
"""
from pathlib import Path
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor
import csv,json,os,re,subprocess,sys,shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/fullpaths-private-v2'
BASE=ROOT/'build/ability-regression-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def rows(p):return list(csv.DictReader(s for s in p.read_text().splitlines() if not s.startswith('#')))
def kv(p):return dict(s.split('=',1) for s in p.read_text().splitlines() if '=' in s)
def qualify():
 assert not (OUT/'qualification.json').exists()
 plan=json.loads((OUT/'plan.json').read_text());env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib'),'D35_FULL_HOST_FIXTURE':'1'}
 ref=ROOT/'build/plus-a7-out/plus-a7.so';rom=ROOT/'build/plus-a7-out/ff6.sfc';core=OUT/'cores/combined.so'
 assert digest(ref)=='80b36f61971e4e649843ea23dc051cd185ba699c413ff9023c93f548e2c738b8'
 reused=[]
 for label,folder in (('fixed','fixed-rows-private-v3'),('subscreen','subscreen-rows-private-v1'),('dsp','dsp-dead-work-private-v1')):
  p=ROOT/f'build/{folder}/qualification.json';q=json.loads(p.read_text());assert q['passed'] and q['core_sha256']==digest(OUT/f'cores/{label}.so')
  reused.append({'variant':label,'proof':str(p.relative_to(ROOT)),'proof_sha256':digest(p),'core_sha256':q['core_sha256'],'cases':18,'calls_per_case':1200})
 (OUT/'exact').mkdir()
 cases=json.loads((BASE/'plan.json').read_text())['cases']
 def compare(c):
  log=OUT/f"exact/{c['seq']:03d}-combined.log"
  with log.open('x') as f:subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(OUT/'compare'),str(ref),str(core),str(rom),str(BASE/f"cases/{c['seq']:03d}/scene.state"),str(BASE/f"cases/{c['seq']:03d}/input.txt"),str(c['observed_effect_id']),'1200'],env=env,check=True,stdout=f,stderr=subprocess.STDOUT,timeout=180)
  assert 'PASS 1200 calls' in log.read_text();print('combined exact',c['seq'],c['name'],flush=True)
  return {'case':c['seq'],'name':c['name'],'passed':True,'calls':1200,'log_sha256':digest(log)}
 with ThreadPoolExecutor(max_workers=2) as pool:comparisons=list(pool.map(compare,cases))
 mock=OUT/'mock';mock.mkdir();shutil.copytree(OUT/'cores',mock/'cores');shutil.copytree(OUT/'cases',mock/'cases')
 with (OUT/'mock.log').open('x') as f:subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(OUT/'ability-suite'),str(mock),str(rom)],env={**env,'D35_ABILITY_MOCK':'1','D35_MVP_NO_PACING':'1'},check=True,stdout=f,stderr=subprocess.STDOUT,timeout=900)
 actual=[]
 for r in plan['runs']:
  d=mock/f"run-{r['run']:03d}";s=kv(d/'last-session.txt');a=rows(d/'animation.csv');p=rows(d/'frames.csv');h=kv(d/'headroom.txt');result=kv(d/'result.txt')
  assert s['runs']==s['video_submitted']=='1200' and s['held']=='0' and not s['error']
  assert len(a)==len(p)==1200 and int(kv(d/'animation.csv')['#matching_property_samples'])>0
  assert s['build_version']=='1.19-fullpaths1' and s['core_crc32']==plan['cores'][r['variant']]['crc32']
  assert s['audio_remaining_frames']=='0' and int(s['output_accepted_frames_including_priming'])==int(s['resampled_enqueued_frames'])+int(s['priming_silence_frames'])
  assert h['physical']=='0' and h['sampled_warm_20_percent_headroom']=='NOT_PHYSICAL'
  assert result['variant']==r['variant'] and int(result['fixture'])==r['fixture'] and result['runner_rc']=='0'
  assert all(int(row['pace_wait_ns'])<=int(row['step_ns']) for row in p)
  actual.append({**r,'calls':1200,'requested_properties_observed':True,'all_frames_submitted':True,'PCM_accounting_exact':True})
 assert kv(mock/'suite-result.txt')['runs']=='100'
 print('PASS actual 100-run controller, five core identities, lossless frames/PCM, nonphysical headroom labels',flush=True)
 libs=['-L'+str(ROOT/'build/sysroot/lib'),'-Wl,--no-as-needed']+['-l:'+n for n in ('libdl-2.30.so','libz.so.1','libpthread-2.30.so','librt-2.30.so','libm-2.30.so','libc-2.30.so','libgcc_s.so.1','ld-2.30.so')]
 subprocess.run(['arm-linux-gnueabihf-gcc','-mcpu=cortex-a7','-mfpu=neon-vfpv4','-mfloat-abi=hard','-marm','-fno-stack-protector','-U_TIME_BITS','-D_TIME_BITS=32','-U_FILE_OFFSET_BITS','-D_FILE_OFFSET_BITS=32','-std=gnu99','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-no-pie','-nostdlib','-I'+str(ROOT/'build/snes9x2005/libretro-common/include'),'/usr/arm-linux-gnueabihf/lib/crt1.o',str(OUT/'runner/ability-native-check.c'),str(ROOT/'build/glibc230-stat-compat.c'),*libs,'-o',str(OUT/'native-check')],check=True)
 native=OUT/'native';native.mkdir();case=OUT/'cases/000'
 with (OUT/'native.log').open('x') as f:subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(OUT/'native-check'),str(rom),str(OUT/'cores/baseline.so'),str(case/'baseline.state'),str(native)],env={**env,'D35_ABILITY_INPUT':str(case/'input.txt'),'D35_ABILITY_EXPECTED':str(case/'expected.bin')},check=True,stdout=f,stderr=subprocess.STDOUT,timeout=90)
 assert 'PASS: consuming native provider' in (OUT/'native.log').read_text()
 wrapper=(OUT/'launch.sh').read_text().replace('BASE=/usr/retro/snes-fullpaths1','BASE=$D35_MVP_BASE').replace('TRIGGER=/usr/retro/snes-mvp','TRIGGER=$D35_MVP_BASE')
 (OUT/'fixture-launch.sh').write_text(wrapper,newline='\n')
 with (OUT/'wrapper.log').open('x') as f:subprocess.run([sys.executable,str(ROOT/'build/ability-suite-private-v1/wrapper-check.py'),str(OUT/'wrapper-fixtures')],env={**env,'D35_WRAPPER_UNDER_TEST':str(OUT/'fixture-launch.sh')},check=True,stdout=f,stderr=subprocess.STDOUT,timeout=120)
 assert 'zero diagnostic card writes or global sync during ready child' in (OUT/'wrapper.log').read_text()
 assert max(tuple(map(int,m)) for m in re.findall(r'GLIBC_(\d+)\.(\d+)',(OUT/'abi.txt').read_text()))<=(2,30)
 q={'version':plan['version'],'passed':True,'measurement_only':True,'production_gate_passed':False,'frameskip':False,'A7_saving_measured':False,'QEMU_timings_used':False,'card_writes':0,'combined_exact_comparisons':comparisons,'reused_standalone_proof':reused,'actual_controller_runs':actual,'runner_sha256':digest(OUT/'ability-suite'),'wrapper_sha256':digest(OUT/'launch.sh'),'native_client_qualified':True,'wrapper_qualified':True,'cores':plan['cores'],'limits':['Finite matched contexts, not every plausible spell.','Headroom requires valid PCM accounting and complete effect/recovery; no physical result yet.']}
 (OUT/'qualification.json').write_text(json.dumps(q,indent=2)+'\n');print('PASS combination, actual controller, native fault/retry/deficit, wrapper and ABI',flush=True)
if __name__=='__main__':qualify()
