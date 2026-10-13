"""Own a five-core measurement-only crossover; immutable old builds/card."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,shutil,struct,zlib
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/fullpaths-private-v2'
BASE=ROOT/'build/ability-regression-private-v1'
NAMES=('baseline','fixed','subscreen','dsp','combined')
SELECT=(0,1,3,5,6,7,8,10,16,17)
AUTH='Stage an automated test on I: to measure the actual A7 savings for these three paths, separately and combined. Keep every frame and log whether we have enough headroom.'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def module(name):
 spec=importlib.util.spec_from_file_location(name,ROOT/f'build/prepare-{name}.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def change(p,old,new,count=1):
 s=p.read_text();assert s.count(old)==count,(p,old,s.count(old));p.write_text(s.replace(old,new),newline='\n')
def prepare():
 assert not OUT.exists();OUT.mkdir();(OUT/'cores').mkdir()
 existing={'baseline':BASE/'plus-a7.so','fixed':ROOT/'build/fixed-rows-private-v3/plus-a7.so',
 'subscreen':ROOT/'build/subscreen-rows-private-v1/plus-a7.so','dsp':ROOT/'build/dsp-dead-work-private-v1/plus-a7.so'}
 expected=('53c6d1f6c0253cb1c6e7b81ba22192f3739fa3f9605837c64691085918e1106b','a3bd2a9772d7388cd3f0986c5c867463485483b5d1330cd4b76e21a0e6a075c5','8a450dbb9bdef49d218fe7aa6403372401ea87f8c1b4553e630f685607c564fd','d6ac3b9714d63caf79b5df55ac62e1667b4e3377cf4fe1405fa5fb985bac018a')
 for (name,p),h in zip(existing.items(),expected):assert digest(p)==h;shutil.copy2(p,OUT/f'cores/{name}.so')
 shutil.copytree(ROOT/'build/fixed-rows-private-v3/core',OUT/'combined-core',ignore=shutil.ignore_patterns('*.o','*.so'))
 module('subscreen-rows').patch(OUT/'combined-core');module('dsp-dead-work').patch(OUT/'combined-core')
 shutil.copytree(BASE/'runner',OUT/'runner')
 for p in BASE.glob('*.h'):shutil.copy2(p,OUT/p.name)
 for p in (OUT/'runner').glob('*.[ch]'):p.write_text(p.read_text().replace('1.19-ability2','1.19-fullpaths1'),newline='\n')
 shutil.copy2(ROOT/'build/fullpaths-headroom.h',OUT/'runner/fullpaths-headroom.h')
 p=OUT/'runner/audio-pipe.h';change(p,'int audio_pipe_admit(unsigned frames,int paced);','int audio_pipe_admit(unsigned frames,int paced);\nuint64_t audio_pipe_pacing_wait_ns(void);')
 p=OUT/'runner/audio-owner.c'
 change(p,'int audio_pipe_admit(unsigned frames,int paced)','static uint64_t full_pacing_wait;\nuint64_t audio_pipe_pacing_wait_ns(void){return full_pacing_wait;}\nint audio_pipe_admit(unsigned frames,int paced)')
 change(p,'    pipe_state.admitting=paced;','    pipe_state.admitting=paced;full_pacing_wait=0;')
 old='''        if(changed(&until)<0) { rc=-1; break; }
    }
    if(pipe_state.stats.error) { errno=pipe_state.stats.error; rc=-1; }
    else if(pipe_state.stop)'''
 new='''        int pure_pacing=paced && pipe_state.refresh_done>=request &&
            pipe_state.count<=AUDIO_CAPACITY-frames &&
            pipe_state.count+pipe_state.device.queued>pipe_state.device.prime;
        uint64_t before=pure_pacing?board_now_ns():0;
        int changed_rc=changed(&until);
        if(pure_pacing)full_pacing_wait+=board_now_ns()-before;
        if(changed_rc<0) { rc=-1; break; }
    }
    if(pipe_state.stats.error) { errno=pipe_state.stats.error; rc=-1; }
    else if(pipe_state.stop)'''
 change(p,old,new)
 p=OUT/'runner/pair-host.h'
 change(p,'    unsigned frame;','    unsigned frame,pointer_valid;\n    uint64_t pace_wait,main_step_cpu,identity_observer;')
 change(p,'static long pair_before_khz;','static long pair_before_khz;\nstatic uint64_t full_step_cpu;\n#include "fullpaths-headroom.h"\nstatic void pair_step_begin(void){full_step_cpu=thread_cpu_ns();}')
 change(p,'    audio_pipe_stats(&r->audio);board_video_metrics(&r->video,0);','''    audio_pipe_stats(&r->audio);r->audio.worker_cpu_ns=audio_pipe_live_cpu();board_video_metrics(&r->video,0);
    r->pace_wait=audio_pipe_pacing_wait_ns();r->main_step_cpu=thread_cpu_ns()-full_step_cpu;
    r->identity_observer=ability_last_observer_ns();
    r->pointer_valid=r->audio.boundary && r->audio.appl_ptr%r->audio.boundary==r->audio.epoch_transferred%r->audio.boundary;''')
 change(p,'    if(!cost_host.started)return;','    if(!cost_host.started)return;\n    full_headroom(dir,mock,failed);')
 change(p,'submitted,flipped\\n','submitted,flipped,pace_wait_ns,main_step_cpu_ns,identity_observer_ns,pointer_valid\\n')
 change(p,'%llu,%llu\\n",\n            r->frame','%llu,%llu,%llu,%llu,%llu,%u\\n",\n            r->frame')
 change(p,'(unsigned long long)r->video.flipped);','(unsigned long long)r->video.flipped,(unsigned long long)r->pace_wait,(unsigned long long)r->main_step_cpu,(unsigned long long)r->identity_observer,r->pointer_valid);')
 p=OUT/'runner/ability-observer.h';change(p,'static void ability_finish(const char *dir)', 'static uint64_t ability_last_observer_ns(void){return ability_count?ability_rows[ability_count-1].observer_ns:0;}\nstatic void ability_finish(const char *dir)')
 p=OUT/'runner/runner.c'
 change(p,'#include "pair-host.h"\n#include "ability-observer.h"','#include "ability-observer.h"\n#include "pair-host.h"')
 # Observer requires cost_host clock declared before it. Move frequency header first.
 change(p,'#include "ability-observer.h"','#include "frequency-host.h"\n#include "ability-observer.h"')
 # pair-host now calls the existing thread-clock helper before its old declaration.
 change(p,'#include "frequency-host.h"','#include <stdint.h>\nstatic uint64_t thread_cpu_ns(void);\n#include "frequency-host.h"')
 assert '    p_profile_begin=NULL;p_profile_end=NULL;' in p.read_text() # Already disabled in qualified baseline.
 change(p,'        uint64_t audio_before=s.audio_ns,video_before=s.video_ns;', '        pair_step_begin();\n        uint64_t audio_before=s.audio_ns,video_before=s.video_ns;')
 after='        pair_after((unsigned)s.runs-1,cpu_end>=cpu_start?cpu_end-cpu_start:0,elapsed,admission,step_start,s.generated);'
 change(p,after,'')
 change(p,'        if(board_now_ns()>deadline+250000000u) deadline=board_now_ns();','        if(board_now_ns()>deadline+250000000u) deadline=board_now_ns();\n'+after)
 shutil.copy2(ROOT/'build/fullpaths-main.c',OUT/'main.c')
 for n in ('compare.c','ROM-PATH.txt'):shutil.copy2(BASE/n,OUT/n)
 wrapper=(BASE/'launch.sh').read_text().replace('snes-ability2','snes-fullpaths1').replace('1.19-ability2','1.19-fullpaths1')
 (OUT/'launch.sh').write_text(wrapper,newline='\n');(OUT/'dispatch.sh').write_text('#!/bin/sh\nexec /usr/retro/snes-fullpaths1/launch.sh\n',newline='\n')
 old=json.loads((BASE/'plan.json').read_text());cases=[c for c in old['cases'] if c['seq'] in SELECT]
 runs=[]
 for repeat in range(2):
  for c in (cases if repeat==0 else list(reversed(cases))):
   for v in (range(5) if repeat==0 else reversed(range(5))):runs.append({'run':len(runs),'fixture':c['seq'],'variant':NAMES[v],'variant_id':v,'repeat':repeat})
 header='#ifndef FULLPATHS_IDENTITY_H\n#define FULLPATHS_IDENTITY_H\nstruct full_run{unsigned fixture,variant,repeat;};\n'
 header+='static const char *full_variants[]={'+','.join('"'+s+'"' for s in NAMES)+'};\n'
 header+='static const struct full_run full_runs[]={'+','.join('{%d,%d,%d}'%(r['fixture'],r['variant_id'],r['repeat']) for r in runs)+'};\n#define D35_FULL_RUNS 100u\n#endif\n'
 (OUT/'fullpaths-identity.h').write_text(header,newline='\n')
 (OUT/'plan.json').write_text(json.dumps({'version':'1.19-fullpaths1','authorization':AUTH,'measurement_only':True,'frameskip':False,'calls_per_run':1200,'runs':runs,'cases':cases,'variants':list(NAMES),'warmup_calls':120,'headroom_fraction':0.20,'period_ns':16688154.5,'target_ns':13350523.6,'nominal_minutes':100*1200*16.6881545/60000,'production_gate_passed':False},indent=2)+'\n')
 print('Prepared 100-run two-order measurement suite; no card writes')
def migrate():
 plan=json.loads((OUT/'plan.json').read_text());entries=[]
 for c in plan['cases']:
  target=OUT/f"cases/{c['seq']:03d}";target.mkdir(parents=True)
  raw=(BASE/f"cases/{c['seq']:03d}/scene.state").read_bytes();assert raw[:8]==b'D35MVP01' and zlib.crc32(raw[40:])==struct.unpack_from('<I',raw,32)[0]
  for name in NAMES:
   core=OUT/f'cores/{name}.so';head=bytearray(raw[:40]);struct.pack_into('<II',head,20,zlib.crc32(core.read_bytes()),core.stat().st_size)
   p=target/f'{name}.state';p.write_bytes(head+raw[40:]);assert p.read_bytes()[40:]==raw[40:]
   entries.append({'fixture':c['seq'],'variant':name,'state_sha256':digest(p),'payload_sha256':sha256(raw[40:]).hexdigest(),'payload_unchanged':True})
  for n in ('input.txt','expected.bin','case.json'):shutil.copy2(BASE/f"cases/{c['seq']:03d}/{n}",target/n)
 plan['snapshot_migrations']=entries;plan['cores']={name:{'sha256':digest(OUT/f'cores/{name}.so'),'crc32':'%08x'%zlib.crc32((OUT/f'cores/{name}.so').read_bytes()),'bytes':(OUT/f'cores/{name}.so').stat().st_size} for name in NAMES}
 (OUT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');print('Migrated only 50 identity headers; logical payloads unchanged')
if __name__=='__main__':
 import sys
 if len(sys.argv)>1 and sys.argv[1]=='migrate':migrate()
 else:prepare()
