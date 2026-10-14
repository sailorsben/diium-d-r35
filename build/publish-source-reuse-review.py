"""Publish bounded local-source/offline findings, preserving old evidence."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 folders=[ROOT/'build'/n for n in ('shared-geometry-private-v1','shared-geometry-private-v2','cache-alignment-private-v1','source-sharing-private-v1')]
 geometry=json.loads((folders[0]/'qualification.json').read_text())
 probe=json.loads((folders[1]/'eligibility.json').read_text())
 alignment=json.loads((folders[2]/'qualification.json').read_text())
 source=json.loads((folders[3]/'qualification.json').read_text())
 assert geometry['passed'] and alignment['passed'] and source['passed']
 assert sum(c['totals']['replayed_commands'] for c in geometry['cases'])==0
 assert all(not c['ARM_QEMU_layout'][j]%64 for c in alignment['cases'] for j in (0,1,2,7))
 assert all(c['exact'] for c in probe['cases'])
 base=ROOT/'build/common-band-private-v3/plus-a7.so';assert digest(base)==geometry['oracle_core_sha256']==alignment['oracle_core_sha256']
 # Verify the baseline source inventory rather than copying stale provenance.
 baseline=json.loads((folders[0]/'inputs.json').read_text())
 for name,value in baseline['baseline_sources'].items():assert digest(ROOT/'build/common-band-private-v3'/name)==value
 layout=(folders[2]/'elf-layout.txt').read_text();assert '0013db28 00000f00' in layout and '00154900 00000a00' in layout
 data={'card_access':False,'production_gate_passed':False,'A7_savings_measured':False,'QEMU_timings_used':False,'qualified_original_command_calls_this_review':24000,
 'baseline_core_sha256':digest(base),'alignment_candidate_core_sha256':alignment['candidate_core_sha256'],
 'alignment':{'baseline_palette_symbol_offset':0x13db28,'baseline_palette_array_mod64':40,'table_bytes':32,'old_entry_bytes':48,'old_table_member_offset':16,'old_table_starts_mod64':[56,40,24,8],'old_split_tables_out_of80':40,'new_split_tables_out_of80':0,'old_cache_bytes':3840,'new_cache_bytes':3520,'tile_alignment_guarantee':64,'decoded_tile_stride_bytes':64,'tile_allocation_sizes_unchanged':True,'baseline_A7_tile_pointers_recorded':False,'ARM_QEMU_old_tile_pointers_mod64':[p%64 for p in geometry['cases'][0]['ARM_QEMU_layout'].values()][:3],'qualified_original_calls':9600,'new_layout_verified_in_every_case':True},
 'shared_geometry_first_envelope':{'qualified_comparison_calls':9600,'recorded_commands':0,'replayed_commands':0,'active_optimization_coverage':False,'recommended_for_A7_test':False,'guard_probe':probe,'extra_guard_probe_exact_calls':2400,'command_storage_bytes':65536},
 'source_sharing_by_layer':source,
 'copy_removal_scenario':{'basis':'Optimistic illustration using sampled callback means, not an aligned net A7 prediction. No new PPU/chunk/cache or ownership costs priced.','Meteor':{'callback_ms':0.824,'current_deadline_gap_ms':1.3083455,'remaining_gap_if_whole_callback_free_ms':0.4843455,'remaining_saving_for20pct_margin_ms':3.8219764},'Quasar':{'callback_ms':0.8585,'current_deadline_gap_ms':0.803283,'slack_if_whole_callback_free_ms':0.055217,'remaining_saving_for20pct_margin_ms':3.2824139}},
 '2010_local_reviewed_commit':'fe690dd321fa5a46b5234a2bde089d2518c62b0e',
 'limits':['Static baseline palette alignment is exact for its ELF and page-aligned load base; old A7 dynamic tile allocation addresses remain unknown.','A split tile/table footprint is not a cache miss, extra miss per access, DRAM transfer count, or time saving. Neighboring tiles can share warm cache lines.','Geometry v1 exercised fallback only: exact outputs do not qualify its positive path. No production install or A7 measurement should use this version.','Source-key matches are warm nonblank ordinary full-tile2/4bpp requests, not guaranteed visible final owners. No savings overlap with prior hidden-row/fused candidates is measured.','No direct-output-buffer or generalized deferred-span implementation was built. Generic DMA-buffer APIs do not establish the private chunk driver contract.','Original drawings, native PCM and geometry match every call; normalized emulated state is compared every30 calls.']}
 out=folders[2];(out/'public-analysis.json').write_text(json.dumps(data,indent=2)+'\n')
 names=('shared-bg-geometry.h','prepare-shared-bg-geometry.py','build-shared-bg-geometry.sh','qualify-shared-bg-geometry.py','prepare-shared-bg-probe.py','build-shared-bg-geometry-probe.sh','qualify-shared-bg-probe.py','prepare-cache-alignment.py','build-cache-alignment.sh','qualify-cache-alignment.py','prepare-source-sharing-breakdown.py','build-source-sharing-breakdown.sh','qualify-source-sharing-breakdown.py','publish-source-reuse-review.py')
 files=[ROOT/'build'/n for n in names]
 for folder in folders:
  files += [p for p in folder.rglob('*') if p.is_file() and (p.suffix in ('.c','.h') or p.name in ('qualification.json','eligibility.json','elf-layout.txt','snes9x2005_plus_libretro.so','compare'))]
  files += list((folder/'exact').glob('*.log'))
 files += list((folders[0]/'setup-export-failure').glob('*.log'))
 source_files=[ROOT/'build/snes9x2010'/p for p in ('src/memmap.c','src/ppu.c','src/ppu.h','libretro/libretro.c','libretro/libretro-common/memmap/memalign.c')]
 files += source_files
 (out/'public-inputs.json').write_text(json.dumps({'hashes':{p.relative_to(ROOT).as_posix():digest(p) for p in files},'baseline_sources':baseline,'old_source_population_receipt_sha256':digest(ROOT/'evidence/2026-10-13/architecture-populations/analysis.json')},indent=2)+'\n')
 spec=importlib.util.spec_from_file_location('review_public',ROOT/'build/publish-snes-1.19.py');pub=importlib.util.module_from_spec(spec);spec.loader.exec_module(pub)
 manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();old=json.loads(raw)['entries']
 for e in old:assert digest(ROOT/e['published'])==e['published_sha256']
 dest=ROOT/'evidence/2026-10-13/source-reuse-review';dest.mkdir(exist_ok=True);entries=[]
 for src,name in ((out/'public-analysis.json','analysis.json'),(out/'public-inputs.json','inputs.json')):
  d=dest/name;assert not d.exists();d.write_bytes(pub.public_text(src.read_bytes()));entries.append({'source':src.relative_to(ROOT).as_posix(),'published':d.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'published_sha256':digest(d)})
 manifest.write_bytes(pub.append_manifest(raw,entries));assert json.loads(manifest.read_bytes())['entries'][:len(old)]==old
 print('Published source-reuse/alignment review, preserved',len(old),'old evidence entries; no device write')
if __name__=='__main__':main()
