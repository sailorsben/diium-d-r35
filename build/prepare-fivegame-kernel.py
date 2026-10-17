"""Reuse exact matched five-game payload; qualify kernel-aware wrapper only."""
from pathlib import Path
from hashlib import sha256
import json,subprocess,os,shutil
ROOT=Path(__file__).resolve().parent.parent
OLD=ROOT/'build/fivegame-physical-private-v1'
OUT=ROOT/'build/fivegame-kernel-private-v1'
TARGET='retro/snes-fivegame-kernel1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 assert not (OUT/'qualification.json').exists();q=json.loads((OLD/'verification.json').read_text());assert q['passed'] and len(q['actual_epochs'])==20 and q['native_policies']==[0,1]
 for n,h in q['source_hashes'].items():assert digest(ROOT/n)==h,n
 for n,h in q['payload_hashes'].items():assert digest(OLD/n)==h,n
 for n,h in q['proof_hashes'].items():assert digest(OLD/n)==h,n
 assert digest(OLD/'abi.txt')==q['ABI_sha256']
 uart=ROOT/'build/uart-kernel-verify-private';uq=json.loads((uart/'qualification.json').read_text());assert uq['passed'] and digest(uart/'uart-observe')==uq['payload_hashes']['uart-observe']
 physical=json.loads((ROOT/'evidence/2026-10-16/uart-kernel-verification/powered-return.json').read_text());assert physical['two_pass_flash_exact'] and physical['idle_IRQ_flood_acceptance_passed']
 OUT.mkdir(exist_ok=True)
 fixtures=(OUT/'wrapper').resolve();assert fixtures.is_relative_to(ROOT.resolve()) and fixtures.parent==OUT.resolve() and fixtures.name=='wrapper'
 if fixtures.exists():shutil.rmtree(fixtures)
 for n in q['payload_hashes']:
  p=OUT/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(OLD/n,p)
 wrapper=(OLD/'launch.sh').read_text();start=wrapper.index('uart_check() {');end=wrapper.index('uart_check before',start)
 guard='''uart_check() {
  [ ! -e "$PROC/d35_uart_tx" ] || return 1
  [ ! -d "${D35_LAB_SYS_ROOT:-/sys}/module/d35_uart_tx" ] || return 1
  "$LAB/uart-observe" "${D35_LAB_ROOT:-/}" "$OUT/uart-$1" || return 1
  printf 'kernel_UART=1 runtime_patch=0 passive_observation=1\\n' > "$OUT/uart-$1.txt"
}
'''
 wrapper=wrapper[:start]+guard+wrapper[end:];wrapper=wrapper.replace('/usr/retro/snes-fivegame1','/usr/'+TARGET)
 (OUT/'launch.sh').write_text(wrapper,encoding='utf-8',newline='\n')
 (OUT/'dispatch.sh').write_text('#!/bin/sh\nexec /bin/sh /usr/'+TARGET+'/launch.sh\n',encoding='utf-8',newline='\n')
 (OUT/'ROM-PATH.txt').write_text('/usr/'+TARGET+'/cases/000/game.sfc\n',encoding='utf-8',newline='\n');shutil.copyfile(uart/'uart-observe',OUT/'uart-observe')
 changed={'launch.sh','dispatch.sh','ROM-PATH.txt'}
 for n,h in q['payload_hashes'].items():
  if n not in changed:assert digest(OUT/n)==h,n
 checks=[];shell=['qemu-arm','-0','busybox','-L','build/sysroot','build/uart-fix-private/firmware-busybox','sh']
 def rel(p):return p.relative_to(ROOT).as_posix()
 def run(args,want=0):
  r=subprocess.run((['wsl','--exec'] if os.name=='nt' else [])+args,cwd=ROOT,capture_output=True,timeout=15);assert r.returncode==want,(args,r.returncode,r.stdout,r.stderr);return r
 run(shell+['-n',rel(OUT/'launch.sh')]);checks.append('Exact firmware BusyBox syntax')
 for name in ['normal','module_endpoint','loaded_module','observer_before','observer_after','active_splash','child139','forced72']:
  d=OUT/'wrapper'/name;d.mkdir(parents=True);(d/'mvp').mkdir();(d/'proc').mkdir();(d/'sys').mkdir()
  for p in [d/'armed',d/'mvp/armed']:p.write_bytes(b'fixture\n')
  (d/'ROM-PATH.txt').write_text(rel(OUT/'cases/000/game.sfc')+'\n',newline='\n')
  (d/'uart-observe').write_text('#!/bin/sh\ncase "$2" in *uart-before) [ "'+name+'" = observer_before ] && exit 1;; *uart-after) [ "'+name+'" = observer_after ] && exit 1;; esac\nmkdir "$2"\n',newline='\n')
  code=139 if name=='child139' else 72 if name=='forced72' else 0
  (d/'fivegame-suite').write_text('#!/bin/sh\nprintf executed > '+rel(d/'executed')+'\nexit '+str(code)+'\n',newline='\n')
  run(['chmod','+x',rel(d/'uart-observe'),rel(d/'fivegame-suite')])
  if name=='module_endpoint':(d/'proc/d35_uart_tx').write_text('old endpoint')
  if name=='loaded_module':(d/'sys/module/d35_uart_tx').mkdir(parents=True)
  if name=='active_splash':
   (d/'proc/123').mkdir();(d/'proc/123/comm').write_text('showlogo\n',newline='\n');(d/'proc/123/status').write_text('State:\tS\n',newline='\n')
  args=['env','D35_LAB_BASE='+rel(d),'D35_MVP_BASE='+rel(d/'mvp'),'D35_LAB_PROC_ROOT='+rel(d/'proc'),'D35_LAB_SYS_ROOT='+rel(d/'sys'),'D35_LAB_SPLASH_STOP='+rel(d/'stop'),*shell,rel(OUT/'launch.sh')]
  blocked=name in ['child139','forced72'];want=124 if blocked else 1 if name not in ['normal'] else 0
  run((['timeout','2'] if blocked else [])+args,want)
  assert not (d/'armed').exists() and not (d/'mvp/armed').exists()
  assert (d/'executed').exists()==(name in ['normal','observer_after','child139','forced72'])
  if name=='normal':run(args);assert len(list((d/'results').glob('run-*')))==1
  if blocked:assert any('reboot required' in p.read_text() for p in (d/'results').glob('*/wrapper.log'))
  checks.append(name)
 payload={n:digest(OUT/n) for n in [*q['payload_hashes'],'uart-observe']}
 result={'version':'fivegame-kernel1','passed':True,'measurement_only':True,'production_gate':False,'target':TARGET,'unchanged_measured_payloads':{n:h for n,h in q['payload_hashes'].items() if n not in changed},'previous_qualification_sha256':digest(OLD/'verification.json'),'previous_actual_epochs':q['actual_epochs'],'checks':checks,'passive_observer_sha256':digest(OUT/'uart-observe'),'kernel_physical_receipt_sha256':digest(ROOT/'evidence/2026-10-16/uart-kernel-verification/powered-return.json'),'sources':{'build/prepare-fivegame-kernel.py':digest(Path(__file__))},'payload_hashes':payload,'no_full_backup':True,'physical_result':'PENDING'}
 (OUT/'qualification.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS exact 20-epoch measured payload reused;9 kernel wrapper checks;no card writes')
if __name__=='__main__':main()
