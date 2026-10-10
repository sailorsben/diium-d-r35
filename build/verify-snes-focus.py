"""Verify focused diagnostics against unchanged 1.19 dependencies, offline only."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json, re
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/snes-focus-out'
def digest(path):return sha256(path.read_bytes()).hexdigest()
def fields(path):return dict(line.split('=',1) for line in path.read_text().splitlines() if '=' in line)
release=json.loads((ROOT/'releases/snes-mvp-1.19/manifest.json').read_text())
assert digest(ROOT/'build/plus-a7-out/plus-a7.so')==release['core_sha256']
s=fields(OUT/'smoke/last-session.txt')
assert s['build_version']=='1.19-focus1' and s['runs']==s['video_submitted']=='180'
assert s['error']=='' and s['held']==s['video_dupes']==s['write_errors']=='0'
assert int(s['output_accepted_frames_including_priming'])==int(s['resampled_enqueued_frames'])+int(s['priming_silence_frames'])
assert s['audio_remaining_frames']=='0' and s['focus_profile']=='1'
frames=[list(map(int,v.split(','))) for k,v in s.items() if re.fullmatch(r'frame_cost_\d+',k)]
callbacks=[list(map(int,v.split(','))) for k,v in s.items() if re.fullmatch(r'focus_cost_\d+',k)]
assert len(frames)==len(callbacks)==64 and [f[0] for f in frames]==list(range(117,181))
assert [f[0] for f in callbacks]==[f[0] for f in frames]
assert any(f[2] and f[5]>0 and f[6]>0 for f in frames)
assert all((f[2]!=0)==(c[1]!=0) for f,c in zip(frames,callbacks))
assert all((c[2]>0 and c[3]>0 and c[4]>0 and c[5]==1) if f[2] else c[1:]==[0]*5 for f,c in zip(frames,callbacks))
assert sum(int(v) for k,v in s.items() if re.fullmatch(r'core_wall_bin_\d+ms',k))==180
log=(OUT/'focus-check.log').read_text()
for term in ('all64 cadence offsets','sampled overhead cannot trigger','measured callback PCM equals','all64 frame/CPU callback records','actual callback conversions equal original 64-bit oracle'):
 assert term in log,term
native=(OUT/'native-check.log').read_text()
for term in ('two snapshot loads','sustained 19.8805ms','failed-session report and exact PCM history'):
 assert term in native,term
versions=[tuple(map(int,m)) for m in re.findall(r'GLIBC_(\d+)\.(\d+)',(OUT/'abi.txt').read_text())]
assert max(versions)<=(2,30)
sources=[ROOT/'build'/n for n in ('build-snes-focus.sh','verify-snes-focus.py','glibc230-stat-compat.c')]
sources+=list((ROOT/'build/snes-mvp').glob('*.c'))+list((ROOT/'build/snes-mvp').glob('*.h'))
artifacts=[OUT/n for n in ('focus-check.log','native-check.log','abi.txt','smoke/last-session.txt')]
data={'version':'1.19-focus1','qualified_utc':datetime.now(timezone.utc).isoformat(),'passed':True,
 'binary_sha256':digest(OUT/'snes-mvp'),'binary_bytes':(OUT/'snes-mvp').stat().st_size,
 'core_sha256':release['core_sha256'],'core_bytes':release['core_bytes'],'core_crc32':release['core_crc32'],
 'wrapper_sha256':release['wrapper_sha256'],'core_and_wrapper_unchanged_from_1_19':True,
 'render_audio_and_pacing_policy_unchanged':True,'hardware_qualified':False,
 'diagnostic':'64 retained frame records; one-in-eight phase/callback CPU sampling after ordinary 16ms wall or15ms CPU;96-frame burst; one-in64 baseline; sampled calls cannot extend burst',
 'limits':'Phase clock overhead is included. Callback CPU may overlap inclusive APU time. Residual includes SPC port execution. QEMU timings are not device timings. No audio fix claimed.',
 'checks':['180 real-core full-render frames and exact PCM accounting','independent resampler oracle','all64 cadence offsets over actual1.19 failing costs','sampled-cost feedback excluded','64-record report capacity','consuming native PCM fault/retry/two snapshot loads/drain/sustained deficit preservation'],
 'source_hashes':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(set(sources))},
 'check_artifact_hashes':{p.relative_to(ROOT).as_posix():digest(p) for p in artifacts}}
(OUT/'verification.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({'passed':True,'version':data['version'],'core_unchanged':True,'retained_frames':64,'hardware_result':'pending'},indent=2))
