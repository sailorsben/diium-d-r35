"""Inspect the stock D-R35 menu packs without writing to the card."""

import argparse
import io
import json
import re
import struct
import zipfile
import zlib
from pathlib import Path


def open_pack(path):
    data = bytearray(path.read_bytes())
    end = data.rfind(b"WQW\x01")
    if data[:4] != b"WQW\x03" or end != len(data) - 22:
        raise ValueError(f"{path.name}: unexpected pack headers")
    count, size, cursor = struct.unpack_from("<HII", data, end + 10)
    if cursor + size != end:
        raise ValueError(f"{path.name}: invalid central directory bounds")
    data[end:end + 4] = b"PK\x05\x06"
    for _ in range(count):
        if data[cursor:cursor + 4] != b"WQW\x02":
            raise ValueError(f"{path.name}: invalid central header")
        length, extra, comment = struct.unpack_from("<3H", data, cursor + 28)
        local, = struct.unpack_from("<I", data, cursor + 42)
        if data[local:local + 4] != b"WQW\x03":
            raise ValueError(f"{path.name}: invalid local header")
        local_length, = struct.unpack_from("<H", data, local + 26)
        central_name, local_name = cursor + 46, local + 30
        if (length != local_length or data[central_name:central_name + length]
                != data[local_name:local_name + length]):
            raise ValueError(f"{path.name}: mismatched filenames")
        data[cursor:cursor + 4] = b"PK\x01\x02"
        data[local:local + 4] = b"PK\x03\x04"
        for start in (central_name, local_name):
            data[start:start + length] = bytes(b ^ 0x5A for b in data[start:start + length])
        cursor = central_name + length + extra + comment
    if cursor != end:
        raise ValueError(f"{path.name}: wrong directory entry count")
    return zipfile.ZipFile(io.BytesIO(data))


def sprite_records(data):
    header_size, width, height = struct.unpack_from("<IHH", data)
    if not (0 < header_size <= len(data) and header_size % 16 == 0):
        raise ValueError("invalid sprite table size")
    records = []
    for offset, w, h, left, top, right, bottom in struct.iter_unpack("<I6H", data[:header_size]):
        length = (right - left) * (bottom - top) * 2
        if not (w == width and h == height and 0 <= left < right <= w
                and 0 <= top < bottom <= h and header_size <= offset <= len(data) - length):
            raise ValueError("invalid sprite rectangle or pixels")
        records.append((offset, w, h, left, top, right, bottom))
    if records[0][3:] != (0, 0, width, height):
        raise ValueError("first sprite does not cover the canvas")
    return records


def preview_png(data, first, path):
    offset, w, h, *_ = first
    pixels = bytearray()
    for y in range(h):
        pixels.append(0)  # PNG row filter: none
        row = data[offset + y * w * 2:offset + (y + 1) * w * 2]
        for (p,) in struct.iter_unpack("<H", row):
            r, g, b = p >> 11, (p >> 5) & 63, p & 31
            pixels.extend(((r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)))

    def chunk(kind, payload):
        return (struct.pack(">I", len(payload)) + kind + payload
                + struct.pack(">I", zlib.crc32(kind + payload)))

    with path.open("xb") as out:
        out.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                  + chunk(b"IDAT", zlib.compress(pixels)) + chunk(b"IEND", b""))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("retro", type=Path, help="stock retro directory or archived copy")
    parser.add_argument("--settings-preview", type=Path, help="new local PNG path for the English settings background")
    args = parser.parse_args()
    config = (args.retro / "setting.xml").read_bytes()
    packs = [p.decode("ascii") for p in re.findall(rb'<ui\b[^>]*\bfilename="(ui_[a-z]+\.bkp)"', config)]
    if "ui_en.bkp" not in packs:
        raise ValueError("English pack is missing from setting.xml")
    with open_pack(args.retro / "resource") as archive:
        bad = archive.testzip()
        if bad is not None:
            raise ValueError(f"resource: CRC mismatch in {bad}")
        print("Shared resource:", ", ".join(archive.namelist()))

    for pack in sorted(set(packs)):
        with open_pack(args.retro / pack) as archive:
            bad = archive.testzip()
            if bad is not None:
                raise ValueError(f"{pack}: CRC mismatch in {bad}")
            print(f"{pack}: {len(archive.infolist())} entries, CRC OK")
            if pack != "ui_en.bkp":
                continue
            for member in ("menu.raw", "setting.raw", "type.raw", "search.raw", "game.raw"):
                data = archive.read(member)
                records = sprite_records(data)
                print(json.dumps({"asset": member, "width": records[0][1], "height": records[0][2],
                                  "base_offset": records[0][0], "blocks": len(records)}))
                if member == "setting.raw" and args.settings_preview:
                    preview_png(data, records[0], args.settings_preview)


if __name__ == "__main__":
    main()
