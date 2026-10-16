"""Additional actual-runner controls: blocking policy, display error and rejects."""
from pathlib import Path
from hashlib import sha256
import json, subprocess

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/presentation-runtime-private-v1'
RT=OUT/'runner'
def digest(p): return sha256(p.read_bytes()).hexdigest()
def main():
    q=json.loads((OUT/'qualification.json').read_text());assert q['passed']
    for n,h in q['generated_sources'].items(): assert digest(OUT/n)==h,n
    s=(RT/'presentation-native-check.c').read_text()
    s=s.replace('static unsigned output_slot,direct_calls,try_calls,finish_calls;',
                'static unsigned output_slot,direct_calls,try_calls,finish_calls,display_error;')
    s=s.replace('    ++try_calls;', '    ++try_calls; if(display_error)return -1;')
    anchor='    pthread_mutex_lock(&kernel_lock); consumer_stop=1;'
    assert s.count(anchor)==1
    s=s.replace(anchor,'''    unsigned previous_tries=try_calls;
    deficit_mode=0;menu_visits=menu_action=0;next_menu=8;
    before=device_accepted;
    assert(!setenv("D35_PRESENTATION_POLICY","0",1));
    rc=runner_run(argv[1],argv[2],argv[3]);
    if(rc)fprintf(stderr,"blocking control: %s\\n",runner_last_error());
    assert(!rc && s.runs==120 && s.rendered==120 && s.videos==120 && !s.presentation_skipped);
    assert(try_calls==previous_tries && s.snapshot_loads==2 && s.pauses==2 && !s.render_scratch);
    audio_pipe_stats(&out);assert(!out.errors&&!out.remaining&&!out.cleared);
    assert(out.accepted==out.enqueued && out.accepted==device_accepted-before && finish_calls==6);
    puts("PASS: actual blocking control retains 120/120 presentations, identical PCM accounting, two state resumes and exactly three drains");
    assert(!setenv("D35_PRESENTATION_POLICY","1",1));
    display_error=1;next_menu=UINT_MAX;
    assert(runner_run(argv[1],argv[2],argv[3])<0);
    assert(strstr(runner_last_error(),"Display queue unavailable") && !s.runs && !s.rendered && !s.render_scratch && device_fd<0);
    unsigned opened_before=device_opens;
    assert(!setenv("D35_PRESENTATION_POLICY","invalid",1));
    assert(runner_run(argv[1],argv[2],argv[3])<0);
    assert(strstr(runner_last_error(),"Invalid presentation policy") && !s.runs && !s.render_scratch && device_opens==opened_before);
    unsetenv("D35_PRESENTATION_POLICY");
    memset(&s,0,sizeof(s));s.skip_presentation=1;
    video(NULL,256,224,512);assert(s.failed && s.video_dupes==1 && !s.presentation_skipped);
    memset(&s,0,sizeof(s));s.skip_presentation=1;
    uint16_t pixel=0;video(&pixel,513,224,1026);assert(s.failed && !s.rendered && !s.presentation_skipped);
    puts("PASS: unavailable display fails before core call; invalid policy, omitted drawing and invalid geometry remain errors during skip policy");
'''+anchor)
    # The extended test adds valid drains, then clears runner state for callback
    # rejection checks; the original assertion belongs to the original run only.
    s=s.replace(' && finish_calls==3','')
    target=RT/'presentation-controls-check.c';target.write_text(s,encoding='utf-8',newline='\n')
    flags=['-mcpu=cortex-a7','-mfpu=neon-vfpv4','-mfloat-abi=hard','-marm','-fno-stack-protector',
           '-D_TIME_BITS=32','-D_FILE_OFFSET_BITS=32','-std=gnu99','-O2','-Wall','-Wextra','-Werror',
           '-Wno-misleading-indentation','-no-pie','-nostdlib','-Ibuild/snes9x2005/libretro-common/include',
           '/usr/arm-linux-gnueabihf/lib/crt1.o']
    libs=['-Lbuild/sysroot/lib','-Wl,--no-as-needed']+['-l:'+n for n in (
        'libdl-2.30.so','libz.so.1','libpthread-2.30.so','librt-2.30.so','libm-2.30.so','libc-2.30.so','libgcc_s.so.1','ld-2.30.so')]
    subprocess.run(['arm-linux-gnueabihf-gcc',*flags,str(target),'build/glibc230-stat-compat.c',*libs,
                    '-o',str(OUT/'controls-check')],cwd=ROOT,check=True)
    log=OUT/'controls.log'
    with log.open('w') as f:
        subprocess.run(['qemu-arm','-cpu','cortex-a7','-L','build/sysroot','-E','LD_LIBRARY_PATH=build/sysroot/lib',
                        str(OUT/'controls-check'),str(ROOT/'build/plus-a7-out/ff6.sfc'),str(OUT/'plus-a7.so'),str(OUT/'native')],
                       cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
    result={'passed':True,'physical_result':'PENDING','card_access':False,
            'qualification_sha256':digest(OUT/'qualification.json'),'checker_sha256':digest(Path(__file__)),
            'generated_fixture_sha256':digest(target),'log_sha256':digest(log),
            'output':[l for l in log.read_text().splitlines() if l.startswith('PASS:')]}
    (OUT/'controls-qualification.json').write_text(json.dumps(result,indent=2)+'\n')
    print('\n'.join(result['output']))
if __name__=='__main__': main()
