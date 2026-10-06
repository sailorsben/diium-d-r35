"""Publish the consumed 1.12 return and diagnostic gap; never publish progress."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json
ROOT=Path(__file__).resolve().parent.parent
RETURN=ROOT/'device-evidence/snes-mvp-return-20261006T042555Z'
PREFIX='evidence/2026-10-05/snes-mvp-1.12-return/'
def digest(p): return sha256(p.read_bytes()).hexdigest()
def fields(p): return dict(s.split('=',1) for s in p.read_text(encoding='utf-8').splitlines() if '=' in s)
def publish():
    c=json.loads((RETURN/'collection.json').read_text(encoding='utf-8'))
    assert not c['armed_present'] and c['card_writes']==0
    for e in c['copied_and_hash_verified']: assert digest(RETURN/e['archive_path'])==e['sha256']
    lab=json.loads((RETURN/'lab-collection.json').read_text(encoding='utf-8'))
    assert not lab['lab_armed'] and len(lab['copied'])==49
    for e in lab['copied']: assert digest(RETURN/'platform-lab'/e['relative_path'])==e['sha256']
    release=json.loads((ROOT/'releases/snes-mvp-1.12/manifest.json').read_text(encoding='utf-8'))
    for n,k in [('snes-mvp','binary_sha256'),('launch.sh','wrapper_sha256'),('plus-a7.so','core_sha256')]:
        assert digest(RETURN/'snes-mvp'/n)==release[k]
    protected=json.loads((ROOT/'device-evidence/snes-mvp-1.12-install-20261006T041355Z/protected.json').read_text(encoding='utf-8'))
    unchanged=[];changed=[]
    for e in c['copied_and_hash_verified']:
        n=e['card_path']
        if n in protected and ('/saves/' in n or '/states/' in n) and not n.endswith(('.txt','.txt.bak')):
            (unchanged if e['sha256']==protected[n] else changed).append(n)
    assert all(n.endswith(('.srm','.srm.bak')) for n in changed),changed
    assert all(c['production_hashes'][n]==protected[n] for n in c['production_hashes'])
    f=fields(RETURN/'snes-mvp/saves/last-session.txt')
    assert f['build_version']=='1.12' and f['runs']=='1106' and f['phase']=='finished'
    assert f['held']=='0' and f['write_errors']=='1' and f['pcm_state']=='1'
    assert f['snapshot_load_successes']=='1' and f['pcm_error_detail'].startswith('SYNC_OBSERVE errno=77 state=1')
    assert int(f['resampled_enqueued_frames'])+int(f['priming_silence_frames'])==int(f['output_accepted_frames_including_priming'])+int(f['audio_remaining_frames'])
    delta=int(f['pcm_appl_ptr'])-int(f['pcm_epoch_transferred_frames']); assert delta==384
    previous=fields(RETURN/'snes-mvp/saves/last-session.txt.bak'); assert previous['build_version']=='1.11'
    assert not (RETURN/'snes-mvp/last-pcm-fault.txt').exists()
    assert (RETURN/'snes-mvp/last-run.log').stat().st_size==0
    progress=fields(RETURN/'snes-mvp/last-progress.txt'); assert progress['phase']=='wrapper_start'
    result={'version':'1.12','archive_verified':True,'exact_released_payload':True,'one_shot_consumed':True,
        'mvp_files':len(c['copied_and_hash_verified']),'lab_files':49,
        'prior_game_progress_files_unchanged':len(unchanged),'updated_sram_files_archived':len(changed),
        'updated_game_progress_paths':changed,'prior_snapshots_unchanged':True,'stock_binaries_unchanged':True,
        'final_report':{'runs':int(f['runs']),'active_calls_per_second':int(f['runs'])/(int(f['active_wall_ns'])/1e9),
            'mean_core_wall_ms':int(f['core_wall_ns'])/int(f['runs'])/1e6,
            'mean_core_cpu_ms':int(f['core_thread_cpu_ns'])/int(f['runs'])/1e6,
            'max_core_wall_ms':int(f['max_run_ns'])/1e6,'snapshot_load_successes':1,'pauses':1,
            'video_callbacks':int(f['video_submitted']),'held':0,'software_ring_high':int(f['software_ring_high_frames']),
            'accepted_frames':int(f['output_accepted_frames_including_priming']),
            'remaining_frames':int(f['audio_remaining_frames']),'epoch':int(f['pcm_epoch']),
            'admission_min_frames':int(f['pcm_admission_min_lead_frames']),
            'playable_min_frames':int(f['pcm_playable_min_running_frames']),
            'appl_minus_epoch_transferred':delta,'raw_pointer_difference':int(f['pcm_appl_ptr'])-int(f['pcm_hw_ptr']),
            'error_detail':f['pcm_error_detail']},
        'previous_report_identity':{'version':previous['build_version'],'runs':int(previous['runs']),'current_run':False},
        'fault_history_present':False,'stderr_bytes':0,'last_progress_phase':progress['phase'],
        'diagnostic_gap':'Final session persists, but RAM fault history and later periodic/final diagnostic copies do not survive this return. Exact loss mechanism unknown.',
        'kernel_capture_limit':'No retained READ_ALL result or transaction history; cannot infer whether RAM capture or kernel read succeeded.',
        'observation_limit':'SETUP has no playable PCM; raw gap 101 is not queued sound; average call rate is not smoothness or sustained audio proof.',
        'shutdown_limit':'Library READY and B exit with joined display cleanup recorded; final wrapper status absent.',
        'root_cause_limit':'Native stop and 384-frame discrepancy remain unexplained.',
        'next_build':'1.13 writes fault history directly to card, fsyncs file and directory before error return, and reports capture status; playback unchanged.'}
    (RETURN/'analysis.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    spec=importlib.util.spec_from_file_location('publisher',ROOT/'build/publish-snes-1.13.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();entries=json.loads(raw)['entries']
    assert not any(e['published'].startswith(PREFIX) for e in entries)
    for e in entries: assert digest(ROOT/e['published'])==e['published_sha256']
    selected={'analysis.json':RETURN/'analysis.json','session-prior-build-1.11.txt':RETURN/'snes-mvp/saves/last-session.txt.bak',
        'session-final.txt':RETURN/'snes-mvp/saves/last-session.txt'}
    for n in ('startup.log','last-run.log','last-progress.txt','last-progress.previous','runtime-platform.txt','runtime-platform-latest.txt','kernel-tail.txt','diagnostic-flush.log'):
        selected[n]=RETURN/'snes-mvp'/n
    added=[]
    for n,p in selected.items():
        data=p.read_bytes();out=data.decode('utf-8').replace(str(ROOT),'<workspace>').replace(ROOT.as_posix(),'<workspace>').replace('\r\n','\n').encode()
        target=ROOT/PREFIX/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(out)
        added.append({'source':p.relative_to(ROOT).as_posix(),'published':target.relative_to(ROOT).as_posix(),
            'source_sha256':sha256(data).hexdigest(),'published_sha256':sha256(out).hexdigest(),'bytes':len(out),'normalized':data!=out})
    manifest.write_bytes(mod.append_manifest(raw,added));print(json.dumps(result,indent=2))
if __name__=='__main__': publish()
