"""Render the original Bonus Round menu loop as 44.1 kHz stereo PCM and WAV."""
from array import array
import argparse
import math
from pathlib import Path
import random
import sys
import wave


RATE = 44100
BEAT = 60 / 144
FRAMES = round(32 * BEAT * RATE)
TAU = math.tau


def tone(voice, phase, time):
    if voice == "bass":
        return .67 * math.sin(phase) + .23 * math.sin(2 * phase) + .10 * math.sin(3 * phase)
    if voice == "keys":
        index = 1.3 * math.exp(-8 * time)
        return .78 * math.sin(phase + index * math.sin(2 * phase)) + .22 * math.sin(2.003 * phase)
    # Rounded pulse with a decaying brass-like bite.
    return (.76 * math.sin(phase) + .16 * math.sin(3 * phase)
            + .13 * math.exp(-11 * time) * math.sin(5 * phase))


def render():
    left = array("f", [0]) * FRAMES
    right = array("f", [0]) * FRAMES
    noise = random.Random(145)

    def mix(start, duration, level, pan, signal):
        first = round(start * BEAT * RATE)
        count = min(round(duration * BEAT * RATE), FRAMES - first)
        gain_l = level * math.sqrt((1 - pan) / 2)
        gain_r = level * math.sqrt((1 + pan) / 2)
        for i in range(count):
            time = i / RATE
            envelope = min(1, time / .004, (count - 1 - i) / (RATE * .009))
            sample = signal(time) * envelope
            left[first + i] += sample * gain_l
            right[first + i] += sample * gain_r

    def note(start, duration, pitch, level, pan, voice):
        omega = TAU * 440 * 2 ** ((pitch - 69) / 12)
        decay = {"keys": 6.5, "bass": 3, "lead": 2.6}[voice]
        mix(start, duration, level, pan,
            lambda t: tone(voice, omega * t, t) * math.exp(-decay * t))

    def kick(t):
        phase = TAU * (53 * t + 2.4 * (1 - math.exp(-48 * t)))
        return math.sin(phase) * math.exp(-19 * t)

    def snare(t):
        return (.73 * noise.uniform(-1, 1) + .27 * math.sin(TAU * 187 * t)) * math.exp(-29 * t)

    def hi_hat(t):
        metal = math.sin(TAU * 7951 * t) * math.sin(TAU * 6833 * t)
        return (.45 * metal + .55 * noise.uniform(-1, 1)) * math.exp(-59 * t)

    chords = [
        (48, 60, 64, 67, 74), (45, 60, 64, 67, 69), (41, 57, 60, 64, 67), (43, 59, 62, 65, 69),
        (48, 60, 64, 67, 76), (45, 60, 64, 67, 72), (41, 57, 60, 65, 69), (43, 59, 62, 65, 74),
    ]
    hooks = [
        ((.5, 76), (1, 79), (1.75, 81), (2.5, 79), (3, 76)),
        ((.25, 72), (.75, 76), (1.5, 79), (2.25, 81), (3, 84)),
        ((.5, 84), (1, 81), (1.5, 79), (2.25, 76), (3, 77)),
        ((.25, 79), (1, 74), (1.75, 71), (2.5, 74), (3, 76)),
        ((.5, 76), (1, 79), (1.75, 81), (2.5, 84), (3, 88)),
        ((.25, 84), (.75, 81), (1.5, 79), (2.25, 76), (3, 81)),
        ((.5, 84), (1, 81), (1.5, 77), (2.25, 79), (3, 81)),
        ((.25, 79), (1, 74), (1.75, 71), (2.5, 74), (3, 76)),
    ]
    for bar, (root, *chord) in enumerate(chords):
        start = bar * 4
        for beat in (0, 1.75, 2.5, 3.5):
            mix(start + beat, .42, .49, 0, kick)
        for beat in (1, 3):
            mix(start + beat, .46, .26, -.09, snare)
        for step in range(8):
            mix(start + .5 * step, .19, .095 if step % 2 else .045, .32, hi_hat)

        for beat, interval, duration in ((0, 0, .68), (.75, 12, .31), (1.5, 0, .52),
                                         (2.25, 7, .37), (2.75, 12, .42), (3.5, 7, .34)):
            note(start + beat, duration, root + interval, .35, 0, "bass")
        for beat in (.5, 1.5, 2.5, 3.25):
            for i, pitch in enumerate(chord):
                note(start + beat + i * .013, .51, pitch, .11, (-.64, .46, -.34, .62)[i], "keys")
        for i, (beat, pitch) in enumerate(hooks[bar]):
            note(start + beat, .43 if i < 4 else .69, pitch, .23, -.12, "lead")
            if beat < 3:
                note(start + beat + .375, .32, pitch, .063, .54, "keys")

    peak = max(max(left), -min(left), max(right), -min(right))
    gain = 25200 / peak
    data = array("h", (round(sample * gain) for pair in zip(left, right) for sample in pair))
    if sys.byteorder != "little":
        data.byteswap()
    return data.tobytes()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("new_output", type=Path)
    args = parser.parse_args()
    args.new_output.mkdir()
    data = render()
    (args.new_output / "d35-menu.pcm").write_bytes(data)
    with wave.open(str(args.new_output / "Bonus Round.wav"), "wb") as file:
        file.setparams((2, 2, RATE, 0, "NONE", "not compressed"))
        file.writeframes(data)
    print(f"Bonus Round at 144 BPM, {FRAMES / RATE:g} s, stereo, {RATE} Hz, {len(data)} bytes")


if __name__ == "__main__":
    main()
