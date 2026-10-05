#!/usr/bin/env bash
# Build a clean, upload-ready copy of desertranger/ for the web host (runbook: docs/DEPLOY-NS.md).
#   bash dev/make-deploy-folder.sh [SRC=desertranger] [OUT=deploy/desertranger]
# Run it in a checkout that has the binary assets (unzipped assets zip, or dev/make-assets.sh), i.e. the lab Mac clone.
#  - NEVER copies config.php (it holds the database login), the tests, or markdown files.
#  - NEVER copies audio/alt/ (option clips for the review page only; they are not in manifest.json).
#  - Keeps audio/review.html (the listening page) unless you run it with NO_REVIEW=1.
#  - Refuses to overwrite an existing OUT folder. Writes OUT plus DEPLOY-MANIFEST.txt next to it (every file and its size).
set -euo pipefail
SRC=${1:-desertranger}; OUT=${2:-deploy/desertranger}
warn=0; w() { echo "WARNING: $*"; warn=$((warn + 1)); }
[ -f "$SRC/api.php" ] || { echo "ERROR: $SRC/api.php not found; run from the repo root (or pass the folder)." >&2; exit 1; }
[ ! -e "$OUT" ] || { echo "ERROR: $OUT already exists; remove it or pass another folder." >&2; exit 1; }

# Everything the game needs that is NOT in git must be present in SRC.
[ -f "$SRC/assets/img/board-2000.jpg" ] || w "assets/img/board-2000.jpg missing (board picture)"
[ "$(ls "$SRC"/assets/img/pieces/*.png 2>/dev/null | wc -l)" -ge 8 ] || w "fewer than 8 vehicle pictures in assets/img/pieces"
[ "$(ls "$SRC"/assets/fonts/*.ttf 2>/dev/null | wc -l)" -ge 4 ] || w "fewer than 4 fonts in assets/fonts"
[ "$(ls "$SRC"/assets/audio/*.mp3 2>/dev/null | wc -l)" -ge 2 ] || w "crowd clips missing in assets/audio"
[ -f "$SRC/audio/manifest.json" ] || w "audio/manifest.json missing (the sound files)"
if [ ! -f "$SRC/board/desert-ranger.json" ]; then
  if [ -f "$(dirname "$SRC")/board/desert-ranger.json" ]; then mkdir -p "$SRC/board" && cp "$(dirname "$SRC")/board/desert-ranger.json" "$SRC/board/" && echo "copied the master board JSON into $SRC/board/"
  else w "board/desert-ranger.json missing (api.php?a=board will fail)"; fi
fi

excl=(--exclude 'config.php' --exclude 'tests/' --exclude '*.md' --exclude '.DS_Store' --exclude '._*' --exclude '*.log' --exclude '.git*' --exclude 'audio/alt/')   # audio/alt/ = listening options (R55 slowed call sign, Spanish-word alternatives): never played by the game, never uploaded
[ "${NO_REVIEW:-0}" = "1" ] && excl+=(--exclude 'audio/review.html')
mkdir -p "$OUT"
rsync -a "${excl[@]}" "$SRC"/ "$OUT"/

# Safety nets: the database login must not be in the upload.
[ ! -e "$OUT/config.php" ] || { echo "ERROR: config.php ended up in $OUT; aborting." >&2; rm -f "$OUT/config.php"; exit 1; }
if grep -rIlE "db_pass'[[:space:]]*=>[[:space:]]*'[^']+'" "$OUT" 2>/dev/null | grep -v 'config.sample.php' | grep -q .; then
  echo "ERROR: a file in $OUT looks like it contains a database password; aborting." >&2; exit 1; fi

# PHP syntax check with whatever php is on the PATH (set PHP=/path/to/php to pick one, e.g. MAMP's 7.4).
PHPBIN=${PHP:-$(command -v php || true)}
if [ -n "$PHPBIN" ]; then bad=0; while IFS= read -r f; do "$PHPBIN" -l "$f" >/dev/null 2>&1 || { echo "PHP syntax error: $f"; bad=1; }; done < <(find "$OUT" -name '*.php'); [ $bad -eq 0 ] || exit 1; echo "PHP syntax OK ($("$PHPBIN" -r 'echo PHP_VERSION;'))"; else w "no php found: syntax not checked"; fi

(cd "$OUT" && find . -type f | sort | sed 's|^\./||' | while IFS= read -r f; do printf '%10d  %s\n' "$(wc -c < "$f")" "$f"; done) > "$(dirname "$OUT")/DEPLOY-MANIFEST.txt"
n=$(find "$OUT" -type f | wc -l | tr -d ' '); kb=$(du -sk "$OUT" | cut -f1)
echo "Upload folder: $OUT  ($n files, $((kb / 1024)) MB)   manifest: $(dirname "$OUT")/DEPLOY-MANIFEST.txt"
echo "Top level: $(ls "$OUT" | tr '\n' ' ')"
[ $warn -eq 0 ] && echo "All checks passed." || echo "$warn warning(s): fix them before uploading."
