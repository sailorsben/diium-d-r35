"""Qualify exact pre-kernel Wings2 rollback from current kernel image; RAM only."""
from pathlib import Path
from hashlib import sha256
import json,io,zipfile,zlib,struct,subprocess,os
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'device-evidence/battery-rollback1'
OLD=ROOT/'device-evidence/vesper-wings-firmware-20261015'
CURRENT=ROOT/'device-evidence/uart-kernel-firmware1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def main():
 assert not OUT.exists();OUT.mkdir();checks=[];logs=[]
 p=json.loads((OLD/'preparation.json').read_text());q=json.loads((OLD/'qualification.json').read_text());assert q['ram_result_matches_vendor_mutated_candidate'] and digest(OLD/'preparation.json')==q['preparation_sha256']
 for n,h in q['sources'].items():assert digest(ROOT/n)==h,n
 for name,key in [('candidate.bin','candidate_sha256'),('expected-after-vendor.bin','expected_after_vendor_sha256'),('fixture-compatible.bkp','package_sha256')]:assert digest(OLD/name)==p[key]
 package=(OLD/'fixture-compatible.bkp').read_bytes();assert package[:3]==b'WQW'
 with zipfile.ZipFile(io.BytesIO(package[3:])) as z:assert z.testzip() is None and z.namelist()==['SPI_ROM.bin'] and z.read('SPI_ROM.bin')==(OLD/'candidate.bin').read_bytes()
 checks.append('Exact original Wings2 WQW/ZIP/candidate/expected image and original qualification hashes')
 old=(OLD/'expected-after-vendor.bin').read_bytes();current=(CURRENT/'expected-after-vendor.bin').read_bytes();assert sha256(current).hexdigest()=='ef69753afb56c84e4daaf78aa3fad5551d26b7438e49f4f1dbc7312b11e07321'
 assert old[:0x100]==current[:0x100] and old[0x108:0xc0078]==current[0x108:0xc0078] and old[0x301d10:]==current[0x301d10:];checks.append('Only kernel section and vendor CRC/date differ; both screens/rootfs/DT/section table exact')
 kernel=zlib.decompress(old[0xc0078+0x48b8:0x301d10],31);assert sha256(kernel).hexdigest()=='21cc93e3f621c410ebe4174c0ab00aa4f0b21887c1698bbe974ffbeead2f0321'
 module=ROOT/'build/uart-fix-private';uq=json.loads((module/'qualification.json').read_text());assert uq['all_checks_passed'] and len(uq['module_checks'])==18 and len(uq['helper_cases'])==16
 for n,h in uq['sources'].items():assert digest(ROOT/n)==h,n
 for n,h in uq['payloads'].items():assert digest(module/'package'/n)==h,n
 guards=json.loads((module/'prepared.json').read_text());assert guards['kernel_sha256']==sha256(kernel).hexdigest()
 for g in guards['guards']:
  data=kernel[g['address']-0xc0008000:g['address']-0xc0008000+g['bytes']];assert sha256(data).hexdigest()==g['sha256'] and zlib.crc32(data)==g['crc32']
 checks.append('Restored original kernel matches every proven card module code/ABI guard; qualified module/helper/init/wrapper exact')
 def run(args,want=0):
  r=subprocess.run((['wsl','--exec'] if os.name=='nt' else [])+args,cwd=ROOT,capture_output=True,timeout=90);assert r.returncode==want,(args,r.returncode,r.stdout,r.stderr);text=r.stdout.decode();logs.append(text);return text
 for name,libs in [('check-vendor-updater',['-ldl']),('check-static-splash',[]),('check-boot-loader',[])]:run(['arm-linux-gnueabihf-gcc','-mcpu=cortex-a7','-marm','-O2','-Wall','-Wextra','-Werror','-fno-delete-null-pointer-checks','-no-pie','-Wl,-Ttext-segment=0x10000000','build/'+name+'.c',*libs,'-o',rel(OUT/name)])
 arm=['qemu-arm','-cpu','cortex-a7','-L','/usr/arm-linux-gnueabihf'];vendor=ROOT/'device-evidence/survey-return-20261009T180632Z/full-readable-card/files/retro/vrtemu';assert digest(vendor)==p['vendor_sha256']
 text=run(arm+[rel(OUT/'check-vendor-updater'),rel(vendor),rel(CURRENT/'expected-after-vendor.bin'),rel(OLD/'expected-after-vendor.bin'),rel(OLD/'fixture-compatible.bkp'),'1']);assert text.startswith('PASS ');checks.append('Actual ARM vendor updater accepts rollback from current kernel flash and produces exact original Wings2 image in RAM')
 for label,start,fixture in [('incompatible',CURRENT/'expected-after-vendor.bin','fixture-incompatible.bkp'),('CRC error',CURRENT/'expected-after-vendor.bin','fixture-consistent-bad-crc.bkp'),('prefix absent',CURRENT/'expected-after-vendor.bin','fixture-missing-prefix.bkp'),('repeat',OLD/'expected-after-vendor.bin','fixture-compatible.bkp')]:
  text=run(arm+[rel(OUT/'check-vendor-updater'),rel(vendor),rel(start),rel(OLD/'expected-after-vendor.bin'),rel(OLD/fixture),'0']);assert text.startswith('PASS ');checks.append('Updater refuses '+label+' without programming')
 for name in ['check-static-splash','check-boot-loader']:
  text=run(arm+['-B','0x40000000',rel(OUT/name),rel(OLD/'candidate.bin')]);assert text.startswith('PASS ');checks.append('Original ARM '+name+' accepts rollback image')
 shell=['qemu-arm','-0','busybox','-L','build/sysroot','build/uart-fix-private/firmware-busybox','sh']
 for name in ['init','launch.sh']:run(shell+['-n',rel(module/'package'/name)])
 checks.append('Exact firmware shell syntax for restored proven init and card UART wrapper')
 (OUT/'execution.txt').write_text(''.join(logs),encoding='utf-8')
 result={'version':'battery-kernel-rollback1','passed':True,'checks':checks,'package_path':rel(OLD/'fixture-compatible.bkp'),'package_sha256':p['package_sha256'],'candidate_sha256':p['candidate_sha256'],'expected_after_vendor_sha256':p['expected_after_vendor_sha256'],'restored_kernel_sha256':sha256(kernel).hexdigest(),'current_flash_sha256':sha256(current).hexdigest(),'card_UART_payloads':uq['payloads'],'module_qualification_sha256':digest(module/'qualification.json'),'original_Wings2_qualification_sha256':digest(OLD/'qualification.json'),'execution_sha256':digest(OUT/'execution.txt'),'sources':{n:digest(ROOT/n) for n in ['build/prepare-battery-rollback.py','build/check-vendor-updater.c','build/check-static-splash.c','build/check-boot-loader.c']},'rootfs_both_screens_preserved':True,'no_full_backup':True,'physical_flash':'PENDING','battery_cause_or_repair':'UNPROVEN; rollback is a controlled diagnostic, not a confirmed repair'}
 (OUT/'qualification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'checks':len(checks),'package_sha256':p['package_sha256'],'qualification':rel(OUT/'qualification.json')}))
if __name__=='__main__':main()
