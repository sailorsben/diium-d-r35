"""Verify and publish the consumed 1.15 return, excluding private progress."""
from pathlib import Path
from hashlib import sha256
import json,importlib.util,statistics
ROOT=Path(__file__).resolve().parent.parent
RETURN=ROOT/'device-evidence/snes-mvp-return-20261006T055533Z'
PREFIX='evidence/2026-10-06/snes-mvp-1.15-return/'

def digest(path): return sha256(path.read_bytes()).hexdigest()
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'build'/file)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def fields(path): return dict(s.split('=',1) for s in path.read_text(encoding='utf-8').splitlines() if '=' in s)

def publish():
    c=json.loads((RETURN/'collection.json').read_text(encoding='utf-8'))
    assert c['card_writes']==0 and not c['armed_present']
    for e in c['copied_and_hash_verified']: assert digest(RETURN/e['archive_path'])==e['sha256']
    lab=json.loads((RETURN/'lab-collection.json').read_text(encoding='utf-8'))
    assert not lab['lab_armed'] and len(lab['copied'])==49
    for e in lab['copied']: assert digest(RETURN/'platform-lab'/e['relative_path'])==e['sha256']
    release=json.loads((ROOT/'releases/snes-mvp-1.15/manifest.json').read_text(encoding='utf-8'))
    for n,k in [('snes-mvp','binary_sha256'),('launch.sh','wrapper_sha256'),('plus-a7.so','core_sha256')]:
        assert digest(RETURN/'snes-mvp'/n)==release[k]
    protected=json.loads((ROOT/'device-evidence/snes-mvp-1.15-install-20261006T054832Z/protected.json').read_text())
    unchanged=[];changed=[]
    for e in c['copied_and_hash_verified']:
        n=e['card_path']
        if n in protected and ('/saves/' in n or '/states/' in n) and not n.endswith(('.txt','.txt.bak')):
            (unchanged if e['sha256']==protected[n] else changed).append(n)
    assert all(n.endswith(('.srm','.srm.bak')) for n in changed),changed
    assert all(c['production_hashes'][n]==protected[n] for n in c['production_hashes'])
    original=RETURN/'snes-mvp/saves/game-a27f1c7a-3145728-core-5ba71d2a-656816.state'
    matched=RETURN/'snes-mvp/saves/game-a27f1c7a-3145728-core-5f68b738-785504.state'
    replay=ROOT/'build/plus-a7-out/returned.state'
    assert original.read_bytes()[40:]==matched.read_bytes()[40:]==replay.read_bytes()[40:]
    reports=[]
    for name,count in [('last-session.txt.bak',819),('last-session.txt',196)]:
        f=fields(RETURN/'snes-mvp/saves'/name)
        assert f['build_version']=='1.15' and int(f['runs'])==count and f['phase']=='finished'
        assert f['held']=='0' and f['write_errors']=='1' and f['pcm_state']=='1'
        assert f['snapshot_load_successes']=='1' and f['snapshot_load_rejections']=='0'
        assert 'trace_errno=0 trace_synced=1' in f['pcm_error_detail']
        assert int(f['resampled_enqueued_frames'])+int(f['priming_silence_frames'])==int(f['output_accepted_frames_including_priming'])+int(f['audio_remaining_frames'])
        assert int(f['pcm_appl_ptr'])-int(f['pcm_epoch_transferred_frames'])==384
        rows=[list(map(int,v.split(','))) for k,v in f.items() if k.startswith('frame_cost_') and k.split('_')[-1].isdigit()]
        samples=[list(map(int,v.split(','))) for k,v in f.items() if k.startswith('sample_cost_') and k.split('_')[-1].isdigit()]
        loaded=[r for r in rows if r[1]==2]
        assert len(loaded) in (18,19) and loaded[-1][8]==0 and loaded[0][2]==0
        steady=[r for r in loaded[1:-1] if not r[2]]
        metrics={}
        for label,index in [('core_wall',3),('core_cpu',4),('audio_callback_wall',7),('video_callback_wall',8),('admission_wait',9)]:
            values=[r[index]/1e6 for r in steady]
            metrics[label+'_ms']={'count':len(values),'mean':statistics.mean(values),
                'median':statistics.median(values),'min':min(values),'max':max(values)}
        reports.append({'runs':count,'post_load_runs':len(loaded),
            'snapshot_load_successes':1,'snapshot_load_rejections':0,'ordinary_post_load':metrics,
            'sampled_loaded_frames':[{'run':r[0],'wall_ms':r[3]/1e6,'cpu_ms':r[4]/1e6,
                'apu_inclusive_cpu_ms':r[5]/1e6,'ppu_inclusive_cpu_ms':r[6]/1e6} for r in samples if r[1]==2],
            'display_reservation_total_ms':int(f['display_reserve_wait_ns'])/1e6,
            'display_queue_high':int(f['display_queue_high']),
            'error_detail':f['pcm_error_detail']})
    trace=module('flight','analyze-pcm-flight.py').analyze(RETURN/'snes-mvp/last-pcm-fault.txt',44100)
    assert [e['appl_minus_accepted'] for e in trace['application_pointer_difference_changes']]==[128,256,384]
    assert trace['accepted_pointer_difference_first_sample']==0
    trace['matched_large_batch_interval']['limit'] += ' A batch split at the 8192-frame software-ring boundary is omitted from these large anchors; the long anchor gap is not one slow core call. Endpoint accepted production rate remains valid.'
    result={'version':'1.15','mvp_files':len(c['copied_and_hash_verified']),'lab_files':49,
        'read_only_archive_verified':True,'one_shots_consumed':True,'exact_release_verified':True,
        'prior_game_progress_files_unchanged':len(unchanged),'updated_sram_files_archived':len(changed),
        'snapshots_unchanged':True,'stock_hook_core_unchanged':True,'exact_replay_payload_verified':True,
        'reports':reports,'flight_analysis':trace,
        'attempts':3,'capture_limit':'Only the second and third final reports survive; each retry rotates the final report and replaces the PCM history. First-attempt SYNC_OBSERVE metadata remains in stderr, but its individual frame history is lost.',
        'physical_failure_boundary':'Successful snapshot loads followed by 19/18 core calls and controlled audio failure, library return and clean display teardown. No new whole-device poweroff or snapshot rejection independently established.',
        'inference':'The expensive scene consumes approximately 18ms of ordinary main-thread CPU and 19.3ms wall time before loop/platform work. About 0.18ms admission waits cannot explain the deficit. Sampled PPU cost is about 10ms; raster work census follows.',
        'limits':'Two sampled expensive calls are attribution clues, not a latency distribution. Kernel CPU-clock sampling itself adds about 2ms on sampled calls; APU time includes callback work. First-launch cause and exact vendor pointer/stop mechanism remain unresolved.',
        'next_action':'Use exact local state replay to identify repeated raster/tile work, then correct the actual renderer budget. No blind re-arm of 1.15.'}
    (RETURN/'analysis.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();entries=json.loads(raw)['entries']
    assert not any(e['published'].startswith(PREFIX) for e in entries)
    for e in entries: assert digest(ROOT/e['published'])==e['published_sha256']
    selected={'analysis.json':RETURN/'analysis.json','session-second.txt':RETURN/'snes-mvp/saves/last-session.txt.bak',
        'session-third.txt':RETURN/'snes-mvp/saves/last-session.txt'}
    for n in ('last-pcm-fault.txt','startup.log','last-run.log','last-progress.txt','last-progress.previous',
              'runtime-platform.txt','runtime-platform-latest.txt','kernel-tail.txt','diagnostic-flush.log'):
        selected[n]=RETURN/'snes-mvp'/n
    additions=[]
    for n,p in selected.items():
        data=p.read_bytes();out=data.decode().replace(str(ROOT),'<workspace>').replace(ROOT.as_posix(),'<workspace>').replace('\r\n','\n').encode()
        for forbidden in (b'GITHUB_TOKEN',b'Bearer ',b'github_pat_',b'ghp_',b'C:\\Users',b'.codex/attachments'): assert forbidden not in out,(n,forbidden)
        target=ROOT/PREFIX/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(out)
        additions.append({'source':p.relative_to(ROOT).as_posix(),'published':target.relative_to(ROOT).as_posix(),
            'source_sha256':sha256(data).hexdigest(),'published_sha256':sha256(out).hexdigest(),'bytes':len(out),'normalized':data!=out})
    manifest.write_bytes(module('publisher','publish-snes-1.15.py').append_manifest(raw,additions))
    print(json.dumps(result,indent=2))
if __name__=='__main__': publish()
