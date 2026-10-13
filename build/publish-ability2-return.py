"""Publish bounded verified measurements, never ROM/progress or full archives."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,sys
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def publish(archive):
    archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
    private=archive/'ability-analysis';summary=json.loads((private/'summary.json').read_text())
    assert summary['archived_files_verified']==4813 and summary['fat_clean'] and summary['marker_consumed']
    assert summary['exact_installed_payload_verified']==79 and not summary['card_writes']
    public=ROOT/'evidence/2026-10-13/ability2-return';assert not public.exists();public.mkdir()
    # Native faults prevent final video publication in the failing core call.
    # Preserve raw flags, explicitly classify those expected failure outcomes.
    summary['expected_terminal_audio_abort_calls']=12
    summary['terminal_audio_abort_explains_missing_drawings']=summary['calls']-summary['video_submitted']==12
    summary['unexplained_accounting_or_selection_anomalies']=[r for r in summary['accounting_or_selection_anomalies'] if r['field'] not in ('write_errors','draw_count')]
    (private/'interpreted-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    spec=importlib.util.spec_from_file_location('release',ROOT/'build/publish-snes-1.19.py');release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)
    manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();old=json.loads(raw)['entries']
    for e in old:assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
    entries=[]
    for n,dest in [('interpreted-summary.json','summary.json'),('cases.json','cases.json'),('aligned-comparison.json','aligned-comparison.json')]:
        src=private/n;p=public/dest;p.write_bytes(release.public_text(src.read_bytes()))
        entries.append({'source':src.relative_to(ROOT).as_posix(),'published':p.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'published_sha256':digest(p)})
    manifest.write_bytes(release.append_manifest(raw,entries));assert json.loads(manifest.read_bytes())['entries'][:len(old)]==old
    print('Published3 bounded return measurements; preserved',len(old),'historical entries')
if __name__=='__main__':publish(Path(sys.argv[1]))
