"""Verify and publish the consumed 1.16 return; exclude private game progress."""
from pathlib import Path
from hashlib import sha256
import json, importlib.util, statistics
ROOT=Path(__file__).resolve().parent.parent
RETURN=ROOT/'device-evidence/snes-mvp-return-20261006T125627Z'
PREFIX='evidence/2026-10-06/snes-mvp-1.16-return/'
def digest(p): return sha256(p.read_bytes()).hexdigest()
def fields(p): return dict(s.split('=',1) for s in p.read_text().splitlines() if '=' in s)
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'build'/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def publish():
    c=json.loads((RETURN/'collection.json').read_text())
    assert c['card_writes']==0 and not c['armed_present']
    for e in c['copied_and_hash_verified']: assert digest(RETURN/e['archive_path'])==e['sha256']
    lab=json.loads((RETURN/'lab-collection.json').read_text())
    assert not lab['lab_armed'] and len(lab['copied'])==49
    for e in lab['copied']: assert digest(RETURN/'platform-lab'/e['relative_path'])==e['sha256']
    release=json.loads((ROOT/'releases/snes-mvp-1.16/manifest.json').read_text())
    for n,k in [('snes-mvp','binary_sha256'),('launch.sh','wrapper_sha256'),('plus-a7.so','core_sha256')]:
        assert digest(RETURN/'snes-mvp'/n)==release[k]
    protected=json.loads((ROOT/'device-evidence/snes-mvp-1.16-install-20261006T062305Z/protected.json').read_text())
    unchanged=[];changed=[]
    for e in c['copied_and_hash_verified']:
        n=e['card_path']
        if n in protected and ('/saves/' in n or '/states/' in n) and not n.endswith(('.txt','.txt.bak')):
            (unchanged if e['sha256']==protected[n] else changed).append(n)
    assert all(n.endswith(('.srm','.srm.bak')) for n in changed),changed
    assert all(c['production_hashes'][n]==protected[n] for n in c['production_hashes'])
    original=RETURN/'snes-mvp/saves/game-a27f1c7a-3145728-core-5ba71d2a-656816.state'
    matched=RETURN/'snes-mvp/saves/game-a27f1c7a-3145728-core-4d245ba5-785504.state'
    assert original.read_bytes()[40:]==matched.read_bytes()[40:]
    first=fields(RETURN/'snes-mvp/saves/failure-493-9622671000-session.txt')
    good=fields(RETURN/'snes-mvp/saves/last-session.txt')
    assert first['build_version']==good['build_version']=='1.16'
    assert first['phase']==good['phase']=='finished'
    assert int(first['runs'])==70 and int(good['runs'])==31601
    assert first['write_errors']=='1' and good['write_errors']=='0'
    assert first['held']==good['held']==good['video_dupes']=='0'
    assert good['video_submitted']==good['runs']
    assert good['snapshot_load_successes']=='1' and good['snapshot_load_rejections']=='0'
    assert digest(RETURN/'snes-mvp/saves/failure-493-9622671000-pcm.txt')==digest(RETURN/'snes-mvp/last-pcm-fault.txt')
    for f in (first,good):
        assert int(f['resampled_enqueued_frames'])+int(f['priming_silence_frames'])==int(f['output_accepted_frames_including_priming'])+int(f['audio_remaining_frames'])
    assert int(first['pcm_appl_ptr'])-int(first['pcm_epoch_transferred_frames'])==384
    assert int(good['pcm_appl_ptr'])==int(good['pcm_epoch_transferred_frames'])
    rows=[list(map(int,v.split(','))) for k,v in first.items() if k.startswith('frame_cost_') and k.split('_')[-1].isdigit()]
    by_run={r[0]:r for r in rows}
    assert by_run[64][3]>38000000 and by_run[64][4]<10000000
    flush=(RETURN/'snes-mvp/diagnostic-flush.log').read_text()
    assert 'checkpoint=0 begin_uptime=11.27 end_after_copy_uptime=11.57 global_sync=0' in flush
    long=ROOT/'build/plus-a7-out/narshe-long-equivalence.log'
    assert 'PASS: 12000 frames exact visible pixels, native PCM' in long.read_text()
    trace=module('flight','analyze-pcm-flight.py').analyze(RETURN/'snes-mvp/last-pcm-fault.txt',44100)
    result={'version':'1.16','mvp_files':len(c['copied_and_hash_verified']),'lab_files':49,
        'read_only_archive_verified':True,'one_shots_consumed':True,'exact_release_verified':True,
        'prior_game_progress_files_unchanged':len(unchanged),'updated_sram_files_archived':len(changed),
        'snapshots_unchanged':True,'stock_hook_core_unchanged':True,
        'successful_session':{'runs':int(good['runs']),'active_seconds':int(good['active_wall_ns'])/1e9,
          'calls_per_active_second':int(good['runs'])*1e9/int(good['active_wall_ns']),
          'held_drawings':0,'duplicate_video_callbacks':0,'audio_write_errors':0,
          'snapshot_load_successes':1,'pauses':int(good['pauses']),
          'mean_core_wall_ms':int(good['core_wall_ns'])/int(good['runs'])/1e6,
          'mean_core_thread_cpu_ms':int(good['core_thread_cpu_ns'])/int(good['runs'])/1e6,
          'display_reservation_mean_ms':int(good['display_reserve_wait_ns'])/int(good['runs'])/1e6,
          'minimum_running_playable_frames':int(good['pcm_playable_min_running_frames'])},
        'first_failure':{'runs':70,'session_id':first['session_id'],'error':first['pcm_error_detail'],
          'selected_calls':[{'run':r[0],'wall_ms':r[3]/1e6,'cpu_ms':r[4]/1e6,
              'audio_callback_ms':r[7]/1e6,'video_callback_ms':r[8]/1e6} for r in rows if r[0]>=63],
          'diagnostic_checkpoint_begin_uptime_s':11.27,'diagnostic_checkpoint_end_uptime_s':11.57,
          'last_successful_pcm_observation_uptime_s':11.437640,
          'fault_uptime_s':11.470791,'flight_analysis':trace},
        'long_equivalence':{'frames':12000,'checks':'visible pixels, native PCM, geometry and periodic logical state match clean core',
          'coverage':'6000 boot/intro frames plus6000 returned-snapshot frames; scripted movement and menus',
          'limit':'Does not prove correctness of effects in the clean core or prove exact user scene was reached.'},
        'user_result':'Very playable; combat, party menu, game save and snapshot load succeeded. Wind sound and blowing snow both reported missing in opening outdoor Narshe gameplay. First launch failed with audio error; second worked.',
        'inference':'First-launch scheduling stalls overlap the wrapper first platform discovery/card-copy window exactly. Strong suspect, not proven causal. Core CPU remains around9ms while call64 wall time reaches38.7ms. Eliminate live diagnostics, preserving renderer/core/audio transport.',
        'limits':'Generated/submitted frames and accepted PCM do not prove physical scanout cadence or audible effect fidelity. The final physical scene is not a controlled replay of the earlier1.15 scene. Rare long core calls remain. Whole-device poweroff loses RAM-only progress.',
        'next_action':'1.17 moves routine discovery and card copies outside child lifetime; native fault/session reports remain durable. Continue separate effects investigation with private offline scene inspection.'}
    (RETURN/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();entries=json.loads(raw)['entries']
    assert not any(e['published'].startswith(PREFIX) for e in entries)
    for e in entries: assert digest(ROOT/e['published'])==e['published_sha256']
    selected={'analysis.json':RETURN/'analysis.json','session-first.txt':RETURN/'snes-mvp/saves/failure-493-9622671000-session.txt',
      'session-successful.txt':RETURN/'snes-mvp/saves/last-session.txt','long-equivalence.log':long}
    for n in ('last-pcm-fault.txt','startup.log','last-run.log','last-progress.txt','last-progress.previous',
              'runtime-platform.txt','runtime-platform-latest.txt','kernel-tail.txt','diagnostic-flush.log'):
        selected[n]=RETURN/'snes-mvp'/n
    additions=[]
    for n,p in selected.items():
        data=p.read_bytes();out=data.decode().replace(str(ROOT),'<workspace>').replace(ROOT.as_posix(),'<workspace>').replace('\r\n','\n').encode()
        for forbidden in (b'GITHUB_TOKEN',b'Bearer ',b'github_pat_',b'ghp_',b'C:\\Users',b'.codex/attachments'):assert forbidden not in out,(n,forbidden)
        target=ROOT/PREFIX/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(out)
        additions.append({'source':p.relative_to(ROOT).as_posix(),'published':target.relative_to(ROOT).as_posix(),
          'source_sha256':sha256(data).hexdigest(),'published_sha256':sha256(out).hexdigest(),'bytes':len(out),'normalized':data!=out})
    manifest.write_bytes(module('publisher','publish-snes-1.16.py').append_manifest(raw,additions))
    print(json.dumps(result,indent=2))
if __name__=='__main__':publish()
