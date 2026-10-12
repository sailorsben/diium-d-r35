"""Offline owned ROM replay controls and exact-output qualification."""
from pathlib import Path
import subprocess, sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/confuser-private-v1'
Q=['qemu-arm','-cpu','cortex-a7','-L','build/sysroot','-E','LD_LIBRARY_PATH=build/sysroot/lib']
def replay(folder,state,inputs,core='build/a7-pair-private-v1/core/snes9x2005_plus_libretro.so'):
    folder=OUT/folder
    folder.mkdir(parents=True,exist_ok=True)
    assert not (folder/'replay.log').exists()
    (folder/'input.txt').write_text(inputs)
    with (folder/'input.txt').open() as src,(folder/'replay.log').open('w') as log:
        subprocess.run(Q+['build/a7-pair-private-v1/replay',core,'build/plus-a7-out/ff6.sfc',state,'-',str(folder.relative_to(ROOT))],
                       stdin=src,stdout=log,stderr=subprocess.STDOUT,check=True,cwd=ROOT)
if sys.argv[1]=='inspect':
    for f in (40,120,200):
        replay('inspect-'+str(f),'build/confuser-private-v1/selection/scene.state',
               'advance 8 100\nadvance 20 0\nadvance 8 100\nadvance '+str(f)+' 0\nimage\nquit\n')
elif sys.argv[1]=='select':
    replay('selection2','build/magitek-bio-private/scene.state',
           'advance 8 40\nadvance 30 0\nadvance 16 20\nadvance 30 0\nimage\nsave\nquit\n')
elif sys.argv[1]=='select-confuser':
    replay('confuser-selection','build/magitek-bio-private/scene.state',
           'advance 8 20\nadvance 30 0\nimage\nsave\nquit\n')
elif sys.argv[1]=='qualify':
    for name in ('baseline','bg3-window'):
        dest=OUT/name
        with (dest/'equivalence-confuser.log').open('x') as log:
            subprocess.run(Q+['build/a7-pair-private-v1/equivalence',
              'build/a7-pair-private-v1/core/snes9x2005_plus_libretro.so',
              str((dest/'core/snes9x2005_plus_libretro.so').relative_to(ROOT)),
              'build/plus-a7-out/ff6.sfc','build/confuser-private-v1/confuser-selection/scene.state',
              '1200','magitek-bio'],stdout=log,stderr=subprocess.STDOUT,check=True,cwd=ROOT)
    dest=OUT/'bg3-window'
    for label,state,iters,mode in [('bio','build/magitek-bio-private/scene.state','1200','magitek-bio'),
                                 ('general','build/combined-gameplay-private-v1/saves/game-a27f1c7a-3145728-core-b77a9eb3-794156.state','1200',None)]:
        with (dest/('equivalence-'+label+'.log')).open('x') as log:
            args=Q+['build/a7-pair-private-v1/equivalence',
              'build/a7-pair-private-v1/core/snes9x2005_plus_libretro.so',
              str((dest/'core/snes9x2005_plus_libretro.so').relative_to(ROOT)),
              'build/plus-a7-out/ff6.sfc',state,iters]
            if mode:args.append(mode)
            subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,check=True,cwd=ROOT)
elif sys.argv[1]=='qualify-blend':
    dest=OUT/(sys.argv[2] if len(sys.argv)>2 else 'bg3-blend')
    for label,state,iters,mode in [('confuser','build/confuser-private-v1/confuser-selection/scene.state','1200','magitek-bio'),
                                 ('bio','build/magitek-bio-private/scene.state','1200','magitek-bio')]:
        with (dest/('equivalence-'+label+'.log')).open('x') as log:
            subprocess.run(Q+['build/a7-pair-private-v1/equivalence',
              'build/a7-pair-private-v1/core/snes9x2005_plus_libretro.so',
              str((dest/'core/snes9x2005_plus_libretro.so').relative_to(ROOT)),
              'build/plus-a7-out/ff6.sfc',state,iters,mode],stdout=log,stderr=subprocess.STDOUT,check=True,cwd=ROOT)
elif sys.argv[1]=='oracle':
    subprocess.run(['gcc','-DUSE_BLARGG_APU','-std=c99','-O2','-Wall','-Wextra','-Werror',
      '-Wno-error=implicit-fallthrough','-Ibuild/snes9x2005/libretro-common/include',
      'build/confuser-window-check.c','-o',str((OUT/'window-check').relative_to(ROOT))],check=True,cwd=ROOT)
    with (OUT/'window-oracle.log').open('x') as log:
        subprocess.run([str(OUT/'window-check')],stdout=log,stderr=subprocess.STDOUT,check=True,cwd=ROOT)
elif sys.argv[1]=='blend-oracle':
    name=sys.argv[2] if len(sys.argv)>2 else 'bg3-blend'
    stem='blend' if name=='bg3-blend' else 'submask'
    source=(ROOT/'build/plus-a7-check.c').read_text()
    source=source.replace('#include "plus-a7-render.h"',
      'unsigned long long d35_census[128];\n#include "confuser-private-v1/'+name+'/core/source/a7_tile.h"\nunsigned long long d35_conf[128];')
    (OUT/(stem+'-check.c')).write_text(source)
    flags=['-DUSE_BLARGG_APU','-DD35_PLUS_A7','-mcpu=cortex-a7','-mfpu=neon-vfpv4','-mfloat-abi=hard',
           '-marm','-std=gnu99','-O2','-Wall','-Wextra','-Werror','-no-pie','-nostdlib',
           '-U_TIME_BITS','-D_TIME_BITS=32','-U_FILE_OFFSET_BITS','-D_FILE_OFFSET_BITS=32',
           '-Ibuild','-Ibuild/snes9x2005/libretro-common/include']
    libs=['-Lbuild/sysroot/lib','-Wl,--no-as-needed','-l:libm-2.30.so','-l:libc-2.30.so','-l:libgcc_s.so.1']
    subprocess.run(['arm-linux-gnueabihf-gcc']+flags+['/usr/arm-linux-gnueabihf/lib/crt1.o',
      'build/confuser-private-v1/'+stem+'-check.c']+libs+['-o','build/confuser-private-v1/'+stem+'-check'],check=True,cwd=ROOT)
    with (OUT/(stem+'-oracle.log')).open('x') as log:
        subprocess.run(Q+['build/confuser-private-v1/'+stem+'-check'],stdout=log,stderr=subprocess.STDOUT,check=True,cwd=ROOT)
