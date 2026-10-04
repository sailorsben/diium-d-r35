"""Extract the actual stock libretro mask fixture, independent of MVP mapping."""
from pathlib import Path
from hashlib import sha256
import struct
import sys

source=Path(sys.argv[1]); target=Path(sys.argv[2]); data=source.read_bytes()
assert sha256(data).hexdigest()=='8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72'
assert data[:6]==b'\x7fELF\x01\x01', 'Expected pinned little-endian ARM32 executable'
phoff=struct.unpack_from('<I',data,28)[0]
size,count=struct.unpack_from('<HH',data,42)
address=0x16b254  # Stock joy_key_mask, indexed by libretro joypad ID.
for index in range(count):
    kind,offset,vaddr,_,length,_,_,_=struct.unpack_from('<8I',data,phoff+index*size)
    if kind==1 and vaddr<=address and address+64<=vaddr+length:
        masks=struct.unpack_from('<16I',data,offset+address-vaddr)
        break
else:
    raise AssertionError('Stock input reference is outside file-backed LOAD segments')
assert masks[4:8]==(0x10,0x40,0x80,0x20)
target.write_text('/* Extracted from pinned stock joy_key_mask at 0x16b254. */\n'
                  'static const uint32_t vendor_native_masks[16] = {\n    '+
                  ','.join(f'0x{mask:x}u' for mask in masks)+'\n};\n')
print('PASS: input reference extracted from pinned stock callback table; UP/DOWN/LEFT/RIGHT=10/40/80/20 hex')
