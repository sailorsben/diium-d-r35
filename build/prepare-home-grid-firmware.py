"""Prepare the internal boot handoff for the permanent SD launcher grid."""

import argparse
from importlib import import_module
import io
import json
from pathlib import Path
import struct
import zipfile
import zlib


direct = import_module("prepare-direct-launcher-firmware")
ROOT = direct.ROOT
DATE = (2026, 11, 13, 19, 30, 0)


def prepare(baseline, out):
    prior = json.loads(
        (ROOT/"evidence/2026-11-13/direct-launcher-firmware-qualification.json").read_text()
    )
    flash = baseline.read_bytes()
    if len(flash)!=8388608 or direct.digest(flash)!=prior["artifact_sha256"]["expected-after-vendor.bin"]:
        raise ValueError("Expected the verified direct-launcher SPI image")
    size, = struct.unpack_from("<I", flash, direct.LENGTH)
    compressed = flash[direct.START:direct.START+size]
    cpio, consumed = direct.inspect.gunzip(compressed)
    assert consumed==size and compressed[3]==0
    entries = direct.inspect.newc(cpio)
    entry = next(e for e in entries if e["name"]=="init.project.rc")
    start, offset, length = (entry[k] for k in ("header_offset", "data_offset", "bytes"))
    project = cpio[offset:offset+length]
    assert direct.digest(project)==prior["artifact_sha256"]["init.project.rc"]
    board = project.replace(b"firmware=direct-launcher-v1", b"firmware=direct-launcher-grid-v2")
    board = direct.replace_once(board, b"        if IFS= read -r boot_id", b"""        layout=stock
        if [ -r /usr/retro/d35-launcher1/home-grid.rgb565 ]; then
            layout=grid
        fi
        if IFS= read -r boot_id""")
    board = direct.replace_once(board,
        b"frontend=/usr/retro/vrtemu\n' \"$boot_id\"",
        b"frontend=/usr/retro/vrtemu\nlayout=%s\n' \"$boot_id\" \"$layout\"")
    header = bytearray(cpio[start:offset])
    header[54:62] = f"{len(board):08x}".encode()
    record = bytes(header)+board
    record += b"\0"*(-len(record)%4)
    updated = cpio[:start]+record+cpio[(offset+length+3)&~3:]
    updated = updated[:(direct.inspect.newc(updated)[-1]["data_offset"]+3)&~3]
    updated += b"\0"*(-len(updated)%512)
    def identity(items):
        return [(e["name"],e["mode"],e["bytes"],e["sha256"])
                for e in items if e["name"]!="init.project.rc"]
    assert identity(direct.inspect.newc(updated))==identity(entries)

    compressor = zlib.compressobj(9,zlib.DEFLATED,-15)
    packed = compressed[:10]+compressor.compress(updated)+compressor.flush()
    packed += struct.pack("<II",zlib.crc32(updated),len(updated))
    assert len(packed)<=direct.SLOT and direct.inspect.gunzip(packed)==(updated,len(packed))
    candidate = bytearray(flash)
    struct.pack_into("<I",candidate,direct.LENGTH,len(packed))
    candidate[direct.START:direct.START+direct.SLOT] = packed+b"\xff"*(direct.SLOT-len(packed))
    assert candidate[:direct.LENGTH]==flash[:direct.LENGTH]
    assert candidate[direct.LENGTH+4:direct.START]==flash[direct.LENGTH+4:direct.START]
    assert candidate[direct.START+direct.SLOT:]==flash[direct.START+direct.SLOT:]
    archive = io.BytesIO()
    member = zipfile.ZipInfo("SPI_ROM.bin",DATE)
    member.compress_type = zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(archive,"w") as package:
        package.writestr(member,candidate,compresslevel=9)
    crc = zlib.crc32(candidate)
    assert crc!=struct.unpack_from("<I",flash,0x100)[0]
    year,month,day,hour,minute,second = DATE
    timestamp = ((year-1980)<<25)|(month<<21)|(day<<16)|(hour<<11)|(minute<<5)|(second//2)
    expected = bytearray(candidate)
    struct.pack_into("<II",expected,0x100,crc,timestamp)
    files = {"candidate.bin":candidate,"expected-after-vendor.bin":expected,
             "Code.bkp":b"WQW"+archive.getvalue(),"init.project.rc":board}
    out.mkdir(exist_ok=False)
    for name,data in files.items():
        (out/name).write_bytes(data)
    blocks = [f"{i:06x}" for i in range(0,len(expected),65536)
              if expected[i:i+65536]!=flash[i:i+65536]]
    report = {"baseline_sha256":direct.digest(flash),
              "artifact_sha256":{n:direct.digest(data) for n,data in files.items()},
              "changed_rootfs_files":["init.project.rc"],"rootfs_bytes":len(packed),
              "expected_erased_blocks":blocks,"expected_page_programs":len(blocks)*256}
    (out/"preparation.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("baseline",type=Path)
    p.add_argument("output",type=Path)
    a = p.parse_args()
    out = a.output.resolve()
    if not out.is_relative_to(ROOT/"device-evidence"):
        p.error("output must be private under device-evidence")
    prepare(a.baseline,out)
