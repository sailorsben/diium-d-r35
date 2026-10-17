"""Validate fresh powered repeat against its exact staged file inventory."""
from pathlib import Path
import importlib.util,json,sys
ROOT=Path(__file__).resolve().parent.parent
FIRST=ROOT/'device-evidence/uart-kernel-return-20261017T022201466502Z'
def analyze(archive):
 s=importlib.util.spec_from_file_location('prior',ROOT/'build/analyze-uart-kernel-verify-return.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);v=m.analyze(archive)
 prior=json.loads((FIRST/'analysis.json').read_text());assert v['boot_id']!=prior['boot_id'],'Stale boot'
 install=json.loads((FIRST/'repeat-installation.json').read_text());a=json.loads((archive/'archive.json').read_text());o=json.loads((archive/'outside-retro.json').read_text());entries={e['path']:e['sha256'] for e in a['all_retro_files']+o['files']};expected=install['expected_files']
 changes={n:entries.get(n) for n,h in expected.items() if entries.get(n)!=h};assert set(changes)=={'retro/swapfile','retro/uart-kernel-verify1/armed'},changes
 extra=set(entries)-set(expected);base='retro/uart-kernel-verify1/'
 assert extra and all(n in [base+'consumed',base+'wrapper.log'] or n.startswith(base+'logs/') or n.startswith(base+'results/') for n in extra),extra
 assert entries[base+'consumed']==expected[base+'armed']
 v.update({'powered_repeat':True,'repeat_attempt_id':install['attempt_id'],'fresh_boot_verified':True,'all_prior_run_outputs_unchanged':True,'protected_staged_files_unchanged':len(expected)-2,'repeat_expected_changes':changes,'new_run_output_files':len(extra),'user_observation':'Completed plugged in and stayed on at stock.','stock_stability_on_external_power_user_accepted':True,'shutdown_cause':'Previous shutdown remains unproven; stable powered repeat supports low battery as a possible cause.','first_run_IRQ_brackets':[w['IRQ19_per_second_bracket'] for w in prior['windows']]})
 return v
if __name__=='__main__':
 p=Path(sys.argv[1]).resolve();assert p.is_relative_to(ROOT/'device-evidence');v=analyze(p);(p/'powered-analysis.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
