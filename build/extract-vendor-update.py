"""Recover bounded updater contracts from the exact private vrtemu ELF.

Never executes the vendor program or opens hardware. Emits interpreted metadata,
not the executable, disassembly or an update image.
"""
from pathlib import Path
from hashlib import sha256
import argparse,json,struct

EXPECTED='8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72'

def extract(path):
    data=Path(path).read_bytes();assert sha256(data).hexdigest()==EXPECTED
    assert data[:6]==b'\x7fELF\x01\x01' and struct.unpack_from('<H',data,18)[0]==40
    start=struct.unpack_from('<I',data,28)[0];size,count=struct.unpack_from('<HH',data,42)
    loads=[struct.unpack_from('<8I',data,start+i*size) for i in range(count)]
    def offset(address):
        for kind,off,virtual,_,length,_,_,_ in loads:
            if kind==1 and virtual<=address<virtual+length:return off+address-virtual
        raise ValueError(f'Address is not file-backed: {address:x}')
    def word(address):return struct.unpack_from('<I',data,offset(address))[0]
    def text(address):
        off=offset(address);end=data.index(b'\x00',off,off+256)
        return data[off:end].decode('ascii')
    def relative(add,literal):return text(add+8+word(literal))
    # Independent machine instructions, not string-name inference. A different
    # binary is rejected rather than applying these offsets to another version.
    wanted={0x1231c:0xeb000436,0x12824:0xe3a01c6b,0x12830:0xe3441020,
            0x1288c:0xe3a02006,0x128b8:0xe3a02005,0x12960:0xe3e01027,
            0x129f0:0xe3a03002,0x12aa8:0xe3a0e003,0x12ab4:0xe3441040,
            0x13680:0xe3530057,0x1368c:0xe3530051,0x13698:0xe3530057,
            0x137a4:0xeb0231b2,0x13950:0xebfffdd2,0x1399c:0xebfff899}
    for address,value in wanted.items():assert word(address)==value,hex(address)
    stage=relative(0x122f0,0x12418);device=relative(0x13414,0x13a24)
    assert stage=='update/Code.bkp' and device=='/dev/spidev0.0'
    assert relative(0x1364c,0x13a64)=='r+b'
    return {'vendor_sha256':EXPECTED,'vendor_bytes':len(data),'vendor_execution':False,
        'main_update_call':'0x1231c -> UpdateROM 0x133fc',
        'staging_path':'Executable directory + '+stage,
        'update_file_open_mode':'r+b','update_file_prefix':'WQW',
        'alternate_path_string':text(0x19969c),
        'alternate_path_string_is_not_a_proven_trigger':True,
        'spi_device':device,'single_transfer_ioctl':'0x40206b00',
        'two_transfer_ioctl':'0x40406b00','transfer_struct_bytes':32,
        'commands':{'read':'03 + 24-bit address','read_status':'05',
            'write_enable':'06','page_program':'02 + 24-bit address',
            'block_erase':'d8 + 24-bit address'},
        'read_contract':'4-byte command transfer then receive transfer, same ioctl',
        'update_validation_observed':['WQW prefix','OpenZipU and first item',
            'first-item CRC32 compared with _ucrc32','internal/image compatibility comparison'],
        'update_proc':'0x130a0: 64 KiB reads/compare, erase on difference, 256-byte programs, reread/retry',
        'successful_update':'sync then reboot',
        'limits':'No chip ID, capacity, full image format, physical read/write or recovery mechanism qualified. A dump is a backup, not a proven unbrick path.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('binary',type=Path)
    p.add_argument('--output',type=Path);a=p.parse_args();raw=json.dumps(extract(a.binary),indent=2)+'\n'
    if a.output:a.output.write_text(raw,encoding='utf-8',newline='\n')
    else:print(raw,end='')
