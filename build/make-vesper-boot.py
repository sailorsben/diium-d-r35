"""Author Vesper boot artwork and replace only the known ELF's ZIP data span.

Requires the owner's exact stock showlogo, never downloads/distributes it.
Public outputs contain our artwork/schema only; the patched executable remains
private. Stock instructions, allocation and handoff stay
byte-identical. Pillow is a build-time dependency only.
"""
from pathlib import Path
from hashlib import sha256
import argparse, array, io, json, struct, sys, zipfile
from PIL import Image, ImageDraw

STOCK_SHA = '436d8018808b150c926274575a195f664e61db646f44713371019e9ae10caf3b'
START, END = 0x7180, 0x29bf4
CAPACITY = END - START
ARTWORK = Path(__file__).resolve().parent.parent / 'releases/vesper-boot-1/artwork.png'

def artwork(source, phase=None):
    # Imagegen supplies the composed art. Device-size conversion and the
    # code-native loading dots have their own bounded sprite rectangle.
    im = Image.open(source).convert('RGB').resize((640,480),Image.Resampling.LANCZOS)
    if phase is not None:
        draw=ImageDraw.Draw(im)
        for i in range(3):
            draw.ellipse((309+i*9,232,312+i*9,235),
                         fill=(98,203,204) if (phase//3)%3==i else (16,52,53))
    return im

def rgb565(image):
    pixels=array.array('H', ((r>>3)<<11|(g>>2)<<5|(b>>3) for r,g,b in image.getdata()))
    if sys.byteorder != 'little': pixels.byteswap()
    return pixels.tobytes()

def packed_zip(raw, padding):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:
        for name,data,method in [('ui.raw',raw,zipfile.ZIP_DEFLATED),
                                 ('.padding',b'\0'*padding,zipfile.ZIP_STORED)]:
            info=zipfile.ZipInfo(name,(2026,10,9,0,0,0));info.compress_type=method
            z.writestr(info,data,compresslevel=9)
    return out.getvalue()

def make(stock, output, private_output, source):
    original=stock.read_bytes(); assert sha256(original).hexdigest()==STOCK_SHA
    with zipfile.ZipFile(io.BytesIO(original[START:END])) as z:
        assert z.namelist()==['ui.raw']; old=z.read('ui.raw')
    assert struct.unpack_from('<IIHHHH',old)==(304,31457920,0,0,640,480) and len(old)==1476592
    # Full static artwork plus tiny loading-dot sprites avoids recompressing
    # ornate feathers eighteen times beyond the embedded fixed-size ZIP span.
    rectangles=[(0,0,640,480)]+[(306,229,334,239)]*18
    records=[];offset=304
    for x,y,x2,y2 in rectangles:
        records.append((offset,31457920,x,y,x2,y2));offset+=(x2-x)*(y2-y)*2
    assert offset<0x2ad91c # actual joytest allocation
    raw=bytearray(offset)
    for i,record in enumerate(records):struct.pack_into('<IIHHHH',raw,i*16,*record)
    background=artwork(source); frames=[]
    for i,(offset,resolution,x,y,x2,y2) in enumerate(records):
        assert resolution==31457920 and 0<=x<x2<=640 and 0<=y<y2<=480
        image=background if i==0 else artwork(source,i-1)
        pixels=rgb565(image.crop((x,y,x2,y2)))
        assert offset+len(pixels)==(records[i+1][0] if i<18 else len(raw))
        raw[offset:offset+len(pixels)]=pixels
        if i: frames.append(image)
    first=packed_zip(raw,0); assert len(first)<=CAPACITY
    encoded=packed_zip(raw,CAPACITY-len(first));assert len(encoded)==CAPACITY
    with zipfile.ZipFile(io.BytesIO(encoded)) as z:
        assert z.read('ui.raw')==raw and z.testzip() is None
    patched=original[:START]+encoded+original[END:]
    assert len(patched)==len(original) and patched[:START]==original[:START] and patched[END:]==original[END:]
    output.mkdir(parents=True,exist_ok=True);private_output.mkdir(parents=True,exist_ok=True)
    (output/'logo.zip').write_bytes(encoded);(output/'ui.raw').write_bytes(raw)
    background.save(output/'preview.png')
    frames[0].save(output/'preview.gif',save_all=True,append_images=frames[1:],duration=90,loop=0)
    (private_output/'showlogo-vesper').write_bytes(patched)
    result={'version':'1','stock_sha256':STOCK_SHA,'zip_start':START,'zip_end':END,
            'bytes':len(patched),'stock_code_and_all_outside_zip_unchanged':True,
            'sprite_geometry':'640x480 background; eighteen 28x10 loading-dot crops',
            'frames':18,'width':640,'height':480,
            'uncompressed_bytes':len(raw),'stock_allocation_bytes':0x2ad91c,
            'logo_zip_sha256':sha256(encoded).hexdigest(),'ui_raw_sha256':sha256(raw).hexdigest(),
            'artwork_sha256':sha256(source.read_bytes()).hexdigest(),
            'patched_showlogo_sha256':sha256(patched).hexdigest(),
            'physical_boot_appearance':'pending','stock_loader_and_sprite_check':'pending'}
    (output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock',type=Path,required=True)
    p.add_argument('--output',type=Path,default=Path('releases/vesper-boot-1'))
    p.add_argument('--private-output',type=Path,default=Path('build/vesper-boot-private'))
    p.add_argument('--artwork',type=Path,default=ARTWORK);a=p.parse_args()
    make(a.stock,a.output,a.private_output,a.artwork)
