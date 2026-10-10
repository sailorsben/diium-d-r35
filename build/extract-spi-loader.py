"""Recover bounded loader contracts from the exact private SPI readback.

Only interpreted offsets/metadata are emitted. No vendor disassembly, bitmap,
image, device I/O or vendor-code execution.
"""
from pathlib import Path
from hashlib import sha256
import argparse, json, struct

EXPECTED = '5c4ea86ca5c497a26136ee9a59d8a31085e15c8d1dc5f063b874a20c400d9e2b'


def extract(path):
    data = path.read_bytes()
    assert len(data) == 8388608 and sha256(data).hexdigest() == EXPECTED
    word = lambda offset: struct.unpack_from('<I', data, offset)[0]
    half = lambda offset: struct.unpack_from('<H', data, offset)[0]
    assert word(0x220) == 0x02600040 and word(0x308) == 0x026051ed
    assert half(0x54c0) == 0x4b58 and half(0x54c4) == 0x4a58 and half(0x54ca) == 0x601a
    assert word(0x5624) == 0xd05001e0 and word(0x5628) == 0x02608654
    assert half(0x54ea) == 0x4b51 and half(0x54f0) == 0x4a50 and half(0x54f6) == 0x601a
    assert word(0x5630) == 0xd05002e4 and word(0x5634) == 0x01e00280
    assert word(0x64a8) == 0x47f0e92d and word(0x5a1c) == 0x4ff0e92d
    assert data[0xb0000:0xb0004] == b'GPAP'
    boot_bytes = struct.unpack_from('<H', data, 0x10)[0] * 512
    app_header = (boot_bytes+0x10000+0x1ff)&~0xffff
    assert boot_bytes == 0xa2200 and app_header == 0xb0000
    return {'version': 1, 'image_sha256': EXPECTED, 'image_bytes': len(data),
        'instruction_set': 'ARM entry vectors; Thumb boot main and section-table routines',
        'flash_to_ram_bias': '0x025ffe00', 'boot_main': 'flash0x53ec / RAM0x026051ed Thumb',
        'static_splash_reference': {'bitmap_flash_offset': '0x8854', 'bitmap_bytes': 614400,
            'bitmap_ram_pointer': '0x02608654', 'pointer_literal_flash_offset': '0x5628',
            'pointer_store_instruction': 'Thumb flash0x54ca: str r2,[r3]',
            'pointer_register_address': '0xd05001e0',
            'dimensions_store_instruction': 'Thumb flash0x54f6',
            'dimensions_register_address': '0xd05002e4', 'dimensions_packed': '0x01e00280',
            'dimensions': [640, 480], 'code_reference_verified': True,
            'physical_MMIO_contract_tested': False},
        'bootloader_size_bytes': boot_bytes, 'app_header_offset': hex(app_header),
        'app_header_copy_stride': '0x1000', 'app_partition_offset': '0xc0000',
        'app_partition_limit': '0x650000',
        'functions_flash_offsets': {'section_name_compare': '0x641c', 'word_reader': '0x6448',
            'section_getter': '0x6478', 'section_parser': '0x64a8', 'section_loader': '0x5a1c',
            'dt_initrd_patch': '0x6594', 'gp_header_magic_copy': '0x6e64',
            'gp_header_select': '0x6e8c', 'partition_find_by_type': '0x6ef8', 'partition_decode': '0x6ec8'},
        'section_parser': 'type1, header body >=28 bytes; first three names kernel/initrd/cmdline; offset/length/load-address records',
        'section_destination_addresses': {'kernel_scratch': '0x02000000', 'initrd': '0x00a00000', 'device_tree': '0x00000100'},
        'gp_header_selection': 'GPAP magic and generation byte7 choose primary/secondary header copy; this does not establish a second full firmware slot',
        'existing_update_metadata': {'crc_offset': '0x100', 'crc': hex(word(0x100)),
            'zip_dos_time_offset': '0x104', 'zip_dos_time': hex(word(0x104)),
            'compatibility_offset': '0x108', 'compatibility': hex(word(0x108))},
        'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
        'device_access': False, 'vendor_code_executed': False,
        'limits': 'Exact pointer/instruction fingerprints and interpreted routine contracts; QEMU execution is a separate result. No physical flash-write, boot-ROM recovery or full kernel execution qualification.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('image', type=Path)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    report = json.dumps(extract(args.image), indent=2)+'\n'
    if args.output:
        args.output.write_text(report, encoding='utf-8', newline='\n')
    else:
        print(report, end='')
