"""Bind physical results to the replay-aware installation; archive-only analysis."""
from pathlib import Path
import importlib.util,json,sys
from attempt_archive import digest,verify_saved

ROOT=Path(__file__).resolve().parent.parent

def kv(p):return dict(l.split('=',1) for l in p.read_text().splitlines() if '=' in l) if p.exists() else {}

def main(archive):
    archive=archive.resolve();assert archive.is_relative_to((ROOT/'device-evidence').resolve())
    i=json.loads((ROOT/'evidence/2026-10-17/fivegame-replay/installation.json').read_text())
    a=json.loads((archive/'archive.json').read_text());o=json.loads((archive/'outside-retro.json').read_text())
    assert a['fat_clean'] and a['card_writes']==o['card_writes']==0;verify_saved(archive,a)
    entries={e['path']:e['sha256'] for e in a['all_retro_files']+o['files']};target=i['target']
    assert not any(n.endswith('/armed') or n.endswith('/Code.bkp') for n in entries)
    assert entries[target+'/last-launch']==entries['retro/snes-mvp/last-launch-lab']==i['marker_sha256']
    for n,h in i['payload_hashes'].items():assert entries[target+'/'+n]==h,n
    assert entries['retro/init']==i['normal_init_sha256']
    package=ROOT/'build/fivegame-kernel-private-v2';assert digest(package/'plan.json')==i['payload_hashes']['plan.json']
    plan=json.loads((package/'plan.json').read_text());runs=list((archive/target/'results').glob('run-*'));assert len(runs)==1
    spec=importlib.util.spec_from_file_location('report',ROOT/'build/report-fivegame.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    v=m.analyze(runs[0],plan);v['replay_supervisor']=kv(runs[0]/'supervisor.txt')
    for row in v['epochs']:
        if row['fixture']==3:
            warm=kv(runs[0]/f"run-{row['run']:03d}"/'warmup.txt');row['replay_progress']=warm
            if row['status']=='CLEAN_BOUNDED_WINDOW' and warm.get('status')!='completed':row['status']='INVALID_OR_INCOMPLETE'
    v.update({'profile':'fivegame-kernel2','installation_sha256':digest(ROOT/'evidence/2026-10-17/fivegame-replay/installation.json'),'no_full_backup':True,'physical_run_directory':runs[0].name})
    out=archive/'fivegame-replay-analysis.json';assert not out.exists();out.write_text(json.dumps(v,indent=2)+'\n');print(out)

if __name__=='__main__':main(Path(sys.argv[1]))
