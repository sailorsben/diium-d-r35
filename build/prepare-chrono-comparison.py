from pathlib import Path
from hashlib import sha256
import json
import struct
import zipfile
root=Path(__file__).resolve().parent.parent
out=root/'SNES-comparison-Chrono-Trigger'
out.mkdir(exist_ok=True)
source=Path('C:/Users/sailo/Downloads/Chrono_Trigger_USA_SNES.zip')
with zipfile.ZipFile(source) as z:
    rom=z.read('Chrono_Trigger_USA_SNES.sfc')
assert len(rom)==4194304
header=rom[0xffc0:0x10000]
assert header[:21].rstrip()==b'CHRONO TRIGGER'
assert header[21]==0x31 and header[25]==1
complement,checksum=struct.unpack('<HH',header[28:32])
assert complement^checksum==65535 and sum(rom)&65535==checksum
dest=out/'Chrono Trigger.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('Chrono Trigger.sfc',rom)
with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None
    assert z.read('Chrono Trigger.sfc')==rom
report={'game':'Chrono Trigger (USA)','source':str(source),
        'requested_archive':'H:/DR35.zip','requested_archive_bytes':Path('H:/DR35.zip').stat().st_size,
        'rom_sha256':sha256(rom).hexdigest(),'rom_bytes':len(rom),
        'internal_title':header[:21].decode().strip(),'country':header[25],
        'map_mode':header[21],'checksum':checksum,'checksum_valid':True,
        'game_zip_sha256':sha256(dest.read_bytes()).hexdigest(),'target':'D:/002/Chrono Trigger.zip'}
(out/'prepared.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
