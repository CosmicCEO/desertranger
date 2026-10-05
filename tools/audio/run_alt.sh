#!/usr/bin/env bash
# Spanish option C: takes with the ALTERNATIVE respellings (docs/audio-lines.json "pronunciation_alternatives"), scored by the same strict gate.
# usage: tools/audio/run_alt.sh <id,id,...>      (run from the repo root; one heavy model at a time)
# 6 takes (seeds 1-6) -> QA; ids still failing the strict gate get seeds 7-12, then 13-20. Takes: audio-work/takes-alt/<id>/, QA: audio-work/qa-alt/.
# Nothing here touches manifest.json or audio-work/takes: build the options afterwards with  python3 tools/audio/spanish_options.py build
set -u
IDS="${1:?comma-separated ids}"; cd "$(dirname "$0")/../.."; export PATH=/opt/homebrew/bin:$PATH
gen() { ( . .venv-cb/bin/activate && python tools/audio/gen_lines.py --pron-alt "$@" ); }
qa()  { ( . .venv-tts/bin/activate && python tools/audio/qa_check.py --takes-dir audio-work/takes-alt --qa-dir audio-work/qa-alt "$@" ); }
fails() { python3 - "$IDS" <<'PY'
import json, sys
s = json.load(open("audio-work/qa-alt/summary.json"))
print(",".join(i for i in sys.argv[1].split(",") if s.get(i, {}).get("fail_reason") == "pronunciation/words"))
PY
}
echo "== alt pass 1 (seeds 1-6) $(date +%T)"; gen --ids "$IDS" --takes 6 --device auto && qa --ids "$IDS"
F=$(fails); if [ -n "$F" ]; then echo "== alt rung 1 (seeds 7-12) for: $F"; gen --ids "$F" --takes 6 --seed0 7 --device auto && qa --ids "$F"; fi
F=$(fails); if [ -n "$F" ]; then echo "== alt rung 2 (seeds 13-20) for: $F"; gen --ids "$F" --takes 8 --seed0 13 --device auto && qa --ids "$F"; fi
echo "== alt done: still failing the strict gate: $(fails) ($(date +%T))"
