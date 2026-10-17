"""Rebuild only replay observability/supervision; freeze all matched game inputs."""
from pathlib import Path
import json, os, shutil
from attempt_archive import digest

ROOT=Path(__file__).resolve().parent.parent
OLD=ROOT/'build/fivegame-kernel-private-v1'
BASE=ROOT/'build/fivegame-physical-private-v1'
OUT=ROOT/'build/fivegame-kernel-private-v2'
TARGET='retro/snes-fivegame-kernel2'

def write(path,text):
    path.write_text(text,encoding='utf-8',newline='\n')

def main():
    assert not OUT.exists()
    q=json.loads((OLD/'qualification.json').read_text())
    original=json.loads((BASE/'verification.json').read_text())
    assert q['passed'] and len(q['previous_actual_epochs'])==20
    assert digest(BASE/'verification.json')==q['previous_qualification_sha256']
    for n,h in q['payload_hashes'].items():assert digest(OLD/n)==h,n
    for n,h in original['source_hashes'].items():assert digest(ROOT/n)==h,n
    OUT.mkdir()
    for name in q['payload_hashes']:
        p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
        # Static ROM/core/fixture/plan bytes have a single host content copy.
        if name in ('fivegame-suite','launch.sh','dispatch.sh','ROM-PATH.txt'):continue
        os.link(OLD/name,p)
    shutil.copytree(BASE/'runner',OUT/'runner',ignore=shutil.ignore_patterns('*.o'))
    for name in ['identity.h','presentation-burst.h','plus-a7-profile.h']:
        shutil.copyfile(BASE/name,OUT/name)
    shutil.copyfile(ROOT/'build/fivegame-warmup-progress.h',OUT/'runner/fivegame-warmup.h')
    shutil.copyfile(ROOT/'build/fivegame-replay-progress.h',OUT/'fivegame-replay-progress.h')
    shutil.copyfile(ROOT/'build/fivegame-replay-progress.h',OUT/'runner/fivegame-replay-progress.h')
    s=(BASE/'main.c').read_text()
    s=s.replace('#include <errno.h>','#include <errno.h>\n#include <sys/mman.h>\n#include "fivegame-replay-progress.h"')
    s=s.replace(' pid_t child=fork();',''' d35_replay_shared=mmap(NULL,sizeof(*d35_replay_shared),PROT_READ|PROT_WRITE,MAP_SHARED|MAP_ANONYMOUS,-1,0);
 if(d35_replay_shared==MAP_FAILED){d35_replay_shared=NULL;return 72;}
 uint64_t last_progress=now();unsigned last_calls=0,seen=0,warm_stall=0;
 pid_t child=fork();''',1)
    old='  if(stopped||!now()||now()>=deadline){kill(child,SIGTERM);forced=1;break;}'
    assert old in s
    s=s.replace(old,'''  uint64_t current=now();
  if(d35_replay_shared->active){
   __sync_synchronize();unsigned calls=d35_replay_shared->calls;
   if(!seen||calls!=last_calls){last_progress=current;last_calls=calls;seen=1;}
   else if(current-last_progress>=D35_COLD_STALL_NS)warm_stall=1;
  }else{seen=0;last_progress=current;}
  if(stopped||!current||current>=deadline||warm_stall){kill(child,SIGTERM);forced=1;break;}''',1)
    needle='durable(f);\n if(!reaped||forced||!WIFEXITED(status))return 72;'
    assert needle in s
    s=s.replace(needle,'''fprintf(f,"cold_replay_active=%u\\ncold_replay_calls=%u\\ncold_replay_epoch=%u\\ncold_replay_stall=%u\\nstop_reason=%s\\n",d35_replay_shared->active,d35_replay_shared->calls,d35_replay_shared->epoch,warm_stall,warm_stall?"cold_replay_no_progress":forced?(stopped?"supervisor_signal":"suite_deadline"):"child_exit");
 durable(f);munmap(d35_replay_shared,sizeof(*d35_replay_shared));d35_replay_shared=NULL;
 if(!reaped||forced||!WIFEXITED(status))return 72;''',1)
    needle='  int rc=runner_run(rom,core,dir);'
    assert needle in s
    s=s.replace(needle,'  if(r->fixture==3&&d35_replay_shared)d35_replay_shared->epoch=seq;\n'+needle,1)
    write(OUT/'main.c',s)
    wrapper=(OLD/'launch.sh').read_text().replace('/usr/retro/snes-fivegame-kernel1','/usr/'+TARGET)
    write(OUT/'launch.sh',wrapper)
    write(OUT/'dispatch.sh','#!/bin/sh\nexec /bin/sh /usr/'+TARGET+'/launch.sh\n')
    write(OUT/'ROM-PATH.txt','/usr/'+TARGET+'/cases/000/game.sfc\n')
    frozen={n:digest(OUT/n) for n in q['payload_hashes'] if n not in ('fivegame-suite','launch.sh','dispatch.sh','ROM-PATH.txt')}
    for n,h in frozen.items():assert h==q['payload_hashes'][n],n
    write(OUT/'replay-preparation.json',json.dumps({'target':TARGET,'prior_qualification_sha256':digest(OLD/'qualification.json'),'frozen_payloads':frozen,'cold_calls_per_Star_Fox_epoch':8656,'UI_and_durable_progress_interval_ns':2000000000,'cold_no_progress_deadline_ns':60000000000,'suite_deadline_minutes':35,'measured_policy_game_core_fixtures_inputs_oracles_unchanged':True,'no_card_access':True},indent=2)+'\n')
    print('Prepared isolated replay-observable controller; matched core/plan/cases exact, no card access')

if __name__=='__main__':main()
