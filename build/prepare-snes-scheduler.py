"""Apply one isolated scheduling experiment to the frozen five-game core."""
from pathlib import Path


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f'Expected one matching source anchor: {old[:80]}')
    return source.replace(old, new)


CENSUS = '''/* Separate diagnostic build. Output is read only after replay. */
static uint64_t d35_apu_counts[8];
__attribute__((visibility("default"))) void d35_apu_census(uint64_t *out)
{
   memcpy(out, d35_apu_counts, sizeof(d35_apu_counts));
   memset(d35_apu_counts, 0, sizeof(d35_apu_counts));
}
'''

NOOP_GUARD = '''   /* An instruction that cannot begin/finish at this timestamp takes the
    * original exit without changing the SPC registers, timers, or DSP. */
   uint8_t opcode = m.ram.ram[m.cpu_regs.pc];
   if (end_time <= m.spc_time ||
       (!allow_time_overflow && end_time - m.spc_time < m.cycle_table[opcode]))
      return &m.smp_regs[0][R_CPUIO0];
'''


def generate(core, mode):
    if mode == 'apu-service':
        for component in ('apu-clock', 'apu-carry', 'apu-unity'):
            generate(core, component)
        return
    path = core / 'source/apu_blargg.c'
    source = path.read_text()
    execute = '   spc_end_frame(S9X_APU_GET_CLOCK(CPU.Cycles));\n\n   spc_remainder = S9X_APU_GET_CLOCK_REMAINDER(CPU.Cycles);'
    interpreter = 'static uint8_t* spc_run_until_( int32_t end_time )\n{\n'
    if mode == 'apu-clock':
        # Preserve the original uint32_t numerator, including fallback tempo.
        source = replace_once(source, execute, '''   uint32_t numerator = ratio_numerator * (CPU.Cycles - reference_time) + spc_remainder;
   uint32_t elapsed;
   if (ratio_denominator == APU_DENOMINATOR_NTSC)
      elapsed = numerator / APU_DENOMINATOR_NTSC;
   else if (ratio_denominator == APU_DENOMINATOR_PAL)
      elapsed = numerator / APU_DENOMINATOR_PAL;
   else
      elapsed = numerator / ratio_denominator;
   spc_end_frame(elapsed);
   spc_remainder = numerator - elapsed * ratio_denominator;''')
    elif mode == 'apu-noop':
        source = replace_once(source, interpreter, interpreter + NOOP_GUARD)
    elif mode in ('apu-port-noop', 'apu-port-noop-census'):
        guard = NOOP_GUARD
        probe = ''
        count = ''
        if mode.endswith('-census'):
            probe = CENSUS.replace('d35_apu_', 'd35_port_')
            guard = replace_once(guard, '      return &m.smp_regs[0][R_CPUIO0];',
                                 '   {\n      ++d35_port_counts[1];\n      return &m.smp_regs[0][R_CPUIO0];\n   }')
            count = '   ++d35_port_counts[0];\n'
            link = core / 'link.T'
            link.write_text(replace_once(link.read_text(), 'retro_*;', 'retro_*; d35_port_census;'), newline='\n')
        anchor = '/* Emulated port read at specified time */'
        source = replace_once(source, anchor, probe + '''
static INLINE uint8_t *spc_sync_port(int32_t end_time)
{
''' + count + guard + '   return spc_run_until_(end_time);\n}\n\n' + anchor)
        source = replace_once(source, 'spc_run_until_(S9X_APU_GET_CLOCK(CPU.Cycles))[port]',
                              'spc_sync_port(S9X_APU_GET_CLOCK(CPU.Cycles))[port]')
        source = replace_once(source, 'spc_run_until_( S9X_APU_GET_CLOCK(CPU.Cycles) ) [0x10 + port]',
                              'spc_sync_port(S9X_APU_GET_CLOCK(CPU.Cycles))[0x10 + port]')
    elif mode == 'apu-carry':
        # The output spill only feeds spc_set_output, which follows finalization.
        # Preserve the previous path when the front end requests SoundSync.
        marker = '   /* Save any extra samples beyond what should be generated */'
        start = source.index(marker)
        end = source.index('\n}\n', start)
        spill = source[start:end]
        source = source[:start] + '   if (Settings.SoundSync)\n      spc_capture_output_tail();' + source[end:]
        anchor = 'static void spc_end_frame( int32_t end_time )'
        source = replace_once(source, anchor, 'static void spc_capture_output_tail(void)\n{\n' + spill + '\n}\n\n' + anchor)
        finalize = 'void S9xFinalizeSamples(void)\n{\n'
        source = replace_once(source, finalize, finalize + '   if (!Settings.SoundSync)\n      spc_capture_output_tail();\n')
    elif mode in ('apu-unity', 'apu-unity-census'):
        finalize = 'void S9xFinalizeSamples(void)\n{\n'
        source = replace_once(source, finalize, '''/* Unity-rate PCM with an empty ring would be written and read straight
 * through. Copy directly into the existing libretro-owned output buffer. */
bool S9xFinalizeUnitySamples(int16_t *out, size_t capacity, size_t *written)
{
   int32_t count = SPC_SAMPLE_COUNT();
   if (Settings.SoundSync || r_step != 65536 || rb_size || lag ||
       !rb_buffer || count < 0 || count > MAX_WRITE() || (size_t)count > capacity)
      return false;

   if (count)
      memcpy(out, landing_buffer, (size_t)count * sizeof(*out));
   rb_start += count * (int32_t)sizeof(*out);
   if (rb_start >= rb_buffer_size)
      rb_start -= rb_buffer_size;
   sound_in_sync = true;
   m.extra_clocks &= CLOCKS_PER_SAMPLE - 1;
   spc_set_output(landing_buffer, buffer_size);
   *written = count;
   return true;
}

''' + finalize)
        if 'static void spc_capture_output_tail(void)' in source:
            # The unity path bypasses normal finalization. Retire its pending
            # spill at the same boundary, before resetting the DSP destination.
            source = replace_once(source, '   sound_in_sync = true;\n   m.extra_clocks &= CLOCKS_PER_SAMPLE - 1;\n',
                                  '   sound_in_sync = true;\n   spc_capture_output_tail();\n   m.extra_clocks &= CLOCKS_PER_SAMPLE - 1;\n')
        header = core / 'source/apu_blargg.h'
        header.write_text(replace_once(header.read_text(), 'void    S9xFinalizeSamples();',
                                       'void    S9xFinalizeSamples();\nbool    S9xFinalizeUnitySamples(int16_t *out, size_t capacity, size_t *written);'), newline='\n')
        retro = core / 'libretro.c'
        r = retro.read_text()
        a = r.index('   S9xFinalizeSamples();\n')
        b = r.index('   audio_out_buffer_pos += available_samples;', a)
        fallback = r[a:b]
        r = r[:a] + '''   if (!S9xFinalizeUnitySamples(audio_out_buffer + audio_out_buffer_pos,
                                buffer_capacity, &available_samples))
   {
''' + '\n'.join('   ' + line if line else '' for line in fallback.rstrip().split('\n')) + '\n   }\n' + r[b:]
        retro.write_text(r, newline='\n')
        if mode == 'apu-unity-census':
            probe = CENSUS.replace('d35_apu_', 'd35_unity_')
            source = replace_once(source, 'bool S9xFinalizeUnitySamples(', probe + '\nbool S9xFinalizeUnitySamples(')
            source = replace_once(source, '   int32_t count = SPC_SAMPLE_COUNT();',
                                  '   ++d35_unity_counts[0];\n   int32_t count = SPC_SAMPLE_COUNT();')
            source = replace_once(source, '   *written = count;',
                                  '   ++d35_unity_counts[1];\n   d35_unity_counts[2] += count;\n   *written = count;')
            link = core / 'link.T'
            link.write_text(replace_once(link.read_text(), 'retro_*;', 'retro_*; d35_unity_census;'), newline='\n')
    elif mode == 'apu-port-all':
        source = replace_once(source, '   if(d35_complete_port_writes)allow_time_overflow=true;',
                              '   allow_time_overflow = true;')
    elif mode == 'apu-census':
        source = replace_once(source, interpreter, CENSUS + '\n' + interpreter + '''   ++d35_apu_counts[1];
   if (end_time <= m.spc_time || (!allow_time_overflow &&
       end_time - m.spc_time < m.cycle_table[m.ram.ram[m.cpu_regs.pc]]))
      ++d35_apu_counts[2];
''')
        source = replace_once(source, execute, '   ++d35_apu_counts[0];\n' + execute)
        source = replace_once(source, '   m.spc_time     -= end_time;', '   ++d35_apu_counts[3];\n   m.spc_time     -= end_time;')
        source = replace_once(source, 'uint8_t S9xAPUReadPort (int32_t port)\t{ return',
                              'uint8_t S9xAPUReadPort (int32_t port)\t{ ++d35_apu_counts[4]; return')
        source = replace_once(source, '   bool previous_overflow=allow_time_overflow;',
                              '   ++d35_apu_counts[5];\n   bool previous_overflow=allow_time_overflow;')
        source = replace_once(source, '   if (SPC_SAMPLE_COUNT() >= APU_MINIMUM_SAMPLE_BLOCK || !sound_in_sync)\n      sa_callback();',
                              '   if (SPC_SAMPLE_COUNT() >= APU_MINIMUM_SAMPLE_BLOCK || !sound_in_sync) {\n      ++d35_apu_counts[6];\n      sa_callback();\n   }')
        link = core / 'link.T'
        link.write_text(replace_once(link.read_text(), 'retro_*;', 'retro_*; d35_apu_census;'), newline='\n')
    elif mode.startswith('apu-slice'):
        limit = int(mode.removeprefix('apu-slice'))
        if limit not in (2, 4, 8):
            raise ValueError(mode)
        source = replace_once(source, '/* Emulated port read at specified time */', '''/* Host scheduling only. Retire accumulated SPC time at every observable
 * boundary. The saved CPU clock reference is still advanced per scanline. */
static int32_t pending_apu_clocks;
static unsigned pending_apu_lines;

void S9xAPUFlushPending(void)
{
   if (!pending_apu_lines)
      return;
   spc_end_frame(pending_apu_clocks);
   pending_apu_clocks = 0;
   pending_apu_lines = 0;
}

/* Emulated port read at specified time */''')
        source = replace_once(source, 'uint8_t S9xAPUReadPort (int32_t port)\t{ return ((uint8_t) spc_run_until_(S9X_APU_GET_CLOCK(CPU.Cycles))[port]); }',
                              '''uint8_t S9xAPUReadPort (int32_t port)
{
   S9xAPUFlushPending();
   return spc_run_until_(S9X_APU_GET_CLOCK(CPU.Cycles))[port];
}''')
        source = replace_once(source, '   bool previous_overflow=allow_time_overflow;',
                              '   S9xAPUFlushPending();\n   bool previous_overflow=allow_time_overflow;')
        source = replace_once(source, execute, '''   pending_apu_clocks += S9X_APU_GET_CLOCK(CPU.Cycles);
   ++pending_apu_lines;
   spc_remainder = S9X_APU_GET_CLOCK_REMAINDER(CPU.Cycles);''')
        source = replace_once(source, '   if (SPC_SAMPLE_COUNT() >= APU_MINIMUM_SAMPLE_BLOCK || !sound_in_sync)\n      sa_callback();', f'''   bool publish = (((m.extra_clocks + pending_apu_clocks) >> 5) * 2 >= APU_MINIMUM_SAMPLE_BLOCK) || !sound_in_sync;
   if (publish || pending_apu_lines >= {limit} || allow_time_overflow)
      S9xAPUFlushPending();
   if (publish)
      sa_callback();''')
        # Reset discards derived pending state. Normal libretro callers see a
        # fully retired interval at the return boundary, including saves.
        for name in ('S9xResetAPU', 'S9xSoftResetAPU'):
            anchor = f'void {name}()\n{{\n'
            source = replace_once(source, anchor, anchor + '   pending_apu_clocks = 0;\n   pending_apu_lines = 0;\n')
        header = core / 'source/apu_blargg.h'
        header.write_text(replace_once(header.read_text(), 'void    S9xAPUExecute();',
                                       'void    S9xAPUExecute();\nvoid    S9xAPUFlushPending(void);'), newline='\n')
        retro = core / 'libretro.c'
        retro.write_text(replace_once(retro.read_text(), '   S9xMainLoop();\n',
                                      '   S9xMainLoop();\n   S9xAPUFlushPending();\n'), newline='\n')
    else:
        raise ValueError(mode)
    path.write_text(source, newline='\n')


if __name__ == '__main__':
    import sys
    generate(Path(sys.argv[1]), sys.argv[2])
