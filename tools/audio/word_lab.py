#!/usr/bin/env python3
"""Word lab for issue #28 (Chatterbox venv, .venv-cb). One heavy model at a time: never run this while word_metrics.py / qa_check.py (Whisper) runs.

For each hard word and each place-name voice (senior_ranger, ranger_273) render several CANDIDATE SPELLINGS x seeds inside the real clip text:
  wc   = the real word-only place clip (pl-sr-NN / pl-r273-NN) when there is one, 3 seeds
  sent = one real sentence clip that contains the word (q12a, q46a, ...), 1 seed
Candidates per word (9): plain (the clip text as written), own (the owner's respelling, lowercase, no dashes), title (same, Title-case),
p1-p3 (rule-generated phonetic variants, letters a-z only), and three CONTROLS that keep the old format on purpose so the report can show
what each format really does:  dash (Title-case syllables joined by hyphens), caps (one ALL-CAPS word), dcaps (hyphens + a capitalised syllable).
Chatterbox's punc_norm() capitalises a text's first letter, so for a word at the start of a clip lowercase and Title are the SAME text; identical
(voice, clip, normalised text, seed) is rendered once and the other file is a copy (manifest "dup_of").
Output: audio-work/wordlab/takes/<word>__<voice>__<clip>__<fmt>-<id>__s<seed>.wav (all lowercase, format and id in the name, never case-only
differences), manifest audio-work/wordlab/manifest.jsonl (one line per file). Resumable.
usage: python tools/audio/word_lab.py [--words Ocotillo,Olla] [--voices senior_ranger,ranger_273] [--dry] [--out audio-work/wordlab]"""
import argparse, json, os, re, shutil, sys, time, warnings; warnings.filterwarnings("ignore")

VOICE_TAG = {"senior_ranger": "sr", "ranger_273": "r273"}
# word -> dict(own=owner's respelling (lowercase, dash-free), p=[3 phonetic variants], dash/caps/dcaps = old-format controls,
#              wc=word-only clip number (pl-sr-NN), sent=sentence line id, wc_line=explicit line id for a word-only clip that is not a pl clip)
SPEC = {
    "Ocotillo": dict(own="ocotiyo",    p=["okoteeyo", "ocoteeyoh", "Okohteeyo"],      dash="Oh-Koh-Tee-Yoh",   caps="OCOTIYO",    dcaps="oh-koh-TEE-yoh",   wc=12, sent="q12a"),
    "Vallecito": dict(own="vayaseetoe", p=["vayeseetoh", "vahyaseetoh", "Vayaseeto"],  dash="Vaya-See-Toe",     caps="VAYASEETOE", dcaps="VAYA-SEE-TOE",     wc=18, sent=None),
    "Olla":      dict(own="oya",        p=["oyah", "ohya", "Oyuh"],                    dash="Oy-Yah",           caps="OYA",        dcaps="OY-yah",           wc=26, sent="q26b"),
    "Yaqui":     dict(own="yacky",      p=["yackee", "yahkee", "Yakee"],               dash="Yah-Kee",          caps="YACKY",      dcaps="YAH-kee",          wc=32, sent=None),
    "Cholla":    dict(own="choya",      p=["choyah", "choyuh", "Chohya"],              dash="Choy-Yah",         caps="CHOYA",      dcaps="CHOY-yah",         wc=46, sent="q46a"),
    "Salado":    dict(own="sahlahdoh",  p=["salahdoe", "sahladoh", "Salahdo"],         dash="Sah-Lah-Doh",      caps="SAHLAHDOH",  dcaps="sah-LAH-doh",      wc=19, sent="q50a"),
    "Cabezas":   dict(own="kahbaysahs", p=["kabaysas", "cabaysahs", "Kahbaysas"],      dash="Kah-Bay-Sahs",     caps="KAHBAYSAHS", dcaps="kah-BAY-sahs",     wc=11, sent=None),
    "Cafe":      dict(own="kafay",      p=["cafay", "kahfay", "Kafay"],                dash="Ka-Fay",           caps="KAFAY",      dcaps="ka-FAY",           wc=None, wc_synth="Burro Bend Cafe.", sent="ch01-2"),
    "Burro":     dict(own="burroh",     p=["burrow", "buro", "Burrah"],                dash="Bur-Ro",           caps="BURRO",      dcaps="BUR-ro",           wc_line="ch06-2", sent="ch01-2", target="burro bend"),
}
ORDER = ["plain", "own", "title", "p1", "p2", "p3", "dash", "caps", "dcaps"]
SENT_CANDS = {"plain", "own", "p1", "dcaps"}   # sentence clips cost ~60 s a take on this Mac (vs ~14 s for a word clip): a 1-seed confirmation of four candidates is enough

def fmt_of(cid, s):
    """plain | lower | title | dashed (hyphens, no capital run) | allcaps (capital run, no hyphen) | dashedcaps (both)."""
    if cid == "plain": return "plain"
    caps = bool(re.search(r"[A-Z]{2,}", s))
    if "-" in s: return "dashedcaps" if caps else "dashed"
    if caps: return "allcaps"
    return "title" if s[0].isupper() else "lower"

def candidates(word, surface):
    sp = SPEC[word]
    c = {"plain": surface, "own": sp["own"], "title": sp["own"].capitalize()}
    c.update({f"p{i + 1}": v for i, v in enumerate(sp["p"])}); c.update(dash=sp["dash"], caps=sp["caps"], dcaps=sp["dcaps"])
    return [(cid, c[cid], fmt_of(cid, c[cid])) for cid in ORDER]

def clips(word, D):
    """-> list of dict(tag, kind, line_ids{voice: id}, text, max_sec, seeds, surface)."""
    L = {l["id"]: l for l in D["lines"]}; sp = SPEC[word]; out = []
    def mk(tag, kind, sr_id, seeds):
        l = L[sr_id]; text = l.get("tts_text", l["text"]); m = re.search(r"\b" + word + r"\b", text, re.I)
        ids = {"senior_ranger": sr_id}
        n = re.match(r"pl-sr-(\d+)$", sr_id)
        ids["ranger_273"] = f"pl-r273-{n.group(1)}" if n else sr_id
        return dict(tag=tag, kind=kind, ids=ids, text=text, max_sec=l.get("max_sec", 3.0), seeds=seeds, surface=m.group(), real_text=l["text"])
    if sp.get("wc"): out.append(mk(f"pl{sp['wc']}", "word", f"pl-sr-{sp['wc']}", 3))
    if sp.get("wc_synth"):       # no word-only clip exists: the first words of the real line, short enough to be cheap and to look like a place-name clip
        c = mk("ch012short", "word", "ch01-2", 3); c["text"] = sp["wc_synth"]; c["real_text"] = sp["wc_synth"]; c["max_sec"] = 2.5; out.append(c)
    if sp.get("wc_line"): out.append(mk(sp["wc_line"].replace("-", ""), "word", sp["wc_line"], 3))
    if sp.get("sent"): out.append(mk(sp["sent"].replace("-", ""), "sent", sp["sent"], 3 if not out else 1))
    return out

def slug(w): return re.sub(r"[^a-z0-9]", "", w.lower())

def plan(D, words, voices):
    items = []
    for w in words:
        for c in clips(w, D):
            for v in voices:
                for cid, spell, fm in candidates(w, c["surface"]):
                    if c["kind"] == "sent" and cid not in SENT_CANDS: continue
                    text = c["text"] if cid == "plain" else re.sub(r"\b" + re.escape(c["surface"]) + r"\b", lambda m: spell, c["text"], count=1, flags=re.I)
                    for s in range(1, c["seeds"] + 1):
                        fn = f"{slug(w)}__{VOICE_TAG[v]}__{c['tag']}__{fm}-{cid}__s{s}.wav"
                        items.append(dict(word=w, voice=v, clip=c["tag"], kind=c["kind"], line_id=c["ids"][v], cand=cid, fmt=fm, spelling=spell, text=text,
                                          real_text=c["real_text"], max_sec=c["max_sec"], seed=s, file=fn, target=SPEC[w].get("target", w.lower())))
    return items

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--words"); ap.add_argument("--voices"); ap.add_argument("--dry", action="store_true"); ap.add_argument("--out", default="audio-work/wordlab")
    ap.add_argument("--device", default="auto"); a = ap.parse_args()
    D = json.load(open("docs/audio-lines.json")); CAST = json.load(open("tools/audio/cast.json"))
    words = a.words.split(",") if a.words else list(SPEC); voices = a.voices.split(",") if a.voices else list(VOICE_TAG)
    items = plan(D, words, voices); os.makedirs(f"{a.out}/takes", exist_ok=True)
    print(len(items), "files planned;", len({(i["voice"], i["clip"], i["text"], i["seed"]) for i in items}), "distinct renders", flush=True)
    if a.dry:
        for i in items[:: max(1, len(items) // 40)]: print(i["file"], "|", i["text"])
        sys.exit(0)
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    import torch, torchaudio as ta
    from chatterbox.tts import ChatterboxTTS, punc_norm
    torch.set_num_threads(max(4, (os.cpu_count() or 8) // 2))
    dev = a.device if a.device != "auto" else ("mps" if torch.backends.mps.is_available() else "cpu")
    m = ChatterboxTTS.from_pretrained(device=dev); print("device", dev, flush=True)
    man_path = f"{a.out}/manifest.jsonl"; done = {json.loads(x)["file"] for x in open(man_path)} if os.path.exists(man_path) else set()
    man = open(man_path, "a"); first = {}; t_start = time.time(); n = 0
    for v in voices:
        c = CAST[v]; m.prepare_conditionals(f"audio-work/refs/{v}.wav", exaggeration=c["ex"])
        for it in [i for i in items if i["voice"] == v]:
            fp = f"{a.out}/takes/{it['file']}"
            key = (v, it["clip"], punc_norm(it["text"]), it["seed"])
            if it["file"] in done and os.path.exists(fp): first.setdefault(key, fp); continue
            rec = dict(it, ex=c["ex"], cfg=c["cfg"], temp=c.get("temp", 0.8), ref=f"audio-work/refs/{v}.wav", tts_input=punc_norm(it["text"]))
            if key in first and os.path.exists(first[key]):
                shutil.copyfile(first[key], fp); rec.update(dup_of=os.path.basename(first[key]), gen_s=0)
            else:
                cap = it["max_sec"] * 1.8 + 0.5       # same runaway guard as gen_lines.py
                torch.manual_seed(it["seed"]); t0 = time.time()
                try: w = m.generate(it["text"], exaggeration=c["ex"], cfg_weight=c["cfg"], temperature=c.get("temp", 0.8))
                except (RuntimeError, NotImplementedError) as e:
                    if dev != "mps": raise
                    print("MPS failed -> CPU:", repr(e)[:200], flush=True); dev = "cpu"; del m
                    m = ChatterboxTTS.from_pretrained(device="cpu"); m.prepare_conditionals(f"audio-work/refs/{v}.wav", exaggeration=c["ex"]); torch.manual_seed(it["seed"])
                    w = m.generate(it["text"], exaggeration=c["ex"], cfg_weight=c["cfg"], temperature=c.get("temp", 0.8))
                w = w[:, :int(m.sr * cap)].cpu(); ta.save(fp, w, m.sr); first[key] = fp
                rec.update(sec=round(w.shape[-1] / m.sr, 2), gen_s=round(time.time() - t0, 1)); n += 1
            if "sec" not in rec: rec["sec"] = None
            man.write(json.dumps(rec) + "\n"); man.flush()
            print(it["file"], rec.get("sec"), rec.get("gen_s"), "dup" if "dup_of" in rec else "", f"[{n} rendered, {round((time.time() - t_start) / 60, 1)} min]", flush=True)
    print("DONE", n, "rendered", round((time.time() - t_start) / 60, 1), "min", flush=True)
