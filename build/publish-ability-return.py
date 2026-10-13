"""Publish bounded return statistics/receipts; never raw ROM/state/PCM buffers."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,sys
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def publish(archive):
    archive=archive.resolve();out=archive/'ability-analysis';public=ROOT/'evidence/2026-10-13/ability-return'
    assert archive.is_relative_to(ROOT/'device-evidence') and not public.exists()
    summary=json.loads((out/'summary.json').read_text());assert summary['cases_started']==400 and summary['bounded_cases_completed']==376
    assert summary['card_writes']==0 and summary['fat_clean'] and summary['marker_consumed']
    offline=json.loads((out/'offline-contexts/summary.json').read_text());assert offline['exact_output_state_completed_contexts']==11
    for r in offline['records']:
        log=out/f"offline-contexts/{r['case']:03d}.log";assert digest(log)==r['log_sha256']
        for n,h in r['identities'].items():assert digest(ROOT/n)==h,n
    spec=importlib.util.spec_from_file_location('ability_return_release',ROOT/'build/publish-snes-1.19.py');release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)
    manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();old=json.loads(raw)['entries']
    for e in old:assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
    public.mkdir(parents=True);entries=[]
    sources=[(out/'summary.json','summary.json'),(out/'cases.csv','cases.csv'),(out/'cases.json','cases.json'),
        (out/'failure-analysis.json','failure-analysis.json'),(out/'offline-contexts/summary.json','offline-summary.json')]
    for source,name in sources:
        published=public/name;published.write_bytes(release.public_text(source.read_bytes()))
        entries.append({'source':source.relative_to(ROOT).as_posix(),'published':published.relative_to(ROOT).as_posix(),
            'source_sha256':digest(source),'published_sha256':digest(published)})
    manifest.write_bytes(release.append_manifest(raw,entries));assert json.loads(manifest.read_bytes())['entries'][:len(old)]==old
    print(f'Published5 bounded return proofs; preserved{len(old)} historical entries;card writes0')
if __name__=='__main__':publish(Path(sys.argv[1]))
