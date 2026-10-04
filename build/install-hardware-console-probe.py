"""Install a reversible one-shot probe without changing any emulator binary."""
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

workspace = Path(__file__).resolve().parent.parent
package = workspace / 'Hardware-Console-v3'
package.mkdir(exist_ok=True)
card = Path('D:/retro')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
critical = ['libs/emu_sfc.so', 'libs/emu_sfc_plus.so', 'vrtemu', 'driver.so']
before = {p: sha(card / p) for p in critical}
original = (card / 'init').read_bytes()
assert b'hardware_probe_v3' not in original
assert not (package / 'installation.json').exists(), 'Already installed; inspect before repeating'
for name in ['hardware_probe_v3', 'hardware_probe_v3.once',
             'hardware_probe_v3.once.started', 'hardware_probe_v3.jsonl', 'hardware_probe_v3.err']:
    assert not (card / name).exists(), f'Preserve existing {name}'
(package / 'init.before').write_bytes(original)
hook = b'''# D35 one-shot passive console and IRQ inventory; removes itself from repeat execution.
if [ -f /usr/retro/hardware_probe_v3.once ]; then
  /usr/retro/hardware_probe_v3 --once /usr/retro/hardware_probe_v3.once /usr/retro/hardware_probe_v3.jsonl > /usr/retro/hardware_probe_v3.err 2>&1 &
fi

'''
anchor = b'# Keep init alive just enough for background to spawn\n'
assert original.count(anchor) == 1
launch = b"  /usr/retro/main &\n"
quiet = b"""  # One boot only: discard frontend userspace console output.
  if [ -f /usr/retro/hardware_probe_v3.once ]; then
    /usr/retro/main > /dev/null 2>&1 &
  else
    /usr/retro/main &
  fi
"""
assert original.count(launch) == 1
candidate = original.replace(launch, quiet).replace(anchor, hook + anchor)
assert candidate.replace(hook, b'').replace(quiet, launch) == original
(package / 'init.with-probe').write_bytes(candidate)
(package / 'init.diff').write_text(''.join(difflib.unified_diff(
    original.decode().splitlines(True), candidate.decode().splitlines(True),
    fromfile='init.before', tofile='init.with-probe')))
shutil.copyfile(workspace / 'build/hardware-console-probe/hardware_probe', package / 'hardware_probe_v3')
shutil.copyfile(workspace / 'build/hardware-console-probe/verification.json', package / 'verification.json')
linuxpkg = '/mnt/c/' + str(package)[3:].replace('\\', '/')
linuxbuild = '/mnt/c/' + str(workspace / 'build')[3:].replace('\\', '/')
subprocess.run(['wsl', '--exec', 'sh', '-n', linuxpkg + '/init.with-probe'], check=True)
shutil.copyfile(Path('H:/DIIUM D-R35/retro/Tests/root_copy/bin/busybox'),
                package / 'validation-busybox')
subprocess.run(['wsl', '--exec', 'qemu-arm', '-0', 'busybox', '-cpu', 'cortex-a7', '-L', linuxbuild + '/sysroot',
                linuxpkg + '/validation-busybox', 'sh', '-n', linuxpkg + '/init.with-probe'], check=True)
# Validation helper is PC-only and can be discarded after successful syntax check.
(package / 'validation-busybox').unlink()
shutil.copyfile(package / 'hardware_probe_v3', card / 'hardware_probe_v3')
assert sha(card / 'hardware_probe_v3') == sha(package / 'hardware_probe_v3')
(card / 'init').write_bytes(candidate)
assert (card / 'init').read_bytes() == candidate
# Arm last, after all validation and readbacks. Program claims marker before collecting.
(card / 'hardware_probe_v3.once').write_bytes(b'one boot only\n')
after = {p: sha(card / p) for p in critical}
assert before == after
manifest = {'init_original_sha256': hashlib.sha256(original).hexdigest(),
            'init_probe_sha256': sha(card / 'init'), 'probe_sha256': sha(card / 'hardware_probe_v3'),
            'critical_before': before, 'critical_after': after,
            'created_card_files': ['hardware_probe_v3', 'hardware_probe_v3.once'],
            'expected_generated_card_files': ['hardware_probe_v3.once.started',
                                             'hardware_probe_v3.jsonl', 'hardware_probe_v3.err'],
            'changed_card_files': ['init'], 'hardware_execution_verified': False}
(package / 'installation.json').write_text(json.dumps(manifest, indent=2))
print(json.dumps(manifest, indent=2))
