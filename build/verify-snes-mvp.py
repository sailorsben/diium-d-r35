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
assert report['build_version']=='1.9' and report['phase']=='finished' and report['session_id']
assert report['sink_rate']=='32040' and report['native_audio_frames']==report['resampled_enqueued_frames']
assert 'PASS: actual ARM32 PCM ABI' in (out/'native-pcm-check.log').read_text()
assert 'bounded blocked flush without silent recovery' in (out/'audio-owner-check.log').read_text()
assert 'PASS: real ARM runner killed before cleanup' in (out/'diagnostic-crash.log').read_text()
assert 'PASS: diagnostic progress persisted before child exit' in (out/'wrapper-contract.log').read_text()
assert 'PASS: wrapper captures CPU/memory with firmware-style PATH lacking head and sed' in (out/'wrapper-contract.log').read_text()
assert 'PASS: 8388608 scalar/vector color comparisons' in (root/'build/plus-a7-out/kernel-check.log').read_text()
assert 'PASS: 60000 backdrop/window spans' in (root/'build/plus-a7-out/kernel-check.log').read_text()
assert 'PASS: seven A7 tile modes specialized' in (root/'build/plus-a7-out/codegen-check.log').read_text()
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
      'version':'1.9','core_sha256':digest(core),'core_crc32':report['core_crc32'],'core_bytes':core.stat().st_size,
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
      'full_render':True,'equivalence_frames':1200,'kernel_color_comparisons':8388608,
      'kernel_tile_rows':280000,'display_queue_contract':(out/'display-queue-contract.log').read_text().strip(),
      'kernel_backdrop_window_spans':60000,
      'a7_codegen':(root/'build/plus-a7-out/codegen-check.log').read_text().strip(),
      'snapshot_runner_integration':'120 frames, migrated snapshot loaded via pause menu, zero held drawings',
      'core_equivalence':(root/'build/plus-a7-out/equivalence.log').read_text().strip(),
      'diagnostic_crash_contract':(out/'diagnostic-crash.log').read_text().strip(),
      'native_pcm_contract':(out/'native-pcm-check.log').read_text().strip(),
      'audio_owner_contract':(out/'audio-owner-check.log').read_text().strip(),
      'hardware_audio_display_controls':'Earlier boot/input/state/save confirmed; 1.9 native PCM settings, audible continuity, sustained full rendering and stability pending physical test',
      'hardware_qualified':False,
      'performance':'QEMU timings are not device performance evidence'}
sources=list((root/'build/snes-mvp').glob('*.c'))+list((root/'build/snes-mvp').glob('*.h'))
sources+=list((root/'build/snes-mvp').glob('*.py'))+list((root/'build/snes-mvp').glob('*.sh'))
sources += [root/'build'/name for name in ('build-snes-mvp.sh','check-snes-mvp.sh','check-native-pcm.sh',
    'apply-plus-a7.py','build-plus-a7.sh','check-plus-a7.sh','plus-a7-render.h','plus-a7-check.c',
    'plus-a7-equivalence.c','prepare-plus-inputs.py','check-plus-a7-codegen.py','verify-snes-mvp.py')]
data['source_hashes']={p.relative_to(root).as_posix():digest(p) for p in sorted(set(sources))}
logs=[out/name for name in ('contracts.log','display-queue-contract.log','startup-contract.log',
    'wrapper-contract.log','board-input-contract.log','vendor-input-reference.log','timing-contract.log',
    'platform-contract.log','abi-versions.txt','dependencies.txt','diagnostic-crash.log',
    'native-pcm-check.log','audio-owner-check.log')]
logs += [out/'smoke-final/last-session.txt',out/'paced-smoke/last-session.txt']
logs += [root/'build/plus-a7-out'/name for name in ('kernel-check.log','codegen-check.log',
    'equivalence.log','runner-integration.log')]
data['check_artifact_hashes']={p.relative_to(root).as_posix():digest(p) for p in logs}
(out/'verification.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(data,indent=2))
