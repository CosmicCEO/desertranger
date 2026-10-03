#!/usr/bin/env python3
"""Any Python 3 + ffmpeg. Master the synthesized ambience bed and critters (hand-off 8.3, 8.4) into shipped MP3s.
usage: python tools/audio/make_ambience.py      (expects audio-work/amb/{bed_loop,rattle,truck,crickets}.wav, built by the 8.3/8.4 ffmpeg recipes)
Reuses norm_mp3()/register() from master.py (the part above its argparse block)."""
import os
src = open("tools/audio/master.py").read().split("p = argparse.ArgumentParser()")[0]
exec(compile(src, "master.py", "exec"))
A = "audio-work/amb"
JOBS = [  # (wav, shipped file, id, kind, LUFS target, kbps, true-peak limit, note)
    ("bed_loop", "amb/amb-bed-01.mp3", "amb-bed-01", "amb", -28, 64, -6, "90 s desert wind bed; loop with a 1.5 s equal-power crossfade at runtime"),
    ("rattle", "amb/amb-rattle-01.mp3", "amb-rattle-01", "critter", -26, 64, -3, "rare; synthesized 52 Hz AM hiss"),
    ("truck", "amb/amb-truck-01.mp3", "amb-truck-01", "critter", -26, 64, -3, "distant truck pass-by; synthesized"),
    ("crickets", "amb/amb-crickets-01.mp3", "amb-crickets-01", "critter", -26, 64, -3, "cricket burst; synthesized"),
]
for wav, rel, cid, kind, tgt, kbps, tp, note in JOBS:
    f = f"{A}/{wav}.wav"
    if not os.path.exists(f): print("skip (missing)", f); continue
    r = norm_mp3(f, f"{OUT}/{rel}", tgt, kbps, tp)
    register(cid, rel, kind=kind, note=note, source="original, synthesized with ffmpeg", **r)
