"""Accept fresh physical UART verification against its actual cleaned-card staging."""
from pathlib import Path
import importlib.util, json, sys
from attempt_archive import digest

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT/'evidence/2026-10-17/uart-kernel-reflash'
BASE = 'retro/uart-kernel-verify1/'

def read(path):
    return json.loads(path.read_text())

def analyze(archive):
    install = read(PUBLIC/'verification-installation.json')
    check = read(PUBLIC/'verification-live-check.json')
    assert check['passed'] and check['installation_sha256'] == digest(PUBLIC/'verification-installation.json')
    before = ROOT/'device-evidence'/install['archive']
    old = read(before/'archive.json')['all_retro_files'] + read(before/'outside-retro.json')['files']
    assert not any(e['path'].startswith(BASE) for e in old), 'Probe output must have been absent before staging'
    expected = {e['path']:e['sha256'] for e in old if e['path'] != 'retro/update/Code.bkp'}
    expected['retro/init'] = install['init_sha256']
    expected.update({BASE+n:h for n,h in install['payload_hashes'].items()})
    expected[BASE+'armed'] = install['marker_sha256']
    a, o = read(archive/'archive.json'), read(archive/'outside-retro.json')
    entries = a['all_retro_files'] + o['files']
    actual = {e['path']:e['sha256'] for e in entries}
    changed = {n:actual.get(n) for n,h in expected.items() if actual.get(n) != h}
    assert set(changed) <= {'retro/swapfile','retro/setting.xml',BASE+'armed'}, changed
    assert changed.get(BASE+'armed','not-removed') is None
    outputs = {BASE+'consumed',BASE+'wrapper.log',BASE+'results/captures.bin',BASE+'results/report.jsonl'}
    for window in ['uart-before','uart-after']:
        prefix = BASE+'logs/'+window+'/'
        outputs.add(prefix+'timing.txt')
        for tag in ['before','after']:
            for name in ['interrupts','serial','stat','modules','version','cmdline','boot-id','presence']:
                outputs.add(prefix+tag+'-'+name+'.txt')
    assert set(actual)-set(expected) == outputs
    assert actual[BASE+'consumed'] == install['marker_sha256']
    for e in entries:
        # Consumed is an unchanged qualified marker, intentionally hash-only;
        # its inventory hash is pinned above. All measured outputs need bytes.
        if e['path'] in outputs and e['path'] != BASE+'consumed':
            assert e['stored'] and digest(archive/e['path']) == e['sha256'], e['path']
    spec = importlib.util.spec_from_file_location('probe',ROOT/'build/analyze-uart-kernel-verify-return.py')
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    v = probe.analyze_probe(archive,install)
    previous = [ROOT/'evidence/2026-10-16/uart-kernel-verification/powered-return.json',
                ROOT/'device-evidence/uart-kernel-return-20261017T022201466502Z/analysis.json']
    prior_ids = {read(p)['boot_id'] for p in previous}
    assert v['boot_id'] not in prior_ids, 'Stale physical boot'
    windows = v['windows']
    assert windows[0]['kernel_times_ns']['end_snapshot_end_ns'] < windows[1]['kernel_times_ns']['begin_snapshot_start_ns']
    v.update({'reflash_verification':True,'fresh_boot_verified':True,
              'prior_boot_ids_compared':sorted(prior_ids),
              'verification_installation_sha256':digest(PUBLIC/'verification-installation.json'),
              'archive_manifest_sha256':digest(archive/'archive.json'),
              'outside_manifest_sha256':digest(archive/'outside-retro.json'),
              'saves_and_prior_evidence_unchanged':True,
              'protected_staged_files_unchanged':len(expected)-len(changed),
              'expected_card_changes':changed,'new_run_output_files':len(outputs),
              'both_Vesper_screens_and_rootfs_exact':True,
              'user_observation':'Completed plugged in and returned to stock.',
              'stock_return_on_external_power_user_accepted':True,
              'battery_boundary':'User reports full charge restored normal behavior; no physical ADC fault demonstrated.',
              'analyzer_sources':{n:digest(ROOT/'build'/n) for n in ['analyze-uart-reflash-verification.py','analyze-uart-kernel-verify-return.py']}})
    return v

if __name__ == '__main__':
    p = Path(sys.argv[1]).resolve()
    assert p.is_relative_to((ROOT/'device-evidence').resolve())
    v = analyze(p)
    text = json.dumps(v,indent=2)+'\n'
    (p/'reflash-verification-analysis.json').write_text(text)
    (PUBLIC/'verified-return.json').write_text(text)
    print(text)
