from pathlib import Path
p = Path(__file__).resolve().parent
s = (p / 'emu_sfc_plus_clean.c').read_text()
s = s.replace('static struct retro_system_av_info native_av;', 'static struct retro_system_av_info native_av;\n#include "render_test_v9.h"')
s = s.replace('   if (frontend_batch) frontend_batch(output, output_count);', '   uint64_t rt9_write_start = rt9_audio_before();\n   if (frontend_batch) frontend_batch(output, output_count);')
s = s.replace('   output_frames += output_count;', '   rt9_audio_after(rt9_write_start, output_count);\n   output_frames += output_count;')
s = s.replace('   if (!frontend_video) return;', '   if (!frontend_video) return;\n   uint64_t rt9_video_start = rt9_now();')
s = s.replace('   if (!data) { frontend_video(NULL, w, h, (size_t)w * 2); return; }', '   if (!data) {\n      frontend_video(NULL, w, h, (size_t)w * 2);\n      ++rt9_current()->duplicates;\n      rt9_current()->video_us += rt9_now() - rt9_video_start;\n      return;\n   }')
s = s.replace('   video_slot ^= 1;', '   video_slot ^= 1;\n   ++rt9_current()->draws;\n   rt9_current()->video_us += rt9_now() - rt9_video_start;')
s = s.replace('      *(int *)data = 3; return true;', '      *(int *)data = rt9_mode ? 2 : 3; return true;')
s = s.replace('      loaded = true; audio_reset(); runs = native_frames = output_frames = 0;', '      loaded = true; audio_reset(); rt9_reset(); runs = native_frames = output_frames = 0;')
s = s.replace('   p_retro_run(); ++runs;', '''   rt9_mode = rt9_select_mode();
   uint64_t began = rt9_now();
   struct rt9_bin *b = rt9_current();
   if (!b->calls) b->first_us = began;
   p_retro_run(); ++runs;
   uint64_t end = rt9_now();
   ++b->calls; b->last_us = end; b->run_us += end - began;
   rt9_max(&b->max_run_us, end - began); ++rt9_runs;''')
s = s.replace('p_retro_reset(); audio_reset();', 'p_retro_reset(); audio_reset(); rt9_reset();')
s = s.replace('{ if (loaded) p_retro_unload_game(); loaded = false;', '{ if (loaded) { rt9_save(); p_retro_unload_game(); } loaded = false;')
s = s.replace('   bytes = (uint32_t)p_retro_serialize_size();', '   rt9_save();\n   bytes = (uint32_t)p_retro_serialize_size();')
s = s.replace('   audio_reset(); return true;\n}', '   audio_reset(); rt9_reset(); return true;\n}')
assert '*(int *)data = rt9_mode ? 2 : 3' in s
assert s.count('rt9_reset();') == 3
(p/'emu_sfc_plus_v9_render.c').write_text(s, newline='\n')
