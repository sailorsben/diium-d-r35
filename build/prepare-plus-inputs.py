"""Prepare local owner-supplied FF6 inputs and a separate candidate state copy."""
from pathlib import Path
import argparse,struct,zipfile,zlib
ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--rom',type=Path,required=True);parser.add_argument('--snapshot',type=Path,required=True)
args=parser.parse_args()
if args.rom.suffix.lower()=='.zip':
    with zipfile.ZipFile(args.rom) as archive:
        entries=[e for e in archive.infolist() if e.filename.lower().endswith(('.sfc','.smc'))]
        assert len(entries)==1 and entries[0].file_size<=8*1024*1024
        rom=archive.read(entries[0])
else:rom=args.rom.read_bytes()
state=args.snapshot.read_bytes();crc=zlib.crc32(rom)&0xffffffff
assert crc==0xa27f1c7a and len(rom)==3145728,'This qualification targets the known FF6 workload'
assert state[:8]==b'D35MVP01' and len(state)==531668+40
assert struct.unpack_from('<IIII',state,12)==(crc,len(rom),0x5ba71d2a,656816)
assert struct.unpack_from('<I',state,32)[0]==zlib.crc32(state[40:])&0xffffffff
out=ROOT/'plus-a7-out';out.mkdir(exist_ok=True)
(out/'ff6.sfc').write_bytes(rom);(out/'returned.state').write_bytes(state)
core=(out/'plus-a7.so').read_bytes();candidate_crc=zlib.crc32(core)&0xffffffff
migrated=bytearray(state);struct.pack_into('<II',migrated,20,candidate_crc,len(core))
destination=out/'integration-saves';destination.mkdir(exist_ok=True)
path=destination/f'game-{crc:08x}-{len(rom)}-core-{candidate_crc:08x}-{len(core)}.state'
assert not path.exists() or path.read_bytes()==migrated,'Preserve a progressed test state'
path.write_bytes(migrated)
print('Prepared local ROM/state copies; owner originals unchanged')
