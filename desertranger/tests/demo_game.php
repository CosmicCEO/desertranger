<?php
/**
 * Solo demo mode over HTTP, plus a regression check that NORMAL games still enforce the 2-player minimum.
 *
 *   php tests/demo_game.php http://localhost:8888/desertranger
 *
 * Checks: a normal 1-player start is refused; a normal 2-player start works; the demo start works only for the host
 * alone; computer rivals are ordinary players (tokens go to the host once, flags in the state); a whole demo game plays
 * to the finish; every turn event carries play_at; End demo returns the same room to a clean lobby and refuses on a
 * normal game; a demo can be restarted in the same room; bots=0 is a pure solo game. Exit code 0 = all good.
 * (Creates a few finished test rooms in the database, like simulate_game.php.)
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
function newRoom($name = 'Marigold', $vehicle = 'bronco-orange')
{
    $c = req('POST', 'create', array('name' => $name, 'vehicle' => $vehicle));
    return array($c['code'], $c['token']);
}
function tapKey() { return bin2hex(random_bytes(8)); }

/** Play a started game to the finish. $tokens = player id => token. Returns [actions, finished, every turn event had playAt]. */
function playOut($code, $tokens, $maxActions = 600)
{
    $n = 0; $since = 0; $allPlayAt = true; $hostTok = reset($tokens);
    while ($n < $maxActions) {
        $st = state($code, $hostTok, $since);
        foreach ($st['events'] as $e) {
            $since = max($since, $e['id']);
            if (in_array($e['type'], array('turn', 'win'), true) && !$e['playAt']) $allPlayAt = false;
        }
        if ($st['game']['status'] === 'finished') return array($n, true, $allPlayAt);
        $g = $st['game']; $actor = $g['pending'] ? $g['pending']['playerId'] : $g['currentId'];
        $tok = $tokens[$actor];
        if ($g['pending']) $r = req('POST', 'choose', array('code' => $code, 'turn' => $g['turn'], 'key' => tapKey(), 'action' => $g['pending']['type'] === 'shortcut' ? 'shortcut' : 'skip'), $tok);
        else $r = req('POST', 'roll', array('code' => $code, 'turn' => $g['turn'], 'key' => tapKey()), $tok);
        if (!$r['ok']) return array($n, false, $allPlayAt);
        $n++;
    }
    return array($n, false, $allPlayAt);
}

echo "Normal games still need 2+ players ($BASE)\n";
list($code, $host) = newRoom();
$s = req('POST', 'start', array('code' => $code), $host);
check(!$s['ok'] && $s['_status'] === 409 && stripos($s['error'], '2 players') !== false, 'normal start with 1 player is refused (409 "Need at least 2 players")');
check(state($code, $host)['game']['status'] === 'lobby', 'the room is still a lobby after the refused start');
$j = req('POST', 'join', array('code' => $code, 'name' => 'Jeff', 'vehicle' => 'jeep-red'));
check($j['ok'], 'second player joins');
$guest = $j['token'];
$s = req('POST', 'start', array('code' => $code, 'demo' => true), $guest);
check(!$s['ok'] && $s['_status'] === 403, 'a guest cannot start (even with demo = true)');
$s = req('POST', 'start', array('code' => $code, 'demo' => true), $host);
check(!$s['ok'] && $s['_status'] === 409, 'demo start refused once a second player has joined (the demo is for the host alone)');
check(state($code, $host)['game']['status'] === 'lobby', 'the room is still a lobby after the refused demo start');
$s = req('POST', 'start', array('code' => $code), $host);
check($s['ok'] && empty($s['rivals']), 'normal 2-player start works and adds no rivals');
$st = state($code, $host);
check($st['game']['status'] === 'active' && $st['game']['demo'] === false && count($st['players']) === 2, 'normal game: active, demo = false, 2 players');
check(!array_filter($st['players'], function ($p) { return $p['bot']; }), 'normal game: nobody is flagged as a computer rival');
$e = req('POST', 'enddemo', array('code' => $code), $host);
check(!$e['ok'] && $e['_status'] === 409, 'End demo is refused on a normal game (409)');
$e = req('POST', 'enddemo', array('code' => $code), $guest);
check(!$e['ok'] && $e['_status'] === 403, 'End demo by a guest is refused (403)');
check(state($code, $host)['game']['status'] === 'active', 'the normal game is untouched (still active)');

echo "\nSolo demo with 2 computer rivals\n";
list($code, $host) = newRoom();
$s = req('POST', 'start', array('code' => $code, 'demo' => true, 'bots' => 2), $host);
check($s['ok'] && count($s['rivals']) === 2 && $s['rivals'][0]['token'] && $s['rivals'][0]['id'], 'demo start with only the host works; the host gets 2 rival tokens');
$st = state($code, $host);
check($st['game']['status'] === 'active' && $st['game']['demo'] === true, 'state: active with demo = true');
check(count($st['players']) === 3 && array_column($st['players'], 'bot') === array(false, true, true), 'state: host + 2 rivals, only the rivals flagged bot');
check(array_column($st['players'], 'name') === array('Marigold', 'Rival 1', 'Rival 2') && count(array_unique(array_column($st['players'], 'vehicle'))) === 3, 'rivals are named Rival 1/2 and have their own vehicles');
check($st['game']['currentId'] === $st['players'][0]['id'], 'the host rolls first');
$again = req('POST', 'start', array('code' => $code, 'demo' => true, 'bots' => 2), $host);
check($again['ok'] && empty($again['rivals']) && count(state($code, $host)['players']) === 3, 'a double tap on the demo button adds no extra rivals');
$rivals = array(); foreach ($s['rivals'] as $r) $rivals[$r['id']] = $r['token'];
$rivalTok = reset($rivals);
$r = req('POST', 'roll', array('code' => $code, 'turn' => $st['game']['turn'], 'key' => tapKey()), $rivalTok);
check(!$r['ok'] && $r['_status'] === 409, "a rival cannot roll on the host's turn (409)");
$r = req('POST', 'enddemo', array('code' => $code), $rivalTok);
check(!$r['ok'] && $r['_status'] === 403, 'a rival token cannot end the demo (403)');
$tokens = array($st['players'][0]['id'] => $host) + $rivals;
list($n, $finished, $allPlayAt) = playOut($code, $tokens);
check($finished, "the demo plays to the finish ($n actions: host rolls and rival rolls through the normal endpoints)");
check($allPlayAt, 'every turn/win event carries play_at (so the audio stays in sync in a demo too)');
$st = state($code, $host);
check($st['game']['status'] === 'finished' && $st['game']['demo'] === true, 'a finished demo still reports demo = true');
$e = req('POST', 'enddemo', array('code' => $code), $host);
check($e['ok'], 'host ends the finished demo');
$st = state($code, $host);
check($st['game']['status'] === 'lobby' && $st['game']['demo'] === false && $st['game']['turn'] === 0 && $st['game']['pending'] === null && $st['game']['winnerId'] === null, 'the same room is a clean lobby again (turn 0, no winner, demo = false)');
check(count($st['players']) === 1 && $st['players'][0]['pos'] === 0 && $st['players'][0]['skip'] === 0, 'only the host remains, back on the start square');
check(!array_filter($st['events'], function ($e) { return in_array($e['type'], array('turn', 'win', 'start', 'skip'), true); }), "the demo's log is gone");
$r = req('POST', 'roll', array('code' => $code, 'turn' => 1, 'key' => tapKey()), $rivalTok);
check(!$r['ok'], 'the old rival tokens are dead');
$again = req('POST', 'enddemo', array('code' => $code), $host);
check($again['ok'], 'a double tap on End demo is harmless');

echo "\nRestart in the same room, end mid-game, and a pure solo game (0 rivals)\n";
$s = req('POST', 'start', array('code' => $code, 'demo' => true, 'bots' => 1), $host);
check($s['ok'] && count($s['rivals']) === 1 && count(state($code, $host)['players']) === 2, 'the same room starts a new demo with 1 rival');
$st = state($code, $host);
$r = req('POST', 'roll', array('code' => $code, 'turn' => $st['game']['turn'], 'key' => tapKey()), $host);
check($r['ok'], 'host rolls in the restarted demo');
$e = req('POST', 'enddemo', array('code' => $code), $host);
$st = state($code, $host);
check($e['ok'] && $st['game']['status'] === 'lobby' && count($st['players']) === 1, 'ending mid-game also returns to the lobby');
$s = req('POST', 'start', array('code' => $code, 'demo' => true, 'bots' => 0), $host);
check($s['ok'] && empty($s['rivals']), 'bots = 0: a pure solo game starts');
$st = state($code, $host);
check(count($st['players']) === 1 && $st['game']['demo'] === true && $st['game']['currentId'] === $st['players'][0]['id'], 'solo: one player, demo = true, it is their turn');
$r = req('POST', 'roll', array('code' => $code, 'turn' => $st['game']['turn'], 'key' => tapKey()), $host);
$st = state($code, $host);
check($r['ok'] && ($st['game']['status'] === 'finished' || $st['game']['currentId'] === $st['players'][0]['id']), 'solo: after a roll it is the host again (no one else to wait for)');
req('POST', 'enddemo', array('code' => $code), $host);
list($code2, $host2) = newRoom();
$s = req('POST', 'start', array('code' => $code2, 'demo' => true, 'bots' => 9), $host2);
check($s['ok'] && count($s['rivals']) === 2, 'bots = 9 is capped at 2 rivals');
req('POST', 'enddemo', array('code' => $code2), $host2);

echo $fails ? "\n$fails FAILED\n" : "\nALL PASSED\n";
exit($fails ? 1 : 0);
