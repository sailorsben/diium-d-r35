"""Isolated real-emulator presentation policy. Never modifies frozen runners/card."""
from pathlib import Path
from hashlib import sha256
import json, shutil

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'build/presentation-runtime-private-v1'
BASE = ROOT / 'build/demand-private-v1/runtime-v1'

def digest(p): return sha256(p.read_bytes()).hexdigest()
def write(p, s): p.write_text(s, encoding='utf-8', newline='\n')
def edit(p, old, new):
    s = p.read_text()
    assert s.count(old) == 1, (p, old, s.count(old))
    write(p, s.replace(old, new))

def main():
    assert not OUT.exists(), 'Preserve previous candidates'
    proof = json.loads((ROOT/'build/demand-private-v1/runtime-proof.json').read_text())
    assert proof['passed']
    assert digest(ROOT/'build/demand-private-v1/owned-output-runner') == proof['runner_sha256']
    # The returned pressure3 runner pins the board/audio used on hardware.
    pressure = ROOT/'build/render-pressure3-private'
    q = json.loads((pressure/'qualification.json').read_text())
    assert q['passed']
    for n, h in q['private_support'].items(): assert digest(pressure/'runner'/n) == h, n
    OUT.mkdir(); rt = OUT/'runner'; rt.mkdir()
    frozen = {}
    for p in BASE.iterdir():
        if p.suffix in ('.c', '.h'):
            frozen[p.relative_to(ROOT).as_posix()] = digest(p)
            shutil.copyfile(p, rt/p.name)
    shutil.copyfile(ROOT/'build/plus-a7-profile.h', OUT/'plus-a7-profile.h')
    # Import only the pressure3 display board. Its PCM collector is diagnostic
    # and deliberately differs from production's durable fault capture.
    # Keep production audio/PCM and its failure persistence byte-identical.
    for n in ('board.c','board.h'):
        shutil.copyfile(pressure/'runner'/n, rt/n)
    assert 'board_video_target' in (rt/'board.c').read_text()
    p = rt/'runner.c'
    edit(p, '    bool have_previous, av_changed;', '''    bool have_previous, av_changed;
    unsigned presentation_policy, skip_presentation;
    void *render_scratch;
    uint64_t rendered, presentation_skipped, presentation_try_ns;''')
    edit(p, '    began=board_now_ns();\n    if(board_video_submit', '''    ++s.rendered;
    if(s.skip_presentation) { ++s.presentation_skipped; return; }
    began=board_now_ns();
    if(board_video_submit''')
    edit(p, '        if(board_video_reserve()<0) { fail("Display queue stalled: %s",board_last_error()); break; }', '''        { uint64_t wait=board_now_ns();
          int credit=s.presentation_policy?board_video_try_reserve():
              (board_video_reserve()<0?-1:1);
          s.presentation_try_ns+=board_now_ns()-wait;
          if(credit<0) { fail("Display queue unavailable: %s",board_last_error()); break; }
          s.skip_presentation=!credit; }''')
    edit(p, '        if(p_output_acquire){size_t bytes=0;void *target=board_video_target(&bytes);p_output_acquire(target,bytes);}', '''        if(p_output_acquire){
            size_t bytes=0;
            void *target=s.skip_presentation?(uint8_t *)s.render_scratch+32:board_video_target(&bytes);
            if(s.skip_presentation) bytes=512u*240u+32u;
            p_output_acquire(target,bytes);
        }''')
    # Allocate once, before starting PCM. The core retains its own full-layout
    # fallback for unsupported geometry. Its callback is still fully rendered.
    anchor = '    if(!ensure_directory(save_dir))'
    text = p.read_text(); assert text.count(anchor)==1
    text = text.replace(anchor, '''    s.presentation_policy=1;
    { const char *policy=getenv("D35_PRESENTATION_POLICY");
      if(policy) {
        if(strcmp(policy,"0")&&strcmp(policy,"1")) { fail("Invalid presentation policy"); goto done; }
        s.presentation_policy=(unsigned)(policy[0]-'0');
      }
    }
    if(posix_memalign(&s.render_scratch,64,512u*240u+64u)) {
        fail("Could not allocate presentation scratch"); goto done;
    }
    memset(s.render_scratch,0,512u*240u+64u);
'''+anchor)
    write(p,text)
    edit(p, '    if(s.core) dlclose(s.core);', '    if(s.core) dlclose(s.core);\n    free(s.render_scratch); s.render_scratch=NULL;')
    edit(p, '      "audio_cleared_frames=%llu', '''      "presentation_policy=%u\\nrendered_frames=%llu\\npresentation_skipped=%llu\\npresentation_try_ns=%llu\\n"
      "audio_cleared_frames=%llu''')
    edit(p, '      (unsigned long long)s.audio_cleared,(unsigned long long)s.audio_remaining,', '''      s.presentation_policy,(unsigned long long)s.rendered,
      (unsigned long long)s.presentation_skipped,(unsigned long long)s.presentation_try_ns,
      (unsigned long long)s.audio_cleared,(unsigned long long)s.audio_remaining,''')
    edit(p, '"build_version=1.19\\nsession_id=', '"build_version=1.19-presentation1\\nsession_id=')
    report={'version':'presentation-runtime1','frozen_sources':frozen,
            'pressure3_qualification_sha256':digest(pressure/'qualification.json'),
            'sources':{p.relative_to(OUT).as_posix():digest(p) for p in rt.iterdir() if p.is_file()},
            'card_access':False,'installed':False,'physical_result':'PENDING'}
    write(OUT/'preparation.json',json.dumps(report,indent=2)+'\n')
    print('Prepared isolated real-runner policy; no card access')

if __name__=='__main__': main()
