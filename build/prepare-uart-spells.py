"""Clone frozen draw-order48-epoch suite; only destination/UART boundary reads change."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,os,shutil,subprocess
ROOT=Path(__file__).resolve().parent.parent
OLD=ROOT/'build/draw-order-test-private-v1'
OUT=ROOT/'build/uart-spells-private'
NAME='snes-draw-uart1'
CHECK='''uart_status() {
  IFS= read -r UART_LINE < /proc/d35_uart_tx || return 1
  printf '%s\\n' "$UART_LINE" > "$BASE/uart-$1.txt"
  case "$UART_LINE" in
    'version=4 result=0 irq=19 attached=1 '*fault=0\ bypass=0\ *cap=0) return 0 ;;
    *) return 1 ;;
  esac
}
'''
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 assert not OUT.exists(),'Use a fresh retest package; preserve previous evidence'
 q=json.loads((OLD/'verification.json').read_text());ready=json.loads((OLD/'ready.json').read_text())
 assert q['passed'] and q['native_client_qualified'] and q['wrapper_qualified'] and len(q['actual_epochs'])==48
 assert digest(OLD/'verification.json')==ready['verification_sha256']
 for group in ['source_hashes','payload_hashes','proof_hashes']:
  for n,h in q[group].items():assert digest(ROOT/n if group=='source_hashes' else OLD/n)==h,n
 for n,h in ready['additional_sources'].items():assert digest(ROOT/n)==h,n
 OUT.mkdir()
 for n in q['payload_hashes']:
  p=OUT/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(OLD/n,p)
 wrapper=(OUT/'launch.sh').read_text();assert wrapper.count('BASE=/usr/retro/snes-draw-order1')==1
 wrapper=wrapper.replace('BASE=/usr/retro/snes-draw-order1','BASE=/usr/retro/'+NAME)
 anchor='sync\n# Vendor boot handoff:';assert wrapper.count(anchor)==1
 wrapper=wrapper.replace(anchor,'sync\n'+CHECK+'uart_status before || exit 1\nsync\n# Vendor boot handoff:')
 anchor='RESULT=$?\n';assert wrapper.count(anchor)==1
 wrapper=wrapper.replace(anchor,anchor+'uart_status after || RESULT=1\n')
 (OUT/'launch.sh').write_text(wrapper,encoding='utf-8',newline='\n')
 (OUT/'dispatch.sh').write_text('#!/bin/sh\nexec /bin/sh /usr/retro/'+NAME+'/launch.sh\n',encoding='utf-8',newline='\n')
 (OUT/'suite-identity.json').write_bytes((OLD/'verification.json').read_bytes())
 (OUT/'TEST-ME.txt').write_text('UART-corrected repeat of unchanged draw-order48-epoch FFVI suite. Allow20-25minutes; wait stock, power down, return card. Select+Start aborts. Next boot stock with UART fix still enabled.\n')
 unchanged=[n for n in q['payload_hashes'] if n not in ('launch.sh','dispatch.sh')]
 assert all(digest(OUT/n)==q['payload_hashes'][n] for n in unchanged)
 prefix=['wsl','--exec'] if os.name=='nt' else []
 def run(args):
  r=subprocess.run(prefix+args,cwd=ROOT,capture_output=True,text=True,timeout=60);return r
 shell=['qemu-arm','-0','busybox','-L','build/sysroot','build/uart-fix-private/firmware-busybox','sh']
 r=run(shell+['-n','build/uart-spells-private/launch.sh']);assert r.returncode==0,r.stderr
 # Exercise exact guard in firmware shell with a private status file, no IRQ or hardware access.
 status=OUT/'fixture-status';snippet=OUT/'check-status.sh'
 snippet.write_text('BASE=build/uart-spells-private\n'+CHECK.replace('/proc/d35_uart_tx','build/uart-spells-private/fixture-status')+'uart_status check\n',encoding='utf-8',newline='\n')
 for label,fields,want in [('active','attached=1 fault=0 bypass=0 cap=0',0),('inactive','attached=0 fault=0 bypass=0 cap=0',1),('fault','attached=1 fault=1 bypass=0 cap=0',1),('bypass','attached=1 fault=0 bypass=1 cap=0',1),('capped','attached=1 fault=0 bypass=0 cap=200000',1)]:
  fields=fields.replace(' fault=',' calls=0 added=0 writes=0 fault=');status.write_text('version=4 result=0 irq=19 '+fields+'\n',encoding='utf-8',newline='\n')
  r=run(shell+['build/uart-spells-private/check-status.sh']);assert r.returncode==want,(label,r.returncode,r.stderr)
 # Reuse the frozen full48-epoch qualification by hash; execute a bounded
 # one-epoch retarget seam here. Never deploy the host-only run-limit setting.
 r=run(['env','D35_ABILITY_MOCK=1','D35_MVP_NO_PACING=1','D35_FULL_HOST_FIXTURE=1','D35_FULL_RUN_LIMIT=1','LD_LIBRARY_PATH=build/sysroot/lib','qemu-arm','-cpu','cortex-a7','-L','build/sysroot','build/uart-spells-private/ability-suite','build/uart-spells-private','build/plus-a7-out/ff6.sfc'])
 (OUT/'mock-retarget.log').write_text(r.stdout+r.stderr);assert r.returncode==0,(r.returncode,r.stderr)
 suite=dict(l.split('=',1) for l in (OUT/'suite-result.txt').read_text().splitlines() if '=' in l);assert suite['runs']=='1' and suite['stopped']=='0',suite
 names=list(q['payload_hashes'])+['suite-identity.json','TEST-ME.txt']
 report={'version':'uart-spells1','target':NAME,'baseline_suite_verification_sha256':digest(OLD/'verification.json'),
 'baseline_physical_analysis_sha256':digest(ROOT/'evidence/2026-10-14/draw-order-return/analysis.json'),
 'unchanged_payloads':unchanged,'unchanged_plan_runner_cores_states_inputs':True,'epochs':48,
 'qualification':['original48-epoch suite proofs and all source hashes','exact firmware wrapper syntax','five active/fault/cap boundary guards','unchanged controller one-epoch mock retarget'],
 'payloads':{n:digest(OUT/n) for n in names},'sources':{n:digest(ROOT/n) for n in ['build/prepare-uart-spells.py','build/install-uart-spells.py']},
 'physical_result':'PENDING','QEMU_timing_used':False,'card_access':False,
 'measurement_gate':{'measured_A7_CPU_saving_ms':None,'measured_IRQ_reduction_percent':98.99431555,'added_A7_cost_ms':None,
 'break_even':'IRQ time avoided > added correction service and dispatch cost; exact A7 prices unmeasured',
 'predicted_remaining_audio_deficit_ms':None,'falsifiable_result':'same48 epochs retain clean candidate histories; compare raw/boundary/priority valid-prefix CPU, reserve and Quasar regression to prior return, with UART attached and fault/bypass zero before/after'}}
 (OUT/'qualification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'prepared':NAME,'unchanged_payloads':len(unchanged),'epochs':48}))
if __name__=='__main__':main()
