"""Direct exact-image kernel driver correction. No module, hook or card I/O."""
from pathlib import Path
from hashlib import sha256
import importlib.util,io,json,os,struct,subprocess,zipfile,zlib
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'device-evidence/uart-kernel-firmware1'
BASELINE='5c2f34e6b4451b27fa5e6782f1396d8e6a3bf485e24c0fe209b44854f77660c3'
def digest(b):return sha256(b).hexdigest()
def run(args):subprocess.run((['wsl','--exec'] if os.name=='nt' else [])+args,cwd=ROOT,check=True,capture_output=True,timeout=60)
def main(replace_generated=False):
 if OUT.exists():
  assert replace_generated
  old=json.loads((OUT/'preparation.json').read_text())
  for n,v in old['files'].items():assert digest((OUT/n).read_bytes())==v['sha256'] and (OUT/n).stat().st_nlink==1
  rejected=OUT/'rejected-fextra'
  if rejected.exists():
   note=OUT/('rejected-kernel-'+old['kernel_corrected_sha256'][:12]);note.mkdir(exist_ok=True)
   (note/'preparation.json').write_bytes((OUT/'preparation.json').read_bytes())
   oldkernel=(OUT/'kernel.bin').read_bytes();(note/'patch-regions.bin').write_bytes(b''.join(oldkernel[int(x['address'],16)-0xc0008000:int(x['address'],16)-0xc0008000+x['bytes']] for x in old['patches']))
  else:
   rejected.mkdir();(rejected/'preparation.json').write_bytes((OUT/'preparation.json').read_bytes());(rejected/'kernel.gzip').write_bytes((OUT/'kernel.gzip').read_bytes())
 baseline=(ROOT/'device-evidence/vesper-wings-firmware-20261015/expected-after-vendor.bin').read_bytes();assert digest(baseline)==BASELINE
 zimage=baseline[0xc0078:0x301d10];dec=zlib.decompressobj(31);kernel=dec.decompress(zimage[0x48b8:]);used=len(zimage)-0x48b8-len(dec.unused_data)
 assert len(kernel)==7476028 and digest(kernel)=='21cc93e3f621c410ebe4174c0ab00aa4f0b21887c1698bbe974ffbeead2f0321'
 assert used==2347942 and len(zimage)==0x241c98
 run(['arm-linux-gnueabihf-gcc','-c','-mcpu=cortex-a7','-marm','build/uart-kernel-tx.S','-o','build/uart-kernel-tx.o'])
 run(['arm-linux-gnueabihf-ld','-T','build/uart-kernel-tx.ld','build/uart-kernel-tx.o','-o','build/uart-kernel-tx.elf'])
 for section,name in [('.tx','tx'),('.stop','stop')]:run(['arm-linux-gnueabihf-objcopy','-O','binary','--only-section='+section,'build/uart-kernel-tx.elf','build/uart-kernel-'+name+'.bin'])
 fixed=bytearray(kernel);patches=[(0xc01178d8,(ROOT/'build/uart-kernel-tx.bin').read_bytes()),(0xc0117a00,(ROOT/'build/uart-kernel-stop.bin').read_bytes()),(0xc0117804,struct.pack('<I',0xe3150901)),(0xc0117308,struct.pack('<I',0xe1a03001))]
 assert [len(v) for _,v in patches]==[184,12,4,4]
 for addr,payload in patches:fixed[addr-0xc0008000:addr-0xc0008000+len(payload)]=payload
 changed={i for i,(a,b) in enumerate(zip(kernel,fixed)) if a!=b};assert changed and all(any(addr-0xc0008000<=i<addr-0xc0008000+len(data) for addr,data in patches) for i in changed)
 # Preserve input_data/input_data_end and the original zImage length/relocation
 # metadata. FNAME fills the space gained by recompression, keeping the gzip
 # ISIZE at its original address used by head.S before decompression.
 c=zlib.compressobj(9,zlib.DEFLATED,-15);raw=c.compress(fixed)+c.flush();size=10+len(raw)+8;extra=used-size;assert extra>16
 header=bytearray(zimage[0x48b8:0x48c2]);assert header[3]==0;header[3]=8
 prefix=b'D35-UART-kernel1';name=prefix+b'.'*(extra-len(prefix)-1)+b'\0'
 gz=header+name+raw+struct.pack('<II',zlib.crc32(fixed),len(fixed));assert len(gz)==used and zlib.decompress(gz,31)==fixed
 newz=zimage[:0x48b8]+gz+zimage[0x48b8+used:];assert len(newz)==len(zimage) and newz[-58:]==zimage[-58:]
 image=bytearray(baseline);image[0xc0078:0x301d10]=newz
 assert image[:0xc0078]==baseline[:0xc0078] and image[0x301d10:]==baseline[0x301d10:]
 # Remove only the old card UART hook. All one-shot/stock/logging startup stays.
 init=(ROOT/'build/uart-fix-private/package/init').read_bytes();hook=(b'  # Persistent UART TX correction; independent of the one-shot dispatcher.\n'
 b'  if [ -f /usr/retro/uart-fix1/launch.sh ]; then\n    /bin/sh /usr/retro/uart-fix1/launch.sh || exit 64\n  fi\n')
 assert init.count(hook)==1;normal=init.replace(hook,b'');assert digest(normal)=='b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7'
 def package(data):
  stream=io.BytesIO();info=zipfile.ZipInfo('SPI_ROM.bin',(2026,10,16,13,0,0));info.compress_type=zipfile.ZIP_DEFLATED
  with zipfile.ZipFile(stream,'w') as z:z.writestr(info,data,compresslevel=9)
  return b'WQW'+stream.getvalue()
 good=package(image);crc=zlib.crc32(image);dos=((2026-1980)<<25)|(10<<21)|(16<<16)|(13<<11);expected=bytearray(image);struct.pack_into('<II',expected,0x100,crc,dos)
 wrong=bytearray(image);struct.pack_into('<I',wrong,0x108,struct.unpack_from('<I',image,0x108)[0]+10)
 bad=bytearray(good);bad[bad.index(b'PK\x01\x02')+16]^=1;bad[17]^=1;repeated=bytearray(baseline);struct.pack_into('<I',repeated,0x100,crc)
 files={'kernel.bin':fixed,'zImage.bin':newz,'kernel.gzip':gz,'candidate.bin':image,'expected-after-vendor.bin':expected,'normal-init':normal,'fixture-compatible.bkp':good,'fixture-incompatible.bkp':package(wrong),'fixture-consistent-bad-crc.bkp':bad,'fixture-missing-prefix.bkp':good[3:],'fixture-already-recorded-baseline.bin':repeated}
 OUT.mkdir(exist_ok=True)
 for n,v in files.items():(OUT/n).write_bytes(v)
 blocks=[i for i in range(0,len(image),65536) if expected[i:i+65536]!=baseline[i:i+65536]]
 report={'version':'uart-kernel1','baseline_sha256':BASELINE,'candidate_sha256':digest(image),'expected_after_vendor_sha256':digest(expected),'package_sha256':digest(good),'kernel_original_sha256':digest(kernel),'kernel_corrected_sha256':digest(fixed),
 'patches':[{'address':hex(a),'bytes':len(v),'before_sha256':digest(kernel[a-0xc0008000:a-0xc0008000+len(v)]),'after_sha256':digest(v)} for a,v in patches],
 'kernel_changed_bytes':len(changed),'gzip_FNAME_bytes':extra,'zImage_wrapper_and_length_exact':True,'RX_instructions_and_IRQ_registration_exact':True,'rootfs_and_both_Vesper_screens_exact':True,'no_runtime_module_or_patch_hook':True,'vendor_metadata':[crc,dos],'expected_erased_blocks':[f'{i:06x}' for i in blocks],'expected_erase_count':len(blocks),'expected_page_count':len(blocks)*256,
 'files':{n:{'bytes':len(v),'sha256':digest(v)} for n,v in files.items()},'card_access':False,'physical_kernel_boot':'PENDING','limits':['Exact vendor binary kernel patched in place from owned assembly; not a full vendor-source kernel rebuild.','Correct data bytes and one-byte FIFO-bounded TX service require physical acceptance; wire output and A7 timing not proved offline.','Latest Wings2 baseline user accepted; full post-Wings2 SPI readback pending.']}
 (OUT/'preparation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
 import sys
 main('--replace-generated' in sys.argv)
