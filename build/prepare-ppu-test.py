"""Prepare authorized measurement-only PPU test from qualified ordinary cores."""
from pathlib import Path
from hashlib import sha256
import json,shutil,struct,zlib
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ppu-test-private-v1'
OLD=ROOT/'build/demand-spells-private-v1'
VERSION='1.19-ppu-test1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def main():
 assert not OUT.exists()
 published=json.loads((ROOT/'evidence/2026-10-14/ppu-refinements/inputs.json').read_text())
 for n,h in published.items():assert digest(ROOT/n)==h,n
 oldq=json.loads((OLD/'verification.json').read_text())
 for group in ('source_hashes','payload_hashes','proof_hashes'):
  for n,h in oldq[group].items():assert digest(ROOT/n if group=='source_hashes' else OLD/n)==h,n
 OUT.mkdir();shutil.copytree(OLD/'runner',OUT/'runner')
 for p in (OUT/'runner').glob('*.[ch]'):write(p,p.read_text().replace('1.19-demand-spells1',VERSION))
 for p in OLD.glob('*.h'):shutil.copy2(p,OUT/p.name)
 variants=['reference','demand','obj','shapes','bulk']
 cores=[ROOT/'build/demand-visible-private-v3/core/snes9x2005_plus_libretro.so',ROOT/'build/ppu-refinements-private-v5/combined/snes9x2005_plus_libretro.so']
 cores += [ROOT/f'build/ppu-refinements-private-v4/{v}/snes9x2005_plus_libretro.so' for v in variants[2:]]
 (OUT/'cores').mkdir()
 for v,p in zip(variants,cores):shutil.copy2(p,OUT/f'cores/{v}.so')
 plan=json.loads((OLD/'plan.json').read_text());runs=plan['runs']
 for repeat in range(2):
  for fixture in ([1,8] if not repeat else [8,1]):
   for v in (['reference','obj','shapes','bulk'] if not repeat else ['bulk','shapes','obj','reference']):
    runs.append({'run':len(runs),'fixture':fixture,'name':plan['cases'][fixture]['name'],'variant':v,'variant_id':variants.index(v),'repeat':repeat+2})
 assert len(runs)==56
 head='struct full_run{unsigned fixture,variant,repeat;};\nstatic const char *full_variants[]={'+','.join('"'+v+'"' for v in variants)+'};\n'
 head+='static const char *spell_names[]={'+','.join('"'+c['name']+'"' for c in plan['cases'])+'};\n'
 head+='static const struct full_run full_runs[]={'+','.join('{%d,%d,%d}'%(r['fixture'],r['variant_id'],r['repeat']) for r in runs)+'};\n#define D35_FULL_RUNS 56u\n'
 write(OUT/'combined-identity.h',head)
 write(OUT/'main.c',(OLD/'main.c').read_text().replace('1.19-demand-spells1',VERSION))
 migrations=[]
 for c in plan['cases']:
  dest=OUT/f"cases/{c['seq']:03d}";dest.mkdir(parents=True)
  src=ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}";raw=(src/'scene.state').read_bytes()
  assert zlib.crc32(raw[40:])&0xffffffff==struct.unpack_from('<I',raw,32)[0]
  for v in variants if c['seq'] in (1,8) else ['demand']:
   cb=(OUT/f'cores/{v}.so').read_bytes();h=bytearray(raw[:40]);struct.pack_into('<II',h,20,zlib.crc32(cb)&0xffffffff,len(cb));p=dest/f'{v}.state';p.write_bytes(h+raw[40:])
   assert p.read_bytes()[40:]==raw[40:];migrations.append({'fixture':c['seq'],'variant':v,'payload_unchanged':True,'state_sha256':digest(p)})
  for name in ('input.txt','expected.bin','case.json'):shutil.copy2(src/name,dest/name)
 shutil.copy2(OLD/'ROM-PATH.txt',OUT/'ROM-PATH.txt')
 for name in ('launch.sh','dispatch.sh'):write(OUT/name,(OLD/name).read_text().replace('snes-demand-spells1','snes-ppu-test1').replace('1.19-demand-spells1',VERSION))
 plan.update(version=VERSION,authorization='Arm I after general PPU fixes; measurement-only exception to missing new A7 prices',variants=variants,runs=runs,snapshot_migrations=migrations,
  coverage='18 contexts final twice, demand-v3 Meteor/Quasar AB/BA; isolated obj/shapes/bulk with demand-v3 in forward/reverse blocks.',
  nominal_minutes=56*1200*plan['period_ns']/60e9,
  cores={v:{'sha256':digest(OUT/f'cores/{v}.so'),'crc32':f'{zlib.crc32((OUT/f"cores/{v}.so").read_bytes())&0xffffffff:08x}','bytes':(OUT/f'cores/{v}.so').stat().st_size} for v in variants})
 plan['limits']=['New A7 unit prices and residual audio deficit unknown; explicit measurement-only install, no production promotion.','No row-cache core or nested PPU timers.','Isolated shape variant includes opaque/clip/sparse plain/math together.','Full effect/recovery and cumulative reserve/pointer validity required; no assumed MHz.']
 write(OUT/'plan.json',json.dumps(plan,indent=2)+'\n')
 rootfix="ROOT=Path(__file__).resolve().parents[2]"
 s=(ROOT/'build/build-demand-spells.sh').read_text().replace('build/demand-spells-private-v1','build/ppu-test-private-v1').replace('"$(dirname "$0")/.."','"$(dirname "$0")/../.."');write(OUT/'build.sh',s)
 s=(ROOT/'build/qualify-demand-spells.py').read_text().replace('ROOT=Path(__file__).resolve().parent.parent',rootfix).replace("ROOT/'build/demand-spells-private-v1'","ROOT/'build/ppu-test-private-v1'")
 start=s.index(' q=json.loads(');end=s.index(' env=',start)
 s=s[:start]+''' q=json.loads((ROOT/'build/ppu-refinements-private-v5/qualification.json').read_text());assert q['passed']
 assert all(r['core_sha256']==plan['cores']['demand']['sha256'] for r in q['comparisons'] if r['label']=='combined')
 for v in ('obj','shapes','bulk'):
  q=json.loads((ROOT/'build/ppu-refinements-private-v4/qualification.json').read_text());assert q['passed']
  assert len([r for r in q['comparisons'] if r['label']==v])==18
  assert all(r['core_sha256']==plan['cores'][v]['sha256'] for r in q['comparisons'] if r['label']==v)
'''+s[end:]
 s=s.replace('==40','==56').replace("=='40'","=='56'").replace('40 epochs/48000','56 epochs/67200').replace('snes-demand-spells1','snes-ppu-test1')
 s=s.replace("('prepare-demand-spells.py','build-demand-spells.sh','qualify-demand-spells.py')","('prepare-ppu-test.py',)")
 write(OUT/'qualify.py',s)
 s=(ROOT/'build/install-demand-spells.py').read_text().replace('ROOT=Path(__file__).resolve().parent.parent',rootfix).replace('build/demand-spells-private-v1','build/ppu-test-private-v1').replace('demand-spells','ppu-test').replace('demand-spells1','ppu-test1')
 s=s.replace("(ROOT/'docs/snes-ppu-test-test.txt')","(OUT/'TEST-ME.txt')")
 write(OUT/'install.py',s)
 s=(ROOT/'build/report-demand-spells.py').read_text().replace('1.19-demand-spells1',VERSION).replace('snes-demand-spells1','snes-ppu-test1')
 # Retain baseline/combo pairs; explicitly price isolated blocks against their own controls.
 anchor=" return {'version':plan['version']"
 extra=''' for fixture in (1,8):
  for repeat in (2,3):
   ref=records.get((fixture,repeat,'reference'),{})
   for variant in ('obj','shapes','bulk'):
    new=records.get((fixture,repeat,variant),{});both=sorted(set(ref)&set(new));warm=[i for i in both if i>=plan['warmup_calls']]
    windows=[warm[i:i+16] for i in range(max(0,len(warm)-15)) if warm[i+15]-warm[i]==15]
    chosen=max(windows,key=lambda w:statistics.mean(int(ref[j]['recorded_thread_CPU_ns']) for j in w)) if windows else []
    saving=statistics.mean(int(ref[j]['recorded_thread_CPU_ns'])-int(new[j]['recorded_thread_CPU_ns']) for j in chosen)/1e6 if chosen else None
    comparisons.append({'fixture':fixture,'repeat':repeat,'variant':variant,'reference_heavy_matched_frames':chosen,'mean_recorded_thread_CPU_saving_ms':saving,'interpretation':'isolated family, observers included, valid prefix only'})
'''
 assert s.count(anchor)==1;s=s.replace(anchor,extra+anchor);write(OUT/'report.py',s)
 write(OUT/'TEST-ME.txt','PPU measurement-only: cold boot, allow 25-30 minutes for56 epochs; wait for stock launcher, power down, return I. Select+Start aborts. Next reboot stock. No production acceptance claimed.\n')
 print('Prepared56 PPU pricing/regression epochs; unchanged private state payloads; no card writes')
if __name__=='__main__':main()
