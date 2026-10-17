"""Preservation/boot receipt for the October 17 reflash; archived inputs only."""
from pathlib import Path
import json, sys
from attempt_archive import digest, verify_saved

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT/'evidence/2026-10-17/uart-kernel-reflash'

def read(path):
    return json.loads(path.read_text())

def main(archive):
    archive = archive.resolve()
    assert archive.is_relative_to((ROOT/'device-evidence').resolve())
    a, o = read(archive/'archive.json'), read(archive/'outside-retro.json')
    assert a['fat_clean'] and a['card_writes'] == o['card_writes'] == 0
    verify_saved(archive,a)
    for e in o['files']:
        if e['stored']:
            assert digest(archive/e['path']) == e['sha256']
    i = read(PUBLIC/'installation.json')
    before = ROOT/'device-evidence'/i['archive']
    entries = a['all_retro_files'] + o['files']
    actual = {e['path']:e['sha256'] for e in entries}
    prior = read(before/'archive.json')['all_retro_files'] + read(before/'outside-retro.json')['files']
    expected = {e['path']:e['sha256'] for e in prior}
    expected['retro/init'] = i['normal_init_sha256']
    expected['retro/update/Code.bkp'] = i['package_sha256']
    assert set(actual) == set(expected)
    changes = {n:{'before':h,'after':actual[n]} for n,h in expected.items() if actual[n] != h}
    assert set(changes) <= {'retro/swapfile','retro/setting.xml'}
    assert actual['retro/init'] == i['normal_init_sha256']
    assert actual['retro/update/Code.bkp'] == i['package_sha256']
    assert not any(n.endswith('/armed') or n.startswith('retro/uart-kernel-verify1/') for n in actual)
    r = {'archive':archive.name, 'all_files_hashed':len(actual),
         'archive_manifest_sha256':digest(archive/'archive.json'),
         'outside_manifest_sha256':digest(archive/'outside-retro.json'),
         'installation_sha256':digest(PUBLIC/'installation.json'),
         'physical_boot_user_accepted':True,
         'user_observation':'Flash worked; both Vesper screens and stock launcher came up.',
         'expected_postboot_changes':changes,
         'saves_states_stock_binaries_and_prior_evidence_unchanged':True,
         'returned_stock_setting_and_swap_hashes_preserved':True,
         'new_sparse_content_bytes':a['new_content_bytes']+o['new_content_bytes'],
         'FAT_clean':True, 'card_writes':0, 'no_full_backup':True,
         'exact_flash_readback_this_boot_available':False,
         'fresh_UART_IRQ_observation_this_boot_available':False,
         'update_trigger_present':a['update_trigger_present'],
         'next_step':'Remove exact used update trigger; one read-only SPI/IRQ verification boot, no firmware writes or module loads.',
         'analyzer_sha256':digest(Path(__file__))}
    text = json.dumps(r,indent=2)+'\n'
    (archive/'reflash-boot-analysis.json').write_text(text)
    (PUBLIC/'boot-return.json').write_text(text)
    print(text)

if __name__ == '__main__':
    main(Path(sys.argv[1]))
