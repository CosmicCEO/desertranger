#!/usr/bin/env python3
"""Promote the EXACT lab takes the owner approved in the word check (issue #28) into the normal pipeline so master.py can ship them.
usage: python3 tools/audio/promote_takes.py <exact-takes.json> [--ids pl-sr-12,...]
<exact-takes.json> maps line id -> lab take file in audio-work/wordlab/takes/. For each id: the old takes of the line move to audio-work/takes-prev28/<id>/ (qa_check picks the
best take across ALL takes in the folder, so they must not stay), the lab wav becomes audio-work/takes/<id>/lab.wav, and audio-work/qa/<id>.json is written with status
"owner-approved" and the lab metrics (heard text, leading-artifact flags, pauses) as evidence. master.py then masters it like any other pick and registers qa=owner-approved."""
import json, os, shutil, sys
ids = sys.argv[sys.argv.index("--ids") + 1].split(",") if "--ids" in sys.argv else None
M = json.load(open(sys.argv[1])); lab = "audio-work/wordlab"
met = {json.loads(x)["file"]: json.loads(x) for x in open(f"{lab}/metrics.jsonl")}
lead = {json.loads(x)["file"]: json.loads(x) for x in open(f"{lab}/lead.jsonl")} if os.path.exists(f"{lab}/lead.jsonl") else {}
L = {l["id"]: l for l in json.load(open("docs/audio-lines.json"))["lines"]}
summ = json.load(open("audio-work/qa/summary.json")) if os.path.exists("audio-work/qa/summary.json") else {}
for i, f in M.items():
    if ids and i not in ids: continue
    d = f"audio-work/takes/{i}"
    if os.path.isdir(d): os.makedirs("audio-work/takes-prev28", exist_ok=True); shutil.rmtree(f"audio-work/takes-prev28/{i}", ignore_errors=True); shutil.move(d, f"audio-work/takes-prev28/{i}")
    os.makedirs(d); dst = f"{d}/lab.wav"; shutil.copyfile(f"{lab}/takes/{f}", dst); r = met[f]
    ev = dict(file=dst, lab_take=f, heard=r["transcript"], heard_plain=r["transcript"], errors=0, allowed=0, sec=r["trimmed_sec"], ok=True, strict_ok=True, pron=[], spelled=r["spelled"],
              pauses_inside_word=[w.get("silence_inside") for w in r["words"]], lead_flags=lead.get(f, {}).get("flags", []), note="exact take the owner heard and approved in the word check")
    json.dump(dict(id=i, text=L[i]["text"], status="owner-approved", fail_reason=None, pick=dst, takes=[ev]), open(f"audio-work/qa/{i}.json", "w"), indent=1)
    summ[i] = dict(status="owner-approved", fail_reason=None, pick=dst, heard=r["transcript"], heard_plain=r["transcript"], errors=0, sec=r["trimmed_sec"], pron=[])
    print("promoted", i, "<-", f)
json.dump(summ, open("audio-work/qa/summary.json", "w"), indent=1)
