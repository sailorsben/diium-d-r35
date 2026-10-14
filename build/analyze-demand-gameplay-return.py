"""Reproduce demand-v3 manual-return analysis from immutable private archive."""
from pathlib import Path
from hashlib import sha256
import json,statistics,sys
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def kv(p):return dict(line.split('=',1) for line in p.read_text().splitlines() if '=' in line)
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 a=json.loads((archive/'archive.json').read_text());assert a['fat_clean'] and a['card_writes']==0
 for e in a['all_retro_files']:
  p=archive/e['path'];assert p.stat().st_size==e['bytes'] and digest(p)==e['sha256'],e['path']
 live=json.loads((archive/'demand-live-readback.json').read_text());assert live['live_and_archived_identity_match'] and live['card_writes']==0
 inst=json.loads((ROOT/'evidence/2026-10-14/demand-gameplay/installation.json').read_text())
 before=ROOT/'device-evidence'/inst['archive'];old=json.loads((before/'archive.json').read_text())
 changed=[];unchanged=0
 for e in old['all_retro_files']:
  if e['path']=='retro/snes-mvp/launch.sh':continue
  p=archive/e['path']
  if p.is_file() and digest(p)==e['sha256']:unchanged+=1
  else:changed.append(e['path'])
 # Stock can modify its swapfile; this is reported, never silently excluded.
 unexpected=[n for n in changed if n!='retro/swapfile']
 base=archive/'retro/snes-demand-gameplay1'
 for n in ('plus-a7.so','snes-mvp','launch.sh','suite-identity.json','TEST-ME.txt'):
  assert digest(base/n)==inst['payload_hashes'][n],n
 assert digest(archive/'retro/snes-mvp/launch.sh')==inst['dispatch_sha256']
 assert not list((archive/'retro').rglob('armed'))
 assert (base/'last-launch').read_bytes()==b'SNES demand-gameplay1 experimental manual qualification; separate core/saves\n'
 progress_report=kv(base/'last-progress.txt');s=kv(base/'saves/last-session.txt')
 report_deltas={k:[progress_report.get(k),s.get(k)] for k in sorted(s.keys()|progress_report.keys()) if s.get(k)!=progress_report.get(k)}
 assert set(report_deltas)<= {'checkpoint_kernel_ns','session_elapsed_ns','diagnostic_ram_writes','diagnostic_ram_write_ns'}
 assert int(s['checkpoint_kernel_ns'])>=int(progress_report['checkpoint_kernel_ns'])
 identity=json.loads((base/'suite-identity.json').read_text())
 assert s['core_crc32']==identity['core_crc32'] and int(s['core_bytes'])==identity['core_bytes'] and s['mock_backend']=='0'
 rows=[list(map(int,v.split(','))) for k,v in s.items() if k.startswith('frame_cost_') and k!='frame_cost_columns']
 samples=[list(map(int,v.split(','))) for k,v in s.items() if k.startswith('sample_cost_')]
 assert all(len(r)==10 for r in rows+samples)
 n=int(s['runs']);assert n>0
 log=(base/'startup.log').read_text();normal='process exited status=0 ready=yes' in log and 'display worker joined' in log and 'FreeVFB returned' in log
 rate=int(s['sink_rate']);deadline_ms=358416/21477272*1000;target_ms=deadline_ms*.8
 numeric=('runs','held','video_submitted','video_dupes','write_errors','xrun_count','pauses','snapshot_load_successes','snapshot_load_rejections','native_audio_frames','resampled_enqueued_frames','output_accepted_frames_including_priming','priming_silence_frames','audio_cleared_frames','audio_remaining_frames','device_cleared_frames_estimate','display_scaled','display_flipped','late_calls','max_lateness_ns','pcm_epoch','pcm_admissions','pcm_observations','pcm_playable_min_running_frames','pcm_admission_min_lead_frames','phase_profile_samples','diagnostic_ram_errors')
 totals={k:int(s[k]) for k in numeric}
 accepted=totals['output_accepted_frames_including_priming']-totals['priming_silence_frames']
 accounted=accepted==totals['resampled_enqueued_frames'] and totals['audio_remaining_frames']==totals['audio_cleared_frames']==0
 histogram={int(k.removeprefix('core_wall_bin_').removesuffix('ms')):int(v) for k,v in s.items() if k.startswith('core_wall_bin_')}
 assert sum(histogram.values())==n
 ordinary=[r for r in rows if not r[2]]
 def distribution(items,index):
  v=[r[index]/1e6 for r in items]
  return {'count':len(v),'mean_ms':statistics.mean(v),'min_ms':min(v),'max_ms':max(v)} if v else None
 timing={'session_seconds':int(s['session_elapsed_ns'])/1e9,'active_seconds':int(s['active_wall_ns'])/1e9,
 'active_calls_per_second':n/(int(s['active_wall_ns'])/1e9),'emulated_fps':float(s['fps']),
 'cycle_derived_deadline_ms':deadline_ms,'20_percent_target_ms':target_ms,
 'core_wall_mean_ms':int(s['core_wall_ns'])/n/1e6,'core_thread_CPU_mean_ms':int(s['core_thread_cpu_ns'])/n/1e6,
 'audio_worker_CPU_mean_ms':int(s['audio_worker_cpu_ns'])/n/1e6,'display_worker_CPU_mean_ms':int(s['display_worker_cpu_ns'])/n/1e6,
 'distinct_recorded_threads_CPU_mean_ms':sum(int(s[k]) for k in ('core_thread_cpu_ns','audio_worker_cpu_ns','display_worker_cpu_ns'))/n/1e6,
 'video_callback_mean_ms':int(s['video_callback_ns'])/n/1e6,'audio_callback_mean_ms':int(s['audio_callback_ns'])/n/1e6,
 'admission_wait_mean_ms':int(s['audio_space_wait_ns'])/n/1e6,'display_copy_total_ms':int(s['display_copy_ns'])/1e6,
 'display_copy_total_divided_by_calls_us':int(s['display_copy_ns'])/n/1e3,
 'core_wall_max_ms':int(s['max_run_ns'])/1e6,
 'ordinary_tail_wall':distribution(ordinary,3),'ordinary_tail_CPU':distribution(ordinary,4),'ordinary_tail_video_callback':distribution(ordinary,8),
 'sparse_PPU_CPU':distribution(samples,6),'sparse_APU_inclusive_CPU':distribution(samples,5),
 'sparse_sample_runs':[r[0] for r in samples],'ordinary_tail_runs':[r[0] for r in ordinary],
 'histogram_calls_definitely_over_cycle_deadline':sum(v for k,v in histogram.items() if k>deadline_ms),
 'histogram_calls_possibly_over_cycle_deadline':sum(v for k,v in histogram.items() if k+1>deadline_ms),
 'histogram_calls_definitely_over_20_percent_target':sum(v for k,v in histogram.items() if k>target_ms),
 'histogram_calls_possibly_over_20_percent_target':sum(v for k,v in histogram.items() if k+1>target_ms)}
 bias=int(s['pcm_appl_ptr'])-int(s['pcm_epoch_transferred_frames'])
 reserve={'reported_running_min_frames':int(s['pcm_playable_min_running_frames']),
 'reported_running_min_ms':int(s['pcm_playable_min_running_frames'])/rate*1000,
 'reported_admission_min_frames':int(s['pcm_admission_min_lead_frames']),
 'final_epoch_appl_minus_transferred_frames':bias,'final_epoch_appl_minus_hw_frames':int(s['pcm_appl_ptr'])-int(s['pcm_hw_ptr']),
 'final_pointer_arithmetic_matches_buffer_avail':int(s['pcm_appl_ptr'])-int(s['pcm_hw_ptr'])==int(s['pcm_buffer_frames'])-int(s['pcm_avail_frames']),
 'complete_effect_reserve_timeline_available':False,'physical_minimum_independently_certified':False}
 progress={n:('unchanged' if digest(base/n)==h else 'changed') for n,h in inst['payload_hashes'].items() if n.startswith('saves/')}
 faults=sorted(p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_file() and ('failure-' in p.name or 'pcm-fault' in p.name))
 limits=['Manual opening-scene run; user reports Confuser worked fine and cannot test Ultima/Holy/etc. No retained cast identities/input replay.',
 'Unmatched manual-session times cannot establish incremental demand-v3 savings or compare spell peaks with earlier controls.',
 'Distinct-thread CPU sum omits other main-thread work and OS/kernel/other processes; session average is not worst-effect 20 percent acceptance.',
 'Core wall time includes nested callbacks. APU-inclusive and callback times must not be added again.',
 'Eight sparse samples and24 recent calls do not preserve the complete spell/onset/recovery timeline; sampled overhead remains included.',
 'Reported reserve minimum is aggregate telemetry. Final pointer consistency does not independently validate all earlier observations.',
 'Direct submission count and copied payload bytes are not persisted by this runner. Small copy timer is consistent with direct output but not a measured direct-hit count.',
 'Display scale/flip totals include pause/menu draws; callbacks and completed flips do not establish visual correctness or broad coherency.',
 'Late_calls uses lateness greater than one period at admission, not each core-only overrun. Core histogram includes sampled calls and coarse1ms bins.']
 clean=normal and s['phase']=='finished' and not s['error'] and not s['pcm_error_detail'] and not faults and accounted and not unexpected
 clean=clean and totals['video_submitted']==n and totals['held']==totals['video_dupes']==totals['write_errors']==totals['xrun_count']==0
 result={'archive':archive.name,'card_writes':0,'FAT_clean':True,'archived_files':len(a['all_retro_files']),
 'archived_bytes':sum(e['bytes'] for e in a['all_retro_files']),'all_archive_hashes_verified':True,'candidate_and_stock_identity_verified':True,
 'marker_consumed':True,'stock_next_boot':True,'protected_prior_files_unchanged':unchanged,'changed_prior_files':changed,'unexpected_prior_changes':unexpected,
 'session_id':s['session_id'],'clean_observed_run':clean,'user_observation':'Opening scene only. Confuser worked fine. Cannot test Ultima, Holy, etc.',
 'effect_identity_from_logs':False,'orderly_exit_and_worker_join':normal,'phase':s['phase'],'error':s['error'],'PCM_error_detail':s['pcm_error_detail'],
 'fault_files':faults,'totals':totals,'accepted_nonpriming_PCM_frames':accepted,'software_PCM_accounting_exact':accounted,
 'final_report_vs_RAM_checkpoint_deltas':report_deltas,
 'native_frames_per_call':totals['native_audio_frames']/n,'timing':timing,'reserve':reserve,'test_progress':progress,
 'production_gate_passed':False,'incremental_A7_saving_measured':False,'broad_spell_coverage':False,'limits':limits,
 'input_hashes':{p.relative_to(ROOT).as_posix():digest(p) for p in (archive/'archive.json',archive/'demand-live-readback.json',base/'last-progress.txt',base/'saves/last-session.txt',base/'startup.log',base/'last-run.log',ROOT/'evidence/2026-10-14/demand-gameplay/installation.json',Path(__file__).resolve())}}
 (archive/'demand-gameplay-return-analysis.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main(Path(sys.argv[1]))
