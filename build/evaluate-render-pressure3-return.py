"""Price physical budget and burst recovery, censoring invalid PCM histories."""
from pathlib import Path
from hashlib import sha256
import csv, importlib.util, json, re, statistics, sys

ROOT = Path(__file__).resolve().parent.parent
PERIOD_NS = 16688153
RECORD = re.compile(r'seq=(\d+) ns=(\d+) op=(\S+) arg=(\d+) result=(-?\d+) state=(\d+) queued=(\d+) appl=(\d+) hw=(\d+) epoch=(\d+) xfer=(\d+)')

def digest(p): return sha256(p.read_bytes()).hexdigest()
def kv(p): return dict(x.split('=',1) for x in p.read_text().splitlines() if '=' in x)
def fields(text): return dict(re.findall(r'(\w+)=([^\s]+)', text))
def metric(rows):
    return {k: {'median_ms': statistics.median(int(x[k]) for x in rows)/1e6,
                'maximum_ms': max(int(x[k]) for x in rows)/1e6}
            for k in ['cpu_ns','render_ns','reserve_ns','admit_ns','submit_ns','join_ns']} if rows else {}

def pcm_history(path, r):
    text=path.read_text(); meta=kv(path)
    names=['seq','ns','op','arg','result','state','queued','appl','hw','epoch','xfer']
    records=[]
    for match in RECORD.finditer(text):
        row=dict(zip(names,match.groups()))
        row={k:(v if k=='op' else int(v)) for k,v in row.items()}
        records.append(row)
    assert meta['retained_from']=='0' and len(records)==int(meta['entries_total'])
    assert [x['seq'] for x in records]==list(range(len(records)))
    assert all(x['ns']<=y['ns'] for x,y in zip(records,records[1:]))
    boundary=int(r['pcm_boundary']); buffer=int(r['pcm_buffer'])
    running=[x for x in records if x['op']=='SYNC_OK' and x['state']==3]
    valid=lambda x: boundary>0 and x['appl']%boundary==x['xfer']%boundary and (x['appl']-x['hw'])%boundary==x['queued'] and x['queued']<=buffer
    bad=next((x for x in running if not valid(x)),None)
    begin,end=int(r['begin_ns']),int(r['end_ns'])
    prefix=[x for x in running if begin<=x['ns']<=end and (bad is None or x['seq']<bad['seq'])]
    faults=[x for x in records if x['result']<0 and x['result'] not in (-11,-4)]
    # Censor at the first invalid pointer OR first explicit PCM fault.
    cutoff=min([x['ns'] for x in [bad,*faults] if x is not None],default=end+1)
    prefix=[x for x in prefix if x['ns']<cutoff]
    return records,prefix,bad,faults,cutoff

def main(archive):
    archive=archive.resolve(); assert archive.is_relative_to(ROOT/'device-evidence')
    installation=ROOT/'evidence/2026-10-15/render-pressure3/installation.json'
    receipt=json.loads(installation.read_text())
    baseline=json.loads((ROOT/'device-evidence'/receipt['archive']/'archive.json').read_text())
    a=json.loads((archive/'archive.json').read_text());assert a['fat_clean'] and a['card_writes']==0
    old={x['path']:x['sha256'] for x in baseline['all_retro_files']}
    new={x['path']:x['sha256'] for x in a['all_retro_files']}
    changed=[p for p,h in old.items() if new.get(p)!=h]
    # last-launch-lab can remain identical: both markers use pressure2 bytes.
    assert set(changed)<={'retro/snes-mvp/launch.sh','retro/snes-mvp/last-launch-lab','retro/swapfile','retro/uart-fix1/latest-boot.log'},changed
    assert not [p for p in old if p not in new]
    package=archive/'retro/render-pressure3'
    for name,h in receipt['payload_hashes'].items():assert digest(package/name)==h,name
    assert new['retro/snes-mvp/launch.sh']==receipt['dispatch_sha256']
    assert not list((archive/'retro').rglob('armed')) and not (archive/'retro/update/Code.bkp').exists()
    q=json.loads((package/'qualification.json').read_text())
    for group in ['sources','local_compile_dependencies']:
        for name,h in q[group].items():assert digest(ROOT/name)==h,name
    for name,h in q['private_support'].items():assert digest(ROOT/'build/render-pressure3-private/runner'/name)==h,name
    runs=list((package/'results').iterdir());assert len(runs)==1;run=runs[0]
    spec=importlib.util.spec_from_file_location('pressure3_report',ROOT/'build/report-render-pressure3.py')
    reporter=importlib.util.module_from_spec(spec);spec.loader.exec_module(reporter)
    report=reporter.analyze(run,installation=installation)
    assert report['physical'] and len(report['phases'])==77
    assert report['summary']==dict(version='render-pressure3',mock='0',phases='77',planned_phases='77',issues='15',stopped='0',expired='0')
    assert kv(run/'supervisor.txt')==dict(forced='0',reaped='1',raw_status='256')
    assert 'lab_exit=1' in (run/'wrapper.log').read_text()
    phases=[]
    for cell in report['phases']:
        p,r=cell['parameters'],cell['result'];d=run/cell['phase']
        rows=list(csv.DictReader(x for x in (d/'samples.csv').read_text().splitlines() if not x.startswith('#')))
        requested,done=int(p['requested_frames']),int(r['completed'])
        warm=[x for x in rows if 8<=int(x['frame'])<requested-1]
        item=dict(phase=cell['phase'],parameters=p,result=r,accepted=cell['physical_cell_accepted'],
                  warm=metric(warm),burst_events=[],audio=None,
                  presentation_skipped=int(r['presentation_skipped']),
                  skipped_completed_frames=[int(x['frame']) for x in rows if int(p['kind']) in (4,5) and x['presented']=='0'])
        if int(p['audio']):
            records,prefix,bad,faults,cutoff=pcm_history(d/'pcm-full.txt',r)
            assert prefix
            rate=int(r['rate']);prime=int(r['primed_frames'])
            drains=[x for x in records if x['op']=='DRAIN_REQUEST']
            item['audio']=dict(full_history=True,first_invalid_running_observation=bad,
                               final_fault=faults[-1] if faults else None,
                               valid_prefix_end_ns=cutoff,
                               minimum_valid_production_reserve_frames=min(x['queued'] for x in prefix),
                               minimum_valid_production_reserve_ms=min(x['queued'] for x in prefix)*1000/rate,
                               valid_production_first=prefix[0],valid_production_last=prefix[-1],
                               drain_requests=len(drains),
                               accounting_exact=int(r['audio_enqueued'])==int(r['audio_accepted'])+int(r['audio_remaining'])+int(r['audio_cleared']))
            if item['accepted']:
                assert bad is None and not faults and len(drains)==1 and drains[0]['ns']>=int(r['end_ns'])
                assert r['audio_enqueued']==r['audio_accepted'] and r['audio_remaining']==r['audio_cleared']=='0'
            else:
                item['valid_prefix_warm']=metric([x for x in warm if int(x['end_ns'])<cutoff and x['pointer_valid']=='1'])
            if int(p['load_every'])>1:
                executed=int(r['load_events'])
                for event in range(executed):
                    frame=(event+1)*int(p['load_every'])-1
                    row=next((x for x in rows if int(x['frame'])==frame),None)
                    entry=dict(event=event+1,frame=frame,completed_row=row is not None)
                    if row:
                        start=int(row['begin_ns']); next_frame=frame+int(p['load_every'])
                        following=next((x for x in rows if int(x['frame'])==next_frame),None)
                        end=int(following['begin_ns']) if following else int(r['end_ns'])
                        observations=[x for x in prefix if start<=x['ns']<=end]
                        minimum=min(observations,key=lambda x:x['queued']) if observations else None
                        recovery=next((x for x in observations if minimum and x['seq']>minimum['seq'] and x['queued']>=prime),None)
                        post=[x for x in rows if frame<int(x['frame'])<next_frame and int(x['end_ns'])<cutoff and x['pointer_valid']=='1']
                        entry.update(begin_ns=start,end_ns=int(row['end_ns']),
                                     main_CPU_ms=int(row['cpu_ns'])/1e6,render_and_burn_wall_ms=int(row['render_ns'])/1e6,
                                     frame_wall_including_admission_ms=(int(row['end_ns'])-start)/1e6,
                                     minimum_valid_native_reserve=minimum,
                                     recovery_to_prime=recovery,
                                     recovery_from_observed_minimum_ms=(recovery['ns']-minimum['ns'])/1e6 if recovery else None,
                                     post_burst_valid_rows=len(post),post_burst_metrics=metric(post),
                                     recovery_censored_by_fault_or_invalid_pointer=cutoff<=end,
                                     final_frame_no_recovery_window=frame==requested-1)
                    else:
                        entry['timing_unavailable']='Failure after load execution; incomplete iteration has no samples.csv row.'
                    item['burst_events'].append(entry)
        phases.append(item)
    assert sum(x['accepted'] for x in phases)==62
    assert all(phases[i]['accepted'] for i in [42,59,60,63,64,66,67,68,69,70,71,74])
    assert not any(phases[i]['accepted'] for i in [61,62,65,72,73,75,76])
    assert [int(phases[i]['result']['load_events']) for i in [63,64,65,74,75,76]]==[6,6,1,6,2,1]
    assert all(x['recovery_to_prime'] for i in [63,64,74] for x in phases[i]['burst_events'][:5])
    assert phases[75]['burst_events'][0]['recovery_to_prime'] is None
    assert sum(x['presentation_skipped'] for x in phases)==5
    assert phases[64]['skipped_completed_frames']==[32,62,92,123,152]
    comparisons=[]
    for candidate,control in zip(range(59,66),range(70,77)):
        c,b=phases[candidate],phases[control]
        assert c['parameters']['presentation_policy']=='1' and b['parameters']['presentation_policy']=='0'
        assert {k:v for k,v in c['parameters'].items() if k!='presentation_policy'}=={k:v for k,v in b['parameters'].items() if k!='presentation_policy'}
        comparisons.append(dict(candidate_phase=candidate,blocking_phase=control,parameters_match=True,
                                candidate_pass=c['accepted'],blocking_pass=b['accepted'],
                                candidate_completed=int(c['result']['completed']),blocking_completed=int(b['result']['completed']),
                                candidate_skipped=c['presentation_skipped'],blocking_skipped=b['presentation_skipped']))
    before,after=[fields((run/name).read_text()) for name in ['uart-before.txt','uart-after.txt']]
    for status in [before,after]:
        assert all(status[k]==v for k,v in dict(version='4',result='0',irq='19',attached='1',fault='0',bypass='0',cap='0').items())
    assert int(after['calls'])==int(after['added'])+int(after['fallback'])
    snapshots=[run/'phase-000/before.txt',run/'phase-076/after.txt']
    contents=[p.read_text() for p in snapshots];t=[int(fields(s)['kernel_ns']) for s in contents]
    irq=[int(re.search(r'^\s*19:\s+(\d+)',s,re.M).group(1)) for s in contents]
    inputs={p.relative_to(archive).as_posix():digest(p) for p in sorted(run.rglob('*')) if p.is_file() and p.name!='pressure-analysis.json'}
    data=dict(version='render-pressure3-return',source_sha256=digest(Path(__file__)),archive=archive.name,
              archive_sha256=digest(archive/'archive.json'),installation_sha256=digest(installation),
              archive_files=len(new),archive_bytes=sum(x['bytes'] for x in a['all_retro_files']),
              protected_prior_exact=len(old)-len(changed),changed_prior=changed,
              physical=True,clean_FAT=True,card_writes=0,one_shots_consumed=True,
              sources_and_payloads_exact=True,summary=report['summary'],supervisor=kv(run/'supervisor.txt'),
              accepted=62,failed=15,presentation_skipped_total=5,comparisons=comparisons,period_ms=PERIOD_NS/1e6,
              UART=dict(before=before,after=after,observation_seconds=(t[1]-t[0])/1e9,
                        IRQ19_delta=irq[1]-irq[0],IRQ19_per_second=(irq[1]-irq[0])*1e9/(t[1]-t[0])),
              phases=phases,inputs=inputs,physical_device_ceiling_proven=False,
              limits=report['limits']+['Matched controls run after candidates; ordering/frequency/temperature effects are not independently excluded.',
                  '180-quantum cells are bounded (~3 second), not sustained gameplay qualification.',
                  'Last burst is final produced frame: completion/drain passes but no subsequent recovery window exists.',
                  'Reserve/recovery after the first invalid pointer or explicit PCM error is censored.',
                  'Skipping is intentional presentation loss; rendered frames/audio quanta are retained. No optical quality claim.',
                  'Failed iterations may submit a drawing or execute a load before completed increments. Raw counters retain this boundary.',
                  'Audio-worker CPU includes final drain; do not sum into an exact synchronous per-frame CPU budget.',
                  'Synthetic row stream does not measure whole CPU/APU/PPU or establish an emulator speedup.'])
    out=ROOT/'build/render-pressure3-return-private';out.mkdir(exist_ok=True)
    (out/'return.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({k:data[k] for k in ['archive','archive_files','protected_prior_exact','changed_prior','accepted','failed','UART']},indent=2))

if __name__=='__main__':main(Path(sys.argv[1]))
