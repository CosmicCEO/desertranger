<?php
/**
 * Desert Ranger JSON API.  One file, routed by ?a=<action>.
 * (No URL rewriting needed, so it works on any Apache/PHP host.)
 *
 *   GET  api.php?a=time                     -> {t}          clock-sync ping (no DB)
 *   GET  api.php?a=info                     -> {vehicles}
 *   GET  api.php?a=board                    -> the board JSON (names + x,y of squares)
 *   GET  api.php?a=peek&code=ABCD           -> {status, taken[], count}  (for the join screen)
 *   GET  api.php?a=state&code=ABCD&since=N  -> game, players, events after N   (polled ~1/s)
 *   POST api.php?a=create  {name, vehicle}             -> {code, token}
 *   POST api.php?a=join    {code, name, vehicle}       -> {code, token}
 *   GET  api.php?a=stats                    -> {games}      games being played now (homepage counter)
 *   POST api.php?a=start   {code}
 *   POST api.php?a=rematch {code}           host only: a finished game back to the lobby, same players
 *   POST api.php?a=nudge   {code}           "Knock, knock" to every phone (rate limited)
 *   POST api.php?a=roll    {code, turn, key}
 *   POST api.php?a=choose  {code, turn, key, action, target}
 *
 * Who am I?  The seat token is sent in the X-Player-Token header (from
 * localStorage). If that is missing we fall back to the dr_<CODE> cookie.
 * POSTs must be Content-Type: application/json, which a cross-site HTML form
 * cannot send, so the cookie fallback is not a CSRF hole.
 *
 * Every response includes "serverNow" (ms) so polls double as clock-sync samples.
 */

$action = isset($_GET['a']) ? $_GET['a'] : '';

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

// Fast path for clock sync: no includes, no DB, as little work as possible.
if ($action === 'time') {
    echo '{"ok":true,"t":' . (int)round(microtime(true) * 1000) . '}';
    exit;
}

require __DIR__ . '/lib/game.php';

/** Send JSON and stop. */
function dr_out(array $data, $status = 200)
{
    http_response_code($status);
    $data['serverNow'] = dr_now_ms();
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

/** Remember the seat token in a cookie too (survives localStorage being cleared). */
function dr_set_token_cookie($code, $token)
{
    $path = rtrim(dirname($_SERVER['SCRIPT_NAME']), '/\\') . '/';
    setcookie('dr_' . $code, $token, array(
        'expires'  => time() + 60 * 60 * 24 * 60, // 60 days
        'path'     => $path,
        'secure'   => !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off',
        'httponly' => true,
        'samesite' => 'Lax',
    ));
}

function dr_token_for($code)
{
    if (!empty($_SERVER['HTTP_X_PLAYER_TOKEN'])) {
        return (string)$_SERVER['HTTP_X_PLAYER_TOKEN'];
    }
    $c = 'dr_' . dr_normalize_code($code);
    return isset($_COOKIE[$c]) ? (string)$_COOKIE[$c] : null;
}

try {
    $in = array();
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $ctype = isset($_SERVER['CONTENT_TYPE']) ? $_SERVER['CONTENT_TYPE'] : '';
        if (stripos($ctype, 'application/json') !== 0) {
            throw new ApiError('JSON body required.', 415);
        }
        $in = json_decode(file_get_contents('php://input'), true);
        if (!is_array($in)) {
            throw new ApiError('Bad JSON.');
        }
    }
    $code = dr_normalize_code(isset($in['code']) ? $in['code'] : (isset($_GET['code']) ? $_GET['code'] : ''));
    $db = dr_db();

    switch ($action) {
        case 'info':
            dr_out(array('ok' => true, 'vehicles' => dr_vehicles()));

        case 'board':
            readfile(dr_board_path());
            exit;

        case 'peek':
            $g = dr_find_game($db, $code);
            $taken = array();
            foreach (dr_players($db, $g['id']) as $p) {
                $taken[] = $p['vehicle'];
            }
            dr_out(array('ok' => true, 'code' => $g['code'], 'status' => $g['status'], 'taken' => $taken));

        case 'state':
            $since = isset($_GET['since']) ? (int)$_GET['since'] : 0;
            dr_out(array('ok' => true) + dr_state($db, $code, $since, dr_token_for($code)));

        case 'create':
            requirePost();
            list($code, $token) = dr_create_game($db, isset($in['name']) ? $in['name'] : '', isset($in['vehicle']) ? $in['vehicle'] : '');
            dr_set_token_cookie($code, $token);
            dr_out(array('ok' => true, 'code' => $code, 'token' => $token));

        case 'join':
            requirePost();
            $token = dr_join_game($db, $code, isset($in['name']) ? $in['name'] : '', isset($in['vehicle']) ? $in['vehicle'] : '');
            dr_set_token_cookie($code, $token);
            dr_out(array('ok' => true, 'code' => $code, 'token' => $token));

        case 'start':
            requirePost();
            // demo = solo demo (host alone, 0-2 computer rivals); the rivals' tokens come back once, to the host only.
            $rivals = dr_start_game($db, $code, dr_token_for($code), !empty($in['demo']), isset($in['bots']) ? $in['bots'] : DR_MAX_DEMO_RIVALS);
            dr_out(array('ok' => true, 'rivals' => $rivals));

        case 'enddemo':
            requirePost();
            dr_end_demo($db, $code, dr_token_for($code));
            dr_out(array('ok' => true));

        case 'rematch':
            requirePost();
            dr_rematch($db, $code, dr_token_for($code));
            dr_out(array('ok' => true));

        case 'nudge':
            requirePost();
            dr_nudge($db, $code, dr_token_for($code));
            dr_out(array('ok' => true));

        case 'stats':
            dr_out(array('ok' => true) + dr_stats($db));

        case 'roll':
        case 'choose':
            requirePost();
            $r = dr_take_action($db, $code, dr_token_for($code), $action,
                isset($in['turn']) ? $in['turn'] : -1, isset($in['key']) ? $in['key'] : '', $in);
            dr_out(array('ok' => true, 'duplicate' => $r['duplicate']));

        default:
            throw new ApiError('Unknown action.', 404);
    }
} catch (ApiError $e) {
    dr_out(array('ok' => false, 'error' => $e->getMessage()), $e->status);
} catch (RuleError $e) {
    dr_out(array('ok' => false, 'error' => $e->getMessage()), 409);
} catch (Throwable $e) {
    error_log('Desert Ranger API error: ' . $e);
    $debug = false;
    try { $debug = !empty(dr_config()['debug']); } catch (Throwable $ignored) {}
    dr_out(array('ok' => false, 'error' => $debug ? $e->getMessage() : 'Server error.'), 500);
}

function requirePost()
{
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        throw new ApiError('Use POST.', 405);
    }
}
