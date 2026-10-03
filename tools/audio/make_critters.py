#!/usr/bin/env python3
"""Any Python 3 + ffmpeg. Trim, lightly denoise and master the CC0 Freesound critter previews (hand-off Phase 1.3).
usage: python tools/audio/make_critters.py     (expects the hq preview MP3s in audio-work/src/cc0/, see CREDITS.md for their URLs)
Each: cut the excerpt [start, end] s, afftdn noise reduction, 30 ms/150 ms fades, mono, -26 LUFS, true peak <= -3 dB, 64 kbps MP3."""
import os, subprocess
src = open("tools/audio/master.py").read().split("p = argparse.ArgumentParser()")[0]
exec(compile(src, "master.py", "exec"))
S = "audio-work/src/cc0"
JOBS = [  # (source file, start s, end s, shipped id, note)
    ("crow-1.mp3", 0.15, 0.75, "amb-crow-01", "American crow, single caw"),
    ("coyote-1.mp3", 0.45, 2.30, "amb-coyote-01", "distant coyote yips"),
    ("hawk-2.mp3", 7.40, 9.30, "amb-hawk-01", "red-tailed hawk call"),
]
os.makedirs("audio-work/amb", exist_ok=True)
for fn, a, b, cid, note in JOBS:
    f = f"{S}/{fn}"
    if not os.path.exists(f): print("skip (missing)", f); continue
    out = f"audio-work/amb/{cid}.wav"; d = b - a
    ff("-ss", str(a), "-to", str(b), "-i", f, "-af", f"afftdn=nf=-25,afade=t=in:d=0.03,afade=t=out:st={d - 0.15:.3f}:d=0.15,aresample=44100", "-ac", "1", out)
    r = norm_mp3(out, f"{OUT}/amb/{cid}.mp3", -26, 64, -3)
    register(cid, f"amb/{cid}.mp3", kind="critter", note=note, source=f"CC0 Freesound preview {fn} (see CREDITS.md)", **r)
