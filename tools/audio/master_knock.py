#!/usr/bin/env python3
"""Any Python 3 + ffmpeg. Master the knock-only nudge clip (cue/nudge-01) from the synthesized knock.
usage (repo root):  python3 tools/audio/make_nudge.py && python3 tools/audio/master_knock.py
 in : audio-work/master/nudge-knock.wav  (made by make_nudge.py; audio-work/ is gitignored)
 out: desertranger/audio/cue/nudge-01.mp3  (mono 44.1 kHz, 64 kbps, the library's clean-clip format)
Level: aim for -16 LUFS like the voice clips, but never let the true peak go above -1.8 dBFS (a knock is a sharp transient, so the
peak ceiling wins: the result sits about -17.4 LUFS). Then register the clip in desertranger/audio/manifest.json (kind "cue") and
desertranger/audio/review.html, or run tools/audio/build_review.py."""
import os, re, subprocess
SRC, OUT = "audio-work/master/nudge-knock.wav", "desertranger/audio/cue/nudge-01.mp3"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
def run(*a): return subprocess.run(a, capture_output=True, text=True)
def measure(path):
    t = run("ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-").stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", t)[-1]), float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", t)[-1])
def encode(g):
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", SRC, "-af",
        f"volume={g}dB,alimiter=limit=0.776:level=disabled:attack=1:release=30", "-ar", "44100", "-ac", "1", "-b:a", "64k", OUT)
g = 0.0
for _ in range(6):
    encode(g); lufs, tp = measure(OUT)
    if abs(lufs + 16.0) < 0.35: break
    g += -16.0 - lufs
for _ in range(4):
    encode(g); lufs, tp = measure(OUT)
    if tp <= -1.8: break
    g -= (tp + 1.8) + 0.15
encode(g); lufs, tp = measure(OUT)
print(f"{OUT}: gain {g:.1f} dB, {lufs:.1f} LUFS, peak {tp:.1f} dBFS")
