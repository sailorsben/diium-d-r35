"""Actual runner/native and wrapper seams; never A7 performance evidence."""
from pathlib import Path
import os,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ability-suite-private-v1'
def check():
    source=(ROOT/'build/a7-pair-private-v1/runner/pair-native-check.c').read_text()
    source=source.replace('/* Both real worker owners have joined','/* Audio joined, display idle:')
    p=OUT/'runner/ability-native-check.c';p.write_text(source,newline='\n')
    libraries=['-L'+str(ROOT/'build/sysroot/lib'),'-Wl,--no-as-needed']+['-l:'+n for n in ('libdl-2.30.so','libz.so.1','libpthread-2.30.so','librt-2.30.so','libm-2.30.so','libc-2.30.so','libgcc_s.so.1','ld-2.30.so')]
    subprocess.run(['arm-linux-gnueabihf-gcc','-mcpu=cortex-a7','-mfpu=neon-vfpv4','-mfloat-abi=hard','-marm','-fno-stack-protector','-U_TIME_BITS','-D_TIME_BITS=32','-U_FILE_OFFSET_BITS','-D_FILE_OFFSET_BITS=32','-std=gnu99','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-no-pie','-nostdlib','-I'+str(ROOT/'build/snes9x2005/libretro-common/include'),'/usr/arm-linux-gnueabihf/lib/crt1.o',str(p),str(ROOT/'build/glibc230-stat-compat.c'),*libraries,'-o',str(OUT/'ability-native-check')],check=True)
    capture=OUT/'native-v3';capture.mkdir()
    case=OUT/'targeted-cases/000'
    env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib'),'D35_ABILITY_INPUT':str(case/'input.txt'),'D35_ABILITY_EXPECTED':str(case/'expected.bin')}
    with (OUT/'native-v3.log').open('w') as f:
        subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(OUT/'ability-native-check'),str(ROOT/'build/plus-a7-out/ff6.sfc'),str(OUT/'plus-a7.so'),str(case/'scene.state'),str(capture)],env=env,check=True,stdout=f,stderr=subprocess.STDOUT)
    assert 'PASS: consuming native provider' in (OUT/'native-v3.log').read_text()
    s=(OUT/'launch.sh').read_text().replace('BASE=/usr/retro/snes-ability1','BASE=$D35_MVP_BASE').replace('TRIGGER=/usr/retro/snes-mvp','TRIGGER=$D35_MVP_BASE')
    wrapper=OUT/'fixture-launch.sh';wrapper.write_text(s,newline='\n')
    s=(ROOT/'build/snes-mvp/check-startup-wrapper.py').read_text().replace("base/'snes-mvp'","base/'ability-suite'")
    anchor='    start=time.monotonic()';assert s.count(anchor)==1
    s=s.replace(anchor,"    (base/'owner.rom').write_text('fixture owner ROM')\n    (base/'ROM-PATH.txt').write_text(str(base/'owner.rom')+'\\n')\n"+anchor)
    fixture=OUT/'wrapper-check.py';fixture.write_text(s,newline='\n')
    with (OUT/'wrapper-check.log').open('w') as f:
        subprocess.run([sys.executable,str(fixture),str(OUT/'wrapper-fixtures')],env={**os.environ,'D35_WRAPPER_UNDER_TEST':str(wrapper)},check=True,stdout=f,stderr=subprocess.STDOUT)
    assert 'zero diagnostic card writes or global sync during ready child' in (OUT/'wrapper-check.log').read_text()
    print('PASS: native consuming/fault/drain/deficit and one-shot splash/wrapper seams')
if __name__=='__main__':check()
