"""Read-only archived manual return analysis; no device access or replay."""
from pathlib import Path
from hashlib import sha256
import json, statistics, sys
root=Path(__file__).resolve().parent.parent
a=Path(sys.argv[1]).resolve()
assert a.is_relative_to(root/'device-evidence')
archive=json.loads((a/'archive.json').read_text())
for e in archive['all_retro_files']:
    assert sha256((a/e['path']).read_bytes()).hexdigest()==e['sha256']
p=a/'retro/snes-combined-gameplay1'
expected={'plus-a7.so':'ee0b241c3b7c561e76efbedbbdcf37bf8e104bb6754d7b0493c3ed4774172155',
          'snes-mvp':'c0b56975ea847ecfa737eee43bab0781d8d039b9f3bcc6af5508e7bbfd231310'}
for n,h in expected.items(): assert sha256((p/n).read_bytes()).hexdigest()==h
s=dict(x.split('=',1) for x in (p/'last-progress.txt').read_text().splitlines() if '=' in x)
rows=[list(map(int,v.split(','))) for k,v in s.items() if k.startswith('frame_cost_') and k!='frame_cost_columns']
ordinary=rows[:-1]
deadline=358416/21477272*1000
step=statistics.mean(x[3]+x[9] for x in ordinary)/1e6
result={'archive':a.name,'card_writes':0,'fat_clean':archive['fat_clean'],
 'archive_hashes_verified':True,'runner_core_hashes_match':True,
 'user_observation':'Bio Blast seemed fine; Confuser crashed',
 'effect_identity_from_log':False,'session_seconds':int(s['session_elapsed_ns'])/1e9,
 'runs':int(s['runs']),'drawings':int(s['video_submitted']),'held':int(s['held']),
 'failure':s['pcm_error_detail'],'ordinary_tail_calls':len(ordinary),
 'tail_mean_core_wall_ms':statistics.mean(x[3] for x in ordinary)/1e6,
 'tail_mean_core_cpu_ms':statistics.mean(x[4] for x in ordinary)/1e6,
 'tail_mean_admission_ms':statistics.mean(x[9] for x in ordinary)/1e6,
 'tail_mean_core_plus_admission_ms':step,'nominal_deadline_ms':deadline,
 'tail_minimum_required_saving_ms':step-deadline,
 'tail_local_cadence_proxy_fps':1000/step,
 'tail_local_pcm_proxy_frames_per_second':735.94752/(step/1000),
 'final_pointer_bias_frames':int(s['pcm_appl_ptr'])-int(s['pcm_epoch_transferred_frames']),
 'limits':['Final aborted call excluded from ordinary costs; its audio failure handling inflates wall time.',
 'Short tail is not a complete effect timeline or sustainable throughput measurement.',
 'Pointer bias prevents treating reported reserve as independently trustworthy.',
 'No per-effect identity, renderer mode/subphase counts, or retained input replay.']}
(a/'manual-return-analysis.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
