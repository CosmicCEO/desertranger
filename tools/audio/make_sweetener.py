#!/usr/bin/env python3
"""Crowd sweetener for q35a/q35b (hand-off 8.6): 3 short "whoa!" shouts from the ranger_crowd references, layered under the last
~0.6 s of the nerdy-ranger line at -12 dB.   Two steps, because Chatterbox and mastering use different Python environments:
  .venv-cb/bin/python tools/audio/make_sweetener.py gen      writes audio-work/sweet/whoa_<ref>_s<seed>.wav  (ex=1.0, cfg=0.3, cut at 3 s, like crowd_v2_cb.py)
  python3 tools/audio/make_sweetener.py mix                  layers them under audio-work/master/q35{a,b}.wav and re-masters the MP3 (clean chain, -16 LUFS)
Run `master.py --ids q35a,q35b` first; re-running master.py later overwrites the sweetener, so mix again afterwards."""
import json, os, subprocess, sys
SW = "audio-work/sweet"; os.makedirs(SW, exist_ok=True)   # (master.py defines OUT = desertranger/audio, so keep a different name)
if sys.argv[1:2] == ["gen"]:
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    import torch, torchaudio as ta
    from chatterbox.tts import ChatterboxTTS
    cast = json.load(open("tools/audio/cast.json"))["ranger_crowd"]
    m = ChatterboxTTS.from_pretrained(device="mps" if torch.backends.mps.is_available() else "cpu")
    for ref in cast["refs"]:
        for seed, txt in ((1, "Whoa!!!"), (2, "Woo!!")):
            fn = f"{SW}/whoa_{ref}_s{seed}.wav"
            if os.path.exists(fn): continue
            torch.manual_seed(seed)
            w = m.generate(txt, audio_prompt_path=f"audio-work/refs/{ref}.wav", exaggeration=1.0, cfg_weight=0.3, temperature=cast["temp"])
            ta.save(fn, w[:, :int(m.sr * 3)].cpu(), m.sr); print("wrote", fn, round(w.shape[-1] / m.sr, 2), "s", flush=True)
else:
    src = open("tools/audio/master.py").read().split("p = argparse.ArgumentParser()")[0]
    exec(compile(src, "master.py", "exec"))
    import glob
    shouts = sorted(glob.glob(f"{SW}/whoa_*_s1.wav"))[:3]          # one "Whoa" per crowd voice
    for qid in ("q35a", "q35b"):
        base = f"{WORK}/{qid}.wav"
        if not os.path.exists(base): print("skip (not mastered yet)", qid); continue
        n = dur(base); tail = 0.6
        ins = ["-i", base] + sum([["-i", f] for f in shouts], [])
        # each shout: trim silence, cap at the tail length, delay so it ends with the line, -12 dB, tiny stagger between voices
        fc = "".join(f"[{k+1}]{TRIM},atrim=end={tail},afade=t=out:st={tail-0.15}:d=0.15,volume=-12dB,adelay={int(max(0, n - tail + 0.05*k) * 1000)}[w{k}];" for k in range(len(shouts)))
        mix = "[0]" + "".join(f"[w{k}]" for k in range(len(shouts))) + f"amix=inputs={len(shouts)+1}:normalize=0:duration=first,alimiter=limit=0.95"
        out = f"{WORK}/{qid}.sweet.wav"
        ff(*ins, "-filter_complex", fc + mix, "-ac", "1", out)
        r = norm_mp3(out, f"{OUT}/quotes/{qid}.mp3", TARGET["clean"], 64)
        old = man["clips"].get(qid, {})
        register(qid, f"quotes/{qid}.mp3", **{**{k: v for k, v in old.items() if k not in ("file", "sec", "bytes", "v", "lufs", "tp", "mode")},
                 "sweetener": "3 crowd 'whoa' shouts under the last 0.6 s at -12 dB", **r})
