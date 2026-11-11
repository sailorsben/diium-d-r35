"""Render the English D-R35 launcher assets against the stock sprite layout."""

import argparse
import io
import json
from pathlib import Path
import runpy
import struct
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps


STOCK = runpy.run_path(str(Path(__file__).with_name("inspect-stock-menu.py")))
SIZE = (640, 480)
INK = "#f5f4ec"
GOLD = "#ffcb7a"
PANEL = "#101b2b"
HEADER = "#0e1624"
EDGE = "#5e697a"
SELECTED = "#394965"
TITLES = (
    "MAME", "Sega Mega Drive", "Super Nintendo", "Nintendo NES",
    "Game Boy Advance", "Game Boy", "Game Boy Color", "PlayStation",
    "CPS1", "CPS2", "IGS", "Neo Geo", "Last Played", "Favorites",
    "Search", "All Games", "Download", "Settings",
)
SETTINGS = ("Language", "Volume", "Brightness", "Restore factory settings")
PAUSE = ("Resume", "Exit", "Save state", "Load state", "Controls")
KEYS = tuple("1234567890QWERTYUIOPASDFGHJKL") + ("×",) + tuple("ZXCVBNM") + ("-", ".", "‹")


def write_pack(path, stock, replacements):
    """Encode the vendor's ZIP signatures and name mask."""
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as out:
        for info in stock.infolist():
            payload = replacements[info.filename] if info.filename in replacements else stock.read(info)
            out.writestr(info.filename, payload)
    data = bytearray(archive.getvalue())
    end = len(data) - 22
    count, _, cursor = struct.unpack_from("<HII", data, end + 10)
    data[end:end + 4] = b"WQW\x01"
    for _ in range(count):
        name_size, extra, comment = struct.unpack_from("<3H", data, cursor + 28)
        local, = struct.unpack_from("<I", data, cursor + 42)
        data[cursor:cursor + 4] = b"WQW\x02"
        data[local:local + 4] = b"WQW\x03"
        for start in (cursor + 46, local + 30):
            data[start:start + name_size] = bytes(value ^ 0x5a for value in data[start:start + name_size])
        cursor += 46 + name_size + extra + comment
    path.write_bytes(data)


def sprites(original, images):
    records = STOCK["sprite_records"](original)
    if len(records) != len(images):
        raise ValueError("image count differs from stock sprite layout")
    data = bytearray(original)
    for (offset, width, height, *box), source in zip(records, images):
        if source.size != (width, height):
            raise ValueError("image dimensions differ from stock sprite layout")
        pixels = np.asarray(source.crop(box), dtype=np.uint16)
        red, green, blue = np.moveaxis(pixels, -1, 0)
        encoded = ((red >> 3) << 11) | ((green >> 2) << 5) | (blue >> 3)
        raw = encoded.astype("<u2").tobytes()
        data[offset:offset + len(raw)] = raw
    return data


def illustrated_background(source, carousel=False, vertical=.23):
    art = ImageOps.fit(source, SIZE, Image.Resampling.LANCZOS, centering=(.5, vertical))
    x = np.linspace(0, 1, SIZE[0])[None, :]
    y = np.linspace(0, 1, SIZE[1])[:, None]
    if carousel:
        alpha = .79 * np.maximum(0, 1 - x / .78) ** 1.15 + .16 * y ** 4
    else:
        alpha = .63 + .24 * (1 - x) + .1 * y
    base = np.asarray(art) * (1 - alpha[:, :, None])
    base += np.array([8, 13, 23]) * alpha[:, :, None]
    return Image.fromarray(base.round().astype("uint8"), "RGB")


class LauncherArt:
    def __init__(self, font, scenes):
        self.font = font
        self.scenes = scenes
        self.fonts = {}

    def type(self, size):
        if size not in self.fonts:
            self.fonts[size] = ImageFont.truetype(str(self.font), size)
        return self.fonts[size]

    def label(self, draw, at, words, size=23, fill=INK, anchor="lm", **style):
        draw.text(at, words, font=self.type(size), fill=fill, anchor=anchor, **style)

    def heading(self, image, title):
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 639, 53), fill=HEADER)
        if title:
            self.label(draw, (32, 26), title, 30)
        draw.rectangle((32, 48, 127, 51), fill=GOLD)
        return draw

    def carousel(self):
        pages = []
        for title, scene in zip(TITLES, self.scenes):
            image = illustrated_background(scene, carousel=True, vertical=.66 if title == "Super Nintendo" else .23)
            draw = ImageDraw.Draw(image)
            size = 60
            while self.type(size).getlength(title) > 325:
                size -= 1
            self.label(draw, (37, 138), title, size, stroke_width=2, stroke_fill=HEADER)
            draw.rectangle((39, 176, 38 + round(self.type(size).getlength(title)), 180), fill=GOLD)
            pages.append(image)
        return pages

    def controls(self, draw, x, y, spacing, controls):
        for index, (key, action) in enumerate(controls):
            center = x + index * spacing
            draw.ellipse((center - 17, y - 17, center + 17, y + 17), fill=HEADER, outline=GOLD, width=2)
            if key == "D-pad":
                draw.line((center - 7, y, center + 7, y), fill=GOLD, width=3)
                draw.line((center, y - 7, center, y + 7), fill=GOLD, width=3)
            else:
                self.label(draw, (center, y), key, 16, GOLD, "mm")
            self.label(draw, (center, y + 34), action, 15, INK, "mm")

    def list_surface(self, image, original):
        draw = ImageDraw.Draw(image)
        rows = STOCK["sprite_records"](original)[1:10]
        for _, _, _, left, top, right, bottom in rows:
            draw.rounded_rectangle((left + 5, top + 6, right - 6, bottom - 9),
                                   radius=7, fill=PANEL, outline=EDGE)
        return rows

    def library(self, original):
        base = illustrated_background(self.scenes[15])
        draw = self.heading(base, "")
        rows = self.list_surface(base, original)
        draw.rectangle((324, 66, 627, 353), outline=EDGE, width=2)
        draw.rounded_rectangle((324, 370, 627, 465), radius=8, fill=PANEL, outline=EDGE)
        self.controls(draw, 365, 405, 73, (("D-pad", "Select"), ("A", "Enter"), ("B", "Back"), ("L2", "Favorites")))
        variants = [base]
        for _, _, _, left, top, right, bottom in rows:
            highlighted = base.copy()
            ImageDraw.Draw(highlighted).rounded_rectangle(
                (left + 5, top + 6, right - 6, bottom - 9), radius=7, fill=SELECTED, outline=GOLD, width=2)
            variants.append(highlighted)
        for title in ("Select games", "History", "Favorites", "Search"):
            titled = base.copy()
            self.label(ImageDraw.Draw(titled), (32, 24), title, 25)
            variants.append(titled)
        modal = illustrated_background(self.scenes[15])
        frame = ImageDraw.Draw(modal)
        frame.rounded_rectangle((12, 8, 629, 465), radius=6, fill=PANEL, outline=EDGE, width=2)
        self.label(frame, (34, 29), "ROM")
        frame.rectangle((34, 48, 127, 51), fill=GOLD)
        variants.append(modal)
        return variants

    def settings(self):
        base = illustrated_background(self.scenes[17])
        draw = self.heading(base, "Settings")
        draw.rounded_rectangle((62, 106, 577, 344), radius=11, fill=PANEL, outline=EDGE)
        rows = []
        for index, title in enumerate(SETTINGS):
            y = 161 + index * 50
            self.settings_row(draw, title, index, y)
            rows.append(y)
        self.controls(draw, 193, 405, 127, (("D-pad", "Select"), ("A", "Enter"), ("B", "Back")))
        variants = [base]
        for index, (title, y) in enumerate(zip(SETTINGS, rows)):
            selected = base.copy()
            painter = ImageDraw.Draw(selected)
            painter.rounded_rectangle((96, y - 19, 544, y + 19),
                                      radius=6, fill=SELECTED, outline=GOLD, width=2)
            self.settings_row(painter, title, index, y)
            variants.append(selected)
        return variants

    def settings_row(self, draw, title, index, y):
        if index == 0:
            draw.ellipse((125, y - 9, 143, y + 9), outline=GOLD, width=2)
            draw.ellipse((130, y - 9, 138, y + 9), outline=GOLD)
            draw.line((126, y, 142, y), fill=GOLD)
        elif index == 1:
            draw.polygon(((123, y - 3), (128, y - 3), (133, y - 8),
                          (133, y + 8), (128, y + 3), (123, y + 3)), fill=GOLD)
            draw.arc((128, y - 8, 144, y + 8), -64, 64, fill=GOLD, width=2)
        elif index == 2:
            draw.ellipse((130, y - 4, 138, y + 4), outline=GOLD, width=2)
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)):
                draw.line((134 + 6 * dx, y + 6 * dy, 134 + 9 * dx, y + 9 * dy), fill=GOLD, width=2)
        else:
            draw.arc((126, y - 8, 142, y + 8), -90, 220, fill=GOLD, width=2)
            draw.polygon(((124, y - 5), (131, y - 8), (130, y - 1)), fill=GOLD)
        self.label(draw, (178, y), title)
        if index == 0:
            self.label(draw, (298, y), "›", 24, GOLD)
        if index in (1, 2):
            draw.line((419, y, 427, y), fill=GOLD, width=2)
            self.label(draw, (485, y), "+", 25, GOLD, "mm")

    def search(self, original, library):
        base = illustrated_background(self.scenes[14])
        draw = self.heading(base, "Search")
        # The stock compositor also pastes the nine list-row highlights here.
        left_box = (0, 54, 318, 480)
        base.paste(library.crop(left_box), left_box)
        draw.line((318, 63, 318, 465), fill=EDGE)
        draw.rounded_rectangle((324, 65, 627, 107), radius=6, fill="#fcfbf2", outline=GOLD)
        draw.rounded_rectangle((324, 122, 627, 349), radius=7, fill=PANEL, outline=EDGE)
        draw.rounded_rectangle((324, 370, 627, 465), radius=8, fill=PANEL, outline=EDGE)
        self.controls(draw, 365, 405, 73, (("D-pad", "Select"), ("A", "Enter"), ("B", "Back"), ("L2", "Favorites")))
        keys = STOCK["sprite_records"](original)[1:]
        for (_, _, _, left, top, right, bottom), value in zip(keys, KEYS + ("Enter",)):
            self.label(draw, ((left + right) / 2, (top + bottom) / 2), value, 16, INK, "mm")
        variants = [base]
        for (_, _, _, left, top, right, bottom), value in zip(keys, KEYS + ("Enter",)):
            selected = base.copy()
            painter = ImageDraw.Draw(selected)
            painter.rectangle((left, top, right - 1, bottom - 1), fill=GOLD)
            self.label(painter, ((left + right) / 2, (top + bottom) / 2), value, 16, HEADER, "mm")
            variants.append(selected)
        return variants

    def pause(self, original):
        base = illustrated_background(self.scenes[12])
        draw = self.heading(base, "Game Settings")
        draw.rectangle((344, 89, 540, 235), outline=EDGE, width=2)
        draw.rounded_rectangle((286, 263, 615, 445), radius=8, outline=EDGE, width=2)
        records = STOCK["sprite_records"](original)
        for (_, _, _, left, top, right, bottom), title in zip(records[1:6], PAUSE):
            draw.rounded_rectangle((left + 4, top + 5, right - 5, bottom - 6),
                                   radius=6, fill=PANEL, outline=EDGE)
            self.label(draw, (left + 19, (top + bottom) / 2), title)
        variants = [base]
        for (_, _, _, left, top, right, bottom), title in zip(records[1:6], PAUSE):
            selected = base.copy()
            painter = ImageDraw.Draw(selected)
            painter.rounded_rectangle((left + 4, top + 5, right - 5, bottom - 6),
                                      radius=6, fill=SELECTED, outline=GOLD, width=2)
            self.label(painter, (left + 19, (top + bottom) / 2), title)
            variants.append(selected)
        slots = base.copy()
        painter = ImageDraw.Draw(slots)
        for row in range(2):
            for column in range(3):
                x, y = 295 + column * 101, 291 + row * 70
                painter.rounded_rectangle((x, y, x + 91, y + 59), radius=5, fill=PANEL, outline=EDGE)
                painter.line((x + 40, y + 30, x + 50, y + 30), fill=INK, width=2)
        controls = base.copy()
        painter = ImageDraw.Draw(controls)
        painter.ellipse((293, 318, 375, 400), fill=PANEL, outline=GOLD, width=2)
        self.label(painter, (334, 359), "D-pad", 17, GOLD, "mm")
        for row, pair in enumerate((("L1", "R1"), ("X", "Y"), ("A", "B"))):
            for column, key in enumerate(pair):
                x, y = 395 + 99 * column, 284 + 47 * row
                painter.rounded_rectangle((x, y, x + 89, y + 41), radius=13, fill=PANEL, outline=EDGE)
                self.label(painter, (x + 15, y + 21), key, 16, GOLD)
        return variants + [slots, controls]


def scenes_from_manifest(path):
    """Each reviewed scene names its contact sheet and row-major tile index."""
    scenes = []
    for name, index in json.loads(path.read_text(encoding="utf-8-sig")):
        with Image.open(path.parent / name) as sheet:
            width, height = sheet.size
            row, column = divmod(index, 3)
            if not (0 <= row < 3):
                raise ValueError(f"invalid scene index {index}")
            box = (round(column * width / 3) + 2, round(row * height / 3) + 2,
                   round((column + 1) * width / 3) - 2, round((row + 1) * height / 3) - 2)
            scenes.append(sheet.crop(box).convert("RGB"))
    if len(scenes) != len(TITLES):
        raise ValueError("need one reviewed scene per carousel entry")
    return scenes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stock_english", type=Path)
    parser.add_argument("scene_manifest", type=Path)
    parser.add_argument("font", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    art = LauncherArt(args.font, scenes_from_manifest(args.scene_manifest))
    args.output.mkdir()
    pack = args.output / "ui_en.bkp"
    with STOCK["open_pack"](args.stock_english) as stock:
        raw = {name: stock.read(name) for name in ("type.raw", "menu.raw", "setting.raw", "search.raw", "game.raw")}
        library = art.library(raw["menu.raw"])
        images = {
            "type.raw": art.carousel(), "menu.raw": library, "setting.raw": art.settings(),
            "search.raw": art.search(raw["search.raw"], library[0]), "game.raw": art.pause(raw["game.raw"]),
        }
        updated = {name: sprites(raw[name], frames) for name, frames in images.items()}
        write_pack(pack, stock, updated)
        with STOCK["open_pack"](pack) as result:
            if result.testzip() or stock.namelist() != result.namelist():
                raise ValueError("launcher pack failed ZIP validation")
            for name in result.namelist():
                expected = updated[name] if name in updated else stock.read(name)
                if result.read(name) != expected:
                    raise ValueError(f"launcher pack round trip differs at {name}")
    for name, index, preview in (("type.raw", 2, "snes"), ("type.raw", 17, "settings-tile"),
                                 ("setting.raw", 0, "settings"), ("search.raw", 0, "search"),
                                 ("game.raw", 0, "pause")):
        STOCK["preview_png"](updated[name], STOCK["sprite_records"](updated[name])[index],
                             args.output / f"{preview}.png")
    overview = Image.new("RGB", (960, 900))
    for index, frame in enumerate(images["type.raw"]):
        row, column = divmod(index, 4)
        overview.paste(frame.resize((240, 180), Image.Resampling.LANCZOS), (column * 240, row * 180))
    overview.save(args.output / "carousel.png")
    print(f"{pack}: {sum(map(len, images.values()))} sprites, {pack.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
