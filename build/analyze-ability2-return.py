"""Analyze an immutable returned archive; no card access and no emulation runs."""
from pathlib import Path
from hashlib import sha256
import csv,json,math,statistics,sys
ROOT=Path(__file__).resolve().parent.parent
BUDGET_MS=16.6881545
def digest(p):return sha256(p.read_bytes()).hexdigest()
def kv(p):return dict(x.split('=',1) for x in p.read_text().splitlines() if '=' in x) if p.exists() else {}
def csv_rows(p):return list(csv.DictReader(x for x in p.read_text().splitlines() if not x.startswith('#'))) if p.exists() else []
def dist(v):
    if not v:return None
    v=sorted(v);at=lambda q:v[max(0,math.ceil(len(v)*q)-1)]
    return {'count':len(v),'mean':statistics.mean(v),'median':statistics.median(v),'p95':at(.95),'p99':at(.99),'max':v[-1]}
def analyze(archive):
    archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
    a=json.loads((archive/'archive.json').read_text());assert a['fat_clean'] and not a['card_writes']
    for e in a['all_retro_files']:
        p=archive/e['path'];assert p.stat().st_size==e['bytes'] and digest(p)==e['sha256'],e['path']
    base=archive/'retro/snes-ability2';q=json.loads((base/'suite-identity.json').read_text());plan=json.loads((base/'plan.json').read_text())
    before=ROOT/'device-evidence'/q['archive'];install=json.loads((before/'ability2-installation.json').read_text())
    for n,h in install['payload_hashes'].items():assert digest(base/n)==h,n
    assert digest(archive/'retro/snes-mvp/launch.sh')==install['dispatch_sha256']
    assert not list((archive/'retro').rglob('armed')) and (base/'last-launch').is_file()
    unchanged=[];changed=[]
    for e in json.loads((before/'archive.json').read_text())['all_retro_files']:
        if e['path']=='retro/snes-mvp/launch.sh':continue
        p=archive/e['path'];(unchanged if p.is_file() and digest(p)==e['sha256'] else changed).append(e['path'])
    assert not [p for p in changed if p!='retro/swapfile'],changed
    output=archive/'ability-analysis';assert not output.exists();output.mkdir()
    results=[];all_cpu=[];all_wall=[];all_observer=[];all_animation_observer=[];failures=[];anomalies=[]
    total_runs=total_videos=total_native=total_converted=total_accepted=0;elapsed=active=0;freq=set();pin=set();families={}
    for c in plan['cases']:
        seq=c['seq'];d=base/f'run-{seq:03d}';result=kv(d/'result.txt');session=kv(d/'last-session.txt');frames=csv_rows(d/'frames.csv');anim=csv_rows(d/'animation.csv')
        if not d.exists():results.append({'case':seq,'name':c['name'],'family':c['family'],'status':'not_started'});continue
        runs=int(session.get('runs',len(frames)));rc=result.get('runner_rc');error=session.get('error','') or result.get('error','')
        status='runtime_failed' if rc not in (None,'0') or error else 'incomplete' if rc is None or runs<1200 or len(frames)!=1200 or len(anim)!=1200 else 'bounded_run_completed'
        if status!='bounded_run_completed':failures.append({'case':seq,'name':c['name'],'status':status,'calls':runs,'error':error})
        if session:
            assert session['mock_backend']=='0' and session['core_crc32']=='4eef8dba' and session['build_version']=='1.19-ability2'
            for field in ['held','video_dupes','write_errors','xrun_count','snapshot_load_rejections']:
                if int(session.get(field,0)):anomalies.append({'case':seq,'field':field,'value':session[field]})
        header=kv(d/'frames.csv');pin.add(header.get('#pin','missing'))
        for f in frames:
            freq.update(int(f[k]) for k in ['freq_before_khz','freq_after_khz'] if int(f[k])>0)
        cpu=[int(f['cpu_ns'])/1e6 for f in frames];wall=[int(f['wall_ns'])/1e6 for f in frames];step=[int(f['step_ns'])/1e6 for f in frames]
        observer=[int(f['observer_ns'])/1000 for f in frames];ao=[int(r['observer_ns'])/1000 for r in anim]
        all_cpu+=cpu;all_wall+=wall;all_observer+=observer;all_animation_observer+=ao
        expected=(base/f'cases/{seq:03d}/expected.bin').read_bytes();expected_pairs={(f'{expected[1+i*15]:02x}',expected[2+i*15:16+i*15].hex()) for i in range(expected[0])}
        matched=[i for i,r in enumerate(anim) if (r['attack'],r['properties']) in expected_pairs]
        first=matched[0] if matched else None;last=matched[-1] if matched else None
        changed_after_first=first is not None and any((r['attack'],r['properties'])!=(anim[first]['attack'],anim[first]['properties']) for r in anim[first+1:])
        rage_ids=sorted({int(r[k],16) for r in anim for k in ['rage_terra','rage_wedge','rage_vicks'] if r[k]!='ff'})
        dance_ids=sorted({int(r[k],16) for r in anim for k in ['dance_terra','dance_wedge','dance_vicks'] if r[k]!='ff'})
        selection_ok=(c['original_case']-145 in rage_ids) if c['family']=='rage' else (c['original_case']-137 in dance_ids) if c['family']=='dance' else None
        if selection_ok is False:anomalies.append({'case':seq,'field':'selected_command_not_observed','rage_ids':rage_ids,'dance_ids':dance_ids})
        reserve=[int(f['playable']) for f in frames if int(f['state'])==3]
        bias=sorted({int(f['appl'])-int(f['xfer']) for f in frames if int(f['state'])==3})
        active_ns=int(session.get('active_wall_ns',0));count=int(session.get('runs',0));videos=int(session.get('video_submitted',0))
        native=int(session.get('native_audio_frames',0));converted=int(session.get('resampled_enqueued_frames',0));accepted=int(session.get('output_accepted_frames_including_priming',0))-int(session.get('priming_silence_frames',0))
        if accepted+int(session.get('audio_remaining_frames',0))+int(session.get('audio_cleared_frames',0))!=converted:anomalies.append({'case':seq,'field':'PCM_accounting'})
        if videos!=count:anomalies.append({'case':seq,'field':'draw_count','calls':count,'videos':videos})
        total_runs+=count;total_videos+=videos;total_native+=native;total_converted+=converted;total_accepted+=accepted;active+=active_ns;elapsed+=int(session.get('session_elapsed_ns',0))
        item={'case':seq,'name':c['name'],'family':c['family'],'status':status,'calls':runs,'error':error,
            'requested_property_samples':len(matched),'first_requested_property_frame':first,'last_requested_property_frame':last,
            'subsequent_property_change_observed':changed_after_first,'animation_completion_proven':False,
            'random_or_conditional':c['random_or_conditional'],'rage_ids':rage_ids,'dance_ids':dance_ids,'selection_observed':selection_ok,
            'cpu_ms':dist(cpu),'wall_ms':dist(wall),'step_ms':dist(step),'frequency_observer_us':dist(observer),'animation_observer_us':dist(ao),
            'core_wall_over_budget_calls':sum(v>BUDGET_MS for v in wall),'core_cpu_over_budget_calls':sum(v>BUDGET_MS for v in cpu),
            'reported_running_reserve_min_frames':min(reserve) if reserve else None,'running_pointer_bias_frames':bias,
            'active_calls_per_second':count*1e9/active_ns if active_ns else None,'native_quota_percent':100*native/(count*534.688) if count else None,
            'native_frames':native,'converted_frames':converted,'accepted_minus_prime':accepted}
        results.append(item);families.setdefault(c['family'],[]).append(item)
    summary={'archive':archive.name,'card_writes':0,'fat_clean':True,'archived_files_verified':len(a['all_retro_files']),
        'exact_installed_payload_verified':len(install['payload_hashes']),'marker_consumed':True,'protected_files_unchanged':len(unchanged),'changed_prior_files':changed,
        'cases_started':sum(r['status']!='not_started' for r in results),'bounded_cases_completed':sum(r['status']=='bounded_run_completed' for r in results),
        'runtime_failed_cases':failures,'accounting_or_selection_anomalies':anomalies,'calls':total_runs,'video_submitted':total_videos,
        'native_frames':total_native,'converted_frames':total_converted,'accepted_minus_prime':total_accepted,
        'active_seconds':active/1e9,'summed_session_seconds_excluding_between_case_flushes':elapsed/1e9,
        'active_calls_per_second':total_runs*1e9/active if active else None,'native_quota_percent':100*total_native/(total_runs*534.688) if total_runs else None,
        'frequency_khz_observed':sorted(freq),'frequency_pin_reports':sorted(pin),'core_cpu_ms':dist(all_cpu),'core_wall_ms':dist(all_wall),
        'frequency_observer_us':dist(all_observer),'animation_observer_us':dist(all_animation_observer),
        'cases_requested_properties_observed':sum(r.get('requested_property_samples',0)>0 for r in results),
        'cases_requested_properties_not_observed':[{'case':r['case'],'name':r['name'],'family':r['family'],'random_or_conditional':r.get('random_or_conditional')} for r in results if r['status']!='not_started' and not r.get('requested_property_samples')],
        'production_gate_passed':False,'animation_completion_proven':False,'limits':['Frame-boundary cached properties are not complete animation-thread proof.','One seeded Dance/Rage outcome does not cover every possible branch.','Whole-core timings do not price renderer e/r/b or identify PPU subphases.','Observed timing includes instrumentation; no calibration subtraction.']}
    summary['family_summary']={k:{'started':len(v),'bounded_completed':sum(r['status']=='bounded_run_completed' for r in v),'requested_properties_observed':sum(r['requested_property_samples']>0 for r in v),'mean_core_cpu_ms':statistics.mean(r['cpu_ms']['mean'] for r in v if r['cpu_ms'])} for k,v in families.items()}
    (output/'cases.json').write_text(json.dumps(results,indent=2)+'\n');(output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    with (output/'cases.csv').open('w',newline='') as f:
        fields=['case','name','family','status','calls','requested_property_samples','selection_observed','active_calls_per_second','reported_running_reserve_min_frames','core_wall_over_budget_calls','core_cpu_over_budget_calls']
        w=csv.DictWriter(f,fields,extrasaction='ignore');w.writeheader();w.writerows(results)
    print(json.dumps({k:v for k,v in summary.items() if k not in ('cases_requested_properties_not_observed','accounting_or_selection_anomalies')},indent=2))
if __name__=='__main__':analyze(Path(sys.argv[1]))
