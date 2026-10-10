from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json, re, zlib
root=Path(__file__).resolve().parent.parent
out=root/'build/snes-mvp/out'
def digest(p): return sha256(p.read_bytes()).hexdigest()
report=dict(line.split('=',1) for line in (out/'smoke-final/last-session.txt').read_text().splitlines() if '=' in line)
assert report['runs']=='180' and report['mock_backend']=='1'
assert report['error']=='' and report['write_errors']=='0'
assert int(report['output_accepted_frames_including_priming']) == int(report['resampled_enqueued_frames'])+int(report['priming_silence_frames'])
core=root/'build/plus-a7-out/plus-a7.so'
assert report['rom_crc32']=='a27f1c7a' and report['core_crc32']==f'{zlib.crc32(core.read_bytes())&0xffffffff:08x}'
assert report['held']=='0' and report['video_dupes']=='0' and report['video_submitted']=='180'
assert int(report['audio_cleared_frames'])==0 and int(report['audio_remaining_frames'])==0
paced=dict(line.split('=',1) for line in (out/'paced-smoke/last-session.txt').read_text().splitlines() if '=' in line)
assert paced['runs']=='30' and paced['error']=='' and paced['write_errors']=='0'
assert paced['held']=='0' and paced['video_submitted']=='30'
assert 'PASS: real display FIFO' in (out/'display-queue-contract.log').read_text()
assert report['build_version']=='1.19' and report['phase']=='finished' and report['session_id']
assert report['phase_profile_available']=='1' and int(report['phase_profile_samples'])==3
costs=[list(map(int,v.split(','))) for k,v in report.items() if k.startswith('frame_cost_') and k[len('frame_cost_'):].isdigit()]
assert len(costs)==24 and [f[0] for f in costs]==list(range(157,181))
samples=[list(map(int,v.split(','))) for k,v in report.items() if k.startswith('sample_cost_')]
assert len(samples)==3 and [f[0] for f in samples]==[4,68,132]
assert all(f[2]==1 and f[5]>0 and f[6]>0 for f in samples)
assert 'actual callback conversions equal original 64-bit oracle' in (out/'contracts.log').read_text()
assert 'sustained 19.8805ms production against 44100Hz' in (out/'native-runner-check.log').read_text()
assert report['sink_rate']=='32040' and report['native_audio_frames']==report['resampled_enqueued_frames']
assert 'kernel WRITEI auto-start without duplicate START' in (out/'native-pcm-check.log').read_text()
assert 'runtime errors and kernel snapshot captured with tail absent' in (out/'wrapper-contract.log').read_text()
assert 'PCM fault capture fsyncs file and directory before error return' in (out/'native-pcm-check.log').read_text()
assert 'bounded PCM flight history writes only on fault' in (out/'native-pcm-check.log').read_text()
assert 'fresh PCM fault history persisted before exit' in (out/'wrapper-contract.log').read_text()
assert 'post-HWSYNC state/pointers' in (out/'native-pcm-check.log').read_text()
assert 'fresh observation required before paced admission' in (out/'audio-owner-check.log').read_text()
assert 'two snapshot loads and re-primed resumes' in (out/'native-runner-check.log').read_text()
assert 'PASS: shipped1.10' in (out/'old-owner-regression.log').read_text()
assert 'PASS: actual ARM32 PCM ABI' in (out/'native-pcm-check.log').read_text()
assert 'bounded blocked flush without silent recovery' in (out/'audio-owner-check.log').read_text()
assert 'PASS: real ARM runner killed before cleanup' in (out/'diagnostic-crash.log').read_text()
assert 'PASS: actual wrapper performs zero diagnostic card writes or global sync during ready child' in (out/'wrapper-contract.log').read_text()
assert 'PASS: wrapper captures CPU/memory with firmware-style PATH lacking head and sed' in (out/'wrapper-contract.log').read_text()
assert 'PASS: 8388608 scalar/vector color comparisons' in (root/'build/plus-a7-out/kernel-check.log').read_text()
assert 'PASS: 60000 backdrop/window spans' in (root/'build/plus-a7-out/kernel-check.log').read_text()
assert 'PASS: 60000 planar tiles' in (root/'build/plus-a7-out/kernel-check.log').read_text()
assert 'PASS: 20000 lazy-row cache cases' in (root/'build/plus-a7-out/kernel-check.log').read_text()
assert 'PASS: 16777216 extracted stock/patched register cases' in (root/'build/plus-a7-out/raster-contract.log').read_text()
assert 'failed-session report and exact PCM history survive library retry' in (out/'native-runner-check.log').read_text()
assert 'PASS: seven A7 tile modes specialized' in (root/'build/plus-a7-out/codegen-check.log').read_text()
assert 'O3/LTO and internal visibility applied' in (root/'build/plus-a7-out/codegen-check.log').read_text()
assert 'owned sampled phase ABI measures APU/PPU' in (root/'build/plus-a7-out/equivalence.log').read_text()
assert 'PASS: 12000 frames exact visible pixels' in (root/'build/plus-a7-out/narshe-long-equivalence.log').read_text()
assert 'PASS: expected old-wrapper rejection' in (out/'wrapper-regression.log').read_text()
assert 'PASS: 131072 actual CGRAM half-write cases' in (root/'build/plus-a7-out/color-cache-contract.log').read_text()
assert 'complete Magitek Bio Blast scene replay' in (root/'build/plus-a7-out/magitek-bio-equivalence.log').read_text()
assert 'PASS: 1200 frames exact visible pixels' in (root/'build/plus-a7-out/equivalence.log').read_text()
assert 'splits 1196 frames into multiple byte-equivalent batches' in (root/'build/plus-a7-out/equivalence.log').read_text()
assert 'submitted=120 held=0' in (root/'build/plus-a7-out/runner-integration.log').read_text()
for line in (root/'build/plus-a7-out/checked-inputs.sha256').read_text().splitlines():
    wanted,name=line.split(maxsplit=1)
    assert digest(root/'build'/name.strip())==wanted, 'Core check input changed: '+name
assert 'PASS:' in (out/'contracts.log').read_text()
assert 'PASS: real launcher first frame completes' in (out/'startup-contract.log').read_text()
assert 'PASS: real launcher menu keeps polling through kernel-clock waits' in (out/'startup-contract.log').read_text()
assert 'READY: first library frame completed' in (out/'startup-contract/startup.log').read_text()
assert (out/'startup-contract/ready').read_text()=='ready\n'
assert 'PASS: startup wrapper stalled' in (out/'wrapper-contract.log').read_text()
assert 'startup deadline does not limit a ready session' in (out/'wrapper-contract.log').read_text()
assert 'PASS: startup wrapper splash-handoff' in (out/'wrapper-contract.log').read_text()
assert 'PASS: splash timeout refuses to start competing MVP display owner' in (out/'wrapper-contract.log').read_text()
assert 'PASS: actual board GPIO decoder matches vendor D-pad/face pins' in (out/'board-input-contract.log').read_text()
assert 'PASS: input reference extracted from pinned stock callback table' in (out/'vendor-input-reference.log').read_text()
assert 'PASS: vendor heartbeat layout/counter/rate' in (out/'platform-contract.log').read_text()
assert 'PASS: 26-second libc/kernel clock skew cannot stall 8 ms input waits' in (out/'timing-contract.log').read_text()
assert 'PASS: real ARM kernel-clock/relative-sleep loop completed 25 polls' in (out/'timing-contract.log').read_text()
assert 'Unsupported SNES ROM size' in (out/'reject.log').read_text()
assert 'ff3.zip' in (out/'library-list.txt').read_text()
assert all((out/'preview'/name).stat().st_size>900000 for name in ('library.ppm','pause.ppm','empty.ppm'))
versions=[tuple(map(int,m)) for m in re.findall(r'GLIBC_(\d+)\.(\d+)',(out/'abi-versions.txt').read_text())]
assert max(versions)<=(2,30)
data={'passed':True,'time_utc':datetime.now(timezone.utc).isoformat(),
      'version':'1.19','core_sha256':digest(core),'core_crc32':report['core_crc32'],'core_bytes':core.stat().st_size,
      'qualified_snapshot_sha256':digest(root/'build/plus-a7-out/returned.state'),
      'a7_header_sha256':digest(root/'build/plus-a7-render.h'),
      'binary_sha256':digest(out/'snes-mvp'),'binary_bytes':(out/'snes-mvp').stat().st_size,
      'wrapper_sha256':digest(root/'build/snes-mvp/launch.sh'),
      'glibc_max':'.'.join(map(str,max(versions))),'real_core_frames':180,
      'audio_transport_and_save_contracts':(out/'contracts.log').read_text().strip(),
      'checks':['exact core ZIP run','PCM accounting','UI rendering','library scanning','invalid ROM rejection',
                'real launcher first frame with stuck buttons','input suppression and repeat',
                'durable startup breadcrumbs','startup watchdog and ready-session lifetime',
                'vendor splash handoff before child launch','splash timeout prevents competing display owner',
                'actual GPIO backend against extracted stock callback table','shared heartbeat preserves other control fields',
                'clock-skew input-sleep regression and real ARM polling loop',
                'real launcher Down/Up/A through real waits','30-frame real core run with kernel-clock pacing'],
      'full_render':True,'equivalence_frames':1200,'extended_equivalence_frames':12000,'kernel_color_comparisons':8388608,
      'kernel_tile_rows':280000,'display_queue_contract':(out/'display-queue-contract.log').read_text().strip(),
      'kernel_backdrop_window_spans':60000,
      'kernel_planar_tiles':60000,'frontend_conversion_oracle_cases':8,
      'raster_register_contract':(root/'build/plus-a7-out/raster-contract.log').read_text().strip(),
      'compilation':'GCC Cortex-A7 ARM hard-float O3/LTO, internal visibility, explicit libretro/owned exports; no blanket fast-math',
      'phase_accounting':'24 recent calls and eight retained sampled calls in RAM; kernel thread CPU APU/PPU inclusive regions on one in 64 calls, reset on resume; unsampled calls retain CPU/wall/frontend costs',
      'a7_codegen':(root/'build/plus-a7-out/codegen-check.log').read_text().strip(),
      'snapshot_runner_integration':'120 frames, migrated snapshot loaded via pause menu, zero held drawings',
      'core_equivalence':(root/'build/plus-a7-out/equivalence.log').read_text().strip(),
      'diagnostic_crash_contract':(out/'diagnostic-crash.log').read_text().strip(),
      'native_lifecycle_contract':(out/'native-runner-check.log').read_text().strip(),
      'native_pcm_contract':(out/'native-pcm-check.log').read_text().strip(),
      'audio_owner_contract':(out/'audio-owner-check.log').read_text().strip(),
      'hardware_audio_display_controls':'1.18 recovered physical trace shows Bio Blast underproduction followed by pointer divergence and SETUP/EBADFD; 1.19 physical result pending',
      'color_cache_bytes':36864,'lazy_row_cache_cases':20000,'magitek_bio_equivalence_frames':1200,'hardware_qualified':False,'purpose':'materialize only visible demanded RGB565 tile rows; preserve every frame and native audio; retain the existing PCM policy and diagnostic isolation',
      'performance':'QEMU timings are not device performance evidence'}
sources=list((root/'build/snes-mvp').glob('*.c'))+list((root/'build/snes-mvp').glob('*.h'))
sources+=list((root/'build/snes-mvp').glob('*.py'))+list((root/'build/snes-mvp').glob('*.sh'))
sources += [root/'build'/name for name in ('build-snes-mvp.sh','check-snes-mvp.sh','check-native-pcm.sh',
    'check-native-runner.sh','check-old-audio-admission.py','apply-plus-a7.py','build-plus-a7.sh','check-plus-a7.sh','plus-a7-render.h','plus-a7-check.c',
    'plus-a7-equivalence.c','plus-a7-profile.h','plus-a7-profile-core.h','plus-a7-raster.h','check-raster-contract.py',
    'plus-a7-color-cache.h','check-color-cache-contract.py','check-magitek-bio.sh','replay-snes-scene.c','replay-snes-scene.sh','prepare-render-census.py',
    'capture-snes-scene.c','capture-snes-scene.sh','prepare-plus-inputs.py','check-plus-a7-codegen.py','glibc230-stat-compat.c','verify-snes-mvp.py',
    'qualify-snes-1.19.sh','check-color-row-census.sh','analyze-color-row-census.py')]
data['source_hashes']={p.relative_to(root).as_posix():digest(p) for p in sorted(set(sources))}
logs=[out/name for name in ('contracts.log','display-queue-contract.log','startup-contract.log',
    'wrapper-contract.log','wrapper-regression.log','board-input-contract.log','vendor-input-reference.log','timing-contract.log',
    'platform-contract.log','abi-versions.txt','dependencies.txt','diagnostic-crash.log',
    'native-pcm-check.log','audio-owner-check.log','native-runner-check.log','old-owner-regression.log')]
logs += [out/'smoke-final/last-session.txt',out/'paced-smoke/last-session.txt']
logs += [root/'build/plus-a7-out'/name for name in ('kernel-check.log','codegen-check.log',
    'equivalence.log','narshe-long-equivalence.log','narshe-capture.log','runner-integration.log','raster-contract.log','color-cache-contract.log','magitek-bio-equivalence.log')]
data['check_artifact_hashes']={p.relative_to(root).as_posix():digest(p) for p in logs}
(out/'verification.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(data,indent=2))
