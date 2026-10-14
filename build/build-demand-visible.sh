#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
python3 - <<'PY'
from pathlib import Path
import subprocess
source=Path('build/build-demand-final.sh').read_text().replace('build/demand-final-private-v2','build/demand-visible-private-v3').replace('"$(dirname "$0")/.."','"$(dirname "$0")/../.."')
p=Path('build/demand-visible-private-v3/build.sh');p.write_text(source)
subprocess.run(['sh',str(p)],check=True)
PY
