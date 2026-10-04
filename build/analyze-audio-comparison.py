"""Check captured FF3 resampling against an independent vectorized reference."""
from pathlib import Path
import json
import wave
import numpy as np
from PIL import Image, ImageDraw

base = Path(__file__).resolve().parent / 'audio-comparison'
native = np.fromfile(base/'plus-native/native.s16le', dtype='<i2').reshape(-1, 2)
adapted = np.fromfile(base/'plus-adapter/native.s16le', dtype='<i2').reshape(-1, 2)
expected_count = ((len(native)-1)*44100 + 32040-1)//32040
assert len(adapted) == expected_count
different = 0
for begin in range(0, len(adapted), 250000):
    end = min(begin+250000, len(adapted))
    position = np.arange(begin, end, dtype=np.int64)*32040
    index, phase = np.divmod(position, 44100)
    weighted = native[index].astype(np.int64)*(44100-phase[:,None]) + native[index+1].astype(np.int64)*phase[:,None]
    # C signed division truncates toward zero.
    reference = np.where(weighted < 0, -((-weighted)//44100), weighted//44100).astype('<i2')
    different += np.count_nonzero(reference != adapted[begin:end])
report = dict(native_stereo_samples=len(native), adapted_stereo_samples=len(adapted),
              expected_stereo_samples=expected_count, differing_channel_samples=int(different),
              captured_seconds=len(native)/32040,
              limitation='Checks sample conversion only; does not test physical audio timing or prove the native core has no audible clicks.')
(base/'resampler-analysis.json').write_text(json.dumps(report, indent=2)+'\n')
assert different == 0, report
for kind, samples, rate in [('plus-native',native,32040),('plus-adapter',adapted,44100)]:
    with wave.open(str(base/kind/'opening-45-to-90-seconds.wav'),'wb') as out:
        out.setnchannels(2);out.setsampwidth(2);out.setframerate(rate)
        out.writeframes(samples[45*rate:90*rate].tobytes())
    with wave.open(str(base/kind/'wind-140-to-150-seconds.wav'),'wb') as out:
        out.setnchannels(2);out.setsampwidth(2);out.setframerate(rate)
        out.writeframes(samples[140*rate:150*rate].tobytes())
canvas=Image.new('RGB',(512,488))
draw=ImageDraw.Draw(canvas)
for n,frame in enumerate([1799,3599,7199,8999]):
    pic=Image.open(base/f'plus-native/frame-{frame}.ppm')
    x=(n%2)*256;y=(n//2)*244
    canvas.paste(pic,(x,y+20));draw.text((x+4,y+4),f'Frame {frame}, about {frame/59.9227:.0f}s',fill='white')
canvas.save(base/'captured-scenes.png')
print(json.dumps(report,indent=2))
