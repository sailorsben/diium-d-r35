"""Check copied progress, regular binary, manual snapshot/client and wrapper seams."""
from pathlib import Path
from hashlib import sha256
import json,os,re,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/combined-gameplay-private-v1'
p=json.loads((OUT/'prepared.json').read_text());archive=ROOT/'device-evidence'/p['archive']
def digest(path):return sha256(path.read_bytes()).hexdigest()
env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')}
def qemu(args,log,extra=None):
    with log.open('w') as f:subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),*map(str,args)],env={**env,**(extra or {})},check=True,stdout=f,stderr=subprocess.STDOUT)
qemu([ROOT/'build/a7-pair-private-v1/equivalence',ROOT/'build/plus-a7-out/plus-a7.so',OUT/'plus-a7.so',ROOT/'build/plus-a7-out/ff6.sfc',archive/p['snapshot_source'],1200],OUT/'snapshot-equivalence.log')
assert 'PASS: 2400 frames exact' in (OUT/'snapshot-equivalence.log').read_text()
smoke=OUT/'smoke';smoke.mkdir()
qemu([OUT/'snes-mvp','--mock','--rom',ROOT/'build/plus-a7-out/ff6.sfc','--core',OUT/'plus-a7.so','--saves',smoke],OUT/'smoke.log',{'D35_MVP_FRAMES':'180','D35_MVP_NO_PACING':'1'})
values=dict(l.split('=',1) for l in (smoke/'last-session.txt').read_text().splitlines() if '=' in l)
assert values['runs']==values['video_submitted']=='180' and values['error']=='' and values['held']=='0'
assert values['audio_remaining_frames']=='0'
assert int(values['output_accepted_frames_including_priming'])==int(values['resampled_enqueued_frames'])+int(values['priming_silence_frames'])
# Compile the unchanged regular runner with the independent consuming provider.
# The fixture drives the actual manual load/resume menu twice and tests failed
# sessions, save isolation, orderly drain and truthful deficit handling.
native=OUT/'native';native.mkdir()
for f in (OUT/'saves').iterdir():shutil.copy2(f,native/f.name)
s=(ROOT/'build/snes-mvp/native-runner-check.c').read_text()
old='const char *trace_path="build/snes-mvp/out/native-runner-fault-fixture.txt";';assert s.count(old)==1
s=s.replace(old,'char trace_path[1200];snprintf(trace_path,sizeof(trace_path),"%s/fault-fixture.txt",argv[3]);')
fixture=OUT/'native-runner-check.c';fixture.write_text(s,newline='\n')
libs=['-L'+str(ROOT/'build/sysroot/lib'),'-Wl,--no-as-needed']+['-l:'+n for n in ('libdl-2.30.so','libz.so.1','libpthread-2.30.so','librt-2.30.so','libm-2.30.so','libc-2.30.so','libgcc_s.so.1','ld-2.30.so')]
subprocess.run(['arm-linux-gnueabihf-gcc','-mcpu=cortex-a7','-mfpu=neon-vfpv4','-mfloat-abi=hard','-marm','-fno-stack-protector','-U_TIME_BITS','-D_TIME_BITS=32','-U_FILE_OFFSET_BITS','-D_FILE_OFFSET_BITS=32','-std=gnu99','-O2','-Wall','-Wextra','-Werror','-no-pie','-nostdlib','-I'+str(ROOT/'build/snes-mvp'),'-I'+str(ROOT/'build/snes9x2005/libretro-common/include'),'/usr/arm-linux-gnueabihf/lib/crt1.o',str(fixture),str(ROOT/'build/glibc230-stat-compat.c'),*libs,'-o',str(OUT/'native-check')],check=True)
qemu([OUT/'native-check',ROOT/'build/plus-a7-out/ff6.sfc',OUT/'plus-a7.so',native],OUT/'native-check.log')
assert 'two snapshot loads' in (OUT/'native-check.log').read_text() and 'failed-session report and exact PCM history survive' in (OUT/'native-check.log').read_text()
wrapper_log=OUT/'wrapper-check.log'
with wrapper_log.open('w') as f:
    # Point the unchanged real wrapper at the fixture's explicitly owned base.
    fixture_wrapper=OUT/'fixture-launch.sh'
    s=(OUT/'launch.sh').read_text().replace('TRIGGER=${D35_GAMEPLAY_TRIGGER:-/usr/retro/snes-mvp}','TRIGGER=$BASE')
    fixture_wrapper.write_text(s,newline='\n')
    subprocess.run([sys.executable,str(ROOT/'build/snes-mvp/check-startup-wrapper.py'),str(OUT/'wrapper-fixtures')],env={**os.environ,'D35_WRAPPER_UNDER_TEST':str(fixture_wrapper)},check=True,stdout=f,stderr=subprocess.STDOUT)
assert 'zero diagnostic card writes or global sync during ready child' in wrapper_log.read_text()
subprocess.run(['arm-linux-gnueabihf-readelf','-V',str(OUT/'snes-mvp')],check=True,stdout=(OUT/'abi.txt').open('w'))
assert max(tuple(map(int,m)) for m in re.findall(r'GLIBC_(\d+)\.(\d+)',(OUT/'abi.txt').read_text()))<=(2,30)
assert digest(OUT/'snes-mvp')==p['regular_runner_sha256'] and digest(OUT/'plus-a7.so')==p['core_sha256']
sources=[ROOT/'build'/name for name in ('prepare-combined-gameplay.py','qualify-combined-gameplay.py','snes-mvp/native-runner-check.c','snes-mvp/check-startup-wrapper.py')]
sources+=list((ROOT/'build/snes-mvp').glob('*.[ch]'))
payload=[OUT/'snes-mvp',OUT/'plus-a7.so',OUT/'launch.sh',OUT/'dispatch.sh',*(OUT/'saves').iterdir()]
proofs=[OUT/name for name in ('snapshot-equivalence.log','smoke.log','native-check.log','wrapper-check.log','abi.txt')]
q={**p,'passed':True,'long_gameplay_qualified':False,
    'checks':['same measured combined core; exact regular1.19 binary','2400 exact-output frames using copied current snapshot',
    '180 actual regular-binary frames: full rendering, lossless PCM and orderly close',
    'native client: two copied-snapshot loads/resumes, preserved failed sessions, clean drain and sustained deficit rejection',
    'one-shot/splash/startup wrapper fixtures; no live-child card diagnostics'],
    'source_hashes':{x.relative_to(ROOT).as_posix():digest(x) for x in sources},
    'payload_hashes':{x.relative_to(OUT).as_posix():digest(x) for x in payload},
    'proof_hashes':{x.name:digest(x) for x in proofs},'timing_evidence':'Only previous A7 pair1 return; QEMU durations excluded',
    'telemetry':'regular cumulative counters and bounded recent/sparse samples; not a complete per-call timeline'}
(OUT/'verification.json').write_text(json.dumps(q,indent=2)+'\n')
print(json.dumps({'passed':True,'version':q['version'],'manual_controls':True,'long_gameplay':'PENDING'},indent=2))
