"""Prepare the permanent D-R35 launcher boot handoff for the verified SPI image."""

import argparse
from hashlib import sha256
from importlib import import_module
import io
import json
from pathlib import Path
import struct
import zipfile
import zlib


ROOT = Path(__file__).resolve().parent.parent
BASELINE = "ef69753afb56c84e4daaf78aa3fad5551d26b7438e49f4f1dbc7312b11e07321"
STOCK_INIT = "b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7"
START = 0x301d10
LENGTH = 0xc0040
SLOT = 0x33fade
DATE = (2026, 11, 13, 12, 0, 0)
READY = b"/tmp/d35-direct-launcher.ready"
BOOT_LOG = b"/usr/retro/d35-launcher1/direct-boot.log"
inspect = import_module("inspect-spi-boot")

# Both the installed firmware and the SD startup used to invoke the updater
# need the same exclusion between the splash and the next display owner.
SPLASH_WAIT = b"""wait_for_splash() {
    : > /tmp/vrtemu.log || return 1
    waited=0
    while :; do
        active=0
        for task in /proc/[0-9]*; do
            [ -r "$task/comm" ] || continue
            IFS= read -r name < "$task/comm" || continue
            [ "$name" = showlogo ] || continue
            zombie=0
            if [ -r "$task/status" ]; then
                while IFS= read -r line; do
                    case "$line" in State:*Z*) zombie=1; break ;; esac
                done < "$task/status"
            fi
            [ "$zombie" = 1 ] || active=1
        done
        [ "$active" = 1 ] || return 0
        [ "$waited" -lt 5 ] || return 1
        sleep 1
        waited=$((waited+1))
    done
}
"""


def digest(data):
    return sha256(data).hexdigest()


def replace_once(data, old, new):
    if data.count(old) != 1:
        raise ValueError("Unexpected pinned startup script")
    return data.replace(old, new)


def startup_scripts(project, stock_init):
    card_start = b"/usr/retro/init &\n"
    board = replace_once(project, card_start, b"""if [ -x /usr/retro/vrtemu ] && [ -r /usr/retro/d35-launcher1/libs/d35-snes.so ]; then
""" + SPLASH_WAIT + b"""    if wait_for_splash && printf 'firmware=direct-launcher-v1\n' > """ + READY + b"""; then
        if IFS= read -r boot_id < /proc/sys/kernel/random/boot_id; then
            printf 'firmware=direct-launcher-v1\nboot_id=%s\nfrontend=/usr/retro/vrtemu\n' "$boot_id" > """ + BOOT_LOG + b"""
        fi
    else
        printf 'Direct launcher: splash handoff failed\n' >&2
        exit 1
    fi
fi
""" + card_start)
    anchor = b'  /usr/retro/main &\n'
    sd = replace_once(stock_init, anchor, b"""  # First update boot still runs under the old firmware.
  if [ ! -f """ + READY + b""" ]; then
""" + SPLASH_WAIT + b"""    wait_for_splash || exit 1
  fi
""" + anchor)
    return board, sd


def prepare(out):
    flash = (ROOT/"device-evidence/uart-kernel-firmware1/expected-after-vendor.bin").read_bytes()
    stock_init = (ROOT/"device-evidence/uart-kernel-firmware1/normal-init").read_bytes()
    assert len(flash) == 8388608 and digest(flash) == BASELINE and digest(stock_init) == STOCK_INIT
    physical = json.loads((ROOT/"evidence/2026-10-17/uart-kernel-reflash/verified-return.json").read_text())
    assert physical["two_pass_flash_exact"] and physical["flash_sha256"] == BASELINE
    size, = struct.unpack_from("<I", flash, LENGTH)
    compressed = flash[START:START+size]
    cpio, consumed = inspect.gunzip(compressed)
    assert consumed == size and compressed[3] == 0
    entries = inspect.newc(cpio)
    entry = next(item for item in entries if item["name"] == "init.project.rc")
    start, offset, size = entry["header_offset"], entry["data_offset"], entry["bytes"]
    old_end = (offset+size+3)&~3
    board, card = startup_scripts(cpio[offset:offset+size], stock_init)
    header = bytearray(cpio[start:offset])
    header[54:62] = f"{len(board):08x}".encode()
    record = bytes(header) + board
    record += b"\0" * (-len(record)%4)
    updated = cpio[:start] + record + cpio[old_end:]
    updated = updated[:(inspect.newc(updated)[-1]["data_offset"]+3)&~3]
    updated += b"\0" * (-len(updated)%512)
    def identity(items):
        return [(e["name"],e["mode"],e["bytes"],e["sha256"]) for e in items if e["name"] != "init.project.rc"]
    assert identity(inspect.newc(updated)) == identity(entries)
    compressor = zlib.compressobj(9,zlib.DEFLATED,-15)
    packed = compressed[:10]+compressor.compress(updated)+compressor.flush()
    packed += struct.pack("<II",zlib.crc32(updated),len(updated))
    assert len(packed) <= SLOT and inspect.gunzip(packed) == (updated,len(packed))
    candidate = bytearray(flash)
    struct.pack_into("<I",candidate,LENGTH,len(packed))
    candidate[START:START+SLOT] = packed+b"\xff"*(SLOT-len(packed))
    assert candidate[:LENGTH] == flash[:LENGTH]
    assert candidate[LENGTH+4:START] == flash[LENGTH+4:START]
    assert candidate[START+SLOT:] == flash[START+SLOT:]
    archive = io.BytesIO()
    item = zipfile.ZipInfo("SPI_ROM.bin", DATE)
    item.compress_type = zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(archive,"w") as container:
        container.writestr(item,candidate,compresslevel=9)
    package = b"WQW"+archive.getvalue()
    crc = zlib.crc32(candidate)
    year, month, day, hour, minute, second = DATE
    timestamp = ((year-1980)<<25)|(month<<21)|(day<<16)|(hour<<11)|(minute<<5)|(second//2)
    expected = bytearray(candidate)
    struct.pack_into("<II",expected,0x100,crc,timestamp)
    blocks = [f"{i:06x}" for i in range(0,len(expected),65536)
              if expected[i:i+65536] != flash[i:i+65536]]
    files = {"candidate.bin":candidate,"expected-after-vendor.bin":expected,
             "Code.bkp":package,"rootfs.cpio.gz":packed,"init.project.rc":board,"sd-init":card}
    out.mkdir()
    for name, contents in files.items():
        (out/name).write_bytes(contents)
    report = {"baseline_sha256":BASELINE,"artifact_sha256":{n:digest(d) for n,d in files.items()},
              "changed_rootfs_files":["init.project.rc"],"rootfs_bytes":len(packed),
              "rootfs_slot_bytes":SLOT,"vendor_metadata":[crc,timestamp],
              "expected_erased_blocks":blocks,"expected_page_programs":len(blocks)*256}
    (out/"preparation.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    out = parser.parse_args().output.resolve()
    assert out.is_relative_to(ROOT/"device-evidence") and not out.exists()
    print(json.dumps(prepare(out),indent=2))
