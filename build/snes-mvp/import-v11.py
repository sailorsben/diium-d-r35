"""Convert one v11 Plus vendor snapshot into a separate, build-bound MVP copy.
Never writes source/card files. The old wrapper contains no ROM identity, so the
caller must explicitly select the matching ROM. This importer pins the known
v11 Plus binary and rejects different cores and malformed containers.
"""
from pathlib import Path
import argparse, hashlib, json, struct, zipfile, zlib

PINNED_CORE_SHA256='1812b19b50270c625b43126253f687edc46bb9ba3cf0c4ccaaf3e2c29bef6657'
EXPECTED_STATE_BYTES=531668
LIMIT=8*1024*1024

def sha(data): return hashlib.sha256(data).hexdigest()
def crc(data): return zlib.crc32(data)&0xffffffff

def convert(state_path,rom_path,core_path,output_dir,validation_rom=None):
 state_path,rom_path,core_path,output_dir=map(Path,(state_path,rom_path,core_path,output_dir))
 source=state_path.read_bytes(); core=core_path.read_bytes()
 if sha(core)!=PINNED_CORE_SHA256: raise ValueError('Core differs from the exact tested v11 Plus binary')
 if not 20<=len(source)<=LIMIT: raise ValueError('Invalid vendor state size')
 compressed_size=struct.unpack_from('<I',source)[0]
 if not 0<compressed_size<=len(source)-4: raise ValueError('Invalid compressed state boundary')
 decoder=zlib.decompressobj();wrapper=decoder.decompress(source[4:4+compressed_size],LIMIT)
 if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail: raise ValueError('Invalid bounded zlib stream')
 if wrapper[:8]!=b'D35PLUS1' or wrapper[12:16]!=b'a79d': raise ValueError('Wrong adapter/core signature')
 if len(wrapper)!=EXPECTED_STATE_BYTES+16 or struct.unpack_from('<I',wrapper,8)[0]!=EXPECTED_STATE_BYTES:
  raise ValueError('Unexpected core serialized size')
 raw=wrapper[16:]
 member=None
 if rom_path.suffix.lower()=='.zip':
  with zipfile.ZipFile(rom_path) as archive:
   candidates=[i for i in archive.infolist() if not i.is_dir() and Path(i.filename).suffix.lower() in ('.sfc','.smc','.bin')]
   if len(candidates)!=1 or candidates[0].file_size>LIMIT: raise ValueError('ROM archive needs exactly one bounded SNES ROM')
   member=candidates[0].filename;rom=archive.read(candidates[0])
 else: rom=rom_path.read_bytes()
 if not 0<len(rom)<=LIMIT: raise ValueError('Invalid ROM size')
 header=b'D35MVP01'+struct.pack('<8I',1,crc(rom),len(rom),crc(core),len(core),len(raw),crc(raw),0)
 assert len(header)==40
 payload=header+raw
 output_dir.mkdir(parents=True,exist_ok=True)
 destination=output_dir/f'game-{crc(rom):08x}-{len(rom)}-core-{crc(core):08x}-{len(core)}.state'
 if destination.exists() and destination.read_bytes()!=payload: raise ValueError('Refusing to replace an existing different MVP snapshot')
 if not destination.exists(): destination.write_bytes(payload)
 if destination.read_bytes()!=payload: raise IOError('Output readback mismatch')
 manifest=dict(source=str(state_path.resolve()),source_sha256=sha(source),rom=str(rom_path.resolve()),rom_member=member,
   rom_sha256=sha(rom),rom_crc32=f'{crc(rom):08x}',rom_bytes=len(rom),core=str(core_path.resolve()),
   core_sha256=sha(core),core_crc32=f'{crc(core):08x}',core_bytes=len(core),raw_bytes=len(raw),
   raw_sha256=sha(raw),output=str(destination.resolve()),output_sha256=sha(payload),
   caveat='Old vendor wrapper has no ROM identity. Caller explicitly selected matching working FF6 ROM. Original state unchanged.',
   validation='Input checksum/signature/size and output readback verified. Runner checks exact ROM/core and core serialized size before loading.')
 if sha(state_path.read_bytes())!=manifest['source_sha256']: raise IOError('Source changed during extraction')
 destination.with_suffix('.import.json').write_text(json.dumps(manifest,indent=2)+'\n')
 if validation_rom:
  r=Path(validation_rom)
  if r.exists() and r.read_bytes()!=rom: raise ValueError('Refusing to overwrite validation ROM')
  r.write_bytes(rom)
 print(json.dumps(manifest,indent=2))
 return destination

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['state','rom','core','output_dir']:p.add_argument('--'+name.replace('_','-'),required=True)
 p.add_argument('--validation-rom');a=p.parse_args()
 convert(a.state,a.rom,a.core,a.output_dir,a.validation_rom)
