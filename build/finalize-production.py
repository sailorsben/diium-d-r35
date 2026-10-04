from pathlib import Path
from hashlib import sha256
import json

root = Path(__file__).resolve().parent.parent
package = root / 'SNES-Plus-v11-production'
result_path = package / 'card-D-installation-verification.json'
result = json.loads(result_path.read_text())
assert sha256(Path('D:/retro/libs/emu_sfc.so').read_bytes()).hexdigest() == result['adapter_sha256']
assert not Path('D:/retro/emu_sfc_plus_v10_audio_priority.txt').exists()
assert not list((root / 'build/production/verification').rglob('*.s16le'))
result['cleanup'] = {
    'v10_handheld_report': 'verified archived on PC, removed from card',
    'temporary_pc_pcm': 'removed after recording equality hashes',
    'v9_handheld_report': 'retained; prior automatic approval review rejected removal, no workaround attempted',
}
result['changed_contents_after_cleanup'] = ['retro/libs/emu_sfc.so', 'retro/emu_sfc_plus_v10_audio_priority.txt (removed after verified archive)']
result_path.write_text(json.dumps(result, indent=2) + '\n')
proof_path = package / 'verification.json'
proof = json.loads(proof_path.read_text())
proof['raw_test_pcm_cleanup'] = 'complete'
proof_path.write_text(json.dumps(proof, indent=2) + '\n')
return_path = Path((root / 'build/v10-return-path.txt').read_text().strip())
analysis = json.loads((return_path / 'analysis.json').read_text())
findings = f'''Successful handheld test and production cleanup

User: no clicks noticed during the intro into Narshe and the wind scenes;
no obvious dropped frames noticed. This is evidence for these tested scenes,
not a guarantee for every game or every later FF6 scene.

Returned v10 report: {analysis['core_frames']} core steps, {analysis['drawn_frames']}
drawn pictures and {analysis['held_frames']} held pictures ({analysis['held_percent']} percent).
Audio produced: {analysis['produced_audio_seconds']:.3f} seconds.
The 14 measured heavy two-second bins produced {analysis['heavy_bins_audio_seconds']:.3f}
seconds of audio over {analysis['heavy_bins_wall_seconds']:.3f} seconds. Each bin
omits one inter-bin gap; interpret throughput approximately. The long final
aggregate includes a 3.7165-second pause, so it is not an uninterrupted-play
throughput measurement. OSS queue readings are not hardware underrun counts.

This supports rendering-dependent audio starvation on the handheld rather
than a damaged FF6 ROM. Host rendering cost is not evidence of a corresponding
slowdown on original SNES hardware. The fix preserves each emulated game step
and audio output while omitting some rendered pictures in expensive scenes.

v11 retains the exact v10 cost-estimation and skip-selection mathematics.
It removes automatic report bins/writes, OSS queries and callback timing.
It retains the two clock reads per core step required by the scheduler.
ARM checks: 4200 emulated frames with all draws versus half draws, exact PCM
and audio callback equality, matching the original v10 comparison hashes;
real save-state serialization/restoration and video geometry checks passed.
The production adapter still awaits a handheld confirmation after cleanup.

Only the SNES adapter was replaced. Current SNES saves were backed up first.
ROMs, core, launcher and saves were verified unchanged. The v10 report was
verified archived and removed; temporary PC PCM files were removed. The older
v9 report remains because its removal was previously rejected by automatic
approval review with the reason blocked by policy. No workaround was attempted.

Report archive: {return_path}
Installation backup: {result['backup']}
'''
(package / 'findings.txt').write_text(findings)
old_findings = root / 'SNES-Plus-v10-audio-priority/findings.txt'
text = old_findings.read_text()
start = text.index('This candidate has not yet been verified on the handheld.')
end = text.index('v10 replaced only', start)
text = text[:start] + '''The returned v10 test is now successful: the user noticed no clicks during
the intro into Narshe and wind scenes. The log held pictures on 5.012 percent
of core steps overall, and measured heavy intervals produced approximately
as much audio as elapsed time. The final aggregate includes user pauses.
The v11 production package preserves the adaptive mathematics and removes
automatic diagnostics. See SNES-Plus-v11-production/findings.txt for results.

''' + text[end:]
old_findings.write_text(text)
print(json.dumps(result, indent=2))
