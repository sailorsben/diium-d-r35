"""Publish derived demand return and telemetry, never ROM/state/vendor bytes."""
from pathlib import Path
from hashlib import sha256
import json,shutil,sys
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 report=archive/'demand-gameplay-return-analysis.json';r=json.loads(report.read_text())
 assert r['card_writes']==0 and r['FAT_clean'] and r['all_archive_hashes_verified']
 for n,h in r['input_hashes'].items():assert digest(ROOT/n)==h,n
 dest=ROOT/'evidence/2026-10-14/demand-gameplay-return';assert not dest.exists();dest.mkdir()
 manifest=ROOT/'evidence/manifest.json';m=json.loads(manifest.read_text())
 # All previous published receipts stay exact.
 for e in m['entries']:assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
 frozen=ROOT/'build/demand-visible-private-v3/frozen.json'
 for n,h in json.loads(frozen.read_text()).items():assert digest(ROOT/n)==h,n
 for name,source in [('analysis.json',report),('session-telemetry.txt',archive/'retro/snes-demand-gameplay1/saves/last-session.txt')]:
  target=dest/name;shutil.copy2(source,target);assert digest(source)==digest(target)
  m['entries'].append({'source':source.relative_to(ROOT).as_posix(),'published':target.relative_to(ROOT).as_posix(),
   'source_sha256':digest(source),'published_sha256':digest(target),'bytes':target.stat().st_size,'normalized':False})
 manifest.write_text(json.dumps(m,indent=2)+'\n')
 print(json.dumps({'published':str(dest),'card_writes':0,'old_evidence_and_frozen_inputs_verified':True}))
if __name__=='__main__':main(Path(sys.argv[1]))
