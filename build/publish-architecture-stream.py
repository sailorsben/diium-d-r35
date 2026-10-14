"""Publish measured offline populations for the two pasted architecture proposals."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/architecture-stream-private-v1'
FOLLOW=ROOT/'build/architecture-followup-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 q=json.loads((OUT/'qualification.json').read_text());follow=json.loads((FOLLOW/'qualification.json').read_text());assert q['passed'] and follow['passed'] and len(q['cases'])==8
 metrics=[]
 for c in q['cases']:
  t=c['totals'];assert not any(t[k] for k in ('source_observer_table_overflow','unsupported_layout_regions','foreground_depth_pixels_missing_store_provenance'))
  assert t['tile_color_math_pixel_writes']+t['final_backdrop_math_pixel_writes']-t['overwritten_math_pixel_writes']==t['final_math_pixel_owners']
  rows=[list(map(int,l[5:].split(','))) for l in (OUT/f"exact/{c['fixture']:03d}.log").read_text().splitlines() if l.startswith('ARCH ')]
  assert all(r[67]+r[87]-r[68]==r[69] for r in rows) # column0 is frame
  for group,r in c['means_per_call'].items():
   if not group.endswith('_peak'):continue
   math=r['tile_color_math_pixel_writes'];dead=r['overwritten_math_pixel_writes'];survivors=math-dead
   metrics.append({'name':c['name'],'interval':group,'means':r,'discarded_tile_math_percent':100*dead/math,'discarded_semantic_RGB_write_percent':100*r['overwritten_main_RGB_writes']/r['tracked_main_RGB_pixel_writes'],'matched_source_fraction_of_main':r['matched_main_sub_source_row_requests']/r['main_full_tile_source_row_requests'],'global_palette_hit_percent':100*(1-r['palette_cache_misses']/r['palette_cache_queries']),'simple_byte_metadata_deferred_model':{'metadata_writes_bytes':r['tracked_main_RGB_pixel_writes'],'metadata_scan_bytes':r['backdrop_bulk_depth_scan_bytes'],'additional_survivor_RGB_read_write_bytes':4*survivors,'total_extra_logical_bytes':r['tracked_main_RGB_pixel_writes']+r['backdrop_bulk_depth_scan_bytes']+4*survivors,'not_DRAM_or_timing_evidence':True}})
 data={'observer_only':True,'optimization_implemented':False,'card_access':False,'A7_savings_measured':False,'QEMU_timings_used':False,'qualified_original_command_calls':9600,'prior_two_censuses_calls':19200,'current_palette_cache_bytes':3840,'current_palette_cache_symbol':'d35_palette_entries.lto_priv.0 size0x0f00','narrow_peak_metrics':metrics,'all_contexts':q['cases'],'followup_contexts':follow['cases'],'limits':['Semantic successful pixel writes, not retired vector arithmetic lanes or bus transactions.','Source sharing counts only warm nonblank full-tile requests, same BG/destination/index row/flip/palette within one redraw.','Matching source and hidden-row savings may overlap; do not add their credits.','Memory ledger covers explicit depth/RGB initialization and backdrop bulk depth scan, not all kernel/CPU/DRAM traffic.','No receiver guard, deferred math, source descriptor cache, DMA fast path or strip backend was installed or timed.']}
 (OUT/'public-analysis.json').write_text(json.dumps(data,indent=2)+'\n')
 files=[ROOT/'build'/n for n in ('prepare-architecture-followup.py','build-architecture-followup.sh','qualify-architecture-followup.py','architecture-stream-census.h','prepare-architecture-stream.py','build-architecture-stream.sh','qualify-architecture-stream.py','publish-architecture-stream.py')]
 files += [p for folder in (OUT,FOLLOW) for p in folder.rglob('*') if p.is_file() and p.suffix in ('.c','.h')]
 files += [OUT/'qualification.json',FOLLOW/'qualification.json',OUT/'core/snes9x2005_plus_libretro.so',FOLLOW/'core/snes9x2005_plus_libretro.so']
 files += list((OUT/'exact').glob('*.log'))+list((FOLLOW/'exact').glob('*.log'))
 (OUT/'public-inputs.json').write_text(json.dumps({'hashes':{p.relative_to(ROOT).as_posix():digest(p) for p in files},'baseline_input_hashes':json.loads((OUT/'inputs.json').read_text())},indent=2)+'\n')
 spec=importlib.util.spec_from_file_location('stream_public',ROOT/'build/publish-snes-1.19.py');pub=importlib.util.module_from_spec(spec);spec.loader.exec_module(pub)
 manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();old=json.loads(raw)['entries']
 for e in old:assert digest(ROOT/e['published'])==e['published_sha256']
 dest=ROOT/'evidence/2026-10-13/architecture-populations';dest.mkdir(exist_ok=True);entries=[]
 for src,name in ((OUT/'public-analysis.json','analysis.json'),(OUT/'public-inputs.json','inputs.json')):
  d=dest/name;assert not d.exists();d.write_bytes(pub.public_text(src.read_bytes()));entries.append({'source':src.relative_to(ROOT).as_posix(),'published':d.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'published_sha256':digest(d)})
 manifest.write_bytes(pub.append_manifest(raw,entries));assert json.loads(manifest.read_bytes())['entries'][:len(old)]==old
 print('Published pasted-hypothesis population census; preserved',len(old),'historical entries')
if __name__=='__main__':main()
