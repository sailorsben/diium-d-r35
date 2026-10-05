"""Publish selected native PCM failure evidence; keep all private progress local."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json
ROOT=Path(__file__).resolve().parent.parent
RETURN=ROOT/'device-evidence/snes-mvp-return-20261005T183649Z'
PREFIX='evidence/2026-10-05/snes-mvp-1.10-return/'
def digest(p): return sha256(p.read_bytes()).hexdigest()
def fields(p): return dict(s.split('=',1) for s in p.read_text(encoding='utf-8').splitlines() if '=' in s)
def publish():
    c=json.loads((RETURN/'collection.json').read_text(encoding='utf-8'))
    assert not c['armed_present'] and c['card_writes']==0
    for e in c['copied_and_hash_verified']: assert digest(RETURN/e['archive_path'])==e['sha256']
    lab=json.loads((RETURN/'lab-collection.json').read_text(encoding='utf-8'))
    assert not lab['lab_armed'] and len(lab['copied'])==49
    for e in lab['copied']: assert digest(RETURN/'platform-lab'/e['relative_path'])==e['sha256']
    release=json.loads((ROOT/'releases/snes-mvp-1.10/manifest.json').read_text(encoding='utf-8'))
    for n,k in [('snes-mvp','binary_sha256'),('launch.sh','wrapper_sha256'),('plus-a7.so','core_sha256')]:
        assert digest(RETURN/'snes-mvp'/n)==release[k]
    previous=json.loads((ROOT/'device-evidence/snes-mvp-1.10-install-20261005T134606Z/protected.json').read_text(encoding='utf-8'))
    same=0; changed=[]
    for e in c['copied_and_hash_verified']:
        n=e['card_path']
        if n in previous and ('/saves/' in n or '/states/' in n) and not n.endswith(('.txt','.txt.bak')):
            if e['sha256']==previous[n]: same+=1
            else: changed.append(n)
    assert same==19 and changed==['retro/snes-mvp/saves/game-a27f1c7a-3145728.srm']
    assert all(c['production_hashes'][n]==previous[n] for n in c['production_hashes'])
    first=fields(RETURN/'snes-mvp/saves/last-session.txt.bak');last=fields(RETURN/'snes-mvp/saves/last-session.txt')
    for f,count in [(first,72),(last,605)]:
        assert f['build_version']=='1.10' and int(f['runs'])==count and f['phase']=='finished'
        assert f['core_crc32']==release['core_crc32'] and f['sink_rate']=='44100'
        assert f['held']=='0' and f['write_errors']=='1' and f['software_ring_high_frames']=='2823'
        assert f['pcm_error_detail'].startswith('WRITEI_FRAMES errno=77')
        assert int(f['resampled_enqueued_frames'])+int(f['priming_silence_frames'])==int(f['output_accepted_frames_including_priming'])+int(f['audio_remaining_frames'])
    result={'version':'1.10','exact_released_payload':True,'archive_verified':True,'one_shot_consumed':True,
        'mvp_files':len(c['copied_and_hash_verified']),'lab_files':49,
        'prior_game_progress_files_unchanged':same,'updated_sram_files_archived':len(changed),
        'all_prior_snapshots_unchanged':True,'stock_binaries_unchanged':True,
        'first_runs':72,'second_runs':605,'second_pauses':1,'second_priming_frames':5646,
        'software_ring_capacity':8192,'both_software_high_frames':2823,'both_remaining_frames':705,
        'actual_error_operation':'WRITEI_FRAMES','errno':77,'queue_overflow_label':'incorrect for worker errors',
        'last_observation_boundary':'first SETUP and second RUNNING are pre-failed-write samples, not post-fault states',
        'first_active_calls_per_second':72/(int(first['active_wall_ns'])/1e9),
        'second_active_calls_per_second':605/(int(last['active_wall_ns'])/1e9),
        'second_mean_core_wall_ms':int(last['core_wall_ns'])/605/1e6,
        'second_mean_core_cpu_ms':int(last['core_thread_cpu_ns'])/605/1e6,
        'drawing_limit':'zero intentional holds; final fatal callbacks prevent one video publication per attempt',
        'snapshot_load_success':'not explicitly retained by1.10; second report proves one pause and re-priming',
        'shutdown':'normal wrapper status255 after library B exit and joined display cleanup; no new whole-device poweroff evidence',
        'kernel_capture':'dmesg absent; no kernel-ring evidence',
        'root_cause_boundary':'stale admission reproduced in shipped source; exact vendor transition and long-game stability remain unproved'}
    (RETURN/'analysis.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    spec=importlib.util.spec_from_file_location('publisher',ROOT/'build/publish-snes-1.11.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();entries=json.loads(raw)['entries']
    assert not any(e['published'].startswith(PREFIX) for e in entries)
    for e in entries: assert digest(ROOT/e['published'])==e['published_sha256']
    selected={'analysis.json':RETURN/'analysis.json','session-first.txt':RETURN/'snes-mvp/saves/last-session.txt.bak',
        'session-final.txt':RETURN/'snes-mvp/saves/last-session.txt'}
    for n in ('startup.log','last-run.log','last-progress.txt','last-progress.previous','runtime-platform.txt','kernel-tail.txt','diagnostic-flush.log'):
        selected[n]=RETURN/'snes-mvp'/n
    added=[]
    for n,p in selected.items():
        data=p.read_bytes();out=data.decode().replace(str(ROOT),'<workspace>').replace(ROOT.as_posix(),'<workspace>').replace('\r\n','\n').encode()
        target=ROOT/PREFIX/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(out)
        added.append({'source':p.relative_to(ROOT).as_posix(),'published':target.relative_to(ROOT).as_posix(),
            'source_sha256':sha256(data).hexdigest(),'published_sha256':sha256(out).hexdigest(),'bytes':len(out),'normalized':data!=out})
    manifest.write_bytes(mod.append_manifest(raw,added)); print(json.dumps(result,indent=2))
if __name__=='__main__': publish()
