#!/usr/bin/env python3
"""Any Python 3 + ffmpeg. Master the CC0 Kenney Casino Audio dice sounds (hand-off Phase 1.1) into shipped MP3s.
usage: python tools/audio/make_dice.py   (expects the pack unzipped at audio-work/src/kenney/Audio/)
shake  = dice-shake-1.ogg trimmed to 0.7 s, 120 ms fade-out, mono, -20 LUFS     -> dice/dice-shake-01.mp3
clatter = die-throw-1..4.ogg, mono, -18 LUFS (peak mode if the clip is under the 400 ms LUFS gate) -> dice/dice-clatter-01..04.mp3"""
import os
src = open("tools/audio/master.py").read().split("p = argparse.ArgumentParser()")[0]
exec(compile(src, "master.py", "exec"))
K = "audio-work/src/kenney/Audio"
os.makedirs("audio-work/dice", exist_ok=True)
ff("-i", f"{K}/dice-shake-1.ogg", "-af", "atrim=end=0.7,asetpts=N/SR/TB,afade=t=out:st=0.58:d=0.12", "-ac", "1", "audio-work/dice/shake.wav")
r = norm_mp3("audio-work/dice/shake.wav", f"{OUT}/dice/dice-shake-01.mp3", -20)
register("dice-shake-01", "dice/dice-shake-01.mp3", kind="dice", note="local shake on ROLL tap", source="Kenney Casino Audio 1.1 dice-shake-1.ogg (CC0)", **r)
for n in range(1, 5):
    ff("-i", f"{K}/die-throw-{n}.ogg", "-af", "afade=t=out:st=%.3f:d=0.04" % (float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{K}/die-throw-{n}.ogg"], capture_output=True, text=True).stdout) - 0.04), "-ac", "1", f"audio-work/dice/clatter{n}.wav")
    r = norm_mp3(f"audio-work/dice/clatter{n}.wav", f"{OUT}/dice/dice-clatter-0{n}.mp3", -18)
    register(f"dice-clatter-0{n}", f"dice/dice-clatter-0{n}.mp3", kind="dice", note="synced clatter at the roll reveal", source=f"Kenney Casino Audio 1.1 die-throw-{n}.ogg (CC0)", **r)
