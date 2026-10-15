"""Prepare authorized draw-order measurement and18-context regression suite."""
from pathlib import Path
from hashlib import sha256
import json, shutil, struct, zlib

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/draw-order-test-private-v1'
OLD=ROOT/'build/demand-spells-private-v1'
VERSION='1.19-draw-order1'

def digest(p):return sha256(p.read_bytes()).hexdigest()
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')

def main():
 assert not OUT.exists()
 qualified=json.loads((ROOT/'build/draw-order-private-v1/qualification.json').read_text())
 assert qualified['passed'] and qualified['raw_graphics_PCM_geometry_calls']==43200
 assert json.loads((ROOT/'build/draw-order-private-v1/seams.json').read_text())['passed']
 OUT.mkdir();shutil.copytree(OLD/'runner',OUT/'runner')
 for p in (OUT/'runner').glob('*.[ch]'):write(p,p.read_text().replace('1.19-demand-spells1',VERSION))
 for p in OLD.glob('*.h'):shutil.copy2(p,OUT/p.name)
 variants=['reference','demand','boundary']
 sources=[ROOT/'build/demand-visible-private-v3/core/snes9x2005_plus_libretro.so',
          ROOT/'build/draw-order-private-v1/priority/snes9x2005_plus_libretro.so',
          ROOT/'build/draw-order-private-v1/boundary/snes9x2005_plus_libretro.so']
 (OUT/'cores').mkdir()
 for v,p in zip(variants,sources):shutil.copy2(p,OUT/f'cores/{v}.so')
 plan=json.loads((OLD/'plan.json').read_text());runs=[]
 # Two full regression passes, with reversed fixture order.
 for repeat in range(2):
  for c in plan['cases'] if not repeat else reversed(plan['cases']):
   runs.append({'run':len(runs),'fixture':c['seq'],'name':c['name'],'variant':'demand','variant_id':1,'repeat':repeat,'block':'regression'})
 # Each price block compares raw v3, boundary only and the same-boundary candidate.
 for repeat in range(2):
  for fixture in ([1,8] if not repeat else [8,1]):
   for v in (variants if not repeat else list(reversed(variants))):
    runs.append({'run':len(runs),'fixture':fixture,'name':plan['cases'][fixture]['name'],'variant':v,'variant_id':variants.index(v),'repeat':repeat+2,'block':'pricing'})
 assert len(runs)==48
 head='struct full_run{unsigned fixture,variant,repeat;};\nstatic const char *full_variants[]={'+','.join('"'+v+'"' for v in variants)+'};\n'
 head+='static const char *spell_names[]={'+','.join('"'+c['name']+'"' for c in plan['cases'])+'};\n'
 head+='static const struct full_run full_runs[]={'+','.join('{%d,%d,%d}'%(r['fixture'],r['variant_id'],r['repeat']) for r in runs)+'};\n#define D35_FULL_RUNS 48u\n'
 write(OUT/'combined-identity.h',head);write(OUT/'main.c',(OLD/'main.c').read_text().replace('1.19-demand-spells1',VERSION))
 migrations=[]
 for c in plan['cases']:
  dest=OUT/f"cases/{c['seq']:03d}";dest.mkdir(parents=True)
  src=ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}";raw=(src/'scene.state').read_bytes()
  assert zlib.crc32(raw[40:])&0xffffffff==struct.unpack_from('<I',raw,32)[0]
  for v in variants if c['seq'] in (1,8) else ['demand']:
   cb=(OUT/f'cores/{v}.so').read_bytes();h=bytearray(raw[:40]);struct.pack_into('<II',h,20,zlib.crc32(cb)&0xffffffff,len(cb))
   p=dest/f'{v}.state';p.write_bytes(h+raw[40:]);assert p.read_bytes()[40:]==raw[40:]
   migrations.append({'fixture':c['seq'],'variant':v,'payload_unchanged':True,'state_sha256':digest(p)})
  for name in ('input.txt','expected.bin','case.json'):shutil.copy2(src/name,dest/name)
 for name in ('ROM-PATH.txt','launch.sh','dispatch.sh'):
  write(OUT/name,(OLD/name).read_text().replace('snes-demand-spells1','snes-draw-order1').replace('1.19-demand-spells1',VERSION))
 plan.update(version=VERSION,variants=variants,runs=runs,snapshot_migrations=migrations,
  authorization='Implement draw order, keep APU compiler output stable, validate and put on I:; measurement candidate, not production promotion',
  coverage='18 candidate contexts twice; raw v3/fixed-APU control/same-APU priority on Meteor and Quasar in forward/reverse blocks',
  nominal_minutes=48*1200*plan['period_ns']/60e9,
  cores={v:{'sha256':digest(OUT/f'cores/{v}.so'),'crc32':f'{zlib.crc32((OUT/f"cores/{v}.so").read_bytes())&0xffffffff:08x}','bytes':(OUT/f'cores/{v}.so').stat().st_size} for v in variants})
 plan['limits']=['Net A7 draw-order saving and boundary cost remain unmeasured until this return.','No PC sampler, work arrays, nested phase clocks, frameskip or dropped audio.',
  'Byte-identical non-LTO APU object in boundary/priority; linked addresses/layout may differ.','Candidate must beat both boundary and raw v3 on valid matched intervals and full reserve/recovery; no assumed MHz or work-count speed claim.']
 write(OUT/'plan.json',json.dumps(plan,indent=2)+'\n')
 script=(ROOT/'build/build-demand-spells.sh').read_text().replace('build/demand-spells-private-v1','build/draw-order-test-private-v1').replace('"$(dirname "$0")/.."','"$(dirname "$0")/../.."')
 script=script.replace('"$out/cores/reference.so"','"$out/cores/reference.so" "$out/cores/boundary.so"');write(OUT/'build.sh',script)
 code=(ROOT/'build/qualify-demand-spells.py').read_text().replace('ROOT=Path(__file__).resolve().parent.parent','ROOT=Path(__file__).resolve().parents[2]').replace("ROOT/'build/demand-spells-private-v1'","ROOT/'build/draw-order-test-private-v1'")
 a=code.index(' q=json.loads(');b=code.index(' env=',a)
 code=code[:a]+''' q=json.loads((ROOT/'build/draw-order-private-v1/qualification.json').read_text());assert q['passed']
 for variant,label in [('demand','priority'),('boundary','boundary')]:
  matches=[r for r in q['comparisons'] if r['label']==label];assert len(matches)==18
  assert all(r['core_sha256']==plan['cores'][variant]['sha256'] for r in matches)
 assert plan['cores']['reference']['sha256']=='1eaf05f36adcbc8286de5777cc47f1cf24a588856a2b0a85e48a9bfa0984e6f8'
 assert json.loads((ROOT/'build/draw-order-private-v1/seams.json').read_text())['passed']
'''+code[b:]
 code=code.replace('==40','==48').replace("=='40'","=='48'").replace('40 epochs/48000','48 epochs/57600').replace('snes-demand-spells1','snes-draw-order1')
 code=code.replace("('prepare-demand-spells.py','build-demand-spells.sh','qualify-demand-spells.py')","('prepare-draw-order-test.py',)")
 code=code.replace("'core_exactness_reused_by_hash':['18 raw original-command v3 contexts','18 reference contexts']","'core_exactness_reused_by_hash':['18 priority contexts vs v3','18 boundary contexts vs v3','unchanged raw v3']")
 write(OUT/'qualify.py',code)
 report=(ROOT/'build/report-demand-spells.py').read_text().replace('1.19-demand-spells1',VERSION).replace('snes-demand-spells1','snes-draw-order1')
 a=report.index(' comparisons=[]');b=report.index(" return {'version':plan['version']",a)
 report=report[:a]+''' comparisons=[]
 for fixture in (1,8):
  for repeat in (2,3):
   for reference,candidate,label in [('reference','boundary','boundary_vs_raw'),('boundary','demand','priority_vs_boundary'),('reference','demand','priority_vs_raw')]:
    ref=records.get((fixture,repeat,reference),{});new=records.get((fixture,repeat,candidate),{})
    common=sorted(set(ref)&set(new));warm=[i for i in common if i>=120]
    windows=[warm[i:i+16] for i in range(max(0,len(warm)-15)) if warm[i+15]-warm[i]==15]
    chosen=max(windows,key=lambda w:statistics.mean(int(ref[j]['recorded_thread_CPU_ns']) for j in w)) if windows else []
    fixed={}
    for name,span in [('earlier',range(384,416)),('late',range(496,536))]:
     complete=all(j in ref and j in new for j in span)
     fixed[name]={'all_frames_valid_in_both':complete,'saving_ms':statistics.mean(int(ref[j]['recorded_thread_CPU_ns'])-int(new[j]['recorded_thread_CPU_ns']) for j in span)/1e6 if complete else None}
    comparisons.append({'fixture':fixture,'repeat':repeat,'comparison':label,'common_valid_calls':len(common),
     'warm_common_saving_ms':statistics.mean(int(ref[j]['recorded_thread_CPU_ns'])-int(new[j]['recorded_thread_CPU_ns']) for j in warm)/1e6 if warm else None,
     'reference_heavy_matched_frames':chosen,'mean_recorded_thread_CPU_saving_ms':statistics.mean(int(ref[j]['recorded_thread_CPU_ns'])-int(new[j]['recorded_thread_CPU_ns']) for j in chosen)/1e6 if chosen else None,
     'fixed_intervals':fixed,'interpretation':'Matched valid prefix; boundary cost and total result remain separate, no synthetic observer subtraction.'})
'''+report[b:]
 write(OUT/'report.py',report)
 print('Prepared48 automatic regression/pricing epochs; cores exact by qualification hashes; no card writes')

if __name__=='__main__':main()
