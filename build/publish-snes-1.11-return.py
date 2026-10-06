"""Publish the consumed 1.11 failure return; never publish game progress."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,re
ROOT=Path(__file__).resolve().parent.parent
RETURN=ROOT/'device-evidence/snes-mvp-return-20261006T040033Z'
PREFIX='evidence/2026-10-05/snes-mvp-1.11-return/'
def digest(p): return sha256(p.read_bytes()).hexdigest()
def fields(p): return dict(s.split('=',1) for s in p.read_text(encoding='utf-8').splitlines() if '=' in s)
def publish():
    c=json.loads((RETURN/'collection.json').read_text(encoding='utf-8'))
    assert not c['armed_present'] and c['card_writes']==0
    for e in c['copied_and_hash_verified']: assert digest(RETURN/e['archive_path'])==e['sha256']
    lab=json.loads((RETURN/'lab-collection.json').read_text(encoding='utf-8'))
    assert not lab['lab_armed'] and len(lab['copied'])==49
    for e in lab['copied']: assert digest(RETURN/'platform-lab'/e['relative_path'])==e['sha256']
    release=json.loads((ROOT/'releases/snes-mvp-1.11/manifest.json').read_text(encoding='utf-8'))
    for n,k in [('snes-mvp','binary_sha256'),('launch.sh','wrapper_sha256'),('plus-a7.so','core_sha256')]:
        assert digest(RETURN/'snes-mvp'/n)==release[k]
    protected=json.loads((ROOT/'device-evidence/snes-mvp-1.11-install-20261005T190929Z/protected.json').read_text(encoding='utf-8'))
    unchanged=[];changed=[]
    for e in c['copied_and_hash_verified']:
        n=e['card_path']
        if n in protected and ('/saves/' in n or '/states/' in n) and not n.endswith(('.txt','.txt.bak')):
            (unchanged if e['sha256']==protected[n] else changed).append(n)
    assert all(n.endswith(('.srm','.srm.bak')) for n in changed),changed
    assert all(c['production_hashes'][n]==protected[n] for n in c['production_hashes'])
    reports=[]
    for name,count in [('last-session.txt.bak',2195),('last-session.txt',253)]:
        f=fields(RETURN/'snes-mvp/saves'/name)
        assert f['build_version']=='1.11' and int(f['runs'])==count and f['phase']=='finished'
        assert f['held']=='0' and f['write_errors']=='1' and f['pcm_state']=='1'
        assert f['pcm_error_detail'].startswith('SYNC_OBSERVE errno=77 state=1')
        assert int(f['resampled_enqueued_frames'])+int(f['priming_silence_frames'])==int(f['output_accepted_frames_including_priming'])+int(f['audio_remaining_frames'])
        delta=int(f['pcm_appl_ptr'])-int(f['pcm_epoch_transferred_frames'])
        assert delta==384
        reports.append({'runs':count,'active_calls_per_second':count/(int(f['active_wall_ns'])/1e9),
            'mean_core_wall_ms':int(f['core_wall_ns'])/count/1e6,'mean_core_cpu_ms':int(f['core_thread_cpu_ns'])/count/1e6,
            'max_core_wall_ms':int(f['max_run_ns'])/1e6,'pauses':int(f['pauses']),
            'snapshot_load_successes':int(f['snapshot_load_successes']),
            'admission_min_frames':int(f['pcm_admission_min_lead_frames']),
            'playable_min_frames':int(f['pcm_playable_min_running_frames']),
            'accepted_frames':int(f['output_accepted_frames_including_priming']),
            'remaining_frames':int(f['audio_remaining_frames']),
            'epoch':int(f['pcm_epoch']),'appl_minus_epoch_transferred':delta,
            'raw_pointer_difference':int(f['pcm_appl_ptr'])-int(f['pcm_hw_ptr']),
            'error_detail':f['pcm_error_detail']})
    stderr=(RETURN/'snes-mvp/last-run.log').read_text(encoding='utf-8')
    initial=re.search(r'SYNC_OBSERVE errno=77 state=1.*appl=(\d+) hw=(\d+).*xfer=(\d+)',stderr)
    assert initial and int(initial[1])-int(initial[3])==384
    result={'version':'1.11','archive_verified':True,'exact_released_payload':True,'one_shot_consumed':True,
        'mvp_files':len(c['copied_and_hash_verified']),'lab_files':49,
        'prior_game_progress_files_unchanged':len(unchanged),'updated_sram_files_archived':len(changed),
        'updated_game_progress_paths':changed,
        'prior_snapshots_unchanged':True,'stock_binaries_unchanged':True,'final_reports':reports,
        'earlier_stderr_fault':{'operation':'SYNC_OBSERVE','errno':77,'state':1,
            'appl_minus_epoch_transferred':384,'raw_pointer_difference':int(initial[1])-int(initial[2])},
        'snapshot_result':'final report explicitly proves one successful snapshot load and re-primed resume before failure',
        'observation_limit':'SETUP has no playable PCM; raw pointer gaps 92/107/101 are not valid queued sound in SETUP',
        'drawing_limit':'zero intentional holds; each final fatal report lacks one final video callback',
        'shutdown_limit':'user confirms audio error/our library; application records display join/FreeVFB; final wrapper status absent; no whole-device poweroff reported',
        'root_cause_limit':'stream stops and pointer/count discrepancy observed; no transaction history or kernel ring explains why',
        'next_build':'1.12 adds bounded RAM PCM history and read-only SYS_syslog READ_ALL on fault; no claimed driver fix'}
    (RETURN/'analysis.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    spec=importlib.util.spec_from_file_location('publisher',ROOT/'build/publish-snes-1.12.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();entries=json.loads(raw)['entries']
    assert not any(e['published'].startswith(PREFIX) for e in entries)
    for e in entries: assert digest(ROOT/e['published'])==e['published_sha256']
    selected={'analysis.json':RETURN/'analysis.json','session-previous.txt':RETURN/'snes-mvp/saves/last-session.txt.bak',
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
