from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json, re
root=Path(__file__).resolve().parent.parent
out=root/'build/snes-mvp/out'
def digest(p): return sha256(p.read_bytes()).hexdigest()
report=dict(line.split('=',1) for line in (out/'smoke-final/last-session.txt').read_text().splitlines() if '=' in line)
assert report['runs']=='180' and report['mock_backend']=='1'
assert report['error']=='' and report['write_errors']=='0'
assert int(report['output_accepted_frames_including_priming']) == int(report['resampled_enqueued_frames'])+int(report['priming_silence_frames'])
assert report['rom_crc32']=='a27f1c7a' and report['core_crc32']=='5ba71d2a'
paced=dict(line.split('=',1) for line in (out/'paced-smoke/last-session.txt').read_text().splitlines() if '=' in line)
assert paced['runs']=='30' and paced['error']=='' and paced['write_errors']=='0'
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
      'binary_sha256':digest(out/'snes-mvp'),'binary_bytes':(out/'snes-mvp').stat().st_size,
      'glibc_max':'.'.join(map(str,max(versions))),'real_core_frames':180,
      'audio_transport_and_save_contracts':(out/'contracts.log').read_text().strip(),
      'checks':['exact core ZIP run','PCM accounting','UI rendering','library scanning','invalid ROM rejection',
                'real launcher first frame with stuck buttons','input suppression and repeat',
                'durable startup breadcrumbs','startup watchdog and ready-session lifetime',
                'vendor splash handoff before child launch','splash timeout prevents competing display owner',
                'actual GPIO backend against extracted stock callback table','shared heartbeat preserves other control fields',
                'clock-skew input-sleep regression and real ARM polling loop',
                'real launcher Down/Up/A through real waits','30-frame real core run with kernel-clock pacing'],
      'hardware_audio_display_controls':'unverified; repaired startup device test required',
      'performance':'QEMU timings are not device performance evidence'}
(out/'verification.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(data,indent=2))
