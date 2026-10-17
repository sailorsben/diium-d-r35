"""Original ARM driver/decompressor/loader/updater qualification; RAM only."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,os,subprocess,struct
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'device-evidence/uart-kernel-firmware1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def rel(p):return p.resolve().relative_to(ROOT).as_posix()
def run(args,want=0):
 p=subprocess.run((['wsl','--exec'] if os.name=='nt' else [])+args,cwd=ROOT,capture_output=True,timeout=60)
 assert p.returncode==want,(args,p.returncode,p.stdout.decode(errors='replace'),p.stderr.decode(errors='replace'))
 return p.stdout.decode()
def main():
 p=json.loads((OUT/'preparation.json').read_text());checks=[];logs=[]
 for n,v in p['files'].items():assert digest(OUT/n)==v['sha256'],n
 base=ROOT/'device-evidence/vesper-wings-firmware-20261015/expected-after-vendor.bin';b=base.read_bytes();candidate=(OUT/'candidate.bin').read_bytes();assert digest(base)==p['baseline_sha256']
 assert candidate[:0xc0078]==b[:0xc0078] and candidate[0x301d10:]==b[0x301d10:];checks.append('All non-kernel flash bytes exact, both screens/rootfs/DT/section table preserved')
 kernel=(OUT/'kernel.bin').read_bytes();old=(ROOT/'device-evidence/uart-kernel-offline/kernel.bin').read_bytes()
 for a,z in [(0xc01177dc,0xc0117804),(0xc0117818,0xc01178d8),(0xc0117990,0xc0117a00)]:assert kernel[a-0xc0008000:z-0xc0008000]==old[a-0xc0008000:z-0xc0008000]
 checks.append('Original ISR entry, RX body and RX error/urgent tails exact')
 assert subprocess.run((['wsl','--exec'] if os.name=='nt' else [])+['gzip','-dc',rel(OUT/'kernel.gzip')],capture_output=True,check=True).stdout==kernel;checks.append('Independent GNU gzip expands all corrected kernel bytes')
 helpers=ROOT/'build/uart-kernel-check';helpers.mkdir(exist_ok=True)
 for name,libs in [('check-static-splash',[]),('check-boot-loader',[]),('check-vendor-updater',['-ldl']),('check-kernel-decompressor',[])]:
  run(['arm-linux-gnueabihf-gcc','-mcpu=cortex-a7','-marm','-O2','-Wall','-Wextra','-Werror','-fno-delete-null-pointer-checks','-no-pie','-Wl,-Ttext-segment=0x10000000','build/'+name+'.c',*libs,'-o',rel(helpers/name)])
 run(['arm-linux-gnueabihf-gcc','-mcpu=cortex-a7','-marm','-O2','-Wall','-Wextra','-Werror','-no-pie','-static','build/check-uart-kernel-driver.c','-o',rel(helpers/'driver')])
 text=run(['qemu-arm','-cpu','cortex-a7',rel(helpers/'driver'),'device-evidence/uart-kernel-offline/kernel.bin',rel(OUT/'kernel.bin')]);assert '7344 independent' in text and 'all256 byte' in text;checks.extend(text.strip().splitlines());logs.append(text)
 q=['qemu-arm','-cpu','cortex-a7','-L','/usr/arm-linux-gnueabihf']
 baselinez=helpers/'baseline.zImage';baselinez.write_bytes(b[0xc0078:0x301d10])
 for label,z,k in [('baseline',baselinez,ROOT/'device-evidence/uart-kernel-offline/kernel.bin'),('corrected',OUT/'zImage.bin',OUT/'kernel.bin')]:
  text=run(q+['-B','0x40000000',rel(helpers/'check-kernel-decompressor'),rel(z),rel(k)]);assert text.startswith('PASS ');checks.append('Captured ARM self-decompressor complete equality: '+label);logs.append(text)
 # Reproduce the unsupported-header negative even from a fresh build directory.
 gzip=(OUT/'kernel.gzip').read_bytes();end=gzip.index(b'\0',10)+1;head=bytearray(gzip[:10]);head[3]=4
 negative=head+struct.pack('<H',end-12)+b'\0'*(end-12)+gzip[end:];assert len(negative)==len(gzip)
 bad=bytearray(baselinez.read_bytes());bad[0x48b8:0x48b8+len(negative)]=negative;badz=helpers/'rejected-fextra.zImage';badz.write_bytes(bad)
 run(q+['-B','0x40000000',rel(helpers/'check-kernel-decompressor'),rel(badz),rel(OUT/'kernel.bin')],4);checks.append('Negative FEXTRA stream fails actual decompressor byte equality; FNAME supported')
 for image in [base,OUT/'candidate.bin']:
  for helper in ['check-static-splash','check-boot-loader']:
   text=run(q+['-B','0x40000000',rel(helpers/helper),rel(image)]);assert text.startswith('PASS ');checks.append(helper+': '+image.name);logs.append(text)
 vendor=ROOT/'device-evidence/survey-return-20261009T180632Z/full-readable-card/files/retro/vrtemu';assert digest(vendor)=='8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72'
 modulebase=ROOT/'device-evidence/uart-firmware1/expected-after-vendor.bin'
 for label,baseline,package,want in [('compatible Wings2',base,'fixture-compatible.bkp',1),('compatible prior module firmware',modulebase,'fixture-compatible.bkp',1),('incompatible',base,'fixture-incompatible.bkp',0),('CRC error',base,'fixture-consistent-bad-crc.bkp',0),('prefix absent',base,'fixture-missing-prefix.bkp',0),('repeated CRC',OUT/'fixture-already-recorded-baseline.bin','fixture-compatible.bkp',0)]:
  text=run(q+[rel(helpers/'check-vendor-updater'),rel(vendor),rel(baseline),rel(OUT/'candidate.bin'),rel(OUT/package),str(want)]);assert text.startswith('PASS ') and f'accepted={want}' in text
  if want and baseline==base:assert f"erases={p['expected_erase_count']} pages={p['expected_page_count']}" in text and 'erased_blocks='+','.join(p['expected_erased_blocks']) in text
  if want:assert 'metadata=%08x/%08x'%tuple(p['vendor_metadata']) in text
  else:assert 'erases=0 pages=0' in text
  checks.append('Captured updater RAM-only: '+label);logs.append(text)
 s=importlib.util.spec_from_file_location('inspect',ROOT/'build/inspect-spi-boot.py');inspect=importlib.util.module_from_spec(s);s.loader.exec_module(inspect)
 size=struct.unpack_from('<I',candidate,0xc0040)[0];cpio,_=inspect.gunzip(candidate[0x301d10:0x301d10+size]);entries=inspect.newc(cpio)
 assert not any(e['name'].startswith('d35-uart') for e in entries)
 logo=next(e for e in entries if e['name']=='showlogo');lp=helpers/'showlogo';lp.write_bytes(cpio[logo['data_offset']:logo['data_offset']+logo['bytes']])
 text=run(['sh','build/check-stock-boot.sh',rel(lp),'releases/vesper-wings-2/ui.raw']);checks.append('Original showlogo ZIP decoder and all18 Wings2 frames');logs.append(text)
 sh=['qemu-arm','-0','busybox','-L','build/sysroot','build/uart-fix-private/firmware-busybox','sh'];run(sh+['-n',rel(OUT/'normal-init')]);checks.append('Exact firmware shell validates original normal card init, no UART hook')
 assert digest(OUT/'normal-init')=='b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7'
 sources=['build/uart-kernel-tx.S','build/uart-kernel-tx.ld','build/prepare-uart-kernel-firmware.py','build/qualify-uart-kernel-firmware.py','build/check-uart-kernel-driver.c','build/check-uart-tx-observer.c','build/check-kernel-decompressor.c','build/check-static-splash.c','build/check-boot-loader.c','build/check-vendor-updater.c','build/check-stock-boot.c','build/check-stock-boot.sh','build/inspect-spi-boot.py']
 (OUT/'execution.txt').write_text(''.join(logs))
 report={'version':'uart-kernel1','passed':True,'checks':checks,'preparation_sha256':digest(OUT/'preparation.json'),'execution_sha256':digest(OUT/'execution.txt'),'sources':{n:digest(ROOT/n) for n in sources},'candidate_sha256':p['candidate_sha256'],'package_sha256':p['package_sha256'],'expected_after_vendor_sha256':p['expected_after_vendor_sha256'],'physical_boot':'PENDING','runtime_modules_or_IRQ_hooks':False,'external_recovery_qualified':False,'negative_results':['FEXTRA valid to GNU gzip but unsupported by the exact vendor kernel decompressor; retained negative stream and metadata.','Initial TX assembly relied on caller-clobbered r3 surviving PutChar; independent wrapper exposed it. Final assembly reloads ring tail and all7344 cases pass.'],'limits':p['limits']}
 (OUT/'qualification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'checks':len(checks),'qualification':str(OUT/'qualification.json')}))
if __name__=='__main__':main()
