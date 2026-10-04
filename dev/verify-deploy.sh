#!/usr/bin/env bash
# Checks a deployed Desert Ranger (runbook: docs/DEPLOY-NS.md).
#   bash dev/verify-deploy.sh https://YOURDOMAIN/desertranger [--full]
# Without --full it only READS pages: it never creates a game or writes to the database.
# --full also plays complete games through the live API with the repo's PHP tests (needs `php` on this Mac). That creates a
#   few finished test rooms in the database: remove them afterwards with dev/cleanup-test-rooms.sql.
# Exit code 0 = no FAIL (warnings are advice). Prints OK / WARN / FAIL lines; never prints secrets.
set -uo pipefail
BASE=${1:?usage: verify-deploy.sh https://YOURDOMAIN/desertranger [--full]}; BASE=${BASE%/}; FULL=${2:-}
pass=0; fails=0; warns=0
ok()   { pass=$((pass + 1));   echo "  OK    $*"; }
warn() { warns=$((warns + 1)); echo "  WARN  $*"; }
bad()  { fails=$((fails + 1)); echo "  FAIL  $*"; }
code() { curl -s -m 20 -o /dev/null -w '%{http_code}' "$1"; }
body() { curl -s -m 20 "$1"; }
ctype() { curl -s -m 20 -o /dev/null -w '%{content_type}' "$1"; }

echo "Checking $BASE"
case "$BASE" in https://*) ok "HTTPS address" ;; *) warn "plain http: fine for testing, but turn on the host's SSL certificate for real use" ;; esac

echo "PHP and the database"
t=$(body "$BASE/api.php?a=time"); grep -q '"ok":true' <<<"$t" && ok "api.php?a=time answers (PHP runs)" || bad "api.php?a=time did not answer with {\"ok\":true,...}. NOTE: on this host a PHP file that is missing ALSO answers 500, so first check api.php was uploaded (got: $(echo "$t" | head -c 80 | tr -d '\n'))"
i=$(body "$BASE/api.php?a=info"); grep -q 'bronco-orange' <<<"$i" && ok "api.php?a=info lists the vehicles (config.php and the database login work)" || bad "api.php?a=info failed: config.php missing/wrong, tables not installed, or database unreachable  (got: $(echo "$i" | head -c 120))"
b=$(body "$BASE/api.php?a=board"); grep -q '"squares"' <<<"$b" && ok "api.php?a=board returns the board (board/desert-ranger.json uploaded)" || bad "api.php?a=board has no board data: upload desertranger/board/desert-ranger.json"

echo "Pages and files"
ix=$(body "$BASE/index.html"); [ "$(code "$BASE/index.html")" = 200 ] && grep -q 'Desert' <<<"$ix" && ok "index.html" || bad "index.html missing or wrong"
for p in assets/css/style.css assets/js/app.js assets/js/radio.js assets/js/ambience.js assets/js/sync.js assets/js/board.js assets/img/board-2000.jpg about.html assets/img/about-ranger.jpg assets/img/pieces/bronco-orange.png assets/fonts/Bungee-Regular.ttf assets/audio/crowd-cheer-v2.mp3; do
  [ "$(code "$BASE/$p")" = 200 ] && ok "$p" || bad "$p is missing (200 expected)"; done

echo "Sound"
m=$(body "$BASE/audio/manifest.json"); grep -q '"clips"' <<<"$m" && ok "audio/manifest.json ($(grep -o '"file"' <<<"$m" | wc -l | tr -d ' ') clips listed)" || bad "audio/manifest.json missing"
ct=$(ctype "$BASE/audio/dice/dice-clatter-01.mp3"); case "$ct" in audio/mpeg*) ok "mp3 files are served as audio/mpeg" ;; *) bad "dice-clatter-01.mp3 is served as '$ct' (expected audio/mpeg)" ;; esac
[ "$(code "$BASE/audio/amb/amb-bed-01.mp3")" = 200 ] && ok "audio/amb/amb-bed-01.mp3" || bad "audio/amb/amb-bed-01.mp3 missing"
[ "$(code "$BASE/audio/review.html")" = 200 ] && ok "audio/review.html (the listening page) is there" || warn "audio/review.html not found (fine only if you deliberately left it out)"

echo "Protection (these should NOT be readable)"
c=$(body "$BASE/config.php"); if grep -qiE "db_pass|db_user|password" <<<"$c"; then bad "config.php is READABLE and contains settings: block it NOW (check .htaccess) and change the database password"; else ok "config.php does not leak its contents (status $(code "$BASE/config.php"))"; fi
for p in config.sample.php lib/schema.sql lib/game.php; do
  s=$(code "$BASE/$p"); case "$s" in 403|404) ok "$p is blocked ($s)" ;; 200) [ "$p" = "lib/game.php" ] && { g=$(body "$BASE/$p"); grep -q '<?php' <<<"$g" && bad "lib/game.php is served as TEXT: PHP source is exposed" || ok "lib/game.php runs as PHP (empty output)"; } || warn "$p is readable (not secret, but .htaccess did not block it)" ;; *) warn "$p returned $s" ;; esac; done
[ "$(code "$BASE/install.php")" = 200 ] && warn "install.php is still there: after the tables exist, delete it (it refuses to run again, but remove it anyway)" || ok "install.php is gone (or blocked)"

echo "Caching (the host puts a cache in front of the site)"
h=$(curl -sI -m 20 "$BASE/api.php?a=time"); grep -qi 'no-store' <<<"$h" && ok "api.php replies carry Cache-Control: no-store" || warn "api.php replies are not marked no-store (expected only while api.php is not answering yet)"
grep -qi '^age: *[1-9]' <<<"$h" && bad "api.php?a=time was served from a cache (Age header): game state would be stale" || ok "api.php replies are not served from a cache (no Age header)"
t1=$(body "$BASE/api.php?a=time" | grep -o '"t":[0-9]*' | cut -d: -f2); sleep 1.2; t2=$(body "$BASE/api.php?a=time" | grep -o '"t":[0-9]*' | cut -d: -f2)
if [ -z "${t1:-}" ] || [ -z "${t2:-}" ]; then warn "two-calls cache test skipped: api.php?a=time is not answering yet"
elif [ $((t2 - t1)) -ge 1000 ]; then ok "two api.php?a=time calls 1.2 s apart return different times (not cached)"
else bad "api.php?a=time returned (nearly) the same time twice: a cache is answering instead of PHP"; fi
for p in index.html audio/manifest.json; do
  ma=$(curl -sI -m 20 "$BASE/$p" | tr -d '\r' | grep -i '^cache-control' | grep -o 'max-age=[0-9]*' | cut -d= -f2)
  if [ -z "${ma:-}" ]; then ok "$p has no long cache time"; elif [ "$ma" -le 600 ]; then ok "$p is cached at most ${ma} s"; else warn "$p is cached for ${ma} s: after an update players may see the old version for that long (check the .htaccess Expires lines, or ask the host)"; fi
done

echo "Speed"
ms=$(curl -s -m 20 -o /dev/null -w '%{time_total}' "$BASE/api.php?a=time" | awk '{printf "%d", $1 * 1000}'); [ "${ms:-9999}" -lt 800 ] && ok "api.php?a=time answered in ${ms} ms" || warn "api.php?a=time took ${ms} ms (the game polls once a second per phone)"

if [ "$FULL" = "--full" ]; then
  echo "Full games through the live API (creates finished test rooms)"
  here=$(cd "$(dirname "$0")/.." && pwd); PHPBIN=${PHP:-$(command -v php || true)}
  if [ -z "$PHPBIN" ]; then warn "no php on this Mac: skipped --full"; else
    for n in 4; do "$PHPBIN" "$here/desertranger/tests/simulate_game.php" "$BASE" $n 2>&1 | grep -q 'ALL PASSED' && ok "simulate_game.php ($n players) ALL PASSED" || bad "simulate_game.php ($n players) failed: run it by hand to see which check"; done
    "$PHPBIN" "$here/desertranger/tests/demo_game.php" "$BASE" 2>&1 | grep -q 'ALL PASSED' && ok "demo_game.php ALL PASSED (solo demo + the 2-player minimum)" || bad "demo_game.php failed: run it by hand to see which check"
  fi
fi
echo; echo "$pass OK, $warns warning(s), $fails FAIL"
[ $fails -eq 0 ]
