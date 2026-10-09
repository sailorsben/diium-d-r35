"""Summarize private survey evidence, preserving failures and partial captures."""
from pathlib import Path
from hashlib import sha256
import argparse, collections, json
def analyze(base):
    base=Path(base);report=base/'results/report.jsonl'
    if not report.exists(): return {'complete':False,'reason':'No report; inspect startup.log and marker identity'}
    records=[];parse_errors=[]
    for number,line in enumerate(report.read_text(encoding='utf-8').splitlines(),1):
        try: records.append(json.loads(line))
        except json.JSONDecodeError as e: parse_errors.append({'line':number,'error':str(e)})
    captured=[];groups=collections.defaultdict(collections.Counter);failures=[]
    for r in records:
        if r.get('kind')!='capture':continue
        name=r.get('output');g=groups[r['group']]
        if r['errno'] in [2,20]:g['missing']+=1
        elif r['errno']:g['failed']+=1;failures.append(r)
        else:g['read']+=1
        if r['truncated']:g['truncated']+=1
        if name:
            assert Path(name).name==name and name.startswith('capture-')
            p=base/'results'/name
            if not p.exists(): failures.append({'source':r['source'],'missing_capture':name});continue
            data=p.read_bytes();assert len(data)==r['bytes'],name
            captured.append({'source':r['source'],'output':name,'bytes':len(data),'sha256':sha256(data).hexdigest(),
                'errno':r['errno'],'truncated':r['truncated']})
    end=next((r for r in reversed(records) if r.get('kind')=='complete'),None)
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
        'capture_complete_is_not_hardware_qualification':True,'consumed':consumed,'identity':identity,
        'wrapper_exit':wrapper_exit,'end':end,'groups':dict(groups),'parse_errors':parse_errors,
        'failed_captures':failures,'captured':captured}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('base',type=Path);a=p.parse_args()
    print(json.dumps(analyze(a.base),indent=2))
