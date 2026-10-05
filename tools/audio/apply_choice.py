#!/usr/bin/env python3
"""Plain Python 3 + ffmpeg, run in the audio worktree (needs audio-work/). Ship the user's choice for one Spanish-options clip.
usage: python3 tools/audio/apply_choice.py <clip-id> <A|B|C>     e.g.  python3 tools/audio/apply_choice.py pl-sr-18 C
  A = the reading that shipped before this run, B = the user's respelling, C = the alternative respelling (see desertranger/audio/review.html, "Spanish options").
It points the clip's QA pick at the chosen take (audio-work/spanish-opts/<id>-<L>.wav), runs the normal master.py path (radio/clean chain, loudness,
manifest.json entry), records the choice in docs/spanish-options.json ("shipped") and rebuilds review.html. Then run
  node dev/audio/review_check.js && node dev/audio/landing_test.js    and commit desertranger/audio/<clip file>, manifest.json, review.html, docs/spanish-options.json."""
import json, os, subprocess, sys
if len(sys.argv) != 3 or sys.argv[2] not in "ABC" or len(sys.argv[2]) != 1: sys.exit(__doc__)
i, L = sys.argv[1], sys.argv[2]
O = json.load(open("docs/spanish-options.json"))
if i not in O or L not in O[i]["candidates"]: sys.exit(f"no option {L} for {i}; options: {sorted(O.get(i, {}).get('candidates', {}))}")
wav = O[i]["candidates"][L]["wav"]
c = O[i]["candidates"][L]; qf = f"audio-work/qa/{i}.json"; q = json.load(open(qf)); q["pick"] = wav
rec = dict(c["rec"], file=wav); q["takes"] = [t for t in q["takes"] if t["file"] != wav] + [rec]         # keep the gate evidence of the chosen take
q["status"] = "pass" if rec["ok"] else "FAIL"; q["fail_reason"] = None if rec["ok"] else ("length only" if rec.get("strict_ok") and rec["errors"] <= rec["allowed"] else "pronunciation/words")
json.dump(q, open(qf, "w"), indent=1)
subprocess.run(["python3", "tools/audio/master.py", "--ids", i], check=True)
sf = "audio-work/qa/summary.json"; sm = json.load(open(sf)); sm[i] = dict(status=q["status"], fail_reason=q["fail_reason"], pick=wav, heard=rec["heard"], heard_plain=rec.get("heard_plain"), errors=rec["errors"], sec=rec["sec"], pron=rec.get("pron", [])); json.dump(sm, open(sf, "w"), indent=1)
O[i]["shipped"] = L; json.dump(O, open("docs/spanish-options.json", "w"), indent=1)
subprocess.run(["python3", "tools/audio/build_review.py"], check=True)
print("shipped", i, "=", L)
