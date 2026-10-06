"""Publish verified 1.13 failure evidence and budget review, never private progress."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json
ROOT=Path(__file__).resolve().parent.parent
RETURN=ROOT/'device-evidence/snes-mvp-return-20261006T050932Z'
PREFIX='evidence/2026-10-06/snes-mvp-1.13-return/'
def digest(p): return sha256(p.read_bytes()).hexdigest()
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'build'/file)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def fields(p):return dict(s.split('=',1) for s in p.read_text(encoding='utf-8').splitlines() if '=' in s)
def publish():
    c=json.loads((RETURN/'collection.json').read_text(encoding='utf-8'))
    assert c['card_writes']==0 and not c['armed_present']
    for e in c['copied_and_hash_verified']:assert digest(RETURN/e['archive_path'])==e['sha256']
    lab=json.loads((RETURN/'lab-collection.json').read_text(encoding='utf-8'))
    assert not lab['lab_armed'] and len(lab['copied'])==49
    for e in lab['copied']:assert digest(RETURN/'platform-lab'/e['relative_path'])==e['sha256']
    release=json.loads((ROOT/'releases/snes-mvp-1.13/manifest.json').read_text(encoding='utf-8'))
    for n,k in [('snes-mvp','binary_sha256'),('launch.sh','wrapper_sha256'),('plus-a7.so','core_sha256')]:
        assert digest(RETURN/'snes-mvp'/n)==release[k]
    protected=json.loads((ROOT/'device-evidence/snes-mvp-1.13-install-20261006T044239Z/protected.json').read_text(encoding='utf-8'))
    unchanged=[];changed=[]
    for e in c['copied_and_hash_verified']:
        n=e['card_path']
        if n in protected and ('/saves/' in n or '/states/' in n) and not n.endswith(('.txt','.txt.bak')):
            (unchanged if e['sha256']==protected[n] else changed).append(n)
    assert all(n.endswith(('.srm','.srm.bak')) for n in changed),changed
    assert all(c['production_hashes'][n]==protected[n] for n in c['production_hashes'])
    reports=[]
    for name,count in [('last-session.txt.bak',26),('last-session.txt',230)]:
        f=fields(RETURN/'snes-mvp/saves'/name)
        assert f['build_version']=='1.13' and int(f['runs'])==count and f['phase']=='finished'
        assert f['held']=='0' and f['write_errors']=='1' and f['pcm_state']=='1'
        assert f['pcm_error_detail'].startswith('SYNC_OBSERVE errno=77 state=1')
        assert 'trace_errno=0 trace_synced=1' in f['pcm_error_detail']
        assert int(f['resampled_enqueued_frames'])+int(f['priming_silence_frames'])==int(f['output_accepted_frames_including_priming'])+int(f['audio_remaining_frames'])
        assert int(f['pcm_appl_ptr'])-int(f['pcm_epoch_transferred_frames'])==384
        reports.append({'runs':count,'active_calls_per_second':count/(int(f['active_wall_ns'])/1e9),
            'mean_core_wall_ms':int(f['core_wall_ns'])/count/1e6,'mean_core_cpu_ms':int(f['core_thread_cpu_ns'])/count/1e6,
            'max_core_wall_ms':int(f['max_run_ns'])/1e6,'snapshot_load_successes':int(f['snapshot_load_successes']),
            'pauses':int(f['pauses']),'display_reserve_wait_ms':int(f['display_reserve_wait_ns'])/1e6,
            'software_high':int(f['software_ring_high_frames']),'partial_writes':int(f['short_writes']),
            'again':int(f['eagain_or_zero']),'error_detail':f['pcm_error_detail']})
    trace=module('flight','analyze-pcm-flight.py').analyze(RETURN/'snes-mvp/last-pcm-fault.txt',44100)
    assert trace['retained_operations']==96 and trace['epoch']==2
    assert [e['appl_minus_accepted'] for e in trace['application_pointer_difference_changes']]==[128,256,384]
    assert trace['accepted_pointer_difference_first_sample']==0 and trace['kernel_read_result']=={'bytes':16335,'errno':0}
    result={'version':'1.13','mvp_files':len(c['copied_and_hash_verified']),'lab_files':49,
        'read_only_archive_verified':True,'one_shots_consumed':True,'exact_release_verified':True,
        'prior_game_progress_files_unchanged':len(unchanged),'updated_sram_files_archived':len(changed),
        'updated_game_progress_paths':changed,'snapshots_unchanged':True,'stock_hook_core_unchanged':True,
        'reports':reports,'flight_analysis':trace,
        'capture_result':'Both final errors report file/directory sync success. Retained trace is the second fault; retry replaced first history.',
        'inference':'Repeated production shortfall drains reserve before period-sized application-pointer changes and SETUP; starvation is the leading trigger.',
        'unresolved':'Exact vendor pointer mutation/stop path, sound contents during divergence, per-subsystem and per-phase CPU costs, previous whole-device poweroffs.',
        'physical_crash_boundary':'Logs show two controlled audio failures, retry, successful snapshot and library cleanup; user says crashed again; no new poweroff independently established.',
        'next_action':'Review and correct whole execution budget; no new executable installation, card writes or re-arm in this review.'}
    (RETURN/'analysis.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();entries=json.loads(raw)['entries']
    assert not any(e['published'].startswith(PREFIX) for e in entries)
    for e in entries:assert digest(ROOT/e['published'])==e['published_sha256']
    selected={'analysis.json':RETURN/'analysis.json','session-first.txt':RETURN/'snes-mvp/saves/last-session.txt.bak',
        'session-final.txt':RETURN/'snes-mvp/saves/last-session.txt'}
    for n in ('last-pcm-fault.txt','startup.log','last-run.log','last-progress.txt','last-progress.previous',
              'runtime-platform.txt','runtime-platform-latest.txt','kernel-tail.txt','diagnostic-flush.log'):
        selected[n]=RETURN/'snes-mvp'/n
    additions=[]
    for n,p in selected.items():
        data=p.read_bytes();out=data.decode('utf-8').replace(str(ROOT),'<workspace>').replace(ROOT.as_posix(),'<workspace>').replace('\r\n','\n').encode()
        for forbidden in (b'GITHUB_TOKEN',b'Bearer ',b'github_pat_',b'ghp_',b'C:\\Users',b'.codex/attachments'):assert forbidden not in out,(n,forbidden)
        target=ROOT/PREFIX/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(out)
        additions.append({'source':p.relative_to(ROOT).as_posix(),'published':target.relative_to(ROOT).as_posix(),
            'source_sha256':sha256(data).hexdigest(),'published_sha256':sha256(out).hexdigest(),'bytes':len(out),'normalized':data!=out})
    manifest.write_bytes(module('publisher','publish-snes-1.13.py').append_manifest(raw,additions))
    print(json.dumps(result,indent=2))
if __name__=='__main__':publish()
