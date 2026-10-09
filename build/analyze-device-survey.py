"""Summarize private survey evidence, preserving failures and partial captures."""
from pathlib import Path
from hashlib import sha256
import argparse, collections, json, zlib

def capture_bytes(results, record):
    """Read a v1 file or a bounded v2 bundle range, checking returned integrity."""
    name=record['output']
    if not isinstance(name,str) or Path(name).name!=name or not (name=='captures.bin' or name.startswith('capture-')):
        raise ValueError('Invalid capture filename')
    p=Path(results)/name
    size=record['bytes']
    if not isinstance(size,int) or not 0<=size<=8*1024*1024: raise ValueError('Invalid capture size')
    if name=='captures.bin':
        offset=record.get('offset')
        if not isinstance(offset,int) or not 0<=offset<=48*1024*1024 or offset+size>48*1024*1024:
            raise ValueError('Invalid bundle range')
        with p.open('rb') as f: f.seek(offset);data=f.read(size)
        if len(data)!=size: raise ValueError('Bundle range is truncated')
        expected=record.get('crc32')
        if expected!=f'{zlib.crc32(data):08x}': raise ValueError('Bundle CRC32 is absent or differs')
    else:
        data=p.read_bytes()
        if len(data)!=size: raise ValueError('Capture size differs from report')
    return data
def analyze(base):
    base=Path(base);report=base/'results/report.jsonl'
    if not report.exists(): return {'complete':False,'reason':'No report; inspect startup.log and marker identity'}
    records=[];parse_errors=[]
    for number,line in enumerate(report.read_text(encoding='utf-8').splitlines(),1):
        try: records.append(json.loads(line))
        except json.JSONDecodeError as e: parse_errors.append({'line':number,'error':str(e)})
    captured=[];groups=collections.defaultdict(collections.Counter);failures=[];bundle_end=0
    for r in records:
        if r.get('kind')!='capture':continue
        name=r.get('output');g=groups[r['group']]
        if r['errno'] in [2,20]:g['missing']+=1
        elif r['errno']:g['failed']+=1;failures.append(r)
        else:g['read']+=1
        if r['truncated']:g['truncated']+=1
        if name:
            if name=='captures.bin':
                if r.get('offset')!=bundle_end: failures.append({'source':r['source'],'capture_error':'Bundle range is not contiguous'})
                bundle_end+=r['bytes']
            try: data=capture_bytes(base/'results',r)
            except (OSError,ValueError) as e:
                failures.append({'source':r['source'],'capture':name,'capture_error':str(e)});continue
            captured.append({'source':r['source'],'output':name,'bytes':len(data),'sha256':sha256(data).hexdigest(),
                'errno':r['errno'],'truncated':r['truncated'],
                **({k:r[k] for k in ['offset','crc32']} if name=='captures.bin' else {})})
    end=next((r for r in reversed(records) if r.get('kind')=='complete'),None)
    version=next((r.get('version') for r in records if r.get('kind')=='start'),1)
    if version==2:
        p=base/'results/captures.bin'
        if not p.exists() or p.stat().st_size!=bundle_end or end and end.get('bytes')!=bundle_end:
            failures.append({'capture_error':'Bundle length or completion byte count differs'})
    consumed=(base/'consumed').exists() and not (base/'armed').exists()
    startup=(base/'startup.log').read_text(encoding='utf-8',errors='replace') if (base/'startup.log').exists() else ''
    exits=[line.split('=',1)[1] for line in startup.splitlines() if line.startswith('survey_exit=')]
    wrapper_exit=int(exits[-1]) if exits and exits[-1].isdigit() else None
    identity={}
    if (base/'installation.json').exists():
        r=json.loads((base/'installation.json').read_text());identity={'expected_run_id':r['run_id']}
        identity['marker_matches']=consumed and (base/'consumed').read_text().strip()==r['run_id']
    return {'report_ended':bool(end),'complete':bool(end) and not parse_errors and not end['capped']
            and not end['stuck_child'] and not end['failures'] and not end['truncated'] and not failures
            and wrapper_exit==0 and identity.get('marker_matches',consumed),
        'version':version,'capture_complete_is_not_hardware_qualification':True,'consumed':consumed,'identity':identity,
        'wrapper_exit':wrapper_exit,'end':end,'groups':dict(groups),'parse_errors':parse_errors,
        'failed_captures':failures,'captured':captured}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('base',type=Path);a=p.parse_args()
    print(json.dumps(analyze(a.base),indent=2))
