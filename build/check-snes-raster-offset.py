"""Check Mode 2 geometry independently of the game replay windows."""
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory


BUILD = Path(__file__).resolve().parent
source = (BUILD/'multigame-fixes-private-v1/core/source/gfx.c').read_text()
start = source.index('static void DrawBackgroundOffset(')
end = source.index('static void DrawBackgroundMode5(', start)
with TemporaryDirectory(prefix='d35-raster-check-') as tmp:
    scratch = Path(tmp)
    (scratch/'offset-reference.inc').write_text(source[start:end])
    exe = scratch/'check'
    subprocess.run(['cc', '-std=gnu11', '-Wall', '-Wextra', '-Werror', '-Wno-sign-compare',
                    '-O2', '-I'+tmp, BUILD/'check-snes-raster-offset.c', '-o', exe], check=True)
    subprocess.run([exe], check=True)
