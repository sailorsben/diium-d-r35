"""Prepare an unchanged-core diagnostic; no optimization payload or card access."""
from pathlib import Path
from hashlib import sha256
import json,shutil,struct,zlib
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/current-pc-profile-private-v1';OLD=ROOT/'build/ppu-test-private-v1'
VERSION='1.19-pc-profile1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def once(s,a,b):assert s.count(a)==1,a;return s.replace(a,b)
def main():
 assert not OUT.exists();OUT.mkdir();shutil.copytree(OLD/'runner',OUT/'runner')
 for p in OLD.glob('*.h'):shutil.copy2(p,OUT/p.name)
 shutil.copy2(ROOT/'build/main-pc-sampler.h',OUT/'main-pc-sampler.h')
 for p in (OUT/'runner').glob('*.[ch]'):write(p,p.read_text().replace('1.19-ppu-test1',VERSION))
 p=OUT/'runner/runner.c';s=p.read_text();s=once(s,'#include <errno.h>','#include <errno.h>\n#include "../main-pc-sampler.h"\nstatic unsigned pc_requested;')
 s=once(s,'    memset(&s,0,sizeof(s)); memset(&native_av,0,sizeof(native_av));','    pc_requested=getenv("D35_PC_SAMPLE")!=NULL;\n    memset(&s,0,sizeof(s)); memset(&native_av,0,sizeof(native_av));')
 s=once(s,'    progress("running",1);','    if(pc_requested&&pc_start_timer((void *)p_retro_run)){fail("Main PC sampler unavailable: errno=%d",pc_sample.error);goto done;}\n    progress("running",1);')
 s=once(s,'        p_retro_run();','        if(pc_requested)pc_enter_frame((unsigned)s.runs);\n        p_retro_run();\n        if(pc_requested)pc_leave_frame();')
 s=once(s,'    pcm_cost_flush(s.save_dir);','    if(pc_requested){pc_stop_timer();if(pc_flush(s.save_dir)&&!s.failed)fail("PC sample flush failed");}\n    pcm_cost_flush(s.save_dir);')
 write(p,s)
 core=ROOT/'build/demand-visible-private-v3/core/snes9x2005_plus_libretro.so';assert digest(core)=='1eaf05f36adcbc8286de5777cc47f1cf24a588856a2b0a85e48a9bfa0984e6f8'
 (OUT/'cores').mkdir()
 for v in ('reference','demand'):shutil.copy2(core,OUT/f'cores/{v}.so')
 plan=json.loads((OLD/'plan.json').read_text());runs=[]
 for fixture,variants in [(1,['reference','demand']),(8,['demand','reference'])]:
  for v in variants:runs.append({'run':len(runs),'fixture':fixture,'name':plan['cases'][fixture]['name'],'variant':v,'variant_id':int(v=='demand'),'repeat':0,'PC_sampling':v=='demand'})
 head='struct full_run{unsigned fixture,variant,repeat;};\nstatic const char *full_variants[]={"reference","demand"};\n'
 head+='static const char *spell_names[]={'+','.join('"'+c['name']+'"' for c in plan['cases'])+'};\n'
 head+='static const struct full_run full_runs[]={'+','.join('{%d,%d,%d}'%(r['fixture'],r['variant_id'],r['repeat']) for r in runs)+'};\n#define D35_FULL_RUNS 4u\n';write(OUT/'combined-identity.h',head)
 s=(OLD/'main.c').read_text().replace('1.19-ppu-test1',VERSION)
 s=once(s,'  setenv("D35_FULL_VARIANT",','  if(r->variant)setenv("D35_PC_SAMPLE","1",1);else unsetenv("D35_PC_SAMPLE");\n  setenv("D35_FULL_VARIANT",');write(OUT/'main.c',s)
 shutil.copytree(OLD/'cases',OUT/'cases')
 for folder in (OUT/'cases').iterdir():
  if not folder.is_dir():continue
  for state in folder.glob('*.state'):
   raw=state.read_bytes();h=bytearray(raw[:40]);cb=core.read_bytes();struct.pack_into('<II',h,20,zlib.crc32(cb)&0xffffffff,len(cb));state.write_bytes(h+raw[40:])
 for name in ('launch.sh','dispatch.sh','ROM-PATH.txt'):
  write(OUT/name,(OLD/name).read_text().replace('snes-ppu-test1','snes-pc-profile1').replace('1.19-ppu-test1',VERSION))
 plan.update(version=VERSION,runs=runs,variants=['reference','demand'],cores={v:{'sha256':digest(core),'crc32':f'{zlib.crc32(core.read_bytes())&0xffffffff:08x}','bytes':core.stat().st_size} for v in ('reference','demand')},
  authorization='Research requested; local measurement preparation only, not authorized for installation by this receipt',
  coverage='Same exact demand-v3 core; Meteor control/sample, Quasar sample/control; no emulator source instrumentation',
  limits=['PC samples are statistical owner evidence, not inner-kernel unit prices.','Timer requested1ms; kernel coalescing/overruns and actual sample counts must be reported, never weighted into invented samples.','Thread CPU timer unsupported or occupied signal fails explicitly.','Only valid pointer prefix accepted; sampling disturbance measured against unchanged-core control.','No new optimization core; installation/rearm pending separate instruction.'])
 plan['nominal_minutes']=4*1200*plan['period_ns']/60e9;write(OUT/'plan.json',json.dumps(plan,indent=2)+'\n')
 script=(ROOT/'build/build-demand-spells.sh').read_text().replace('build/demand-spells-private-v1','build/current-pc-profile-private-v1').replace('"$(dirname "$0")/.."','"$(dirname "$0")/../.."');write(OUT/'build.sh',script)
 code=(ROOT/'build/qualify-demand-spells.py').read_text().replace('ROOT=Path(__file__).resolve().parent.parent','ROOT=Path(__file__).resolve().parents[2]').replace("ROOT/'build/demand-spells-private-v1'","ROOT/'build/current-pc-profile-private-v1'")
 a=code.index(' q=json.loads(');b=code.index(' env=',a)
 code=code[:a]+''' q=json.loads((ROOT/'build/demand-visible-private-v3/qualification.json').read_text());assert q['passed']
 assert plan['cores']['reference']['sha256']==plan['cores']['demand']['sha256']=='1eaf05f36adcbc8286de5777cc47f1cf24a588856a2b0a85e48a9bfa0984e6f8'
'''+code[b:]
 code=code.replace('==40','==4').replace("=='40'","=='4'").replace('40 epochs/48000','4 epochs/4800').replace('snes-demand-spells1','snes-pc-profile1')
 code=code.replace("('prepare-demand-spells.py','build-demand-spells.sh','qualify-demand-spells.py')","('prepare-current-pc-profile.py','main-pc-sampler.h')")
 code=code.replace("'D35_ABILITY_INPUT':str(OUT/'cases/000/input.txt')","'D35_PC_SAMPLE':'1','D35_ABILITY_INPUT':str(OUT/'cases/000/input.txt')")
 write(OUT/'qualify.py',code)
 print('Prepared four unchanged-core PC/control diagnostic epochs; no card writes or install authorization')
if __name__=='__main__':main()
