from pathlib import Path
from hashlib import sha256, sha1
import json
import shutil
import zipfile
import zlib

root = Path(__file__).resolve().parent.parent
package = root / 'SNES-comparison-FFVI-Rev1'
package.mkdir(exist_ok=True)
source = Path('E:/R35/002/Final Fantasy 3.zip')
with zipfile.ZipFile(source) as archive:
    assert archive.testzip() is None
    raw = archive.read('Final Fantasy 3.sfc')
assert len(raw) == 3145728 + 512
rom = raw[512:]
assert sha1(rom).hexdigest() == '057ada1c641e3e0b3ca34e6e4f4eb1b05a87143a'
assert zlib.crc32(rom) == 0xc0fa0464
assert rom[0xffc0:0xffd5].rstrip() == b'FINAL FANTASY 3'
assert rom[0xffdb] == 1
dest = package / 'Final Fantasy VI (Rev 1).zip'
assert not dest.exists(), 'Inspect existing comparison before replacing'
with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED) as archive:
    archive.writestr('Final Fantasy VI (Rev 1).sfc', rom)
with zipfile.ZipFile(dest) as archive:
    assert archive.testzip() is None
    assert archive.read('Final Fantasy VI (Rev 1).sfc') == rom
shutil.copy2(Path('D:/002/images/Final Fantasy VI.png'), package / 'Final Fantasy VI (Rev 1).png')
report = {
    'game': 'Final Fantasy III (USA) (Rev 1)',
    'menu_label': 'Final Fantasy VI (Rev 1)',
    'source': str(source),
    'source_zip_sha256': sha256(source.read_bytes()).hexdigest(),
    'stripped_copier_header_bytes': 512,
    'rom_sha1': sha1(rom).hexdigest(),
    'rom_crc32': f'{zlib.crc32(rom):08X}',
    'rom_sha256': sha256(rom).hexdigest(),
    'rom_bytes': len(rom),
    'game_zip_sha256': sha256(dest.read_bytes()).hexdigest(),
    'hash_reference': 'https://raw.githubusercontent.com/libretro/libretro-database/master/metadat/no-intro/Nintendo%20-%20Super%20Nintendo%20Entertainment%20System.dat',
    'purpose': 'Separate revision comparison. No evidence that Rev 1 fixes clicking.',
}
(package / 'prepared.json').write_text(json.dumps(report, indent=2) + '\n')
(package / 'README.txt').write_text('Select Final Fantasy VI (Rev 1) in SFC/SNES. Start a new game and compare the same opening/outdoor music with Final Fantasy VI. Uses the restored clean Plus emulator. Separate filename keeps existing game and state slots intact. This is a diagnostic comparison, not a confirmed audio fix.\n')
print(json.dumps(report, indent=2))
