"""Render the D-R35 Home and game list button legends."""

import argparse
from pathlib import Path
import runpy

import numpy as np
from PIL import Image, ImageDraw, ImageFont


PANEL = "#101c2c"
TEXT = "#f1f5fa"
HOME_PROMPTS = (("START", "Settings"), ("SELECT", "Favorites"), ("X", "Search"),
                ("Y", "Recent"), ("A", "Open"), ("ESC", "Power"))
LIST_PROMPTS = (("D-pad", "Move"), ("A", "Open"), ("B", "Back"), ("L2", "Favorites"))
GAME_FOOTER = (324, 370, 628, 466)
SCALE = 4


class Footer:
    def __init__(self, font, bold):
        self.font = font
        self.bold = bold

    def lettering(self, size, bold=False):
        return ImageFont.truetype(str(self.bold if bold else self.font), size*SCALE)

    def cap_width(self, key, height):
        if key == "D-pad" or len(key) == 1:
            return height
        if key == "L2":
            return height+8
        metrics = self.lettering(11, True)
        return round(metrics.getlength(key)/SCALE)+10

    def cap(self, canvas, x, y, key, height):
        width = self.cap_width(key, height)
        accent = key == "A"
        edge = "#ffd782" if accent else "#7690a7"
        top = (255, 228, 163) if accent else (64, 91, 115)
        bottom = (215, 155, 60) if accent else (33, 53, 72)
        w, h = width*SCALE, height*SCALE
        cap = Image.new("RGBA", (w, h))
        draw = ImageDraw.Draw(cap)
        for row in range(h):
            fade = (row/(h-1))**0.68
            color = tuple(round(a+(b-a)*fade) for a, b in zip(top, bottom))
            if row >= h-3*SCALE:
                color = (184, 121, 36) if accent else (24, 42, 60)
            draw.line((0, row, w-1, row), fill=color)

        mask = Image.new("L", (w, h))
        silhouette = ImageDraw.Draw(mask)
        if key == "D-pad":
            cut, bevel = round(h*.30), round(h*.04)
            points = ((cut+bevel, 0), (w-cut-bevel-1, 0), (w-cut-1, bevel),
                      (w-cut-1, cut), (w-bevel-1, cut), (w-1, cut+bevel),
                      (w-1, h-cut-bevel-1), (w-bevel-1, h-cut-1), (w-cut-1, h-cut-1),
                      (w-cut-1, h-bevel-1), (w-cut-bevel-1, h-1), (cut+bevel, h-1),
                      (cut, h-bevel-1), (cut, h-cut-1), (bevel, h-cut-1), (0, h-cut-bevel-1),
                      (0, cut+bevel), (bevel, cut), (cut, cut), (cut, bevel))
            silhouette.polygon(points, fill=255)
            draw.line(points+(points[0],), fill=edge, width=SCALE+1, joint="curve")
            pivot = 3*SCALE
            draw.ellipse((w//2-pivot,h//2-pivot,w//2+pivot,h//2+pivot),
                         fill="#182b3e", outline=edge, width=SCALE)
        else:
            radius = (height//2 if len(key) == 1 or key in ("START", "SELECT") else 6)*SCALE
            bounds = (0,0,w-1,h-1)
            silhouette.rounded_rectangle(bounds,radius,fill=255)
            draw.rounded_rectangle(bounds,radius,outline=edge,width=SCALE)
            size = (17 if height>=30 else 16) if len(key) == 1 else (16 if key == "L2" else 11)
            draw.text((w//2,(h-SCALE)//2), key, font=self.lettering(size,True),
                      fill="#251909" if accent else "#f6f9fc", anchor="mm")
        cap.putalpha(mask)
        canvas.alpha_composite(cap, (x*SCALE,y*SCALE))

    def home(self):
        canvas = Image.new("RGBA", (640*SCALE, 45*SCALE), PANEL)
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((0,0,640*SCALE-1,SCALE-1),fill="#314965")
        label_font = self.lettering(17)
        heights = [25 if len(key)==1 else 22 for key,_ in HOME_PROMPTS]
        cap_widths = [self.cap_width(key,height) for (key,_),height in zip(HOME_PROMPTS,heights)]
        widths = [chip+6+round(label_font.getlength(label)/SCALE)
                  for chip,(_,label) in zip(cap_widths,HOME_PROMPTS)]
        free = 606-sum(widths)
        if free < 5*6:
            raise ValueError("Home shortcuts do not fit with readable spacing")
        for index, ((key,label),height,width) in enumerate(zip(HOME_PROMPTS,heights,cap_widths)):
            x = 17+sum(widths[:index])+round(index*free/5)
            self.cap(canvas,x,(45-height)//2,key,height)
            draw.text(((x+width+6)*SCALE,23*SCALE),label,font=label_font,fill=TEXT,anchor="lm")
        return canvas.resize((640,45),Image.Resampling.LANCZOS).convert("RGB")

    def games(self, background):
        width, height = background.size
        canvas = background.convert("RGBA").resize((width*SCALE,height*SCALE))
        draw = ImageDraw.Draw(canvas)
        draw.rounded_rectangle((0,0,width*SCALE-1,height*SCALE-1),9*SCALE,
                               fill=PANEL,outline="#314965",width=SCALE)
        for index,(key,label) in enumerate(LIST_PROMPTS):
            center = 42+73*index
            self.cap(canvas,center-self.cap_width(key,32)//2,20,key,32)
            draw.text((center*SCALE,69*SCALE),label,font=self.lettering(16),fill=TEXT,anchor="mm")
        return canvas.resize((width,height),Image.Resampling.LANCZOS).convert("RGB")


def encode(image):
    r,g,b = np.moveaxis(np.asarray(image,dtype=np.uint16),-1,0)
    return (((r>>3)<<11)|((g>>2)<<5)|(b>>3)).astype("<u2").tobytes()


def build_assets(home, pack, font, bold, output):
    art = runpy.run_path(str(Path(__file__).with_name("make-stock-shell-art.py")))
    reader = art["STOCK"]
    footer = Footer(font,bold)
    grid = home.read_bytes()
    if len(grid) != 640*480*2+12*320*30*2+4 or grid[-4:] != b"D354":
        raise ValueError("Expected the reviewed D354 Home grid")
    grid = grid[:435*1280]+encode(footer.home())+grid[480*1280:]
    (output/"home-grid.rgb565").write_bytes(grid)

    replacements = {}
    left,top,right,bottom = GAME_FOOTER
    with reader["open_pack"](pack) as original:
        for name in ("menu.raw","search.raw"):
            member = bytearray(original.read(name))
            record = reader["sprite_records"](member)[0]
            if record[1:] != (640,480,0,0,640,480):
                raise ValueError(f"Unexpected game list canvas in {name}")
            frame = art["read_sprite"](member,record)
            panel = footer.games(frame.crop(GAME_FOOTER))
            encoded = encode(panel)
            stride = (right-left)*2
            for row in range(bottom-top):
                start = record[0]+(top+row)*1280+left*2
                member[start:start+stride] = encoded[row*stride:(row+1)*stride]
            replacements[name] = member
        result = output/"ui_en.bkp"
        art["write_pack"](result,original,replacements)
        with reader["open_pack"](result) as built:
            if built.testzip() or built.namelist()!=original.namelist():
                raise ValueError("Game list pack validation failed")
            for name in built.namelist():
                expected = replacements[name] if name in replacements else original.read(name)
                if built.read(name)!=expected:
                    raise ValueError(f"Pack member did not match: {name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("home","pack","font","bold","output"):
        parser.add_argument(argument,type=Path)
    args = parser.parse_args()
    args.output.mkdir()
    build_assets(args.home,args.pack,args.font,args.bold,args.output)
