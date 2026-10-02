<?php
/**
 * Game service: everything that touches the database for a game.
 * The rules themselves live in rules.php (pure); this file loads state from
 * MySQL, calls the rules engine, and saves the result in ONE transaction.
 */
require_once __DIR__ . '/db.php';
require_once __DIR__ . '/rules.php';

/** Errors safe to show to the player (bad code, vehicle taken...). $status = HTTP status. */
class ApiError extends Exception
{
    public $status;
    public function __construct($message, $status = 400)
    {
        parent::__construct($message);
        $this->status = $status;
    }
}

const DR_MAX_PLAYERS = 8;
const DR_MIN_PLAYERS = 2;

/** The 8 pieces. Key = art file name (assets/img/pieces/<key>.png), value = display label. */
function dr_vehicles()
{
    return array(
        'bronco-orange'  => 'Marigold',
        'scout-butter'   => 'Butter Scout',
        'jeep-red'       => 'Red Rocket',
        'ranger-green'   => 'Ranger Green',
        'buggy-blue'     => 'Blue Buggy',
        'rail-purple'    => 'Purple Rail',
        'cruiser-teal'   => 'Teal Cruiser',
        'blazer-twotone' => 'Two-Tone',
    );
}

/**
 * Where the board JSON lives. On the web host it is desertranger/board/ (copied
 * there by dev/make-assets.sh); in a repo checkout it is the master copy in /board/.
 */
function dr_board_path()
{
    foreach (array(__DIR__ . '/../board/desert-ranger.json', __DIR__ . '/../../board/desert-ranger.json') as $f) {
        if (is_file($f)) {
            return $f;
        }
    }
    throw new RuntimeException('board/desert-ranger.json not found');
}

/** The rules engine for the (only) board. */
function dr_rules()
{
    static $r = null;
    if ($r === null) {
        $r = DesertRangerRules::fromFile(dr_board_path());
    }
    return $r;
}

/** Clean up a display name: trim, collapse spaces, 1-20 characters. */
function dr_clean_name($name)
{
    $name = preg_replace('/[\x00-\x1F\x7F]+/u', '', (string)$name);
    $name = trim(preg_replace('/\s+/u', ' ', $name));
    if ($name === '') {
        throw new ApiError('Please enter a name.');
    }
    if (function_exists('mb_substr')) {
        $name = mb_substr($name, 0, 20, 'UTF-8');
    } else {
        $name = substr($name, 0, 20);
    }
    return $name;
}

function dr_check_vehicle($vehicle)
{
    $v = dr_vehicles();
    if (!isset($v[$vehicle])) {
        throw new ApiError('Pick a vehicle.');
    }
    return $vehicle;
}

function dr_normalize_code($code)
{
    return strtoupper(preg_replace('/[^A-Za-z]/', '', (string)$code));
}

/** Random 4-letter room code (no I or O, they look like 1 and 0). */
function dr_random_code()
{
    $letters = 'ABCDEFGHJKLMNPQRSTUVWXYZ';
    $code = '';
    for ($i = 0; $i < 4; $i++) {
        $code .= $letters[random_int(0, strlen($letters) - 1)];
    }
    return $code;
}

/** New secret seat token. The client keeps the token; the DB only keeps its sha256. */
function dr_new_token()
{
    return bin2hex(random_bytes(24));
}

function dr_hash_token($token)
{
    return hash('sha256', (string)$token);
}

/** Find a game by code, or throw 404. $lock = true adds FOR UPDATE (call inside a transaction). */
function dr_find_game(PDO $db, $code, $lock = false)
{
    $st = $db->prepare('SELECT * FROM games WHERE code = ?' . ($lock ? ' FOR UPDATE' : ''));
    $st->execute(array(dr_normalize_code($code)));
    $g = $st->fetch();
    if (!$g) {
        throw new ApiError('No game with that room code.', 404);
    }
    return $g;
}

/** All players of a game in seat (= turn) order. */
function dr_players(PDO $db, $gameId)
{
    $st = $db->prepare('SELECT * FROM players WHERE game_id = ? ORDER BY seat');
    $st->execute(array($gameId));
    return $st->fetchAll();
}

/** Which player does this token belong to (in this game)? null if none. */
function dr_player_for_token(array $players, $token)
{
    if (!$token) {
        return null;
    }
    $h = dr_hash_token($token);
    foreach ($players as $p) {
        if (hash_equals($p['token_hash'], $h)) {
            return $p;
        }
    }
    return null;
}

/** Append a log event. $payload is any array (stored as JSON). */
function dr_add_event(PDO $db, $gameId, $turn, $type, $message, $payload = null, $cue = null)
{
    $playAt = null;
    if ($cue) {
        // Schedule the sound a little in the future so every polling device can hear about it in time.
        $playAt = dr_now_ms() + (int)dr_config()['cue_lead_ms'];
    }
    $st = $db->prepare('INSERT INTO events (game_id, turn_number, type, message, payload, cue, play_at_ms, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)');
    $st->execute(array($gameId, $turn, $type, mb_substr_safe($message, 500),
        $payload === null ? null : json_encode($payload), $cue, $playAt, dr_now_sql()));
}

function mb_substr_safe($s, $len)
{
    return function_exists('mb_substr') ? mb_substr($s, 0, $len, 'UTF-8') : substr($s, 0, $len);
}

// ===========================================================================
//  ACTIONS
// ===========================================================================

/** Create a game with the caller as host (seat 0). Returns [code, token]. */
function dr_create_game(PDO $db, $name, $vehicle)
{
    $name = dr_clean_name($name);
    dr_check_vehicle($vehicle);
    $now = dr_now_sql();
    $db->beginTransaction();
    try {
        $result = dr_create_game_tx($db, $name, $vehicle, $now);
        $db->commit();
        return $result;
    } catch (Exception $e) {
        $db->rollBack();
        throw $e;
    }
}

function dr_create_game_tx(PDO $db, $name, $vehicle, $now)
{
    // Pick an unused code (retry on the rare collision).
    for ($try = 0; ; $try++) {
        $code = dr_random_code();
        try {
            $st = $db->prepare('INSERT INTO games (code, status, created_at, updated_at) VALUES (?, \'lobby\', ?, ?)');
            $st->execute(array($code, $now, $now));
            break;
        } catch (PDOException $e) {
            if ($try > 20) {
                throw $e;
            }
        }
    }
    $gameId = (int)$db->lastInsertId();
    list($token, $playerId) = dr_join_insert($db, $gameId, 0, $name, $vehicle);
    $db->prepare('UPDATE games SET host_player_id = ? WHERE id = ?')->execute(array($playerId, $gameId));
    dr_add_event($db, $gameId, 0, 'join', $name . ' created the game (' . dr_vehicles()[$vehicle] . ').');
    return array($code, $token);
}

/** Insert a player row; returns [plain token, new player id]. */
function dr_join_insert(PDO $db, $gameId, $seat, $name, $vehicle)
{
    $token = dr_new_token();
    $now = dr_now_sql();
    $st = $db->prepare('INSERT INTO players (game_id, seat, display_name, vehicle, token_hash, joined_at, last_seen_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)');
    $st->execute(array($gameId, $seat, $name, $vehicle, dr_hash_token($token), $now, $now));
    return array($token, (int)$db->lastInsertId());
}

/** Join an existing game that is still in the lobby. Returns the token. */
function dr_join_game(PDO $db, $code, $name, $vehicle)
{
    $name = dr_clean_name($name);
    dr_check_vehicle($vehicle);
    $db->beginTransaction();
    try {
        $g = dr_find_game($db, $code, true); // lock: two people joining at once get different seats
        if ($g['status'] !== 'lobby') {
            throw new ApiError('That game has already started.', 409);
        }
        $players = dr_players($db, $g['id']);
        if (count($players) >= DR_MAX_PLAYERS) {
            throw new ApiError('That game is full (8 players).', 409);
        }
        foreach ($players as $p) {
            if ($p['vehicle'] === $vehicle) {
                throw new ApiError('Someone already picked that vehicle.', 409);
            }
        }
        list($token) = dr_join_insert($db, $g['id'], count($players), $name, $vehicle);
        dr_add_event($db, $g['id'], 0, 'join', $name . ' joined (' . dr_vehicles()[$vehicle] . ').');
        $db->prepare('UPDATE games SET updated_at = ? WHERE id = ?')->execute(array(dr_now_sql(), $g['id']));
        $db->commit();
        return $token;
    } catch (Exception $e) {
        $db->rollBack();
        throw $e;
    }
}

/** Host starts the game. */
function dr_start_game(PDO $db, $code, $token)
{
    $db->beginTransaction();
    try {
        $g = dr_find_game($db, $code, true);
        $players = dr_players($db, $g['id']);
        $me = dr_player_for_token($players, $token);
        if (!$me || (int)$me['id'] !== (int)$g['host_player_id']) {
            throw new ApiError('Only the host can start the game.', 403);
        }
        if ($g['status'] !== 'lobby') {
            $db->rollBack();
            return; // already started: treat as success (double tap)
        }
        if (count($players) < DR_MIN_PLAYERS) {
            throw new ApiError('Need at least 2 players.', 409);
        }
        $db->prepare("UPDATE games SET status = 'active', turn_number = 1, current_seat = ?, updated_at = ? WHERE id = ?")
           ->execute(array($players[0]['seat'], dr_now_sql(), $g['id']));
        dr_add_event($db, $g['id'], 1, 'start', 'Game on! ' . $players[0]['display_name'] . ' rolls first.');
        $db->commit();
    } catch (Exception $e) {
        if ($db->inTransaction()) {
            $db->rollBack();
        }
        throw $e;
    }
}

/**
 * Roll or answer a choice.  ONE transaction, game row locked with FOR UPDATE.
 *
 * Double-tap protection:
 *   - $turn must equal games.turn_number (the client sends the turn it saw);
 *     a second tap carries the old number and is rejected as stale.
 *   - $key is a random id per tap. If the exact same request is retried
 *     (flaky network), we see last_action_key === $key and report success
 *     without rolling again.
 *
 * $kind = 'roll' | 'choose'.  $choice = ['action'=>..., 'target'=>playerId]
 */
function dr_take_action(PDO $db, $code, $token, $kind, $turn, $key, array $choice = array())
{
    $key = substr(preg_replace('/[^A-Za-z0-9_-]/', '', (string)$key), 0, 64);
    if ($key === '') {
        throw new ApiError('Missing request key.');
    }
    $db->beginTransaction();
    try {
        $g = dr_find_game($db, $code, true);
        if ($g['last_action_key'] === $key) {
            $db->rollBack();
            return array('duplicate' => true);
        }
        if ($g['status'] !== 'active') {
            throw new ApiError('The game is not in progress.', 409);
        }
        if ((int)$turn !== (int)$g['turn_number']) {
            throw new ApiError('That turn already happened.', 409);
        }
        $players = dr_players($db, $g['id']);
        $me = dr_player_for_token($players, $token);
        if (!$me) {
            throw new ApiError('You are not in this game.', 403);
        }

        // ---- Build the engine state from the DB rows ----
        $state = dr_engine_state($g, $players);
        if ($state['current'] !== (int)$me['seat']) {
            throw new ApiError("It's not your turn.", 409);
        }

        $rules = dr_rules();
        $die = function ($sides) { return random_int(1, $sides); }; // the ONLY place dice are rolled
        if ($kind === 'roll') {
            $res = $rules->roll($state, $die);
        } else {
            $c = array('action' => isset($choice['action']) ? (string)$choice['action'] : '');
            if (isset($choice['target'])) {
                // Client sends a player id; the engine wants a seat index.
                $c['target'] = -1;
                foreach ($players as $i => $p) {
                    if ((int)$p['id'] === (int)$choice['target']) {
                        $c['target'] = $i;
                    }
                }
            }
            $res = $rules->choose($state, $c, $die);
        }
        $new = $res['state'];

        // ---- Save players ----
        $up = $db->prepare('UPDATE players SET position = ?, skip_turns = ? WHERE id = ?');
        foreach ($new['players'] as $i => $p) {
            if ($p['pos'] !== $state['players'][$i]['pos'] || $p['skip'] !== $state['players'][$i]['skip']) {
                $up->execute(array($p['pos'], $p['skip'], $players[$i]['id']));
            }
        }
        // ---- Save game ----
        $db->prepare('UPDATE games SET status = ?, turn_number = ?, current_seat = ?, pending_json = ?,
                             winner_player_id = ?, last_action_key = ?, updated_at = ? WHERE id = ?')
           ->execute(array(
               $new['status'], $new['turn'], $players[$new['current']]['seat'],
               $new['pending'] ? json_encode($new['pending']) : null,
               $new['winner'] === null ? null : $players[$new['winner']]['id'],
               $key, dr_now_sql(), $g['id']));

        // ---- Log events: first line carries the animation steps + sound cue ----
        $steps = dr_events_with_ids($res['events'], $players);
        foreach ($res['log'] as $n => $line) {
            if ($n === 0) {
                dr_add_event($db, $g['id'], $state['turn'], $new['status'] === 'finished' ? 'win' : 'turn',
                             $line, array('steps' => $steps), $res['cue']);
            } else {
                dr_add_event($db, $g['id'], $state['turn'], 'skip', $line);
            }
        }
        $db->commit();
        return array('duplicate' => false);
    } catch (Exception $e) {
        if ($db->inTransaction()) {
            $db->rollBack();
        }
        throw $e;
    }
}

/** DB rows -> rules engine state (players in seat order). */
function dr_engine_state(array $g, array $players)
{
    $list = array();
    $current = 0;
    foreach ($players as $i => $p) {
        $list[] = array('id' => (int)$p['id'], 'name' => $p['display_name'],
                        'pos' => (int)$p['position'], 'skip' => (int)$p['skip_turns']);
        if ((int)$p['seat'] === (int)$g['current_seat']) {
            $current = $i;
        }
    }
    $winner = null;
    foreach ($players as $i => $p) {
        if ((int)$p['id'] === (int)$g['winner_player_id']) {
            $winner = $i;
        }
    }
    return array(
        'status'  => $g['status'],
        'turn'    => (int)$g['turn_number'],
        'current' => $current,
        'players' => $list,
        'pending' => $g['pending_json'] ? json_decode($g['pending_json'], true) : null,
        'winner'  => $winner,
    );
}

/** Engine events use seat indexes; clients want player ids. */
function dr_events_with_ids(array $events, array $players)
{
    foreach ($events as &$e) {
        foreach (array('player', 'other') as $f) {
            if (isset($e[$f])) {
                $e[$f] = (int)$players[$e[$f]]['id'];
            }
        }
    }
    return $events;
}

/**
 * The polling endpoint's data: game, players, and events after $since.
 * Read-only except a cheap "last seen" touch at most every 20 s per player.
 */
function dr_state(PDO $db, $code, $since, $token)
{
    $g = dr_find_game($db, $code);
    $players = dr_players($db, $g['id']);
    $me = dr_player_for_token($players, $token);

    if ($me && strtotime($me['last_seen_at'] . ' UTC') < time() - 20) {
        $db->prepare('UPDATE players SET last_seen_at = ? WHERE id = ?')->execute(array(dr_now_sql(), $me['id']));
    }

    $since = max(0, (int)$since);
    if ($since > 0) {
        $st = $db->prepare('SELECT * FROM events WHERE game_id = ? AND id > ? ORDER BY id LIMIT 200');
        $st->execute(array($g['id'], $since));
        $rows = $st->fetchAll();
    } else {
        // First load: just the most recent history (the client will not animate/play these).
        $st = $db->prepare('SELECT * FROM events WHERE game_id = ? ORDER BY id DESC LIMIT 40');
        $st->execute(array($g['id']));
        $rows = array_reverse($st->fetchAll());
    }

    $events = array();
    foreach ($rows as $r) {
        $events[] = array(
            'id'     => (int)$r['id'],
            'type'   => $r['type'],
            'msg'    => $r['message'],
            'data'   => $r['payload'] ? json_decode($r['payload'], true) : null,
            'cue'    => $r['cue'],
            'playAt' => $r['play_at_ms'] === null ? null : (int)$r['play_at_ms'],
        );
    }

    $pl = array();
    $currentId = null;
    foreach ($players as $p) {
        $pl[] = array(
            'id'      => (int)$p['id'],
            'name'    => $p['display_name'],
            'vehicle' => $p['vehicle'],
            'seat'    => (int)$p['seat'],
            'pos'     => (int)$p['position'],
            'skip'    => (int)$p['skip_turns'],
        );
        if ((int)$p['seat'] === (int)$g['current_seat']) {
            $currentId = (int)$p['id'];
        }
    }
    $pending = $g['pending_json'] ? json_decode($g['pending_json'], true) : null;
    if ($pending) {
        $pending = array('type' => $pending['type'], 'playerId' => (int)$players[$pending['player']]['id']);
    }

    return array(
        'game' => array(
            'code'      => $g['code'],
            'status'    => $g['status'],
            'turn'      => (int)$g['turn_number'],
            'currentId' => $g['status'] === 'active' ? $currentId : null,
            'hostId'    => (int)$g['host_player_id'],
            'winnerId'  => $g['winner_player_id'] === null ? null : (int)$g['winner_player_id'],
            'pending'   => $pending,
        ),
        'players' => $pl,
        'meId'    => $me ? (int)$me['id'] : null,
        'events'  => $events,
    );
}
