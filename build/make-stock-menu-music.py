"""Render the original Blue Circuit menu loop as 44.1 kHz stereo PCM and WAV."""
from array import array
import argparse
import math
from pathlib import Path
import sys
import wave


RATE = 44100
BEAT = 0.5
FRAMES = int(32 * BEAT * RATE)
TAU = math.tau


def render():
    left, right = array("f", [0.0])*FRAMES, array("f", [0.0])*FRAMES

    def note(start, duration, pitch, level, pan, voice):
        at = round(start*BEAT*RATE)
        frames = round(duration*BEAT*RATE)
        freq = 440*2**((pitch-69)/12)
        l, r = math.sqrt((1-pan)/2), math.sqrt((1+pan)/2)
        for i in range(frames):
            t = i/RATE
            x = TAU*freq*t
            if voice == "pad":
                env = min(1,t/.18,(frames-i)/(RATE*.32))
                y = env*(.54*math.sin(x)+.26*math.sin(x*1.0027)+.10*math.sin(2*x)+.025*math.sin(3*x))
            elif voice == "bass":
                env = min(1,t/.018,(frames-i)/(RATE*.1))*math.exp(-1.2*t)
                y = env*(.78*math.sin(x)+.18*math.sin(2*x)+.04*math.sin(4*x))
            else:
                env = min(1,t/.009,(frames-i)/(RATE*.09))*math.exp(-3.3*t)
                y = env*(.66*math.sin(x+.3*math.sin(2*x)*math.exp(-4*t))+.16*math.sin(3*x)+.045*math.sin(5*x))
            j=(at+i)%FRAMES
            left[j]+=y*level*l
            right[j]+=y*level*r

    chords = [(45,57,60,64,71),(41,57,60,64,69),(48,55,59,62,67),(43,55,57,62,69),
              (45,57,60,64,72),(41,57,60,65,69),(50,57,60,64,69),(43,55,59,62,67)]
    arp = [(2,3,4,3,1,3),(2,4,3,4,1,2),(1,2,4,3,2,1),(2,3,4,2,1,3)]
    melody = [(0.75,76),(2,72),(3.25,71),(4.75,72),(6,69),(8.5,74),(10,71),
              (11.25,67),(12.5,69),(14.25,74),(16.75,76),(18,79),(19.25,76),
              (20.75,77),(22,72),(24.5,74),(26,72),(27.25,69),(28.5,71),(30.25,67)]
    for bar,chord in enumerate(chords):
        start=bar*4
        for j,pitch in enumerate(chord[1:]):
            note(start+.08*j,4.12,pitch,.095,(-.65,.55,-.30,.42)[j],"pad")
        for j,i in enumerate(arp[bar%len(arp)]):
            note(start+.50*j+.17,1.15,chord[i]+(12 if j%3==2 else 0),.071,
                 -.47 if j%2 else .51,"bell")
        note(start,1.85,chord[0]-12,.26,0,"bass")
        note(start+2.18,1.65,chord[0]-5,.16,0,"bass")
    for j,(when,pitch) in enumerate(melody):
        note(when,1.65,pitch,.167,.11*(-1)**j,"bell")

    a, b = round(.161*RATE), round(.257*RATE)
    # Circular stereo reflections retain ambience across the loop point.
    def sample(i):
        return (left[i]+.18*right[i-a]+.075*left[i-b],
                right[i]+.18*left[i-b]+.075*right[i-a])

    peak = max(abs(s) for i in range(FRAMES) for s in sample(i))
    gain = 26000/peak
    data = array("h", (round(s*gain) for i in range(FRAMES) for s in sample(i)))
    if sys.byteorder != "little":
        data.byteswap()
    return data.tobytes()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("new_output", type=Path)
    args = parser.parse_args()
    args.new_output.mkdir()
    data=render()
    (args.new_output/"d35-menu.pcm").write_bytes(data)
    with wave.open(str(args.new_output/"Blue Circuit.wav"),"wb") as file:
        file.setparams((2,2,RATE,0,"NONE","not compressed"))
        file.writeframes(data)
    print(f"Blue Circuit: {FRAMES/RATE:g} s, stereo, {RATE} Hz, 16-bit, {len(data)} bytes")


if __name__ == "__main__":
    main()
