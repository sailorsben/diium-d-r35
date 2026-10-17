"""Rearm unchanged qualified probe; rename completed output, never overwrite it."""
from pathlib import Path
import importlib.util,json,sys,uuid
from attempt_archive import digest,verify_saved
ROOT=Path(__file__).resolve().parent.parent
BASE='retro/uart-kernel-verify1'
def load(name):
 s=importlib.util.spec_from_file_location('fix',ROOT/'build'/name);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 fix=load('install-uart-fix.py');assert not fix.git('status','--porcelain');commit=fix.git('rev-parse','HEAD');assert commit==fix.git('rev-parse','origin/codex/snes-mvp-foundation')
 a=json.loads((archive/'archive.json').read_text());o=json.loads((archive/'outside-retro.json').read_text());assert a['fat_clean'];verify_saved(archive,a)
 entries=a['all_retro_files']+o['files'];expected={e['path']:e['sha256'] for e in entries};card=Path('I:/');base=card/BASE
 assert not list(card.rglob('armed')) and not list(card.rglob('Code.bkp'))
 installed=json.loads((ROOT/'evidence/2026-10-16/uart-kernel-verification/installation.json').read_text())
 assert expected['retro/init']==installed['init_sha256']
 for name,h in installed['payload_hashes'].items():assert expected[BASE+'/'+name]==h
 assert (base/'consumed').read_bytes()==(ROOT/'build/uart-kernel-verify-private/armed').read_bytes()
 assert 'verification_exit=0 owned_reader_reaped=1' in (archive/BASE/'wrapper.log').read_text()
 for n,h in expected.items():assert digest(card/n)==h,n
 assert {p.relative_to(card).as_posix() for p in card.rglob('*') if p.is_file()}==set(expected)
 fix.health(archive,'repeat-before')
 attempt=uuid.uuid4().hex;history=base/('completed-'+attempt);assert not history.exists();history.mkdir()
 moved={}
 for name in ['logs','results','wrapper.log','consumed']:
  source=base/name;assert source.exists();source.rename(history/name)
  for n,h in list(expected.items()):
   if n==BASE+'/'+name or n.startswith(BASE+'/'+name+'/'):
    new=BASE+'/'+history.name+'/'+n[len(BASE)+1:];moved[n]=new;expected[new]=expected.pop(n)
 marker=(ROOT/'build/uart-kernel-verify-private/armed').read_bytes()
 # Preserve exact qualified payload/installation/run marker. The repeat has a
 # separate receipt and prior output directory; fresh output cannot be stale.
 try:
  for n,h in expected.items():assert digest(card/n)==h,n
  fix.health(archive,'repeat-preserved')
  fix.atomic(base/'armed',marker);expected[BASE+'/armed']=digest(base/'armed')
  assert {p.relative_to(card).as_posix() for p in card.rglob('*') if p.is_file()}==set(expected)
  assert sorted(p.relative_to(card).as_posix() for p in card.rglob('armed'))==[BASE+'/armed']
  assert not list(card.rglob('Code.bkp'));fix.health(archive,'repeat-armed')
 except BaseException:
  if (base/'armed').exists():assert (base/'armed').read_bytes()==marker;(base/'armed').unlink()
  raise
 report={'source_commit':commit,'attempt_id':attempt,'archive':archive.name,'read_only_probe_armed':True,'unchanged_qualified_payloads':True,'reused_qualified_run_id':json.loads((base/'installation.json').read_text())['run_id'],'fresh_output_required':True,'previous_outputs_renamed':moved,'all_existing_files_hash_verified':len(entries),'saves_and_prior_evidence_preserved':True,'no_full_backup':True,'firmware_update_absent':True,'FAT_clean':True,'expected_files':expected}
 (archive/'repeat-installation.json').write_text(json.dumps(report,indent=2)+'\n');print('Armed repeat',attempt,'preserved',len(entries),'files')
if __name__=='__main__':main(Path(sys.argv[1]))
