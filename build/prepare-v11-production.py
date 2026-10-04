from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
import csv, io, json, shutil

root = Path(__file__).resolve().parent.parent
build = root / 'build'
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
evidence = root / 'device-evidence' / ('v10-budget-return-' + stamp)
evidence.mkdir()
report = Path('D:/retro/emu_sfc_plus_v10_audio_priority.txt')
shutil.copy2(report, evidence / report.name)
shutil.copy2(Path('D:/retro/libs/emu_sfc.so'), evidence / 'emu_sfc.so')
text = report.read_text()
rows = list(csv.DictReader(io.StringIO('bin,adaptive_enabled,' + text.split('bin,adaptive_enabled,', 1)[1])))
rows = [{k: int(v) for k, v in r.items()} for r in rows if r.get('calls') is not None]
calls = sum(r['calls'] for r in rows)
draws = sum(r['draws'] for r in rows)
duplicates = sum(r['duplicates'] for r in rows)
assert calls == 23604 and calls == draws + duplicates
regular = [r for r in rows if r['calls'] == 120]
heavy = [r for r in regular if r['duplicates'] >= 15]
analysis = {
    'report_sha256': sha256(report.read_bytes()).hexdigest(),
    'core_frames': calls, 'drawn_frames': draws, 'held_frames': duplicates,
    'held_percent': round(100 * duplicates / calls, 3),
    'produced_audio_seconds': sum(r['audio_frames'] for r in rows) / 44100,
    'regular_bins': len(regular),
    'regular_bins_wall_seconds': sum(r['wall_us'] for r in regular) / 1e6,
    'regular_bins_audio_seconds': sum(r['audio_frames'] for r in regular) / 44100,
    'heavy_regular_bins': len(heavy),
    'heavy_bins_wall_seconds': sum(r['wall_us'] for r in heavy) / 1e6,
    'heavy_bins_audio_seconds': sum(r['audio_frames'] for r in heavy) / 44100,
    'heavy_bins_draws': sum(r['draws'] for r in heavy),
    'heavy_bins_held_frames': sum(r['duplicates'] for r in heavy),
    'aggregate_last_bin': rows[-1],
    'interpretation': '120-call intervals include about 119 inter-frame gaps; final aggregate includes user pauses. Queue snapshots are not an underrun counter.',
    'user_result': 'No clicks noticed during intro into Narshe and wind scenes; no obvious dropped frames noticed.',
}
(evidence / 'analysis.json').write_text(json.dumps(analysis, indent=2) + '\n')
(build / 'v10-return-path.txt').write_text(str(evidence) + '\n')
installation = root / 'SNES-Plus-v10-audio-priority/card-D-installation-verification.json'
data = json.loads(installation.read_text())
data['hardware_test'] = analysis['user_result']
data['returned_report'] = str(evidence / report.name)
data['hardware_analysis'] = analysis
installation.write_text(json.dumps(data, indent=2) + '\n')

# Keep the proven v10 scheduling mathematics; remove its measurement/report machinery.
h = (build / 'render_budget_v10.h').read_text()
algorithm = h[h.index('static uint32_t rb10_draw_us'):h.index('static void rt9_max')]
header = '''/* Adaptive rendering from the successful v10 handheld test.
 * Two monotonic reads per core frame; no OSS queries, report bins or file writes.
 * Audio/game CPU remain enabled. Test controls are unset on the handheld. */
#include <time.h>
static unsigned rt9_mode;
static bool rt9_disabled;
static uint64_t rt9_now(void)
{
   struct timespec t;
   if (clock_gettime(CLOCK_MONOTONIC, &t)) return 0;
   return (uint64_t)t.tv_sec * 1000000u + t.tv_nsec / 1000u;
}
''' + algorithm + '''static void rt9_reset(void)
{
   const char *v = getenv("D35_V10_DISABLE");
   rt9_disabled = v && !strcmp(v, "1");
   rt9_mode = 0; rb10_reset();
}
'''
(build / 'render_budget_production.h').write_text(header, newline='\n')
s = (build / 'emu_sfc_plus_clean.c').read_text()
s = s.replace('/* D-R35 stable adapter: v2 playback; diagnostic logging is opt-in only. */',
              '/* D-R35 production v11: adaptive rendering; diagnostic logging is opt-in only. */')
s = s.replace('static struct retro_system_av_info native_av;', 'static struct retro_system_av_info native_av;\n#include "render_budget_production.h"')
s = s.replace('*(int *)data = 3; return true;', '*(int *)data = rt9_mode ? 2 : 3; return true;')
s = s.replace('loaded = true; audio_reset(); runs', 'loaded = true; audio_reset(); rt9_reset(); runs')
s = s.replace('   p_retro_run(); ++runs;', '''   rt9_mode = rt9_select_mode();
   uint64_t began = rt9_now();
   p_retro_run(); ++runs;
   uint64_t end = rt9_now();
   if (end >= began) rb10_observe(rt9_mode, end - began);''')
s = s.replace('p_retro_reset(); audio_reset();', 'p_retro_reset(); audio_reset(); rt9_reset();')
s = s.replace('   audio_reset(); return true;\n}\nAPI void retro_set_controller', '   audio_reset(); rt9_reset(); return true;\n}\nAPI void retro_set_controller')
s = s.replace('adapter v2', 'adapter v11').replace('info->library_version = "v2"', 'info->library_version = "v11"')
assert s.count('rt9_reset();') == 3
(build / 'emu_sfc_plus_production.c').write_text(s, newline='\n')
check = (build / 'v10-budget-check.c').read_text().replace('emu_sfc_plus_v10_budget.c', 'emu_sfc_plus_production.c')
check = check.replace(' ++rt9_runs;', '').replace('rt9_runs==0', 'rt9_mode==0')
(build / 'production-budget-check.c').write_text(check, newline='\n')
script = (build / 'build-v10-budget.sh').read_text().replace('v10-budget', 'production').replace('emu_sfc_plus_v10_budget.c', 'emu_sfc_plus_production.c').replace('production-check.c', 'production-budget-check.c')
(build / 'build-production.sh').write_text(script, newline='\n')
capture = (build / 'capture-audio.c').read_text()
capture = capture.replace('static unsigned frame, video_count;', 'static unsigned frame, video_count, drawn_count, held_count;')
capture = capture.replace('   ++video_count;', '   ++video_count; if (data) ++drawn_count; else ++held_count;')
capture = capture.replace('   finish();dlclose(core);return 0;', '   printf("Drawn=%u Held=%u\\n",drawn_count,held_count);\n   finish();dlclose(core);return 0;')
(build / 'capture-production-check.c').write_text(capture, newline='\n')
print(json.dumps(analysis, indent=2))
