from pathlib import Path
import json
import shutil
import wave
from hashlib import sha256
import numpy as np

root=Path(__file__).resolve().parent.parent
out=root/'device-evidence/card-D-v7-return'
out.mkdir(exist_ok=False)
for p in Path('D:/retro').glob('*v7*'):
    if p.is_file(): shutil.copy2(p,out/p.name)
shutil.copy2('D:/retro/libs/emu_sfc.so',out/'emu_sfc.so')
for p in Path('D:/retro/states/SFC').glob('Final Fantasy VI.*'):
    shutil.copy2(p,out/p.name)
with wave.open(str(out/'emu_sfc_plus_v7_audio.wav'),'rb') as w:
    params={'rate':w.getframerate(),'channels':w.getnchannels(),
            'bits':w.getsampwidth()*8,'frames':w.getnframes()}
    pcm=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,2).astype(np.int32)
assert params=={'rate':44100,'channels':2,'bits':16,'frames':264600}
meta=dict(line.split('=',1) for line in (out/'emu_sfc_plus_v7_capture.txt').read_text().splitlines() if '=' in line)
d=np.abs(np.diff(pcm,axis=0))
report={'format':params,'seconds':len(pcm)/44100,'metadata':meta,
        'adapter_sha256':sha256((out/'emu_sfc.so').read_bytes()).hexdigest(),
        'min_per_channel':pcm.min(axis=0).tolist(),'max_per_channel':pcm.max(axis=0).tolist(),
        'rms_per_channel':np.sqrt(np.mean(pcm.astype(float)**2,axis=0)).tolist(),
        'full_scale_sample_count':int(np.sum((pcm==-32768)|(pcm==32767))),
        'max_step_per_channel':d.max(axis=0).tolist(),
        'step_quantiles':{str(q):np.quantile(d,q,axis=0).tolist() for q in [.5,.99,.999]},
        'limitation':'Waveform statistics do not establish whether perceived clicks are present. User listening required.'}
(out/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
for p in out.glob('*.sv*'):
    b=p.read_bytes()
    print(p.name,'bytes=',len(b),'adapter_header_offset=',b.find(b'D35PLUS1'),'first_bytes=',b[:32].hex())
