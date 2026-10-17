"""Analyze the exact sparse returned kernel-UART five-game profile."""
from pathlib import Path
import importlib.util,json,sys
from attempt_archive import verify_saved,digest
ROOT=Path(__file__).resolve().parent.parent
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 installation=json.loads((ROOT/'evidence/2026-10-16/fivegame-kernel/installation.json').read_text());a=json.loads((archive/'archive.json').read_text());verify_saved(archive,a);hashes={e['path']:e['sha256'] for e in a['all_retro_files']};target=installation['target']
 assert hashes[target+'/last-launch']==hashes['retro/snes-mvp/last-launch-lab']==installation['marker_sha256']
 assert not any(n.endswith('/armed') for n in hashes)
 for n,h in installation['payload_hashes'].items():assert hashes[target+'/'+n]==h,n
 assert hashes['retro/init']==installation['normal_init_sha256']
 package=ROOT/'build/fivegame-kernel-private-v1';assert digest(package/'plan.json')==installation['payload_hashes']['plan.json'];plan=json.loads((package/'plan.json').read_text())
 runs=list((archive/target/'results').glob('run-*'));assert len(runs)==1
 s=importlib.util.spec_from_file_location('report',ROOT/'build/report-fivegame.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);v=m.analyze(runs[0],plan)
 v.update({'profile':'fivegame-kernel1','kernel_UART_verified_before_install':True,'limits_note':'Analyze passive UART snapshots separately; old module endpoint is intentionally absent.'});out=archive/'fivegame-kernel-analysis.json';assert not out.exists();out.write_text(json.dumps(v,indent=2)+'\n');print(out)
if __name__=='__main__':main(Path(sys.argv[1]))
