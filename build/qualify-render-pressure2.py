"""Functional ARM/controller/firmware-shell qualification; no A7 speed claims."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,os,re,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/render-pressure2-private'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def kv(p):return dict(l.split('=',1) for l in p.read_text().splitlines() if '=' in l)
def run(args,timeout=60):
 r=subprocess.run((['wsl','--exec'] if os.name=='nt' else [])+args,cwd=ROOT,capture_output=True,text=True,timeout=timeout);return r
def okay(args):
 r=run(args);assert r.returncode==0,(args,r.returncode,r.stdout,r.stderr);return r.stdout
def main():
 prep=json.loads((OUT/'preparation.json').read_text());assert prep['phases']==70
 seam=json.loads((OUT/'controller-qualification.json').read_text());assert seam['passed'] and seam['reintroduced_double_finish_rejected'] and seam['bursts_executed']==6
 for n,h in seam['sources'].items():assert digest(ROOT/n)==h,n
 for n,h in prep['copied_support'].items():assert digest(OUT/'runner'/n)==h,n
 qemu=['qemu-arm','-cpu','cortex-a7','-L','build/sysroot','-E','LD_LIBRARY_PATH=build/sysroot/lib']
 oracle=okay(qemu+['build/render-pressure2-private/render-pressure','--self-test']);assert '60 full-frame cases' in oracle
 case=OUT/'mock';assert not case.exists();case.mkdir()
 text=okay(qemu+['build/render-pressure2-private/render-pressure','--supervise-mock','--output','build/render-pressure2-private/mock'])
 summary=kv(case/'summary.txt');assert summary['mock']=='1' and summary['phases']=='70' and summary['issues']==summary['stopped']==summary['expired']=='0',summary
 for i in range(59,66):
  cell=kv(case/f'phase-{i:03d}/begin.txt');assert cell['scene']=='static' and cell['variant']=='2' and cell['direct']=='1' and cell['serial']=='0' and cell['audio']=='1'
  assert cell['load_ms']==str([4,8,12,16,24,48,80][i-59]) and cell['load_every']==('1' if i<63 else '30')
 assert kv(case/'supervisor.txt')['reaped']=='1' and kv(case/'supervisor.txt')['forced']=='0'
 spec=importlib.util.spec_from_file_location('pressure_report',ROOT/'build/report-render-pressure2.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 report=m.analyze(case,True);assert len(report['phases'])==70 and not report['physical'] and all(p['metrics'] is None and not p['physical_cell_accepted'] for p in report['phases'])
 try:m.analyze(case)
 except AssertionError as e:assert 'Mock telemetry' in str(e)
 else:raise AssertionError('Mock was accepted as physical')
 # Exact shell syntax and execution with a private, owned fake child.
 shell=['qemu-arm','-0','busybox','-L','build/sysroot','build/uart-fix-private/firmware-busybox','sh']
 okay(shell+['-n','build/render-pressure2-private/launch.sh'])
 fixture=OUT/'wrapper';fixture.mkdir();(fixture/'mvp').mkdir();(fixture/'proc').mkdir()
 (fixture/'proc/d35_uart_tx').write_text('version=4 result=0 irq=19 attached=1 calls=0 fault=0 bypass=0 cap=0\n',encoding='utf-8',newline='\n')
 (fixture/'platform-lab').write_bytes(b'unused')
 shim=fixture/'render-pressure';shim.write_text('#!/bin/sh\nexit "${PRESSURE_FIXTURE_EXIT:-0}"\n',encoding='utf-8',newline='\n');okay(['chmod','+x','build/render-pressure2-private/wrapper/render-pressure'])
 command=['env','D35_LAB_BASE=build/render-pressure2-private/wrapper','D35_MVP_BASE=build/render-pressure2-private/wrapper/mvp','D35_LAB_PROC_ROOT=build/render-pressure2-private/wrapper/proc','D35_LAB_SPLASH_STOP=build/render-pressure2-private/wrapper/splash-stop',*shell,'build/render-pressure2-private/launch.sh']
 for label in ['normal','replay']:
  if label=='normal':
   for p in [fixture/'armed',fixture/'mvp/armed']:p.write_bytes(b'fixture marker\n')
  okay(command);assert not (fixture/'armed').exists() and not (fixture/'mvp/armed').exists()
 assert len(list((fixture/'results').glob('run-*')))==1
 for p in [fixture/'armed',fixture/'mvp/armed']:p.write_bytes(b'fixture marker\n')
 blocked=run(['timeout','2',*command[:1],'PRESSURE_FIXTURE_EXIT=72',*command[1:]])
 assert blocked.returncode==124 and not (fixture/'armed').exists() and not (fixture/'mvp/armed').exists(),blocked
 assert any('deadline reached; reboot required' in p.read_text() for p in (fixture/'results').glob('*/wrapper.log'))
 sources=['build/render-pressure2.c','build/render-pressure-kernels.h','build/plus-a7-render.h','build/prepare-render-pressure2.py','build/build-render-pressure2.sh','build/report-render-pressure2.py','build/qualify-render-pressure2.py','build/audit-device-render-path.py','build/launch-platform-lab2.sh','build/install-render-pressure2.py','build/check-render-pressure2-controller.py','build/check-render-pressure2-controller.c','build/check-render-pressure2-faults.py']
 abi=(OUT/'abi.txt').read_text();versions=set(re.findall(r'Name: (\S+)',abi))
 assert all(tuple(map(int,v.removeprefix('GLIBC_').split('.'))) <= (2,30) for v in versions if v.startswith('GLIBC_')),versions
 dependencies=(OUT/'render-dependencies.txt').read_text().replace('\\\n',' ').split(':',1)[1].split()
 assert 'build/snes9x2005/source/gfx.h' in dependencies
 assert 'vtbl.8' in (OUT/'disassembly.txt').read_text()
 result={'version':'render-pressure2','passed':True,'oracle':oracle.strip(),'controller_mock_phases':70,'supervisor_child_reaped':True,
 'firmware_shell_checks':['syntax','normal consumption and completion','consumed reboot skips','forced72 withholds stock'],
 'mock_rejected_as_physical':True,'mock_timings_published':False,'native_board_audio_support_reused_by_hash':True,
 'controller_qualification_sha256':digest(OUT/'controller-qualification.json'),'load_sweeps_on_light_workload':True,'sources':{n:digest(ROOT/n) for n in sources},'local_compile_dependencies':{n:digest(ROOT/n) for n in dependencies},'ABI_versions':sorted(versions),'private_support':prep['copied_support'],
 'payloads':{n:digest(OUT/n) for n in ['render-pressure','launch.sh','dispatch.sh']},'preparation_sha256':digest(OUT/'preparation.json'),
 'card_access':False,'physical_result':'PENDING','installed':False,'armed':False,'production_gate':False,
 'limits':['Null backend does not exercise new controller against real DMA/display/PCM.','Frozen support seams have prior physical evidence, not qualification of this new combined test.','Fault injection and a sustained physical return are still required before treating every stress threshold as a device ceiling.']}
 (OUT/'qualification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
