#!/usr/bin/env python3
"""Whisper venv (faster-whisper). Word-check every take against its script line and pick a keeper.
usage: python tools/audio/qa_check.py [--ids ...] [--phase N] [--model small.en]
reads audio-work/takes/<id>/*.wav, writes audio-work/qa/<id>.json and audio-work/qa/summary.json.
The reference is the line's "qa_text" when present (stylised TTS such as the drawn-out R55 call sign), else its "text".
A leading [bracketed phrase] in qa_text (e.g. "[R five five], ten-twenty?") is a loose lead-in: Whisper cannot reliably transcribe
a deliberately drawn-out word ("fiiive" is heard as "phi, I've"), so 1-10 heard words before the rest of the line are accepted
instead of the bracketed words (something must be heard there); everything after the bracket is checked as usual.
Words in the shared docs/audio-lines.json "pronunciations" table are respelled for the TTS, so the check accepts either the
written word or something close to the respelling (a run of 1-4 heard words that sounds like it) for them.
A take PASSES when (after trimming silence) word errors <= allowed and duration <= max_sec.
NEVER run this while gen_lines.py (Chatterbox) is running: one heavy model at a time."""
import argparse, glob, json, os, re, unicodedata, warnings; warnings.filterwarnings("ignore")
import difflib
import numpy as np, librosa
from faster_whisper import WhisperModel
p = argparse.ArgumentParser(); p.add_argument("--ids"); p.add_argument("--phase", type=int)
p.add_argument("--model", default="small.en"); a = p.parse_args()
D = json.load(open("docs/audio-lines.json")); L = {l["id"]: l for l in D["lines"]}; PRON = D.get("pronunciations", {})
ids = a.ids.split(",") if a.ids else [i for i, l in L.items() if a.phase is None or l["phase"] == a.phase]
ids = [i for i in ids if glob.glob(f"audio-work/takes/{i}/*.wav")]
m = WhisperModel(a.model, device="cpu", compute_type="int8", cpu_threads=max(4, (os.cpu_count() or 8) // 2))
TEMPO_MAX = 1.15   # master.py may speed a clip up by at most this (pitch-preserving atempo) to fit max_sec
def hint(l):      # SHORT prompt with only this line's proper nouns; a long vocabulary prompt makes Whisper hallucinate
    ref_t = LEAD.sub("", l.get("qa_text", l["text"]), count=1)
    w = re.findall(r"\b[A-Z][a-z]+(?:'s)?\b", ref_t) + list(l.get("pronounce", {})) + [k for k in PRON if re.search(r"\b" + k + r"\b", ref_t, re.I)]
    return ", ".join(dict.fromkeys(w)) + "." if w else None
ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
def n2w(n):
    n = int(n)
    if n < 20: return ONES[n]
    if n < 100: return TENS[n // 10] + ("" if n % 10 == 0 else " " + ONES[n % 10])
    return ONES[n // 100] + " " + ("" if n % 100 == 0 else n2w(n % 100))
DROP = {"hundred", "and", "uh", "um"}
def norm(t, ignore=(), digits=False):    # digits=True reads digit runs one by one ("273" = two seven three) instead of as a number
    t = re.sub("[\u2012-\u2015\u2212]", " ", t)   # em/en dashes separate words ("westward\u2014please"); folding them away would merge the words
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"\d+", lambda x: " " + (" ".join(ONES[int(c)] for c in x.group()) if digits else n2w(x.group())) + " ", t)
    t = re.sub(r"[^a-z' ]+", " ", t.replace("-", " ")).replace("'", "")
    toks = [w for w in t.split() if w not in DROP and w not in ignore]
    out, run = [], False   # spelled-out letters ("V I P", "H R") are heard by Whisper as one word ("VIP", "HR"): merge runs of single letters
    for w in toks:
        if len(w) == 1 and w not in ("a", "i") or (len(w) == 1 and run):
            if run: out[-1] += w
            else: out.append(w)
            run = True
        else:
            out.append(w); run = False
    return out
def collapse(h, r, ign):
    """Shared-table words: if the reference has such a word and Whisper heard something that sounds like the word or its
    respelling (1-4 consecutive tokens, joined, similarity >= 0.6), count it as the written word."""
    h = list(h)
    for k, v in PRON.items():
        wt = "".join(norm(k)); sp = "".join(norm(v))
        if not wt or wt in ign: continue
        for _ in range(max(0, r.count(wt) - h.count(wt))):
            best = None
            for n in (1, 2, 3, 4):
                for i in range(len(h) - n + 1):
                    seg = h[i:i + n]
                    if wt in seg: continue
                    j = "".join(seg); sc = max(difflib.SequenceMatcher(None, j, wt).ratio(), difflib.SequenceMatcher(None, j, sp).ratio())
                    if sc >= 0.6 and (best is None or sc > best[0] + 1e-9): best = (sc, i, n)
            if best: h[best[1]:best[1] + best[2]] = [wt]
            else: break
    return h
LEAD = re.compile(r"^\s*\[[^\]]*\]\s*[,.;:]?\s*")
def errors(text, hyp_t, ign):
    lead = LEAD.match(text); text = text[lead.end():] if lead else text
    best = None
    for dg in (False, True):          # numbers heard as a number or digit by digit: accept whichever reading matches
        r = norm(text, ign, dg); h = collapse(norm(hyp_t, ign, dg), r, ign)
        e = min(edits(r, h[k:]) for k in range(1, 11)) if lead else edits(r, h)
        best = e if best is None else min(best, e)
    return best
def edits(r, h):
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (r[i - 1] != h[j - 1])); prev, d[j] = d[j], cur
    return d[len(h)]
os.makedirs("audio-work/qa", exist_ok=True)
summ = json.load(open("audio-work/qa/summary.json")) if os.path.exists("audio-work/qa/summary.json") else {}
for i in ids:
    l = L[i]; ign = set(l.get("whisper_ignore", [])); ref_text = l.get("qa_text", l["text"]); ref = norm(LEAD.sub("", ref_text, count=1), ign)
    allowed = 0 if len(ref) < 6 else max(1, len(ref) // 10)
    res = []
    for f in sorted(glob.glob(f"audio-work/takes/{i}/*.wav")):
        y, sr = librosa.load(f, sr=16000); yt, _ = librosa.effects.trim(y, top_db=40); dur = len(yt) / sr
        x = np.pad(yt, (4000, 4000)).astype(np.float32)
        for prompt in (None, hint(l)):          # pass 1: no prompt; pass 2 (only if needed): proper-noun hint
            segs, _ = m.transcribe(x, beam_size=5, language="en", initial_prompt=prompt, condition_on_previous_text=False)
            hyp_t = "".join(s.text for s in segs).strip(); e = errors(ref_text, hyp_t, ign)
            if e <= allowed or not hint(l): break
        ok = e <= allowed and 0.3 <= dur <= l.get("max_sec", 9) * TEMPO_MAX and float(np.abs(y).max()) > 0.02
        res.append(dict(file=f, heard=hyp_t, errors=e, allowed=allowed, sec=round(dur, 2), ok=ok))
    good = [r for r in res if r["ok"]]
    if good:
        med = float(np.median([r["sec"] for r in good]))
        pick = min(good, key=lambda r: (r["errors"], abs(r["sec"] - med)))
    else:
        pick = min(res, key=lambda r: (r["errors"], r["sec"]))
    out = dict(id=i, text=ref_text, status="pass" if good else "FAIL", pick=pick["file"], takes=res)
    json.dump(out, open(f"audio-work/qa/{i}.json", "w"), indent=1)
    summ[i] = dict(status=out["status"], pick=pick["file"], heard=pick["heard"], errors=pick["errors"], sec=pick["sec"])
    print(i, out["status"], pick["errors"], pick["sec"], "|", pick["heard"], flush=True)
json.dump(summ, open("audio-work/qa/summary.json", "w"), indent=1)
print("FAILS:", [k for k, v in summ.items() if v["status"] != "pass"])
