#!/usr/bin/env bash
# Polling load check: N simulated clients each poll api.php?a=state once a
# second (like the real page) for D seconds while a game is being played.
#   bash tests/poll_load.sh http://localhost:8098/desertranger CODE [clients=8] [seconds=60]
# Prints requests/sec, latency, and MySQL queries/sec (if run on the DB box with sudo).
BASE=${1:-http://localhost:8098/desertranger}; CODE=$2; N=${3:-8}; D=${4:-60}
[ -z "$CODE" ] && { echo "usage: $0 BASE CODE [clients] [seconds]"; exit 1; }
OUT=$(mktemp -d)
q0=$(sudo -n mariadb -N -e "SHOW GLOBAL STATUS LIKE 'Questions'" 2>/dev/null | awk '{print $2}')
cpu0=$(ps -C apache2 -o times= | awk '{s+=$1} END {print s+0}')
end=$(( $(date +%s) + D ))
for i in $(seq 1 "$N"); do
  ( since=0
    while [ "$(date +%s)" -lt "$end" ]; do
      curl -s -o "$OUT/body$i" -w "%{time_total}\n" "$BASE/api.php?a=state&code=$CODE&since=$since" >> "$OUT/t$i"
      s=$(grep -o '"id":[0-9]*' "$OUT/body$i" | tail -1 | cut -d: -f2); [ -n "$s" ] && since=$s
      sleep 1
    done ) &
done
wait
q1=$(sudo -n mariadb -N -e "SHOW GLOBAL STATUS LIKE 'Questions'" 2>/dev/null | awk '{print $2}')
cpu1=$(ps -C apache2 -o times= | awk '{s+=$1} END {print s+0}')
cat "$OUT"/t* | sort -n | awk -v D="$D" -v N="$N" '
  { a[NR]=$1; s+=$1 }
  END { printf "clients %d, %d s: %d requests = %.1f req/s; latency avg %.1f ms, p50 %.1f ms, p95 %.1f ms, max %.1f ms\n",
        N, D, NR, NR/D, s/NR*1000, a[int(NR*.5)]*1000, a[int(NR*.95)]*1000, a[NR]*1000 }'
[ -n "$q0" ] && echo "MySQL queries: $((q1-q0)) total = $(( (q1-q0)/D )) /s"
echo "Apache CPU time used: $((cpu1-cpu0)) s over $D s"
rm -rf "$OUT"
