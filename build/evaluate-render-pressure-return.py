"""Source-bound physical return analysis; keep production and shutdown separate."""
from pathlib import Path
from hashlib import sha256
import csv, importlib.util, json, re, statistics, sys

ROOT = Path(__file__).resolve().parent.parent
RECORD = re.compile(r'seq=(\d+) ns=(\d+) op=(\S+) arg=(\d+) result=(-?\d+) state=(\d+) queued=(\d+) appl=(\d+) hw=(\d+) epoch=(\d+) xfer=(\d+)')

def digest(p): return sha256(p.read_bytes()).hexdigest()
def kv(p): return dict(l.split('=', 1) for l in p.read_text().splitlines() if '=' in l)
def fields(text): return dict(re.findall(r'(\w+)=([^\s]+)', text))

def main(archive):
    archive = archive.resolve()
    assert archive.is_relative_to(ROOT / 'device-evidence')
    installation = ROOT / 'evidence/2026-10-15/render-pressure1/installation.json'
    receipt = json.loads(installation.read_text())
    baseline = json.loads((ROOT / 'device-evidence' / receipt['archive'] / 'archive.json').read_text())
    manifest = json.loads((archive / 'archive.json').read_text())
    assert manifest['fat_clean'] and manifest['card_writes'] == 0
    original = {e['path']: e['sha256'] for e in baseline['all_retro_files']}
    returned = {e['path']: e['sha256'] for e in manifest['all_retro_files']}
    changed = [p for p, h in original.items() if returned.get(p) != h]
    assert set(changed) == {'retro/snes-mvp/launch.sh', 'retro/snes-mvp/last-launch-lab', 'retro/swapfile'}, changed
    package = archive / 'retro/render-pressure1'
    for name, h in receipt['payload_hashes'].items(): assert digest(package / name) == h, name
    assert returned['retro/snes-mvp/launch.sh'] == receipt['dispatch_sha256']
    assert not list((archive / 'retro').rglob('armed'))
    assert not (archive / 'retro/update/Code.bkp').exists()
    q = json.loads((package / 'qualification.json').read_text())
    for name, h in q['sources'].items(): assert digest(ROOT / name) == h, name
    for name, h in q['private_support'].items():
        assert digest(ROOT / 'build/render-pressure-private/runner' / name) == h, name
    runs = list((package / 'results').iterdir()); assert len(runs) == 1
    run = runs[0]
    spec = importlib.util.spec_from_file_location('pressure_report', ROOT / 'build/report-render-pressure.py')
    reporter = importlib.util.module_from_spec(spec); spec.loader.exec_module(reporter)
    report = reporter.analyze(run, installation=installation)
    assert report['physical'] and len(report['phases']) == 70
    assert report['summary'] == dict(version='render-pressure1', mock='0', phases='70', planned_phases='70', issues='20', stopped='0', expired='0')
    assert kv(run / 'supervisor.txt') == dict(forced='0', reaped='1', raw_status='256')
    assert 'lab_exit=1' in (run / 'wrapper.log').read_text()
    results = []
    for cell in report['phases']:
        d = run / cell['phase']; p = cell['parameters']; r = cell['result']
        count = int(p['requested_frames']); done = int(r['completed'])
        rows = list(csv.DictReader(l for l in (d / 'samples.csv').read_text().splitlines() if not l.startswith('#')))
        warm = [x for x in rows if 8 <= int(x['frame']) < count - 1]
        item = dict(phase=cell['phase'], parameters=p, result=r,
                    end_to_end_accepted=cell['physical_cell_accepted'],
                    warm={k: dict(median_ms=statistics.median(int(x[k]) for x in warm)/1e6,
                                  maximum_ms=max(int(x[k]) for x in warm)/1e6)
                          for k in ['cpu_ns','render_ns','reserve_ns','admit_ns','submit_ns','join_ns'] if warm},
                    production_completed=done == count, production_wall_ms=int(r['wall_ns'])/1e6,
                    production_main_CPU_ms=int(r['main_cpu_ns'])/1e6,
                    completed_per_second=done*1e9/int(r['wall_ns']),
                    audio=None)
        if p['audio'] == '1':
            text = (d / 'pcm-full.txt').read_text(); meta = kv(d / 'pcm-full.txt')
            records = [dict(zip(['seq','ns','op','arg','result','state','queued','appl','hw','epoch','xfer'], m.groups())) for m in RECORD.finditer(text)]
            assert meta['retained_from'] == '0' and len(records) == int(meta['entries_total'])
            begin, end = int(r['begin_ns']), int(r['end_ns']); boundary = int(r['pcm_boundary']); buffer = int(r['pcm_buffer'])
            first_invalid = None; prefix = []; invalid_production = []
            for x in records:
                if x['op'] != 'SYNC_OK' or x['state'] != '3': continue
                valid = int(x['appl']) % boundary == int(x['xfer']) % boundary and (int(x['appl'])-int(x['hw'])) % boundary == int(x['queued']) and int(x['queued']) <= buffer
                if not valid and first_invalid is None: first_invalid = x
                if begin <= int(x['ns']) <= end:
                    if not valid: invalid_production.append(x)
                    elif first_invalid is None: prefix.append(int(x['queued']))
            drains = [x for x in records if x['op'] == 'DRAIN_REQUEST']
            faults = [x for x in records if int(x['result']) < 0 and x['op'] not in ['WRITE_AGAIN']]
            production_valid = done == count and r['audio_error'] == '0' and not invalid_production and bool(prefix)
            classification = 'production_failure'
            if production_valid:
                assert len(drains) == 1 and int(drains[0]['ns']) > end
                assert faults[-1]['op'] == 'SYNC_AVAIL_MIN' and int(faults[-1]['ns']) > int(drains[0]['ns'])
                assert r['audio_enqueued'] == r['audio_accepted'] and r['audio_remaining'] == r['audio_cleared'] == '0'
                classification = 'completed_production_second_finish_failure'
            item['audio'] = dict(classification=classification, full_history=True,
                                production_pointer_valid=not invalid_production,
                                minimum_valid_prefix_reserve_frames=min(prefix) if prefix else None,
                                first_invalid_running_observation=first_invalid,
                                drain_requests=drains, final_fault=faults[-1] if faults else None,
                                accounting_exact=int(r['audio_enqueued']) == int(r['audio_accepted'])+int(r['audio_remaining'])+int(r['audio_cleared']))
        results.append(item)
    assert sum(x['end_to_end_accepted'] for x in results) == 50
    assert sum(x['audio'] is not None and x['audio']['classification'] == 'completed_production_second_finish_failure' for x in results) == 5
    assert sum(x['audio'] is not None and x['audio']['classification'] == 'production_failure' for x in results) == 15
    uart_before = fields((run / 'uart-before.txt').read_text()); uart_after = fields((run / 'uart-after.txt').read_text())
    for status in [uart_before, uart_after]:
        assert all(status[k] == v for k,v in dict(version='4', result='0', irq='19', attached='1', fault='0', bypass='0', cap='0').items())
    snapshots = [(d / name) for d in sorted(run.glob('phase-*')) for name in ['before.txt','after.txt']]
    first, last = snapshots[0].read_text(), snapshots[-1].read_text()
    times = [int(fields(x)['kernel_ns']) for x in [first, last]]
    irq_counts = [int(re.search(r'^\s*19:\s+(\d+)', x, re.M).group(1)) for x in [first,last]]
    inputs = {p.relative_to(archive).as_posix(): digest(p) for p in sorted(run.rglob('*')) if p.is_file() and p.name != 'pressure-analysis.json'}
    data = dict(version='render-pressure1-return', archive=archive.name, archive_sha256=digest(archive/'archive.json'),
                source_sha256=digest(Path(__file__)), installation_sha256=digest(installation),
                run=run.name, physical=True, clean_FAT=True, card_writes=0,
                protected_prior_exact=len(original)-len(changed), changed_prior=changed,
                source_and_payload_hashes_exact=True, one_shots_consumed=True,
                supervisor=kv(run/'supervisor.txt'), summary=report['summary'], end_to_end_accepted=50,
                completed_production_shutdown_failures=5, production_failures=15,
                UART=dict(before=uart_before, after=uart_after, observation_seconds=(times[1]-times[0])/1e9,
                          IRQ19_delta=irq_counts[1]-irq_counts[0], IRQ19_per_second=(irq_counts[1]-irq_counts[0])*1e9/(times[1]-times[0])),
                phases=results, inputs=inputs, physical_device_ceiling_proven=False,
                limits=report['limits'] + ['All audio cells fail end-to-end; five finish production before a controller double-finish bug. No passing audio lifecycle claim.',
                    'Three burst cells fail before frame29, so none executes its first requested burst.',
                    'Single ordered physical run; synthetic controls do not establish full-core improvement.',
                    'CPU frequency file unavailable; no frequency or thermal ceiling claim.'])
    out = ROOT / 'build/render-pressure-return-private'; out.mkdir(exist_ok=True)
    (out/'return.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({k:data[k] for k in ['archive','protected_prior_exact','changed_prior','end_to_end_accepted','completed_production_shutdown_failures','production_failures','UART']},indent=2))

if __name__ == '__main__': main(Path(sys.argv[1]))
