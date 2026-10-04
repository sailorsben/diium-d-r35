from pathlib import Path
import json
import sys
import numpy as np

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / 'build/audio-inspection-tools'))
import av

out = root / 'device-evidence/ff3-2010-click-recording'
meta = json.loads((out / 'recording-metadata.json').read_text())
with av.open(str(root / meta['source'])) as container:
    stream = container.streams.audio[0]
    rate = stream.codec_context.sample_rate
    samples = np.concatenate([f.to_ndarray() for f in container.decode(stream)], axis=1)[0].astype(np.float64)
window = rate // 100
windows = samples[:len(samples) // window * window].reshape(-1, window)
level = np.sqrt(np.mean(windows ** 2, axis=1))
exact_silence = np.max(np.abs(windows), axis=1) < 1e-6
silent_windows = np.flatnonzero(exact_silence).tolist()
delta = np.abs(np.diff(samples))
# An AAC microphone recording cannot distinguish music attacks from clicks.
# Report objective measurements only, rather than classifying musical transients.
report = {
    'ten_ms_windows': len(level),
    'exact_silent_ten_ms_windows': int(exact_silence.sum()),
    'silent_window_start_seconds': [i / 100 for i in silent_windows],
    'rms_percentiles': {str(q): float(np.percentile(level, q)) for q in [0, 10, 50, 90, 100]},
    'peak_sample_step': float(delta.max()),
    'sample_step_99_9_percentile': float(np.percentile(delta, 99.9)),
    'conclusion': 'Silent-window locations and sample steps are measured, but these statistics do not establish recurring playback interruptions. AAC priming/padding, shorter interruptions, held/repeated samples, and microphone background noise require separate consideration.',
    'limitation': 'Music attacks and playback clicks cannot be reliably separated by these waveform statistics. No causal diagnosis or claim of listening.',
}
(out / 'waveform-check.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))

comparison = root / 'SNES-2010-comparison'
manifest = json.loads((comparison / 'manifest.json').read_text())
manifest['verification']['handheld_performance_and_clicking'] = 'User reports: Clicks like crazy. Headphones or not. Comparison unsuccessful; clean Plus restored.'
manifest['current_card_status'] = json.loads((comparison / 'restoration.json').read_text())
(comparison / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
install = json.loads((comparison / 'card-D-installation-verification.json').read_text())
install['handheld_result'] = 'User reports: Clicks like crazy. Headphones or not.'
install['subsequent_restoration'] = manifest['current_card_status']
(comparison / 'card-D-installation-verification.json').write_text(json.dumps(install, indent=2) + '\n')
