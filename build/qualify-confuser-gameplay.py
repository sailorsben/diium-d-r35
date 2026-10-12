"""Qualify exact counter-free core, latest progress, regular runner and wrapper."""
from pathlib import Path
from hashlib import sha256
import json,os,re,shutil,struct,subprocess,zlib
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/confuser-gameplay-private-v1'
assert not (OUT/'verification.json').exists()
p=json.loads((OUT/'prepared.json').read_text());archive=ROOT/'device-evidence'/p['archive']
def digest(path):return sha256(path.read_bytes()).hexdigest()
core=OUT/'core/snes9x2005_plus_libretro.so';shutil.copy2(core,OUT/'plus-a7.so')
crc=zlib.crc32(core.read_bytes());raw=(OUT/'snapshot-source.state').read_bytes();head=bytearray(raw[:40])
struct.pack_into('<II',head,20,crc,core.stat().st_size)
state_name=f'game-a27f1c7a-3145728-core-{crc:08x}-{core.stat().st_size}.state'
(OUT/'saves'/state_name).write_bytes(head+raw[40:])
assert (OUT/'saves'/state_name).read_bytes()[40:]==raw[40:]
env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')}
def qemu(args,log,extra=None):
    with log.open('x') as f:subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),*map(str,args)],env={**env,**(extra or {})},check=True,stdout=f,stderr=subprocess.STDOUT)
for label,state,iters,mode in [('confuser',ROOT/'build/confuser-private-v1/confuser-selection/scene.state',1200,'magitek-bio'),
                             ('bio',ROOT/'build/magitek-bio-private/scene.state',1200,'magitek-bio'),
                             ('snapshot',archive/p['snapshot_source'],1200,None)]:
    args=[ROOT/'build/a7-pair-private-v1/equivalence',ROOT/'build/a7-pair-private-v1/core/snes9x2005_plus_libretro.so',core,
          ROOT/'build/plus-a7-out/ff6.sfc',state,iters]
    if mode:args.append(mode)
    qemu(args,OUT/('equivalence-'+label+'.log'))
    assert f'PASS: {iters if mode else 2*iters} frames exact' in (OUT/('equivalence-'+label+'.log')).read_text()
smoke=OUT/'smoke';smoke.mkdir()
qemu([OUT/'snes-mvp','--mock','--rom',ROOT/'build/plus-a7-out/ff6.sfc','--core',core,'--saves',smoke],OUT/'smoke.log',{'D35_MVP_FRAMES':'180','D35_MVP_NO_PACING':'1'})
v=dict(l.split('=',1) for l in (smoke/'last-session.txt').read_text().splitlines() if '=' in l)
assert v['runs']==v['video_submitted']=='180' and v['held']=='0' and v['error']=='' and v['audio_remaining_frames']=='0'
assert int(v['output_accepted_frames_including_priming'])==int(v['resampled_enqueued_frames'])+int(v['priming_silence_frames'])
native=OUT/'native';native.mkdir()
for f in (OUT/'saves').iterdir():shutil.copy2(f,native/f.name)
# Reuse unchanged consuming-client fixture binary; it loads the candidate dynamically.
qemu([ROOT/'build/combined-gameplay-private-v1/native-check',ROOT/'build/plus-a7-out/ff6.sfc',core,native],OUT/'native-check.log')
assert 'two snapshot loads' in (OUT/'native-check.log').read_text()
fixture=OUT/'fixture-launch.sh';fixture.write_text((OUT/'launch.sh').read_text().replace('TRIGGER=${D35_GAMEPLAY_TRIGGER:-/usr/retro/snes-mvp}','TRIGGER=$BASE'),newline='\n')
with (OUT/'wrapper-check.log').open('x') as f:subprocess.run(['python3',str(ROOT/'build/snes-mvp/check-startup-wrapper.py'),str(OUT/'wrapper-fixtures')],
 env={**os.environ,'D35_WRAPPER_UNDER_TEST':str(fixture)},check=True,stdout=f,stderr=subprocess.STDOUT)
assert 'zero diagnostic card writes or global sync during ready child' in (OUT/'wrapper-check.log').read_text()
with (OUT/'abi.txt').open('x') as f:subprocess.run(['arm-linux-gnueabihf-readelf','-V',str(core),str(OUT/'snes-mvp')],check=True,stdout=f)
assert max(tuple(map(int,m)) for m in re.findall(r'GLIBC_(\d+)\.(\d+)',(OUT/'abi.txt').read_text()))<=(2,30)
assert digest(OUT/'snes-mvp')==p['regular_runner_sha256']
sources=[ROOT/'build'/n for n in ('prepare-confuser-gameplay.py','qualify-confuser-gameplay.py','build-confuser-gameplay.sh','snes-mvp/native-runner-check.c','snes-mvp/check-startup-wrapper.py')]
sources+=list((OUT/'core/source').glob('*.[ch]'))+[OUT/'core/libretro.c',OUT/'core/link.T']
payload=[OUT/'snes-mvp',OUT/'plus-a7.so',OUT/'launch.sh',OUT/'dispatch.sh',*(OUT/'saves').iterdir()]
proofs=[OUT/n for n in ('equivalence-confuser.log','equivalence-bio.log','equivalence-snapshot.log','smoke.log','native-check.log','wrapper-check.log','abi.txt')]
q={**p,'passed':True,'long_gameplay_qualified':False,'core_sha256':digest(core),'core_crc32':f'{crc:08x}','core_bytes':core.stat().st_size,
 'snapshot_name':state_name,'checks':['counter-free BG3 batching + refined half-add; exact regular1.19 runner',
 '4800 exact Confuser/Bio/intro/latest snapshot output/state comparisons',
 '180 actual regular-binary frames: full rendering, lossless PCM and close',
 'native consuming client: two latest snapshot loads, fault retention, drain and deficit handling',
 'actual wrapper one-shot/splash/startup, no live-child card diagnostics'],
 'source_hashes':{x.relative_to(ROOT).as_posix():digest(x) for x in sources},
 'payload_hashes':{x.relative_to(OUT).as_posix():digest(x) for x in payload},
 'proof_hashes':{x.name:digest(x) for x in proofs},'timing_evidence':'New incremental A7 prices unmeasured; QEMU durations excluded',
 'telemetry':'regular cumulative and bounded recent/sparse samples; no forced input or nested diagnostic clocks'}
(OUT/'verification.json').write_text(json.dumps(q,indent=2)+'\n')
print(json.dumps({'passed':True,'version':q['version'],'core_sha256':q['core_sha256'],'crc':q['core_crc32'],'bytes':q['core_bytes'],'hardware_saving_measured':False},indent=2))
