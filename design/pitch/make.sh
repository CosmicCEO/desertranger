#!/usr/bin/env bash
# One command: build a pitch sheet, render it to NEW dated files, run the layout check, verify the PDF.
#   design/pitch/make.sh              main sheet (page 1 pitch + page 2 status)  -> desert-ranger-pitch-status-<date>
#   design/pitch/make.sh wave2        build-wave2.py                              -> desert-ranger-wave2-<date>
# Env: PITCH_PREFIX (default desert-ranger), PITCH_OUT (output folder), CHROME (browser path).
# Never overwrites: if the name exists it adds -2, -3 ... Exit 2 if the layout check finds overflow or overlap.
set -eu
cd "$(dirname "$0")/../.."
export PATH=/opt/homebrew/bin:$PATH
SHEET="${1:-}"; PREFIX="${PITCH_PREFIX:-desert-ranger}"; DATE=$(date +%Y-%m-%d)
[ -d dev/e2e/node_modules/playwright-core ] || { echo "need playwright-core: cd dev/e2e && npm install"; exit 1; }
[ -f design/pitch/fonts/Bungee-Regular.ttf ] && [ -d design/art/icons ] || { echo "fonts/art missing: unzip the assets zip at the repo root first"; exit 1; }
# output folder: explicit, else this checkout's art-binaries/pitch, else the main checkout's, else design/pitch/out
COMMON="$(cd "$(git rev-parse --git-common-dir)/.." && pwd)"
OUTDIR="${PITCH_OUT:-}"
[ -n "$OUTDIR" ] || for d in art-binaries/pitch "$COMMON/art-binaries/pitch"; do [ -d "$d" ] && { OUTDIR="$d"; break; }; done
OUTDIR="${OUTDIR:-design/pitch/out}"; mkdir -p "$OUTDIR"
BASE="$OUTDIR/$PREFIX-${SHEET:-pitch-status}-$DATE"; N=2; OUT="$BASE"
while [ -e "$OUT.pdf" ]; do OUT="$BASE-$N"; N=$((N+1)); done
LOG=$(mktemp); SHEET="$SHEET" node design/pitch/render.js "$OUT" | tee "$LOG"
HTML="design/pitch/$PREFIX-${SHEET:-pitch}.html"
SECTIONS=$(grep -o '<section class="sheet"' "$HTML" | wc -l | tr -d ' ')
PAGES=$(python3 -c "import re,sys;print(len(re.findall(rb'/Type\s*/Page(?![a-zA-Z])',open(sys.argv[1],'rb').read())))" "$OUT.pdf")
echo "pdf pages: $PAGES (sheets in html: $SECTIONS)  size: $(du -h "$OUT.pdf" | cut -f1)"
[ "$PAGES" = "$SECTIONS" ] || { echo "PAGE COUNT MISMATCH"; exit 1; }
for f in "$OUT.png" "$OUT-status.png"; do [ -f "$f" ] && echo "$f  $(sips -g pixelWidth -g pixelHeight "$f" | awk '/pixel/{printf "%s ", $2}')"; done
echo "NEXT: Read each PNG above and look at it; fix and re-run if anything is off."
if grep -q 'past its box\|overlaps' "$LOG"; then echo "LAYOUT PROBLEMS: fix before sending"; exit 2; fi
