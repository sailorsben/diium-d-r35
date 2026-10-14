"""Fresh automatic18-context demand-v3 test; no card writes or new core build."""
from pathlib import Path
from hashlib import sha256
import json,shutil,struct,zlib
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/demand-spells-private-v1'
OLD=ROOT/'build/combined-test-private-v1'
BASE=ROOT/'build/ability-regression-private-v1'
VERSION='1.19-demand-spells1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def replace(s,old,new):assert s.count(old)==1,old;return s.replace(old,new)
def main():
 assert not OUT.exists()
 frozen=ROOT/'build/demand-visible-private-v3/frozen.json'
 for n,h in json.loads(frozen.read_text()).items():assert digest(ROOT/n)==h,n
 q=json.loads((OLD/'verification.json').read_text())
 for group in ('source_hashes','payload_hashes','proof_hashes'):
  for n,h in q[group].items():assert digest(ROOT/n)==h,n
 OUT.mkdir();(OUT/'cores').mkdir()
 cores={'reference':ROOT/'build/common-band-private-v3/plus-a7.so','demand':ROOT/'build/demand-visible-private-v3/core/snes9x2005_plus_libretro.so'}
 assert digest(cores['reference'])=='e9c421e4e228a5c91eba112a8fd7ec9e0a3c66cc996ba6a6a86f995622ef8129'
 assert digest(cores['demand'])=='1eaf05f36adcbc8286de5777cc47f1cf24a588856a2b0a85e48a9bfa0984e6f8'
 for name,p in cores.items():shutil.copy2(p,OUT/f'cores/{name}.so')
 shutil.copytree(OLD/'runner',OUT/'runner',ignore=shutil.ignore_patterns('*.png','*.ppm','*-arm','ui-preview'))
 for p in OLD.glob('*.h'):shutil.copy2(p,OUT/p.name)
 for p in (OUT/'runner').glob('*.[ch]'):write(p,p.read_text().replace('1.19-combined1',VERSION))
 for name in ('board.c','board.h'):shutil.copy2(ROOT/'build/demand-private-v1/runtime-v1'/name,OUT/'runner'/name)
 p=OUT/'runner/runner.c';s=p.read_text()
 s=replace(s,'static void (*p_profile_begin)(unsigned);','static int (*p_output_acquire)(void *,size_t);\nstatic void (*p_profile_begin)(unsigned);')
 s=replace(s,'    p_profile_begin=NULL; p_profile_end=NULL;','    p_output_acquire=NULL;p_profile_begin=NULL; p_profile_end=NULL;')
 s=replace(s,'    *(void **)(&p_profile_begin)=dlsym(s.core,"d35_profile_begin");','    *(void **)(&p_output_acquire)=dlsym(s.core,"d35_output_acquire");\n    *(void **)(&p_profile_begin)=dlsym(s.core,"d35_profile_begin");')
 s=replace(s,'        if(p_profile_begin) p_profile_begin(sample);','        if(p_output_acquire){size_t bytes=0;void *target=board_video_target(&bytes);p_output_acquire(target,bytes);}\n        if(p_profile_begin) p_profile_begin(sample);')
 s=replace(s,'    if(s.core) dlclose(s.core);','    p_output_acquire=NULL;\n    if(s.core) dlclose(s.core);')
 write(p,s)
 # Persist actual direct/copy counts; old service/accounting columns stay intact.
 p=OUT/'runner/pair-host.h';s=p.read_text()
 s=replace(s,'identity_observer_ns,pointer_valid\\n','identity_observer_ns,pointer_valid,direct_submitted,copied_payload_bytes\\n')
 s=replace(s,'%llu,%llu,%llu,%u\\n",','%llu,%llu,%llu,%u,%llu,%llu\\n",')
 s=replace(s,'r->pointer_valid);','r->pointer_valid,(unsigned long long)r->video.direct_submitted,(unsigned long long)r->video.copied_payload_bytes);')
 write(p,s)
 # Disable optional frequency pinning even if the ambient environment asks for it.
 p=OUT/'runner/frequency-host.h';s=p.read_text()
 s=replace(s,'    cost_host.mode=mode?(unsigned)cost_parse(mode):0;','    (void)mode;cost_host.mode=0; /* read-only frequency observation */')
 write(p,s)
 cases=json.loads((BASE/'plan.json').read_text())['cases'];assert len(cases)==18
 runs=[]
 for repeat in range(2):
  for c in (cases if repeat==0 else list(reversed(cases))):
   variants=['reference','demand'] if c['seq'] in (1,8) else ['demand']
   if repeat:variants.reverse()
   for variant in variants:runs.append({'run':len(runs),'fixture':c['seq'],'name':c['name'],'variant':variant,'variant_id':int(variant=='demand'),'repeat':repeat})
 assert len(runs)==40
 header='struct full_run{unsigned fixture,variant,repeat;};\nstatic const char *full_variants[]={"reference","demand"};\n'
 header+='static const char *spell_names[]={'+','.join('"'+c['name']+'"' for c in cases)+'};\n'
 header+='static const struct full_run full_runs[]={'+','.join('{%d,%d,%d}'%(r['fixture'],r['variant_id'],r['repeat']) for r in runs)+'};\n#define D35_FULL_RUNS 40u\n'
 write(OUT/'combined-identity.h',header)
 s=(ROOT/'build/combined-test-main.c').read_text().replace('1.19-combined1',VERSION)
 s=s.replace('"snes-mvp/','"runner/')
 s=replace(s,'variant=%s\\nrepeat=%u\\nphase=before_audio_display_workers\\n",seq,r->fixture,full_variants[r->variant],r->repeat);','variant=%s\\nrepeat=%u\\nspell=%s\\nphase=before_audio_display_workers\\n",seq,r->fixture,full_variants[r->variant],r->repeat,spell_names[r->fixture]);')
 s=replace(s,'variant=%s repeat=%u\\n",seq,limit,r->fixture,full_variants[r->variant],r->repeat);','variant=%s spell=%s repeat=%u\\n",seq,limit,r->fixture,full_variants[r->variant],spell_names[r->fixture],r->repeat);')
 write(OUT/'main.c',s)
 migrations=[]
 for c in cases:
  dest=OUT/f"cases/{c['seq']:03d}";dest.mkdir(parents=True)
  src=BASE/f"cases/{c['seq']:03d}";raw=(src/'scene.state').read_bytes()
  assert raw[:8]==b'D35MVP01' and zlib.crc32(raw[40:])&0xffffffff==struct.unpack_from('<I',raw,32)[0]
  assert len(raw)==40+struct.unpack_from('<I',raw,28)[0]
  for variant in (['reference','demand'] if c['seq'] in (1,8) else ['demand']):
   cb=(OUT/f'cores/{variant}.so').read_bytes();head=bytearray(raw[:40]);struct.pack_into('<II',head,20,zlib.crc32(cb)&0xffffffff,len(cb))
   p=dest/f'{variant}.state';p.write_bytes(head+raw[40:]);assert p.read_bytes()[40:]==raw[40:]
   migrations.append({'fixture':c['seq'],'variant':variant,'payload_unchanged':True,'state_sha256':digest(p),'payload_sha256':sha256(raw[40:]).hexdigest()})
  for name in ('input.txt','expected.bin','case.json'):shutil.copy2(src/name,dest/name)
 shutil.copy2(OLD/'ROM-PATH.txt',OUT/'ROM-PATH.txt')
 write(OUT/'launch.sh',(OLD/'launch.sh').read_text().replace('snes-combined1','snes-demand-spells1').replace('1.19-combined1',VERSION))
 write(OUT/'dispatch.sh','#!/bin/sh\nexec /bin/sh /usr/retro/snes-demand-spells1/launch.sh\n')
 # New native fixture exercises this actual measurement runner's acquired output.
 p=OUT/'runner/ability-native-check.c';s=p.read_text()
 s=replace(s,'static uint64_t production_deadline;','static uint64_t production_deadline;\nstatic unsigned output_slot,direct_calls;\nstatic unsigned char output_slots[3][512*240+128] __attribute__((aligned(64)));\nvoid *board_video_target(size_t *bytes){*bytes=512*240+64;return output_slots[output_slot]+64;}')
 s=replace(s,'int board_video_reserve(void) { production_deadline=','int board_video_reserve(void) { output_slot=(output_slot+1)%3;production_deadline=')
 s=replace(s,'    assert(data && w && h && pitch>=w*2);','    assert(data && w && h && pitch>=w*2);\n    if(data==output_slots[output_slot]+64){assert(w==256&&h<=239&&pitch==512);++direct_calls;}\n    memset(output_slots[output_slot],0x93,sizeof(output_slots[output_slot]));')
 pos=s.rindex('    return 0;');s=s[:pos]+'    assert(direct_calls>=120);printf("PASS: %u direct-output callbacks in actual spell measurement runner\\n",direct_calls);\n'+s[pos:]
 write(p,s)
 plan={'version':VERSION,'authorization':'Put together a test for the spells that we have not fixed.','status':'LOCAL_BUILD_NOT_INSTALLED_OR_ARMED',
 'measurement_only':True,'production_gate_passed':False,'frameskip':False,'calls_per_run':1200,'warmup_calls':120,
 'period_ns':358416/21477272*1e9,'target_ns':358416/21477272*1e9*.8,'nominal_minutes':len(runs)*1200*358416/21477272/60,
 'variants':['reference','demand'],'cases':cases,'runs':runs,'snapshot_migrations':migrations,
 'cores':{n:{'sha256':digest(OUT/f'cores/{n}.so'),'crc32':f'{zlib.crc32((OUT/f"cores/{n}.so").read_bytes())&0xffffffff:08x}','bytes':(OUT/f'cores/{n}.so').stat().st_size} for n in cores},
 'known_unresolved_physical_cases':['METEOR','QUASAR'],'coverage':'All18 contexts on v3 twice; Confuser is a previously working manual control; ref/v3 AB/BA on Meteor and Quasar only.',
 'observations':['original archived input and expected effect properties','full frame/native PCM production and final accounting','complete bounded PCM history flushed after join','per-call main/thread worker CPU and valid pointers','direct/copy counts and retained full effect/recovery window'],
 'limits':['No isolated per-optimization A7 prices.','Conditional/Rage fixture coverage is its observed branch, not all random branches.','Observer costs included; no frequency pinning or assumed MHz.','Offline equivalence reused by exact core hash; physical panel/speaker correctness requires observation.']}
 write(OUT/'plan.json',json.dumps(plan,indent=2)+'\n')
 print('Prepared40 epochs,18 spell contexts,20 unchanged state payloads; no card writes')
if __name__=='__main__':main()
