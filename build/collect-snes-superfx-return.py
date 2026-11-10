"""Archive a Super FX return before checking the FAT32 volume read-only."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from attempt_archive import digest, inventory, write_manifest


ROOT = Path(__file__).resolve().parent.parent
INSTALLATION = ROOT/'evidence/2026-11-10/snes-raster-batches/superfx-device-installation.json'


def main():
    card = Path('I:/').resolve()
    assert str(card).lower() in ('i:/', 'i:\\')
    receipt = json.loads(INSTALLATION.read_text())
    assert digest(card/'retro/snes-mvp/launch.sh') == receipt['dispatch_sha256']
    assert digest(card/receipt['target']/'launch.sh') == receipt['payload_hashes']['launch.sh']
    assert not list(card.rglob('armed')) and not list(card.rglob('Code.bkp'))
    out = ROOT/'device-evidence'/('superfx-return-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir()
    entries = inventory(card, out)
    outside = inventory(card, out, outside=True)

    dirty = subprocess.run(['fsutil', 'dirty', 'query', 'I:'], capture_output=True, text=True, timeout=15)
    scan = subprocess.run(['chkdsk', 'I:'], capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=120)
    (out/'fsutil-dirty.txt').write_text(dirty.stdout + dirty.stderr, encoding='utf-8')
    (out/'chkdsk-return.txt').write_text(scan.stdout + scan.stderr, encoding='utf-8')
    assert dirty.returncode == 0 and '11EB-1465' in scan.stdout
    assert ' is dirty' in dirty.stdout.lower() or ' is not dirty' in dirty.stdout.lower()
    dirty_bit = ' is dirty' in dirty.stdout.lower()
    scan_clean = scan.returncode == 0 and 'Windows has scanned the file system and found no problems.' in scan.stdout
    write_manifest(out/'archive.json', entries, all_retro_files=entries, card_writes=0,
                   fat_clean=scan_clean and not dirty_bit, filesystem_scan_clean=scan_clean,
                   dirty_bit=dirty_bit, chkdsk_exit_code=scan.returncode, update_trigger_present=False)
    write_manifest(out/'outside-retro.json', outside, files=outside, card_writes=0)
    print(out)
    print(dirty.stdout + scan.stdout)


if __name__ == '__main__':
    main()
