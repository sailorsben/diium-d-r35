"""Offline ELF review of privately captured tools; never executes vendor code."""
from pathlib import Path
from hashlib import sha256
import argparse,importlib.util,json,re,subprocess
ROOT=Path(__file__).resolve().parent.parent
def linux(path):
    path=path.resolve();return '/mnt/'+path.drive[0].lower()+path.as_posix()[2:]
def review(base):
    base=base.resolve();assert base.is_relative_to(ROOT/'device-evidence')
    records=[json.loads(x) for x in (base/'results/report.jsonl').read_text().splitlines()]
    dest=base/'offline-review';dest.mkdir(exist_ok=False);entries=[];missing=[]
    spec=importlib.util.spec_from_file_location('survey_analysis',ROOT/'build/analyze-device-survey.py')
    analysis=importlib.util.module_from_spec(spec);spec.loader.exec_module(analysis)
    priority=['/bin/nand_part_info','/bin/nandsync','/sysinit','/power_key','/wdt','/showlogo']
    candidates=[r for r in records if r.get('kind')=='capture' and r.get('output') and not r['errno'] and not r['truncated']]
    candidates.sort(key=lambda r:priority.index(r['source']) if r['source'] in priority else len(priority))
    for r in candidates:
        try: data=analysis.capture_bytes(base/'results',r)
        except (OSError,ValueError) as e:
            missing.append({'source':r['source'],'capture':r['output'],'error':str(e)});continue
        if data[:4]!=b'\x7fELF':continue
        if len(entries)>=32:break
        name=f'elf-{len(entries):04d}.bin'
        prefix=dest/name
        p=prefix;p.write_bytes(data)
        strings=[x.decode('ascii') for x in re.findall(rb'[ -~]{4,}',data)]
        leads=[s for s in strings if re.search(r'nand|flash|spi|usb|updat|ioctl|recover|boot|/dev/|/sys/|gpio|key',s,re.I)]
        prefix.with_suffix('.strings.txt').write_text('\n'.join(strings)+'\n',encoding='utf-8')
        entry={'source':r['source'],'capture':r['output'],'review_file':name,'sha256':sha256(data).hexdigest(),'leads':leads,'tool_results':[]}
        for label,args in [('readelf',['arm-linux-gnueabihf-readelf','-W','-h','-s','-d','-V']),
                           ('disassembly',['arm-linux-gnueabihf-objdump','-d'])]:
            result=subprocess.run(['wsl','--exec',*args,linux(p)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            text=result.stdout[:2*1024*1024].decode('utf-8',errors='replace')
            prefix.with_suffix('.'+label+'.txt').write_text(text,encoding='utf-8')
            entry['tool_results'].append({'tool':label,'exit':result.returncode,'truncated':len(result.stdout)>2*1024*1024})
        entries.append(entry)
    (dest/'index.json').write_text(json.dumps({'vendor_execution':False,'entries':entries,'missing_captures':missing},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'review_directory':str(dest),'elf_files_reviewed':len(entries),'vendor_execution':False},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('base',type=Path);a=p.parse_args();review(a.base)
