"""Analyze an archived focus report; no card access or causal sum of overlapping regions."""
from pathlib import Path
from hashlib import sha256
from statistics import mean
import argparse
import json
import re

ROOT = Path(__file__).resolve().parent.parent


def analyze(path):
    raw = path.read_bytes()
    fields = {}
    for line in raw.decode().splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            assert key not in fields, 'Duplicate report field: ' + key
            fields[key] = value
    assert fields['build_version'] == '1.19-focus1' and fields['focus_profile'] == '1'
    expected = json.loads((ROOT / 'releases/snes-mvp-1.19/manifest.json').read_text())
    assert fields['core_crc32'] == expected['core_crc32']
    assert int(fields['core_bytes']) == expected['core_bytes']
    assert fields['frame_cost_columns'] == 'run,epoch,sampled,wall_ns,cpu_ns,apu_inclusive_cpu_ns,ppu_cpu_ns,audio_wall_ns,video_wall_ns,admission_wall_ns'
    assert fields['focus_cost_columns'] == 'run,reason,audio_callback_cpu_ns,video_callback_cpu_ns,audio_callbacks,video_callbacks'

    def table(prefix, columns):
        found = sorted((int(key[len(prefix):]), value) for key, value in fields.items()
                       if re.fullmatch(re.escape(prefix) + r'\d+', key))
        assert [index for index, _ in found] == list(range(len(found)))
        rows = [list(map(int, value.split(','))) for _, value in found]
        assert all(len(row) == columns and all(value >= 0 for value in row) for row in rows)
        return rows

    frames, callbacks = table('frame_cost_', 10), table('focus_cost_', 6)
    assert len(frames) == len(callbacks) == min(64, int(fields['runs']))
    assert [row[0] for row in frames] == list(range(int(fields['runs']) - len(frames) + 1,
                                                 int(fields['runs']) + 1))
    assert [row[0] for row in callbacks] == [row[0] for row in frames]
    for frame, callback in zip(frames, callbacks):
        assert frame[2] in (0, 1) and callback[1] in (0, 1, 2)
        assert bool(frame[2]) == bool(callback[1]), 'Sample selection mismatch'
        if not frame[2]:
            assert callback[1:] == [0] * 5, 'Unsampled callback counters are nonzero'
    rows = [dict(zip(fields['frame_cost_columns'].split(',') +
                     fields['focus_cost_columns'].split(',')[1:], frame + callback[1:]))
            for frame, callback in zip(frames, callbacks)]
    groups = {}
    for label, sampled in [('ordinary', False), ('profiled', True)]:
        selected = [row for row in rows if bool(row['sampled']) == sampled]
        columns = ['wall_ns', 'cpu_ns', 'admission_wall_ns']
        if sampled:
            columns += ['apu_inclusive_cpu_ns', 'ppu_cpu_ns',
                        'audio_callback_cpu_ns', 'video_callback_cpu_ns']
        groups[label] = {'count': len(selected), 'mean_ns': {
            column: mean(row[column] for row in selected) for column in columns} if selected else {}}
    return {'version': fields['build_version'], 'session_id': fields['session_id'],
            'source_sha256': sha256(raw).hexdigest(), 'runs': int(fields['runs']),
            'error': fields['error'], 'backend': fields['audio_backend'],
            'mock_backend': fields['mock_backend'] == '1',
            'budget_ns': 1e9 / float(fields['fps']), 'retained_frame_count': len(rows),
            'sampled_runs': [row['run'] for row in rows if row['sampled']],
            'clock_loop_mean_ns': int(fields['focus_profile_clock_loop_mean_ns']),
            'groups': groups, 'frames': rows,
            'limits': ['Timings include instrumentation; ordinary and profiled calls are different scenes, not controlled overhead pairs.',
                       'APU timing may include audio callback CPU. Do not add these regions as independent costs.',
                       'Unassigned CPU can include SPC port execution and timer costs; it is not pure game CPU.',
                       'Mock/QEMU measurements do not establish physical costs. Validate archived card payload and report identity separately.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('session', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = analyze(args.session)
    text = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.write_text(text, encoding='utf-8')
        print(json.dumps({key: result[key] for key in ('version', 'session_id', 'retained_frame_count', 'sampled_runs', 'mock_backend')}, indent=2))
    else:
        print(text, end='')
