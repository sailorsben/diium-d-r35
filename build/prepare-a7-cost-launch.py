"""Create an isolated measurement launcher, without writing the card."""
from pathlib import Path
from hashlib import sha256
import json, sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build'/sys.argv[1];q=json.loads((OUT/'verification.json').read_text());assert q['passed']
original=ROOT/'releases/snes-mvp-1.19/launch.sh'
release=json.loads((ROOT/'releases/snes-mvp-1.19/manifest.json').read_text())
assert sha256(original.read_bytes()).hexdigest()==release['wrapper_sha256']
text=original.read_text()
text=text.replace('BASE=${D35_MVP_BASE:-/usr/retro/snes-mvp}',
                  'BASE=/usr/retro/snes-cost1\nTRIGGER=/usr/retro/snes-mvp')
text=text.replace('"$BASE/armed"','"$TRIGGER/armed"')
old='"$BASE/snes-mvp" --base "$BASE" --core "$BASE/plus-a7.so" > "$RUNTIME_LOG" 2>&1 &'
assert text.count(old)==1
text=text.replace(old,'''IFS= read -r D35_COST_ROM < "$BASE/ROM-PATH.txt" || exit 1
[ -f "$D35_COST_ROM" ] || exit 1
"$BASE/unit-suite" "$BASE" "$BASE/measure-core.so" "$D35_COST_ROM" "$BASE/replay.state" > "$RUNTIME_LOG" 2>&1 &''')
text=text.replace('1.19','1.19-cost1')
(OUT/'launch.sh').write_text(text,encoding='utf-8',newline='\n')
(OUT/'dispatch.sh').write_text('#!/bin/sh\nexec /usr/retro/snes-cost1/launch.sh\n',encoding='utf-8',newline='\n')
print('Created separate diagnostic launcher; stock/production binaries are not payloads')
