"""Verify the ROM-to-register trace and isolated window experiment; no device writes."""
from hashlib import sha256
from pathlib import Path
from statistics import mean
import json
import re
import zlib

ROOT = Path(__file__).resolve().parent.parent
TRACE = ROOT / 'build/ff6-cause-private'
WINDOW = ROOT / 'build/ff6-window-batch-private'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def protocol(path):
    return [line for line in path.read_text().splitlines()
            if line.startswith(('READY:', 'advanced='))]


def census(path):
    rows = []
    for line in path.read_text().splitlines():
        fields = line.split()
        assert fields[:1] == ['CENSUS'] and fields[1] == f'frame={len(rows)+1}'
        row = list(map(int, fields[2:])); assert len(row) == 128
        rows.append(row)
    assert len(rows) == 1200
    return rows


def analyze():
    owner = ROOT / 'build/plus-a7-out/ff6.sfc'
    rebuilt = ROOT / 'build/ff6-disasm/build/en/rom/ff6-en.sfc'
    assert owner.read_bytes() == rebuilt.read_bytes()
    assert len(owner.read_bytes()) == 3145728 and zlib.crc32(owner.read_bytes()) & 0xffffffff == 0xa27f1c7a
    lift = json.loads((TRACE / 'c-map/verification.json').read_text())
    assert lift['rebuilt_rom_byte_equal'] and lift['owner_rom_sha256'] == digest(owner)
    assert lift['native_instruction_addresses_lifted'] == 103538
    for name, wanted in lift['generated_c_sha256'].items():
        assert digest(TRACE / 'c-map' / name) == wanted, name
    assert (WINDOW / 'c-map-syntax.log').read_text().startswith('PASS:')
    # The traced core used this exact independent wave model.
    assert (ROOT / 'build/ff6-bio-blast-model.h').read_bytes() == (TRACE / 'core/source/bio-blast-model.h').read_bytes()
    baseline = ROOT / 'build/magitek-lazy-candidate-private'
    expected = protocol(baseline / 'replay.log')
    assert len(expected) == 5 and expected[-1].startswith('advanced=1164 total=1200 ')
    assert protocol(TRACE / 'replay/trace.log') == protocol(WINDOW / 'replay.log') == expected
    trace_text = (TRACE / 'replay/trace.log').read_text()
    checks = [tuple(map(int, item)) for item in re.findall(r'wave_checks=(\d+) wave_bad=(\d+)', trace_text)]
    assert checks and max(row[0] for row in checks) == 178 and not any(row[1] for row in checks)
    registers = {}
    for address, writes, changes, flushes in re.findall(
            r'REG frame=320 address=([0-9a-f]+) writes=(\d+) byte_changes=(\d+) rendered_flushes=(\d+)', trace_text):
        registers[address] = dict(zip(('writes', 'byte_changes', 'rendered_flushes'), map(int, (writes, changes, flushes))))
    assert registers['210d']['rendered_flushes'] == registers['210e']['rendered_flushes'] == 0
    assert registers['2128']['rendered_flushes'] + registers['2129']['rendered_flushes'] == 123
    a = census(baseline / 'census.txt'); b = census(WINDOW / 'census.txt')
    names = json.loads((ROOT / 'build/render-census-window-batch-private/fields.json').read_text())
    effect_a, effect_b = a[277:439], b[277:439]
    changed = [column for column in range(128)
               if any(x[column] != y[column] for x, y in zip(effect_a, effect_b))]
    assert changed == [0, 46, 47, 105, 108], changed
    metrics = {}
    for column in (0, 46, 47):
        old = mean(row[column] for row in effect_a); new = mean(row[column] for row in effect_b)
        metrics[names[str(column)]] = {'baseline_mean': old, 'candidate_mean': new,
                                      'change_percent': 100 * (new / old - 1)}
    for name, frames in (('equivalence-bio.log', 1200), ('equivalence-general.log', 2400)):
        log = (WINDOW / name).read_text()
        assert f'PASS: {frames} frames' in log and 'periodic state' in log and 'FAIL' not in log
    oracle = (WINDOW / 'window-check.log').read_text()
    assert 'PASS: 524288 window states' in oracle and 'fallback guards' in oracle
    assert (ROOT / 'build/plus-a7-window.h').read_bytes() == (
        ROOT / 'build/render-census-window-batch-private/core/source/a7_window.h').read_bytes()
    shipping = json.loads((ROOT / 'releases/snes-mvp-1.19/manifest.json').read_text())
    assert digest(ROOT / 'build/plus-a7-out/plus-a7.so') == shipping['core_sha256']
    source_names = ['analyze-ff6-cause.py', 'lift-ff6-code.py', 'ff6-python-private.sh',
                    'ff6-bio-blast.c', 'ff6-bio-blast-model.h', 'ff6-cause-trace.c',
                    'prepare-ff6-cause.py', 'check-ff6-cause.sh', 'prepare-window-batch.py',
                    'plus-a7-window.h', 'plus-a7-window-check.c', 'check-window-oracle.sh',
                    'prepare-render-census.py', 'check-render-census.sh', 'plus-a7-equivalence.c']
    input_names = ['build/ff6-cause-private/replay/trace.log', 'build/ff6-window-batch-private/census.txt',
                   'build/magitek-lazy-candidate-private/census.txt', 'build/ff6-window-batch-private/replay.log',
                   'build/ff6-window-batch-private/equivalence-bio.log',
                   'build/ff6-window-batch-private/equivalence-general.log',
                   'build/ff6-window-batch-private/window-check.log',
                   'build/ff6-window-batch-private/c-map-syntax.log']
    result = {
        'passed': True, 'experiment': 'ROM-derived BG1 window batching; separate private core',
        'hardware_qualified': False, 'installed_on_card': False,
        'owner_rom_byte_matched': True, 'rom_crc32': 'a27f1c7a',
        'assembly_repository': 'https://github.com/everything8215/ff6',
        'assembly_commit': '813013276c952fdd27edcf7b8b86f17291542cbf',
        'cc65_commit': '555282497c3ecf8b313d87d5973093af19c35bd5',
        'c_map_instruction_addresses': 103538, 'c_map_banks': 8,
        'wave_model_checks': 178, 'wave_model_mismatches': 0,
        'frame_320_registers': {name: registers[name] for name in ('210d', '210e', '2128', '2129', '2132')},
        'effect_range': {'zero_based_inclusive_census_indices': [277, 438], 'frames': 162},
        'metrics': metrics, 'unchanged_effect_counters': 123,
        'counter_limit': 'flush_before_2129 is recorded before the new deferral condition and is not an actual-flush count. ppu_updates counts actual S9xUpdateScreen entries.',
        'clip_oracle_states': 524288, 'clip_oracle_reference': 'unchanged source/clip.c ComputeClipWindows',
        'equivalence_frames': 3600,
        'equivalence_method': 'per-frame visible RGB565 and native PCM CRC32; sample counts/geometry; byte-comparison of normalized serialized state every30 frames',
        'replay_protocol_identical': True,
        'shipping_1_19_core_unchanged': True,
        'candidate_core_sha256': digest(ROOT / 'build/render-census-window-batch-private/core/snes9x2005_plus_libretro.so'),
        'candidate_instrumented': True,
        'next_step': 'Read the armed unchanged-core focus result; assess a separate production-core candidate and its actual A7 costs before installation.',
        'limits': ['This C map is not original C or a runnable native game. RAM overlays, SPC code and game data are not broadly lifted.',
                   'The private derived battle is not the exact physical encounter. These are emulation correctness and work counts, not hardware speed or audio acceptance.',
                   'Color-row materializations rise34.58%; reduced renderer entry counts alone do not prove a net CPU improvement.',
                   'Frame-end display masks in the behavior trace are blanking-time values and are not active scanline-state evidence.'],
        'source_hashes': {'build/' + name: digest(ROOT / 'build' / name) for name in source_names},
        'private_input_hashes': {name: digest(ROOT / name) for name in input_names}}
    (WINDOW / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    value = analyze()
    print(json.dumps({name: value[name] for name in ('passed', 'wave_model_checks', 'metrics', 'equivalence_frames', 'installed_on_card')}, indent=2))
