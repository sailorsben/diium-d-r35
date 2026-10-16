"""Actual80-epoch controller, consuming PCM and firmware recovery qualification."""
from pathlib import Path
from hashlib import sha256
import csv,json,os,re,subprocess,shutil,signal,time,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/presentation-ffvi-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def kv(p):return dict(l.split('=',1) for l in p.read_text().splitlines() if '=' in l)
def rows(p):return list(csv.DictReader(l for l in p.read_text().splitlines() if not l.startswith('#')))
def run(args,name,env=None,timeout=120,expected=0):
 with (OUT/name).open('w') as f:r=subprocess.run(args,cwd=ROOT,env={**os.environ,**(env or {})},stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 assert r.returncode==expected,(name,r.returncode,(OUT/name).read_text()[-2000:])
 return (OUT/name).read_text()
def main():
 assert os.name!='nt' and not (OUT/'verification.json').exists()
 plan=json.loads((OUT/'plan.json').read_text());rt=OUT/'runner'
 for n,h in json.loads((OUT/'frozen.json').read_text()).items():assert digest(ROOT/n)==h,n
 flags=['-DD35_PLUS_A7','-DD35_NATIVE_PCM','-mcpu=cortex-a7','-mfpu=neon-vfpv4','-mfloat-abi=hard','-marm',
 '-fno-stack-protector','-D_TIME_BITS=32','-D_FILE_OFFSET_BITS=32','-std=gnu99','-O3','-flto=4','-Wall','-Wextra','-Werror',
 '-Wno-misleading-indentation','-no-pie','-nostdlib','-Ibuild','-Ibuild/snes9x2005/libretro-common/include','/usr/arm-linux-gnueabihf/lib/crt1.o']
 libs=['-Lbuild/sysroot/lib','-Wl,--no-as-needed']+['-l:'+n for n in ('libdl-2.30.so','libz.so.1','libpthread-2.30.so','librt-2.30.so','libm-2.30.so','libc-2.30.so','libgcc_s.so.1','ld-2.30.so')]
 sources=[OUT/'main.c']+[rt/n for n in ('board.c','runner.c','audio-owner.c','native-pcm.c','startup.c','platform.c','timing.c')]
 run(['arm-linux-gnueabihf-gcc',*flags,*map(str,sources),'build/glibc230-stat-compat.c',*libs,'-o',str(OUT/'ffvi-suite')],'build.log')
 abi=run(['arm-linux-gnueabihf-readelf','-V',str(OUT/'ffvi-suite'),str(OUT/'plus-a7.so')],'abi.txt')
 assert all(tuple(map(int,m))<=(2,30) for m in re.findall(r'GLIBC_(\d+)\.(\d+)',abi))
 qemu=['qemu-arm','-cpu','cortex-a7','-L','build/sysroot','-E','LD_LIBRARY_PATH=build/sysroot/lib']
 rom=ROOT/'build/plus-a7-out/ff6.sfc';mock=OUT/'mock'
 env={'D35_ABILITY_MOCK':'1','D35_MVP_NO_PACING':'1','D35_FULL_HOST_FIXTURE':'1'}
 if '--reuse-mock' not in sys.argv:
  mock.mkdir();run([*qemu,str(OUT/'ffvi-suite'),'--supervise',str(mock),str(OUT),str(rom)],'mock.log',env,1800)
 checked=[]
 for r in plan['runs']:
  d=mock/f"run-{r['run']:03d}";s=kv(d/'last-session.txt');f=rows(d/'frames.csv');a=rows(d/'animation.csv');p=kv(d/'pcm-full.txt')
  assert s['runs']==s['rendered_frames']==s['video_submitted']=='1200' and s['presentation_skipped']=='0' and not s['error'],r
  assert len(f)==len(a)==1200 and s['phase_profile_samples']=='0'
  assert int(kv(d/'animation.csv')['#matching_property_samples'])>0,r
  assert int(s['presentation_policy'])==r['policy'] and kv(d/'result.txt')['runner_rc']=='0'
  assert s['audio_remaining_frames']==s['audio_cleared_frames']=='0'
  assert int(s['output_accepted_frames_including_priming'])==int(s['resampled_enqueued_frames'])+int(s['priming_silence_frames'])
  assert p['retained_from']=='0' and not p['failure']
  assert int(f[-1]['load_events'])==(7 if r['load_ms'] else 0)
  assert kv(d/'headroom.txt')['physical']=='0'
  assert f[-1]['rendered']=='1200' and all(x['skipped']=='0' for x in f)
  checked.append({**r,'calls':1200,'expected_effect_observed':True,'all_render_and_PCM':True})
 assert kv(mock/'suite-result.txt')['runs']=='80' and kv(mock/'supervisor.txt')['forced']=='0' and kv(mock/'supervisor.txt')['reaped']=='1'
 print('PASS actual80-epoch controller: 96000 real-core renders/PCM,18 effects,56 executed CPU bursts; mock rejected as physical',flush=True)
 # Native fixture uses this actual measurement runner, including full histories.
 s=(rt/'ability-native-check.c').read_text()
 s=s.replace('static unsigned output_slot,direct_calls;','static unsigned output_slot,direct_calls,finish_calls;')
 s=s.replace('int board_audio_finish(void) { return pcm_finish(); }','int board_audio_finish(void) { ++finish_calls;return pcm_finish(); }')
 s=s.replace('void board_video_cancel(void) { }', '''int board_video_try_reserve(void){if(!deficit_mode && s.runs%3==1)return 0;return board_video_reserve()<0?-1:1;}
void board_video_cancel(void) { }''')
 s=s.replace('s.runs==120 && s.videos==120','s.runs==120 && s.rendered==120 && s.videos==(s.presentation_policy?80:120) && s.presentation_skipped==(s.presentation_policy?40:0)')
 s=s.replace('assert(direct_calls>=120);','assert(direct_calls>=80 && finish_calls==1);')
 target=rt/'presentation-native-check.c';target.write_text(s,newline='\n')
 native_flags=[f for f in flags if f!='-flto=4']+['-O2'] # retain established consuming-fixture build
 run(['arm-linux-gnueabihf-gcc',*native_flags,str(target),'build/glibc230-stat-compat.c',*libs,'-o',str(OUT/'native-check')],'native-build.log')
 for policy in ('0','1'):
  d=OUT/('native-'+policy);d.mkdir()
  text=run([*qemu,str(OUT/'native-check'),str(rom),str(OUT/'plus-a7.so'),str(OUT/'cases/000/scene.state'),str(d)],'native-'+policy+'.log',
   {'D35_FULL_HOST_FIXTURE':'1','D35_PRESENTATION_POLICY':policy,'D35_ABILITY_INPUT':str(OUT/'cases/000/input.txt'),'D35_ABILITY_EXPECTED':str(OUT/'cases/000/expected.bin')},180)
  assert 'PASS: consuming native provider' in text
  retry=kv(d/'retry/last-session.txt');assert retry['presentation_skipped']==('40' if policy=='1' else '0')
 print('PASS actual native runner both policies, forced busy40/120, single drain, fault/retry/full-history and sustained-deficit rejection',flush=True)
 # Exercise the shipped wrapper under actual firmware BusyBox with owned shims.
 shell=['qemu-arm','-0','busybox','-L','build/sysroot','build/uart-fix-private/firmware-busybox','sh']
 run([*shell,'-n',str(OUT/'launch.sh')],'wrapper-syntax.log')
 checks=[]
 for name in ('normal','UART_absent','UART_fault','child139','forced72','forced_UART_fault','after_UART_fault','active_splash'):
  d=OUT/'wrapper'/name;d.mkdir(parents=True);(d/'mvp').mkdir();(d/'proc').mkdir()
  valid='version=4 result=0 irq=19 attached=1 calls=0 fault=0 bypass=0 cap=0\n'
  if name!='UART_absent':(d/'proc/d35_uart_tx').write_text(valid.replace('fault=0','fault=1') if name=='UART_fault' else valid)
  for p in (d/'armed',d/'mvp/armed'):p.write_bytes(b'owned fixture\n')
  (d/'ROM-PATH.txt').write_text(str(rom)+'\n')
  if name=='active_splash':(d/'proc/123').mkdir();(d/'proc/123/comm').write_text('showlogo\n');(d/'proc/123/status').write_text('State:\tS\n')
  body='#!/bin/sh\nprintf executed > "'+str(d/'executed')+'"\n'
  if name in ('forced_UART_fault','after_UART_fault'):body+='printf "'+valid.replace('fault=0','fault=1').replace('\n','\\n')+'" > "'+str(d/'proc/d35_uart_tx')+'"\n'
  code=139 if name=='child139' else 72 if name.startswith('forced') else 0
  (d/'ffvi-suite').write_text(body+f'exit {code}\n');(d/'ffvi-suite').chmod(0o755)
  args=['env','D35_LAB_BASE='+str(d),'D35_MVP_BASE='+str(d/'mvp'),'D35_LAB_PROC_ROOT='+str(d/'proc'),'D35_LAB_SPLASH_STOP='+str(d/'stop'),*shell,str(OUT/'launch.sh')]
  blocked=name in ('child139','forced72','forced_UART_fault')
  run((['timeout','2'] if blocked else [])+args,'wrapper-'+name+'.log',timeout=12,
      expected=124 if blocked else 1 if name in ('UART_absent','UART_fault','after_UART_fault','active_splash') else 0)
  assert not (d/'armed').exists() and not (d/'mvp/armed').exists()
  assert (d/'executed').exists()==(name not in ('UART_absent','UART_fault','active_splash'))
  if blocked:assert any('reboot required' in p.read_text() for p in (d/'results').glob('*/wrapper.log'))
  if name=='normal':
   run(args,'wrapper-replay.log');assert len(list((d/'results').glob('run-*')))==1
  checks.append(name)
 # Interrupted supervisor must reap its own child and return unsafe72, even if
 # child subsequently cooperates. No stock-return success on a forced boundary.
 d=OUT/'interrupted';d.mkdir()
 with (OUT/'supervisor-interrupted.log').open('w') as f:
  proc=subprocess.Popen([*qemu,str(OUT/'ffvi-suite'),'--supervise',str(d),str(OUT),str(rom)],cwd=ROOT,env={**os.environ,**env},stdout=f,stderr=subprocess.STDOUT)
  time.sleep(0.5);proc.send_signal(signal.SIGTERM);rc=proc.wait(timeout=15)
 assert rc==72 and kv(d/'supervisor.txt')['forced']=='1' and kv(d/'supervisor.txt')['reaped']=='1'
 for n,h in json.loads((OUT/'frozen.json').read_text()).items():assert digest(ROOT/n)==h,n
 payload=[p for p in OUT.rglob('*') if p.is_file() and (p.relative_to(OUT).parts[0]=='cases' or p.name in ('ffvi-suite','plus-a7.so','launch.sh','dispatch.sh','ROM-PATH.txt','plan.json'))]
 sources=[ROOT/'build'/n for n in ('prepare-presentation-ffvi.py','qualify-presentation-ffvi.py','presentation-ffvi-main.c','presentation-burst.h')]+list(rt.glob('*.[ch]'))+[OUT/'main.c',OUT/'identity.h',OUT/'presentation-burst.h',OUT/'plus-a7-profile.h']
 result={'version':'presentation-ffvi1','passed':True,'measurement_only':True,'production_gate':False,'installed':False,'physical_result':'PENDING','card_writes':0,
         'actual_epochs':checked,'native_policies':[0,1],'forced_busy_skips':40,'wrapper_checks':checks,'interrupted_supervisor_reaped':True,
         'source_hashes':{p.relative_to(ROOT).as_posix():digest(p) for p in sources},'payload_hashes':{p.relative_to(OUT).as_posix():digest(p) for p in payload},
         'proof_hashes':{p.name:digest(p) for p in OUT.glob('*.log')},'ABI_sha256':digest(OUT/'abi.txt'),'QEMU_performance_evidence':False}
 (OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS matched FFVI physical package, ABI, firmware guard/replay/fault and forced supervisor; no card writes',flush=True)
if __name__=='__main__':main()
