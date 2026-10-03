#!/usr/bin/env python3
"""Kokoro/Whisper venv (librosa). Hand-off 7 'distinctness check': median F0 (pyin) per character across up to 3 raw takes,
and the gap for the pairs that must differ by >= 20 Hz (dispatch vs senior_ranger, r55 vs ranger_273).
usage: python tools/audio/f0_check.py"""
import glob, json, warnings; warnings.filterwarnings("ignore")
import numpy as np, librosa
L = {l["id"]: l for l in json.load(open("docs/audio-lines.json"))["lines"]}
by = {}
for f in sorted(glob.glob("audio-work/takes/*/*.wav")):
    i = f.split("/")[2]
    if i in L and "_alt" not in f and "_pron" not in f: by.setdefault(L[i]["character"], []).append(f)
def f0(f):
    y, sr = librosa.load(f, sr=16000)
    v, vf, _ = librosa.pyin(y, fmin=65, fmax=400, sr=sr)
    v = v[vf & ~np.isnan(v)]
    return float(np.median(v)) if len(v) > 10 else None
med = {}
for c, fs in by.items():
    # spread across different lines first so one long line doesn't dominate
    pick = sorted(fs, key=lambda f: (f.split("/")[2], f))[:0] or fs[::max(1, len(fs) // 3)][:3]
    vals = [x for x in (f0(f) for f in pick) if x]
    if vals: med[c] = round(float(np.median(vals)), 1); print(f"{c:14s} median F0 {med[c]:6.1f} Hz  ({len(vals)} takes: {[round(v) for v in vals]})")
for a, b in (("dispatch", "senior_ranger"), ("r55", "ranger_273")):
    if a in med and b in med:
        d = abs(med[a] - med[b]); print(f"{a} vs {b}: {d:.1f} Hz ->", "OK" if d >= 20 else "TOO CLOSE (regenerate with make_refs.py <char> --alt)")
