"""Exercise the actual collector's corrupted-entry seam without a card."""
from pathlib import Path
from unittest.mock import patch
import importlib.util, json, tempfile

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('collector',ROOT/'build/collect-snes-mvp.py')
collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)

with tempfile.TemporaryDirectory(dir=ROOT/'build') as temporary:
    fixture=Path(temporary);card=fixture/'card';project=fixture/'project'
    (card/'retro/snes-mvp/saves').mkdir(parents=True);project.mkdir()
    (card/'retro/snes-mvp/snes-mvp').write_bytes(b'runner')
    (card/'retro/init').write_bytes(b'init')
    (card/'retro/snes-mvp/saves/good.state').write_bytes(b'private preserved state')
    bad=card/'retro/snes-mvp/saves/bad.srm.bak';bad.write_bytes(b'unreadable fixture')
    before={p.relative_to(card).as_posix():p.read_bytes() for p in card.rglob('*') if p.is_file()}
    original=Path.is_file
    def stat(path):
        if path==bad:
            error=OSError('Corrupted entry fixture');error.winerror=1392;raise error
        return original(path)
    collector.ROOT=project
    with patch.object(Path,'is_file',stat):
        archive=collector.collect(card,allow_read_errors=True)
    result=json.loads((archive/'collection.json').read_text())
    assert result['card_writes']==0 and not result['complete']
    assert len(result['read_errors'])==1 and result['read_errors'][0]['winerror']==1392
    assert (archive/'snes-mvp/saves/good.state').read_bytes()==b'private preserved state'
    assert not (archive/'snes-mvp/saves/bad.srm.bak').exists()
    # Strict default must still stop; make its archive distinct this second.
    second=fixture/'strict';second.mkdir();collector.ROOT=second
    with patch.object(Path,'is_file',stat):
        try:collector.collect(card)
        except OSError:pass
        else:raise AssertionError('Strict install-baseline collection accepted corruption')
    assert before=={p.relative_to(card).as_posix():p.read_bytes() for p in card.rglob('*') if p.is_file()}
print('PASS actual collector preserves readable progress, records corruption, performs zero card writes, and strict default rejects damage')
