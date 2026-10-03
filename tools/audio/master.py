#!/usr/bin/env python3
"""Any Python 3 + ffmpeg. Turn QA-picked takes into shipped MP3s and keep desertranger/audio/manifest.json current.
usage: python tools/audio/master.py --fx                 # build shared radio click / squelch / hiss assets
       python tools/audio/master.py [--ids ...|--phase N] # master voice lines (uses audio-work/qa/<id>.json pick)
Chains: radio = band-pass 300-3000 Hz + compression + presence + light tanh overdrive + mild bit grit;
        clean = 80 Hz high-pass + gentle compression;  crowd = 3 voices layered (q51*)."""
import argparse, glob, hashlib, json, os, re, subprocess, sys
OUT = "desertranger/audio"; WORK = "audio-work/master"; os.makedirs(WORK, exist_ok=True)
TRIM = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02,areverse,"
        "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.04,areverse")
RADIO = ("highpass=f=300:poles=2,highpass=f=300:poles=2,lowpass=f=3000:poles=2,lowpass=f=3000:poles=2,"
         "acompressor=threshold=-20dB:ratio=4:attack=5:release=90:makeup=2,equalizer=f=1700:t=q:w=1.0:g=4,"
         "volume=8dB,asoftclip=type=tanh,volume=-8dB,acrusher=bits=12:mix=0.25:mode=log,highpass=f=300,lowpass=f=3200")
CLEAN = "highpass=f=80,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=1,equalizer=f=3500:t=q:w=1:g=1.5"
TARGET = {"radio": -16.0, "clean": -16.0, "crowd": -14.0}
KBPS = {"radio": 48, "clean": 64, "crowd": 64}   # the radio chain band-limits to ~3 kHz, so 48 kbps mono is transparent and keeps the budgets
def sh(*a): subprocess.run(a, check=True)
def ff(*a): sh("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *a)
def meas(f):
    o = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", f, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    s = o[o.rfind("Summary"):]
    return float(re.search(r"I:\s+(-?[\d.]+)", s).group(1)), float(re.search(r"Peak:\s+(-?[\d.inf]+)", s).group(1))
def dur(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f],
                                capture_output=True, text=True).stdout.strip())
def norm_mp3(src, out, tgt, kbps=64, tp=-1.5):
    """crowd_norm.py recipe generalised: static gain -> 4x oversampled limiter -> MP3, re-measure the MP3, iterate."""
    os.makedirs(os.path.dirname(out), exist_ok=True)
    I0, P0 = meas(src)
    if I0 < -60:   # shorter than the 400 ms LUFS gate: peak-normalise instead
        ff("-i", src, "-af", f"volume={tp - 4.5 - P0:.2f}dB", "-ac", "1", "-ar", "44100", "-c:a", "libmp3lame", "-b:a", f"{kbps}k", out)
        return dict(mode="peak", tp=meas(out)[1])
    g, lim = tgt - I0, tp - 0.5
    for it in range(10):
        ff("-i", src, "-af", f"volume={g:.2f}dB,aresample=176400,alimiter=limit={lim}dB:attack=1:release=50:level=false,aresample=44100",
           "-ac", "1", "-c:a", "libmp3lame", "-b:a", f"{kbps}k", out)
        I, P = meas(out)
        if abs(I - tgt) <= 0.3 and P <= tp: break
        if P > tp: lim -= 0.3
        g += tgt - I
    return dict(lufs=I, tp=P)
MAN = f"{OUT}/manifest.json"
man = json.load(open(MAN)) if os.path.exists(MAN) else {"version": 1, "clips": {}}
def save(): json.dump(man, open(MAN, "w"), indent=1, ensure_ascii=False)
def register(cid, rel, **kw):
    f = f"{OUT}/{rel}"
    kw.update(file=rel, sec=round(dur(f), 3), bytes=os.path.getsize(f), v=hashlib.sha1(open(f, "rb").read()).hexdigest()[:8])
    man["clips"][cid] = kw; save()          # client fetches  audio/<file>?v=<v>  (Apache caches mp3 for 30 days)
    print(cid, kw, flush=True)
p = argparse.ArgumentParser(); p.add_argument("--fx", action="store_true"); p.add_argument("--ids"); p.add_argument("--phase", type=int)
a = p.parse_args()
if a.fx:
    w = WORK
    ff("-f", "lavfi", "-i", "anoisesrc=d=0.006:c=white:a=0.9:r=48000", "-f", "lavfi", "-i", "sine=f=1200:d=0.03:r=48000", "-filter_complex",
       "[0]highpass=f=800,afade=t=out:st=0.002:d=0.004[a];[1]volume=0.25,afade=t=in:d=0.003,afade=t=out:st=0.012:d=0.018[b];"
       "[a][b]concat=n=2:v=0:a=1,highpass=f=300,lowpass=f=3500,apad=pad_dur=0.02", "-ac", "1", f"{w}/click.wav")
    for n, (d, seed) in enumerate([(0.22, 1), (0.18, 2), (0.26, 3)], 1):
        ff("-f", "lavfi", "-i", f"anoisesrc=d={d}:c=white:a=0.6:r=48000:s={seed}", "-af",
           f"highpass=f=500,lowpass=f=4000,equalizer=f=2500:t=q:w=1:g=6,afade=t=in:d=0.004,afade=t=out:st=0.03:d={d-0.03:.2f}:curve=exp",
           "-ac", "1", f"{w}/squelch{n}.wav")
    ff("-f", "lavfi", "-i", "anoisesrc=d=4:c=pink:a=0.5:r=48000:s=5", "-af", "highpass=f=300,lowpass=f=3000", "-ac", "1", f"{w}/hiss.wav")
    norm_mp3(f"{w}/click.wav", f"{OUT}/radio/fx/radio-click-01.mp3", -20); register("radio-click-01", "radio/fx/radio-click-01.mp3", kind="fx")
    for n in (1, 2, 3):
        norm_mp3(f"{w}/squelch{n}.wav", f"{OUT}/radio/fx/radio-squelch-0{n}.mp3", -20); register(f"radio-squelch-0{n}", f"radio/fx/radio-squelch-0{n}.mp3", kind="fx")
    norm_mp3(f"{w}/hiss.wav", f"{OUT}/radio/fx/radio-hiss-loop.mp3", -40); register("radio-hiss-loop", "radio/fx/radio-hiss-loop.mp3", kind="fx",
             note="loop under the whole call at runtime gain ~0.5; crossfade-loop it (MP3 has encoder padding)")
    sys.exit(0)
L = {l["id"]: l for l in json.load(open("docs/audio-lines.json"))["lines"]}
ids = a.ids.split(",") if a.ids else [i for i, l in L.items() if a.phase is None or l["phase"] == a.phase]
for i in ids:
    qf = f"audio-work/qa/{i}.json"
    if not os.path.exists(qf): print("skip (no QA yet)", i); continue
    q = json.load(open(qf)); l = L[i]; t = l["treatment"]; tmp = f"{WORK}/{i}.wav"
    if t == "crowd":   # layer the best take of each voice (_v0/_v1/_v2) with small onset offsets
        picks = []
        for v in range(3):
            c = [r for r in q["takes"] if f"_v{v}" in r["file"]]
            if c: picks.append(min(c, key=lambda r: (not r["ok"], r["errors"]))["file"])
        ins = sum([["-i", f] for f in picks], [])
        fc = "".join(f"[{k}]{TRIM},adelay={[0, 25, 55][k]},volume={[1, 0.8, 0.7][k]}[x{k}];" for k in range(len(picks)))
        ff(*ins, "-filter_complex", fc + "".join(f"[x{k}]" for k in range(len(picks))) +
           f"amix=inputs={len(picks)}:normalize=0,{CLEAN}", "-ac", "1", "-ar", "44100", tmp)
    else:
        ff("-i", q["pick"], "-af", f"aresample=48000,{TRIM}", "-ac", "1", f"{WORK}/{i}.trim.wav")
        d0 = dur(f"{WORK}/{i}.trim.wav"); mx = l.get("max_sec", 9)
        tempo = f"atempo={min(1.15, d0 / mx):.3f}," if d0 > mx else ""      # pitch-preserving speed-up, max +15 %
        ff("-i", f"{WORK}/{i}.trim.wav", "-af", f"{tempo}{RADIO if t == 'radio' else CLEAN}", "-ac", "1", tmp)
    r = norm_mp3(tmp, f"{OUT}/{l['file']}", TARGET[t], KBPS[t])
    register(i, l["file"], character=l["character"], text=l["text"], square=l["square"], kind=l["kind"], treatment=t,
             qa=q["status"], take=os.path.basename(q["pick"]), **r)
