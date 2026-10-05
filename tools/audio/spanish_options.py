#!/usr/bin/env python3
"""Plain Python 3 + ffmpeg. Build the "Spanish options" for every line that contains a word of the shared respelling table
(docs/audio-lines.json "pronunciations"): up to 3 candidate readings, none of them ever heard by a human before the user picks.
  A = what shipped before Wave 2 / before this run (frozen copy in audio-work/takes-A/<id>/A.wav, scored by qa_check --takes-dir audio-work/takes-A --qa-dir audio-work/qa-A)
  B = best take with the user's respelling (all takes in audio-work/takes/<id>, scored in audio-work/qa/<id>.json)
  C = best take with the ALTERNATIVE respelling (pronunciation_alternatives; audio-work/takes-alt/<id>, scored in audio-work/qa-alt/<id>.json); only for the five Spanish words
usage: python3 tools/audio/spanish_options.py build        -> docs/spanish-options.json, desertranger/audio/alt/spanish/<id>-<A|B|C>.mp3, audio-work/spanish-opts/<id>-<L>.wav
The score is a PROXY, not a listening test: how closely the best 1-4 consecutive words in Whisper's UNPROMPTED transcript match the written word or the user's
respelling (difflib letter ratio, 0-1; mean over the table words in the line). A candidate must pass qa_check's STRICT gate (heard word within 1 character and the same syllable count of the real word or the respelling) with word errors <= allowed, and
have a length not beyond max(1.15 x max_sec, A's length + 0.2 s) when any candidate satisfies that. B/C replace A as the shipped clip only when A fails the strict gate or they score >= A + 0.10. If nothing passes strictly the least-bad B/C take ships marked FAIL.
Lines in TAINTED never ship A. Choose differently per clip later with  python3 tools/audio/apply_choice.py <id> <A|B|C>."""
import difflib, json, os, re, shutil, subprocess, sys
src = open("tools/audio/master.py").read().split("p = argparse.ArgumentParser()")[0]
exec(compile(src, "master.py", "exec"))            # ff, dur, norm_mp3, TRIM, RADIO, CLEAN, TARGET, KBPS, OUT
sys.path.insert(0, "tools/audio"); from pron import apply as apply_pron
D = json.load(open("docs/audio-lines.json")); L = {l["id"]: l for l in D["lines"]}; PRON = D["pronunciations"]
TAINTED = {"q50a"}          # the shipped take read the stress syllable letter by letter ("L A H")
ALT = f"{OUT}/alt/spanish"; STORE = "audio-work/spanish-opts"; os.makedirs(ALT, exist_ok=True); os.makedirs(STORE, exist_ok=True)
def toks(t): return re.sub(r"[^a-z ]", "", t.lower().replace("-", " ")).split()
def letters(t): return re.sub(r"[^a-z]", "", t.lower())
def score(line, heard):
    h = toks(heard); sc = []
    for k, v in PRON.items():
        if not re.search(r"\b" + k + r"\b", line["text"], re.I): continue
        wt, sp = letters(k), letters(v); best = 0
        for n in (1, 2, 3, 4):
            for i in range(len(h) - n + 1):
                j = "".join(h[i:i + n]); best = max(best, difflib.SequenceMatcher(None, j, wt).ratio(), difflib.SequenceMatcher(None, j, sp).ratio())
        sc.append(best)
    return round(sum(sc) / len(sc), 2) if sc else None
def pool(path, line):
    if not os.path.exists(path): return []
    q = json.load(open(path)); out = []
    for t in q["takes"]:
        heard = t.get("heard_plain") or t["heard"]
        out.append(dict(wav=t["file"], heard=heard, sec=t["sec"], errors=t["errors"], allowed=t["allowed"], score=score(line, heard),
                        strict_ok=bool(t.get("strict_ok")), words_ok=bool(t.get("strict_ok")) and t["errors"] <= t["allowed"], ok=bool(t["ok"]), pron=t.get("pron", []), rec=t))
    return out
def master_candidate(wav, line, out):
    t = line["treatment"]; tmp = f"{WORK}/opt.trim.wav"
    ff("-i", wav, "-af", f"aresample=48000,{TRIM}", "-ac", "1", tmp)
    d0 = dur(tmp); mx = line.get("max_sec", 9); tempo = f"atempo={min(1.15, d0 / mx):.3f}," if d0 > mx else ""
    ff("-i", tmp, "-af", f"{tempo}{RADIO if t == 'radio' else CLEAN}", "-ac", "1", f"{WORK}/opt.wav")
    norm_mp3(f"{WORK}/opt.wav", out, TARGET[t], KBPS[t])
def build():
    ids = [i for i, l in L.items() if any(re.search(r"\b" + k + r"\b", l["text"], re.I) for k in PRON)]
    res = {}; prev = json.load(open("docs/spanish-options.json")) if os.path.exists("docs/spanish-options.json") else {}
    for i in ids:
        l = L[i]; cap = l.get("max_sec", 9) * 1.15
        a = pool(f"audio-work/qa-A/{i}.json", l)
        if not a: print("no A score for", i); continue
        a = a[0]; a["wav"] = f"{STORE}/{i}-A.wav"; shutil.copy(f"audio-work/takes-A/{i}/A.wav", a["wav"]); a["src"] = f"audio-work/takes-A/{i}/A.wav"
        cands = {"A": a}
        for letter, p in (("B", pool(f"audio-work/qa/{i}.json", l)), ("C", pool(f"audio-work/qa-alt/{i}.json", l))):
            good = [t for t in p if t["words_ok"] and t["score"] is not None]       # STRICT gate only: a loose match is never a candidate for "pass"
            near = [t for t in good if t["sec"] <= max(cap, a["sec"] + 0.2)] or good
            if near:
                top = max(t["score"] for t in near)
                best = min([t for t in near if t["score"] >= top - 0.05], key=lambda t: t["sec"])      # near-ties go to the shorter take
            elif p:                                                                                   # nothing passes strictly: show the least-bad take, flagged
                best = max([t for t in p if t["score"] is not None] or p, key=lambda t: ((t["score"] or 0), -t["sec"]))
            else: continue
            best = dict(best); w = f"{STORE}/{i}-{letter}.wav"; shutil.copy(best["wav"], w); best["src"] = best["wav"]; best["wav"] = w
            best["rec"] = dict(best["rec"], file=w); cands[letter] = best
        strict = {k: v for k, v in cands.items() if v["words_ok"]}
        ship, why = "A", "no candidate scored 0.10 higher than the previous clip"
        if i in TAINTED: strict.pop("A", None)
        if not strict:
            alt = {k: v for k, v in cands.items() if not (k == "A" and i in TAINTED)}
            top = max((alt[k]["score"] or 0) for k in alt)
            ship = max([k for k in alt if (alt[k]["score"] or 0) >= top - 0.05], key=lambda k: ("CBA".index(k), -alt[k]["sec"]))      # near-ties keep the previous clip, then B before C; why = "NO candidate passes the strict pronunciation gate: least-bad take shipped, marked FAIL, needs the user's decision"
        else:
            better = {k: v for k, v in strict.items() if k != "A" and (("A" not in strict) or (v["score"] or 0) >= (a["score"] or 0) + 0.10)}
            if "A" in strict and not better: ship, why = "A", "previous clip already passes the strict gate and nothing scores 0.10 higher"
            else:
                pick = better or strict; top = max((pick[k]["score"] or 0) for k in pick)
                ship = max([k for k in pick if (pick[k]["score"] or 0) >= top - 0.05], key=lambda k: ("CBA".index(k), -pick[k]["sec"]))   # near-ties: user's respelling (B) before the alternative (C)
                why = f"best strict-gate pass (score {pick[ship]['score']}" + (f" vs {a['score']} for the previous clip" if "A" in cands else "") + ")" + (" (previous clip is tainted)" if i in TAINTED else "")
        for k, c in cands.items():
            if k != "A": master_candidate(c["wav"], l, f"{ALT}/{i}-{k}.mp3")
            c["mp3"] = f"alt/spanish/{i}-{k}.mp3"; c["mp3_sec"] = round(dur(f"{OUT}/{c['mp3']}"), 3)
            base = l.get("tts_text", l["text"])
            c["respelling_sent"] = {"A": "as written before: " + base, "B": apply_pron(base, PRON), "C": apply_pron(base, {**PRON, **D.get("pronunciation_alternatives", {})})}[k]
            c["respelling"] = {"A": "previous", "B": "user table (Title-Cased)", "C": "alternative"}[k]
        res[i] = dict(text=l["text"], max_sec=l.get("max_sec"), words=[k for k in PRON if re.search(r"\b" + k + r"\b", l["text"], re.I)], candidates=cands, recommended=ship, why=why, shipped=prev.get(i, {}).get("shipped", "A"))
        print(i, {k: (v["score"], v["sec"], "strict" if v["words_ok"] else "NO") for k, v in cands.items()}, "->", ship, flush=True)
    json.dump(res, open("docs/spanish-options.json", "w"), indent=1)
if __name__ == "__main__" and sys.argv[1:2] == ["build"]: build()
