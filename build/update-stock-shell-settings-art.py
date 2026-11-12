"""Build the six-row Settings artwork from the two reviewed launcher themes."""

import argparse
import io
from pathlib import Path
import runpy
import struct
import zipfile

import numpy as np
from PIL import ImageDraw


ART = runpy.run_path(str(Path(__file__).with_name('make-stock-shell-art.py')))
STOCK = ART['STOCK']
ROW_BOXES = ((90, 339, 550, 378), (90, 382, 550, 421))
VALUES = (('Off', 'Auto'), ('New', 'Classic'))
LABELS = ('Frame Skip', 'Theme')


def settings_art(original, font, classic):
    records = STOCK['sprite_records'](original)
    if [r[3:] for r in records] != [(0, 0, 640, 480),
                                    *((90, y, 550, y + 54) for y in (134, 184, 234, 284))]:
        raise ValueError('Unexpected stock Settings geometry')

    art = ART['LauncherArt'](font, [])
    canvas = ART['read_sprite'](original, records[0])
    draw = ImageDraw.Draw(canvas)
    accent = '#83f8ff' if classic else ART['GOLD']
    panel = '#101e32' if classic else ART['PANEL']
    edge = '#55818f' if classic else ART['EDGE']
    focused = '#204761' if classic else ART['SELECTED']
    ink = ART['INK']
    if classic:
        # Retain the original gradients and outer shell. The controls now
        # share one panel inside it, extending over the old button legend.
        for y in range(46):
            draw.line((0, y, 639, y), fill=canvas.getpixel((320, y)))
        art.label(draw, (32, 26), 'Settings', 30, ink)
        draw.polygon(((61, 116), (81, 99), (558, 99), (579, 118),
                      (579, 427), (561, 445), (80, 445), (61, 426)), fill=panel,
                     outline=accent, width=2)
        draw.rectangle((77, 356, 563, 435), fill=panel)
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
        painter.rounded_rectangle((left+6, top+1, right-6, bottom-2), radius=6,
                                  fill=focused if selected else panel,
                                  outline=accent if selected else edge, width=2 if selected else 1)
        art.label(painter, (178, y), LABELS[index], 23, ink)
        art.label(painter, (516, y), VALUES[index][value], 22, accent, anchor='rm')

    for index in range(4):
        main_row(canvas, index)
    for index, value in enumerate((0, int(classic))):
        option_row(canvas, index, value)
    draw = ImageDraw.Draw(canvas)
    for x, key, text in ((105, 'D-pad', 'Select'), (255, 'A', 'Change'), (399, 'B', 'Back / apply theme')):
        art.label(draw, (x, 435), key, 16, accent)
        advance = art.type(16).getlength(key) + 10
        art.label(draw, (x + advance, 435), text, 16, ink)

    frames = [(records[0][3:], canvas)]
    for index in range(4):
        frame = canvas.copy()
        main_row(frame, index, selected=True)
        frames.append((records[index+1][3:], frame))
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
