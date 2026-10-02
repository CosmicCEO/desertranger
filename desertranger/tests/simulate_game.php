<?php
/**
 * End-to-end simulation over HTTP: N players create/join, start, and play a
 * full game to the finish through the real API (no browser).
 *
 *   php tests/simulate_game.php http://localhost:8098/desertranger 4
 *
 * Also checks: vehicle uniqueness, host-only start, out-of-turn rolls,
 * stale-turn double taps, idempotent retries, and two truly PARALLEL taps
 * (fired with two curl processes at once). Exit code 0 = all good.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }

$BASE = rtrim(isset($argv[1]) ? $argv[1] : 'http://localhost:8098/desertranger', '/');
$N = isset($argv[2]) ? max(2, min(8, (int)$argv[2])) : 4;
$fails = 0;

function req($method, $action, $body = null, $token = null, $query = '')
{
    global $BASE;
    $headers = "Accept: application/json\r\n";
    if ($token) $headers .= "X-Player-Token: $token\r\n";
    $opts = array('http' => array('method' => $method, 'ignore_errors' => true, 'header' => $headers, 'timeout' => 10));
    if ($body !== null) {
        $opts['http']['header'] .= "Content-Type: application/json\r\n";
        $opts['http']['content'] = json_encode($body);
    }
    $raw = file_get_contents("$BASE/api.php?a=$action$query", false, stream_context_create($opts));
    $status = 0;
    if (isset($http_response_header[0]) && preg_match('/\s(\d{3})\s/', $http_response_header[0], $m)) $status = (int)$m[1];
    $j = json_decode($raw, true);
    if (!is_array($j)) $j = array('ok' => false, 'error' => 'non-JSON: ' . substr($raw, 0, 200));
    $j['_status'] = $status;
    return $j;
}
function check($cond, $label) { global $fails; echo ($cond ? '  ok   ' : '  FAIL ') . $label . "\n"; if (!$cond) $fails++; }
function state($code, $token = null, $since = 0) { return req('GET', 'state', null, $token, "&code=$code&since=$since"); }

$names = array('Marigold', 'Jeff', 'Jerod', 'Rosa', 'Kit', 'Ana', 'Lee', 'Sam');
$vehicles = array('bronco-orange', 'scout-butter', 'jeep-red', 'ranger-green', 'buggy-blue', 'rail-purple', 'cruiser-teal', 'blazer-twotone');

echo "Lobby ($N players) against $BASE\n";
$c = req('POST', 'create', array('name' => $names[0], 'vehicle' => $vehicles[0]));
check($c['ok'] && preg_match('/^[A-Z]{4}$/', $c['code']), 'create -> room code ' . (isset($c['code']) ? $c['code'] : '?'));
$code = $c['code'];
$tokens = array($c['token']);
$dup = req('POST', 'join', array('code' => $code, 'name' => 'Dupe', 'vehicle' => $vehicles[0]));
check(!$dup['ok'] && $dup['_status'] === 409, 'same vehicle twice rejected (409)');
for ($i = 1; $i < $N; $i++) {
    $j = req('POST', 'join', array('code' => strtolower($code), 'name' => $names[$i], 'vehicle' => $vehicles[$i]));
    check($j['ok'], "join {$names[$i]} ({$vehicles[$i]})");
    $tokens[] = $j['token'];
}
$s = req('POST', 'start', array('code' => $code), $tokens[1]);
check(!$s['ok'] && $s['_status'] === 403, 'non-host cannot start');
$s = req('POST', 'start', array('code' => $code), $tokens[0]);
check($s['ok'], 'host starts');
$late = req('POST', 'join', array('code' => $code, 'name' => 'Late', 'vehicle' => $vehicles[7]));
check(!$late['ok'], 'cannot join after start');

$st = state($code, $tokens[0]);
$ids = array();
foreach ($st['players'] as $p) $ids[] = $p['id'];
check($st['game']['status'] === 'active' && $st['game']['currentId'] === $ids[0], 'turn order = join order, host first');

echo "Double-tap protection\n";
$turn = $st['game']['turn'];
$wrong = req('POST', 'roll', array('code' => $code, 'turn' => $turn, 'key' => 'k-wrong'), $tokens[1]);
check(!$wrong['ok'], 'out-of-turn roll rejected');
$r1 = req('POST', 'roll', array('code' => $code, 'turn' => $turn, 'key' => 'k1-' . $code), $tokens[0]);
$r1b = req('POST', 'roll', array('code' => $code, 'turn' => $turn, 'key' => 'k1-' . $code), $tokens[0]);
check($r1['ok'] && $r1b['ok'] && $r1b['duplicate'] === true, 'retry with same key = duplicate, no second roll');
$r2 = req('POST', 'roll', array('code' => $code, 'turn' => $turn, 'key' => 'k2-' . $code), $tokens[0]);
check(!$r2['ok'] && $r2['_status'] === 409, 'second tap with stale turn rejected (409)');
$after = state($code, $tokens[0]);
$turnEvents = array_filter($after['events'], function ($e) { return in_array($e['type'], array('turn', 'win')); });
check(count($turnEvents) === 1, 'exactly one turn event logged');

// Two taps at the SAME moment from the current player (separate processes).
$st = state($code);
$cur = array_search($st['game']['currentId'], $ids);
if (!$st['game']['pending']) {
    $procs = array();
    for ($k = 0; $k < 2; $k++) {
        $body = escapeshellarg(json_encode(array('code' => $code, 'turn' => $st['game']['turn'], 'key' => "par$k-" . $code)));
        $cmd = "curl -s -H 'Content-Type: application/json' -H 'X-Player-Token: {$tokens[$cur]}' -d $body '$BASE/api.php?a=roll'";
        $procs[] = popen($cmd, 'r');
    }
    $okCount = 0;
    foreach ($procs as $p) { $out = json_decode(stream_get_contents($p), true); pclose($p); if (!empty($out['ok'])) $okCount++; }
    check($okCount === 1, "two parallel taps -> exactly one accepted ($okCount)");
    $st2 = state($code);
    check($st2['game']['turn'] === $st['game']['turn'] + 1, 'turn advanced by exactly 1');
}

echo "Playing to the finish\n";
$actions = 0; $cues = array(); $since = 0; $log = array(); $swaps = 0; $shortcuts = 0; $maxLead = 0; $minLead = PHP_INT_MAX;
while ($actions < 2000) {
    $st = state($code, null, $since);
    foreach ($st['events'] as $e) {
        $since = $e['id'];
        $log[] = $e['msg'];
        if ($e['cue']) {
            $cues[$e['cue']] = (isset($cues[$e['cue']]) ? $cues[$e['cue']] : 0) + 1;
            $lead = $e['playAt'] - $st['serverNow'];
            $maxLead = max($maxLead, $lead); $minLead = min($minLead, $lead);
        }
    }
    if ($st['game']['status'] === 'finished') break;
    $cur = array_search($st['game']['currentId'], $ids);
    $base = array('code' => $code, 'turn' => $st['game']['turn'], 'key' => "a$actions-" . bin2hex(random_bytes(4)));
    if ($st['game']['pending']) {
        if ($st['game']['pending']['type'] === 'swap') {
            $others = array_values(array_diff($ids, array($ids[$cur])));
            $r = req('POST', 'choose', $base + array('action' => 'swap', 'target' => $others[array_rand($others)]), $tokens[$cur]);
            $swaps++;
        } else {
            $r = req('POST', 'choose', $base + array('action' => 'shortcut'), $tokens[$cur]);
            $shortcuts++;
        }
    } else {
        $r = req('POST', 'roll', $base, $tokens[$cur]);
    }
    if (!$r['ok']) { check(false, 'action failed: ' . $r['error']); break; }
    $actions++;
}
$final = state($code, $tokens[0]);
$winner = null;
foreach ($final['players'] as $p) if ($p['id'] === $final['game']['winnerId']) $winner = $p;
check($final['game']['status'] === 'finished' && $winner && $winner['pos'] === 51, "game finished after $actions actions; winner {$winner['name']} on square 51");
check(count(array_filter($log, function ($m) { return strpos($m, 'wins!') !== false; })) === 1, 'one win line in the log');
echo "       cues: " . json_encode($cues) . ", swaps $swaps, shortcuts $shortcuts\n";
if ($cues) echo "       cue play_at lead seen at poll time: $minLead..$maxLead ms (target ~1500 minus poll delay)\n";
$r = req('POST', 'roll', array('code' => $code, 'turn' => $final['game']['turn'], 'key' => 'after'), $tokens[0]);
check(!$r['ok'], 'no rolls after the finish');
echo "\nLast 8 log lines:\n";
foreach (array_slice($log, -8) as $m) echo "   $m\n";
echo "\nRoom code: $code\n";
echo $fails ? "\n$fails FAILED\n" : "\nALL PASSED\n";
exit($fails ? 1 : 0);
