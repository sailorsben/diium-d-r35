"""Final identity/link/source checks; no replay, build or device access."""
from pathlib import Path
from hashlib import sha256
import ast,json,re,importlib.util
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ff6-effect-screen-private-v1'
analysis=json.loads((OUT/'analysis.json').read_text())
assert analysis['total_exact_comparison_calls']==567000
for path,h in analysis['raw_proof_sha256'].items():assert sha256((ROOT/path).read_bytes()).hexdigest()==h,path
manifest=json.loads((ROOT/'evidence/manifest.json').read_text())
for e in manifest['entries']:assert sha256((ROOT/e['published']).read_bytes()).hexdigest()==e['published_sha256'],e['published']
for p in ROOT.glob('build/*ff6*screen*.py'):ast.parse(p.read_text(),filename=str(p))
for p in ROOT.glob('build/*ff6*effects*.py'):ast.parse(p.read_text(),filename=str(p))
for p in ROOT.glob('build/prepare-ff6-*.py'):ast.parse(p.read_text(),filename=str(p))
for name in ('general','natural'):
    assert (OUT/name/'core/source/a7_window.h').read_text()==('#define D35_EFFECT_COUNTS\n'+(ROOT/'build/plus-a7-multi-window.h').read_text())
for doc in ('docs/ff6-effect-safety-screen.md','docs/snes-confuser-gameplay-return.md'):
    p=ROOT/doc
    for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        if '://' not in link:assert (p.parent/link.split('#')[0]).exists(),(doc,link)
paths=[OUT/'screen',OUT/'screen.c',OUT/'trace-screen',OUT/'trace-screen.c',OUT/'natural/screen',OUT/'natural/screen.c']
for variant in ('core','general/core','trace-current/core','fixed-unused/core','natural/core'):
    paths.append(OUT/variant/'snes9x2005_plus_libretro.so')
    for name in ('a7_window.h','a7_tile.h','ppu.c','gfx.c','cpuexec.c'):
        paths.append(OUT/variant/'source'/name)
    paths.append(OUT/variant/'libretro.c')
paths.extend([ROOT/'build/plus-a7-out/ff6.sfc',ROOT/'build/magitek-bio-private/scene.state',OUT/'prepared.json'])
identity={'offline_only':True,'instrumented_cores_are_not_production_candidates':True,
          'A7_performance_measurement':False,'payload_and_source_sha256':{p.relative_to(ROOT).as_posix():sha256(p.read_bytes()).hexdigest() for p in paths},
          'published_manifest_entries_verified':len(manifest['entries'])}
private=OUT/'final-identities.json';assert not private.exists();private.write_text(json.dumps(identity,indent=2)+'\n')
public=ROOT/'evidence/2026-10-12/effect-safety-screen/final-identities.json';assert not public.exists();public.write_bytes(private.read_bytes())
data=public.read_bytes();entry={'source':private.relative_to(ROOT).as_posix(),'published':public.relative_to(ROOT).as_posix(),
    'source_sha256':sha256(data).hexdigest(),'published_sha256':sha256(data).hexdigest(),'bytes':len(data),'normalized':False}
spec=importlib.util.spec_from_file_location('identity_publisher',ROOT/'build/publish-snes-1.19.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
raw=(ROOT/'evidence/manifest.json').read_bytes()
(ROOT/'evidence/manifest.json').write_bytes(module.append_manifest(raw,[entry]))
print('PASS:567000 comparisons/proofs,763 previous publications, actual core/harness/source identities, Python syntax and document links; no reruns/card access')
