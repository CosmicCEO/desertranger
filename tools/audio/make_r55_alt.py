#!/usr/bin/env python3
"""Needs numpy + librosa (the .venv-tts venv has them) and ffmpeg. NOT shipped to the game.
Option B for the R55 lines: take the QA-picked natural "R five five, ..." take, slow ONLY the call sign (pitch-preserving atempo, factor
STRETCH; ffmpeg has no rubberband filter here and sox is not installed), keep the rest, then run the normal radio mastering.
The call sign and the rest of the line are split inside the natural pause between them (the first silence >= 0.10 s after 0.25 s of speech),
so the splice is in silence. Outputs desertranger/audio/alt/r55/<id>-B.mp3 (NOT in manifest.json, excluded from the deploy) and info.json
with the objective checks: splice jump (largest sample step within 5 ms of the splice vs the clip's 99.9th-percentile step), LUFS of the two halves, total length.
usage: .venv-tts/bin/python tools/audio/make_r55_alt.py [ids]"""
import json, os, subprocess, sys
import numpy as np, librosa, soundfile as sf
STRETCH = 0.65; GAP = 0.22
src = open("tools/audio/master.py").read().split("p = argparse.ArgumentParser()")[0]
exec(compile(src, "master.py", "exec"))            # ff, meas, dur, norm_mp3, RADIO, TARGET, KBPS, TRIM, OUT, WORK
ALT = f"{OUT}/alt/r55"; os.makedirs(ALT, exist_ok=True)
L = {l["id"]: l for l in json.load(open("docs/audio-lines.json"))["lines"]}
ids = sys.argv[1].split(",") if len(sys.argv) > 1 else ["ch01-1", "ch02-1", "ch04-1", "ch05-1", "ch06-1", "ch06-3", "ch08-1"]
info = {}
for i in ids:
    q = json.load(open(f"audio-work/qa/{i}.json")); y, sr = librosa.load(q["pick"], sr=24000)
    yt, (a, b) = librosa.effects.trim(y, top_db=40); y = yt
    hop = int(0.01 * sr); rms = librosa.feature.rms(y=y, frame_length=2 * hop, hop_length=hop)[0]
    db = 20 * np.log10(rms / rms.max() + 1e-9); sil = db < -38
    gap = None; k = 25
    while k < len(sil):
        if sil[k]:
            e = k
            while e < len(sil) and sil[e]: e += 1
            if e - k >= 10: gap = (k, e); break
            k = e
        else: k += 1
    if not gap: print(i, "no clean pause after the call sign: skipped"); continue
    cut = (gap[0] + gap[1]) // 2 * hop
    p1, p2 = y[:cut], y[cut:]
    sf.write(f"{WORK}/{i}.cs.wav", p1, sr); sf.write(f"{WORK}/{i}.rest.wav", p2, sr)
    ff("-i", f"{WORK}/{i}.cs.wav", "-af", f"aresample=48000,atempo={STRETCH},areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse", "-ac", "1", f"{WORK}/{i}.cs.slow.wav")
    # re-trim edges of both parts so the pause length is exactly GAP (cut points were mid-pause: edges are near-silent)
    ff("-i", f"{WORK}/{i}.rest.wav", "-af", f"aresample=48000,silenceremove=start_periods=1:start_threshold=-45dB", "-ac", "1", f"{WORK}/{i}.rest.t.wav")
    l1, l2 = meas(f"{WORK}/{i}.cs.slow.wav")[0], meas(f"{WORK}/{i}.rest.t.wav")[0]; g = max(-6.0, min(6.0, l2 - l1))   # level-match the call sign to the rest of the line
    ff("-i", f"{WORK}/{i}.cs.slow.wav", "-af", f"volume={g:.2f}dB", f"{WORK}/{i}.cs.adj.wav")
    ff("-i", f"{WORK}/{i}.cs.adj.wav", "-i", f"{WORK}/{i}.rest.t.wav", "-filter_complex",
       f"[0]aresample=48000,apad=pad_dur={GAP}[a];[1]aresample=48000[b];[a][b]concat=n=2:v=0:a=1", "-ac", "1", f"{WORK}/{i}.alt.raw.wav")
    d1 = dur(f"{WORK}/{i}.cs.adj.wav"); x, xr = sf.read(f"{WORK}/{i}.alt.raw.wav")
    s0 = int((d1 + GAP) * xr); w = int(0.005 * xr); step = np.abs(np.diff(x)); jump = float(step[max(0, s0 - w):s0 + w].max()); ref = float(np.percentile(step, 99.9))
    ff("-i", f"{WORK}/{i}.alt.raw.wav", "-af", RADIO, "-ac", "1", f"{WORK}/{i}.alt.radio.wav")
    r = norm_mp3(f"{WORK}/{i}.alt.radio.wav", f"{ALT}/{i}-B.mp3", TARGET["radio"], KBPS["radio"])
    l1a = meas(f"{WORK}/{i}.cs.adj.wav")[0]
    info[i] = dict(file=f"alt/r55/{i}-B.mp3", sec=round(dur(f"{ALT}/{i}-B.mp3"), 3), call_sign_sec_natural=round(cut / sr, 2), call_sign_sec_stretched=round(d1, 2),
                   gap_sec=GAP, splice_jump=round(jump, 4), clip_p999_step=round(ref, 4), splice_ok=jump <= 3 * ref + 0.01,
                   lufs_call_sign_raw=l1, gain_applied_db=round(g, 1), lufs_call_sign=l1a, lufs_rest=l2, lufs_diff=round(abs(l1a - l2), 1), take=os.path.basename(q["pick"]), **r)
    print(i, info[i], flush=True)
json.dump(info, open(f"{ALT}/info.json", "w"), indent=1)
