#!/usr/bin/env python3
"""Any Python 3 + ffmpeg. Synthesise the double wood-knock that opens the "Knock, knock" nudge cue (nudge-01, Wave 2 feature #24).
usage: python3 tools/audio/make_nudge.py        -> audio-work/master/nudge-knock.wav  (mono 48 kHz, ~0.5 s)
master.py places it before the ranger voice (line nudge-01 has "lead_sfx": "nudge-knock"). Original sound, generated with ffmpeg
only (damped sine partials + a short noise transient, band-limited like a knuckle on a wooden door); no third-party audio."""
import os, subprocess
WORK = "audio-work/master"; os.makedirs(WORK, exist_ok=True)
def ff(*a): subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *a], check=True)
def knock(fn, f0, amp):
    # body: three decaying partials (fundamental, ~2.3x, ~4.6x) = hollow wood; transient: 12 ms of noise through a band-pass
    e = (f"{amp}*(0.9*sin(2*PI*{f0}*t)*exp(-t*42)+0.45*sin(2*PI*{f0*2.3:.0f}*t)*exp(-t*70)+0.2*sin(2*PI*{f0*4.6:.0f}*t)*exp(-t*110))")
    ff("-f", "lavfi", "-i", f"aevalsrc='{e}':d=0.16:s=48000",
       "-f", "lavfi", "-i", "anoisesrc=d=0.012:c=white:a=0.5:r=48000:s=7",
       "-filter_complex", "[1]highpass=f=1500,lowpass=f=5000,afade=t=out:st=0.002:d=0.01[n];[0][n]amix=inputs=2:normalize=0:duration=first,"
       "highpass=f=90,afade=t=in:d=0.0015,afade=t=out:st=0.12:d=0.04", "-ac", "1", fn)
knock(f"{WORK}/knock1.wav", 215, 0.55)
knock(f"{WORK}/knock2.wav", 200, 0.48)       # second knock slightly softer and lower, like a real hand
ff("-i", f"{WORK}/knock1.wav", "-i", f"{WORK}/knock2.wav", "-filter_complex",
   "[1]adelay=220[b];[0][b]amix=inputs=2:normalize=0,apad=pad_dur=0.1,alimiter=limit=0.9", "-ac", "1", f"{WORK}/nudge-knock.wav")
print("wrote", f"{WORK}/nudge-knock.wav")
