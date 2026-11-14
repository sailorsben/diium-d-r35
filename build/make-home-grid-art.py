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
PREVIEW_LABELS = (
    "Super Nintendo", "Nintendo Entertainment System", "Sega Genesis", "PlayStation",
    "Game Boy Advance", "Game Boy Color", "Game Boy", "MAME",
    "Capcom Arcade · CPS-1", "Capcom Arcade · CPS-2", "IGS Arcade", "Neo Geo",
)
# The reviewed mockup puts SNES and GBA first. Preserve those artwork assets
# while laying out the physical launcher in Nintendo release order.
TILE_ORDER = (1, 0, 2, 3, 6, 5, 4, 7, 8, 9, 10, 11)
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
    assert len(images) == len(PREVIEW_LABELS) == len(TILE_ORDER)
    bg, bar, ink, accent = "#0a1421", "#111c2d", "#f2f3f4", "#ffd083"
    canvas = Image.new("RGB", (640, 480), bg)
    draw = ImageDraw.Draw(canvas)
    text = lambda size: ImageFont.truetype(str(font), size)
    draw.text((20, 28), "Game Library", font=text(26), fill=ink, anchor="lm")
    draw.line((0, 51, 639, 51), fill="#35465e")
    for i, source_index in enumerate(TILE_ORDER):
        uri = images[source_index]
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
    for source_index in TILE_ORDER:
        name = PREVIEW_LABELS[source_index]
        image = Image.new("RGB", (320, 30), bg)
        ImageDraw.Draw(image).text((319, 15), name, font=text(16), fill=accent, anchor="rm")
        labels.extend(rgb565(image))
    (output/"home-grid.rgb565").write_bytes(rgb565(canvas)+labels+b"D353")
    canvas.save(output/"home-grid.png")


POWER_MESSAGES = (
    ("Turn off the handheld?", "The launcher will finish writing to the SD card.",
     (("A", "Turn off"), ("B", "Cancel"))),
    ("Powering off", "Securing the SD card. Please wait.", ()),
    ("Shutdown paused", "Check the SD card on your computer.",
     (("", "Use the power button"),)),
    ("Couldn’t secure the SD card", "Shutdown could not start.",
     (("A", "Retry"), ("B", "Cancel"))),
    ("SD card secured", "Requesting power off…", ()),
    ("Power off request failed", "The SD card is safe to remove.",
     (("", "Use the power button"),)),
)
POWER_BOX = (77, 153, 486, 174)


def build_power(font, output):
    x, y, width, height = POWER_BOX
    scale = 3
    size = (width*scale, height*scale)
    face = lambda points: ImageFont.truetype(str(font), points*scale)
    data = bytearray()
    for classic in (False, True):
        bg, button, edge, accent = (
            ("#122c3e", "#193a4b", "#5e899b", "#8eeaf4") if classic else
            ("#111c2d", "#162337", "#556780", "#ffd083")
        )
        for i, (title, detail, buttons) in enumerate(POWER_MESSAGES):
            panel = Image.new("RGBA", size)
            draw = ImageDraw.Draw(panel)
            def box(left, top, right, bottom, radius, fill, outline=None):
                draw.rounded_rectangle(
                    (left*scale, top*scale, right*scale-1, bottom*scale-1),
                    radius=radius*scale, fill=fill, outline=outline, width=scale,
                )
            def text(left, top, label, points, color):
                draw.text((left*scale, top*scale), label, font=face(points), fill=color, anchor="lm")
            box(0, 0, width, height, 10, bg, accent)
            text(24, 39, title, 27, "#f2f3f4")
            text(24, 80, detail, 18, "#d3deea")
            left = 24
            for key, label in buttons:
                if not key:
                    text(left, 132, label, 17, accent)
                    continue
                w = round(draw.textlength(label, font=face(17))/scale)+59
                box(left, 114, left+w, 151, 5, button, edge)
                box(left+9, 121, left+31, 144, 4, bg, edge)
                text(left+14, 132, key, 14, accent)
                text(left+40, 132, label, 17, "#f2f3f4")
                left += w+12
            panel = panel.resize((width,height),Image.Resampling.LANCZOS)
            # Zero encodes the rounded transparent corners in the RGB565 panel.
            opaque = panel.getchannel("A").point(lambda a: 255 if a>=128 else 0)
            frame = Image.new("RGB", panel.size)
            frame.paste(panel, (0, 0), opaque)
            data.extend(rgb565(frame))
            if i==0:
                with Image.open(output/"home-grid.png") as home:
                    preview = home.point(lambda v: v//2)
                preview.paste(frame, (x,y), opaque)
                preview.save(output/("power-classic.png" if classic else "power-new.png"))
    (output/"power-dialog.rgb565").write_bytes(data)


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
    build_power(a.font, a.output)
    for pack, classic in ((a.new, False), (a.classic, True)):
        build_settings(pack, a.font, a.output/pack.name, classic)
