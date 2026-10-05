<?php
/**
 * Wave 2 server features over HTTP: the games counter (a=stats), the rematch, and the Knock-knock nudge.
 *
 *   php tests/wave2_game.php http://localhost:8888/desertranger
 *
 * Checks: stats returns only a count and counts a fresh room; a rematch is host-only, refused unless the game is over
 * and on a solo demo, keeps the same players and tokens, resets positions and the log, and the room can be played again;
 * a nudge needs a seated player in an active game, is stamped with the shared play_at and the nudge cue, shows up for
 * every player, and is rate limited. Exit code 0 = all good. (Creates a few test rooms in the database, like the other
 * tests; dev/cleanup-test-rooms.sql removes old ones.)
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
function newRoom($name = 'Marigold', $vehicle = 'bronco-orange')
{
    $c = req('POST', 'create', array('name' => $name, 'vehicle' => $vehicle));
    return array($c['code'], $c['token']);
}
function joinRoom($code, $name, $vehicle)
{
    $j = req('POST', 'join', array('code' => $code, 'name' => $name, 'vehicle' => $vehicle));
    return $j['token'];
}
/** Play a started game to the finish. $tokens = player id => token. Returns true when it finished. */
function playOut($code, $tokens, $maxActions = 700)
{
    $hostTok = reset($tokens);
    for ($n = 0; $n < $maxActions; $n++) {
        $st = state($code, $hostTok);
        if ($st['game']['status'] === 'finished') return true;
        $g = $st['game']; $actor = $g['pending'] ? $g['pending']['playerId'] : $g['currentId'];
        $tok = $tokens[$actor];
        if ($g['pending']) $r = req('POST', 'choose', array('code' => $code, 'turn' => $g['turn'], 'key' => tapKey(), 'action' => $g['pending']['type'] === 'shortcut' ? 'shortcut' : 'skip'), $tok);
        else $r = req('POST', 'roll', array('code' => $code, 'turn' => $g['turn'], 'key' => tapKey()), $tok);
        if (!$r['ok']) return false;
    }
    return false;
}
/** A started 2-player room: [code, hostToken, guestToken, [playerId => token]]. */
function startedRoom()
{
    list($code, $host) = newRoom('Host', 'bronco-orange');
    $guest = joinRoom($code, 'Guest', 'jeep-red');
    req('POST', 'start', array('code' => $code), $host);
    $st = state($code, $host);
    $tokens = array();
    foreach ($st['players'] as $p) $tokens[$p['id']] = ($p['id'] === $st['meId']) ? $host : $guest;
    return array($code, $host, $guest, $tokens);
}

echo "Games counter ($BASE)\n";
list($lc, $lh) = newRoom('Counter', 'bronco-orange');
$s = req('GET', 'stats');
$keys = array_diff(array_keys($s), array('_status', 'serverNow'));
sort($keys);
check($s['ok'] && $s['_status'] === 200 && $keys === array('games', 'ok'), 'a=stats returns only ok + a games count (no codes, names or players)');
check(is_int($s['games']) && $s['games'] >= 1, 'a just-created room is counted (' . $s['games'] . ' game(s) being played)');
$s1 = req('GET', 'stats'); sleep(1); $s2 = req('GET', 'stats');
check($s1['serverNow'] <= $s2['serverNow'] && $s2['ok'], 'stats can be called repeatedly (not cached)');

echo "\nNudge (Knock, knock)\n";
list($code, $host, $guest, $tokens) = startedRoom();
check(state($code, $host)['game']['status'] === 'active', 'a 2-player game is active');
$n = req('POST', 'nudge', array('code' => $code), null);
check(!$n['ok'] && $n['_status'] === 403, 'a nudge without a seat is refused (403)');
list($lcode, $lhost) = newRoom('Lobby', 'scout-butter');
$n = req('POST', 'nudge', array('code' => $lcode), $lhost);
check(!$n['ok'] && $n['_status'] === 409, 'a nudge in a lobby is refused (409)');
$before = state($code, $host)['events'];
$lastId = $before ? end($before)['id'] : 0;
$n = req('POST', 'nudge', array('code' => $code), $guest);
check($n['ok'], 'a seated player can nudge during a game');
$ev = array_values(array_filter(state($code, $host, $lastId)['events'], function ($e) { return $e['type'] === 'nudge'; }));
check(count($ev) === 1 && $ev[0]['cue'] === 'nudge-01', 'the nudge event carries the nudge cue');
check(count($ev) === 1 && $ev[0]['playAt'] > 0 && $ev[0]['playAt'] <= (int)round(microtime(true) * 1000) + 5000 && $ev[0]['playAt'] >= (int)round(microtime(true) * 1000) - 2000, 'the nudge is stamped with a shared play_at (a moment from now)');
$evG = array_values(array_filter(state($code, $guest, $lastId)['events'], function ($e) { return $e['type'] === 'nudge'; }));
check(count($evG) === 1 && $evG[0]['id'] === $ev[0]['id'] && $evG[0]['playAt'] === $ev[0]['playAt'], 'every player gets the same nudge event and play_at');
$n2 = req('POST', 'nudge', array('code' => $code), $host);
check(!$n2['ok'] && $n2['_status'] === 429, 'a second nudge right away is rate limited (429)');
$stNow = state($code, $host);
check($stNow['game']['status'] === 'active' && $stNow['game']['turn'] === 1, 'a nudge does not change the game (still turn 1, active)');

echo "\nRematch\n";
$r = req('POST', 'rematch', array('code' => $code), $host);
check(!$r['ok'] && $r['_status'] === 409, 'a rematch is refused while the game is still being played (409)');
$fin = playOut($code, $tokens);
check($fin, 'the game plays to the finish');
$winner = state($code, $host)['game']['winnerId'];
check($winner !== null, 'there is a winner');
$r = req('POST', 'rematch', array('code' => $code), $guest);
check(!$r['ok'] && $r['_status'] === 403, 'only the host can start a rematch (403 for the guest)');
$r = req('POST', 'rematch', array('code' => $code), null);
check(!$r['ok'] && $r['_status'] === 403, 'a rematch without a seat is refused (403)');
$r = req('POST', 'rematch', array('code' => $code), $host);
check($r['ok'], 'the host starts a rematch');
$st = state($code, $host);
check($st['game']['status'] === 'lobby' && $st['game']['turn'] === 0 && $st['game']['winnerId'] === null && $st['game']['pending'] === null, 'the same room is a lobby again (no winner, turn 0)');
check(count($st['players']) === 2 && $st['players'][0]['pos'] === 0 && $st['players'][1]['pos'] === 0 && $st['players'][0]['skip'] === 0, 'same two players, back on the start square');
check($st['meId'] === array_search($host, $tokens) && state($code, $guest)['meId'] === array_search($guest, $tokens), 'both seat tokens still work');
check(count(array_filter($st['events'], function ($e) { return $e['type'] === 'turn' || $e['type'] === 'win'; })) === 0, 'the old turn log is gone');
$r = req('POST', 'rematch', array('code' => $code), $host);
check($r['ok'] && state($code, $host)['game']['status'] === 'lobby', 'a double tap on Play again is harmless');
$n = req('POST', 'nudge', array('code' => $code), $host);
check(!$n['ok'] && $n['_status'] === 409, 'no nudge in the lobby after a rematch');
$s = req('POST', 'start', array('code' => $code), $host);
$st = state($code, $host);
check($s['ok'] && $st['game']['status'] === 'active' && $st['game']['turn'] === 1 && !$st['game']['demo'], 'the host starts the rematch: a fresh normal game');
$cur = $st['game']['currentId']; $tok = $tokens[$cur];
$roll = req('POST', 'roll', array('code' => $code, 'turn' => 1, 'key' => tapKey()), $tok);
check($roll['ok'], 'the first roll of the rematch works');
check(playOut($code, $tokens), 'the rematch plays to a finish too');

echo "\nRematch on a demo\n";
list($dc, $dh) = newRoom('Solo', 'bronco-orange');
$s = req('POST', 'start', array('code' => $dc, 'demo' => true, 'bots' => 1), $dh);
$demoTokens = array(state($dc, $dh)['meId'] => $dh);
foreach ($s['rivals'] as $rv) $demoTokens[$rv['id']] = $rv['token'];
check(playOut($dc, $demoTokens), 'a demo game plays to the finish');
$r = req('POST', 'rematch', array('code' => $dc), $dh);
check(!$r['ok'] && $r['_status'] === 409, 'a rematch on a solo demo is refused (use End demo)');
$e = req('POST', 'enddemo', array('code' => $dc), $dh);
check($e['ok'] && state($dc, $dh)['game']['status'] === 'lobby', 'End demo still works on a finished demo');

echo "\n" . ($fails ? "$fails FAILED" : 'ALL PASSED') . "\n";
exit($fails ? 1 : 0);
