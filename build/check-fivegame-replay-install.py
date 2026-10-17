"""Exact replay-suite installer success and rollback fixtures; never opens I:."""
from pathlib import Path
import importlib.util,json,tempfile
from attempt_archive import digest

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/fivegame-kernel-private-v2'

def main():
    spec=importlib.util.spec_from_file_location('stage',ROOT/'build/install-fivegame-replay.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    cases=['success','payload','dispatcher','target_marker','mvp_marker','health-payload','health-armed','foreign-profile','foreign-marker','firmware-trigger']
    for fault in cases:
        with tempfile.TemporaryDirectory(dir=ROOT/'build') as tmp:
            card=Path(tmp);(card/'retro/snes-mvp').mkdir(parents=True)
            (card/'retro/snes-mvp/launch.sh').write_bytes(b'original')
            (card/'retro/save.srm').write_bytes(b'progress');(card/'retro/old.log').write_bytes(b'evidence')
            if fault=='foreign-profile':(card/m.TARGET).mkdir()
            if fault=='foreign-marker':(card/'retro/armed').write_bytes(b'foreign')
            if fault=='firmware-trigger':(card/'retro/Code.bkp').write_bytes(b'foreign')
            def atomic(path,data):path.write_bytes(data)
            def health(label):
                if fault=='health-'+label:raise RuntimeError('injected FAT failure')
            def inject(label):
                if fault==label:raise RuntimeError('injected write failure')
            def verify():assert (card/'retro/save.srm').read_bytes()==b'progress' and (card/'retro/old.log').read_bytes()==b'evidence'
            try:
                m.stage(card,{'payload':b'new'},b'dispatch',atomic,health,verify,inject)
            except (AssertionError,RuntimeError):
                assert fault!='success' and (card/'retro/snes-mvp/launch.sh').read_bytes()==b'original'
                assert not (card/'retro/snes-mvp/armed').exists() and not (card/m.TARGET/'armed').exists()
            else:assert fault=='success' and (card/m.TARGET/'armed').read_bytes()==m.MARKER
            verify()
    report={'passed':True,'checks':cases,'card_access':False,'installer_sha256':digest(ROOT/'build/install-fivegame-replay.py'),'checker_sha256':digest(Path(__file__)),'qualification_sha256':digest(OUT/'qualification.json'),'replay_checks_sha256':digest(OUT/'replay-checks.json')}
    (OUT/'installation-qualification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS ten installer success/refusal/rollback/FAT cases; saves/evidence intact')

if __name__=='__main__':main()
