#!/usr/bin/env python3
"""Report + winners for the word lab (issue #28). Called by word_metrics.py --report (no heavy models here).
Writes <dir>/report.md and <dir>/winners.json and rewrites the "pronunciations" table block of docs/audio-lines.json with the ranked winners
(default = best pooled over both voices; per-voice override only where that voice's best candidate is strictly better for it).
Only conforming formats (plain / lower / title) can win; dashed / allcaps / dashedcaps are controls that show what the old format does."""
import collections, json, os, re

FMTS = ["plain", "lower", "title", "dashed", "allcaps", "dashedcaps"]
FMT_NAME = {"plain": "plain written word", "lower": "lowercase (dash-free)", "title": "Title-case", "dashed": "dashed (Vaya-See-Toe)", "allcaps": "ALL-CAPS (VAYASEETOE)", "dashedcaps": "dashes + capital syllable (VAYA-SEE-TOE, sah-LAH-doh)"}
PREF = {"plain": 0, "own": 1, "title": 2, "p1": 3, "p2": 4, "p3": 5}
OWNER_WORDS = {"Ocotillo", "Vallecito", "Olla", "Yaqui", "Cholla"}   # the owner asked for a respelling: within noise his respelling goes first and plain is the "next" card
MARGIN = 0.25    # with 3-4 takes per candidate and a weak judge (Whisper small.en), a rate gap below this is noise: the preferred form (owner's respelling, or plain for the other words) keeps the slot

def choose(cl, word, own=None):
    """Best candidate of an already ranked list: the top one, unless the preferred form is within MARGIN of it.
    Preferred = the owner's respelling (any capitalisation) for his five words, plain for the others."""
    top = cl[0]
    pref = next((c for c in cl if own and c["cand"] in ("own", "title") and c["spelling"].lower() == own), None) if word in OWNER_WORDS else next((c for c in cl if c["cand"] == "plain"), None)
    if pref is not None and top["rate"] - pref["rate"] < MARGIN: return pref
    return top
VOICES = ["senior_ranger", "ranger_273"]; WORD_ORDER = ["Ocotillo", "Vallecito", "Olla", "Yaqui", "Cholla", "Salado", "Cabezas", "Cafe", "Burro"]
CRIT = [("a_match", "strict word match"), ("b_frag", "no fragmentation"), ("c_nosilence", "no silence inside word"), ("d_noletters", "no spelled letters"), ("e_dur", "duration ok"), ("f_len", "clip length ok")]

def pct(n, d): return f"{100 * n / d:.0f}%" if d else "-"
def cell(rs): return f"{sum(r['v']['clean'] for r in rs)}/{len(rs)} ({sum(r['v']['ok'] for r in rs)})" if rs else "-"

def rank(rows, word, voices):
    """-> ranked list of candidate dicts (conforming formats only) for a word pooled over the given voices."""
    by = collections.defaultdict(list)
    for r in rows:
        if r["word"] == word and r["voice"] in voices and r["fmt"] in ("plain", "lower", "title"): by[r["cand"]].append(r)
    out = []
    for cid, rs in by.items():
        out.append(dict(cand=cid, spelling=rs[0]["spelling"], fmt=rs[0]["fmt"], n=len(rs), passed=sum(r["v"]["clean"] for r in rs), full=sum(r["v"]["ok"] for r in rs), rate=sum(r["v"]["clean"] for r in rs) / len(rs), rate_full=sum(r["v"]["ok"] for r in rs) / len(rs),
                        soft=sum(r["v"]["soft"] for r in rs) / len(rs), matched=sum(r["v"]["a_match"] for r in rs)))
    out.sort(key=lambda c: (-c["rate"], -c["rate_full"], -c["soft"], PREF.get(c["cand"], 9)))
    # two candidates with the same spelling (e.g. own and title when the word starts the clip) are one choice
    seen, uniq = set(), []
    for c in out:
        if c["spelling"].lower() in seen and c["cand"] != "plain": continue
        seen.add(c["spelling"].lower()); uniq.append(c)
    return uniq

def best_take(rows, word, voice, cand):
    rs = [r for r in rows if r["word"] == word and r["voice"] == voice and r["cand"] == cand]
    wc = [r for r in rs if r["kind"] == "word"] or rs     # the word-only clip is the shortest sensible clip
    return sorted(wc, key=lambda r: (not r["v"]["ok"], not r["v"]["clean"], not r["v"]["a_match"], -r["v"]["soft"], r["trimmed_sec"]))[0]

def main(d, rows):
    L = []; W = L.append
    nt = len(rows); words = [w for w in WORD_ORDER if any(r["word"] == w for r in rows)]
    W("# Word lab report (issue #28)\n")
    W(f"{nt} takes scored ({len(words)} words x 2 voices x 9 candidate spellings x seeds, inside the real clip text). Whisper small.en with word timestamps plus ffmpeg silencedetect (-35 dB, 80 ms). "
      "A take PASSES only if all of: (a) strict word match, (b) no fragmentation (1 token or gaps < 120 ms), (c) no silence inside the word span, (d) no spelled-out letters, "
      "(e) word duration <= 1.3x the median for that word/voice/clip, (f) clip length <= max_sec x 1.15. WORD-CLEAN = a-e (the word itself reads cleanly; length is a pacing issue the regeneration step can still fix); candidates are ranked by word-clean rate first, then full pass. **I cannot hear audio: every number here is a measurement from the transcript and the waveform, not a listening verdict. The owner's word check is the final gate.**\n")
    # ---- by format overall
    W("## 1. What each format does (all words, both voices)\n")
    W("| format | takes | word-clean (a-e) | PASS (a-f) | strict match (a) | fragmented (b fails) | pause inside word (c fails) | spelled letters (d fails) | too long/odd duration (e fails) |")
    W("|---|---|---|---|---|---|---|---|---|")
    for f in FMTS:
        rs = [r for r in rows if r["fmt"] == f]
        if not rs: continue
        W(f"| {FMT_NAME[f]} | {len(rs)} | {pct(sum(r['v']['clean'] for r in rs), len(rs))} | {pct(sum(r['v']['ok'] for r in rs), len(rs))} | {pct(sum(r['v']['a_match'] for r in rs), len(rs))} | {pct(sum(not r['v']['b_frag'] for r in rs), len(rs))} | "
          f"{pct(sum(not r['v']['c_nosilence'] for r in rs), len(rs))} | {pct(sum(not r['v']['d_noletters'] for r in rs), len(rs))} | {pct(sum(not r['v']['e_dur'] for r in rs), len(rs))} |")
    W("\n(the last four columns are FAILURE rates: higher is worse. 'pause inside word' counts takes where a silence >= 80 ms lies inside the time span Whisper gives the word.)\n")
    # ---- by format per word per voice
    W("## 2. By format, per word and voice: word-clean takes / takes (full a-f passes in brackets)\n")
    for v in VOICES:
        W(f"### {v}\n"); W("| format | " + " | ".join(words) + " |"); W("|---|" + "---|" * len(words))
        for f in FMTS:
            W(f"| {FMT_NAME[f]} | " + " | ".join(cell([r for r in rows if r["word"] == w and r["voice"] == v and r["fmt"] == f]) for w in words) + " |")
        W("")
    # ---- evidence
    W("## 3. Pause or literal reading? (measured)\n")
    sp = collections.Counter(); ps = collections.Counter(); tot = collections.Counter()
    for r in rows:
        tot[r["fmt"]] += 1; sp[r["fmt"]] += not r["v"]["d_noletters"]; ps[r["fmt"]] += (not r["v"]["c_nosilence"]) or (not r["v"]["b_frag"])
    for f in FMTS:
        if tot[f]: W(f"- **{FMT_NAME[f]}**: spelled-out letters in {sp[f]}/{tot[f]} takes ({pct(sp[f], tot[f])}); pause or gap inside the word in {ps[f]}/{tot[f]} ({pct(ps[f], tot[f])}).")
    W("")
    def ex(label, pred, k=4):
        W(f"**{label}**\n")
        n = 0
        for r in rows:
            if pred(r) and n < k:
                n += 1; si = [w.get("silence_inside") for w in r["words"] if w.get("silence_inside")]
                W(f"- `{r['file']}` sent as `{r['spelling']}`: heard \"{r['transcript']}\"" + (f"; silence inside word at {si}" if si else "") + (f"; caps tokens {r['capstok']}" if r["capstok"] else ""))
        if not n: W("- (none observed)")
        W("")
    ex("Examples: spelled-out letters / capital tokens", lambda r: not r["v"]["d_noletters"])
    ex("Examples: pauses inside a word (dashed formats)", lambda r: r["fmt"] in ("dashed", "dashedcaps") and not r["v"]["c_nosilence"])
    ex("Examples: pauses inside a word (conforming formats)", lambda r: r["fmt"] in ("plain", "lower", "title") and not r["v"]["c_nosilence"])
    # ---- winners
    W("## 4. Ranked candidates and winners (conforming formats only)\n")
    winners = {}; table = {}
    for w in words:
        pooled = rank(rows, w, VOICES); perv = {v: rank(rows, w, [v]) for v in VOICES}
        own = next((r['spelling'].lower() for r in rows if r['word'] == w and r['cand'] == 'own'), None); default = choose(pooled, w, own); entry = {"default": default["spelling"]}
        W(f"### {w}\n"); W("| voice | rank | spelling | format | word-clean/takes | full pass | mean similarity |"); W("|---|---|---|---|---|---|---|")
        for v in VOICES:
            for i, c in enumerate(perv[v][:4]): W(f"| {v} | {i + 1} | `{c['spelling']}` | {c['fmt']} | {c['passed']}/{c['n']} | {c['full']} | {c['soft']:.2f} |")
        for v in VOICES:
            dv = next((c for c in perv[v] if c["spelling"].lower() == default["spelling"].lower()), None); top = choose(perv[v], w, own)
            if top["spelling"].lower() != default["spelling"].lower() and dv is not None and top["rate"] >= dv["rate"] + 0.34: entry[v] = top["spelling"]
        use = {v: entry.get(v, entry["default"]) for v in VOICES}
        nopass = {v: next(c for c in perv[v] if c["spelling"].lower() == use[v].lower())["passed"] == 0 for v in VOICES}
        for v in VOICES:
            cl = perv[v]; mine = next(i for i, c in enumerate(cl) if c["spelling"].lower() == use[v].lower())
            nxt = next((c for c in cl if c["spelling"].lower() != use[v].lower()), None)     # the best other candidate, ready if the owner says Not OK
            t1 = best_take(rows, w, v, cl[mine]["cand"]); t2 = best_take(rows, w, v, nxt["cand"]) if nxt else None
            winners[f"{w}|{v}"] = dict(word=w, voice=v, spelling=use[v], cand=cl[mine]["cand"], passed=cl[mine]["passed"], n=cl[mine]["n"], no_passing=nopass[v], file=t1["file"], clip=t1["clip"],
                                       heard=t1["transcript"], next=dict(spelling=nxt["spelling"], cand=nxt["cand"], passed=nxt["passed"], n=nxt["n"], file=t2["file"], heard=t2["transcript"]) if nxt else None)
        W(f"\n**Table entry:** `{json.dumps(entry)}`" + ("  (**no word-clean take for: " + ", ".join(v for v in VOICES if nopass[v]) + " -- best available shown, owner check decides**)" if any(nopass.values()) else "") + "\n")
        table[w] = entry
    W("## 5. Winners, one line each\n"); W("| word | voice | spelling | word-clean/takes | heard in the chosen take |"); W("|---|---|---|---|---|")
    for k, x in winners.items(): W(f"| {x['word']} | {x['voice']} | `{x['spelling']}` | {x['passed']}/{x['n']}{' NO CLEAN TAKE' if x['no_passing'] else ''} | {x['heard']} |")
    old = "audio-work/wordlab/old-takes-metrics.json"
    if os.path.exists(old):
        W("\n## 6. Did the new metrics flag takes the old gate passed? (old Wave 2 takes, q12a and pl-sr-18)\n")
        W("| clip | dir | take | old gate strict/ok | new verdict | failed criteria | heard | silence inside |"); W("|---|---|---|---|---|---|---|---|---|")
        for r in json.load(open(old)):
            o = r["old"]; v = r["v"]; failed = [n for k, n in CRIT if not v[k]]
            W(f"| {r['id']} | {r['dir']} | {r['take']} | {(str(o['strict_ok']) + '/' + str(o['ok'])) if o else '-'} | {'PASS' if v['ok'] else 'FAIL'} | {', '.join(failed) or '-'} | {v['heard']} | {[w.get('silence_inside') for w in r['m']['words'] if w.get('silence_inside')] or '-'} |")
    op = "audio-work/wordlab/old-passed-metrics.json"
    if os.path.exists(op):
        R = json.load(open(op)); passed = [r for r in R if r["old"]["ok"]]; flagged = [r for r in passed if not r["v"]["ok"]]
        W(f"\n## 7. Old takes the OLD gate passed (ok=True) for Ocotillo/Vallecito, re-scored: {len(flagged)} of {len(passed)} flagged\n")
        W("| clip | dir | take | old gate | new verdict | failed criteria | heard | silence inside the word (s) |"); W("|---|---|---|---|---|---|---|---|")
        for r in passed:
            v = r["v"]; failed = [n for k, n in CRIT if not v[k]]
            W(f"| {r['id']} | {r['dir']} | {r['take']} | PASS | {'PASS' if v['ok'] else 'FLAGGED'} | {', '.join(failed) or '-'} | {v['heard']} | {[w.get('silence_inside') for w in r['m']['words'] if w.get('silence_inside')] or '-'} |")
    open(f"{d}/report.md", "w").write("\n".join(L) + "\n"); json.dump(winners, open(f"{d}/winners.json", "w"), indent=1)
    write_table(table); print("wrote", f"{d}/report.md", f"{d}/winners.json", "and the pronunciations table;", sum(x["no_passing"] for x in winners.values()), "word/voice pairs with no passing take")

def write_table(new):
    p = "docs/audio-lines.json"; s = open(p).read(); D = json.loads(s); table = D["pronunciations"]
    for w, e in new.items():
        if w == "Burro" and e["default"].lower() == "burro" and len(e) == 1: table.pop(w, None); continue      # plain wins: nothing to respell
        table[w] = e
    rows = []
    for k, v in table.items(): rows.append(f"  {json.dumps(k)}: " + json.dumps(v if isinstance(v, dict) else {"default": v}))
    block = ' "pronunciations": {\n' + ",\n".join(rows) + "\n },\n"
    a = s.index(' "pronunciations": {'); b = s.index("\n },\n", a) + len("\n },\n")
    open(p, "w").write(s[:a] + block + s[b:]); json.loads(open(p).read())
