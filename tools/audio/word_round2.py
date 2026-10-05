#!/usr/bin/env python3
"""Pick two candidate clips per owner-Not-OK card for the round 2 word check (issue #28). No models.
usage: python3 tools/audio/word_round2.py [--dir audio-work/wordlab] -> <dir>/round2.json (+ prints the ranking)
For each (word, voice) card: every conforming take (plain / lowercase / Title, letters only) of that word in that voice, except the exact clip the owner heard, must be WORD-CLEAN
(strict match, no fragmentation, no silence inside the word, no spelled letters, duration ok) AND have a clean LEADING-ARTIFACT check (word_lead.py: no burst/click/stray sound/
long lead-in/early onset/stray first token) to be eligible. Spellings are ranked by their rate of eligible takes, then mean similarity to the word; the top two distinct spellings
win (same spelling twice only if nothing else is eligible: then two different takes of it). Clip length (f) is not a filter: the word-only clips are mastered and length-capped later."""
import argparse, collections, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import word_metrics as wm

CARDS = [("Vallecito", "senior_ranger"), ("Olla", "senior_ranger"), ("Yaqui", "senior_ranger"), ("Yaqui", "ranger_273")]
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dir", default="audio-work/wordlab"); a = ap.parse_args(); d = a.dir
    rows = wm.load_metrics(d); lead = {json.loads(x)["file"]: json.loads(x) for x in open(f"{d}/lead.jsonl")}
    heard = {x["file"] for x in json.load(open(f"{d}/winners.json")).values() for x in [x]}      # the clips the owner already heard (round 1)
    man = {json.loads(x)["file"]: json.loads(x) for x in open(f"{d}/manifest.jsonl")}; out = []
    for w, v in CARDS:
        rs = [r for r in rows if r["word"] == w and r["voice"] == v and r["fmt"] in ("plain", "lower", "title") and r["kind"] == "word"]
        by = collections.defaultdict(list)
        for r in rs: by[r["spelling"].lower()].append(r)
        ranked = []
        for sp, ts in by.items():
            elig = [r for r in ts if r["v"]["clean"] and lead[r["file"]]["lead_ok"] and r["file"] not in heard]
            loose = [r for r in ts if r not in elig and all(r["v"][k] for k in ("b_frag", "c_nosilence", "d_noletters", "e_dur")) and r["v"]["soft"] >= 0.6 and lead[r["file"]]["lead_ok"] and r["file"] not in heard]
            ranked.append(dict(spelling=sp, n=len(ts), elig=elig, loose=loose, rate=len(elig) / len(ts), soft=sum(r["v"]["soft"] for r in ts) / len(ts), clean=sum(r["v"]["clean"] for r in ts), leadok=sum(lead[r["file"]]["lead_ok"] for r in ts)))
        ranked.sort(key=lambda c: (-c["rate"], -c["soft"]))
        print(f"\n== {w} / {v}: spelling, eligible/takes, word-clean, lead-clean, mean similarity")
        for c in ranked[:10]: print(f"   {c['spelling']:14} {len(c['elig'])}/{c['n']}  clean {c['clean']}  loose-ok {len(c['loose'])}  lead {c['leadok']}  sim {c['soft']:.2f}")
        pick = [c for c in ranked if c["elig"]][:2]
        best = lambda c: sorted(c["elig"] or c["loose"], key=lambda r: (-r["v"]["soft"], r["trimmed_sec"]))
        chosen = [(c["spelling"], best(c)[0]) for c in pick]
        if len(chosen) < 2:     # not enough strictly clean spellings: fill with spellings whose takes have no pause/letters/artifact and sound close (similarity >= 0.6) although the strict word match fails
            # (Whisper hears a correct "vayaseetoe" as "vaya sito"; the owner approved exactly such a Vallecito take on ranger_273)
            more = sorted([c for c in ranked if not c["elig"] and c["loose"] and c["spelling"] not in [x[0] for x in chosen]], key=lambda c: (-len(c["loose"]) / c["n"], -c["soft"]))
            chosen += [(c["spelling"], best(c)[0]) for c in more[:2 - len(chosen)]]
        if len(chosen) == 1 and len(pick[0]["elig"]) > 1: chosen.append((pick[0]["spelling"], best(pick[0])[1]))
        if len(chosen) < 2: print("   !! fewer than two eligible candidates");
        card = dict(word=w, voice=v, clip_text=man[chosen[0][1]["file"]]["real_text"] if chosen else "", n_eligible_spellings=len([c for c in ranked if c["elig"]]))
        for k, (sp, r) in enumerate(chosen, 1):
            card[f"c{k}"] = dict(file=r["file"], spelling=man[r["file"]]["spelling"], heard=r["transcript"], trimmed_sec=r["trimmed_sec"], lead_note="leading artifact check: clean" + ("" if r["v"]["clean"] else " (word match relaxed)"),
                                 lead_start=lead[r["file"]]["lead_start"], seed=r["seed"])
        out.append(card)
    json.dump(out, open(f"{d}/round2.json", "w"), indent=1); print("\nwrote", f"{d}/round2.json")
if __name__ == "__main__": main()
