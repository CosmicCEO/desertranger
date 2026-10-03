#!/usr/bin/env bash
# Batch driver for one voice phase (hand-off 8.13 + section 10 retake ladder). One heavy model at a time, always.
# usage: tools/audio/run_phase.sh <phase 2|3|4> [extra gen_lines args for the first pass]
# Run from the repo root. Resumable: gen_lines skips takes that exist, qa_check re-reads every take.
#   pass 1 : 3 takes per line (seeds 1-3)                     -> QA
#   rung 1 : FAIL ids, 3 more seeds (4-6)                     -> QA
#   rung 2 : FAIL ids, seeds 7-9, faster pacing (--ex 0.6 --cfg 0.65) -> QA     (9 takes per line is the cap)
# Then master.py for the phase. FAIL-after-ladder ids are listed in audio-work/fail-after-ladder-<phase>.txt
set -u
PHASE="${1:?phase}"; shift || true
cd "$(dirname "$0")/../.."
export PATH=/opt/homebrew/bin:$PATH
[ "$(git branch --show-current)" = "audio-build" ] || { echo "not on audio-build"; exit 1; }
mkdir -p audio-work
gen()  { ( . .venv-cb/bin/activate && python tools/audio/gen_lines.py "$@" ); }
qa()   { ( . .venv-tts/bin/activate && python tools/audio/qa_check.py "$@" ); }
fails() {  # ids of this phase whose QA status is not pass
  python3 - "$PHASE" <<'EOF'
import json, sys
ph = int(sys.argv[1]); L = {l["id"]: l for l in json.load(open("docs/audio-lines.json"))["lines"]}
s = json.load(open("audio-work/qa/summary.json"))
print(",".join(i for i, v in s.items() if i in L and L[i]["phase"] == ph and v["status"] != "pass"))
EOF
}
echo "== phase $PHASE pass 1 ($(date +%T))";  gen --phase "$PHASE" --takes 3 --device auto "$@" && qa --phase "$PHASE"
F=$(fails)
if [ -n "$F" ]; then echo "== rung 1 (more seeds) for: $F";  gen --ids "$F" --takes 3 --seed0 4 --device auto && qa --ids "$F"; fi
F=$(fails)
if [ -n "$F" ]; then echo "== rung 2 (faster pacing) for: $F"; gen --ids "$F" --takes 3 --seed0 7 --ex 0.6 --cfg 0.65 --device auto && qa --ids "$F"; fi
F=$(fails); echo "$F" | tr ',' '\n' | sed '/^$/d' > "audio-work/fail-after-ladder-$PHASE.txt"
echo "== FAIL-after-ladder (phase $PHASE): ${F:-none}"
python3 tools/audio/master.py --phase "$PHASE" && python3 tools/audio/build_review.py
echo "== phase $PHASE done ($(date +%T))"
