"""Build isolated real runner and exercise ownership, real core and PCM seams."""
from pathlib import Path
from hashlib import sha256
import json, os, re, shutil, subprocess
from concurrent.futures import ThreadPoolExecutor

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/presentation-runtime-private-v1'
RT=OUT/'runner'

def digest(p): return sha256(p.read_bytes()).hexdigest()
def write(p,s): p.write_text(s,encoding='utf-8',newline='\n')
def run(args,log,timeout=120):
    with (OUT/log).open('w') as f:
        r=subprocess.run(args,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
    assert r.returncode==0,(args,log,(OUT/log).read_text()[-3000:])
    return (OUT/log).read_text()
def replace(s,a,b):
    assert s.count(a)==1,(a,s.count(a))
    return s.replace(a,b)

def main():
    assert os.name!='nt','Run through WSL for installed ARM tools'
    assert not (OUT/'qualification.json').exists()
    prep=json.loads((OUT/'preparation.json').read_text())
    for n,h in prep['frozen_sources'].items(): assert digest(ROOT/n)==h,n
    for n,h in prep['sources'].items(): assert digest(OUT/n)==h,n
    flags=['-mcpu=cortex-a7','-mfpu=neon-vfpv4','-mfloat-abi=hard','-marm',
           '-fno-stack-protector','-D_TIME_BITS=32','-D_FILE_OFFSET_BITS=32',
           '-std=gnu99','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-no-pie','-nostdlib',
           '-Ibuild/snes9x2005/libretro-common/include','/usr/arm-linux-gnueabihf/lib/crt1.o']
    libs=['-Lbuild/sysroot/lib','-Wl,--no-as-needed']+['-l:'+n for n in (
        'libdl-2.30.so','libz.so.1','libpthread-2.30.so','librt-2.30.so','libm-2.30.so','libc-2.30.so','libgcc_s.so.1','ld-2.30.so')]
    compat=['build/glibc230-stat-compat.c']
    run(['arm-linux-gnueabihf-gcc',*flags,'-O3','-flto=4','-DD35_NATIVE_PCM',*[str(RT/n) for n in (
        'main.c','ui.c','board.c','runner.c','audio-owner.c','native-pcm.c','startup.c','platform.c','timing.c')],
        *compat,*libs,'-o',str(OUT/'snes-mvp')],'build.log')
    abi=run(['arm-linux-gnueabihf-readelf','-V',str(OUT/'snes-mvp')],'abi.txt')
    versions=set(re.findall(r'Name: (GLIBC_[\d.]+)',abi))
    assert all(tuple(map(int,n[6:].split('.')))<=(2,30) for n in versions)
    # Same state machine as physical pressure3, with actual direct-output board.
    s=(ROOT/'build/check-pressure3-reservation.c').read_text().replace(
        '"render-pressure3-private/runner/board.c"','"runner/board.c"')
    write(OUT/'reservation-check.c',s)
    native_flags=['gcc','-std=gnu99','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',
                  '-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-pthread']
    run([*native_flags,str(OUT/'reservation-check.c'),'-ldl','-o',str(OUT/'reservation-check')],'reservation-build.log')
    ownership=run([str(OUT/'reservation-check')],'reservation.log')
    # Real worker: hold scanout while filling FIFO, verify try never modifies
    # queued pixels, release it, then verify close joins before buffers are freed.
    s=(RT/'display-queue-check.c').read_text()
    s=replace(s,'    assert(!pthread_create(&producer,NULL,fourth,NULL));', '''    unsigned char before[SLOT_BYTES*SOURCE_SLOTS]; memcpy(before,owned,sizeof(before));
    assert(board_video_try_reserve()==0);
    assert(!memcmp(before,owned,sizeof(before)));
    assert(!pthread_create(&producer,NULL,fourth,NULL));''')
    write(RT/'presentation-queue-check.c',s)
    run([*native_flags,str(RT/'presentation-queue-check.c'),str(RT/'timing.c'),'-ldl','-o',str(OUT/'queue-check')],'queue-build.log')
    queue=run([str(OUT/'queue-check')],'queue.log')
    # Actual runner/owner/native client fixture: intermittent exhausted display
    # credit must retain 120 renders and all PCM, with two state-load resumes.
    s=(ROOT/'build/demand-private-v1/runtime-v1/demand-native-check.c').read_text()
    s=replace(s,'static unsigned output_slot,direct_calls;', 'static unsigned output_slot,direct_calls,try_calls,finish_calls;')
    s=replace(s,'int board_audio_finish(void) { return pcm_finish(); }',
              'int board_audio_finish(void) { ++finish_calls; return pcm_finish(); }')
    s=replace(s,'void board_video_cancel(void) { }', '''int board_video_try_reserve(void) {
    ++try_calls;
    if(!deficit_mode && (s.runs%3)==1) return 0;
    return board_video_reserve()<0?-1:1;
}
void board_video_cancel(void) { }''')
    s=replace(s,'s.runs==120 && s.videos==120', 's.runs==120 && s.rendered==120 && s.videos==80 && s.presentation_skipped==40')
    s=replace(s,'assert(direct_calls>=120);','assert(direct_calls>=80 && try_calls>=120 && finish_calls==3);')
    s=s.replace('120 full drawings','120 full renders / 80 presentations / 40 intentional skips')
    write(RT/'presentation-native-check.c',s)
    run(['arm-linux-gnueabihf-gcc',*flags,str(RT/'presentation-native-check.c'),*compat,*libs,'-o',str(OUT/'native-check')],'native-build.log')
    # Copy the already qualified core; no core source or serialization changes.
    core=ROOT/'build/demand-visible-private-v3/core/snes9x2005_plus_libretro.so'
    assert digest(core)=='1eaf05f36adcbc8286de5777cc47f1cf24a588856a2b0a85e48a9bfa0984e6f8'
    shutil.copyfile(core,OUT/'plus-a7.so')
    import struct,zlib
    saves=OUT/'native';saves.mkdir(exist_ok=True)
    rom=ROOT/'build/plus-a7-out/ff6.sfc'; cb=core.read_bytes();rb=rom.read_bytes()
    state=bytearray((ROOT/'build/ability-regression-private-v1/cases/001/scene.state').read_bytes())
    assert zlib.crc32(state[40:])&0xffffffff==struct.unpack_from('<I',state,32)[0]
    struct.pack_into('<II',state,20,zlib.crc32(cb)&0xffffffff,len(cb))
    name='game-%08x-%d-core-%08x-%d.state'%(zlib.crc32(rb)&0xffffffff,len(rb),zlib.crc32(cb)&0xffffffff,len(cb))
    write_path=saves/name;write_path.write_bytes(state)
    qemu=['qemu-arm','-cpu','cortex-a7','-L','build/sysroot','-E','LD_LIBRARY_PATH=build/sysroot/lib']
    native=run([*qemu,str(OUT/'native-check'),str(rom),str(OUT/'plus-a7.so'),str(saves)],'native.log')
    assert 'two snapshot loads' in native and '40 intentional skips' in native
    # Independent full-pixel/PCM/normalized-state oracle over original inputs.
    # Alternate direct slot, private scratch and no acquisition fallback.
    s=(ROOT/'build/demand-private-v1/compare.c').read_text()
    s=replace(s,'uint8_t *owned_owner=calloc(1,512*240+256);',
              'uint8_t *scratch_owner=calloc(1,512*240+256);assert(scratch_owner);uint8_t *scratch=(uint8_t *)(((uintptr_t)scratch_owner+63)&~(uintptr_t)63);\n    uint8_t *owned_owner=calloc(1,512*240+256);')
    s=replace(s,'if(acquire)assert(acquire(owned+64,512*240+64));',
              'if(acquire){if(frame%5==4)assert(!acquire(NULL,0));else assert(acquire((frame%3==1?scratch:owned)+64,512*240+64));}')
    write(OUT/'compare.c',s)
    shutil.copyfile(ROOT/'build/demand-private-v1/demand-equivalence.c',OUT/'demand-equivalence.c')
    run(['arm-linux-gnueabihf-gcc',*flags,'-DUSE_BLARGG_APU','-Ibuild',str(OUT/'compare.c'),*libs,'-o',str(OUT/'compare')],'compare-build.log')
    manifest=json.loads((ROOT/'build/ability-regression-private-v1/plan.json').read_text())
    cases=manifest['cases']
    def compare(case):
        # The manifest provides exact original state/input and expected effect.
        folder=ROOT/'build/ability-regression-private-v1/cases'/f"{case['seq']:03d}"
        effect=case['observed_effect_id']
        log=f"compare-{case['seq']:03d}.log"
        text=run([*qemu,str(OUT/'compare'),str(core),str(OUT/'plus-a7.so'),str(rom),str(folder/'scene.state'),str(folder/'input.txt'),str(effect),'1200'],log,480)
        assert 'PASS 1200 calls: exact graphics/PCM/state' in text
        print('PASS real-core scratch/direct/fallback equivalence:',case['name'],flush=True)
        return {'index':case['seq'],'name':case['name'],'calls':1200,'log_sha256':digest(OUT/log)}
    with ThreadPoolExecutor(max_workers=3) as pool:
        results=list(pool.map(compare,cases))
    result={'version':'presentation-runtime1','passed':True,'card_access':False,'installed':False,'armed':False,
            'physical_result':'PENDING','production_gate':False,'A7_performance_evidence':False,
            'ownership':ownership.strip(),'worker':queue.strip(),
            'native':[l for l in native.splitlines() if l.startswith('PASS:')],
            'real_core_comparisons':results,'core_sha256':digest(core),'runner_sha256':digest(OUT/'snes-mvp'),
            'abi_versions':sorted(versions),'preparation_sha256':digest(OUT/'preparation.json'),
            'sources':{str(p.relative_to(ROOT)).replace('\\','/'):digest(p) for p in [ROOT/'build/prepare-presentation-runtime.py',ROOT/'build/check-presentation-runtime.py']},
            'generated_sources':{str(p.relative_to(OUT)):digest(p) for p in OUT.rglob('*') if p.suffix in ('.c','.h')},
            'log_hashes':{p.name:digest(p) for p in OUT.glob('*.log')}}
    for n,h in prep['frozen_sources'].items(): assert digest(ROOT/n)==h,n
    write(OUT/'qualification.json',json.dumps(result,indent=2)+'\n')
    print('PASS isolated production-runner integration; physical qualification PENDING')

if __name__=='__main__': main()
