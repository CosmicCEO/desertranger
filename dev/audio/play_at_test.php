<?php
/**
 * Offline check of the one allowed server change (hand-off 5.1): dr_add_event() stamps play_at_ms when a cue is set
 * OR when $forcePlayAt is true, and leaves it NULL otherwise. No MySQL, no config.php: the real function source is
 * extracted from desertranger/lib/game.php and evaluated against an in-memory SQLite table.
 * usage: php dev/audio/play_at_test.php      (exit 0 = pass)
 */
$src = file_get_contents(__DIR__ . '/../../desertranger/lib/game.php');
foreach (array('dr_add_event', 'mb_substr_safe') as $fn) {
    if (!preg_match('/^function ' . $fn . '\(.*?^}\n/ms', $src, $m)) { fwrite(STDERR, "cannot find $fn\n"); exit(2); }
    eval($m[0]);
}
function dr_config() { return array('cue_lead_ms' => 1500); }
function dr_now_ms() { return 1000000; }
function dr_now_sql() { return '2026-01-01 00:00:00'; }

$db = new PDO('sqlite::memory:');
$db->exec('CREATE TABLE events (id INTEGER PRIMARY KEY, game_id INT, turn_number INT, type TEXT, message TEXT, payload TEXT, cue TEXT, play_at_ms INT, created_at TEXT)');
dr_add_event($db, 1, 1, 'turn', 'cue only', null, 'cheer');          // old behaviour: cue -> stamped
dr_add_event($db, 1, 1, 'turn', 'forced, no cue', null, null, true);  // new: forced -> stamped
dr_add_event($db, 1, 1, 'skip', 'plain log line');                    // unchanged: no cue, not forced -> NULL
dr_add_event($db, 1, 1, 'join', 'default args', null, null, false);   // unchanged
$rows = $db->query('SELECT message, cue, play_at_ms FROM events ORDER BY id')->fetchAll(PDO::FETCH_ASSOC);
$want = array(1001500, 1001500, null, null);
$fail = 0;
foreach ($rows as $i => $r) {
    $ok = ($r['play_at_ms'] === null ? null : (int)$r['play_at_ms']) === $want[$i];
    echo ($ok ? 'ok   ' : 'FAIL ') . str_pad($r['message'], 18) . ' cue=' . var_export($r['cue'], true) . ' play_at_ms=' . var_export($r['play_at_ms'], true) . "\n";
    if (!$ok) $fail++;
}
echo $fail ? "$fail FAILED\n" : "4 passed, 0 failed\n";
exit($fail ? 1 : 0);
