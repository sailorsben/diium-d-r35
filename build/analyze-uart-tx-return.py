"""Strict archived physical UART TX1 A/B/restoration result; no card writes."""
from pathlib import Path
from hashlib import sha256
import json
import sys
ROOT=Path(__file__).resolve().parent.parent
COUNTERS=['calls','added','writes','full','empty_stop','stopped','urgent','fallback','fault','bypass','rx','tx','frame','parity','overrun','brk']

def digest(path): return sha256(path.read_bytes()).hexdigest()
def fields(line):
 pairs=[x.split('=',1) for x in line.split() if '=' in x];r=dict(pairs);assert len(r)==len(pairs);return r

def status(line,phase=None):
 r=fields(line)
 if phase is not None:assert r.pop('phase')==phase;assert int(r.pop('owner_ns'))>0
 expected={'version','result','irq','attached','ctrl','flags','fifo','head','tail','cap',*COUNTERS}
 assert set(r)==expected
 d={k:int(v,16 if k in ('ctrl','flags') else 10) for k,v in r.items()}
 assert all(0<=v<=0xffffffff for v in d.values())
 assert d['version']==4 and d['result']==0 and d['irq']==19 and d['fifo']==8
 assert d['attached'] in (0,1) and d['cap']==200000 and d['calls']<=d['cap']
 assert d['head']<4096 and d['tail']<4096 and d['flags']<=255
 assert d['calls']==d['added']+d['fallback']+d['fault']
 assert d['added']==d['writes']+d['full']+d['empty_stop']+d['stopped']
 assert d['urgent']<=d['writes']
 return d

def irq(line,phase):
 r=fields(line);assert set(r)=={'phase','begin_ns','end_ns','valid','count'} and r['phase']==phase and r['valid']=='1'
 d={k:int(r[k]) for k in ('begin_ns','end_ns','count')};assert 0<=d['begin_ns']<=d['end_ns'] and d['count']>=0;return d

def cpu(line,phase):
 meta,sep,values=line.rpartition(' cpu ');assert sep
 r=fields(meta);assert set(r)=={'phase','begin_ns','end_ns'} and r['phase']==phase
 values=[int(v) for v in values.split()];assert len(values)==10 and all(v>=0 for v in values)
 assert 0<=int(r['begin_ns'])<=int(r['end_ns'])
 return {'begin_ns':int(r['begin_ns']),'end_ns':int(r['end_ns']),'ticks':values}

def window(a,b):
 assert a['end_ns']<b['begin_ns'] and a['count']<b['count']
 n=b['count']-a['count'];seconds=((b['begin_ns']+b['end_ns'])-(a['begin_ns']+a['end_ns']))/2e9
 return {'interrupts':n,'midpoint_seconds':seconds,'per_second':n/seconds,
 'endpoint_rate_bounds':[n*1e9/(b['end_ns']-a['begin_ns']),n*1e9/(b['begin_ns']-a['end_ns'])]}

def analyze_log(lines):
 assert lines[0]=='version=uart-tx1 clock=kernel_syscall module_flags=0 unload_flags=O_NONBLOCK'
 assert lines[1].startswith('phase=before_load kernel=4.19.128 pid=')
 before=window(irq(lines[2],'before_baseline'),irq(lines[3],'after_baseline'))
 assert lines[4]=='load_result=0 load_errno=0';at=5;phases=[];previous=None
 names=['original0','corrected0','restored0','corrected1','restored1']
 for i,name in enumerate(names):
  attached=i%2
  if i:
   expect='control=on version=4 start_result=0 attached=1' if attached else 'control=off version=4 stop_result=0 restored=1 attached=0'
   assert lines[at]==expect;at+=1
  assert lines[at]==f'phase={name} event=begin';at+=1
  ia=irq(lines[at],name);ca=cpu(lines[at+1],name);sa=status(lines[at+2],name);at+=3
  ib=irq(lines[at],name);cb=cpu(lines[at+1],name);sb=status(lines[at+2],name);at+=3
  assert lines[at]==f'phase={name} event=end';at+=1
  assert sa['attached']==sb['attached']==attached
  if previous:assert all(sa[k]>=previous[k] for k in COUNTERS)
  assert all(sb[k]>=sa[k] for k in COUNTERS);previous=sb
  w=window(ia,ib);assert 4.5<w['midpoint_seconds']<10
  delta={k:sb[k]-sa[k] for k in COUNTERS}
  assert delta['calls']==(w['interrupts'] if attached else 0)
  assert all(sa[k]==sb[k]==0 for k in ('fault','bypass'))
  ticks=[b-a for a,b in zip(ca['ticks'],cb['ticks'])];assert all(v>=0 for v in ticks)
  total=sum(ticks[:8]);assert total>0
  phases.append({'name':name,'attached':bool(attached),'irq':w,'begin':sa,'end':sb,'delta':delta,
   'queue_empty_at_both_boundaries':sa['head']==sa['tail'] and sb['head']==sb['tail'],
   'reported_tx_bytes_per_second':delta['tx']/w['midpoint_seconds'],
   'interrupts_per_reported_tx_byte':w['interrupts']/delta['tx'] if delta['tx'] else None,
   'CPU_accounted_ticks':ticks,'CPU_idle_fraction_of_accounted_ticks':ticks[3]/total})
 assert lines[at]=='control=off version=4 stop_result=0 restored=1 attached=0';at+=1
 assert lines[at]=='phase=frozen';at+=1;frozen=status(lines[at]);at+=1
 assert frozen['attached']==0 and all(frozen[k]==previous[k] for k in COUNTERS)
 assert lines[at]=='unload_result=0 unload_errno=0';at+=1
 after=window(irq(lines[at],'before_final_baseline'),irq(lines[at+1],'after_final_baseline'));at+=2
 assert lines[at:]==['phase=complete result=0 cancelled=0 module_remains=0']
 corrected=[p for p in phases if p['attached']];control=[p for p in phases if not p['attached']]
 comparisons=[]
 for idx in (1,3):
  left,right=phases[idx-1],phases[idx+1];mid=phases[idx]
  ctr=(left['irq']['interrupts']+right['irq']['interrupts'])/(left['irq']['midpoint_seconds']+right['irq']['midpoint_seconds'])
  restoration_ratio=right['irq']['per_second']/left['irq']['per_second']
  tx_control=(left['delta']['tx']+right['delta']['tx'])/(left['irq']['midpoint_seconds']+right['irq']['midpoint_seconds'])
  tx_ratio=mid['reported_tx_bytes_per_second']/tx_control
  comparisons.append({'corrected_phase':mid['name'],'bracketing_control_rate':ctr,
   'corrected_rate':mid['irq']['per_second'],'reduction_percent':100*(1-mid['irq']['per_second']/ctr),
   'restored_vs_preceding_control_ratio':restoration_ratio,'TX_rate_vs_bracketing_controls_ratio':tx_ratio,
   'flood_returns_after_restore':right['irq']['per_second']>mid['irq']['per_second']*10 and 0.75<=restoration_ratio<=1.25})
 cr=sum(p['irq']['interrupts'] for p in control)/sum(p['irq']['midpoint_seconds'] for p in control)
 tr=sum(p['irq']['interrupts'] for p in corrected)/sum(p['irq']['midpoint_seconds'] for p in corrected)
 progress=all(p['delta']['tx']>0 and p['queue_empty_at_both_boundaries'] for p in phases) and all(0.8<=c['TX_rate_vs_bracketing_controls_ratio']<=1.25 for c in comparisons)
 errors=all(not p['delta'][k] for p in phases for k in ['rx','frame','parity','overrun','brk'])
 passed=progress and errors and all(c['reduction_percent']>90 and c['flood_returns_after_restore'] for c in comparisons)
 return {'phases':phases,'comparisons':comparisons,'bookends':{'before':before,'after':after},'frozen':frozen,
 'weighted_control_irq_per_second':cr,'weighted_corrected_irq_per_second':tr,'weighted_reduction_percent':100*(1-tr/cr),
 'queue_and_reported_TX_progress_pass':progress,'RX_and_error_counters_unchanged':errors,
 'restored_flood_reproduced_twice':all(c['flood_returns_after_restore'] for c in comparisons),
 'causal_idle_flood_suppression_pass':passed,'A7_saving_measured':False,'CPU_irq_duration_measured':False,
 'physical_full_FIFO_encountered':bool(frozen['full']),'wire_contents_verified':False,'production_gate':False}

def main(archive):
    archive = archive.resolve()
    assert archive.is_relative_to(ROOT / 'device-evidence')
    metadata = json.loads((archive / 'archive.json').read_text())
    assert metadata['card'] == 'I:' and metadata['fat_clean'] and metadata['card_writes'] == 0
    health = (archive / 'chkdsk-before.txt').read_text()
    assert '11EB-1465' in health and 'Windows has scanned the file system and found no problems.' in health
    entries = {e['path']: e for e in metadata['all_retro_files']}
    assert len(entries) == len(metadata['all_retro_files'])
    for name, entry in entries.items():
        assert digest(archive / name) == entry['sha256'], name
    assert not list((archive / 'retro').rglob('armed'))
    install_path = ROOT / 'evidence/2026-10-15/uart-tx/installation.json'
    install = json.loads(install_path.read_text())
    base = archive / 'retro/uart-tx1'
    for name, expected in install['payload_hashes'].items():
        assert digest(base / name) == expected, name
    assert digest(archive / 'retro/snes-mvp/launch.sh') == install['dispatch_sha256']
    assert (base / 'last-launch').read_bytes() == b'UART TX1 reversible pending correction FIFO8 one-byte limit\n'
    assert (base / 'startup.log').read_text() == 'UART TX1 original/corrected/restored TX test; marker consumed\nowner_exit=0; returning to stock startup\n'
    assert (base / 'owner.err').read_bytes() == b''
    old_path = ROOT / 'device-evidence' / install['archive'] / 'archive.json'
    protected = [e for e in json.loads(old_path.read_text())['all_retro_files'] if e['path'] != 'retro/snes-mvp/launch.sh']
    assert len(protected) == install['protected_files']
    changed = []
    for e in protected:
        assert e['path'] in entries
        if entries[e['path']]['sha256'] != e['sha256']:
            changed.append(e['path'])
    assert set(changed) <= {'retro/swapfile'}, changed
    live_path = archive / 'live-protected-verification.json'
    live = json.loads(live_path.read_text())
    assert live['read_only'] and live['probe_payload_and_logs_match_archive']
    assert set(live['checks']) == {'retro/main', 'retro/vrtemu', 'retro/driver.so', 'retro/showlogo',
        'retro/libs/emu_sfc.so', 'retro/libs/emu_sfc_plus.so', 'retro/init', 'FFVI_ROM'}
    assert all(v is True for v in live['checks'].values())
    lines=(base/'observer.txt').read_text().splitlines();result=analyze_log(lines)
    report={'version':'uart-tx1-physical-return','physical_archive':archive.name,'mock':False,
      'installed_source_commit':install['source_commit'],'archive_files_verified':len(entries),
      'archive_bytes':sum(e['bytes'] for e in entries.values()),'fat_clean':True,'card_writes':0,
      'payloads_verified':len(install['payload_hashes']),'one_shot_consumed':True,
      'protected_prior_files':len(protected),'protected_unchanged':len(protected)-len(changed),'protected_changed':changed,
      'stock_boot_ROM_progress_verified':True,'handler_restored':True,'module_loaded_unloaded':True,'owner_exit':0,
      **result,'limits':['Idle startup workload only; no SNES or sustained mixed-RX stress test.',
       'TX counts and queue progress do not verify wire contents; original literal-zero PutChar remains unchanged.',
       'No full-FIFO refusal occurred physically; full-flag/capacity validation remains conditional on the shared-IP contract.',
       'CPU jiffies are coarse and IRQ-time accounting is disabled; interrupt-count reduction is not measured A7 saving.',
       'Boundary reads are sequential and clock brackets omit procfs enumeration uncertainty.'],
      'input_sha256':{p.relative_to(archive).as_posix():digest(p) for p in [archive/'archive.json',archive/'chkdsk-before.txt',live_path,base/'observer.txt',base/'startup.log',base/'owner.err',base/'last-launch']},
      'installation_receipt_sha256':digest(install_path)}
    (archive/'uart-tx-return.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main(Path(sys.argv[1]))
