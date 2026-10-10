"""Reproduce the bounded 1.19 review; keep ROM/disassembly/census inputs private."""
from pathlib import Path
from hashlib import sha256
from statistics import mean
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def analyze():
    session = ROOT / 'evidence/2026-10-10/snes-mvp-1.19-return/session-failure.txt'
    census = ROOT / 'build/magitek-lazy-candidate-private/census.txt'
    script = ROOT / 'build/ff6-disasm/src/btlgfx/attack_anim_script.asm'
    assert digest(session) == '146bbe7f95adca2c22430b432bcf134f5e5fa66f798c514071b58f2ba1cdb78b'
    assert digest(census) == 'aa66d3d48f97e2c3c83c3277ec5e0d402aabd922eeeee722e461789f886afe55'
    assert digest(script) == '54f843b3a808826ab3f6188e4f5782f36bb6a536b5293bd4a4549612976fa546'
    commit = subprocess.check_output(['git', '-C', str(ROOT / 'build/ff6-disasm'),
                                      'rev-parse', 'HEAD'], text=True).strip()
    assert commit == '813013276c952fdd27edcf7b8b86f17291542cbf'
    fields = dict(line.split('=', 1) for line in session.read_text().splitlines() if '=' in line)
    samples = [list(map(int, value.split(','))) for name, value in fields.items()
               if re.fullmatch(r'sample_cost_\d+', name)]
    rows = [list(map(int, line.split()[2:])) for line in census.read_text().splitlines()
            if line.startswith('CENSUS frame=')]
    assert len(rows) == 1200
    labels = json.loads((ROOT / 'build/render-census-bio-lazy/fields.json').read_text())
    names = ('ppu_updates', 'bg_0_lines', 'bg_1_lines', 'bg_2_lines', 'tile_decodes',
             'full_plain_rows', 'full_add_rows', 'clipped_plain_rows', 'clipped_add_rows',
             'neon_row_calls', 'neon_row_empty', 'neon_row_depth_rejected',
             'color_row_materializations', 'color_row_reuses')
    metrics = {}
    for name in names:
        column = next(int(key) for key, value in labels.items() if value == name)
        metrics[name] = {'pre_effect_mean': mean(row[column] for row in rows[225:260]),
                         'effect_mean': mean(row[column] for row in rows[277:439])}
    # The audited sources contain no host-clock delay calls. This is a narrow
    # source check, not proof of every emulation or driver scheduling path.
    audited = ['libretro.c', 'source/cpuexec.c', 'source/gfx.c', 'source/apu.c']
    for name in audited:
        source = (ROOT / 'build/snes9x2005' / name).read_text(encoding='utf-8', errors='replace')
        assert not re.search(r'\b(?:sleep|usleep|nanosleep|clock_gettime)\s*\(', source), name
    cpu = (ROOT / 'build/snes9x2005/source/cpuexec.c').read_text(encoding='utf-8', errors='replace')
    assert re.search(r'case\s+HBLANK_END_EVENT\s*:.*?S9xAPUExecute\s*\(', cpu, re.S)
    actual = int(fields['native_audio_frames']) / int(fields['runs'])
    expected = int(fields['native_rate']) / float(fields['fps'])
    return {
        'version': '1.19 evidence review', 'returned_session': fields['session_id'],
        'session_sha256': digest(session),
        'game_reference': {'repository': 'https://github.com/everything8215/ff6',
                           'commit': commit, 'script_sha256': digest(script),
                           'bio_blast_bg1': 'horizontal and vertical HDMA scroll waves, expanding circle, repeated frame updates and palette fade'},
        'game_delay_hypothesis': {
            'native_audio_frames_per_core_call': actual,
            'expected_rate_divided_by_fps': expected, 'ratio': actual / expected,
            'core_source': 'S9xDoHBlankProcessing_NoSFX calls S9xAPUExecute on each HBLANK_END_EVENT; no host sleep found in audited libretro/CPU/PPU/APU source files',
            'limit': 'Static scheduling and near-normal sample count weaken an intentional audio-generation pause. They do not establish every core sync path or driver behavior.'},
        'private_replay_work_comparison': {
            'pre_effect_indices': [225, 259], 'effect_indices': [277, 438],
            'index_convention': 'zero-based inclusive census row indices',
            'metrics': metrics, 'census_sha256': digest(census),
            'limit': 'Same existing1200-frame private Narshe-derived replay; not exact physical encounter. Work amplification, not A7 timing attribution.'},
        'physical_phase_samples': {
            'columns': fields['frame_cost_columns'], 'rows': samples,
            'last_sample_run': samples[-1][0], 'failed_run': int(fields['runs']),
            'limit': 'Inclusive measurements contain timers and callbacks; final24 calls unsampled. PPU/APU/callback regions must not be added as independent costs.'},
        'causal_ranking': [
            'repeated background rendering/composition from HDMA wave and raster-state updates',
            'other main-core or frontend work and single-CPU scheduling competition remain possible',
            'deliberate host-clock pause with missing audio is weakened by CPU-heavy final calls and normal native samples per call',
            'exact vendor pointer advance/SETUP transition remains unidentified'],
        'next_probe': 'Unchanged1.19 core plus runner-only adaptive phase/callback CPU capture; no recoloring, frame suppression or PCM policy change.'}


if __name__ == '__main__':
    result = analyze()
    output = ROOT / 'build/snes-focus-out/budget-review.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'review': result['version'], 'delay_hypothesis_ratio': result['game_delay_hypothesis']['ratio'],
                      'physical_attribution': 'pending focused capture'}, indent=2))
