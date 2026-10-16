"""Exercise actual firmware wrapper guards with owned fake children; no I: access."""
from pathlib import Path
from hashlib import sha256
import json,os,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/render-pressure2-private'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 prefix=['wsl','--exec'] if os.name=='nt' else []
 def run(args):return subprocess.run(prefix+args,cwd=ROOT,capture_output=True,text=True,timeout=10)
 shell=['qemu-arm','-0','busybox','-L','build/sysroot','build/uart-fix-private/firmware-busybox','sh']
 root=OUT/'faults';assert not root.exists();root.mkdir();checks=[]
 for name in ['UART_absent','UART_fault','forced_and_UART_fault','unknown_child_exit']:
  base=root/name;base.mkdir();(base/'mvp').mkdir();(base/'proc').mkdir()
  valid='version=4 result=0 irq=19 attached=1 calls=0 fault=0 bypass=0 cap=0\n'
  if name!='UART_absent':(base/'proc/d35_uart_tx').write_text(valid.replace('fault=0','fault=1') if name=='UART_fault' else valid,encoding='utf-8',newline='\n')
  for p in [base/'armed',base/'mvp/armed']:p.write_bytes(b'owned fixture\n')
  script='#!/bin/sh\nprintf executed > '+(base/'executed').relative_to(ROOT).as_posix()+'\n'
  if name=='forced_and_UART_fault':script+='printf "version=4 result=0 irq=19 attached=1 calls=0 fault=1 bypass=0 cap=0\\n" > '+(base/'proc/d35_uart_tx').relative_to(ROOT).as_posix()+'\nexit 72\n'
  else:script+='exit 139\n'
  (base/'render-pressure').write_text(script,encoding='utf-8',newline='\n');assert run(['chmod','+x',(base/'render-pressure').relative_to(ROOT).as_posix()]).returncode==0
  args=['env','D35_LAB_BASE='+base.relative_to(ROOT).as_posix(),'D35_MVP_BASE='+(base/'mvp').relative_to(ROOT).as_posix(),'D35_LAB_PROC_ROOT='+(base/'proc').relative_to(ROOT).as_posix(),'D35_LAB_SPLASH_STOP='+(base/'stop').relative_to(ROOT).as_posix(),*shell,'build/render-pressure2-private/launch.sh']
  blocked=name in ['forced_and_UART_fault','unknown_child_exit'];r=run((['timeout','2'] if blocked else [])+args)
  assert r.returncode==(124 if blocked else 1),(name,r.returncode,r.stderr)
  assert not (base/'armed').exists() and not (base/'mvp/armed').exists()
  assert (base/'executed').exists()==blocked
  if blocked:assert any('deadline reached; reboot required' in p.read_text() for p in (base/'results').glob('*/wrapper.log'))
  checks.append(name)
 result={'passed':True,'checks':checks,'card_access':False,'physical_result':'PENDING','wrapper_sha256':digest(OUT/'launch.sh'),
 'source_sha256':digest(Path(__file__)),'qualification_sha256':digest(OUT/'qualification.json')}
 (OUT/'fault-qualification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
