"""Execute persistent ARM module/helper and actual firmware shell before release."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,os,shutil,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/uart-fix-private'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def load(n):
 s=importlib.util.spec_from_file_location(n,ROOT/'build'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def rel(p):return p.relative_to(ROOT).as_posix()
def run(args):
 if args[:2]==['qemu-arm','build/uart-fix-private/module-fixture']:
  with (OUT/'live-execution.txt').open('w') as f:
   p=subprocess.run((['wsl','--exec'] if os.name=='nt' else [])+args,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,text=True,timeout=60)
  p.stdout=(OUT/'live-execution.txt').read_text();p.stderr='';return p
 p=subprocess.run((['wsl','--exec'] if os.name=='nt' else [])+args,cwd=ROOT,capture_output=True,text=True,timeout=90)
 return p
def checked(args):
 p=run(args);assert p.returncode==0,(args,p.returncode,p.stdout,p.stderr);return p.stdout
def main():
 base=load('check-uart-tx-observer.py');base.OUT=OUT;base.inspect_abi()
 from elftools.elf.elffile import ELFFile
 # Derive local stats address from independent allocated-section layout.
 with (OUT/'d35_uart_tx.ko').open('rb') as f:
  e=ELFFile(f);cursor=0;addresses={}
  for i,s in enumerate(e.iter_sections()):
   if s['sh_flags']&2:
    a=max(4,s['sh_addralign']);cursor=(cursor+a-1)&~(a-1);addresses[i]=0x1000000+cursor;cursor+=s['sh_size']
  s=e.get_section_by_name('.symtab').get_symbol_by_name('stats')[0];stats=addresses[s['st_shndx']]+s['st_value']
 fixture=(ROOT/'build/check-uart-tx-observer.c').read_text()
 start=fixture.index('    reset_hw(0,0,0);for(unsigned i=0;i<200010;')
 end=fixture.index('    puts("UART TX compiled checks passed',start)
 fixture=fixture[:start]+'''    *(unsigned *)STATS_ADDRESS=199998u;
    for(unsigned i=0;i<32;i++) {
      reset_hw(0x531f,2,1);
      assert(call_checked((void *)(uintptr_t)word(action,0),19,(void *)PORT)==1);
      assert(word(state,0xbc)==1);
    }
    show();assert(field("calls")==200030 && field("bypass")==0 && field("writes")==32);
    puts("corrected pending services cross former200000 cutoff and continue without bypass");
    *(unsigned *)STATS_ADDRESS=0xfffffffeu;
    for(unsigned i=0;i<4;i++){reset_hw(0x531f,2,1);assert(call_checked((void *)(uintptr_t)word(action,0),19,(void *)PORT)==1 && word(state,0xbc)==1);}
    show();assert(field("calls")==2 && field("bypass")==0);
    detach();stop();assert(!refs && word(action,0)==ISR);
    puts("unsigned call counter wrap does not disable service; explicit detach still restores and drains");
'''.replace('STATS_ADDRESS',hex(stats))+fixture[end:]
 fixture=fixture.replace('assert(argc==7);','setbuf(stdout,NULL);assert(argc==7);')
 (OUT/'module-fixture.c').write_text(fixture,encoding='utf-8',newline='\n')
 binary=OUT/'module-fixture'
 checked(['arm-linux-gnueabihf-gcc','-O2','-Wall','-Wextra','-Werror','-marm','-no-pie','-static',rel(OUT/'module-fixture.c'),'-o',rel(binary)])
 relocated=base.relocate(binary)
 log=checked(['qemu-arm',rel(binary),'device-evidence/uart-kernel-offline/kernel.bin',rel(OUT/'observer-flat.bin'),hex(relocated['entry_points']['init_module']),hex(relocated['entry_points']['cleanup_module']),rel(OUT/'observer-unrelocated.bin'),rel(OUT/'observer-meta.bin')])
 (OUT/'execution.txt').write_text(log);module_checks=log.splitlines()[:-1];assert len(module_checks)==18
 helper=OUT/'helper-fixture'
 checked(['arm-linux-gnueabihf-gcc','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-marm','-no-pie','-static','-fno-stack-protector','-U_TIME_BITS','-D_TIME_BITS=32','-U_FILE_OFFSET_BITS','-D_FILE_OFFSET_BITS=32','build/uart-fix-boot.c','build/uart-fix-boot-fixture.c',*['-Wl,--wrap='+n for n in ['geteuid','uname','access','open','close','read','syscall']],'-o',rel(helper)])
 cases=[]
 for mode,want in [('normal',0),('nonroot',1),('kernel',1),('existing',64),('missing',1),('load',1),('refuse',1),('status',1),('on_read',1),('off_read',64),('off_refuse',64),('unload',64),('fault',1),('capped',1),('stop_normal',0),('stop_refuse',64)]:
  p=run(['env','FIX_CASE='+mode,'qemu-arm',rel(helper),'stop' if mode.startswith('stop_') else 'start','fixture.ko']);assert p.returncode==want,(mode,p.returncode,p.stderr);cases.append(mode)
 with (OUT/'uart-fix-boot').open('rb') as f:
  e=ELFFile(f);assert e.elfclass==32 and e['e_machine']=='EM_ARM' and e['e_flags']&0x400
  versions={a.name for _,aux in e.get_section_by_name('.gnu.version_r').iter_versions() for a in aux};assert 'GLIBC_2.4' in versions and versions<={'GLIBC_2.4','GCC_3.5'},versions
 shell=OUT/'firmware-busybox';shutil.copyfile(ROOT/'build/uart-tx-private/firmware-busybox',shell)
 assert digest(shell)=='6f974778b29d96a7e825b04c526b0e2948ec4f8497ac5558cb5b4d713f058e2f'
 sh=['qemu-arm','-0','busybox','-L','build/sysroot',rel(shell),'sh']
 for p in [ROOT/'build/launch-uart-fix.sh',OUT/'init']:checked(sh+['-n',rel(p)])
 # Actual shell execution; fixed device paths substituted only in private fixture.
 wrapper=(ROOT/'build/launch-uart-fix.sh').read_text();case=OUT/'shell-case';case.mkdir(exist_ok=True)
 local=wrapper.replace('BASE=/usr/retro/uart-fix1','BASE='+rel(case)).replace('/tmp/d35-uart-fix.log',rel(case/'ram.log'))
 (case/'launch.sh').write_text(local,encoding='utf-8',newline='\n');(case/'d35_uart_tx.ko').write_bytes(b'fixture')
 counter=case/'runs';counter.write_text('')
 (case/'uart-fix-boot').write_text('#!/bin/sh\nprintf x >> '+rel(counter)+'\nexit "$FIX_EXIT"\n',encoding='utf-8',newline='\n')
 checked(['chmod','+x',rel(case/'uart-fix-boot')])
 disabled=case/'disabled'
 if disabled.exists():disabled.unlink()
 for code in [0,0,1,64,127]:
  p=run(['env','FIX_EXIT='+str(code),*sh,rel(case/'launch.sh')]);assert p.returncode==(0 if code in [0,1] else 64),(code,p.stderr)
 assert counter.read_text()=='xxxxx'
 disabled.write_bytes(b'rollback\n');checked(sh+[rel(case/'launch.sh')]);assert counter.read_text()=='xxxxx'
 disabled.unlink();(case/'d35_uart_tx.ko').unlink();checked(sh+[rel(case/'launch.sh')]);assert counter.read_text()=='xxxxx'
 # Boot seam keeps automatic fix ahead of both stock and one-shot test dispatch.
 init=(OUT/'init').read_text();assert init.index('/usr/retro/uart-fix1/launch.sh')<init.index('/usr/retro/snes-mvp/armed')<init.index('  /usr/retro/main &')
 # Execute the actual startup prefix through stock launch, with only device
 # paths/processes replaced. The unrelated delayed display logger is excluded.
 boot=case/'retro';(boot/'uart-fix1').mkdir(parents=True,exist_ok=True);(boot/'snes-mvp').mkdir(exist_ok=True)
 events=case/'events'
 for n,body in [('main','printf "main\\n"'),('ldpath_launcher',':'),('uart-fix1/launch.sh','printf "fix\\n"; exit "$FIX_EXIT"'),('snes-mvp/launch.sh','printf "test\\n"')]:
  (boot/n).write_text('#!/bin/sh\n{ '+body+'; } >> '+rel(events)+'\n',encoding='utf-8',newline='\n')
  checked(['chmod','+x',rel(boot/n)])
 (boot/'snes-mvp/armed').write_bytes(b'fixture marker')
 prefix=init.split('# --- Delayed, background-only logger')[0]
 prefix=prefix.replace('/usr/retro',rel(boot)).replace('/bin/sh '+rel(boot),' '.join(sh)+' '+rel(boot))
 (case/'init-seam.sh').write_text(prefix+'\nwait\n',encoding='utf-8',newline='\n')
 for code in [0,64]:
  events.write_text('');p=run(['env','FIX_EXIT='+str(code),*sh,rel(case/'init-seam.sh')])
  assert p.returncode==code and events.read_text().splitlines()==(['fix','test','main'] if code==0 else ['fix']),(code,p.returncode,events.read_text(),p.stderr)
 package=OUT/'package';package.mkdir(exist_ok=True)
 for src,n in [(OUT/'d35_uart_tx.ko','d35_uart_tx.ko'),(OUT/'uart-fix-boot','uart-fix-boot'),(ROOT/'build/launch-uart-fix.sh','launch.sh'),(OUT/'init','init')]:shutil.copyfile(src,package/n)
 sources=['build/uart-tx-observer.c','build/check-uart-tx-observer.c','build/check-uart-tx-observer.py','build/prepare-uart-tx.py','build/prepare-uart-fix.py','build/build-uart-fix.sh','build/uart-fix-boot.c','build/uart-fix-boot-fixture.c','build/launch-uart-fix.sh','build/check-uart-fix.py']
 q={'version':'uart-fix1','module_checks':module_checks,'helper_cases':cases,'shell_checks':['exact firmware syntax: wrapper/init','every invocation runs fix without armed marker','safe load failure continues stock','uncertain ownership/exec failure withholds stock','disabled skips helper','missing module skips helper','fix before test and stock','executed init startup: fix/test/main order and failure barrier'],
 'sources':{n:digest(ROOT/n) for n in sources},'payloads':{p.name:digest(p) for p in package.iterdir()},'preparation_sha256':digest(OUT/'preparation.json'),'kernel_guard_sha256':digest(OUT/'prepared.json'),
 'all_checks_passed':True,'physical_persistent_boot':'PENDING','physical_sustained_gameplay':'PENDING','card_access':False,'firmware_flash_required':False,'automatic_every_boot':True,'cutoff':False,'resident_userspace_processes':0}
 (OUT/'qualification.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q,indent=2))
if __name__=='__main__':main()
