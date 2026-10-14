"""Three hash-pinned controls x eight contexts x two orders, measurement only."""
from pathlib import Path
from hashlib import sha256
import json,shutil,struct,zlib,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/combined-test-private-v1'
OLD=ROOT/'build/fullpaths-private-v2'
BASE=ROOT/'build/ability-regression-private-v1'
SELECT=(0,1,3,5,6,7,8,10)
NAMES=('baseline','prior','combined')
AUTH='Archive I: first, then stage all the combined improvements for an automated test of the eight failing abilities. Keep every frame and measure the actual A7 savings and headroom.'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def prepare(archive):
 assert archive.is_relative_to(ROOT/'device-evidence') and (archive/'archive.json').exists()
 assert not OUT.exists();OUT.mkdir();(OUT/'cores').mkdir()
 frozen=json.loads((OLD/'verification.json').read_text())
 for key in ('source_hashes','payload_hashes','proof_hashes'):
  for name,h in frozen[key].items():assert digest(ROOT/name)==h,name
 prior=json.loads((OLD/'plan.json').read_text());new=json.loads((ROOT/'evidence/2026-10-13/common-renderer/band-v3.json').read_text())
 latest=ROOT/'build/common-band-private-v3/plus-a7.so'
 assert new['passed'] and all(r['core_sha256']==digest(latest) for r in new['exact'] if r['label']=='ordinary')
 cores={'baseline':OLD/'cores/baseline.so','prior':OLD/'cores/combined.so','combined':latest}
 assert digest(cores['baseline'])==prior['cores']['baseline']['sha256'] and digest(cores['prior'])==prior['cores']['combined']['sha256']
 for name,p in cores.items():shutil.copy2(p,OUT/f'cores/{name}.so')
 shutil.copytree(OLD/'runner',OUT/'runner')
 for p in OLD.glob('*.h'):
  if p.name!='fullpaths-identity.h':shutil.copy2(p,OUT/p.name)
 for p in (OUT/'runner').glob('*.[ch]'):p.write_text(p.read_text().replace('1.19-fullpaths1','1.19-combined1'),newline='\n')
 p=OUT/'runner/pair-host.h';s=p.read_text();assert s.count('#include "fullpaths-headroom.h"')==1;s=s.replace('"fullpaths-headroom.h"','"combined-headroom.h"').replace('    memset(pair_rows,0,sizeof(pair_rows));pair_count=0;','    combined_cleanup_wall=0;\n    memset(pair_rows,0,sizeof(pair_rows));pair_count=0;');p.write_text(s,newline='\n')
 shutil.copy2(ROOT/'build/combined-headroom.h',OUT/'runner/combined-headroom.h')
 (OUT/'runner/fullpaths-headroom.h').unlink() # Owned new local copy only.
 p=OUT/'runner/runner.c';s=p.read_text();assert s.count('    audio_pipe_stop(!s.failed); pump_audio();')==1
 s=s.replace('    audio_pipe_stop(!s.failed); pump_audio();','    uint64_t combined_cleanup_began=board_now_ns();\n    audio_pipe_stop(!s.failed); pump_audio();').replace('    board_wait_display();\n    if(s.loaded','    board_wait_display();\n    combined_cleanup_wall=board_now_ns()-combined_cleanup_began;\n    if(s.loaded');p.write_text(s,newline='\n')
 shutil.copy2(ROOT/'build/combined-test-main.c',OUT/'main.c')
 shutil.copy2(OLD/'ROM-PATH.txt',OUT/'ROM-PATH.txt')
 wrapper=(OLD/'launch.sh').read_text().replace('snes-fullpaths1','snes-combined1').replace('1.19-fullpaths1','1.19-combined1')
 (OUT/'launch.sh').write_text(wrapper,newline='\n');(OUT/'dispatch.sh').write_text('#!/bin/sh\nexec /usr/retro/snes-combined1/launch.sh\n',newline='\n')
 cases=[c for c in json.loads((BASE/'plan.json').read_text())['cases'] if c['seq'] in SELECT];runs=[]
 for repeat in range(2):
  for c in (cases if repeat==0 else list(reversed(cases))):
   for vi in (range(3) if repeat==0 else reversed(range(3))):runs.append({'run':len(runs),'fixture':c['seq'],'variant':NAMES[vi],'variant_id':vi,'repeat':repeat})
 header='#ifndef COMBINED_IDENTITY_H\n#define COMBINED_IDENTITY_H\nstruct full_run{unsigned fixture,variant,repeat;};\n'
 header+='static const char *full_variants[]={'+','.join('"'+x+'"' for x in NAMES)+'};\nstatic const struct full_run full_runs[]={'+','.join('{%d,%d,%d}'%(r['fixture'],r['variant_id'],r['repeat']) for r in runs)+'};\n#define D35_FULL_RUNS 48u\n#endif\n'
 (OUT/'combined-identity.h').write_text(header,newline='\n')
 migrations=[]
 for c in cases:
  dest=OUT/f"cases/{c['seq']:03d}";dest.mkdir(parents=True)
  raw=(BASE/f"cases/{c['seq']:03d}/scene.state").read_bytes();assert raw[:8]==b'D35MVP01' and zlib.crc32(raw[40:])==struct.unpack_from('<I',raw,32)[0]
  for name in NAMES:
   data=(OUT/f'cores/{name}.so').read_bytes();head=bytearray(raw[:40]);struct.pack_into('<II',head,20,zlib.crc32(data),len(data));p=dest/f'{name}.state';p.write_bytes(head+raw[40:]);assert p.read_bytes()[40:]==raw[40:]
   migrations.append({'fixture':c['seq'],'variant':name,'state_sha256':digest(p),'payload_sha256':sha256(raw[40:]).hexdigest(),'payload_unchanged':True})
  for name in ('input.txt','expected.bin','case.json'):shutil.copy2(BASE/f"cases/{c['seq']:03d}/{name}",dest/name)
 plan={'version':'1.19-combined1','archive':archive.name,'authorization':AUTH,'measurement_only':True,'production_gate_passed':False,'frameskip':False,'calls_per_run':1200,'warmup_calls':120,'headroom_fraction':.2,'period_ns':16688154.5,'target_ns':13350523.6,'runs':runs,'cases':cases,'variants':list(NAMES),'snapshot_migrations':migrations,'cores':{n:{'sha256':digest(OUT/f'cores/{n}.so'),'crc32':'%08x'%zlib.crc32((OUT/f'cores/{n}.so').read_bytes()),'bytes':(OUT/f'cores/{n}.so').stat().st_size} for n in NAMES},'nominal_minutes':48*1200*16.6881545/60000,'comparisons':['baseline -> combined overall','prior -> combined new renderer increment','baseline -> prior unchanged control'],'combined_includes':['ability2 window generalization','fixed-color row batching','true-subscreen composition','unused DSP interpolation removal','early depth rejection','sole-BG3 subscreen production','constant-mode background bands','eight batch-local palettes','opaque depth stores']}
 (OUT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
 s=(ROOT/'build/build-fullpaths.sh').read_text().replace('build/fullpaths-private-v2',str(OUT.relative_to(ROOT)).replace('\\','/'))
 start=s.index('if [ ! -e "$out/cores/combined.so" ]; then');end=s.index("libs=",start);s=s[:start]+s[end:]
 s=s.replace('Built five-core measurement suite','Built three-core combined measurement suite')
 s=s.replace('"$out/compare.c"','"build/fullpaths-private-v2/compare.c"')
 (ROOT/'build/build-combined-test.sh').write_text(s,newline='\n')
 print('Prepared48 runs,24 unchanged-state-payload migrations, three frozen cores; no card writes')
if __name__=='__main__':prepare(Path(sys.argv[1]).resolve())
