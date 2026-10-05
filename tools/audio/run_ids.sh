#!/usr/bin/env bash
# Retake ladder for an explicit list of line ids (Wave 2 regeneration; run_phase.sh is per phase and only runs on audio-build).
# usage: tools/audio/run_ids.sh <id,id,...> [extra gen_lines args for the faster-pacing rung, default "--ex 0.6 --cfg 0.65"]
# Run from the repo root. One heavy model at a time: generation, then Whisper, never together. Resumable (existing takes are skipped).
# MOVE the old takes of these ids out of audio-work/takes/ first (to audio-work/takes-old/): qa_check picks the best passing take across ALL takes.
#   pass 1 : 3 takes (seeds 1-3)                      -> QA
#   rung 1 : FAIL ids, 3 more seeds (4-6)             -> QA
#   rung 2 : FAIL ids, seeds 7-9, faster pacing       -> QA      (9 takes per line is the cap)
# Then master.py for the ids. Leftover failures: audio-work/fail-after-ladder-ids.txt. Lines with a per-line "gen" setting keep it unless the rung passes --ex/--cfg.
set -u
IDS="${1:?comma-separated ids}"; shift || true
FAST="${*:---ex 0.6 --cfg 0.65}"
cd "$(dirname "$0")/../.."
export PATH=/opt/homebrew/bin:$PATH
mkdir -p audio-work
gen()  { ( . .venv-cb/bin/activate && python tools/audio/gen_lines.py "$@" ); }
qa()   { ( . .venv-tts/bin/activate && python tools/audio/qa_check.py "$@" ); }
fails() {
  python3 - "$IDS" <<'PY'
import json, sys
want = sys.argv[1].split(","); s = json.load(open("audio-work/qa/summary.json"))
print(",".join(i for i in want if s.get(i, {}).get("status") != "pass"))
PY
}
echo "== pass 1 ($(date +%T))";  gen --ids "$IDS" --takes 3 --device auto && qa --ids "$IDS"
F=$(fails)
if [ -n "$F" ]; then echo "== rung 1 (more seeds) for: $F";  gen --ids "$F" --takes 3 --seed0 4 --device auto && qa --ids "$F"; fi
F=$(fails)
if [ -n "$F" ]; then echo "== rung 2 (faster pacing: $FAST) for: $F"; gen --ids "$F" --takes 3 --seed0 7 $FAST --device auto && qa --ids "$F"; fi
F=$(fails); echo "$F" | tr ',' '\n' | sed '/^$/d' > audio-work/fail-after-ladder-ids.txt
echo "== FAIL-after-ladder: ${F:-none}"
python3 tools/audio/master.py --ids "$IDS"
echo "== done ($(date +%T))"
