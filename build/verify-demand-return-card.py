"""Read-only I: identity verification after strict archived return collection."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,sys
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 a=json.loads((archive/'archive.json').read_text());assert a['card']=='I:' and a['fat_clean'] and a['card_writes']==0
 card=Path('I:/').resolve();assert str(card).lower() in ('i:/','i:\\')
 spec=importlib.util.spec_from_file_location('demand_return_guard',ROOT/'build/package-snes-1.19.py')
 guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
 checks={**guard.BOOT_EXPECTED,'retro/init':guard.baseline.HOOK,
 'retro/snes-mvp/plus-a7.so':'80b36f61971e4e649843ea23dc051cd185ba699c413ff9023c93f548e2c738b8'}
 inst=json.loads((ROOT/'evidence/2026-10-14/demand-gameplay/installation.json').read_text())
 checks['retro/snes-mvp/launch.sh']=inst['dispatch_sha256']
 for n in ('plus-a7.so','snes-mvp','launch.sh','suite-identity.json','TEST-ME.txt'):
  checks['retro/snes-demand-gameplay1/'+n]=inst['payload_hashes'][n]
 for n,h in checks.items():assert digest(card/n)==digest(archive/n)==h,n
 rom=digest(card/'002/Final Fantasy VI.zip');assert rom==inst['original_ROM_zip_sha256']
 assert not list((card/'retro').rglob('armed')) and not (card/'retro/update/Code.bkp').exists()
 marker=(card/'retro/snes-demand-gameplay1/last-launch').read_bytes()
 assert marker==(archive/'retro/snes-demand-gameplay1/last-launch').read_bytes()==b'SNES demand-gameplay1 experimental manual qualification; separate core/saves\n'
 result={'card':'I:','card_writes':0,'live_and_archived_identity_match':True,'protected_hashes':checks,
 'original_ROM_zip_sha256':rom,'marker_consumed':True,'firmware_trigger_absent':True}
 (archive/'demand-live-readback.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'passed':True,'card_writes':0,'identity_files':len(checks),'ROM_unchanged':True,'marker_consumed':True}))
if __name__=='__main__':main(Path(sys.argv[1]))
