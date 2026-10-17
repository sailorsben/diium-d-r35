"""Qualify exact private firmware, startup seams and vendor RAM-only update."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,os,subprocess,shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'device-evidence/uart-firmware1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def rel(p):return p.resolve().relative_to(ROOT).as_posix()
def run(args,want=0):
 p=subprocess.run((['wsl','--exec'] if os.name=='nt' else [])+args,cwd=ROOT,capture_output=True,timeout=60)
 assert p.returncode==want,(args,p.returncode,p.stdout.decode(errors='replace'),p.stderr.decode(errors='replace'))
 return p.stdout
def write(p,text):p.write_bytes(text.encode())
def main():
 p=json.loads((OUT/'preparation.json').read_text());checks=[];logs=[]
 for n,v in p['files'].items():assert digest(OUT/n)==v['sha256'],n
 baseline=ROOT/p['baseline_path'];assert digest(baseline)==p['baseline_sha256']
 assert run(['gzip','-dc',rel(OUT/'rootfs.cpio.gz')])==(OUT/'rootfs.cpio').read_bytes();checks.append('GNU gzip exact expansion')
 extracted={'init.project.rc':OUT/'init.project.rc','d35-uart/d35_uart_tx.ko':ROOT/'build/uart-fix-private/package/d35_uart_tx.ko','d35-uart/uart-fix-boot':ROOT/'build/uart-fix-private/package/uart-fix-boot','d35-uart/launch.sh':OUT/'firmware-launch.sh','showlogo':OUT/'showlogo'}
 for n,path in extracted.items():
  output=subprocess.run([shutil.which('tar'),'-xOf',str(OUT/'rootfs.cpio'),n],capture_output=True,check=True).stdout
  assert output==path.read_bytes();checks.append('Independent libarchive cpio extraction: '+n)
 helpers=ROOT/'build/uart-firmware-check';helpers.mkdir(exist_ok=True)
 for name,libs in [('check-static-splash',[]),('check-boot-loader',[]),('check-vendor-updater',['-ldl'])]:
  run(['arm-linux-gnueabihf-gcc','-mcpu=cortex-a7','-marm','-O2','-Wall','-Wextra','-Werror','-no-pie','-Wl,-Ttext-segment=0x10000000','build/'+name+'.c',*libs,'-o',rel(helpers/name)])
 q=['qemu-arm','-cpu','cortex-a7','-L','/usr/arm-linux-gnueabihf']
 for image in [baseline,OUT/'candidate.bin']:
  for helper in ['check-static-splash','check-boot-loader']:
   text=run(q+['-B','0x40000000',rel(helpers/helper),rel(image)]).decode();assert text.startswith('PASS ');checks.append(helper+': '+image.name);logs.append(text)
 vendor=ROOT/'device-evidence/survey-return-20261009T180632Z/full-readable-card/files/retro/vrtemu';assert digest(vendor)==p['vendor_sha256']
 for label,base,package,want in [('compatible',baseline,'fixture-compatible.bkp',1),('incompatible',baseline,'fixture-incompatible.bkp',0),('bad_crc',baseline,'fixture-consistent-bad-crc.bkp',0),('no_prefix',baseline,'fixture-missing-prefix.bkp',0),('repeated',OUT/'fixture-already-recorded-baseline.bin','fixture-compatible.bkp',0)]:
  text=run(q+[rel(helpers/'check-vendor-updater'),rel(vendor),rel(base),rel(OUT/'candidate.bin'),rel(OUT/package),str(want)]).decode();assert text.startswith('PASS ') and f'accepted={want}' in text
  if want:
   assert f"erases={p['expected_erase_count']} pages={p['expected_page_count']}" in text
   assert 'erased_blocks='+','.join(p['expected_erased_blocks']) in text and 'metadata=%08x/%08x'%tuple(p['vendor_metadata']) in text
  else:assert 'erases=0 pages=0' in text
  checks.append('Exact vendor updater RAM: '+label);logs.append(text)
 run(['sh','build/check-stock-boot.sh',rel(OUT/'showlogo'),'releases/vesper-wings-2/ui.raw']);checks.append('Exact showlogo ZIP decoder and all18 frames')
 shell=ROOT/'build/uart-fix-private/firmware-busybox';assert digest(shell)=='6f974778b29d96a7e825b04c526b0e2948ec4f8497ac5558cb5b4d713f058e2f'
 sh=['qemu-arm','-0','busybox','-L','build/sysroot',rel(shell),'sh']
 for n in ['firmware-launch.sh','card-launch.sh','init.project.rc']:run(sh+['-n',rel(OUT/n)])
 checks.append('Exact firmware BusyBox parses all startup scripts')
 case=helpers/'shell';case.mkdir(exist_ok=True);base=case/'internal';base.mkdir(exist_ok=True);card=case/'card';card.mkdir(exist_ok=True)
 ready=case/'ready';status=case/'status';log=case/'firmware.log';events=case/'events';disabled=card/'disabled'
 fw=(OUT/'firmware-launch.sh').read_text().replace('/tmp/d35-uart-firmware.ready',rel(ready)).replace('/tmp/d35-uart-firmware.log',rel(log)).replace('/d35-uart',rel(base)).replace('/proc/d35_uart_tx',rel(status)).replace('/usr/retro/uart-fix1',rel(card))
 fwpath=base/'launch.sh';write(fwpath,fw)
 helper=base/'uart-fix-boot';write(helper,'#!/bin/sh\nprintf "internal\\n" >> '+rel(events)+'\nexit "$FIX_EXIT"\n');run(['chmod','+x',rel(helper),rel(fwpath)])
 (card/'d35_uart_tx.ko').write_bytes(b'fixture');cardhelper=card/'uart-fix-boot';write(cardhelper,'#!/bin/sh\nprintf "card\\n" >> '+rel(events)+'\nexit "$CARD_EXIT"\n');run(['chmod','+x',rel(cardhelper)])
 cardtext=(OUT/'card-launch.sh').read_text().replace('/tmp/d35-uart-firmware.log',rel(log)).replace('/tmp/d35-uart-fix.log',rel(case/'card.log')).replace('/usr/retro/uart-fix1',rel(card)).replace('/d35-uart',rel(base)).replace('/bin/sh '+rel(fwpath),' '.join(sh)+' '+rel(fwpath))
 cardpath=case/'card-launch.sh';write(cardpath,cardtext)
 valid='version=4 result=0 irq=19 attached=1 calls=0 fault=0 bypass=0 cap=0\n'
 def reset():
  for f in [ready,status,disabled]:f.unlink(missing_ok=True)
  events.write_text('')
 def invoke(path,arg='',code=0,card_code=0,want=0):return run(['env','FIX_EXIT='+str(code),'CARD_EXIT='+str(card_code),*sh,rel(path),*([arg] if arg else [])],want)
 for code,want in [(0,0),(1,0),(64,64),(127,64)]:
  reset();write(status,valid);invoke(fwpath,'start',code,want=want);assert ready.exists()==(code==0);checks.append('Firmware start helper result '+str(code))
 reset();write(status,valid);invoke(fwpath,'start');invoke(fwpath,'verify');invoke(cardpath);assert events.read_text().splitlines()==['internal'];checks.append('Firmware active/card startup verifies owner without duplicate load')
 write(ready,'wrong\n');invoke(fwpath,'verify',want=64);invoke(cardpath,want=64);checks.append('Wrong owner identity withholds duplicate load and stock')
 reset();write(status,valid);invoke(fwpath,'verify',want=64);checks.append('Unowned active module refused')
 reset();invoke(fwpath,'verify',want=1);invoke(cardpath);assert events.read_text().splitlines()==['card'];checks.append('Firmware safe absence retains card fallback')
 for key in ['fault','bypass','cap']:
  reset();write(status,valid);invoke(fwpath,'start');write(status,valid.replace(key+'=0',key+'=1'));invoke(cardpath,want=64);checks.append('Firmware '+key+' status refuses adoption')
 reset();write(disabled,'bypass\n');invoke(fwpath,'start');invoke(cardpath);assert not events.read_text() and not ready.exists();checks.append('Explicit disabled switch bypasses both owners')
 reset();helper.rename(base/'helper-parked');invoke(fwpath,'start',want=64);(base/'helper-parked').rename(helper);checks.append('Missing internal helper withholds startup')
 # Execute the real post-mount project tail for both card and internal boot.
 tail=(OUT/'init.project.rc').read_text().split('# Internal UART correction,',1)[1];tail='# Internal UART correction,'+tail
 assert tail.index('/d35-uart/launch.sh start')<tail.index('/usr/retro/init &')<tail.index('/system/bin/vrtemu &')
 tail=tail.replace('/bin/sh /d35-uart/launch.sh',' '.join(sh)+' '+rel(fwpath)).replace('/usr/retro/init',rel(case/'card-init')).replace('/wdt &',': # wdt fixture').replace('modprobe joydev',': # modprobe fixture').replace('/system/bin/vrtemu &','printf "stock-internal\\n" >> '+rel(events)+' &')
 project=case/'project.sh';write(project,tail+'\nwait\n')
 cardinit=case/'card-init';write(cardinit,'#!/bin/sh\n'+' '.join(sh)+' '+rel(cardpath)+' || exit 64\nprintf "stock-card\\n" >> '+rel(events)+'\n');run(['chmod','+x',rel(cardinit)])
 for card_boot,code,want in [(True,0,0),(True,64,64),(False,0,0),(False,1,0)]:
  reset();write(status,valid)
  if not card_boot:cardinit.rename(case/'parked-init')
  invoke(project,code=code,want=want)
  expected=['internal']+([] if code==64 else ['stock-card' if card_boot else 'stock-internal'])
  assert events.read_text().splitlines()==expected,(card_boot,code,events.read_text())
  if not card_boot:(case/'parked-init').rename(cardinit)
  checks.append('Real project startup tail: card='+str(card_boot)+' helper='+str(code))
 # Reuse qualification only for identical physically used module/helper, with all source/payload hashes checked.
 spec=importlib.util.spec_from_file_location('old',ROOT/'build/install-uart-fix.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old);uart=old.artifacts()
 assert uart['payloads']['d35_uart_tx.ko']==p['module_sha256'] and uart['payloads']['uart-fix-boot']==p['helper_sha256'];checks.append('Exact previous18 module/16 helper qualification retained and hash-verified')
 sources=['build/prepare-uart-firmware.py','build/qualify-uart-firmware.py','build/launch-uart-firmware.sh','build/inspect-spi-boot.py','build/check-static-splash.c','build/check-boot-loader.c','build/check-vendor-updater.c','build/check-stock-boot.c','build/check-stock-boot.sh']
 (OUT/'execution.txt').write_text(''.join(logs))
 report={'version':'uart-firmware1','all_checks_passed':True,'checks':checks,'preparation_sha256':digest(OUT/'preparation.json'),'execution_sha256':digest(OUT/'execution.txt'),'sources':{n:digest(ROOT/n) for n in sources},'reused_UART_qualification_sha256':digest(ROOT/'build/uart-fix-private/qualification.json'),
 'baseline_sha256':p['baseline_sha256'],'candidate_sha256':p['candidate_sha256'],'expected_after_vendor_sha256':p['expected_after_vendor_sha256'],'package_sha256':p['package_sha256'],'ram_erase_blocks':p['expected_erase_count'],'ram_page_programs':p['expected_page_count'],
 'device_access':False,'physical_update':'PENDING','limits':['RAM-only updater simulation; no physical flashing, external recovery or kernel boot acceptance.','Latest Wings2 baseline is user-accepted expected image; post-Wings2 full readback pending.','Exact existing module/helper reused; early rootfs attachment requires physical boot verification.']}
 (OUT/'qualification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
