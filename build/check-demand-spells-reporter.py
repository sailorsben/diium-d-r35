"""Exercise the new reporter against actual controller output; never A7 timing."""
from pathlib import Path
import json,runpy,shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/demand-spells-private-v1'
def main():
 target=OUT/'mock/plan.json'
 if target.exists():assert target.read_bytes()==(OUT/'plan.json').read_bytes()
 else:shutil.copy2(OUT/'plan.json',target)
 reporter=runpy.run_path(str(ROOT/'build/report-demand-spells.py'))
 r=reporter['analyze'](OUT/'mock',True)
 assert not r['physical_result'] and len(r['epochs'])==40 and all(x['status']=='NOT_PHYSICAL' for x in r['epochs'])
 assert all(x['identity_verified'] and x['complete_window'] and x['effect_properties_observed'] and x['PCM_final_accounting_exact'] for x in r['epochs'])
 rejected=False
 try:reporter['analyze'](OUT/'mock',False)
 except AssertionError:rejected=True
 assert rejected,'Physical report must reject actual mock controller output'
 (OUT/'mock/spell-analysis.json').write_text(json.dumps(r,indent=2)+'\n')
 (OUT/'reporter-proof.json').write_text(json.dumps({'passed':True,'actual_epochs':40,'all_nonphysical_labels':True,'physical_route_rejects_mock':True},indent=2)+'\n')
 print('PASS actual40-epoch reporter, effect/completion/accounting metadata and physical mock rejection')
if __name__=='__main__':main()
