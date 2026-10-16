"""Publish compact fix/qualification receipts; keep games, states and pictures private."""
from pathlib import Path
from hashlib import sha256
import json,runpy,shutil,tempfile
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/multigame-fixes-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
 games=read(OUT/'gameplay-v2-result.json');ffvi=read(OUT/'ffvi-v2-result.json');runner=read(OUT/'runner-result.json');hdma=read(OUT/'hdma-check.json');core=OUT/'core/snes9x2005_plus_libretro.so';reference=OUT/'reference/snes9x2005_plus_libretro.so';h=digest(core)
 assert all(g['passed'] and g['recorded_calls']==g['calls'] for g in games['games']) and len(games['games'])==5
 assert len(ffvi['cases'])==18 and all(c['passed'] for c in ffvi['cases'])
 assert len(runner['results'])==10 and all(c['passed'] for c in runner['results'])
 assert games['candidate_sha256']==ffvi['candidate_sha256']==runner['core_sha256']==h
 assert games['reference_sha256']==ffvi['reference_sha256']==digest(reference)
 assert digest(ROOT/'build/qualify-five-gameplay.py')==games['source_sha256'];assert digest(ROOT/'build/check-multigame-ffvi.py')==ffvi['source_sha256'];assert digest(ROOT/'build/check-fixed-gameplay-runner.py')==runner['source_sha256']
 apply=runpy.run_path(str(ROOT/'build/prepare-multigame-fixes.py'))['apply_fixes'];proof={}
 # Reconstruct only the changed source files from immutable bases; no copy of
 # ROMs, binaries or full build trees. This catches diagnostic leftovers.
 with tempfile.TemporaryDirectory(dir=ROOT/'build',prefix='verify-game-fixes-') as name:
  for label,base in [('core','demand-visible-private-v3'),('reference','common-band-private-v3')]:
   d=Path(name)/label/'source';d.mkdir(parents=True);origin=ROOT/'build'/base/'core/source';names=['dma.c','apu_blargg.c','apu_blargg.h','memmap.c']
   if (origin/'a7_demand_output.h').exists():names+=['a7_demand_output.h']
   for n in names:shutil.copyfile(origin/n,d/n)
   apply(d.parent)
   for n in names:
    assert digest(d/n)==digest(OUT/label/'source'/n),(label,n)
    proof[label+'/'+n]={'before_sha256':digest(origin/n),'after_sha256':digest(d/n)}
 old=read(ROOT/'build/multigame-private-v3/inputs.json')
 for g in old:assert digest(Path(g['backup_zip']))==g['zip_sha256'],'Backup was modified'
 for case in games['games']:
  for relative,expected in case['artifacts'].items():assert digest(OUT/relative)==expected,relative
 fixtures=read(OUT/'gameplay-fixtures.json');names=['Super Mario World (PAL backup)','Super Metroid (translation-labeled backup)','F-Zero','Star Fox','Rendering Ranger R2']
 checked=[]
 for case in games['games']:
  i=case['game'];g=old[i];checked.append({**case,'name':names[i],'ROM_sha256':g['ROM_sha256'],'backup_zip_sha256':g['zip_sha256'],'actual_state_checks':(case['calls']+29)//30,'note':'Four gameplay snapshots; Star Fox uses complete cold boot because GSU snapshot continuation is not qualified.'})
 boots=[]
 for c in runner['results']:
  s=c['session'];boots.append({k:c[k] for k in ('game','policy','calls','passed','returncode','log_sha256','session_sha256')})
  boots[-1].update(native_samples=int(s['native_audio_frames']),enqueued=int(s['resampled_enqueued_frames']),accepted=int(s['output_accepted_frames_including_priming']),prime=int(s['priming_silence_frames']),remaining=int(s['audio_remaining_frames']),cleared=int(s['audio_cleared_frames']))
 rootcause={'Ranger':'CPU/SPC SYNC handshake loses acknowledgement at an instruction boundary. Ranger ID AVCJ now finishes the in-progress SPC instruction before CPU port writes; disabled/reset for other ROMs. No ROM edits or forced game-state jumps.',
  'Star_Fox_state':'HDMA termination redundantly adds a cached host-pointer difference to an already advanced logical indirect address. Remove it; retain actual DMA bytes in strict state comparisons.',
  'Star_Fox_pixels':'After the DMA fix, direct-target output fails at frame178 even against the same core; full-layout control passes. SuperFX now takes the established full-layout path. Presentation skipping remains independent; emulation/render/audio are retained.'}
 retained_logs={p.relative_to(OUT).as_posix():digest(p) for p in OUT.rglob('run.log')}
 recipes={p.relative_to(OUT).as_posix():p.read_text() for p in OUT.rglob('inputs.txt') if any(part.startswith(('play-','continue')) for part in p.parts)}
 result={'version':'five-gameplay-fixes1','passed':True,'physical':False,'production_gate':False,'card_access':False,'card_writes':0,'full_backups_created':0,'candidate_core_sha256':h,'reference_core_sha256':digest(reference),'candidate_bytes':core.stat().st_size,'root_causes_and_fixes':rootcause,'changed_sources':proof,
  'gameplay_comparisons':checked,'total_compared_calls':sum(g['calls'] for g in games['games']),'total_gameplay_calls':6000,'state_checks':sum((g['calls']+29)//30 for g in games['games']),
  'FFVI':ffvi,'frontend_mock_boots':boots,'HDMA_contract_cases':hdma,'recorded_input_recipes':recipes,'diagnostic_log_sha256':retained_logs,
  'raw_result_sha256':{p.name:digest(p) for p in [OUT/'gameplay-v2-result.json',OUT/'ffvi-v2-result.json',OUT/'runner-result.json',OUT/'hdma-check.json',OUT/'gameplay-result.json']},
  'source_sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in [ROOT/'build'/n for n in ('prepare-multigame-fixes.py','build-multigame-fixes.sh','explore-multigame.c','explore-five-games.py','qualify-five-gameplay.py','check-hdma-termination.py','check-multigame-ffvi.py','check-fixed-gameplay-runner.py','publish-gameplay-fixes.py')]},
  'limits':['QEMU/software compatibility only; new core is not installed or physically performance-qualified.','Reference shares the scoped APU/HDMA corrections; not an independent original-console accuracy oracle.','SuperFX uses full-layout callback copies, so its A7 cost/headroom must be measured.','Ranger port completion is a scoped instruction-level compatibility rule, not a cycle-perfect SPC timing claim.','Four inspected gameplay snapshots are private derived fixtures, not a claim of compatibility with older user save headers. Existing saves are untouched.','Star Fox GSU snapshot save/restore remains unqualified; its accepted test starts from cold boot.','The old harness prints floor(calls/30); actual state checks are at frame0,30,..., hence the public report uses ceil(calls/30).','Death/respawn in scripted gameplay is not a failure; level completion and sustained playability are not established.']}
 dest=ROOT/'evidence/2026-10-16/gameplay-fixes';dest.mkdir(exist_ok=True);(dest/'qualification.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS publication:',result['total_compared_calls'],'compared calls,',result['state_checks'],'state checks; all5 gameplay/all18 FFVI/all10 mock boots')
if __name__=='__main__':main()
