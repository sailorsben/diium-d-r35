"""Output qualification, aligned private snapshots and complete mock driver."""
from pathlib import Path
from hashlib import sha256
import csv, json, os, re, shutil, struct, subprocess, zlib
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/a7-pair-private-v1'
def digest(p): return sha256(p.read_bytes()).hexdigest()
baseline=ROOT/'build/plus-a7-out/plus-a7.so';combined=OUT/'core/snes9x2005_plus_libretro.so'
release=json.loads((ROOT/'releases/snes-mvp-1.19/manifest.json').read_text())
assert digest(baseline)==release['core_sha256']
for name,frames in [('equivalence-bio.log',1200),('equivalence-general.log',2400)]:
    s=(OUT/name).read_text();assert f'PASS: {frames} frames exact visible pixels, native PCM, geometry and periodic state' in s
    assert 'extra split 0 frames' in s
assert max(tuple(map(int,m)) for m in re.findall(r'GLIBC_(\d+)\.(\d+)',(OUT/'runner-abi.txt').read_text()))<=(2,30)
env=dict(os.environ,LD_LIBRARY_PATH=str(ROOT/'build/sysroot/lib'))
def run(args,log,input=None,extra=None):
    with log.open('w') as f:
        subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),*map(str,args)],
            env={**env,**(extra or {})},input=input,text=True,check=True,stdout=f,stderr=subprocess.STDOUT)
source=(ROOT/'build/magitek-bio-private/scene.state').read_bytes()
assert source[:8]==b'D35MVP01' and zlib.crc32(source[40:])==struct.unpack_from('<I',source,32)[0]
# Derive later starts by executing the shipping core with exactly the replay input.
raw_states={0:source}
for start in (261,384):
    work=OUT/f'derive-{start}';work.mkdir()
    commands=f'advance 8 100\nadvance 20 0\nadvance 8 100\nadvance {start-36} 0\nsave\nquit\n'
    run([OUT/'replay',baseline,ROOT/'build/plus-a7-out/ff6.sfc',ROOT/'build/magitek-bio-private/scene.state','-',work],work/'derive.log',commands)
    raw_states[start]=(work/'scene.state').read_bytes()
for label,core in [('baseline',baseline),('combined',combined)]:
    shutil.copy2(core,OUT/f'{label}.so')
    for start,raw in raw_states.items():
        assert zlib.crc32(raw[40:])==struct.unpack_from('<I',raw,32)[0]
        head=bytearray(raw[:40]);struct.pack_into('<II',head,20,zlib.crc32(core.read_bytes()),core.stat().st_size)
        (OUT/f'{label}-{start}.state').write_bytes(head+raw[40:])
        assert (OUT/f'{label}-{start}.state').read_bytes()[40:]==raw[40:]
# Cold cache reload of each later state must reproduce exact pixels, PCM and state.
for start in (261,384):
    run([OUT/'equivalence',baseline,combined,ROOT/'build/plus-a7-out/ff6.sfc',OUT/f'baseline-{start}.state',1200,'pair-late'],OUT/f'equivalence-reload-{start}.log')
    assert 'PASS: 1200 frames exact' in (OUT/f'equivalence-reload-{start}.log').read_text()
mock=OUT/'mock-suite';mock.mkdir()
for p in [OUT/'baseline.so',OUT/'combined.so',*OUT.glob('*.state')]:shutil.copy2(p,mock/p.name)
run([OUT/'pair-suite',mock,ROOT/'build/plus-a7-out/ff6.sfc'],OUT/'suite-check.log',extra={'D35_PAIR_MOCK':'1','D35_MVP_NO_PACING':'1'})
assert 'pair end passes=12 failures=0 stop=0' in (OUT/'suite-check.log').read_text()
for p in sorted(mock.glob('pass-*')):
    start=int(p.name.split('-')[3]);limit={0:500,261:80,384:96}[start]
    lines=(p/'pair.csv').read_text().splitlines();meta=dict(l[1:].split('=',1) for l in lines if l.startswith('#'))
    assert meta['mock']=='1' and meta['failed']=='0' and meta['phase_clocks']=='disabled'
    rows=list(csv.DictReader(l for l in lines if not l.startswith('#')))
    assert [int(r['frame']) for r in rows]==list(range(start,start+limit))
    session=dict(l.split('=',1) for l in (p/'last-session.txt').read_text().splitlines() if '=' in l)
    assert session['build_version']=='1.19-pair1' and session['runs']==session['video_submitted']==str(limit)
    assert session['snapshot_load_successes']=='1' and session['error']==''
    assert session['held']==session['video_dupes']==session['write_errors']=='0'
    assert session['audio_remaining_frames']=='0'
    assert int(session['output_accepted_frames_including_priming'])==int(session['resampled_enqueued_frames'])+int(session['priming_silence_frames'])
    assert (p/'pcm-full.txt').is_file()
    assert not list(p.glob('*.srm')) and not list(p.glob('*.state'))
payload=['pair-suite','baseline.so','combined.so','launch.sh','dispatch.sh']+[f'{label}-{start}.state' for label in ('baseline','combined') for start in (0,261,384)]
sources=[ROOT/'build'/n for n in ('archive-a7-pair-card.py','prepare-a7-pair.py','a7-pair-main.c','a7-pair-host.h','build-a7-pair.sh','qualify-a7-pair.py','bio-palette-direct.h','bio-palette-cache.h','prepare-window-batch.py','prepare-bio-fast-window.py','plus-a7-window.h','a7-cost-host.h','plus-a7-profile.h','glibc230-stat-compat.c')]
sources+=list((OUT/'runner').glob('*.[ch]'))+list((CORE:=OUT/'core').glob('source/*.[ch]'))+[CORE/'libretro.c',CORE/'link.T']
q={'version':'1.19-pair1','passed':True,'hardware_measured':False,'production_replacement':False,
   'output_comparisons':6000,'checks':['1200 Bio Blast and 2400 general exact pixel/PCM/geometry/state comparisons',
   'two cold-reloaded later states: 1200 comparisons each','12 bounded ABBA mock passes; all frames submitted; exact PCM accounting; no save writes; deferred evidence flushing',
   'shipping baseline binary exact; core profiler disabled; no census counters; GLIBC <=2.30'],
   'payload_hashes':{n:digest(OUT/n) for n in payload},
   'source_hashes':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(set(sources))},
   'proof_hashes':{p.name:digest(p) for p in OUT.glob('*.log') if p.name!='core-build.log'},
   'limits':['QEMU performance timings excluded','later starts have a fresh audio epoch; not recovery or uninterrupted full-effect proof',
   'first 16 calls of each later start are warmup; verify steady state on return','whole-path net saving, not isolated e/r/b unit prices']}
(OUT/'verification.json').write_text(json.dumps(q,indent=2)+'\n')
print(json.dumps({'passed':True,'comparisons':6000,'mock_passes':12,'A7_performance':'PENDING'},indent=2))
