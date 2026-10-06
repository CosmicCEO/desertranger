<?php
/**
 * CLI tests for lib/rules.php.   Run:  php tests/rules_test.php
 * No PHPUnit needed (no Composer on the host). Exit code 0 = all passed.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
require __DIR__ . '/../lib/rules.php';

// Deployed copy first, else the repo's master copy in /board/.
$BOARD = is_file(__DIR__ . '/../board/desert-ranger.json')
    ? __DIR__ . '/../board/desert-ranger.json' : __DIR__ . '/../../board/desert-ranger.json';
$R = DesertRangerRules::fromFile($BOARD);
$pass = 0; $fail = 0;

function check($cond, $label) {
    global $pass, $fail;
    if ($cond) { $pass++; echo "  ok   $label\n"; }
    else       { $fail++; echo "  FAIL $label\n"; }
}
/** A die that returns the given values in order and complains if it runs out. */
function dice(array $values) {
    return function ($sides) use (&$values) {
        if (!$values) throw new Exception('test die ran out of values');
        return array_shift($values);
    };
}
/** State with N players, optionally placing them. */
function st($R, $n, array $pos = array(), $current = 0) {
    $pl = array();
    for ($i = 0; $i < $n; $i++) $pl[] = array('id' => $i + 1, 'name' => 'P' . $i);
    $s = $R->newGameState($pl);
    foreach ($pos as $i => $p) $s['players'][$i]['pos'] = $p;
    $s['current'] = $current;
    return $s;
}
function throwsRule($fn) { try { $fn(); } catch (RuleError $e) { return true; } return false; }

echo "Board: $BOARD\n";
echo "Plain + goto\n";
$r = $R->roll(st($R, 2), dice(array(2)));
check($r['state']['players'][0]['pos'] === 2 && $r['state']['current'] === 1, '0 +2 -> Palm Canyon, turn passes');
check($r['state']['turn'] === 2, 'turn counter increments');
$r = $R->roll(st($R, 2), dice(array(1)));
check($r['state']['players'][0]['pos'] === 20, '1 Go to Hawk Canyon -> 20');
check(strpos($r['log'][0], 'Hawk Canyon') !== false, 'log mentions Hawk Canyon: ' . $r['log'][0]);

echo "Chains\n";
$r = $R->roll(st($R, 2, array(38)), dice(array(3)));
check($r['state']['players'][0]['pos'] === 12 && $r['state']['players'][0]['skip'] === 1, '41 -> 12 Ocotillo Wells also loses a turn');
check($r['cue'] === 'aww', 'big setback cues aww');
$r = $R->roll(st($R, 2, array(43)), dice(array(1, 3)));
check($r['state']['players'][0]['pos'] === 12 && $r['state']['players'][0]['skip'] === 1, '44 dice 3 -> 41 -> 12 + lose turn (3-deep chain)');
$r = $R->roll(st($R, 2, array(43)), dice(array(1, 4)));
check($r['state']['players'][0]['pos'] === 34, '44 dice 4 -> 40 Subpoena -> 34 Court');
$r = $R->roll(st($R, 2, array(43)), dice(array(1, 2)));
check($r['state']['players'][0]['pos'] === 42 && $r['state']['players'][0]['skip'] === 1, '44 dice 2 -> 42 lose turn');
$r = $R->roll(st($R, 2, array(43)), dice(array(1, 6)));
check($r['state']['players'][0]['pos'] === 38 && $r['cue'] === 'aww', '44 dice 6 -> 38, aww');
$r = $R->roll(st($R, 2, array(45)), dice(array(3)));
check($r['state']['players'][0]['pos'] === 39, '48 plain -9 -> 39 Fish Creek (TODO open rule)');
$r = $R->roll(st($R, 2, array(46)), dice(array(4)));
check($r['state']['players'][0]['pos'] === 19, '50 Ground Fire -> 19 Arroyo Salado');
$r = $R->roll(st($R, 2, array(20)), dice(array(2)));
check($r['state']['players'][0]['pos'] === 32, '22 +10 -> 32');

echo "Roll again\n";
$r = $R->roll(st($R, 3, array(11)), dice(array(3)));
check($r['state']['players'][0]['pos'] === 14 && $r['state']['current'] === 0, '14 roll again keeps the turn');
check($r['cue'] === 'cheer', 'roll again cues cheer');
$s = st($R, 3, array(25));
$s = $R->roll($s, dice(array(1)))['state'];   // 26 roll again
$s = $R->roll($s, dice(array(3)))['state'];   // 29 roll again
check($s['players'][0]['pos'] === 29 && $s['current'] === 0, 'consecutive roll-agains (no limit)');
$s = $R->roll($s, dice(array(2)))['state'];   // 31 swap pending
check($s['pending']['type'] === 'swap', 'then lands on swap -> pending choice');

echo "Shortcut (optional, exact landing)\n";
$r = $R->roll(st($R, 2, array(4)), dice(array(2)));
check($r['state']['pending']['type'] === 'shortcut' && $r['state']['current'] === 0, 'exact landing on 6 offers shortcut');
check(throwsRule(function () use ($R, $r) { $R->roll($r['state'], dice(array(1))); }), 'cannot roll while a choice is pending');
$t = $R->choose($r['state'], array('action' => 'shortcut'), dice(array()));
check($t['state']['players'][0]['pos'] === 33 && $t['state']['current'] === 1, 'take shortcut -> 33, turn passes');
$t = $R->choose($r['state'], array('action' => 'skip'), dice(array()));
check($t['state']['players'][0]['pos'] === 6 && $t['state']['current'] === 1, 'decline shortcut stays on 6');
$r = $R->roll(st($R, 2, array(4)), dice(array(3)));
check(empty($r['state']['pending']) && $r['state']['players'][0]['pos'] === 7, 'passing 6 gives no shortcut');

echo "Swap (optional, any player)\n";
$s = st($R, 3, array(25, 40, 3));
$r = $R->roll($s, dice(array(6)));
check($r['state']['pending']['type'] === 'swap', 'land on 31 -> swap pending');
$t = $R->choose($r['state'], array('action' => 'swap', 'target' => 2), dice(array()));
check($t['state']['players'][0]['pos'] === 3 && $t['state']['players'][2]['pos'] === 31, 'swap with player behind works');
$t = $R->choose($r['state'], array('action' => 'swap', 'target' => 1), dice(array()));
check($t['state']['players'][0]['pos'] === 40 && $t['state']['players'][1]['pos'] === 31, 'swap with player ahead works (no chain on 40)');
check(throwsRule(function () use ($R, $r) { $R->choose($r['state'], array('action' => 'swap', 'target' => 0), dice(array())); }), 'cannot swap with yourself');
check(throwsRule(function () use ($R, $r) { $R->choose($r['state'], array('action' => 'shortcut'), dice(array())); }), 'wrong choice type rejected');
$r = $R->roll(st($R, 1, array(25)), dice(array(6)));
check(empty($r['state']['pending']), 'swap skipped in solo play');

echo "Lose turns\n";
$s = st($R, 3, array(9));
$s = $R->roll($s, dice(array(3)))['state']; // P0 -> 12 lose 1
check($s['current'] === 1, 'P1 up next');
$s = $R->roll($s, dice(array(2)))['state']; // P1 -> 2
$r = $R->roll($s, dice(array(2)));          // P2 -> 2, P0 skipped
check($r['state']['current'] === 1 && $r['state']['players'][0]['skip'] === 0, 'P0 skipped once, back to P1');
check(count($r['log']) === 2 && strpos($r['log'][1], 'P0 loses this turn') !== false, 'skip has its own log line');
$s = st($R, 2, array(26)); // from 26 roll 4 -> 30 lose 2 turns
$s = $R->roll($s, dice(array(4)))['state'];
check($s['players'][0]['pos'] === 30 && $s['players'][0]['skip'] === 2, '30 loses 2 turns');
$s = $R->roll($s, dice(array(2)))['state']; // P1, P0 skip -> P1 again
check($s['current'] === 1 && $s['players'][0]['skip'] === 1, '2-player: P1 goes again while P0 skips');
$s = $R->roll($s, dice(array(2)))['state']; // P1 -> 4 (P0 burns 2nd skip)
$s = $R->roll($s, dice(array(1)))['state']; // P1 -> 5, then P0's turn
check($s['current'] === 0 && $s['players'][0]['skip'] === 0, 'P0 back after 2 skipped turns');

echo "Finish\n";
$r = $R->roll(st($R, 2, array(47)), dice(array(6)));
check($r['state']['status'] === 'finished' && $r['state']['winner'] === 0 && $r['state']['players'][0]['pos'] === 51, 'overshoot wins, piece sits on FINISH');
check($r['cue'] === 'cheer', 'win cues cheer');
check(throwsRule(function () use ($R, $r) { $R->roll($r['state'], dice(array(1))); }), 'no rolling after the game ends');
$r = $R->roll(st($R, 2, array(47)), dice(array(4)));
check($r['state']['status'] === 'finished', 'exact landing wins');

echo "Host controls: skipTurn and sitOut\n";
$s = st($R, 3);
$r = $R->skipTurn($s);
check($r['state']['current'] === 1 && $r['state']['turn'] === $s['turn'] + 1 && $r['cue'] === null, 'skipTurn passes the turn on (turn +1, no cue)');
check($r['log'] === array('P0 was skipped by the host.') && $r['events'] === array(), 'skipTurn log line, no events');
check($r['state']['players'][0]['pos'] === 0 && $r['state']['players'][0]['skip'] === 0, 'the skipped player is not moved or penalised');
$s = st($R, 2, array(2));                                     // 2 + 4 = 6: optional shortcut
$s = $R->roll($s, dice(array(4)))['state'];
check(!empty($s['pending']) && $s['pending']['type'] === 'shortcut', 'setup: a shortcut choice is pending');
$r = $R->skipTurn($s);
check($r['state']['pending'] === null && $r['state']['current'] === 1 && $r['state']['players'][0]['pos'] === 6, 'skipTurn drops a pending choice without applying it');
$s = st($R, 2, array(10));                                    // 10 + 4 = 14: roll again, current stays
$s = $R->roll($s, dice(array(4)))['state'];
check($s['current'] === 0, 'setup: roll again keeps the turn');
check($R->skipTurn($s)['state']['current'] === 1, 'skipTurn works on a roll-again turn');
$s = st($R, 3); $s['players'][1]['skip'] = 1;
$r = $R->skipTurn($s);
check($r['state']['current'] === 2 && $r['state']['players'][1]['skip'] === 0 && count($r['events']) === 1 && $r['events'][0]['type'] === 'skipped', 'skipTurn still burns the next player\'s owed turn');
check(count($r['log']) === 2 && strpos($r['log'][1], 'P1 loses this turn') !== false, '...with its own log line');
check(throwsRule(function () use ($R) { $s = st($R, 2); $s['status'] = 'finished'; $R->skipTurn($s); }), 'no skipping after the game ends');
check(throwsRule(function () use ($R) { $s = st($R, 2); $s['players'][1]['skip'] = DesertRangerRules::SIT_OUT; $R->skipTurn($s); }), 'no skipping when nobody else is in');

$s = st($R, 3);
$r = $R->sitOut($s, 1, true);
check($r['state']['players'][1]['skip'] === DesertRangerRules::SIT_OUT && $r['state']['current'] === 0 && $r['state']['turn'] === $s['turn'], 'sitOut on another player: flag set, turn unchanged');
check($r['log'] === array('P1 is sitting out.'), 'sitOut log line');
$s = $r['state']; $lines = 0; $order = array();
for ($i = 0; $i < 6; $i++) {                                  // 6 rolls: P0, P2, P0, P2, P0, P2 and never P1
    $order[] = $s['current'];
    $r = $R->roll($s, dice(array(1)));
    $lines += count($r['log']) - 1;
    $s = $r['state'];
}
check($order === array(0, 2, 0, 2, 0, 2), 'a sitting-out player is passed over every round');
check($lines === 0 && $s['players'][1]['skip'] === DesertRangerRules::SIT_OUT, '...silently, and nothing is burned');
$r = $R->sitOut($s, 1, false);
check($r['state']['players'][1]['skip'] === 0 && $r['log'] === array('P1 is back in the game.'), 'bringing them back clears the flag');
$s = $r['state']; $s['current'] = 0;
check($R->roll($s, dice(array(1)))['state']['current'] === 1, '...and they get their turn again');
$s = st($R, 3);
$r = $R->sitOut($s, 0, true);                                 // the player on turn sits out
check($r['state']['current'] === 1 && $r['state']['turn'] === $s['turn'] + 1 && $r['state']['pending'] === null, 'sitting out the current player moves the turn on (turn +1)');
$s = st($R, 2); $s = $R->sitOut($s, 0, true)['state'];
check(throwsRule(function () use ($R, $s) { $R->sitOut($s, 1, true); }), 'the last player in cannot sit out');
check(throwsRule(function () use ($R) { $R->sitOut(st($R, 2), 5, true); }), 'sitOut: no such player');
check(throwsRule(function () use ($R) { $s = st($R, 2); $s['status'] = 'finished'; $R->sitOut($s, 1, true); }), 'sitOut: not after the game ends');
$s = st($R, 2); $s['players'][0]['skip'] = DesertRangerRules::SIT_OUT; $s['players'][1]['skip'] = DesertRangerRules::SIT_OUT; $s['current'] = 1;
$r = $R->roll($s, dice(array(1)));
check($r['state']['current'] === 1, 'safety: if everybody is sitting out the turn stays put (no endless loop)');
$s = st($R, 2); $s = $R->sitOut($s, 1, true)['state'];       // P0 plays alone against a sitter
$s = $R->roll($s, dice(array(2)))['state'];
check($s['current'] === 0 && $s['players'][0]['pos'] === 2, 'a lone active player keeps rolling');

echo "Synthetic boards (guards)\n";
$loop = array('squares' => array(
    array('i' => 0, 'type' => 'start'), array('i' => 1, 'type' => 'goto', 'target' => 2),
    array('i' => 2, 'type' => 'goto', 'target' => 1), array('i' => 3, 'type' => 'move', 'delta' => -9),
    array('i' => 4, 'type' => 'move', 'delta' => 1), array('i' => 5, 'type' => 'rollAgain'),
    array('i' => 6, 'type' => 'move', 'delta' => 50), array('i' => 7, 'type' => 'finish')));
$L = new DesertRangerRules($loop);
$r = $L->roll(st($L, 2), dice(array(1)));
$guard = array_filter($r['events'], function ($e) { return $e['type'] === 'chainGuard'; });
check(count($guard) === 1 && $r['state']['current'] === 1, 'goto loop 1<->2 stops at MAX_CHAIN_DEPTH and turn passes');
$r = $L->roll(st($L, 2), dice(array(3)));
check($r['state']['players'][0]['pos'] === 0, 'moves never go below START');
$r = $L->roll(st($L, 2), dice(array(4)));
check($r['state']['players'][0]['pos'] === 5 && $r['state']['current'] === 0, 'a move that lands on roll-again chains into roll again');
$r = $L->roll(st($L, 2, array(5)), dice(array(1)));
check($r['state']['status'] === 'finished', 'forward move past FINISH wins');

echo "Exhaustive: every square x every die x every 44-die\n";
$bad = 0; $cases = 0;
for ($sq = 0; $sq < 51; $sq++) for ($d = 1; $d <= 6; $d++) for ($d2 = 1; $d2 <= 6; $d2++) {
    $cases++;
    try {
        $r = $R->roll(st($R, 3, array($sq)), dice(array($d, $d2)));
        $p = $r['state']['players'][0]['pos'];
        if ($p < 0 || $p > 51) $bad++;
    } catch (Exception $e) {
        if ($e->getMessage() !== 'test die ran out of values') { $bad++; echo $e->getMessage(), "\n"; }
    }
}
check($bad === 0, "$cases cases, all terminate with valid positions");

echo "Fuzz: 3000 random games (2-8 players) to the finish\n";
$rng = function ($sides) { return random_int(1, $sides); };
$maxActions = 0; $unfinished = 0; $invalid = 0; $totalActions = 0;
for ($g = 0; $g < 3000; $g++) {
    $s = st($R, random_int(2, 8));
    for ($a = 0; $a < 5000 && $s['status'] === 'active'; $a++) {
        $prevTurn = $s['turn'];
        if (!empty($s['pending'])) {
            $p = $s['pending']['player'];
            if ($s['pending']['type'] === 'swap' && random_int(0, 1)) {
                do { $t = random_int(0, count($s['players']) - 1); } while ($t === $p);
                $r = $R->choose($s, array('action' => 'swap', 'target' => $t), $rng);
            } elseif ($s['pending']['type'] === 'shortcut' && random_int(0, 1)) {
                $r = $R->choose($s, array('action' => 'shortcut'), $rng);
            } else {
                $r = $R->choose($s, array('action' => 'skip'), $rng);
            }
        } else {
            $r = $R->roll($s, $rng);
        }
        $s = $r['state'];
        if ($s['turn'] !== $prevTurn + 1) $invalid++;
        foreach ($s['players'] as $pl) if ($pl['pos'] < 0 || $pl['pos'] > 51 || $pl['skip'] < 0) $invalid++;
    }
    if ($s['status'] !== 'finished') $unfinished++;
    $maxActions = max($maxActions, $a); $totalActions += $a;
}
check($unfinished === 0, 'every game finished');
check($invalid === 0, 'invariants held (turn+1 per action, 0<=pos<=51, skip>=0)');
echo "       avg actions/game " . round($totalActions / 3000) . ", max $maxActions\n";

echo "Fuzz with host controls: 1000 games with random skips and sit-outs\n";
$unfinished = 0; $invalid = 0; $badCurrent = 0;
for ($g = 0; $g < 1000; $g++) {
    $s = st($R, random_int(2, 8));
    for ($a = 0; $a < 5000 && $s['status'] === 'active'; $a++) {
        $prevTurn = $s['turn'];
        $roll = random_int(1, 100);
        try {
            if ($roll <= 6) {                                     // host skips the current player
                $r = $R->skipTurn($s); $s = $r['state'];
                if ($s['turn'] !== $prevTurn + 1) $invalid++;
                continue;
            }
            if ($roll <= 10) {                                    // host sits a random player out or back in
                $i = random_int(0, count($s['players']) - 1);
                $r = $R->sitOut($s, $i, (bool)random_int(0, 1)); $s = $r['state'];
                if ($s['turn'] !== $prevTurn && $s['turn'] !== $prevTurn + 1) $invalid++;
                continue;
            }
        } catch (RuleError $e) { /* refused (last player in, nobody to hand over to): fine */ }
        $in = 0; foreach ($s['players'] as $pl) if ($pl['skip'] < DesertRangerRules::SIT_OUT) $in++;
        if ($in < 1) $invalid++;                                  // sitOut must never leave nobody in
        if ($in >= 1 && $s['players'][$s['current']]['skip'] >= DesertRangerRules::SIT_OUT) $badCurrent++;
        if (!empty($s['pending'])) {
            $r = $R->choose($s, array('action' => 'skip'), $rng);
        } else {
            $r = $R->roll($s, $rng);
        }
        $s = $r['state'];
        if ($s['turn'] !== $prevTurn + 1) $invalid++;
        foreach ($s['players'] as $pl) if ($pl['pos'] < 0 || $pl['pos'] > 51 || $pl['skip'] < 0) $invalid++;
    }
    if ($s['status'] !== 'finished') $unfinished++;
}
check($unfinished === 0, 'every game with host controls finished');
check($invalid === 0, 'invariants held (turn counts, positions, never everybody sitting out)');
check($badCurrent === 0, 'a sitting-out player is never the one on turn');

echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
