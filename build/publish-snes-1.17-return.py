"""Publish the verified consumed 1.17 return and Magitek scene work counts only."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,statistics
ROOT=Path(__file__).resolve().parent.parent
RETURN=ROOT/'device-evidence/snes-mvp-return-20261009T020104Z'
PREFIX='evidence/2026-10-08/snes-mvp-1.17-return/'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def fields(p):return dict(s.split('=',1) for s in p.read_text(encoding='utf-8').splitlines() if '=' in s)
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'build'/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def publish():
    collection=json.loads((RETURN/'collection.json').read_text(encoding='utf-8'))
    assert collection['card_writes']==0 and not collection['armed_present']
    for e in collection['copied_and_hash_verified']:assert digest(RETURN/e['archive_path'])==e['sha256']
    lab=json.loads((RETURN/'lab-collection.json').read_text(encoding='utf-8'))
    assert not lab['lab_armed'] and len(lab['copied'])==49
    for e in lab['copied']:assert digest(RETURN/'platform-lab'/e['relative_path'])==e['sha256']
    release=json.loads((ROOT/'releases/snes-mvp-1.17/manifest.json').read_text(encoding='utf-8'))
    for name,key in [('snes-mvp','binary_sha256'),('plus-a7.so','core_sha256'),('launch.sh','wrapper_sha256')]:
        assert digest(RETURN/'snes-mvp'/name)==release[key]
    protected=json.loads((ROOT/'device-evidence/snes-mvp-1.17-install-20261006T132116Z/protected.json').read_text(encoding='utf-8'))
    assert all(collection['production_hashes'][n]==protected[n] for n in collection['production_hashes'])
    changed=[];unchanged=[]
    for e in collection['copied_and_hash_verified']:
        n=e['card_path']
        if n in protected and ('/saves/' in n or '/states/' in n) and not n.endswith(('.txt','.txt.bak')):
            (unchanged if e['sha256']==protected[n] else changed).append(n)
    assert len(changed)==1 and changed[0].endswith('.srm')
    session=RETURN/'snes-mvp/saves/failure-502-19082405000-session.txt';f=fields(session)
    assert f['build_version']=='1.17' and f['runs']=='35763' and f['write_errors']=='1'
    latest=fields(RETURN/'snes-mvp/saves/last-session.txt')
    # Unique failure persistence follows the final report by a few milliseconds.
    assert {k:v for k,v in f.items() if k not in ('session_elapsed_ns','checkpoint_kernel_ns')}=={
        k:v for k,v in latest.items() if k not in ('session_elapsed_ns','checkpoint_kernel_ns')}
    assert f['held']==f['video_dupes']=='0' and f['video_submitted']=='35762'
    assert int(f['resampled_enqueued_frames'])+int(f['priming_silence_frames'])==int(f['output_accepted_frames_including_priming'])+int(f['audio_remaining_frames'])
    assert f['audio_cleared_frames']=='0' and int(f['pcm_appl_ptr'])-int(f['pcm_epoch_transferred_frames'])==384
    rows=[list(map(int,v.split(','))) for k,v in f.items() if k.startswith('frame_cost_') and k.split('_')[-1].isdigit()]
    ordinary=[x for x in rows if not x[2] and x[0]<35763]
    sampled=next(x for x in rows if x[0]==35747)
    flight=module('flight','analyze-pcm-flight.py').analyze(RETURN/'snes-mvp/saves/failure-502-19082405000-pcm.txt',44100)
    assert fields(RETURN/'snes-mvp/saves/last-session.txt.bak')['build_version']=='1.16'
    assert digest(RETURN/'snes-mvp/last-run.log')==digest(ROOT/'device-evidence/snes-mvp-return-20261006T125627Z/snes-mvp/last-run.log')
    startup=(RETURN/'snes-mvp/startup.log').read_text(encoding='utf-8')
    assert startup.count('library game launch requested')==1
    data={'version':'1.17','archive_utc':'2026-10-09T02:01:04Z','local_date':'2026-10-08 America/Chicago',
      'mvp_files_verified':len(collection['copied_and_hash_verified']),'lab_files_verified':49,'card_writes':0,
      'stock_and_installed_release_verified':True,'snapshots_unchanged':True,
      'unchanged_game_progress_files':len(unchanged),'updated_sram_files_archived':len(changed),
      'user_result':{'first_launch':'succeeded on first attempt','crash':'audio error and return to our library',
        'specific_move':'Terra Magitek armor Bio Blast; not Edgar Tools Bio Blaster',
        'snow_correction':'User checked playthroughs and retracted expected driving snow in that outdoor Narshe section; no demonstrated snow regression'},
      'session':{'id':f['session_id'],'runs':35763,'active_seconds':int(f['active_wall_ns'])/1e9,
        'calls_per_active_second':35763*1e9/int(f['active_wall_ns']),'submitted_videos':35762,
        'held':0,'duplicates':0,'snapshot_loads':int(f['snapshot_load_successes']),
        'audio_write_errors':1,'remaining_frames':int(f['audio_remaining_frames']),
        'display_reservation_mean_ms':int(f['display_reserve_wait_ns'])/35763/1e6,
        'mean_core_cpu_ms':int(f['core_thread_cpu_ns'])/35763/1e6,
        'mean_core_wall_ms':int(f['core_wall_ns'])/35763/1e6},
      'final_effect_window':{'ordinary_calls':len(ordinary),'ordinary_wall_mean_ms':statistics.mean(x[3] for x in ordinary)/1e6,
        'ordinary_cpu_mean_ms':statistics.mean(x[4] for x in ordinary)/1e6,
        'sampled_run':sampled[0],'sampled_ppu_inclusive_ms':sampled[6]/1e6,'sampled_apu_inclusive_ms':sampled[5]/1e6,
        'sampling_limit':'Inclusive sampled regions include their instrumentation; one sample is not a duration distribution.'},
      'pcm_flight':flight,
      'inference':'Effect increases renderer work; native PCM reserve erodes before application pointer diverges in 128-frame steps and SETUP/EBADFD. Transient production deficit, not a core segfault, display FIFO overflow, or evidence all gameplay is too slow.',
      'capture_limits':'Fresh unique native session/fault and startup logs identify 1.17. last-run.log and last-session.txt.bak are historical 1.16. No completed wrapper-exit diagnostic copy; its absence does not prove a power-off mechanism.',
      'next_build':'1.18 bounded pre-math RGB tile cache; exact output checks and offline work counts required before device test.'}
    private_analysis=RETURN/'analysis.json';private_analysis.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    rs={k:[list(map(int,l.split()[2:])) for l in (ROOT/'build'/f'magitek-{k}-census-private/census.txt').read_text(encoding='utf-8').splitlines()] for k in ('original','cache')}
    assert len(rs['original'])==len(rs['cache'])==1200
    assert all(a[:46]==b[:46] and a[48:]==b[48:] for a,b in zip(rs['original'],rs['cache']))
    effect=[i for i,a in enumerate(rs['original']) if i>200 and a[0]>=80]
    misses=sum(rs['cache'][i][46] for i in effect);hits=sum(rs['cache'][i][47] for i in effect)
    lookups=sum(rs['original'][i][40]-rs['original'][i][41] for i in effect)
    peak=max(effect,key=lambda i:rs['original'][i][0])
    work={'frames':1200,'effect_frames_with_at_least_80_raster_updates':len(effect),'effect_frame_indices':[min(effect),max(effect)],
      'color_tile_materializations':misses,'color_tile_reuses':hits,'reuse_fraction':hits/(hits+misses),
      'original_active_palette_lookup_rows':lookups,'candidate_materialized_palette_lookup_rows':misses*8,
      'palette_lookup_row_reduction_fraction':1-misses*8/lookups,
      'peak':{'frame_index':peak,'raster_updates':rs['original'][peak][0],
        'neon_tile_rows':rs['original'][peak][40],'color_tile_materializations':rs['cache'][peak][46],
        'color_tile_reuses':rs['cache'][peak][47]},
      'all_prior_126_work_counters_identical':True,'cache_bytes_including_tags':36864,
      'primary_game_reference':{'repository':'https://github.com/everything8215/ff6','commit':'813013276c952fdd27edcf7b8b86f17291542cbf',
        'script':'src/btlgfx/attack_anim_script.asm BIO_BLAST_BG1; attack134 in src/data/attack_anim_prop.asm'},
      'private_fixture':'Owner Narshe snapshot, private forced formation0/grass battle, real Terra Magitek menu and Bio Blast targeting. No attack script/ROM/core timing edits; not the exact physical battle background.',
      'limits':'Dynamic work counts and exact output equality, not Cortex-A7 runtime timings or physical audio/scanout proof.'}
    census_analysis=ROOT/'build/magitek-cache-census-private/analysis.json'
    census_analysis.write_text(json.dumps(work,indent=2)+'\n',encoding='utf-8')
    selected={'analysis.json':private_analysis,'session-failure.txt':session,
      'magitek-work-counts.json':census_analysis,'magitek-equivalence.log':ROOT/'build/plus-a7-out/magitek-bio-equivalence.log'}
    for name in ('last-pcm-fault.txt','startup.log','last-run.log','last-progress.txt','diagnostic-flush.log'):
        selected[name]=RETURN/'snes-mvp'/name
    publisher=module('publisher','publish-snes-1.18.py');manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes()
    entries=json.loads(raw)['entries'];assert not any(e['published'].startswith(PREFIX) for e in entries)
    for e in entries:assert digest(ROOT/e['published'])==e['published_sha256']
    additions=[]
    for name,source in selected.items():
        original=source.read_bytes();output=publisher.public_text(original)
        for forbidden in (b'GITHUB_TOKEN',b'Bearer ',b'github_pat_',b'ghp_',b'C:\\Users',b'.codex/attachments'):
            assert forbidden not in output,(name,forbidden)
        target=ROOT/PREFIX/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(output)
        additions.append({'source':source.relative_to(ROOT).as_posix(),'published':target.relative_to(ROOT).as_posix(),
          'source_sha256':sha256(original).hexdigest(),'published_sha256':sha256(output).hexdigest(),'bytes':len(output),'normalized':original!=output})
    manifest.write_bytes(publisher.append_manifest(raw,additions))
    print(json.dumps({'return_published_files':len(selected),'first_launch_succeeded':True,'work_counts':work},indent=2))
if __name__=='__main__':publish()
