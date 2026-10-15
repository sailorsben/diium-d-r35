"""Persistent UART card-boot install/rollback. No SPI flash or one-shot arming.

Requires a fresh strict archive and clean FAT before any write. Commit and push
the exact qualified source first. Card must be powered off and mounted on I:.
"""
from pathlib import Path
from hashlib import sha256
import argparse,importlib.util,json,os,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/uart-fix-private'
ORIGINAL='b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7'
ROM='f61af2bd9e3f9b6a2bd543fb176af0b81fd9e5ba4ea0fa0f453371ccb45d3911'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT,text=True).strip()
def load(n):
 s=importlib.util.spec_from_file_location(n,ROOT/'build'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def atomic(p,b):
 tmp=p.with_name(p.name+'.uart-fix-tmp');assert not tmp.exists()
 with tmp.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 assert tmp.read_bytes()==b;os.replace(tmp,p);assert p.read_bytes()==b
def artifacts():
 q=json.loads((OUT/'qualification.json').read_text());assert q['all_checks_passed'] and len(q['module_checks'])==18 and len(q['helper_cases'])==16
 for n,h in q['sources'].items():assert digest(ROOT/n)==h,n
 for n,h in q['payloads'].items():assert digest(OUT/'package'/n)==h,n
 assert digest(OUT/'preparation.json')==q['preparation_sha256']
 assert digest(OUT/'prepared.json')==q['kernel_guard_sha256']
 return q
def stage(card,payload,original,inject=lambda _:None):
 """Filesystem transaction seam; activation is the last atomic rename."""
 target=card/'retro/uart-fix1';init=card/'retro/init'
 assert not target.exists() and init.read_bytes()==original
 target.mkdir();created=[]
 try:
  for n,b in payload.items():
   if n=='init':continue
   assert Path(n).name==n and n!='disabled'
   atomic(target/n,b);created.append(target/n)
  atomic(target/'original-init',original);created.append(target/'original-init')
  inject('before_activation')
  atomic(init,payload['init']);inject('after_activation')
 except BaseException:
  assert init.read_bytes() in (original,payload['init'])
  if init.read_bytes()!=original:atomic(init,original)
  # Keep staged artifacts for inspection after a partial copy. Original boot is
  # restored; never recursively delete paths or touch unrelated card content.
  raise
 return {n:sha256(b).hexdigest() for n,b in payload.items()}
def health(archive,label):
 r=subprocess.run(['chkdsk','I:'],capture_output=True,text=True)
 (archive/('chkdsk-uart-fix-'+label+'.txt')).write_text(r.stdout+r.stderr)
 assert r.returncode==0 and '11EB-1465' in r.stdout and 'Windows has scanned the file system and found no problems.' in r.stdout
def main(archive,rollback=False):
 q=artifacts();archive=archive.resolve();assert archive.is_relative_to((ROOT/'device-evidence').resolve())
 iq=json.loads((OUT/'installation-qualification.json').read_text())
 assert iq['all_checks_passed'] and len(iq['cases'])==5 and iq['qualification_sha256']==digest(OUT/'qualification.json')
 for n,h in iq['sources'].items():assert digest(ROOT/n)==h,n
 baseline=json.loads((archive/'archive.json').read_text());assert baseline['fat_clean'] and baseline['card_writes']==0
 assert not git('status','--porcelain') and git('branch','--show-current')=='codex/snes-mvp-foundation'
 commit=git('rev-parse','HEAD');assert commit==git('rev-parse','origin/codex/snes-mvp-foundation')
 card=Path('I:/').resolve();assert str(card).lower() in ('i:/','i:\\')
 assert not list((card/'retro').rglob('armed')) and not (card/'retro/update/Code.bkp').exists()
 for e in baseline['all_retro_files']:assert digest(card/e['path'])==e['sha256'],e['path']
 guard=load('package-snes-1.19.py')
 for n,h in guard.BOOT_EXPECTED.items():assert digest(card/n)==h,n
 assert digest(card/'002/Final Fantasy VI.zip')==ROM
 health(archive,'before')
 target=card/'retro/uart-fix1';init=card/'retro/init'
 if rollback:
  assert digest(init)==q['payloads']['init'] and digest(target/'original-init')==ORIGINAL
  # Offline card rollback takes effect on next boot. Powered-off RAM is gone.
  atomic(target/'disabled',b'UART fix disabled for rollback\n');atomic(init,(target/'original-init').read_bytes())
  assert digest(init)==ORIGINAL
 else:
  assert digest(init)==ORIGINAL and not target.exists()
  payload={n:(OUT/'package'/n).read_bytes() for n in q['payloads']}
  payload['qualification.json']=(OUT/'qualification.json').read_bytes()
  assert digest(init)==ORIGINAL
  # Reject altered preparation even if someone substituted a matching package.
  p=load('prepare-uart-fix.py');assert p.boot_init(init.read_bytes())==payload['init']
  stage(card,payload,init.read_bytes())
  for n,b in payload.items():assert (init if n=='init' else target/n).read_bytes()==b
 health(archive,'after')
 for e in baseline['all_retro_files']:
  if e['path']!='retro/init':assert digest(card/e['path'])==e['sha256'],e['path']
 assert digest(card/'002/Final Fantasy VI.zip')==ROM
 report={'version':'uart-fix1','source_commit':commit,'archive':archive.name,'rollback':rollback,
 'automatic_every_boot':not rollback,'one_shot_armed':False,'firmware_flash':False,'stock_ROM_progress_preserved':True,
 'init_sha256':digest(init),'qualification_sha256':digest(OUT/'qualification.json'),'physical_boot':'PENDING'}
 (archive/('uart-fix-rollback.json' if rollback else 'uart-fix-installation.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('--rollback',action='store_true');a=p.parse_args();main(a.archive,a.rollback)
