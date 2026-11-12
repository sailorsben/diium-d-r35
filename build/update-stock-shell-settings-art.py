"""Build the six-row Settings artwork from the two reviewed launcher themes."""

import argparse
import io
from pathlib import Path
import runpy
import struct
import zipfile

import numpy as np
from PIL import Image, ImageDraw


ART = runpy.run_path(str(Path(__file__).with_name('make-stock-shell-art.py')))
STOCK = ART['STOCK']
ROW_BOXES = ((90, 339, 550, 378), (90, 382, 550, 421))
VALUES = (('Off', 'Auto'), ('New', 'Classic'))
LABELS = ('Frame Skip', 'Theme')


def extend_classic_panel(canvas, art):
    """Use the original panel, bezel and button art for the taller layout."""
    stock = canvas.copy()
    art.label(ImageDraw.Draw(canvas), (141, 24), 's', 30, '#ffffff')
    panel = stock.crop((31, 328, 609, 343))
    canvas.paste(panel.resize((578, 86), Image.Resampling.NEAREST), (31, 328))
    canvas.paste(stock.crop((30, 343, 610, 365)), (30, 414))

    # Remove the old control legend from the metal using adjacent pixels on
    # the same scanlines. Reuse its bezel and move the buttons below the rows.
    metal = np.asarray(stock.crop((30, 365, 610, 445))).copy()
    for left, top, right, bottom in ((80, 389, 120, 419), (167, 367, 222, 432),
                                     (293, 367, 348, 432), (419, 367, 475, 432),
                                     (525, 389, 565, 419)):
        l, t, r, b = left-30, top-365, right-30, bottom-365
        fraction = (np.arange(1, r-l+1) / (r-l+1))[None, :, None]
        metal[t:b, l:r] = (metal[t:b, l-1:l]*(1-fraction) + metal[t:b, r:r+1]*fraction).round()
    mask = Image.new('L', (580, 80))
    ImageDraw.Draw(mask).polygon(((1, 0), (578, 0), (578, 51), (558, 78),
                                  (26, 78), (1, 51)), fill=255)
    canvas.paste(Image.fromarray(metal).resize((580, 42), Image.Resampling.LANCZOS), (30, 436),
                 mask.resize((580, 42), Image.Resampling.NEAREST))

    circle = Image.new('L', (42, 42))
    ImageDraw.Draw(circle).ellipse((0, 0, 41, 41), fill=255)
    circle = circle.resize((31, 31), Image.Resampling.LANCZOS)
    for x, center, label in ((108, 193, 'Select'), (245, 320, 'Change'), (382, 447, 'Back')):
        button = stock.crop((center-21, 368, center+21, 410))
        canvas.paste(button.resize((31, 31), Image.Resampling.LANCZOS), (x, 441), circle)
        art.label(ImageDraw.Draw(canvas), (x+39, 456), label, 19, '#ffffff')


def settings_art(original, font, classic):
    records = STOCK['sprite_records'](original)
    if [r[3:] for r in records] != [(0, 0, 640, 480),
                                    *((90, y, 550, y + 54) for y in (134, 184, 234, 284))]:
        raise ValueError('Unexpected stock Settings geometry')

    art = ART['LauncherArt'](font, [])
    canvas = ART['read_sprite'](original, records[0])
    draw = ImageDraw.Draw(canvas)
    accent = '#ffffff' if classic else ART['GOLD']
    panel = ART['PANEL']
    edge = ART['EDGE']
    focused = '#163739' if classic else ART['SELECTED']
    ink = '#ffffff' if classic else ART['INK']
    if classic:
        extend_classic_panel(canvas, art)
    else:
        draw.rectangle((62, 106, 577, 445), fill=panel)
        draw.rounded_rectangle((62, 94, 577, 452), radius=10, fill=panel, outline=edge, width=2)

    def main_row(target, index, selected=False):
        painter = ImageDraw.Draw(target)
        y = 161 + index * 50
        painter.rounded_rectangle((96, y-19, 544, y+19), radius=6,
                                  fill=focused if selected else panel,
                                  outline=accent if selected else edge, width=2 if selected else 1)
        art.settings_row(painter, ART['SETTINGS'][index], index, y)

    def option_row(target, index, value, selected=False):
        painter = ImageDraw.Draw(target)
        left, top, right, bottom = ROW_BOXES[index]
        y = (top + bottom) // 2
        background = focused if selected else panel
        if classic:
            if selected:
                painter.rounded_rectangle((left+8, top+2, right-8, bottom-3), radius=5,
                                          fill=focused, outline='#afc8ca', width=2)
        else:
            painter.rounded_rectangle((left+6, top+1, right-6, bottom-2), radius=6,
                                      fill=background,
                                      outline=accent if selected else edge, width=2 if selected else 1)
        if index == 0:
            for x in (124, 133):
                painter.line(((x, y-7), (x+8, y), (x, y+7)), fill=accent, width=2)
        else:
            painter.rounded_rectangle((129, y-9, 144, y+5), radius=2, outline=accent, width=2)
            fill=target.getpixel((124,y)) if classic and not selected else background
            painter.rounded_rectangle((123, y-4, 138, y+10), radius=2, fill=fill,
                                      outline=accent, width=2)
        art.label(painter, (178, y), LABELS[index], 23, ink)
        art.label(painter, (516, y), VALUES[index][value], 22, accent, anchor='rm')

    if not classic:
        for index in range(4):
            main_row(canvas, index)
    for index, value in enumerate((0, int(classic))):
        option_row(canvas, index, value)
    if not classic:
        draw = ImageDraw.Draw(canvas)
        for x, key, text in ((105, 'D-pad', 'Select'), (255, 'A', 'Change'), (399, 'B', 'Back / apply theme')):
            art.label(draw, (x, 435), key, 16, accent)
            advance = art.type(16).getlength(key) + 10
            art.label(draw, (x + advance, 435), text, 16, ink)

    frames = [(records[0][3:], canvas)]
    for index in range(4):
        frame = canvas.copy()
        record = records[index+1]
        if classic:
            frame.paste(ART['read_sprite'](original, record), record[3:5])
        else:
            main_row(frame, index, selected=True)
        frames.append((record[3:], frame))
    for index in range(2):
        for selected in (False, True):
            for value in (0, 1):
                frame = canvas.copy()
                option_row(frame, index, value, selected=selected)
                frames.append((ROW_BOXES[index], frame))

    headers, pixels = bytearray(), bytearray()
    for box, frame in frames:
        headers.extend(struct.pack('<I6H', len(frames)*16 + len(pixels), 640, 480, *box))
        red, green, blue = np.moveaxis(np.asarray(frame.crop(box), dtype=np.uint16), -1, 0)
        pixels.extend((((red >> 3) << 11) | ((green >> 2) << 5) | (blue >> 3)).astype('<u2').tobytes())
    result = bytes(headers + pixels)
    assert [r[3:] for r in STOCK['sprite_records'](result)] == [box for box, _ in frames]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('new_pack', 'classic_pack', 'font', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    args.output.mkdir()
    packs = {}
    for classic, source in ((False, args.new_pack), (True, args.classic_pack)):
        name = 'classic' if classic else 'new'
        path = args.output / ('ui_classic.bkp' if classic else 'ui_en.bkp')
        with STOCK['open_pack'](source) as stock:
            raw = settings_art(stock.read('setting.raw'), args.font, classic)
            if classic:
                temporary = io.BytesIO()
                with zipfile.ZipFile(temporary, 'w') as seed:
                    seed.writestr('setting.raw', b'')
                with zipfile.ZipFile(temporary) as seed:
                    ART['write_pack'](path, seed, {'setting.raw': raw})
            else:
                ART['write_pack'](path, stock, {'setting.raw': raw})
            with STOCK['open_pack'](path) as pack:
                assert pack.testzip() is None and pack.read('setting.raw') == raw
                assert pack.namelist() == (['setting.raw'] if classic else stock.namelist())
                for item in pack.namelist():
                    if item != 'setting.raw':
                        assert pack.read(item) == stock.read(item), item
        path_raw = args.output / f'setting-{name}.raw'
        path_raw.write_bytes(raw)
        STOCK['preview_png'](raw, STOCK['sprite_records'](raw)[0], args.output / f'settings-{name}.png')
        packs[name] = path
    for name, path in packs.items():
        print(f'{name}: {path} ({path.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
