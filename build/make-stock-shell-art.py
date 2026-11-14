"""Render the English D-R35 launcher assets against the stock sprite layout."""

import argparse
import io
import json
from pathlib import Path
import runpy
import struct
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


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
# Pixel bounds in the pinned stock carousel. Preserve the original logos and
# hardware artwork when painting the replacement character panels.
PLATFORM_ART = {
    2: ("snes", None, None),
    3: ("nes", (33, 82, 354, 231), None),
    7: ("playstation", (82, 24, 290, 214), None),
    8: ("cps1", (47, 85, 312, 172), (96, 211, 254, 418)),
    9: ("cps2", (48, 85, 320, 172), (96, 206, 298, 408)),
    10: ("igs", (79, 78, 245, 151), (54, 204, 233, 419)),
    11: ("neogeo", (24, 11, 357, 169), (58, 197, 258, 449)),
}
NES_HARDWARE_OUTLINES = (
    ((147, 281), (183, 243), (207, 240), (298, 258), (308, 275), (303, 291),
     (270, 339), (258, 353), (240, 351), (213, 330), (172, 321), (147, 313)),
    ((66, 334), (77, 307), (211, 336), (215, 346), (206, 396), (194, 410), (62, 382)),
)


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


def read_sprite(data, record):
    offset, _, _, left, top, right, bottom = record
    width, height = right - left, bottom - top
    pixel = np.frombuffer(data, "<u2", width * height, offset).reshape(height, width)
    red, green, blue = pixel >> 11, (pixel >> 5) & 63, pixel & 31
    rgb = np.stack(((red << 3) | (red >> 2), (green << 2) | (green >> 4),
                    (blue << 3) | (blue >> 2)), axis=-1).astype("uint8")
    return Image.fromarray(rgb, "RGB")


def stock_patch(target, stock, box, feather=28):
    """Keep original RGB pixels inside the box and fade only outside it."""
    x = np.arange(SIZE[0])[None, :]
    y = np.arange(SIZE[1])[:, None]
    left, top, right, bottom = box
    dx = np.maximum(0, np.maximum(left - x, x - right + 1))
    dy = np.maximum(0, np.maximum(top - y, y - bottom + 1))
    opacity = np.maximum(0, 1 - np.hypot(dx, dy) / feather)
    target.paste(stock, mask=Image.fromarray((255 * opacity).round().astype("uint8"), "L"))


def stock_nes_hardware(target, stock):
    mask = Image.new("L", SIZE)
    draw = ImageDraw.Draw(mask)
    for outline in NES_HARDWARE_OUTLINES:
        draw.polygon(outline, fill=255)
    target.paste(stock, mask=mask.filter(ImageFilter.GaussianBlur(.65)))


def stock_nes_badge(target, stock):
    # The gray Nintendo badge is a pill. The lower wordmark uses only
    # red and white. Neither mask needs the old character behind the logo.
    mask = Image.new("L", SIZE)
    ImageDraw.Draw(mask).rounded_rectangle((34, 82, 351, 176), radius=47, fill=255)
    box = (52, 178, 339, 232)
    red, green, blue = np.moveaxis(np.asarray(stock.crop(box)), -1, 0)
    wordmark = ((red > 135) & (green < 70) & (blue < 90)) | ((red > 174) & (green > 174) & (blue > 174))
    letters = Image.fromarray(wordmark.astype("uint8") * 255, "L").filter(ImageFilter.MaxFilter(3))
    mask.paste(letters, box[:2])
    target.paste(stock, mask=mask)


def super_nintendo_branding(canvas, portraits):
    with Image.open(portraits / "snes-logo.png") as image:
        badge = image.convert("RGB")
        badge.thumbnail((310, 104), Image.Resampling.LANCZOS)
        canvas.paste(badge, (23, 99))
    with Image.open(portraits / "snes-console.png") as image:
        console = image.convert("RGBA")
        console = console.crop(console.getbbox())
        console.thumbnail((278, 176), Image.Resampling.LANCZOS)
        canvas.paste(console, (37, 226), console)


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

    def familiar_carousel(self, original, portraits):
        frames = self.carousel()
        stock = STOCK["sprite_records"](original)
        for index in range(12):
            reference = read_sprite(original, stock[index])
            if index not in PLATFORM_ART:
                frames[index] = reference
                continue
            name, logo, hardware = PLATFORM_ART[index]
            with Image.open(portraits / f"{name}.png") as source:
                portrait = source.convert("RGB")
            canvas = Image.new("RGB", SIZE, HEADER)
            character = ImageOps.fit(portrait, (350, 480), Image.Resampling.LANCZOS, centering=(.5, .32))
            mask = np.minimum(255, np.arange(350) * 255 // 52).astype("uint8")
            canvas.paste(character, (290, 0), Image.fromarray(np.tile(mask, (480, 1)), "L"))
            if hardware:
                stock_patch(canvas, reference, hardware)
            if index == 2:
                super_nintendo_branding(canvas, portraits)
            elif index == 3:
                stock_nes_hardware(canvas, reference)
                stock_nes_badge(canvas, reference)
            else:
                stock_patch(canvas, reference, logo, feather=10 if index == 7 else 28)
            frames[index] = canvas
        return frames

    def controls(self, draw, x, y, spacing, controls):
        for index, (key, action) in enumerate(controls):
            center = x + index * spacing
            if key == "D-pad":
                cross = ((-5,-15),(5,-15),(5,-5),(15,-5),(15,5),(5,5),
                         (5,15),(-5,15),(-5,5),(-15,5),(-15,-5),(-5,-5))
                draw.polygon([(center+dx,y+dy) for dx,dy in cross], fill=HEADER, outline=GOLD, width=2)
                draw.rounded_rectangle((center-2,y-2,center+2,y+2),2,fill=GOLD)
            else:
                draw.ellipse((center - 17, y - 17, center + 17, y + 17), fill=HEADER, outline=GOLD, width=2)
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
        self.controls(draw, 365, 405, 73, (("D-pad", "Move"), ("A", "Enter"), ("B", "Back"), ("L2", "Favorites")))
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
        self.controls(draw, 193, 405, 127, (("D-pad", "Move"), ("A", "Enter"), ("B", "Back")))
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
        self.controls(draw, 365, 405, 73, (("D-pad", "Move"), ("A", "Enter"), ("B", "Back"), ("L2", "Favorites")))
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
        base = Image.new("RGB", SIZE, HEADER)
        draw = self.heading(base, "Game Settings")
        draw.rectangle((344, 89, 540, 235), fill=PANEL, outline=EDGE, width=2)
        draw.rounded_rectangle((284, 263, 624, 475), radius=8, fill=PANEL, outline=EDGE, width=2)
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
        # The stock save/load routines paint 86x60 thumbnails from block 6's
        # origin at (+4,+3), with 104x75 spacing and a separate selection rim.
        _, _, _, left, top, _, _ = records[6]
        for row in range(2):
            for column in range(3):
                x, y = left + 4 + column * 104, top + 3 + row * 75
                painter.rectangle((x, y, x + 85, y + 59), fill=HEADER, outline=EDGE)
                painter.line((x + 38, y + 29, x + 47, y + 29), fill=INK, width=2)
        controls = base.copy()
        painter = ImageDraw.Draw(controls)
        # Leave the P1 circle blank. The frontend prints the player and
        # mapping names at positions from its original m_joysticktab.
        painter.ellipse((293, 318, 375, 400), fill=HEADER, outline=GOLD, width=2)
        for row, pair in enumerate((("L1", "R1"), ("X", "Y"), ("A", "B"))):
            for column, key in enumerate(pair):
                x, y = 388 + 112 * column, 281 + 54 * row
                painter.rounded_rectangle((x, y, x + 94, y + 43), radius=7, fill=HEADER, outline=EDGE)
                self.label(painter, (x + 12, y + 22), key, 16, GOLD)
        return variants + [slots, controls]


def update_list_controls(pack_path, font, output_path):
    """Update only the two existing list footers in a deployed New art pack."""
    art = LauncherArt(font, ())
    replacements = {}
    with STOCK["open_pack"](pack_path) as pack:
        for member in ("menu.raw", "search.raw"):
            raw = bytearray(pack.read(member))
            record = STOCK["sprite_records"](raw)[0]
            if record[1:] != (640, 480, 0, 0, 640, 480):
                raise ValueError(f"unexpected canvas in {member}")
            base = read_sprite(raw, record)
            if base.getpixel((335, 385)) != base.getpixel((613, 449)):
                raise ValueError(f"missing expected Vesper controls panel in {member}")
            draw = ImageDraw.Draw(base)
            draw.rectangle((341, 383, 618, 454), fill=PANEL)
            art.controls(draw, 365, 405, 73, (("D-pad", "Move"), ("A", "Open"), ("B", "Back"),
                                             ("L2", "Favorites")))
            off = record[0]
            pixels = np.asarray(base.crop((341,383,619,455)), dtype=np.uint16)
            r,g,b = np.moveaxis(pixels,-1,0)
            encoded = (((r>>3)<<11)|((g>>2)<<5)|(b>>3)).astype("<u2")
            for y, row in enumerate(encoded, 383):
                start = off+2*(y*640+341)
                raw[start:start+2*len(row)] = row.tobytes()
            replacements[member] = raw
        write_pack(output_path, pack, replacements)


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
    parser.add_argument("--platform-portraits", type=Path, help="reviewed PNGs named for the replacement platforms")
    args = parser.parse_args()
    art = LauncherArt(args.font, scenes_from_manifest(args.scene_manifest))
    args.output.mkdir()
    pack = args.output / "ui_en.bkp"
    with STOCK["open_pack"](args.stock_english) as stock:
        raw = {name: stock.read(name) for name in ("type.raw", "menu.raw", "setting.raw", "search.raw", "game.raw")}
        library = art.library(raw["menu.raw"])
        carousel = art.familiar_carousel(raw["type.raw"], args.platform_portraits) if args.platform_portraits else art.carousel()
        images = {
            "type.raw": carousel, "menu.raw": library, "setting.raw": art.settings(),
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
    for name, index, preview in (("type.raw", 2, "snes"), ("type.raw", 3, "nes"), ("type.raw", 17, "settings-tile"),
                                 ("setting.raw", 0, "settings"), ("search.raw", 0, "search"),
                                 ("game.raw", 0, "pause")):
        STOCK["preview_png"](updated[name], STOCK["sprite_records"](updated[name])[index],
                             args.output / f"{preview}.png")
    for index, preview in ((6, "save-slots"), (7, "controls")):
        records = STOCK["sprite_records"](updated["game.raw"])
        frame = read_sprite(updated["game.raw"], records[0])
        selected = 3 if index == 6 else 5
        for block in (selected, index):
            frame.paste(read_sprite(updated["game.raw"], records[block]), records[block][3:5])
        frame.save(args.output / f"{preview}.png")
    overview = Image.new("RGB", (960, 900))
    for index, frame in enumerate(images["type.raw"]):
        row, column = divmod(index, 4)
        overview.paste(frame.resize((240, 180), Image.Resampling.LANCZOS), (column * 240, row * 180))
    overview.save(args.output / "carousel.png")
    print(f"{pack}: {sum(map(len, images.values()))} sprites, {pack.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
