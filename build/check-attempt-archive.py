"""Exercise sparse collection on a fake card; never touches D: or I:."""
from pathlib import Path
import json
import importlib.util
import os
import tempfile
import unittest
from unittest.mock import patch
from attempt_archive import SCHEMA, digest, inventory, retain, verify_saved


class SparseArchiveTests(unittest.TestCase):
    def test_progress_logs_hashes_and_changed_generations(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temp:
            root = Path(temp)
            card = root/'card'
            samples = {'retro/saves/game.srm': b'save-one',
                       'retro/snes-mvp/last-session.txt': b'log-one',
                       'retro/test/results/run-1/pcm-history.txt': b'trace',
                       'retro/test/plan.json': b'{"config":1}',
                       'retro/test/cases/000/scene.state': b'frozen-fixture',
                       'retro/test/runner': b'executable',
                       'retro/libs/core.so': b'core',
                       'retro/swapfile': b'large-static',
                       '000/game.sfc': b'rom',
                       '000/game.sav': b'outside-save',
                       'system.cfg': b'outside-config'}
            for name, content in samples.items():
                p = card/name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(content)
            before = {n:digest(card/n) for n in samples}
            out1, out2, out3 = (root/'evidence'/n for n in ('one','two','three'))
            for out in (out1,out2,out3):
                out.mkdir(parents=True)
            first = inventory(card,out1) + inventory(card,out1,outside=True)
            self.assertEqual(len(first),len(samples))
            for e in first:
                self.assertEqual(e['sha256'],before[e['path']])
                self.assertEqual((out1/e['path']).exists(),retain(e['path']))
            second = inventory(card,out2) + inventory(card,out2,outside=True)
            self.assertEqual(sum(e['new_content_bytes'] for e in second),0)
            self.assertTrue(os.path.samefile(out1/'retro/saves/game.srm',out2/'retro/saves/game.srm'))
            self.assertEqual(before,{n:digest(card/n) for n in samples})
            (card/'retro/saves/game.srm').write_bytes(b'save-two')
            third = inventory(card,out3)
            self.assertEqual(sum(e['new_content_bytes'] for e in third),len(b'save-two'))
            self.assertEqual((out1/'retro/saves/game.srm').read_bytes(),b'save-one')
            self.assertEqual((out3/'retro/saves/game.srm').read_bytes(),b'save-two')
            verify_saved(out3,{'schema':SCHEMA,'all_retro_files':third})
            (out3/'retro/saves/game.srm').write_bytes(b'corrupt')
            with self.assertRaises(ValueError):
                verify_saved(out3,{'schema':SCHEMA,'all_retro_files':third})

    def test_no_bulk_copy_fallback(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temp:
            root = Path(temp)
            (root/'card/retro/saves').mkdir(parents=True)
            (root/'card/retro/saves/game.srm').write_bytes(b'save')
            (root/'evidence/one').mkdir(parents=True)
            with patch('attempt_archive.os.link',side_effect=OSError('no hardlinks')):
                with self.assertRaises(OSError):
                    inventory(root/'card',root/'evidence/one')
            self.assertFalse((root/'evidence/one/retro/saves/game.srm').exists())

    def test_classification(self):
        for path in ('retro/states/a.0','retro/game.srm.bak','retro/game.state.bkp',
                     'retro/uart/latest-boot.log','retro/test/results/run-1/raw.bin'):
            self.assertTrue(retain(path),path)
        for path in ('retro/test/expected.bin','retro/test/plan.json','retro/init',
                     'retro/test/cases/0/scene.state','roms/game.zip','retro/libs/core.so'):
            self.assertFalse(retain(path),path)

    def test_current_report_accepts_hash_only_payload(self):
        script = Path(__file__).with_name('report-presentation-ffvi.py')
        spec = importlib.util.spec_from_file_location('sparse_report_test',script)
        report = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(report)
        with tempfile.TemporaryDirectory(dir=script.parent) as temp:
            root = Path(temp)
            archive = root/'archive'
            target = archive/'retro/snes-presentation-ffvi1'
            run = target/'results/run-1'
            run.mkdir(parents=True)
            # Use the frozen local package; it must exist and match the receipt.
            payload = script.parent/'presentation-ffvi-private-v1'
            hashes = {n:digest(payload/n) for n in ('plan.json','launch.sh')}
            entries = [{'path':'retro/snes-presentation-ffvi1/'+n,'sha256':h,'stored':False}
                       for n,h in hashes.items()]
            (archive/'archive.json').write_text(json.dumps({'schema':SCHEMA,'fat_clean':True,
                'card_writes':0,'all_retro_files':entries}))
            receipt = root/'installed.json'
            receipt.write_text(json.dumps({'version':'presentation-ffvi1','payload_hashes':hashes}))
            with patch('sys.argv',[str(script),str(archive),'--installation',str(receipt)]), \
                 patch.object(report,'analyze',return_value={'epochs':[],'physical':True}) as analyze:
                report.main()
                self.assertEqual(analyze.call_args.args[0],run)
            self.assertFalse((target/'plan.json').exists())
            # A manifest hash mismatch is rejected even when local bytes exist.
            entries[0]['sha256']='0'*64
            (archive/'archive.json').write_text(json.dumps({'schema':SCHEMA,'fat_clean':True,
                'card_writes':0,'all_retro_files':entries}))
            with patch('sys.argv',[str(script),str(archive),'--installation',str(receipt)]):
                with self.assertRaises(AssertionError):
                    report.main()


if __name__ == '__main__':
    unittest.main()
