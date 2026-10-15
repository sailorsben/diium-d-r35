"""Animate the existing wing artwork through the unchanged stock sprite path.

Build assets and an offline-only private executable. Never accesses a card or
firmware. Keep the first release and its proofs immutable.
"""
from pathlib import Path
from hashlib import sha256
import argparse
import importlib.util
import json
import math
import struct
import subprocess
import os

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def native_preview(image):
    # Show the actual RGB565 quantization in exported previews.
    r, g, b = image.split()
    return Image.merge('RGB', (r.point(lambda v: (v >> 3) * 255 // 31),
                              g.point(lambda v: (v >> 2) * 255 // 63),
                              b.point(lambda v: (v >> 3) * 255 // 31)))


def main(stock, output, private):
    spec = importlib.util.spec_from_file_location('original_packer', ROOT / 'build/make-vesper-boot.py')
    pack = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pack)
    original = stock.read_bytes()
    assert sha256(original).hexdigest() == pack.STOCK_SHA
    source = ROOT / 'releases/vesper-boot-1/artwork.png'
    background = pack.artwork(source)
    # Only the feather band changes. The stock loop repaints the full background
    # before each sprite, so a moving rectangle cannot leave a previous trail.
    rectangles = [(0, 0, 640, 480)]
    crops = [background]
    for frame in range(18):
        center = 347 - frame * 18
        y0, y1 = max(36, center - 17), min(360, center + 18)
        rect = (154, y0, 486, y1)
        crop = background.crop(rect)
        pixels = crop.load()
        for y in range(crop.height):
            # A broad soft crest followed by a smaller afterglow, clipped to
            # existing cyan feathers. Black and the heart opening stay black.
            distance = y + y0 - center
            crest = math.exp(-0.5 * (distance / 6.0) ** 2)
            wake = 0.22 * math.exp(-0.5 * ((distance - 8) / 5) ** 2)
            envelope = min(1.0, (frame + 1) / 2, (18 - frame) / 2)
            light = (crest + wake) * envelope
            for x in range(crop.width):
                r, g, b = pixels[x, y]
                feather = min(1.0, max(0.0, (max(g, b) - r - 10) / 65))
                strength = light * feather * 0.82
                pixels[x, y] = tuple(min(255, int(v + (target - v) * strength))
                                     for v, target in zip((r, g, b), (150, 255, 255)))
        rectangles.append(rect)
        crops.append(crop)
    offset = 304
    records = []
    for rect in rectangles:
        x0, y0, x1, y1 = rect
        records.append((offset, 31457920, *rect))
        offset += (x1 - x0) * (y1 - y0) * 2
    assert offset < 0x2ad91c
    raw = bytearray(offset)
    for i, (record, crop) in enumerate(zip(records, crops)):
        struct.pack_into('<IIHHHH', raw, i * 16, *record)
        pixels = pack.rgb565(crop)
        end = records[i + 1][0] if i < 18 else len(raw)
        assert record[0] + len(pixels) == end
        raw[record[0]:end] = pixels
    first = pack.packed_zip(raw, 0)
    assert len(first) <= pack.CAPACITY, (len(first), pack.CAPACITY)
    encoded = pack.packed_zip(raw, pack.CAPACITY - len(first))
    assert len(encoded) == pack.CAPACITY
    patched = original[:pack.START] + encoded + original[pack.END:]
    assert len(patched) == len(original)
    assert patched[:pack.START] == original[:pack.START] and patched[pack.END:] == original[pack.END:]
    output.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)
    (output / 'ui.raw').write_bytes(raw)
    (output / 'logo.zip').write_bytes(encoded)
    (private / 'showlogo-vesper-wings').write_bytes(patched)
    frames = []
    for rect, crop in zip(rectangles[1:], crops[1:]):
        frame = background.copy()
        frame.paste(crop, rect[:2])
        frames.append(native_preview(frame))
    # One common palette avoids frame-to-frame GIF palette flicker. This is a
    # review artifact; the native payload remains RGB565 with no GIF decoder.
    atlas = Image.new('RGB', (640, 480 * len(frames)))
    for i, frame in enumerate(frames):
        atlas.paste(frame, (0, i * 480))
    palette = atlas.quantize(colors=256)
    gif = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    gif[0].save(output / 'preview.gif', save_all=True, append_images=gif[1:],
                duration=90, loop=0, disposal=2, optimize=False)
    frames[8].save(output / 'preview.png')
    contact = Image.new('RGB', (960, 720))
    for cell, i in enumerate([0, 2, 4, 6, 8, 10, 12, 14, 17]):
        mini = frames[i].resize((320, 240), Image.Resampling.LANCZOS)
        ImageDraw.Draw(mini).text((8, 8), str(i + 1), fill=(160, 230, 230))
        contact.paste(mini, ((cell % 3) * 320, (cell // 3) * 240))
    contact.save(output / 'contact-sheet.png')
    # Actual vendor ZIP decoder and drawing routines, with guarded RAM buffers.
    command = (['wsl', '--exec', 'sh'] if os.name == 'nt' else ['sh']) + [
        'build/check-stock-boot.sh', (private / 'showlogo-vesper-wings').relative_to(ROOT).as_posix(),
        (output / 'ui.raw').relative_to(ROOT).as_posix()]
    run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr
    assert run.stdout.startswith('PASS exact stock OpenZipU/UnzipItem decode, 18 ShowSprite frames,')
    (output / 'stock-seam-check.log').write_text(run.stdout, encoding='utf-8', newline='\n')
    report = {
        'version': 'vesper-wings-2', 'effect': 'cyan feather light rising from the V tip to both wing tips',
        'frames': 18, 'preview_frame_ms': 90, 'physical_cadence_measured': False,
        'original_artwork_sha256': digest(source), 'stock_sha256': pack.STOCK_SHA,
        'stock_code_and_all_outside_zip_unchanged': True,
        'zip_bytes': len(encoded), 'zip_capacity': pack.CAPACITY,
        'compressed_content_and_headers_bytes': len(first), 'padding_bytes': pack.CAPACITY - len(first),
        'uncompressed_bytes': len(raw), 'stock_allocation_bytes': 0x2ad91c,
        'largest_extra_sprite_pixels': max((r[4] - r[2]) * (r[5] - r[3]) for r in records[1:]),
        'stock_background_pixels_per_frame': 640 * 480,
        'added_runtime_processes_or_decoders': 0, 'new_per_frame_shader_work': 0,
        'stock_loader_and_sprite_check': run.stdout.strip(),
        'preview_review': 'PENDING', 'physical_boot_appearance': 'PENDING',
        'card_access': False, 'firmware_staged': False,
        'private_patched_executable_sha256': digest(private / 'showlogo-vesper-wings'),
        'assets': {n: digest(output / n) for n in ['ui.raw', 'logo.zip', 'preview.gif', 'preview.png', 'contact-sheet.png']},
        'sources': {n: digest(ROOT / n) for n in ['build/make-vesper-wings.py', 'build/make-vesper-boot.py',
                                                     'build/check-stock-boot.c', 'build/check-stock-boot.sh']}}
    (output / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', required=True, type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'releases/vesper-wings-2')
    parser.add_argument('--private-output', type=Path, default=ROOT / 'build/vesper-wings-private')
    args = parser.parse_args()
    main(args.stock.resolve(), args.output.resolve(), args.private_output.resolve())
