"""Publish bounded architecture work counts and source proof, no private replays."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,re,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/architecture-audit-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 q=json.loads((OUT/'qualification.json').read_text());ring=json.loads((OUT/'ring-proof.json').read_text());inputs=json.loads((OUT/'inputs.json').read_text())
 assert q['passed'] and len(q['cases'])==8 and ring['passed'] and not q['card_access']
 for n,h in inputs['input_hashes'].items():assert digest(ROOT/n)==h,n
 assert digest(ROOT/'build/common-band-private-v3/plus-a7.so')==q['oracle_core_sha256']
 rows=[]
 for c in q['cases']:
  t=c['totals'];rows.append({'fixture':c['fixture'],'name':c['name'],'calls':c['calls'],'same_geometry_setups':t['same_geometry_setups'],'OBJ_setups':t['OBJ_setups'],'redundant_VRAM_flag_groups_percent':100*t['all_three_cache_flags_already_invalid']/t['VRAM_byte_invalidations'],'ring_copy_calls_removed_by_two_span':t['actual_ring_copy_calls']-t['minimum_ring_copy_calls'],'max_copies_per_ring_read':t['max_copies_one_ring_read'],'full_width_clipped_OBJ_calls':t['full_width_clipped_OBJ_calls'],'repeated_OBJ_renderer_selections':t['repeated_OBJ_renderer_selections']})
 asm=(OUT/'update-screen.asm').read_text();matches=[l.strip() for l in asm.splitlines() if re.search(r'\b(vceq|vbsl|vbit|vbif)',l)]
 assert matches and 'd35_backdrop' in (ROOT/'build/common-band-private-v3/core/source/gfx.c').read_text()
 summary={'baseline_core_sha256':q['oracle_core_sha256'],'offline_calls':9600,'observer_only':True,'production_candidate_implemented':False,'card_access':False,'A7_savings_measured':False,'QEMU_timings_used':False,'cases':rows,'ring_proof':ring,'current_backdrop':{'already_NEON':True,'helper':'a7_tile.h:d35_backdrop','bulk_pixels':'count & ~7u','scalar_remainder':'count % 8, per contiguous span','width256_scalar_remainder':0,'installed_UpdateScreen_NEON_instructions':matches[:12]},'qualification':q,'limits':['Counts are not A7 prices.','No new unbounded quadratic hot path demonstrated.','DMA span eligibility, source-map boundaries, VRAM wrap, odd lengths, increments and transfer direction must be qualified before bulk-copy/invalidation changes.','No new saving for already installed NEON backdrop, prefix validity, band dispatch or palette reuse.']}
 (OUT/'public-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 files=[ROOT/'build'/n for n in ('architecture-audit.h','prepare-architecture-audit.py','build-architecture-audit.sh','qualify-architecture-audit.py','check-architecture-ring.py','publish-architecture-audit.py')]+[OUT/n for n in ('inputs.json','qualification.json','ring-proof.json','compare.c','core/snes9x2005_plus_libretro.so','update-screen.asm')]
 files += [p for p in (OUT/'core').rglob('*') if p.is_file() and p.suffix in ('.c','.h')]
 (OUT/'public-inputs.json').write_text(json.dumps({'baseline':inputs,'hashes':{p.relative_to(ROOT).as_posix():digest(p) for p in files}},indent=2)+'\n')
 spec=importlib.util.spec_from_file_location('arch_public',ROOT/'build/publish-snes-1.19.py');pub=importlib.util.module_from_spec(spec);spec.loader.exec_module(pub)
 manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();old=json.loads(raw)['entries']
 for e in old:assert digest(ROOT/e['published'])==e['published_sha256']
 dest=ROOT/'evidence/2026-10-13/architecture-audit';dest.mkdir(exist_ok=True);entries=[]
 for src,name in ((OUT/'public-summary.json','analysis.json'),(OUT/'public-inputs.json','inputs.json')):
  d=dest/name;data=pub.public_text(src.read_bytes());assert not d.exists();d.write_bytes(data)
  entries.append({'source':src.relative_to(ROOT).as_posix(),'published':d.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'published_sha256':digest(d)})
 manifest.write_bytes(pub.append_manifest(raw,entries));assert json.loads(manifest.read_bytes())['entries'][:len(old)]==old
 print('Published architectural work census and actual ring-branch equivalence; preserved',len(old),'historical entries')
if __name__=='__main__':main()
