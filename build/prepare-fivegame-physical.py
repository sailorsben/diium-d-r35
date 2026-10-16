"""Fresh five-game matched measurement package. No card access or backup."""
from pathlib import Path
from hashlib import sha256
import csv,json,shutil,struct,zlib
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/fivegame-physical-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def main():
 assert not OUT.exists();base=ROOT/'build/presentation-ffvi-private-v1';fix=ROOT/'build/multigame-fixes-private-v1';q=json.loads((ROOT/'evidence/2026-10-16/gameplay-fixes/qualification.json').read_text());assert q['passed'] and digest(fix/'core/snes9x2005_plus_libretro.so')==q['candidate_core_sha256']
 OUT.mkdir();shutil.copytree(base/'runner',OUT/'runner',ignore=shutil.ignore_patterns('*.o'));rt=OUT/'runner';shutil.copyfile(fix/'core/snes9x2005_plus_libretro.so',OUT/'plus-a7.so')
 for n in ('presentation-burst.h','plus-a7-profile.h'):shutil.copyfile(base/n,OUT/n)
 shutil.copyfile(ROOT/'build/fivegame-observer.h',rt/'ability-observer.h');shutil.copyfile(ROOT/'build/fivegame-warmup.h',rt/'fivegame-warmup.h')
 p=rt/'runner.c';s=p.read_text();s=s.replace('static uint64_t thread_cpu_ns(void);','static uint64_t thread_cpu_ns(void);\nstatic uint64_t game_period_ns;')
 s=s.replace('int runner_run(const char *rom_path', '#include "fivegame-warmup.h"\n\nint runner_run(const char *rom_path',1)
 old='    if(!load_state()) { fail("Pair snapshot identity rejected");goto done; }';assert s.count(old)==1
 s=s.replace(old,'''    if(strcmp(value,"-")) { if(!load_state()) { fail("Pair snapshot identity rejected");goto done; } }
    else if(!game_warmup(save_dir)) { fail("Cold boot warmup failed or aborted");goto done; }
    game_period_ns=(uint64_t)(1000000000.0/native_av.timing.fps+0.5);''')
 s=s.replace('    if(!data||s.failed||!s.audio_ready','    game_oracle_audio(data,frames);\n    if(!data||s.failed||!s.audio_ready',1)
 s=s.replace('    if(s.failed) return;\n    if(!data)', '    if(s.failed) return;\n    game_oracle_video(data,w,h,pitch);\n    if(!data)',1)
 s=s.replace('        p_retro_run();','        game_oracle_begin();\n        p_retro_run();\n        if(!game_oracle_check((unsigned)s.runs))fail("Game oracle mismatch at %u",(unsigned)s.runs);',1)
 s=s.replace('    if(s.loaded) p_retro_unload_game();','    game_final_state(s.save_dir);\n    if(s.loaded) p_retro_unload_game();')
 write(p,s.replace('presentation-ffvi1','fivegame1'))
 p=rt/'pair-host.h';write(p,p.read_text().replace('presentation-ffvi1','fivegame1'))
 p=rt/'combined-headroom.h';s=p.read_text().replace('16688154ull','game_period_ns').replace('13350523ull','(game_period_ns*4/5)')
 s=s.replace('period_ns=16688154\\ntarget_20_percent_ns=13350523','period_ns=%llu\\ntarget_20_percent_ns=%llu')
 s=s.replace('mock,failed,pair_count,count,(unsigned long long)observer','mock,failed,pair_count,count,(unsigned long long)game_period_ns,(unsigned long long)(game_period_ns*4/5),(unsigned long long)observer')
 write(p,s.replace('presentation-ffvi1','fivegame1'))
 fixtures=json.loads((fix/'gameplay-fixtures.json').read_text());cases=[];cb=(OUT/'plus-a7.so').read_bytes()
 for fixture in fixtures:
  i=fixture['game'];d=OUT/f'cases/{i:03d}';d.mkdir(parents=True);rom=ROOT/f'build/multigame-private-v3/game-{i}.sfc';rb=rom.read_bytes();shutil.copyfile(rom,d/'game.sfc')
  lines=(fix/fixture['inputs']).read_text().splitlines()
  if i==3:write(d/'warmup.txt','\n'.join(lines[:-1])+'\n');write(d/'input.txt',lines[-1]+'\n')
  else:
   raw=(fix/fixture['state']).read_bytes();assert digest(fix/fixture['state'])==fixture['state_sha256'];head=bytearray(40);head[:8]=b'D35MVP01';struct.pack_into('<7I',head,8,1,zlib.crc32(rb)&0xffffffff,len(rb),zlib.crc32(cb)&0xffffffff,len(cb),len(raw),zlib.crc32(raw)&0xffffffff);(d/'scene.state').write_bytes(head+raw);write(d/'input.txt','\n'.join(lines)+'\n')
  rows=list(csv.DictReader((fix/f'checked-v2-{i}/frames.csv').open()))[-1200:];(d/'expected.bin').write_bytes(b''.join(struct.pack('<III',int(r['pixels_crc'],16),int(r['pcm_crc'],16),int(r['samples'])) for r in rows))
  cases.append({'game':i,'name':fixture['scene'],'warmup_calls':8656 if i==3 else 0,'fps':50.319739654 if i==0 else 59.922743404,'ROM_sha256':digest(rom),'source_fixture':fixture,'input_sha256':digest(d/'input.txt'),'expected_sha256':digest(d/'expected.bin')})
 runs=[]
 for repeat,policy in enumerate((0,1,1,0)):
  for case in cases if repeat%2==0 else list(reversed(cases)):runs.append({'run':len(runs),'fixture':case['game'],'name':case['name'],'policy':policy,'repeat':repeat,'load_ms':0})
 header='struct ffvi_run {unsigned fixture,policy,repeat,load_ms;};\nstatic const struct ffvi_run ffvi_runs[]={'+','.join('{%d,%d,%d,0}'%(r['fixture'],r['policy'],r['repeat']) for r in runs)+'};\nstatic const char *spell_names[]={'+','.join(json.dumps(c['name']) for c in cases)+'};\n';write(OUT/'identity.h',header)
 s=(ROOT/'build/presentation-ffvi-main.c').read_text();s=s.replace('char dir[1200],state','char rom[1200],warm[1200],dir[1200],state')
 s=s.replace('  if(mkdir(dir,0700))','  snprintf(rom,sizeof(rom),"%s/cases/%03u/game.sfc",argv[3],r->fixture);\n  snprintf(warm,sizeof(warm),"%s/cases/%03u/warmup.txt",argv[3],r->fixture);\n  if(r->fixture==3){strcpy(state,"-");setenv("D35_GAME_WARMUP",warm,1);}else unsetenv("D35_GAME_WARMUP");\n  if(mkdir(dir,0700))')
 s=s.replace('runner_run(argv[4],core,dir)','runner_run(rom,core,dir)').replace('presentation-ffvi1','fivegame1');write(OUT/'main.c',s)
 s=(base/'launch.sh').read_text().replace('snes-presentation-ffvi1','snes-fivegame1').replace('presentation-ffvi','fivegame').replace('ffvi-suite','fivegame-suite');write(OUT/'launch.sh',s);write(OUT/'dispatch.sh','#!/bin/sh\nexec /bin/sh /usr/retro/snes-fivegame1/launch.sh\n');write(OUT/'ROM-PATH.txt','/usr/retro/snes-fivegame1/cases/000/game.sfc\n')
 write(OUT/'plan.json',json.dumps({'version':'fivegame1','runs':runs,'cases':cases,'calls':1200,'core_sha256':digest(OUT/'plus-a7.so'),'deadline_minutes':35,'measurement_only':True,'production_gate':False,'physical_result':'PENDING'},indent=2)+'\n')
 write(OUT/'frozen.json',json.dumps({p.relative_to(ROOT).as_posix():digest(p) for p in [*list((base/'runner').glob('*.[ch]')),fix/'core/snes9x2005_plus_libretro.so',ROOT/'evidence/2026-10-16/gameplay-fixes/qualification.json']},indent=2)+'\n')
 print('Prepared20 ABBA epochs,5 original backup games, native timing; no card access')
if __name__=='__main__':main()
