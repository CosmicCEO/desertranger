#!/usr/bin/env python3
"""Kokoro venv. Build ~10-12 s reference clips for Chatterbox cloning.
usage: python tools/audio/make_refs.py [character ...] [--alt]    |    --crowd  (w_bella, m_michael, m_fenrir)
writes audio-work/refs/<character>.wav (or <character>.alt.wav with --alt)"""
import json, sys, os, warnings; warnings.filterwarnings("ignore")
import numpy as np, soundfile as sf, librosa
from kokoro import KPipeline
CAST = json.load(open("tools/audio/cast.json")); OUT = "audio-work/refs"; os.makedirs(OUT, exist_ok=True)
alt = "--alt" in sys.argv; want = [a for a in sys.argv[1:] if not a.startswith("--")] or [k for k in CAST if not k.startswith("_") and "ref" in CAST[k]]
pipes = {}
def kk(text, voice, speed):
    lc = voice[0]
    if lc not in pipes: pipes[lc] = KPipeline(lang_code=lc, repo_id="hexgrad/Kokoro-82M")
    return np.concatenate([x.numpy() if hasattr(x, "numpy") else x for _, _, x in pipes[lc](text, voice=voice, speed=speed)])
if "--crowd" in sys.argv:   # ranger_crowd refs: the design/scripts/crowd_v2_refs.py recipe (energetic text, speed 1.15)
    TXT = ("Yes! Yes! Did you see that? That was incredible! Oh my goodness, we actually did it! "
           "Come on, everybody, let's go! That's what I'm talking about! Unbelievable!")
    for k, (v, st) in {"w_bella": ("af_bella", 1.0), "m_michael": ("am_michael", 0.0), "m_fenrir": ("am_fenrir", -1.5)}.items():
        x = kk(TXT, v, 1.15); x = librosa.effects.pitch_shift(x, sr=24000, n_steps=st) if st else x
        sf.write(f"{OUT}/{k}.wav", x / np.abs(x).max() * 0.9, 24000); print("crowd ref", k, flush=True)
    sys.exit(0)
for ch in want:
    c = CAST[ch]; v, st = (c["alt"]["ref"], c["alt"]["pitch_st"]) if alt else (c["ref"], c["pitch_st"])
    a = kk(c["ref_text"], v, c["speed"])
    if abs(st) > 0.05: a = librosa.effects.pitch_shift(a, sr=24000, n_steps=st)
    a = a / (np.abs(a).max() + 1e-9) * 0.9
    fn = f"{OUT}/{ch}{'.alt' if alt else ''}.wav"; sf.write(fn, a, 24000)
    print(ch, v, st, round(len(a) / 24000, 2), "s ->", fn, flush=True)
