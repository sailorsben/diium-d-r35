"""Private UART rootfs firmware; preserve latest Wings2 screens and kernel."""
from pathlib import Path
from hashlib import sha256
import argparse, importlib.util, io, json, struct, zipfile, zlib
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'device-evidence/uart-firmware1'
BASELINE='5c2f34e6b4451b27fa5e6782f1396d8e6a3bf485e24c0fe209b44854f77660c3'
VENDOR='8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72'
def digest(b):return sha256(b).hexdigest()
def load(n):
 s=importlib.util.spec_from_file_location(n,ROOT/'build'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def record(name,body,mode,ino):
 fields=[ino,mode,0,0,1,0,len(body),0,0,0,0,len(name.encode())+1,0]
 header=b'070701'+b''.join(('%08x'%v).encode() for v in fields)+name.encode()+b'\0'
 header+=b'\0'*(-len(header)%4);data=header+body;return data+b'\0'*(-len(data)%4)
def prepare(out=OUT):
 out=out.resolve();assert out.is_relative_to(ROOT/'device-evidence') and not out.exists()
 baseline=(ROOT/'device-evidence/vesper-wings-firmware-20261015/expected-after-vendor.bin').read_bytes();assert digest(baseline)==BASELINE and len(baseline)==8388608
 # Reuse the exact qualified and physically used module/helper, never rebuild them here.
 q=load('install-uart-fix.py').artifacts();module=(ROOT/'build/uart-fix-private/package/d35_uart_tx.ko').read_bytes();helper=(ROOT/'build/uart-fix-private/package/uart-fix-boot').read_bytes()
 inspect=load('inspect-spi-boot.py');start,slot,field=0x301d10,3406558,0xc0040;size=struct.unpack_from('<I',baseline,field)[0]
 compressed=baseline[start:start+size];cpio,used=inspect.gunzip(compressed);assert used==size
 entries=inspect.newc(cpio);assert not any(e['name'].startswith('d35-uart') for e in entries)
 original=next(e for e in entries if e['name']=='init.project.rc');body=cpio[original['data_offset']:original['data_offset']+original['bytes']]
 anchor=b'if [ -f /usr/retro/init ];then\n';assert body.count(anchor)==1
 hook=b'# Internal UART correction, before either card or internal stock startup.\n/bin/sh /d35-uart/launch.sh start || exit 64\n\n'
 init=body.replace(anchor,hook+anchor)
 firmware=(ROOT/'build/launch-uart-firmware.sh').read_bytes().replace(b'UART_MODULE_IDENTITY',digest(module).encode())
 card=(ROOT/'build/launch-uart-fix.sh').read_bytes();anchor=b'# Rollback switch is intentionally checked before opening/loading any payload.\n';assert card.count(anchor)==1
 compat=b'''# Firmware-owned correction: verify identity/status, never attempt a second load.
if [ -x /d35-uart/launch.sh ]; then
  /bin/sh /d35-uart/launch.sh verify
  firmware_result=$?
  case "$firmware_result" in
    0) cp /tmp/d35-uart-firmware.log "$BASE/latest-boot.log" 2>/dev/null || true; exit 0 ;;
    1) ;; # Firmware safely retained original handler; use the existing card fallback.
    *) exit 64 ;;
  esac
fi
'''
 # Keep the existing disabled switch first, ahead of firmware verification as well.
 anchor2=b'if [ ! -f "$BASE/d35_uart_tx.ko" ]';assert card.count(anchor2)==1
 card=card.replace(anchor2,compat+anchor2)
 revised=b''
 for e in entries[:-1]:
  end=(e['data_offset']+e['bytes']+3)&~3;raw=cpio[e['header_offset']:end]
  if e['name']=='init.project.rc':
   h=bytearray(raw[:e['data_offset']-e['header_offset']]);h[54:62]=('%08x'%len(init)).encode();raw=bytes(h)+init;raw+=b'\0'*(-len(raw)%4)
  revised+=raw
 ino=max(int(cpio[e['header_offset']+6:e['header_offset']+14],16) for e in entries)+1
 added={'d35-uart':(b'',0o40755),'d35-uart/d35_uart_tx.ko':(module,0o100644),'d35-uart/uart-fix-boot':(helper,0o100755),'d35-uart/launch.sh':(firmware,0o100755)}
 for name,(contents,mode) in added.items():revised+=record(name,contents,mode,ino);ino+=1
 revised+=record('TRAILER!!!',b'',0,ino);revised+=b'\0'*(-len(revised)%512)
 after=inspect.newc(revised);original_entries={e['name']:e for e in entries};after_entries={e['name']:e for e in after}
 for e,a in zip(entries[:-1],after):
  n=e['name'];assert a['name']==n
  if n!='init.project.rc':assert (a['sha256'],a['bytes'],a['mode'])==(e['sha256'],e['bytes'],e['mode'])
  # Duplicate directory records retain their original raw records too.
 z=zlib.compressobj(9,zlib.DEFLATED,-15);gz=compressed[:10]+z.compress(revised)+z.flush()+struct.pack('<II',zlib.crc32(revised),len(revised));assert len(gz)<=slot,(len(gz),slot)
 candidate=bytearray(baseline);struct.pack_into('<I',candidate,field,len(gz));candidate[start:start+slot]=gz+b'\xff'*(slot-len(gz))
 assert candidate[:field]==baseline[:field] and candidate[field+4:start]==baseline[field+4:start] and candidate[start+slot:]==baseline[start+slot:]
 def package(data):
  stream=io.BytesIO();info=zipfile.ZipInfo('SPI_ROM.bin',(2026,10,16,12,0,0));info.compress_type=zipfile.ZIP_DEFLATED
  with zipfile.ZipFile(stream,'w') as archive:archive.writestr(info,data,compresslevel=9)
  return b'WQW'+stream.getvalue()
 normal=package(candidate);crc=zlib.crc32(candidate);dos=((2026-1980)<<25)|(10<<21)|(16<<16)|(12<<11)
 expected=bytearray(candidate);struct.pack_into('<II',expected,0x100,crc,dos)
 wrong=bytearray(candidate);struct.pack_into('<I',wrong,0x108,struct.unpack_from('<I',wrong,0x108)[0]+10)
 bad=bytearray(normal);bad[bad.index(b'PK\x01\x02')+16]^=1;bad[17]^=1
 repeated=bytearray(baseline);struct.pack_into('<I',repeated,0x100,crc)
 logo=after_entries['showlogo'];logo_bytes=revised[logo['data_offset']:logo['data_offset']+logo['bytes']]
 files={'candidate.bin':candidate,'expected-after-vendor.bin':expected,'rootfs.cpio':revised,'rootfs.cpio.gz':gz,'init.project.rc':init,'firmware-launch.sh':firmware,'card-launch.sh':card,'showlogo':logo_bytes,
 'fixture-compatible.bkp':normal,'fixture-incompatible.bkp':package(wrong),'fixture-consistent-bad-crc.bkp':bad,'fixture-missing-prefix.bkp':normal[3:],'fixture-already-recorded-baseline.bin':repeated}
 out.mkdir()
 for n,b in files.items():(out/n).write_bytes(b)
 blocks=[i for i in range(0,len(expected),65536) if expected[i:i+65536]!=baseline[i:i+65536]]
 report={'version':'uart-firmware1','baseline_sha256':BASELINE,'baseline_path':'device-evidence/vesper-wings-firmware-20261015/expected-after-vendor.bin','baseline_evidence':'Wings2 user-reported successful flash; post-Wings2 full SPI readback remains pending.',
 'candidate_sha256':digest(candidate),'expected_after_vendor_sha256':digest(expected),'package_sha256':digest(normal),'vendor_sha256':VENDOR,'module_sha256':digest(module),'helper_sha256':digest(helper),'prior_UART_qualification_sha256':digest((ROOT/'build/uart-fix-private/qualification.json').read_bytes()),
 'rootfs_compressed_bytes':len(gz),'rootfs_slot_bytes':slot,'rootfs_margin_bytes':slot-len(gz),'rootfs_bytes':len(revised),'existing_cpio_changed':['init.project.rc'],'added_cpio':list(added),'showlogo_sha256':digest(logo_bytes),'static_bitmap_sha256':digest(candidate[0x8854:0x9e854]),
 'kernel_DT_boot_instructions_static_bitmap_showlogo_preserved':True,'other_flash_bytes_exact_except_rootfs_and_length':True,'expected_erased_blocks':[f'{i:06x}' for i in blocks],'expected_erase_count':len(blocks),'expected_page_count':len(blocks)*256,'vendor_metadata':[crc,dos],
 'files':{n:{'bytes':len(b),'sha256':digest(b)} for n,b in files.items()},'card_access':False,'physical_update':'PENDING','external_recovery_qualified':False}
 (out/'preparation.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':print(json.dumps(prepare(),indent=2))
