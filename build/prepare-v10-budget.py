from pathlib import Path
p = Path(__file__).resolve().parent
h = (p/'render_test_v9.h').read_text()
h = h.replace('D35_V9_DISABLE', 'D35_V10_DISABLE').replace('D35_V9_REPORT', 'D35_V10_REPORT')
h = h.replace('emu_sfc_plus_v9_render_test.txt', 'emu_sfc_plus_v10_audio_priority.txt')
h = h.replace('static unsigned rt9_select_mode(void)\n{ return !rt9_disabled && rt9_runs >= 1800 && rt9_runs < 3000; }', '''static uint32_t rb10_draw_us, rb10_skip_us, rb10_credit, rb10_fraction;
static unsigned rb10_forced;
static uint32_t rb10_budget(void)
{
   double fps = native_av.timing.fps;
   return fps > 40 && fps < 70 ? (uint32_t)(920000.0 / fps) : 15333;
}
static void rb10_reset(void)
{
   rb10_draw_us = rb10_skip_us = rb10_credit = rb10_fraction = rb10_forced = 0;
   const char *v = getenv("D35_V10_FORCE_HALF_RENDER");
   if (v && !strcmp(v,"1")) rb10_forced = 512;
}
static unsigned rt9_select_mode(void)
{
   if (rt9_disabled) return 0;
   rb10_credit += rb10_forced ? rb10_forced : rb10_fraction;
   if (rb10_credit >= 1024) { rb10_credit -= 1024; return 1; }
   return 0;
}
static void rb10_observe(unsigned skipped, uint64_t elapsed)
{
   /* Discard exceptional stalls; never adapt the sample rate or game clock. */
   if (!elapsed || elapsed > 100000) return;
   uint32_t *mean = skipped ? &rb10_skip_us : &rb10_draw_us;
   *mean = *mean ? (uint32_t)(((uint64_t)*mean * 7 + elapsed) / 8) : (uint32_t)elapsed;
   uint32_t budget = rb10_budget();
   uint32_t cheap = rb10_skip_us ? rb10_skip_us : rb10_draw_us / 2;
   if (rb10_draw_us <= budget || rb10_draw_us <= cheap) rb10_fraction = 0;
   else {
      rb10_fraction = (uint32_t)(((uint64_t)(rb10_draw_us - budget) * 1024) / (rb10_draw_us - cheap));
      if (rb10_fraction > 512) rb10_fraction = 512;
   }
}''')
h = h.replace('rt9_disabled = v && !strcmp(v, "1");', 'rt9_disabled = v && !strcmp(v, "1"); rb10_reset();')
h = h.replace('D-R35 v9 core-render A/B;', 'D-R35 v10 adaptive audio priority;')
h = h.replace('Runs 0-1799 normal; 1800-2999 core rendering off (audio/game CPU on); 3000+ normal. Schedule restarts after successful state load/reset.', 'Draw cost controls skipped rendering; at most one half of frames skipped. Audio/game processing stays enabled every frame. Estimates restart on successful state load/reset.')
h = h.replace('bin,render_off,calls,', 'bin,adaptive_enabled,calls,')
h = h.replace('i, !rt9_disabled && i >= 15 && i < 25, b->calls,', 'i, !rt9_disabled, b->calls,')
h = h.replace('   bool okay = fflush(f)', '   fprintf(f, "estimated_draw_us=%u estimated_skip_us=%u budget_us=%u skip_fraction_1024=%u forced_test_fraction=%u\\n", rb10_draw_us, rb10_skip_us, rb10_budget(), rb10_fraction, rb10_forced);\n   bool okay = fflush(f)')
(p/'render_budget_v10.h').write_text(h, newline='\n')
s = (p/'emu_sfc_plus_v9_render.c').read_text().replace('render_test_v9.h', 'render_budget_v10.h')
s = s.replace('rt9_max(&b->max_run_us, end - began); ++rt9_runs;', 'rt9_max(&b->max_run_us, end - began);\n   rb10_observe(rt9_mode, end - began); ++rt9_runs;')
(p/'emu_sfc_plus_v10_budget.c').write_text(s, newline='\n')
s = (p/'build-v9-render.sh').read_text().replace('v9-render','v10-budget').replace('emu_sfc_plus_v9_render','emu_sfc_plus_v10_budget')
(p/'build-v10-budget.sh').write_text(s, newline='\n')
