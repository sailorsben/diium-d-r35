"""Publish aggregate cross-game findings; no ROMs, screenshots or private saves."""
from pathlib import Path
from hashlib import sha256
import json,re
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/multigame-private-v3'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 raw=json.loads((OUT/'result.json').read_text(encoding='utf-8'));runner=json.loads((OUT/'runner-result.json').read_text(encoding='utf-8'));assert len(raw['games'])==5 and len(runner['results'])==10
 for name,h in raw['source_hashes'].items():assert digest(ROOT/name)==h,name
 assert digest(ROOT/'build/check-multigame-runner.py')==runner['source_sha256']
 names=['Super Mario World (backup PAL copy)','Super Metroid (backup labeled Chinese translation)','F-Zero','Star Fox','Rendering Ranger R2']
 coverage=['Title, welcome, Yoshi\u2019s House and overworld; no normal course established.','Opening narrative and flashback scenes; no player-controlled Ceres/Zebes established.','Menus, race, crash/you-lost screen; no sustained successful racing established.','Boot prefix only; strict state comparison stops at frame150.','Black by inspected frame599 and remains black at sampled checkpoints through5999; no playable scene.']
 games=[]
 for g,name,scene in zip(raw['games'],names,coverage):
  assert digest(Path(g['backup_zip']))==g['zip_sha256'],'Backup changed'
  i=g['index'];folder=OUT/f'game-{i}';log=(folder/'run.log').read_text(encoding='utf-8');fps=float(re.search(r'AV fps=([\d.]+)',log)[1])
  for relative,h in g['artifacts'].items():assert digest(OUT/relative)==h,relative
  boots=[r for r in runner['results'] if r['game']==i];assert all(r['passed'] for r in boots)
  for r in boots:
   s=r['session'];assert s['audio_remaining_frames']==s['audio_cleared_frames']=='0'
   assert int(s['output_accepted_frames_including_priming'])==int(s['resampled_enqueued_frames'])+int(s['priming_silence_frames'])
   assert int(s['rendered_frames'])==int(s['video_submitted'])+int(s['presentation_skipped'])==600
  games.append({'name':name,'backup_zip_sha256':g['zip_sha256'],'ROM_sha256':g['ROM_sha256'],'ROM_bytes':g['ROM_bytes'],'header':g['headers'][0],
   'core_reported_refresh_hz':fps,'strict_equivalence_passed':g['passed'],'recorded_calls':g['recorded_calls'],'adjacent_picture_changes':g['changed_pictures'],'scene_observation':scene,
   'playability_accepted':False,'actual_runner_mock_boots':[{'policy':r['policy'],'passed':r['passed'],'calls':int(r['session']['runs']),'rendered':int(r['session']['rendered_frames']),'skipped':int(r['session']['presentation_skipped']),'remaining_audio_frames':int(r['session']['audio_remaining_frames']),'cleared_audio_frames':int(r['session']['audio_cleared_frames']),'log_sha256':r['log_sha256'],'session_sha256':r['session_sha256']} for r in boots],
   'artifacts':g['artifacts'],'last_log_lines':g['last_log_lines']})
 selflog=OUT/'starfox-self/run.log';rangerlog=OUT/'ranger-single/run.log';assert 'FAIL state frame=150' in selflog.read_text(encoding='utf-8')
 result={'version':'multigame1-review','fixed_emulator_claim_supported':False,'physical':False,'card_access':False,'card_writes':0,'full_backups_created':0,'candidate_core_sha256':raw['candidate_core_sha256'],'reference_core_sha256':raw['reference_core_sha256'],'actual_runner_sha256':runner['runner_sha256'],
  'strict_full_windows_passed':sum(g['passed'] for g in raw['games']),'strict_full_windows_planned':5,'strict_full_window_calls':6000,'strict_state_check_period':30,'actual_runner_mock_cells_passed':sum(r['passed'] for r in runner['results']),'actual_runner_mock_calls':6000,
  'games':games,'followups':{'Star_Fox_same_candidate_two_library_instances':{'result':'Same frame150 state divergence; not established as optimization-specific.','log_sha256':digest(selflog),'log_tail':selflog.read_text(encoding='utf-8').splitlines()[-4:],'serialized_difference_region':'FillRAM offsets0x4325/0x4326 (DMA channel2 transfer-size registers); retain as logical state differences, do not normalize away.'},'Rendering_Ranger_older_single_core':{'result':'Older plus-a7 core, cold boot600 calls then600 held-Start calls; inspected final image black.','core_sha256':digest(ROOT/'build/plus-a7-out/plus-a7.so'),'log_sha256':digest(rangerlog),'image_sha256':digest(OUT/'ranger-single/last.ppm')}},
  'private_result_sha256':digest(OUT/'result.json'),'private_runner_result_sha256':digest(OUT/'runner-result.json'),'source_hashes':{**raw['source_hashes'],'build/check-multigame-runner.py':runner['source_sha256'],'build/publish-multigame.py':digest(Path(__file__))},
  'limits':raw['limits']+runner['limits']+['Picture-change counts depend on reached scene and scripted inputs; they are not a game-wide native FPS census or permission to halve emulation ticks.','Rendering Ranger equivalence passes on matching black output; this is explicitly not a boot/playability pass.','State differences are not suppressed because identical output so far does not establish future equivalence.','No A7 throughput, real input, scanout cadence, speaker, or sustained gameplay qualification from these PC tests.'],
  'recommendation':'Retain UART, diagnostic shutdown and bounded FFVI presentation-recovery fixes. Do not claim the whole emulator fixed. Resolve Rendering Ranger boot and Star Fox state/determinism coverage, establish real gameplay fixtures, then run matched physical sustained tests at each ROM\u2019s reported timing.'}
 dest=ROOT/'evidence/2026-10-16/multigame';dest.mkdir(exist_ok=True);target=dest/'review.json';target.write_text(json.dumps(result,indent=2)+'\n');print('Published',target)
if __name__=='__main__':main()
