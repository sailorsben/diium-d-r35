"""Restore only original normal init after accepted, archived powered return."""
from pathlib import Path
import importlib.util,json,sys
from attempt_archive import digest,verify_saved
ROOT=Path(__file__).resolve().parent.parent
NORMAL='b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7'
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 s=importlib.util.spec_from_file_location('fix',ROOT/'build/install-uart-fix.py');fix=importlib.util.module_from_spec(s);s.loader.exec_module(fix)
 assert not fix.git('status','--porcelain');commit=fix.git('rev-parse','HEAD');assert commit==fix.git('rev-parse','origin/codex/snes-mvp-foundation')
 v=json.loads((archive/'powered-analysis.json').read_text());assert v['complete'] and v['powered_repeat'] and v['fresh_boot_verified'] and v['idle_IRQ_flood_acceptance_passed']
 a=json.loads((archive/'archive.json').read_text());o=json.loads((archive/'outside-retro.json').read_text());assert a['fat_clean'];verify_saved(archive,a)
 card=Path('I:/');expected={e['path']:e['sha256'] for e in a['all_retro_files']+o['files']}
 original=ROOT/'device-evidence/uart-kernel-firmware1/normal-init';assert digest(original)==NORMAL
 installed=json.loads((ROOT/'evidence/2026-10-16/uart-kernel-verification/installation.json').read_text());assert expected['retro/init']==installed['init_sha256']
 for n,h in expected.items():assert digest(card/n)==h,n
 assert {p.relative_to(card).as_posix() for p in card.rglob('*') if p.is_file()}==set(expected)
 assert not list(card.rglob('armed')) and not list(card.rglob('Code.bkp'));fix.health(archive,'restore-before')
 fix.atomic(card/'retro/init',original.read_bytes());expected['retro/init']=NORMAL
 for n,h in expected.items():assert digest(card/n)==h,n
 assert {p.relative_to(card).as_posix() for p in card.rglob('*') if p.is_file()}==set(expected)
 assert not list(card.rglob('armed')) and not list(card.rglob('Code.bkp'));fix.health(archive,'restore-after')
 r={'source_commit':commit,'archive':archive.name,'normal_init_restored_sha256':NORMAL,'only_changed_path':'retro/init','protected_files_unchanged':len(expected)-1,'all_file_count':len(expected),'all_probe_results_retained':True,'no_armed_tests':True,'no_update_trigger':True,'FAT_clean':True,'no_full_backup':True}
 (archive/'restoration.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if __name__=='__main__':main(Path(sys.argv[1]))
