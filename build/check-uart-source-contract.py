"""Check shared-IP definitions against actual kernel behavior, without hardware."""
from pathlib import Path
from hashlib import sha256, sha1
import json
import os
import re
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = ROOT / 'device-evidence/uart-source-research'
sys.path.insert(0, str(ROOT / 'build/lab2-inspection-tools'))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def main():
    source_records = json.loads((PRIVATE / 'matching-uart-sources.json').read_text())
    for record in source_records:
        raw = (PRIVATE / record['local']).read_bytes()
        assert sha256(raw).hexdigest() == record['sha256']
        assert sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == record['git_blob_sha1']
    for name in ['freexyz-gpl32-drv_l1_uart.h', 'gpm4-drv_l1_uart.h']:
        text = (PRIVATE / name).read_text()
        for macro, value in [('C_UART_STATUS_TX_INT', 0x4000), ('C_UART_STATUS_TX_EMPTY', 0x80),
                ('C_UART_CTRL_TX_INT', 0x4000), ('C_UART_STATUS_RX_EMPTY', 0x10)]:
            match = re.search(r'^#define\s+' + macro + r'\s+(0x[0-9A-Fa-f]+)', text, re.M)
            assert match and int(match[1], 16) == value
    kernel = ROOT / 'device-evidence/uart-kernel-offline/kernel.bin'
    assert digest(kernel) == '21cc93e3f621c410ebe4174c0ab00aa4f0b21887c1698bbe974ffbeead2f0321'
    data = kernel.read_bytes()
    assert struct.unpack_from('<I', data, 0xc0117804 - 0xc0008000)[0] == 0xe3150080
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    assert [(i.mnemonic, i.op_str) for i in cs.disasm(struct.pack('<I', 0xe3150901), 0xc0117804)] == [('tst', 'r5, #0x4000')]
    physical = ROOT / 'evidence/2026-10-14/uart-status/return.json'
    returned = json.loads(physical.read_text())
    statuses = returned['status_histogram']
    assert all(int(v, 16) & 0x4000 for v in statuses)
    assert sum(n['count'] for v, n in statuses.items() if int(v, 16) & 0x80) == 144
    tree_path = ROOT / 'device-evidence/hardware-inventory-return-20261004T180435Z/device-tree.json'
    tree = json.loads(tree_path.read_text())
    assert tree['/soc/uart@C0070000']['interrupts']['decoded'] == ['0x0', '0x25', '0x4']
    tool = ['wsl', '--exec'] if os.name == 'nt' else []
    binary = 'build/uart-status-private/check-source-contract'
    subprocess.run(tool + ['arm-linux-gnueabihf-gcc', '-O2', '-Wall', '-Wextra', '-Werror', '-marm', '-no-pie', '-static',
        'build/check-uart-source-contract.c', '-o', binary], cwd=ROOT, check=True, capture_output=True)
    run = subprocess.run(tool + ['qemu-arm', binary, kernel.relative_to(ROOT).as_posix()], cwd=ROOT,
        check=True, capture_output=True, text=True, timeout=30)
    checks = run.stdout.splitlines()
    assert len(checks) == 6
    public_sources = [{k: v for k, v in r.items() if k != 'local'} for r in source_records]
    report = {'kind': 'UART_shared_IP_and_exact_kernel_contract', 'kernel_sha256': digest(kernel),
        'physical_return_sha256': digest(physical), 'archived_device_tree_sha256': digest(tree_path),
        'external_sources': public_sources, 'shared_IP_TX_pending_bit': '0x4000', 'shared_IP_TX_empty_bit': '0x80',
        'captured_entries_with_TX_pending_bit': returned['frozen']['total'], 'captured_entries_with_TX_empty_bit': 144,
        'checks': checks, 'DT_SPI': 37, 'GIC_hwirq': 69, 'DT_trigger': 'level high',
        'gic_state_getter_address': '0xc0303d5c', 'ordinary_gic_eoi_address': '0xc03033a0',
        'next_read_API_exported': 'irq_get_irqchip_state',
        'exact_GPA7_register_manual_recovered': False, 'simultaneous_status_control_GIC_capture': False,
        'live_causal_suppression_performed': False, 'A7_duration_measured': False, 'card_access': False,
        'production_gate': False,
        'negative_findings': ['GPL32900 and SPMP8050 source layouts are incompatible 16550-like blocks; rejected.',
            'Public G-plus-6662118 kernel/openplatform repositories returned empty-tree HTTP409.',
            'GP32/GPM4 names and offsets agree but do not certify undocumented/reserved GPA7 bits.',
            'Earlier state1 TX enables were clear; a one-word TX-condition change alone is not a proven flood fix.',
            'EOI code exists and executes correctly against RAM; live invocation is not traced here.'],
        'sources': {p.relative_to(ROOT).as_posix(): digest(p) for p in [Path(__file__).resolve(),
            ROOT / 'build/check-uart-source-contract.c', ROOT / 'build/check-uart-kernel.c']}}
    (PRIVATE / 'contract-research.json').write_text(json.dumps(report, indent=2) + '\n')
    print(run.stdout)


if __name__ == '__main__':
    main()
