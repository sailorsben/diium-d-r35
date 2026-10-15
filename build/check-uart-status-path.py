"""Confirm captured default-path behavior in actual archived ARM instructions."""
from pathlib import Path
from hashlib import sha256
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'build/uart-status-private'


def main():
    kernel = ROOT / 'device-evidence/uart-kernel-offline/kernel.bin'
    digest = lambda p: sha256(p.read_bytes()).hexdigest()
    assert digest(kernel) == '21cc93e3f621c410ebe4174c0ab00aa4f0b21887c1698bbe974ffbeead2f0321'
    tool = ['wsl', '--exec'] if os.name == 'nt' else []
    binary = 'build/uart-status-private/check-status-path'
    subprocess.run(tool + ['arm-linux-gnueabihf-gcc', '-O2', '-Wall', '-Wextra', '-Werror', '-marm', '-no-pie', '-static',
        'build/check-uart-status-path.c', '-o', binary], cwd=ROOT, check=True, capture_output=True)
    run = subprocess.run(tool + ['qemu-arm', binary, kernel.relative_to(ROOT).as_posix()],
        cwd=ROOT, check=True, capture_output=True, text=True, timeout=30)
    proof = {'kind': 'offline_original_ISR_captured_status_check', 'status': '0x0000531f', 'calls': 1000,
        'IRQ_HANDLED_returns': 1000, 'fixture_RAM_changes': False, 'tty_fixture_calls': 0,
        'original_kernel_sha256': digest(kernel),
        'sources': {p.relative_to(ROOT).as_posix(): digest(p) for p in [Path(__file__).resolve(),
            ROOT / 'build/check-uart-status-path.c', ROOT / 'build/check-uart-kernel.c']},
        'boundary': 'Original ARM instructions against anonymous RAM; no MMIO side effects, electrical causality or A7 duration measured. Control/flags are earlier state1 context, not simultaneous status1 samples.',
        'output': run.stdout.strip()}
    (OUT / 'captured-status-path.json').write_text(json.dumps(proof, indent=2) + '\n')
    print(run.stdout)


if __name__ == '__main__':
    main()
