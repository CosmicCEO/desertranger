#!/usr/bin/env python3
"""Chatterbox venv (Python 3.11). Generate N takes per line from docs/audio-lines.json.
usage: python tools/audio/gen_lines.py [--phase 2|3|4] [--ids q01a,q01b] [--chars senior_ranger] [--takes 3]
                                       [--seed0 1] [--device auto|mps|cpu] [--alt] [--pron] [--force]
writes audio-work/takes/<id>/s<seed>.wav (24 kHz mono) + takes.jsonl. Resumable: existing takes are skipped."""
import argparse, json, os, re, sys, time, warnings; warnings.filterwarnings("ignore")
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
import torch, torchaudio as ta
from chatterbox.tts import ChatterboxTTS
p = argparse.ArgumentParser()
p.add_argument("--phase", type=int); p.add_argument("--ids"); p.add_argument("--chars")
p.add_argument("--takes", type=int, default=3); p.add_argument("--seed0", type=int, default=1)
p.add_argument("--device", default="auto"); p.add_argument("--alt", action="store_true")
p.add_argument("--pron", action="store_true", help="substitute 'pronounce' respellings into the TTS text")
p.add_argument("--ex", type=float); p.add_argument("--cfg", type=float); p.add_argument("--force", action="store_true")
a = p.parse_args()
L = json.load(open("docs/audio-lines.json"))["lines"]; CAST = json.load(open("tools/audio/cast.json"))
sel = [l for l in L if (a.phase is None or l["phase"] == a.phase)
       and (not a.ids or l["id"] in a.ids.split(","))
       and (not a.chars or l["character"] in a.chars.split(","))]
torch.set_num_threads(max(4, (os.cpu_count() or 8) // 2))
def load(dev):
    return ChatterboxTTS.from_pretrained(device=dev)
dev = a.device if a.device != "auto" else ("mps" if torch.backends.mps.is_available() else "cpu")
m = load(dev); print("device", dev, "lines", len(sel), flush=True)
log = open("audio-work/takes.jsonl", "a")
def tts_text(l):
    t = l.get("tts_text", l["text"])
    if a.pron:
        for k, v in l.get("pronounce", {}).items(): t = re.sub(r"\b" + k + r"\b", v, t, flags=re.I)
    return t
for l in sel:
    c = CAST[l["character"]]
    refs = [f"audio-work/refs/{r}.wav" for r in c["refs"]] if "refs" in c else \
           [f"audio-work/refs/{l['character']}{'.alt' if a.alt else ''}.wav"]
    ex = a.ex if a.ex is not None else c["ex"]; cfg = a.cfg if a.cfg is not None else c["cfg"]
    cap = l.get("max_sec", 3.0) * 1.8 + 0.5           # runaway guard (Chatterbox occasionally babbles on)
    for ri, ref in enumerate(refs):
        os.makedirs(f"audio-work/takes/{l['id']}", exist_ok=True)
        for s in range(a.seed0, a.seed0 + a.takes):
            tag = f"s{s}" + (f"_v{ri}" if len(refs) > 1 else "") + ("_alt" if a.alt else "") + ("_pron" if a.pron else "")
            fn = f"audio-work/takes/{l['id']}/{tag}.wav"
            if os.path.exists(fn) and not a.force: continue
            torch.manual_seed(s); t0 = time.time()
            try:
                w = m.generate(tts_text(l), audio_prompt_path=ref, exaggeration=ex, cfg_weight=cfg, temperature=c.get("temp", 0.8))
            except (RuntimeError, NotImplementedError) as e:
                if dev != "mps": raise
                print("MPS failed -> falling back to CPU:", repr(e)[:200], flush=True)
                dev = "cpu"; del m; m = load("cpu"); torch.manual_seed(s)
                w = m.generate(tts_text(l), audio_prompt_path=ref, exaggeration=ex, cfg_weight=cfg, temperature=c.get("temp", 0.8))
            w = w[:, :int(m.sr * cap)].cpu()
            ta.save(fn, w, m.sr)
            rec = dict(id=l["id"], take=tag, file=fn, ref=ref, ex=ex, cfg=cfg, seed=s, device=dev,
                       sec=round(w.shape[-1] / m.sr, 2), gen_s=round(time.time() - t0, 1), text=tts_text(l))
            log.write(json.dumps(rec) + "\n"); log.flush(); print(rec, flush=True)
