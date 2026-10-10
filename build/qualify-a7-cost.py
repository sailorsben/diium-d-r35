"""Qualify the diagnostic; never interpret QEMU times as A7 measurements."""
from pathlib import Path
from hashlib import sha256
import csv, json, re, subprocess, sys, os, struct, zlib
ROOT=Path(__file__).resolve().parent.parent
name=sys.argv[1];assert re.fullmatch(r'a7-cost-private(?:-[a-z0-9]+)?',name)
OUT=ROOT/'build'/name
def digest(p):return sha256(p.read_bytes()).hexdigest()
old=json.loads((ROOT/'releases/snes-mvp-1.19/manifest.json').read_text())
assert digest(ROOT/'build/plus-a7-out/plus-a7.so')==old['core_sha256']
log=(OUT/'equivalence.log').read_text()
for term in ('600 frames exact visible pixels, native PCM, geometry and periodic state',
             'all three diagnostic modes preserve outputs and state',
             'no clock errors/record overflow'):
    assert term in log,term
core=OUT/'core/snes9x2005_plus_libretro.so'
raw=(ROOT/'build/magitek-bio-private/scene.state').read_bytes()
assert raw[:8]==b'D35MVP01' and len(raw)==40+struct.unpack_from('<I',raw,28)[0]
assert zlib.crc32(raw[40:])==struct.unpack_from('<I',raw,32)[0]
header=bytearray(raw[:40]);struct.pack_into('<II',header,20,zlib.crc32(core.read_bytes()),core.stat().st_size)
(OUT/'replay.state').write_bytes(header+raw[40:])
# The payload stays unchanged. Its new identity is allowed only by the actual
# core equivalence above, not by a blanket bypass of the runner's state checks.
assert (OUT/'replay.state').read_bytes()[40:]==raw[40:]
env=dict(os.environ,LD_LIBRARY_PATH=str(ROOT/'build/sysroot/lib'),
         D35_MVP_NO_PACING='1',D35_COST_STATE=str(OUT/'replay.state'))
for mode in (0,1,2,3):
    out=OUT/f'smoke-{mode}';out.mkdir(exist_ok=False)
    env['D35_COST_MODE']=str(mode)
    with (out/'runner.log').open('w') as log:
        subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),
            str(OUT/'unit-runner'),'--mock','--rom',str(ROOT/'build/plus-a7-out/ff6.sfc'),
            '--core',str(core),'--saves',str(out)],check=True,env=env,stdout=log,stderr=subprocess.STDOUT)
    values=dict(line.split('=',1) for line in (out/'last-session.txt').read_text().splitlines() if '=' in line)
    assert values['build_version']=='1.19-cost1'
    assert values['runs']==values['video_submitted']=='500' and values['snapshot_load_successes']=='1'
    assert values['error']=='' and values['held']==values['video_dupes']==values['write_errors']=='0'
    assert int(values['output_accepted_frames_including_priming'])==int(values['resampled_enqueued_frames'])+int(values['priming_silence_frames'])
    assert values['audio_remaining_frames']=='0'
    lines=(out/'unit-cost.csv').read_text().splitlines()
    meta=dict(line[1:].split('=',1) for line in lines if line.startswith('#'))
    assert meta['mock']=='1' and meta['overflow']=='0'
    rows=list(csv.DictReader(line for line in lines if not line.startswith('#')))
    frames=[r for r in rows if r['type']=='frame'];assert len(frames)==500
    assert [int(r['frame']) for r in frames]==list(range(500))
    assert all((277<=int(r['frame'])<=438) or int(r['kind'])==0 for r in frames)
    if mode==2:
        benches=[r for r in rows if r['type']=='bench']
        assert sum(int(r['iterations']) for r in benches)>1000
        assert all(int(r['warm'])==16 and int(r['iterations']) in (1,32) for r in benches)
        assert any(r['iterations']=='1' for r in benches) and any(r['iterations']=='32' for r in benches)
    if mode==1:
        sampled={int(r['frame']) for r in frames if r['kind']=='1'}
        assert sampled=={f for f in range(277,439) if f%8==5}
        assert all(int(r['cpu_ns'])>0 for r in rows if r['type']=='phase' and int(r['frame']) in sampled and r['kind']=='1')
    if mode==3:
        assert {int(r['frame']) for r in frames if r['kind']=='3'}=={320}
        counts=next(r for r in rows if r['type']=='row_sampling' and r['frame']=='320')
        assert counts['warm']=='1' and int(counts['iterations'])>1000
    subprocess.run([sys.executable,str(ROOT/'build/analyze-a7-cost.py'),str(out),'--contracts-only'],check=True,stdout=subprocess.DEVNULL)
versions=[tuple(map(int,m)) for m in re.findall(r'GLIBC_(\d+)\.(\d+)',(OUT/'runner-abi.txt').read_text())]
assert max(versions)<=(2,30)
libs=['-L'+str(ROOT/'build/sysroot/lib'),'-Wl,--no-as-needed']+['-l:'+n for n in ('libdl-2.30.so','libz.so.1','libpthread-2.30.so','librt-2.30.so','libm-2.30.so','libc-2.30.so','libgcc_s.so.1','ld-2.30.so')]
subprocess.run(['arm-linux-gnueabihf-gcc','-DD35_FOCUS_PROFILE','-mcpu=cortex-a7','-mfpu=neon-vfpv4','-mfloat-abi=hard','-marm','-fno-stack-protector','-U_TIME_BITS','-D_TIME_BITS=32','-U_FILE_OFFSET_BITS','-D_FILE_OFFSET_BITS=32','-std=gnu99','-O2','-Wall','-Wextra','-Werror','-no-pie','-nostdlib','-I'+str(ROOT/'build/snes9x2005/libretro-common/include'),'/usr/arm-linux-gnueabihf/lib/crt1.o',str(OUT/'runner/cost-native-check.c'),str(ROOT/'build/glibc230-stat-compat.c'),*libs,'-o',str(OUT/'cost-native-check')],check=True)
native=OUT/'native-contracts';native.mkdir(exist_ok=False)
with (OUT/'native-check.log').open('w') as log:
    subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(OUT/'cost-native-check'),str(ROOT/'build/plus-a7-out/ff6.sfc'),str(core),str(OUT/'replay.state'),str(native)],check=True,env=env,stdout=log,stderr=subprocess.STDOUT)
assert 'deferred full PCM flush after join' in (OUT/'native-check.log').read_text()
suite_capture=OUT/'suite-contracts';suite_capture.mkdir(exist_ok=False)
env['D35_COST_TEST_MOCK']='1';env['D35_COST_CONTRACT_FIXTURE']='1'
with (OUT/'suite-check.log').open('w') as log:
    subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(OUT/'unit-suite'),str(suite_capture),str(core),str(ROOT/'build/plus-a7-out/ff6.sfc'),str(OUT/'replay.state')],check=True,env=env,stdout=log,stderr=subprocess.STDOUT)
assert 'suite end passes=13 failures=0' in (OUT/'suite-check.log').read_text()
assert len(list(suite_capture.glob('pass-*/unit-cost.csv')))==13
assert len(list(suite_capture.glob('pass-*/pcm-full.txt')))==13
subprocess.run([sys.executable,str(ROOT/'build/analyze-a7-cost.py'),str(suite_capture),'--contracts-only'],check=True,stdout=subprocess.DEVNULL)
sources=[ROOT/'build'/p for p in ('a7-cost.h','a7-cost-core.c','a7-cost-host.h','a7-cost-main.c','a7-cost-native-check.c','analyze-a7-cost.py','prepare-a7-cost.py','build-a7-cost.sh','qualify-a7-cost.py')]
sources+=list((ROOT/'build/snes-mvp').glob('*.c'))+list((ROOT/'build/snes-mvp').glob('*.h'))
sources+=[ROOT/'build'/p for p in ('plus-a7-profile.h','plus-a7-window.h','glibc230-stat-compat.c')]
q={'version':'1.19-cost1','passed':True,'hardware_measured':False,'candidate_installed':False,
   'tree':name,'checks':['600 aligned replay frames: exact pixels/native PCM/geometry/normalized state across all three modes',
   'four500-frame real-runner mock captures; identity-checked private state; full PCM accounting; no lost frames',
   'record bounds, per-frame CPU/wall/frequency columns, phase cadence, warmup and individual/batch labels',
   'consuming native provider: injected fault, deferred PCM flushing,120 full-frame retry/drain, sustained deficit rejection, previous pass preserved'],
   'automated_driver_check':'13 distinct500-call captures; zero failures; phase/benchmark/control ordering and post-pass sync',
   'runner_sha256':digest(OUT/'unit-runner'),'core_sha256':digest(core),
   'suite_sha256':digest(OUT/'unit-suite'),
   'core_crc32':f'{zlib.crc32(core.read_bytes()):08x}','core_bytes':core.stat().st_size,
   'shipping_core_sha256':old['core_sha256'],'state_sha256':digest(OUT/'replay.state'),
   'source_hashes':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(set(sources))},
   'artifacts':{p.relative_to(ROOT).as_posix():digest(p) for p in [OUT/'equivalence.log',OUT/'runner-abi.txt',OUT/'native-check.log',OUT/'suite-check.log']},
   'limits':['QEMU timings discarded as performance evidence','warm repeated paths are not full candidate cache interaction costs',
   'shadow deferral lengths in baseline are not the longer candidate spans','gate remains unmeasured until physical captures and coverage checks']}
(OUT/'verification.json').write_text(json.dumps(q,indent=2)+'\n')
print(json.dumps({'passed':True,'version':'1.19-cost1','performance_evidence':'PENDING A7 boot','candidate_installed':False},indent=2))
