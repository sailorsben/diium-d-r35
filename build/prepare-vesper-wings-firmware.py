"""Prepare and qualify Wings2 firmware privately; never access a device/card."""
from pathlib import Path
from hashlib import sha256
import argparse, importlib.util, io, json, os, shutil, struct, subprocess, zipfile, zlib
ROOT=Path(__file__).resolve().parent.parent
BASELINE='509cdc305deca2654fbf48184eb16d523b4b6cae0effffc4a3cba6845622d9fd'
VENDOR='8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72'
DATE=(2026,10,15,12,0,0)

def digest(b): return sha256(b).hexdigest()
def load(name):
 spec=importlib.util.spec_from_file_location(name,ROOT/'build'/name);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def prepare(out):
 out=out.resolve();private=(ROOT/'device-evidence').resolve()
 if not out.is_relative_to(private) or out==private or out.exists():raise ValueError('Fresh private output required')
 baseline=(private/'vesper-static-qualified-20261010/expected-after-vendor.bin').read_bytes()
 assert len(baseline)==8388608 and digest(baseline)==BASELINE
 physical=json.loads((ROOT/'evidence/2026-10-10/vesper-static-verification/flash-comparison.json').read_text())
 assert physical['full_image_matches'] and physical['pass_sha256']==[BASELINE,BASELINE]
 inspect=load('inspect-spi-boot.py');start,slot,field=0x301d10,3406558,0xc0040
 size=struct.unpack_from('<I',baseline,field)[0];compressed=baseline[start:start+size]
 cpio,used=inspect.gunzip(compressed);assert used==size
 entries=inspect.newc(cpio);logo=next(e for e in entries if e['name']=='showlogo')
 assert logo['sha256']=='ab56a67ae629e816a5752b1ad7cec2c335b46c82df84856f8a41376d2f919ebe'
 art=ROOT/'releases/vesper-wings-2';am=json.loads((art/'manifest.json').read_text())
 for name,h in am['assets'].items():assert digest((art/name).read_bytes())==h
 for name,h in am['sources'].items():assert digest((ROOT/name).read_bytes())==h
 encoded=(art/'logo.zip').read_bytes();assert len(encoded)==141940
 lo,hi=logo['data_offset']+0x7180,logo['data_offset']+0x29bf4
 revised=cpio[:lo]+encoded+cpio[hi:]
 assert len(revised)==len(cpio) and revised[:lo]==cpio[:lo] and revised[hi:]==cpio[hi:]
 after=inspect.newc(revised);assert [a['name'] for a,b in zip(entries,after) if a!=b]==['showlogo']
 replacement=revised[logo['data_offset']:logo['data_offset']+logo['bytes']]
 assert digest(replacement)==am['private_patched_executable_sha256']
 compressor=zlib.compressobj(9,zlib.DEFLATED,-15)
 gz=compressed[:10]+compressor.compress(revised)+compressor.flush()+struct.pack('<II',zlib.crc32(revised),len(revised))
 assert len(gz)<=slot and inspect.gunzip(gz)==(revised,len(gz))
 candidate=bytearray(baseline);struct.pack_into('<I',candidate,field,len(gz))
 candidate[start:start+slot]=gz+b'\xff'*(slot-len(gz))
 assert len(candidate)==len(baseline)
 assert candidate[:field]==baseline[:field] and candidate[field+4:start]==baseline[field+4:start] and candidate[start+slot:]==baseline[start+slot:]
 assert candidate[0x8854:0x9e854]==baseline[0x8854:0x9e854]
 def package(data):
  stream=io.BytesIO();info=zipfile.ZipInfo('SPI_ROM.bin',DATE);info.compress_type=zipfile.ZIP_DEFLATED
  with zipfile.ZipFile(stream,'w') as z:z.writestr(info,data,compresslevel=9)
  return b'WQW'+stream.getvalue()
 crc=zlib.crc32(candidate);dos=((DATE[0]-1980)<<25)|(DATE[1]<<21)|(DATE[2]<<16)|(DATE[3]<<11)
 expected=bytearray(candidate);struct.pack_into('<II',expected,0x100,crc,dos)
 normal=package(candidate);incompatible=bytearray(candidate);struct.pack_into('<I',incompatible,0x108,struct.unpack_from('<I',candidate,0x108)[0]+10)
 bad=bytearray(normal);central=bad.index(b'PK\x01\x02');bad[central+16]^=1;bad[17]^=1
 already=bytearray(baseline);struct.pack_into('<I',already,0x100,crc)
 files={'baseline-installed.bin':baseline,'candidate.bin':candidate,'expected-after-vendor.bin':expected,
 'rootfs.cpio':revised,'rootfs.cpio.gz':gz,'showlogo-wings':replacement,'fixture-compatible.bkp':normal,
 'fixture-incompatible.bkp':package(incompatible),'fixture-consistent-bad-crc.bkp':bad,
 'fixture-missing-prefix.bkp':normal[3:],'fixture-already-recorded-baseline.bin':already}
 out.mkdir()
 for n,b in files.items():(out/n).write_bytes(b)
 blocks=[i for i in range(0,len(expected),65536) if expected[i:i+65536]!=baseline[i:i+65536]]
 report={'version':'vesper-wings-2-firmware','baseline_sha256':BASELINE,'candidate_sha256':digest(candidate),
 'expected_after_vendor_sha256':digest(expected),'package_sha256':digest(normal),'vendor_sha256':VENDOR,
 'rootfs_compressed_bytes':len(gz),'rootfs_slot_bytes':slot,'rootfs_bytes':len(revised),
 'static_bitmap_preserved':True,'only_rootfs_showlogo_zip_changed':True,'all_other_cpio_bytes_exact':True,
 'other_flash_bytes_exact_except_rootfs_and_length':True,'vendor_metadata':[crc,dos],
 'expected_erased_blocks':[f'{i:06x}' for i in blocks],'expected_erase_count':len(blocks),'expected_page_count':len(blocks)*256,
 'files':{n:{'sha256':digest(b),'bytes':len(b)} for n,b in files.items()},'card_access':False,'physical_update':'PENDING'}
 (out/'preparation.json').write_text(json.dumps(report,indent=2)+'\n')
 return report

def qualify(out):
 prep=json.loads((out/'preparation.json').read_text());prefix=['wsl','--exec'] if os.name=='nt' else []
 def run(args):
  p=subprocess.run(prefix+args,cwd=ROOT,capture_output=True,timeout=60);assert p.returncode==0,(args,p.stderr.decode(errors='replace'));return p.stdout
 def rel(p):return p.resolve().relative_to(ROOT).as_posix()
 for n,v in prep['files'].items():assert digest((out/n).read_bytes())==v['sha256']
 checks=[]
 expanded=run(['gzip','-dc',rel(out/'rootfs.cpio.gz')]);assert expanded==(out/'rootfs.cpio').read_bytes();checks.append('independent GNU gzip exact expansion')
 tar=shutil.which('tar');assert tar
 p=subprocess.run([tar,'-xOf',str(out/'rootfs.cpio'),'showlogo'],capture_output=True,check=True);assert p.stdout==(out/'showlogo-wings').read_bytes();checks.append('independent libarchive tar extracts exact new showlogo')
 helpers=ROOT/'build/wings-firmware-check';helpers.mkdir(exist_ok=True)
 for name,libs in [('check-static-splash',[]),('check-boot-loader',[]),('check-vendor-updater',['-ldl'])]:
  run(['arm-linux-gnueabihf-gcc','-mcpu=cortex-a7','-marm','-O2','-Wall','-Wextra','-Werror','-no-pie','-Wl,-Ttext-segment=0x10000000','build/'+name+'.c',*libs,'-o',rel(helpers/name)])
 q=['qemu-arm','-cpu','cortex-a7','-L','/usr/arm-linux-gnueabihf']
 logs=[]
 for file in ['baseline-installed.bin','candidate.bin']:
  for helper in ['check-static-splash','check-boot-loader']:
   text=run(q+['-B','0x40000000',rel(helpers/helper),rel(out/file)]).decode();assert text.startswith('PASS ');checks.append(helper+': '+file);logs.append(text)
 vendor=ROOT/'device-evidence/a7-pair-before-20261015T052954Z/retro/vrtemu';assert digest(vendor.read_bytes())==VENDOR
 for label,base,package,want in [('compatible','baseline-installed.bin','fixture-compatible.bkp',1),('incompatible','baseline-installed.bin','fixture-incompatible.bkp',0),('bad_crc','baseline-installed.bin','fixture-consistent-bad-crc.bkp',0),('no_prefix','baseline-installed.bin','fixture-missing-prefix.bkp',0),('repeated','fixture-already-recorded-baseline.bin','fixture-compatible.bkp',0)]:
  text=run(q+[rel(helpers/'check-vendor-updater'),rel(vendor),rel(out/base),rel(out/'candidate.bin'),rel(out/package),str(want)]).decode();assert text.startswith('PASS ') and f'accepted={want}' in text
  if want:
   assert f"erases={prep['expected_erase_count']} pages={prep['expected_page_count']}" in text
   assert 'erased_blocks='+','.join(prep['expected_erased_blocks']) in text
   assert 'metadata=%08x/%08x'%tuple(prep['vendor_metadata']) in text
  else:assert 'erases=0 pages=0' in text
  checks.append('exact vendor updater: '+label);logs.append(text)
 run(['sh','build/check-stock-boot.sh',rel(out/'showlogo-wings'),rel(ROOT/'releases/vesper-wings-2/ui.raw')]);checks.append('exact original ZIP decode and all18 ShowSprite frames')
 (out/'execution.txt').write_text(''.join(logs))
 result={'all_checks_passed':True,'checks':checks,'preparation_sha256':digest((out/'preparation.json').read_bytes()),
 'baseline_sha256':prep['baseline_sha256'],'candidate_sha256':prep['candidate_sha256'],'expected_after_vendor_sha256':prep['expected_after_vendor_sha256'],
 'package_sha256':prep['package_sha256'],'vendor_sha256':VENDOR,'ram_result_matches_vendor_mutated_candidate':True,
 'ram_erase_blocks':prep['expected_erase_count'],'ram_page_programs':prep['expected_page_count'],'device_access':False,
 'physical_update':'PENDING','sources':{n:digest((ROOT/n).read_bytes()) for n in ['build/prepare-vesper-wings-firmware.py','build/inspect-spi-boot.py','build/check-static-splash.c','build/check-boot-loader.c','build/check-vendor-updater.c','build/check-stock-boot.c','build/check-stock-boot.sh']}}
 (out/'qualification.json').write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args();print(json.dumps(prepare(a.output),indent=2));print(json.dumps(qualify(a.output.resolve()),indent=2))
