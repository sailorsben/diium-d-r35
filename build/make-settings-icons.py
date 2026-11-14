"""Rasterize symmetrical coverage masks and full-size Settings icons."""

from math import cos, sin, radians, floor, ceil, hypot
from pathlib import Path


SIZE = 36
SAMPLES = 4
SIDE = SIZE * SAMPLES
UNIT = 1.25
INSET = (SIZE - 24 * UNIT) / 2


class Mask:
    def __init__(self):
        self.pixels = bytearray(SIDE * SIDE)

    def paint(self, bounds, contains):
        left, top, right, bottom = bounds
        for y in range(max(0, floor(top*SAMPLES)), min(SIDE, ceil(bottom*SAMPLES))):
            for x in range(max(0, floor(left*SAMPLES)), min(SIDE, ceil(right*SAMPLES))):
                if contains((x+.5)/SAMPLES, (y+.5)/SAMPLES):
                    self.pixels[y*SIDE+x] = 1

    @staticmethod
    def point(x, y):
        return INSET+x*UNIT, INSET+y*UNIT

    def path(self, *points, width=1.8):
        radius = width*UNIT/2
        scaled = [self.point(*point) for point in points]
        for (x0, y0), (x1, y1) in zip(scaled, scaled[1:]):
            dx, dy = x1-x0, y1-y0
            length2 = dx*dx + dy*dy
            if not length2:
                continue

            def on_stroke(x, y):
                t = max(0, min(1, ((x-x0)*dx+(y-y0)*dy)/length2))
                return (x-x0-t*dx)**2 + (y-y0-t*dy)**2 <= radius**2

            self.paint((min(x0,x1)-radius, min(y0,y1)-radius,
                        max(x0,x1)+radius, max(y0,y1)+radius), on_stroke)

    def arc(self, cx, cy, rx, ry, start=0, end=360, width=1.8):
        steps = ceil(abs(end-start)/10)
        angles = [radians(start+(end-start)*i/steps) for i in range(steps+1)]
        self.path(*[(cx+rx*cos(a),cy+ry*sin(a)) for a in angles], width=width)

    def dot(self, cx, cy, rx, ry=None):
        ry = rx if ry is None else ry
        x, y = self.point(cx, cy)
        rx, ry = rx*UNIT, ry*UNIT
        self.paint((x-rx, y-ry, x+rx, y+ry),
                   lambda px, py: ((px-x)/rx)**2 + ((py-y)/ry)**2 <= 1)

    def polygon(self, *points):
        points = [self.point(*point) for point in points]
        xs, ys = zip(*points)
        edges = list(zip(points[-1:] + points[:-1], points))

        def inside(x, y):
            return sum((y0>y) != (y1>y) and x < x0+(x1-x0)*(y-y0)/(y1-y0)
                       for (x0,y0),(x1,y1) in edges) % 2

        self.paint((min(xs), min(ys), max(xs), max(ys)), inside)

    def tile(self, inset):
        radius = 8 - inset
        edge = SIZE - inset

        def inside(x, y):
            dx = max(8-x, x-(SIZE-8), 0)
            dy = max(8-y, y-(SIZE-8), 0)
            return hypot(dx, dy) <= radius

        self.paint((inset,inset,edge,edge), inside)

    def packed(self, row_count=SIZE):
        area = SAMPLES**2
        rows = []
        for y in range(0, row_count*SAMPLES, SAMPLES):
            coverage = []
            for x in range(0, SIDE, SAMPLES):
                count = sum(sum(self.pixels[i*SIDE+x:i*SIDE+x+SAMPLES])
                            for i in range(y,y+SAMPLES))
                coverage.append((count*3+area//2)//area)
            rows.append([
                a*64+b*16+c*4+d for a,b,c,d in
                zip(coverage[::4],coverage[1::4],coverage[2::4],coverage[3::4])
            ])
        return rows


def brightness(icon):
    icon.arc(12,12,4.5,4.5)
    for angle in range(0,360,45):
        x, y = cos(radians(angle)), sin(radians(angle))
        icon.path((12+8*x,12+8*y),(12+10.6*x,12+10.6*y))


def theme(icon):
    icon.arc(12,12,9.7,9.7,46,370)
    icon.path((21.55,13.69),(20.8,16),(18.9,17),(17,17),(16.6,18.4),(17.8,19.0))
    for x,y in [(6.5,11),(9.5,6.8),(14.6,6.3),(18.3,9.3)]:
        icon.dot(x,y,1.28)


def battery(icon):
    icon.path((4,6),(18,6),(19.5,7.5),(19.5,16.5),(18,18),(4,18),
              (2.5,16.5),(2.5,7.5),(4,6))
    icon.path((22,10),(22,14))
    for x in (6,10,14):
        icon.path((x,9.5),(x,14.5),width=1.9)


def speaker(icon):
    icon.polygon((2,9),(6,9),(11,4.5),(11,19.5),(6,15),(2,15))


def volume(icon):
    speaker(icon)
    icon.arc(10,12,6,6,-44,44)
    icon.arc(10,12,11,10,-47,47)


def music(icon):
    icon.polygon((7,5),(20,2),(20,6),(7,9))
    icon.path((7.8,7),(7.8,17),width=1.9)
    icon.path((19.1,4),(19.1,14.5),width=1.9)
    icon.dot(5.5,17.8,3.2,2.5)
    icon.dot(16.8,15.3,3.2,2.5)


def frame_skip(icon):
    icon.polygon((2.8,5),(11.6,12),(2.8,19))
    icon.polygon((11.5,5),(20.3,12),(11.5,19))
    icon.path((21.8,5.5),(21.8,18.5))


def language(icon):
    icon.arc(12,12,9.5,9.5)
    icon.arc(12,12,4.2,9.5,width=1.5)
    icon.path((3,12),(21,12),width=1.5)


def power(icon):
    icon.arc(12,12.7,8.7,8.7,-49,229,width=2)
    icon.path((12,2.3),(12,11.9),width=2.2)


def reset(icon):
    icon.arc(12,12,8.7,8.7,-91,219,width=1.9)
    icon.path((2.1,6.8),(5.2,6.5),(5.6,9.9),width=1.9)


def mute(icon):
    speaker(icon)
    icon.path((15,9),(21,15))
    icon.path((21,9),(15,15))


ICONS = (brightness, theme, battery, volume, music, frame_skip, language, power, reset, mute)


def write_header(destination):
    with destination.open("w", encoding="ascii", newline="\n") as out:
        out.write("/* Generated by make-settings-icons.py. Four 2-bit coverage values per byte. */\n")
        out.write(f"enum {{ SETTINGS_ICON_SIZE={SIZE} }};\n")
        for index, draw in enumerate(ICONS):
            out.write(f"#define SETTINGS_MASK_{draw.__name__.upper()} {index}\n")

        def array(name, masks, rows):
            out.write(f"static const uint8_t {name}[][{rows}][SETTINGS_ICON_SIZE/4]={{\n")
            for label, mask in masks:
                out.write(f"    {{ /* {label} */\n")
                for row in mask.packed(rows):
                    out.write("        {" + ",".join(f"0x{p:02x}" for p in row) + "},\n")
                out.write("    },\n")
            out.write("};\n")

        tiles = [Mask(), Mask()]
        for inset, tile in enumerate(tiles):
            tile.tile(inset)
        array("settings_tiles", zip(("outer", "inner"), tiles), SIZE//2)
        masks = []
        for draw in ICONS:
            mask = Mask()
            draw(mask)
            masks.append((draw.__name__, mask))
        array("settings_masks", masks, SIZE)
        # 75 ms, rising two-note confirmation. The move sound remains separate.
        out.write("static const int16_t settings_confirm_pcm[][2]={\n")
        for i in range(3308):
            t=i/44100
            j=i if i<1433 else i-1433
            end=1433 if i<1433 else 1875
            envelope=min(1,j/110,(end-j)/375)*(1-j/end)**2
            frequency=659.255 if i<1433 else 880
            sample=round(5200*envelope*(sin(6.283185307*frequency*t)+.17*sin(12.566370614*frequency*t)))
            out.write(f"    {{{sample},{sample}}},\n")
        out.write("};\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("header", type=Path)
    write_header(parser.parse_args().header)
