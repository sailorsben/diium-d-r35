"""Analyze only archived UART verification return; no card access."""
from pathlib import Path
from hashlib import sha256
import json,sys,zlib
from attempt_archive import verify_saved,digest
ROOT=Path(__file__).resolve().parent.parent
BASE='retro/uart-kernel-verify1'
def analyze(archive):
 a=json.loads((archive/'archive.json').read_text());o=json.loads((archive/'outside-retro.json').read_text());assert a['fat_clean'];verify_saved(archive,a)
 entries={e['path']:e for e in a['all_retro_files']+o['files']};base=archive/BASE
 install=json.loads((ROOT/'evidence/2026-10-16/uart-kernel-verification/installation.json').read_text());q=ROOT/'build/uart-kernel-verify-private'
 for n,h in install['payload_hashes'].items():assert entries[BASE+'/'+n]['sha256']==h
 assert entries['retro/init']['sha256']==install['init_sha256']
 assert BASE+'/armed' not in entries and entries[BASE+'/consumed']['sha256']==install['marker_sha256']
 assert not any(n.endswith('/Code.bkp') or n.endswith('/armed') for n in entries)
 wrapper=(base/'wrapper.log').read_text();assert wrapper=='suite=uart-kernel-verify1 flash_writes=0 module_loads=0\nreadback_exit=0\nverification_exit=0 owned_reader_reaped=1\n'
 records=[json.loads(l) for l in (base/'results/report.jsonl').read_text().splitlines()];start=[r for r in records if r['kind']=='start'];ends=[r for r in records if r['kind']=='result'];assert len(start)==len(ends)==1;r=ends[0];n=8388608
 assert start[0]['passes']==2 and start[0]['capacity_bytes']==n and start[0]['expected_jedec']=='c84017'
 for k,v in {'errno':0,'stage':'readback-complete','operations':4111,'bytes':[n,n],'capacity_bytes':n,'block_bytes':4096,'byte_compared':True,'ids':['c84017c84017']*3,'timed_out':False,'reap_pending':False,'flash_writes':False,'global_config_writes':False}.items():assert r[k]==v,k
 assert r['status_before']&1==r['status_after']&1==0
 data=(base/'results/captures.bin').read_bytes();assert len(data)==2*n and data[:n]==data[n:]
 assert [f'{zlib.crc32(data[x:x+n]):08x}' for x in [0,n]]==r['crc32']
 expected=(ROOT/'device-evidence/uart-kernel-firmware1/expected-after-vendor.bin').read_bytes();assert data[:n]==expected
 flash=sha256(data[:n]).hexdigest();assert flash=='ef69753afb56c84e4daaf78aa3fad5551d26b7438e49f4f1dbc7312b11e07321'
 kernel=sha256(zlib.decompress(data[0xc0078+0x48b8:0x301d10],31)).hexdigest();assert kernel=='b1fe94004b84cbf8ee0ec3367466598bc9c8dd1cbfa9f55ae9373bbc6eefa459'
 windows=[];ids=set()
 for label in ['uart-before','uart-after']:
  d=base/'logs'/label;t={k:int(v) for k,v in (l.split('=',1) for l in (d/'timing.txt').read_text().splitlines())};assert t['failed']==t['flash_writes']==t['UART_configuration_writes']==0 and t['relative_wait_ns']==5000000000
  counts=[];serial=[]
  for tag in ['before','after']:
   ids.add((d/(tag+'-boot-id.txt')).read_text().strip());presence=dict(l.split('=',1) for l in (d/(tag+'-presence.txt')).read_text().splitlines());assert set(presence.values())=={'0'}
   assert 'd35_uart_tx' not in (d/(tag+'-modules.txt')).read_text()
   lines=[l.split() for l in (d/(tag+'-interrupts.txt')).read_text().splitlines() if l.strip().startswith('19:')];assert len(lines)==1;counts.append(int(lines[0][1]));serial.append((d/(tag+'-serial.txt')).read_text())
  delta=counts[1]-counts[0];assert delta>=0
  short=(t['end_snapshot_start_ns']-t['begin_snapshot_end_ns'])/1e9;long=(t['end_snapshot_end_ns']-t['begin_snapshot_start_ns'])/1e9;assert long>=short>=5
  rates=[delta/long,delta/short];assert rates[1]<500
  windows.append({'window':label,'IRQ19_counts':counts,'IRQ19_delta':delta,'IRQ19_per_second_bracket':rates,'kernel_times_ns':t,'serial_snapshots':serial})
 assert len(ids)==1 and next(iter(ids))
 before=ROOT/'device-evidence/uart-kernel-return-20261017T015801633471Z';prior=json.loads((before/'archive.json').read_text())['all_retro_files']+json.loads((before/'outside-retro.json').read_text())['files']
 changes={e['path']:entries.get(e['path'],{}).get('sha256') for e in prior if entries.get(e['path'],{}).get('sha256')!=e['sha256']};assert set(changes)=={'retro/init','retro/update/Code.bkp','retro/swapfile'}
 return {'archive':archive.name,'complete':True,'all_files_hashed':len(entries),'new_sparse_content_bytes':a['new_content_bytes']+o['new_content_bytes'],'FAT_clean':True,'saves_and_prior_evidence_unchanged':True,'expected_card_changes':changes,'wrapper_success':True,'two_pass_flash_exact':True,'flash_sha256':flash,'kernel_sha256':kernel,'runtime_UART_module_absent':True,'idle_IRQ_flood_acceptance_passed':True,'windows':windows,'readback_elapsed_seconds':r['elapsed_ns']/1e9,'boot_id':next(iter(ids)),'shutdown_cause':'UNRESOLVED; user reports possible low battery. Probe completes before stock continuation; no retained shutdown telemetry.','limits':['No electrical UART byte/throughput or CPU savings claim.','Successful verification does not prove later stock launcher stability or power state.'],'no_full_backup':True}
if __name__=='__main__':
 p=Path(sys.argv[1]).resolve();assert p.is_relative_to(ROOT/'device-evidence');v=analyze(p);(p/'analysis.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
