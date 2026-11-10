"""Publish compact replay and timing evidence for the shared APU experiments."""
from importlib import import_module
import json
from pathlib import Path
import sys


throughput = import_module('report-snes-throughput')
FIX = Path(__file__).resolve().parent/'fivegame-kernel-private-v2'


def qualification(path):
    result = throughput.replay(path/'scheduler-verify')
    reference = {r['game']:r for r in result['results'] if r['core']=='physical'}
    assert len(reference)==5 and all(r['verified']==1200 for r in reference.values())
    for row in result['results']:
        baseline = reference[row['game']]
        row['callback_layout_matches'] = row['callback_layout_crc32']==baseline['callback_layout_crc32']
        assert row['rendered']==baseline['rendered']==1200
        assert row['audio_frames']==baseline['audio_frames']
        for key in ('cold_cpu_ns','game_cpu_mean_ns','game_cpu_p95_ns','game_cpu_first_four_ns'):
            del row[key]
    return result


def main(first, carry, unity, comparison, fixed, port, pairs, more_pairs, fixed_pairs, port_pairs,
         states, unity_states, output):
    qualified = {name:qualification(folder) for name,folder in (
        ('isolated',first),('carry',carry),('unity',unity),('timing_ablations_and_first_combination',comparison),
        ('final_combination',fixed),('port_only',port))}
    expected_passes = {'apu-clock','apu-noop','apu-carry','apu-census','apu-unity','apu-unity-census',
                       'apu-port-noop','apu-port-noop-census'}
    for group in qualified.values():
        for row in group['results']:
            if row['core'] in expected_passes:
                assert row['verified']==1200 and row['callback_layout_matches'], row
    final = [r for r in qualified['final_combination']['results'] if r['core']=='apu-service']
    assert len(final)==5 and all(r['verified']==1200 and r['callback_layout_matches'] for r in final)
    assert throughput.elf_text(first/'baseline/snes9x2005_plus_libretro.so')==throughput.elf_text(FIX/'plus-a7.so')
    timing = {name:throughput.paired(path) for name,path in (
        ('isolated',pairs),('unity_and_controls',more_pairs),('final_combination',fixed_pairs),('port_only',port_pairs))}
    # The initial combination changed PCM. Keep the correctness trace while
    # omitting its throughput from the comparison of equivalent candidates.
    timing['unity_and_controls']['results'] = [r for r in timing['unity_and_controls']['results'] if r['candidate']!='apu-service']
    timing['unity_and_controls']['meta']['results'] = [r for r in timing['unity_and_controls']['meta']['results'] if r['candidate']!='apu-service']
    state_checks = {'apu-service':json.loads((states/'checks.json').read_text()),
                    'apu-unity':json.loads((unity_states/'checks.json').read_text())}
    assert state_checks['apu-service']['core_sha256']==qualified['final_combination']['meta']['core_sha256']['apu-service']
    assert state_checks['apu-unity']['core_sha256']==qualified['unity']['meta']['core_sha256']['apu-unity']
    output.write_text(json.dumps({'physical':False,'core_qualification':qualified,'paired_cpu_time':timing,
                                  'held_out_state_checks':state_checks,'baseline_executable_text_matches_returned_core':True},indent=2)+'\n')


if __name__=='__main__':
    main(*(Path(arg).resolve() for arg in sys.argv[1:]))
