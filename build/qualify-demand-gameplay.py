"""Qualify exact reused gameplay binaries, archived progress and actual wrapper."""
from pathlib import Path
from hashlib import sha256
import json, os, re, shutil, subprocess, sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/demand-gameplay-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 assert not (OUT/'verification.json').exists()
 p=json.loads((OUT/'prepared.json').read_text());archive=ROOT/'device-evidence'/p['archive']
 for n,h in p['payload_hashes'].items():assert digest(OUT/n)==h,n
 env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')}
 def qemu(args,name,extra=None):
  with (OUT/name).open('x') as f:subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),*map(str,args)],env={**env,**(extra or {})},stdout=f,stderr=subprocess.STDOUT,check=True,timeout=240)
 qemu([ROOT/'build/a7-pair-private-v1/equivalence',archive/'retro/snes-confuser-gameplay1/plus-a7.so',OUT/'plus-a7.so',ROOT/'build/plus-a7-out/ff6.sfc',archive/p['snapshot_source'],1200],'latest-progress-exact.log')
 assert 'PASS: 2400 frames exact' in (OUT/'latest-progress-exact.log').read_text()
 smoke=OUT/'smoke';smoke.mkdir()
 qemu([OUT/'snes-mvp','--mock','--rom',ROOT/'build/plus-a7-out/ff6.sfc','--core',OUT/'plus-a7.so','--saves',smoke],'smoke.log',{'D35_MVP_FRAMES':'180','D35_MVP_NO_PACING':'1'})
 v=dict(l.split('=',1) for l in (smoke/'last-session.txt').read_text().splitlines() if '=' in l)
 assert v['runs']==v['video_submitted']=='180' and v['held']=='0' and not v['error'] and v['audio_remaining_frames']=='0'
 assert int(v['output_accepted_frames_including_priming'])==int(v['resampled_enqueued_frames'])+int(v['priming_silence_frames'])
 native=OUT/'native';shutil.copytree(OUT/'saves',native)
 qemu([ROOT/'build/demand-visible-private-v3/native-check',ROOT/'build/plus-a7-out/ff6.sfc',OUT/'plus-a7.so',native],'native.log')
 assert 'two snapshot loads' in (OUT/'native.log').read_text() and 'real runner direct-output callbacks' in (OUT/'native.log').read_text()
 fixture=OUT/'fixture-launch.sh';fixture.write_text((OUT/'launch.sh').read_text().replace('TRIGGER=${D35_GAMEPLAY_TRIGGER:-/usr/retro/snes-mvp}','TRIGGER=$BASE'),newline='\n')
 check=OUT/'wrapper-check.py';check.write_text((ROOT/'build/ability-suite-private-v1/wrapper-check.py').read_text().replace('ability-suite','snes-mvp'),newline='\n')
 with (OUT/'wrapper.log').open('x') as f:subprocess.run([sys.executable,str(check),str(OUT/'wrapper-fixtures')],env={**env,'D35_WRAPPER_UNDER_TEST':str(fixture)},stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
 assert 'zero diagnostic card writes or global sync during ready child' in (OUT/'wrapper.log').read_text()
 with (OUT/'abi.txt').open('x') as f:subprocess.run(['arm-linux-gnueabihf-readelf','-V',str(OUT/'plus-a7.so'),str(OUT/'snes-mvp')],stdout=f,check=True)
 assert max(tuple(map(int,m)) for m in re.findall(r'GLIBC_(\d+)\.(\d+)',(OUT/'abi.txt').read_text()))<=(2,30)
 sources=[ROOT/'build'/n for n in ('prepare-demand-gameplay.py','qualify-demand-gameplay.py','install-demand-gameplay.py')]
 sources+=[ROOT/'docs/snes-demand-gameplay-test.txt']
 proofs=[OUT/n for n in ('latest-progress-exact.log','smoke.log','native.log','wrapper.log','abi.txt')]
 q={**p,'passed':True,'physical_gameplay_qualified':False,'native_client_qualified':True,'wrapper_qualified':True,
 'checks':['2400 exact latest-progress output/state comparisons','180 actual gameplay-runner full-frame mock calls and exact PCM accounting','actual native consuming client: migrated progress, direct callbacks, two state loads, fault/retry/drain','actual gameplay wrapper splash/timeout/one-shot/no live-child diagnostics','glibc <=2.30'],
 'source_hashes':{f.relative_to(ROOT).as_posix():digest(f) for f in sources},'proof_hashes':{f.name:digest(f) for f in proofs}}
 (OUT/'verification.json').write_text(json.dumps(q,indent=2)+'\n')
 print(json.dumps({'passed':True,'checks':q['checks'],'physical_result':'PENDING'},indent=2))
if __name__=='__main__':main()
