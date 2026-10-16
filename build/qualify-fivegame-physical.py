"""Actual20-epoch rehearsal, per-frame offline oracle, native and firmware guards."""
from pathlib import Path
from hashlib import sha256
import csv,json,os,re,signal,subprocess,time,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/fivegame-physical-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def kv(p):return dict(l.split('=',1) for l in p.read_text().splitlines() if '=' in l)
def rows(p):return list(csv.DictReader(l for l in p.read_text().splitlines() if not l.startswith('#')))
def run(args,name,env=None,timeout=120,expected=0):
 with (OUT/name).open('w') as f:r=subprocess.run(args,cwd=ROOT,env={**os.environ,**(env or {})},stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 assert r.returncode==expected,(name,r.returncode,(OUT/name).read_text()[-1800:]);return (OUT/name).read_text()
def main():
 assert os.name!='nt' and not (OUT/'verification.json').exists();plan=json.loads((OUT/'plan.json').read_text());rt=OUT/'runner'
 for n,h in json.loads((OUT/'frozen.json').read_text()).items():assert digest(ROOT/n)==h,n
 flags=['-DD35_PLUS_A7','-DD35_NATIVE_PCM','-mcpu=cortex-a7','-mfpu=neon-vfpv4','-mfloat-abi=hard','-marm','-fno-stack-protector','-D_TIME_BITS=32','-D_FILE_OFFSET_BITS=32','-std=gnu99','-O3','-flto=4','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-no-pie','-nostdlib','-Ibuild','-Ibuild/snes9x2005/libretro-common/include','/usr/arm-linux-gnueabihf/lib/crt1.o']
 libs=['-Lbuild/sysroot/lib','-Wl,--no-as-needed']+['-l:'+n for n in ('libdl-2.30.so','libz.so.1','libpthread-2.30.so','librt-2.30.so','libm-2.30.so','libc-2.30.so','libgcc_s.so.1','ld-2.30.so')]
 run(['arm-linux-gnueabihf-gcc',*flags,str(OUT/'main.c'),*[str(rt/n) for n in ('board.c','runner.c','audio-owner.c','native-pcm.c','startup.c','platform.c','timing.c')],'build/glibc230-stat-compat.c',*libs,'-o',str(OUT/'fivegame-suite')],'build.log')
 abi=run(['arm-linux-gnueabihf-readelf','-V',str(OUT/'fivegame-suite'),str(OUT/'plus-a7.so')],'abi.txt');assert all(tuple(map(int,m))<=(2,30) for m in re.findall(r'GLIBC_(\d+)\.(\d+)',abi))
 qemu=['qemu-arm','-cpu','cortex-a7','-L','build/sysroot','-E','LD_LIBRARY_PATH=build/sysroot/lib'];mock=OUT/'mock';env={'D35_ABILITY_MOCK':'1','D35_MVP_NO_PACING':'1','D35_FULL_HOST_FIXTURE':'1','D35_FIVE_ORACLE':'1'}
 if '--reuse-mock' not in sys.argv:
  mock.mkdir();run([*qemu,str(OUT/'fivegame-suite'),'--supervise',str(mock),str(OUT),'unused'],'mock.log',env,1800)
 checked=[]
 for r in plan['runs']:
  d=mock/f"run-{r['run']:03d}";s=kv(d/'last-session.txt');f=rows(d/'frames.csv');a=kv(d/'input.csv');pcm=kv(d/'pcm-full.txt');head=kv(d/'headroom.txt')
  assert s['runs']==s['rendered_frames']==s['video_submitted']=='1200' and s['presentation_skipped']=='0' and not s['error'],(r,s.get('error'))
  assert len(f)==1200 and a['#oracle_checks']=='1200' and a['#oracle_enabled']=='1'
  assert int(s['presentation_policy'])==r['policy'] and kv(d/'result.txt')['runner_rc']=='0'
  assert s['audio_remaining_frames']==s['audio_cleared_frames']=='0' and int(s['output_accepted_frames_including_priming'])==int(s['resampled_enqueued_frames'])+int(s['priming_silence_frames'])
  assert pcm['retained_from']=='0' and not pcm['failure'] and head['physical']=='0' and int(f[-1]['load_events'])==0
  assert int(head['period_ns'])==round(1e9/plan['cases'][r['fixture']]['fps'])
  if r['fixture']==3:assert kv(d/'warmup.txt')['cold_boot_calls']=='8656'
  assert (d/'end-state.bin').stat().st_size>300000
  checked.append({**r,'calls':1200,'exact_original_gameplay_pixels_PCM_samples':True,'warmup_calls':8656 if r['fixture']==3 else 0})
 assert kv(mock/'suite-result.txt')['runs']=='20' and kv(mock/'supervisor.txt')['forced']=='0' and kv(mock/'supervisor.txt')['reaped']=='1'
 print('PASS actual20-epoch controller:24000 exact gameplay pixel/PCM calls,34624 Star Fox cold calls; mock rejected as physical',flush=True)
 # The exact new runner under an independently consuming native PCM provider.
 s=(ROOT/'build/presentation-ffvi-private-v1/runner/presentation-native-check.c').read_text();s=s.replace('19880500u','(game_period_ns+3192345u)');(rt/'fivegame-native-check.c').write_text(s,newline='\n')
 native_flags=[f for f in flags if f!='-flto=4']+['-O2']
 run(['arm-linux-gnueabihf-gcc',*native_flags,str(rt/'fivegame-native-check.c'),'build/glibc230-stat-compat.c',*libs,'-o',str(OUT/'native-check')],'native-build.log')
 for policy in ('0','1'):
  d=OUT/('native-pal-v2-'+policy);d.mkdir();text=run([*qemu,str(OUT/'native-check'),str(OUT/'cases/000/game.sfc'),str(OUT/'plus-a7.so'),str(OUT/'cases/000/scene.state'),str(d)],'native-pal-v2-'+policy+'.log',{'D35_FULL_HOST_FIXTURE':'1','D35_PRESENTATION_POLICY':policy,'D35_ABILITY_INPUT':str(OUT/'cases/000/input.txt'),'D35_ABILITY_EXPECTED':str(OUT/'cases/000/expected.bin')},180)
  assert 'PASS: consuming native provider' in text
 print('PASS actual native runner both policies, forced busy40/120, fault/drain/retry/full history and sustained-deficit rejection',flush=True)
 shell=['qemu-arm','-0','busybox','-L','build/sysroot','build/uart-fix-private/firmware-busybox','sh'];run([*shell,'-n',str(OUT/'launch.sh')],'wrapper-syntax.log');checks=[]
 rom=OUT/'cases/000/game.sfc'
 for name in ('normal','UART_absent','UART_fault','child139','forced72','forced_UART_fault','after_UART_fault','active_splash'):
  d=OUT/'wrapper'/name;d.mkdir(parents=True);(d/'mvp').mkdir();(d/'proc').mkdir();valid='version=4 result=0 irq=19 attached=1 calls=0 fault=0 bypass=0 cap=0\n'
  if name!='UART_absent':(d/'proc/d35_uart_tx').write_text(valid.replace('fault=0','fault=1') if name=='UART_fault' else valid)
  for p in (d/'armed',d/'mvp/armed'):p.write_bytes(b'owned fixture\n')
  (d/'ROM-PATH.txt').write_text(str(rom)+'\n')
  if name=='active_splash':(d/'proc/123').mkdir();(d/'proc/123/comm').write_text('showlogo\n');(d/'proc/123/status').write_text('State:\tS\n')
  body='#!/bin/sh\nprintf executed > "'+str(d/'executed')+'"\n'
  if name in ('forced_UART_fault','after_UART_fault'):body+='printf "'+valid.replace('fault=0','fault=1').replace('\n','\\n')+'" > "'+str(d/'proc/d35_uart_tx')+'"\n'
  code=139 if name=='child139' else 72 if name.startswith('forced') else 0;(d/'fivegame-suite').write_text(body+f'exit {code}\n');(d/'fivegame-suite').chmod(0o755)
  args=['env','D35_LAB_BASE='+str(d),'D35_MVP_BASE='+str(d/'mvp'),'D35_LAB_PROC_ROOT='+str(d/'proc'),'D35_LAB_SPLASH_STOP='+str(d/'stop'),*shell,str(OUT/'launch.sh')];blocked=name in ('child139','forced72','forced_UART_fault')
  run((['timeout','2'] if blocked else [])+args,'wrapper-'+name+'.log',timeout=12,expected=124 if blocked else 1 if name in ('UART_absent','UART_fault','after_UART_fault','active_splash') else 0)
  assert not (d/'armed').exists() and not (d/'mvp/armed').exists();assert (d/'executed').exists()==(name not in ('UART_absent','UART_fault','active_splash'))
  if blocked:assert any('reboot required' in p.read_text() for p in (d/'results').glob('*/wrapper.log'))
  if name=='normal':run(args,'wrapper-replay.log');assert len(list((d/'results').glob('run-*')))==1
  checks.append(name)
 d=OUT/'interrupted';d.mkdir()
 with (OUT/'supervisor-interrupted.log').open('w') as f:
  proc=subprocess.Popen([*qemu,str(OUT/'fivegame-suite'),'--supervise',str(d),str(OUT),'unused'],cwd=ROOT,env={**os.environ,**env},stdout=f,stderr=subprocess.STDOUT);time.sleep(0.5);proc.send_signal(signal.SIGTERM);rc=proc.wait(timeout=15)
 assert rc==72 and kv(d/'supervisor.txt')['forced']=='1' and kv(d/'supervisor.txt')['reaped']=='1'
 for n,h in json.loads((OUT/'frozen.json').read_text()).items():assert digest(ROOT/n)==h,n
 payload=[p for p in OUT.rglob('*') if p.is_file() and (p.relative_to(OUT).parts[0]=='cases' or p.relative_to(OUT).as_posix() in ('fivegame-suite','plus-a7.so','launch.sh','dispatch.sh','ROM-PATH.txt','plan.json'))]
 sources=[ROOT/'build'/n for n in ('prepare-fivegame-physical.py','qualify-fivegame-physical.py','fivegame-observer.h','fivegame-warmup.h','presentation-ffvi-main.c')]+list(rt.glob('*.[ch]'))+[OUT/'main.c',OUT/'identity.h',OUT/'presentation-burst.h',OUT/'plus-a7-profile.h']
 result={'version':'fivegame1','passed':True,'measurement_only':True,'production_gate':False,'installed':False,'physical_result':'PENDING','card_writes':0,'actual_epochs':checked,'native_policies':[0,1],'forced_busy_skips':40,'wrapper_checks':checks,'interrupted_supervisor_reaped':True,'source_hashes':{p.relative_to(ROOT).as_posix():digest(p) for p in sources},'payload_hashes':{p.relative_to(OUT).as_posix():digest(p) for p in payload},'proof_hashes':{p.name:digest(p) for p in OUT.glob('*.log')},'ABI_sha256':digest(OUT/'abi.txt'),'QEMU_performance_evidence':False}
 (OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS five-game physical package, ABI, native lifecycle, firmware guards/replay/fault and forced supervisor; no card writes',flush=True)
if __name__=='__main__':main()
