"""Freeze correctness, compiler stability and explicit hardware measurement gate."""
from pathlib import Path
from hashlib import sha256
import json, runpy, shutil

ROOT=Path(__file__).resolve().parent.parent
CORE=ROOT/'build/draw-order-private-v1'
OUT=ROOT/'build/draw-order-test-private-v1'
DEST=ROOT/'evidence/2026-10-14/draw-order'

def digest(p):return sha256(p.read_bytes()).hexdigest()

def main():
 assert not DEST.exists() and not (OUT/'ready.json').exists()
 q=json.loads((OUT/'verification.json').read_text());assert q['passed'] and len(q['actual_epochs'])==48
 for group in ('source_hashes','payload_hashes','proof_hashes'):
  for n,h in q[group].items():assert digest(ROOT/n if group=='source_hashes' else OUT/n)==h,n
 ordinary=json.loads((CORE/'qualification.json').read_text());seams=json.loads((CORE/'seams.json').read_text());apu=json.loads((CORE/'APU-audit.json').read_text())
 assert ordinary['passed'] and seams['passed'] and apu['passed'] and apu['APU_object_byte_identical']
 for n,h in json.loads((CORE/'frozen.json').read_text()).items():assert digest(ROOT/n)==h,n
 shutil.copy2(OUT/'plan.json',OUT/'mock/plan.json')
 reporter=runpy.run_path(str(OUT/'report.py'));a=reporter['analyze'](OUT/'mock',True)
 assert len(a['epochs'])==48 and len(a['matched_Meteor_Quasar'])==12
 assert all(r['status']=='NOT_PHYSICAL' and r['identity_verified'] and r['complete_window'] and r['PCM_final_accounting_exact'] and r['effect_properties_observed'] for r in a['epochs'])
 try:reporter['analyze'](OUT/'mock',False)
 except AssertionError:pass
 else:raise AssertionError('Physical reporter accepted mock telemetry')
 paths=[ROOT/'build'/n for n in ('draw-order.h','prepare-draw-order.py','build-draw-order.py','qualify-draw-order.py',
  'draw-order-render-probe.h','draw-order-render-check.c','check-draw-order-seams.py','audit-draw-order-apu.py',
  'prepare-draw-order-test.py','install-draw-order.py','publish-draw-order-install.py','finalize-draw-order.py')]
 paths += [OUT/n for n in ('build.sh','qualify.py','report.py')]+[ROOT/'docs/snes-draw-order-test.txt']
 paths += [CORE/n for n in ('build-identity.json','qualification.json','seams.json','APU-audit.json')]
 paths += [p for label in ('boundary','priority') for p in (CORE/label/'source').glob('*.[ch]')]
 paths += [CORE/label/n for label in ('boundary','priority') for n in ('Makefile','source/apu_blargg.o','snes9x2005_plus_libretro.so')]
 inputs={p.relative_to(ROOT).as_posix():digest(p) for p in paths}
 gate={'measured_A7_saving_ms':None,'boundary_only_A7_cost_ms':None,'net_candidate_A7_saving_ms':None,
  'added_costs':['Two extra BG invocations per eligible main/sub pair; repeated BG3 traversal.','Priority guards on scalar, batch and sole-source consumers.','Code footprint, branch and linked-layout/cache effects; final linked addresses can move despite fixed APU object.'],
  'break_even':'saved color/depth/palette production time > extra traversal + priority guards + code/layout costs; total candidate must also beat raw v3 including APU-boundary cost',
  'offline_lead':'Research prototype: Meteor late main RGB writes85687->57865, vector expansions10922.5->7515.3; not hardware times and not newly measured ordinary-candidate counts.',
  'predicted_remaining_audio_deficit_ms':None,'latest_unprofiled_recorded_deficit_ms':0.265972053946141,
  'deficit_limit':'Recorded worst valid16 CPU gap, excluding system costs; not a sufficient fix budget.',
  'falsifiable_physical_result':'All18 candidate contexts clean twice with full valid PCM/reserve/recovery and every frame; positive priority-vs-boundary and priority-vs-raw matched cost in both orders, no unacceptable Quasar/noneligible regression. Pointer drift, incomplete effect/recovery or nonpositive net saving rejects promotion.',
  'authorization':'User explicitly requested implementation, stable APU output, validation and installation on I:. Separately owned measurement candidate obtains missing net A7 prices; production gate remains false.'}
 ready={'version':'1.19-draw-order1','ready':True,'installed':False,'armed':False,'measurement_only':True,'production_gate_passed':False,
  'verification_sha256':digest(OUT/'verification.json'),'additional_sources':inputs,'reporter_mock_rejection_passed':True,
  'ordinary_exact_calls':43200,'renderer_oracle_fixtures':2560,'resolution_state_calls':8400,'actual_controller_calls':57600,
  'APU_compiler_output_stable':True,'APU_object_sha256':apu['APU_object_sha256'],'SPC_DSP_function_sizes_identical':True,'gate':gate}
 (OUT/'ready.json').write_text(json.dumps(ready,indent=2)+'\n')
 manifest=ROOT/'evidence/manifest.json';m=json.loads(manifest.read_text())
 for e in m['entries']:assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
 DEST.mkdir(parents=True)
 files=[(CORE/n,DEST/n) for n in ('build-identity.json','qualification.json','seams.json','APU-audit.json')]
 files += [(OUT/n,DEST/n) for n in ('plan.json','ready.json','verification.json')]
 for src,target in files:
  shutil.copy2(src,target)
  m['entries'].append({'source':src.relative_to(ROOT).as_posix(),'published':target.relative_to(ROOT).as_posix(),
   'source_sha256':digest(src),'published_sha256':digest(target),'bytes':target.stat().st_size,'normalized':False})
 manifest.write_text(json.dumps(m,indent=2)+'\n')
 print('PASS48-epoch/native/wrapper/ABI/physical-mock rejection; ordinary rendering/state and fixed APU verified; A7 prices pending')

if __name__=='__main__':main()
