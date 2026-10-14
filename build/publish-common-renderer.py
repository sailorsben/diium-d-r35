"""Publish bounded common-renderer evidence and conditional break-even gates."""
from pathlib import Path
from hashlib import sha256
from importlib.util import spec_from_file_location,module_from_spec
import json,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/common-band-private-v3'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 roots=[ROOT/'build/common-batch-private-v1',ROOT/'build/common-band-private-v2',OUT]
 qs=[json.loads((d/'qualification.json').read_text()) for d in roots]
 for d,q in zip(roots,qs):
  assert q['passed'] and not q['A7_savings_measured'] and not q['production_gate_passed']
  for r in q['exact']:
   log=d/f"exact/{r['case']:03d}-{r['label']}.log";core=d/('plus-a7.so' if r['label']=='ordinary' else 'counted-core/snes9x2005_plus_libretro.so')
   assert digest(log)==r['log_sha256'] and digest(core)==r['core_sha256']
 seams=[OUT/'clipping-exact.log',OUT/'clipping-candidate.log',OUT/'palette-exact.log',OUT/'palette-candidate.log']
 assert all('PASS' in p.read_text() for p in seams)
 asm=[]
 for d,label in [(roots[0],'generic'),(OUT,'band')]:
  names=['DrawBackground'] if label=='generic' else ['d35_band_0','d35_band_1','d35_band_3']
  for name in names:
   result=subprocess.check_output(['arm-linux-gnueabihf-objdump','-d','--disassemble='+name,str(d/'plus-a7.so')],text=True)
   assert '<'+name+'>:' in result,name
   path=d/('asm-'+name+'.txt');path.write_text(result)
   blend=[l.strip() for l in result.splitlines() if 'd35_blend' in l and '\tbl\t' in l]
   if label=='band':assert not blend
   else:assert blend
   asm.append({'variant':label,'symbol':name,'sha256':digest(path),'out_of_line_blend_call_sites':blend,'A7_time':False})
 forecast=json.loads((ROOT/'evidence/2026-10-13/pearl-workback/forecast-cases.json').read_text())
 cases=[]
 for prev in forecast['cases']:
  c=next(c for c in qs[2]['cases'] if c['case']==prev['fixture']);v2=next(c for c in qs[1]['cases'] if c['case']==prev['fixture'])
  for k in ('warm_nonblank_calls','blank_handled','band_calls','opaque_rows'):assert c['common'][k]==v2['common'][k]
  d=c['new_indirect_calls_removed'];o=c['common']['opaque_rows'];b=c['common']['band_calls']
  cases.append({'name':c['name'],'case':c['case'],'tile_dispatches_handled_in_band':d,'band_calls':b,'opaque_rows':o,'palette_materializations_before':v2['common']['palette_materializations'],'palette_materializations_after':c['common']['palette_materializations'],'conditional_additional_saving_to_deadline_us':[max(0,x-forecast['deadline_us']) for x in prev['conditional_service_step_us']],'conditional_additional_saving_to_20pct_us':[max(0,x-forecast['target_20pct_us']) for x in prev['conditional_service_step_us']],'conditional_deadline_net_per_cell_us':[max(0,x-forecast['deadline_us'])/d for x in prev['conditional_service_step_us']],'conditional_20pct_net_per_cell_us':[max(0,x-forecast['target_20pct_us'])/d for x in prev['conditional_service_step_us']],'equation':f'S_common_us = {d}*entry_credit + {o}*opaque_store_credit - added_band_cache_and_spill_cost; measure whole combination','new_unit_prices_measured':False})
 analysis={'cases':cases,'source_scope':['CPU dispatch/WaitAddress owner','APU interpolation/envelope/clock path','PPU register flush/window/fixed-color ownership','background/OBJ/Mode7/mosaic/clipped rendering and tile-cache invalidation','NEON mask/palette/color/store kernels','runner resampling/audio publication and display buffer ownership'],'gate_is_conditional_on_prior_forecast':True,'A7_prices_measured':False,'production_gate_passed':False,'no_card_access':True,'assumptions':['Earlier all-new-code forecast is itself unmeasured; replace it with measured service before accepting a gate.','Per-cell threshold is normalized net saving after added costs, not an isolated ABI instruction price.','No conversion of disassembly or QEMU duration to A7 microseconds.','Only ordinary indexed 2/4bpp plain/full-add/full-sub background bands use specialization; unsupported and cold paths retain original behavior.'],'negative_results':['Generic v1 exact output passes, but emitted code introduces out-of-line per-row blend calls; reject that performance design.','One-palette v2 exact output passes; Quasar rebuilds palette256 times. Eight-slot batch-local v3 avoids repeated materialization; slot lifetime ends with DrawBackground.','Tile decode, exact arithmetic-only replacement and simulation quota are not demonstrated universal millisecond sources.'],'assembly':asm}
 frozen=json.loads((ROOT/'build/fullpaths-private-v2/verification.json').read_text());identities={}
 for key in ('source_hashes','payload_hashes','proof_hashes'):
  for name,expected in frozen[key].items():assert digest(ROOT/name)==expected,name
  identities[key]=len(frozen[key])
 verify={'passed':True,'new_original_command_calls':sum(q['calls'] for q in qs),'final_candidate_calls':qs[2]['calls'],'independent_final_tile_cases':129024,'independent_repeated_palette_cases':3584,'repeated_palette_calls_per_case':16,'seam_logs':[{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'text':p.read_text()} for p in seams],'staged_frozen_identities_unchanged':identities,'A7_saving_measured':False,'card_access':False,'production_gate_passed':False}
 spec=spec_from_file_location('publish',ROOT/'build/publish-snes-1.19.py');m=module_from_spec(spec);spec.loader.exec_module(m)
 manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();prior=json.loads(raw)['entries']
 for e in prior:assert digest(ROOT/e['published'])==e['published_sha256']
 public=ROOT/'evidence/2026-10-13/common-renderer';assert not public.exists();public.mkdir();entries=[]
 for name,data in [('generic-v1.json',qs[0]),('band-v2.json',qs[1]),('band-v3.json',qs[2]),('analysis.json',analysis),('verification.json',verify)]:
  src=OUT/('public-'+name);src.write_text(json.dumps(data,indent=2)+'\n');dest=public/name;dest.write_bytes(m.public_text(src.read_bytes()))
  entries.append({'source':src.relative_to(ROOT).as_posix(),'published':dest.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'published_sha256':digest(dest)})
 manifest.write_bytes(m.append_manifest(raw,entries));assert json.loads(manifest.read_bytes())['entries'][:len(prior)]==prior
 print('Published common candidate and negative designs;',verify['new_original_command_calls'],'exact calls; preserved',len(prior),'old publications; gate NOT MET')
 for c in cases:print(c['name'],c['tile_dispatches_handled_in_band'],c['band_calls'],c['opaque_rows'],c['palette_materializations_after'])
if __name__=='__main__':main()
