"""Inspect archived board/alias/clock contracts, never live GPIO or MMIO."""
from pathlib import Path
from hashlib import sha256
import json
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = ROOT / 'device-evidence/uart-source-research'
sys.path.insert(0, str(ROOT / 'build/lab2-inspection-tools'))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    kernel = ROOT / 'device-evidence/uart-kernel-offline/kernel.bin'
    assert digest(kernel) == '21cc93e3f621c410ebe4174c0ab00aa4f0b21887c1698bbe974ffbeead2f0321'
    data = kernel.read_bytes()
    tree_path = ROOT / 'device-evidence/hardware-inventory-return-20261004T180435Z/device-tree.json'
    tree = json.loads(tree_path.read_text())
    assert tree['/']['model']['decoded'] == ['Generalplus EMU Board']
    assert tree['/aliases']['serial0']['decoded'] == ['/soc/uart@C0070000']
    assert tree['/aliases']['serial1']['decoded'] == ['/soc/uart@C0060000']
    assert tree['/chosen']['stdout-path']['decoded'] == ['serial0:115200n8']
    uart_nodes = {k: v for k, v in tree.items() if k.startswith('/soc/uart@')}
    assert len(uart_nodes) == 3 and all(v['status']['decoded'] == ['okay'] for v in uart_nodes.values())
    pin_properties = {k: [p for p in v if any(s in p.lower() for s in ['pin', 'bias', 'pull'])] for k, v in uart_nodes.items()}
    assert not any(pin_properties.values())
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    def instructions(start, size):
        return list(cs.disasm(data[start - 0xc0008000:start - 0xc0008000 + size], start))
    clk = {i.address: (i.mnemonic, i.op_str) for i in instructions(0xc0117d54, 148)}
    assert clk[0xc0117d68] == ('beq', '#0xc0117dc4')
    assert clk[0xc0117d6c] == ('cmp', 'r4, #0')
    assert clk[0xc0117d70] == ('beq', '#0xc0117da0')
    assert clk[0xc0117da4] == ('movw', 'r0, #0x2db4') and clk[0xc0117da8] == ('movt', 'r0, #0xc059')
    assert clk[0xc0117db0] == ('movw', 'r0, #0x2dbc') and clk[0xc0117db8] == ('movt', 'r0, #0xc059')
    def string(address):
        offset = address - 0xc0008000
        return data[offset:data.index(b'\0', offset)].decode('ascii')
    assert string(0xc0592db4) == 'uart1' and string(0xc0592dbc) == 'uart1_reg'
    assert string(0xc0592da0) == 'uart0' and string(0xc0592da8) == 'uart0_reg'
    assert all(i.op_str == '#0xc01269bc' for i in instructions(0xc0117d54, 148) if i.mnemonic == 'bl')
    get_status = instructions(0xc0117314, 20)
    get_rx_error = instructions(0xc0117328, 20)
    assert get_status[3].op_str == 'r0, [r0, #0x10]' and get_status[3].mnemonic == 'ldr'
    assert get_rx_error[3].op_str == 'r0, [r0, #4]' and get_rx_error[3].mnemonic == 'ldr'
    gic = {i.address: (i.mnemonic, i.op_str) for i in instructions(0xc0303800, 92)}
    assert gic[0xc0303828] == ('cmp', 'r1, #4') and gic[0xc030382c] == ('cmpne', 'r1, #1')
    board_doc = ROOT / 'docs/board-identification.md'
    assert '**VT569B**' in board_doc.read_text()
    report = {'kind': 'offline_UART_board_contract_inspection', 'card_access': False, 'production_gate': False,
        'kernel_sha256': digest(kernel), 'device_tree_sha256': digest(tree_path),
        'board_marking_authority': 'docs/board-identification.md', 'board_marking_authority_sha256': digest(board_doc),
        'physical_marking': 'VT569B', 'device_tree_model': 'Generalplus EMU Board',
        'enabled_UART_nodes': list(uart_nodes), 'UART_node_pin_bias_properties': pin_properties,
        'serial0_physical_block': '0xc0070000', 'serial0_clock_names': ['uart1', 'uart1_reg'],
        'alias_clock_mismatch_observed': False, 'RX_pad_number_or_pull_state_recovered': False,
        'RX_trace_connection_proven': False, 'SPI_trigger_types_accepted_by_code': ['rising edge', 'level high'],
        'checks': ['Three UART nodes available; serial0/serial1 aliases independently checked.',
            'Actual line0 clock-helper branch selects uart1/uart1_reg, matching C0070000 hardware block.',
            'Actual clock helper only directly calls gp_enable_clock; no direct pad/pull call in that helper.',
            'UART DT nodes specify no pin/pull/bias properties; physical pad state remains unknown.',
            'Actual status and RX-error getters read different offsets; low status bits are not RX-error evidence.',
            'Actual GIC SPI type validation admits1/4, not arbitrary low-level polarity settings.'],
        'sources': {Path(__file__).resolve().relative_to(ROOT).as_posix(): digest(Path(__file__).resolve())}}
    (PRIVATE / 'board-contract.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
