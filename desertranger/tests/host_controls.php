<?php
/**
 * Host controls over HTTP: Remove (lobby), Skip turn, Sit out.
 *
 *   php tests/host_controls.php http://localhost:8888/desertranger
 *
 * Checks: only the host can use them (403 for guests and for no token); Remove is lobby-only, frees the vehicle, renumbers the seats
 * so the next join does not clash, and the removed seat's token stops working; Skip turn needs the turn the host saw (409 when stale),
 * moves the turn on and logs it; Sit out passes a player over silently until the host brings them back, and a whole game still plays
 * to the finish with someone sitting out. Exit code 0 = all good. (Creates a few test rooms in the database, like the other tests.)
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }

$BASE = rtrim(isset($argv[1]) ? $argv[1] : 'http://localhost:8888/desertranger', '/');
$fails = 0;

function req($method, $action, $body = null, $token = null, $query = '')
{
    global $BASE;
    $headers = "Accept: application/json\r\n";
    if ($token) $headers .= "X-Player-Token: $token\r\n";
    $opts = array('http' => array('method' => $method, 'ignore_errors' => true, 'header' => $headers, 'timeout' => 15));
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
function tapKey() { return bin2hex(random_bytes(8)); }
function newRoom($name, $vehicle) { $c = req('POST', 'create', array('name' => $name, 'vehicle' => $vehicle)); return array($c['code'], $c['token']); }
function joinRoom($code, $name, $vehicle) { $j = req('POST', 'join', array('code' => $code, 'name' => $name, 'vehicle' => $vehicle)); return $j; }
function idOf($code, $token) { return state($code, $token)['meId']; }
function playerByName($st, $name) { foreach ($st['players'] as $p) if ($p['name'] === $name) return $p; return null; }
function seats($st) { $s = array(); foreach ($st['players'] as $p) $s[] = $p['seat']; sort($s); return $s; }
function roll($code, $token, $turn) { return req('POST', 'roll', array('code' => $code, 'turn' => $turn, 'key' => tapKey()), $token); }

echo "Host controls ($BASE)\n";

echo "\nRemove (lobby)\n";
list($code, $host) = newRoom('Host', 'bronco-orange');
$g1 = joinRoom($code, 'Guest1', 'jeep-red')['token'];
$g2 = joinRoom($code, 'Guest2', 'scout-butter')['token'];
$g3 = joinRoom($code, 'Guest3', 'buggy-blue')['token'];
$st = state($code, $host);
check(seats($st) === array(0, 1, 2, 3), 'four seated players, seats 0..3');
$id1 = idOf($code, $g1); $id2 = idOf($code, $g2); $hostId = idOf($code, $host);
$r = req('POST', 'remove', array('code' => $code, 'playerId' => $id2), $g1);
check(!$r['ok'] && $r['_status'] === 403, 'a guest cannot remove anyone (403)');
$r = req('POST', 'remove', array('code' => $code, 'playerId' => $id2), null);
check(!$r['ok'] && $r['_status'] === 403, 'no token: refused (403)');
$r = req('POST', 'remove', array('code' => $code, 'playerId' => $hostId), $host);
check(!$r['ok'] && $r['_status'] === 409, 'the host cannot remove themself (409)');
$r = req('POST', 'remove', array('code' => $code, 'playerId' => $id1), $host);          // a MIDDLE seat (1)
check($r['ok'], 'the host removes Guest1 (seat 1 of 0..3)');
$st = state($code, $host);
check(count($st['players']) === 3 && playerByName($st, 'Guest1') === null, 'Guest1 is gone');
check(seats($st) === array(0, 1, 2), 'seats are renumbered 0..2 (no gap)');
check(state($code, $g1)['meId'] === null, "the removed player's token no longer has a seat");
$ev = array_values(array_filter($st['events'], function ($e) { return $e['type'] === 'removed'; }));
check(count($ev) === 1 && strpos($ev[0]['msg'], 'Guest1 was removed by the host') !== false, 'the log says who was removed');
$j = joinRoom($code, 'Guest4', 'jeep-red');
check($j['ok'] && $j['_status'] === 200, "the freed vehicle can be picked again and the next join works (no seat clash)");
$st = state($code, $host);
check(seats($st) === array(0, 1, 2, 3), 'four players again, seats 0..3 all different');
$r = req('POST', 'remove', array('code' => $code, 'playerId' => $id1), $host);
check($r['ok'], 'removing someone who is already gone is harmless');
$r = req('POST', 'remove', array('code' => $code, 'playerId' => 999999), $host);
check($r['ok'], 'removing an unknown id is harmless too');

echo "\nSkip turn and Sit out (a game of 4)\n";
$g4 = $j['token'];
$tok = array($hostId => $host, idOf($code, $g2) => $g2, idOf($code, $g3) => $g3, idOf($code, $g4) => $g4);
$s = req('POST', 'start', array('code' => $code), $host);
check($s['ok'] && state($code, $host)['game']['status'] === 'active', 'the game starts');
$r = req('POST', 'remove', array('code' => $code, 'playerId' => $id2), $host);
check(!$r['ok'] && $r['_status'] === 409, 'Remove is lobby-only: refused once the game has started (409)');
$st = state($code, $host); $g = $st['game'];
check($g['turn'] === 1 && $g['currentId'] === $hostId, 'the host is on turn 1');
$r = req('POST', 'skip', array('code' => $code, 'turn' => 1), $g2);
check(!$r['ok'] && $r['_status'] === 403, 'a guest cannot skip (403)');
$r = req('POST', 'skip', array('code' => $code, 'turn' => 7), $host);
check(!$r['ok'] && $r['_status'] === 409, 'a stale or wrong turn number is refused (409)');
$r = req('POST', 'skip', array('code' => $code, 'turn' => 1), $host);
$st = state($code, $host); $g = $st['game'];
check($r['ok'] && $g['turn'] === 2 && $g['currentId'] !== $hostId, 'the host skips their own turn: turn 2, someone else is up');
$ev = array_values(array_filter($st['events'], function ($e) { return $e['type'] === 'hostskip'; }));
check(count($ev) === 1 && strpos($ev[0]['msg'], 'was skipped by the host') !== false && empty($ev[0]['playAt']) && empty($ev[0]['cue']), 'logged as a host skip (no animation, no sound)');
$r = req('POST', 'skip', array('code' => $code, 'turn' => 1), $host);
check(!$r['ok'] && $r['_status'] === 409, 'tapping Skip twice with the old turn number only skips once (409)');
$cur = $g['currentId']; $r = roll($code, $tok[$cur], 2);
check($r['ok'], 'the player now on turn can roll normally');

// sit out
$st = state($code, $host); $cur = $st['game']['currentId'];
$others = array_values(array_filter(array_keys($tok), function ($i) use ($hostId, $cur) { return $i !== $hostId; }));
$victim = $others[0]; $victimTok = $tok[$victim];
$r = req('POST', 'sitout', array('code' => $code, 'playerId' => $victim, 'on' => true), $victimTok);
check(!$r['ok'] && $r['_status'] === 403, 'a guest cannot make anyone sit out (403)');
$r = req('POST', 'sitout', array('code' => $code, 'playerId' => $hostId, 'on' => true), $host);
check(!$r['ok'] && $r['_status'] === 409, 'the host cannot sit themself out (409)');
$r = req('POST', 'sitout', array('code' => $code, 'playerId' => 999999, 'on' => true), $host);
check(!$r['ok'] && $r['_status'] === 404, 'sit out: unknown player (404)');
$turnBefore = state($code, $host)['game']['turn'];
$r = req('POST', 'sitout', array('code' => $code, 'playerId' => $victim, 'on' => true), $host);
$st = state($code, $host);
check($r['ok'] && playerByName($st, 'Host') !== null, 'the host sits a player out');
$vp = null; foreach ($st['players'] as $p) if ($p['id'] === $victim) $vp = $p;
check($vp['out'] === true, 'the state shows them as sitting out');
$r2 = req('POST', 'sitout', array('code' => $code, 'playerId' => $victim, 'on' => true), $host);
check($r2['ok'], 'sitting out someone who already sits out is harmless');
// play a few rounds: the victim must never be on turn
$never = true; $actions = 0;
for ($i = 0; $i < 24; $i++) {
    $st = state($code, $host); $g = $st['game'];
    if ($g['status'] !== 'active') break;
    $actor = $g['pending'] ? $g['pending']['playerId'] : $g['currentId'];
    if ($actor === $victim) { $never = false; break; }
    if ($g['pending']) req('POST', 'choose', array('code' => $code, 'turn' => $g['turn'], 'key' => tapKey(), 'action' => 'skip'), $tok[$actor]);
    else roll($code, $tok[$actor], $g['turn']);
    $actions++;
}
check($never && $actions >= 6, "a sitting-out player is never on turn over $actions actions");
$st = state($code, $host);
$lines = array_filter($st['events'], function ($e) use ($vp) { return strpos($e['msg'], $vp['name'] . ' loses this turn') !== false; });
check(count($lines) === 0, 'and no "loses this turn" noise is logged for them');
$r = req('POST', 'sitout', array('code' => $code, 'playerId' => $victim, 'on' => false), $host);
$st = state($code, $host);
$vp2 = null; foreach ($st['players'] as $p) if ($p['id'] === $victim) $vp2 = $p;
check($r['ok'] && $vp2['out'] === false && $vp2['skip'] === 0, 'bring them back: the flag is cleared');
$seen = false;
for ($i = 0; $i < 40 && !$seen; $i++) {
    $st = state($code, $host); $g = $st['game'];
    if ($g['status'] !== 'active') break;
    $actor = $g['pending'] ? $g['pending']['playerId'] : $g['currentId'];
    if ($actor === $victim) { $seen = true; break; }
    if ($g['pending']) req('POST', 'choose', array('code' => $code, 'turn' => $g['turn'], 'key' => tapKey(), 'action' => 'skip'), $tok[$actor]);
    else roll($code, $tok[$actor], $g['turn']);
}
check($seen || $g['status'] !== 'active', 'and they get their turns again');

// the current player sits out: the turn moves on at once
$st = state($code, $host);
if ($st['game']['status'] === 'active') {
    $cur = $st['game']['currentId'];
    if ($cur !== $hostId) {
        $t0 = $st['game']['turn'];
        $r = req('POST', 'sitout', array('code' => $code, 'playerId' => $cur, 'on' => true), $host);
        $st = state($code, $host);
        check($r['ok'] && $st['game']['currentId'] !== $cur && $st['game']['turn'] === $t0 + 1, 'sitting out the player on turn moves the turn on at once (turn +1)');
        $r = roll($code, $tok[$cur], $t0);
        check(!$r['ok'], 'their old roll is refused (409)');
        req('POST', 'sitout', array('code' => $code, 'playerId' => $cur, 'on' => false), $host);
    } else {
        check(true, '(host was on turn: skipped the sit-out-current case)');
    }
}

echo "\nA whole game with someone sitting out, and the end\n";
list($c2, $h2) = newRoom('HostB', 'bronco-orange');
$a2 = joinRoom($c2, 'A', 'jeep-red')['token']; $b2 = joinRoom($c2, 'B', 'scout-butter')['token'];
req('POST', 'start', array('code' => $c2), $h2);
$ids2 = array(idOf($c2, $h2) => $h2, idOf($c2, $a2) => $a2, idOf($c2, $b2) => $b2);
$bId = idOf($c2, $b2);
req('POST', 'sitout', array('code' => $c2, 'playerId' => $bId, 'on' => true), $h2);
$fin = false; $bActed = false;
for ($i = 0; $i < 700; $i++) {
    $st = state($c2, $h2); $g = $st['game'];
    if ($g['status'] === 'finished') { $fin = true; break; }
    $actor = $g['pending'] ? $g['pending']['playerId'] : $g['currentId'];
    if ($actor === $bId) { $bActed = true; break; }
    if ($g['pending']) req('POST', 'choose', array('code' => $c2, 'turn' => $g['turn'], 'key' => tapKey(), 'action' => $g['pending']['type'] === 'shortcut' ? 'shortcut' : 'skip'), $ids2[$actor]);
    else roll($c2, $ids2[$actor], $g['turn']);
}
check($fin && !$bActed, 'the game plays to the finish without the player who sits out ever being on turn');
$r = req('POST', 'skip', array('code' => $c2, 'turn' => state($c2, $h2)['game']['turn']), $h2);
check(!$r['ok'] && $r['_status'] === 409, 'no skipping after the game is over (409)');
list($c3, $h3) = newRoom('HostC', 'bronco-orange');
$a3 = joinRoom($c3, 'A', 'jeep-red')['token']; req('POST', 'start', array('code' => $c3), $h3);
$aId = idOf($c3, $a3);
req('POST', 'sitout', array('code' => $c3, 'playerId' => $aId, 'on' => true), $h3);
$r = req('POST', 'skip', array('code' => $c3, 'turn' => 1), $h3);
check(!$r['ok'] && $r['_status'] === 409, 'Skip is refused when nobody else is in the game (409)');

echo "\n" . ($fails ? "$fails FAILED" : 'ALL PASSED') . "\n";
exit($fails ? 1 : 0);
