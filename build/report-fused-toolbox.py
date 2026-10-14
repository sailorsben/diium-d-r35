"""Price-free composition report: exact source work, disjoint credits, added costs."""
from pathlib import Path
from hashlib import sha256
import json,re,statistics,sys
ROOT=Path(__file__).resolve().parent.parent
V2=sys.argv[1:]==['--v2']
assert sys.argv[1:] in ([],['--v2'])
OUT=ROOT/('build/fused-toolbox-private-v2' if V2 else 'build/fused-toolbox-private-v1')
def digest(p):return sha256(p.read_bytes()).hexdigest()
def data(p,prefix):return [list(map(int,l[len(prefix):].split(','))) for l in p.read_text().splitlines() if l.startswith(prefix)]
def main():
 q=json.loads((OUT/'qualification.json').read_text());v2=json.loads((ROOT/'build/fused-count-private-v2/qualification.json').read_text());old=json.loads((ROOT/'build/partial-merge-private-v1/analysis.json').read_text());blind=json.loads((ROOT/'build/partial-preflight-private-v1/analysis.json').read_text());baseline={c['case']:c for c in json.loads((ROOT/'evidence/2026-10-13/common-renderer/band-v3.json').read_text())['cases']}
 assert q['passed'] and q['calls']==43200 and v2['prior_observer_fields_unchanged_every_call'];cases=[];whole=[]
 if V2:v2={'comparisons':[c for c in q['comparisons'] if c['label']=='census' and c['case'] in (0,1,8)]}
 for c in v2['comparisons']:
  f=c['heavy_counts'];p=next(x for x in old['cases'] if x['case']==c['case']);probe=next(x['totals'] for x in blind['cases'] if x['case']==c['case']);old_rows=sum(b['rows'] for b in p['buckets'] if b['mode']==0);old_2=f['two_bpp_prefix_depth_loads'];old_depth_model=old_rows+old_2;new_depth=f['prefix_depth_loads']+f['normal_depth_loads'];hits4=f['fully_hidden_tile_returns']-baseline[c['case']]['common']['early_hidden_calls']
  assert f['index_row_loads']<=old_rows and f['sparse_one']+f['sparse_two']==sum(m['rows_per_call'] for m in p['mask_shapes'] if m['mode']==0 and int(m['mask_hex'],16).bit_count()<=2)
  cases.append({'case':c['case'],'name':c['name'],'old_nonsole_plain_index_row_loads':old_rows,'fused_nonsole_plain_index_row_loads':f['index_row_loads'],'index_rows_avoided':old_rows-f['index_row_loads'],'index_bytes_avoided':8*(old_rows-f['index_row_loads']),'old_blind_4bpp_probe_rows':probe['depth4_probe_row_visits'],'fused_4bpp_probe_rows':f['four_bpp_prefix_depth_loads'],'new_fully_hidden_4bpp_tiles':hits4,'tile_metadata_reads_avoided_before_probe':hits4-f['four_bpp_hidden_policy_samples'],'sparse_rows':f['sparse_one']+f['sparse_two'],'same_sparse_population_preserved':True,'first_visible_depth_results_reused':f['first_visible_depth_reused'],'old_logical_plain_depth_load_model':old_depth_model,'new_logical_plain_depth_loads':new_depth,'logical_depth_load_reduction_model':old_depth_model-new_depth,'depth_model_assumptions':['Same2bpp prefix predicate/order and warm aligned controls; no cold fallback in these tails.','Old row loop separately rereads depth after prepass. Intrinsic load requests, not retired instructions or DRAM transactions.'],'band_cells':f['band_cells'],'band_entries':f['ordinary_bands']+f['sole_bands'],'counts':f})
 for c in q['comparisons']:
  if c['label']!='census':continue
  new=data(OUT/f"exact/{c['case']:03d}-census.log",'FUSED ');prior=data(ROOT/f"build/common-band-private-v3/exact/{c['case']:03d}-census.log",'PEARL ');assert len(new)==len(prior)==1200
  probes=sum(x[3]+x[4] for x in new);hits=[x[7]-y[351] for x,y in zip(new,prior)];assert min(hits)>=0
  item={'case':c['case'],'name':c['name'],'calls':1200,'four_bpp_probes_total':probes,'four_bpp_hidden_tiles_total':sum(hits),'four_bpp_hidden_hit_fraction':sum(hits)/probes if probes else None,'four_bpp_hidden_hits_nonnegative_every_call':True}
  if V2:
   first=data(ROOT/f"build/fused-toolbox-private-v1/exact/{c['case']:03d}-census.log",'FUSED ')
   assert len(first)==1200
   assert all(a[17:28]==b[17:28] for a,b in zip(first,new)),('Active/store/palette populations changed',c['case'])
   item.update({'v1_four_bpp_probes_total':sum(x[3]+x[4] for x in first),'v1_four_bpp_depth_loads_total':None,'four_bpp_depth_loads_total':sum(x[31] for x in new),'policy_vetoes_total':sum(x[12] for x in new),'v1_index_rows_total':sum(x[11] for x in first),'index_rows_total':sum(x[11] for x in new),'active_store_palette_populations_unchanged_every_call':True})
  whole.append(item)
 assembly={}
 for name in ('d35_fused_band_0_0','d35_fused_band_0_1','d35_fused_band_1_0','d35_fused_band_3_0'):
  p=OUT/f'asm-{name}.txt';text=p.read_text();assert f'<{name}>:' in text
  assembly[name]={'asm_sha256':digest(p),'prologue':[l.strip() for l in text.splitlines() if re.search(r'\b(push|vpush)\b|sub\s+sp, sp, #',l)][:3]}
 abi=[tuple(map(int,v)) for v in re.findall(r'GLIBC_(\d+)\.(\d+)',(OUT/'abi.txt').read_text())];assert abi and max(abi)<=(2,30)
 result={'passed':True,'ordinary_core_sha256':digest(OUT/'plus-a7.so'),'cases':cases,'whole_window_selection':whole,'assembly':assembly,'max_GLIBC':list(max(abi)),'every_frame':True,'A7_saving_measured':False,'QEMU_timings_used':False,'card_access':False,'production_gate_passed':False,'interaction_model':'Fewer expensive rows times cheaper surviving rows, plus shared setup; all added policy/cache/spill costs belong in the total.','cost_limitations':['The prefix selector still checks eligible tiles; only mode/sole dispatch is moved to band scope.','Plain nonsole kernel saves2 additional D registers versus selective control; frame176 vs168 bytes.','No palette materialization saving established for Pearl, which already uses one sole palette.','Whole-window selection is a finite replay, not a universal predictor.','Source load counts are not hardware bandwidth or microseconds.']}
 (OUT/'composition.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS disjoint work budgets, full-window selection checks and ABI; no A7 timing')
 for c in cases:print(c['name'],'index rows',c['old_nonsole_plain_index_row_loads'],'->',c['fused_nonsole_plain_index_row_loads'],'4bpp probes',c['old_blind_4bpp_probe_rows'],'->',c['fused_4bpp_probe_rows'],'sparse',c['sparse_rows'],'logical depth reduction',c['logical_depth_load_reduction_model'])
if __name__=='__main__':main()
