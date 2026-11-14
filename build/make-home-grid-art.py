"""Pack the reviewed home grid and reorder the English Settings artwork."""

import argparse
import base64
import io
import json
from pathlib import Path
import re
import runpy
import struct

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps


ART = runpy.run_path(str(Path(__file__).with_name("make-stock-shell-art.py")))
STOCK = ART["STOCK"]
LABELS = (
    "Super Nintendo", "Nintendo Entertainment System", "Sega Genesis", "PlayStation",
    "Game Boy Advance", "Game Boy Color", "Game Boy", "MAME",
    "Capcom Arcade · CPS-1", "Capcom Arcade · CPS-2", "IGS Arcade", "Neo Geo",
)
SHORTCUTS = (
    ("START", "Settings"), ("SELECT", "Favorites"), ("X", "Search"), ("Y", "Last Played"),
    ("L", "All Games"), ("R", "Browse Files"), ("D-pad", "Move"), ("A", "Open"),
)


def rgb565(image):
    r, g, b = np.moveaxis(np.asarray(image.convert("RGB"), dtype=np.uint16), -1, 0)
    return (((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)).astype("<u2").tobytes()


def build_home(preview, font, output):
    match = re.search(r"^  const art = (.*);$", preview.read_text(encoding="utf-8"), re.M)
    images = json.loads(match[1])["tiles"]
    assert len(images) == len(LABELS)
    bg, bar, ink, accent = "#0a1421", "#111c2d", "#f2f3f4", "#ffd083"
    canvas = Image.new("RGB", (640, 480), bg)
    draw = ImageDraw.Draw(canvas)
    text = lambda size: ImageFont.truetype(str(font), size)
    draw.text((20, 28), "Game Library", font=text(26), fill=ink, anchor="lm")
    draw.line((0, 51, 639, 51), fill="#35465e")
    for i, uri in enumerate(images):
        prefix, data = uri.split(",", 1)
        assert prefix == "data:image/webp;base64"
        with Image.open(io.BytesIO(base64.b64decode(data, validate=True))) as asset:
            tile = ImageOps.fit(asset.convert("RGB"), (144, 104), Image.Resampling.LANCZOS)
        pos = (20+152*(i%4), 62+112*(i//4))
        mask = Image.new("L", tile.size)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, 143, 103), radius=5, fill=255)
        canvas.paste(tile, pos, mask)
        x, y = pos
        draw.rounded_rectangle((x, y, x+143, y+103), radius=5, outline="#35465e")

    draw.rectangle((0, 402, 639, 479), fill=bar)
    draw.line((0, 402, 639, 402), fill="#35465e")
    for i, (key, label) in enumerate(SHORTCUTS):
        x, y = 25+152*(i%4), 413+30*(i//4)
        width = int(draw.textlength(key, font=text(12)))+10
        draw.rounded_rectangle((x, y, x+width, y+19), radius=3, fill=bg, outline="#35465e")
        draw.text((x+5, y+10), key, font=text(12), fill=accent, anchor="lm")
        draw.text((x+width+7, y+10), label, font=text(15), fill=ink, anchor="lm")
    labels = bytearray()
    for name in LABELS:
        image = Image.new("RGB", (320, 30), bg)
        ImageDraw.Draw(image).text((319, 15), name, font=text(16), fill=accent, anchor="rm")
        labels.extend(rgb565(image))
    (output/"home-grid.rgb565").write_bytes(rgb565(canvas)+labels)
    canvas.save(output/"home-grid.png")


def build_settings(pack, font, destination, classic):
    with STOCK["open_pack"](pack) as archive:
        raw = archive.read("setting.raw")
        records = STOCK["sprite_records"](raw)
        assert len(records) == 13
        shift = 18 if classic else 0
        base = ART["read_sprite"](raw, records[0])
        draw = ImageDraw.Draw(base)
        art = ART["LauncherArt"](font, [])
        panel = base.getpixel((100, 350-shift))
        draw.rectangle((90, 288-shift, 549, 441-shift), fill=panel)
        accent = "#afc8ca" if classic else ART["GOLD"]
        focus = "#163739" if classic else ART["SELECTED"]

        def simple_row(y, label, selected, power_icon):
            row = Image.new("RGB", (460, 37), panel)
            p = ImageDraw.Draw(row)
            p.rounded_rectangle((6, 1, 454, 35), radius=5,
                                fill=focus if selected else panel,
                                outline=accent if selected else ART["EDGE"],
                                width=2 if selected else 1)
            if power_icon:
                p.arc((29, 10, 45, 26), -51, 231, fill=accent, width=2)
                p.line((37, 8, 37, 17), fill=accent, width=2)
            else:
                p.arc((29, 10, 45, 26), 22, 308, fill=accent, width=2)
                p.line(((38, 14), (45, 14), (45, 8)), fill=accent, width=2)
            art.label(p, (88, 18), label, 22, "#ffffff")
            return (90, y-shift, 550, y-shift+37), row

        reset = simple_row(404, "Restore factory settings", False, False)
        power = simple_row(365, "Power Off", False, True)
        for box, row in (reset, power):
            base.paste(row, box[:2])
        if not classic:
            draw.rectangle((90, 442, 549, 451), fill=panel)
        frames = [(records[0][3:], base)]
        frames.extend((row[3:], ART["read_sprite"](raw, row)) for row in records[1:4])
        frames.append(simple_row(404, "Restore factory settings", True, False))
        for index, row in enumerate(records[5:13]):
            y = (288 if index<4 else 326)-shift
            scene = ART["read_sprite"](raw, row).resize((460, 37), Image.Resampling.LANCZOS)
            frames.append(((90, y, 550, y+37), scene))
            if index in (0, 4+int(classic)):
                base.paste(scene, (90, y))
        frames.extend((power, simple_row(365, "Power Off", True, True)))
        pixels, headers = bytearray(), bytearray()
        for box, image in frames:
            headers.extend(struct.pack("<I6H", len(frames)*16+len(pixels), 640, 480, *box))
            pixels.extend(rgb565(image))
        result = bytes(headers+pixels)
        assert [r[3:] for r in STOCK["sprite_records"](result)] == [box for box, _ in frames]
        ART["write_pack"](destination, archive, {"setting.raw": result})
        base.save(destination.with_suffix(".png"))
        with STOCK["open_pack"](destination) as verified:
            assert verified.namelist() == archive.namelist() and verified.testzip() is None
            assert all(verified.read(n) == archive.read(n) for n in archive.namelist() if n!="setting.raw")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("preview", "new", "classic", "font", "output"):
        p.add_argument(name, type=Path)
    a = p.parse_args()
    a.output.mkdir(exist_ok=True)
    build_home(a.preview, a.font, a.output)
    for pack, classic in ((a.new, False), (a.classic, True)):
        build_settings(pack, a.font, a.output/pack.name, classic)
