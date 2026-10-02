<?php
/*
 * ===================================================================
 *  Desert Ranger - AMP host test kit  (amp-test.php)
 * ===================================================================
 *  One self-contained file. Upload it to the web host, open it in a
 *  browser, send the results to Jerod, then DELETE IT.
 *
 *  - Shows PASS / WARN / FAIL rows for PHP, Apache, MySQL, limits, clock.
 *  - Never shows full phpinfo() unless FULL_TOKEN below is set and
 *    the URL is  amp-test.php?full=1&token=THE_TOKEN
 *  - Turns itself off EXPIRE_DAYS after the file's modification time
 *    (i.e. after it was uploaded). Re-upload to reset the clock.
 *  - MySQL credentials are POSTed, used once, never stored, never echoed.
 *  - Deliberately written to *parse* on old PHP (5.4+) so that an old
 *    host shows a red FAIL instead of a blank page.
 * ===================================================================
 */

// ---- Settings (Jerod may edit these) ------------------------------
define('FULL_TOKEN', '');     // '' = full phpinfo() disabled. Set e.g. 'k7Qp2x' to enable ?full=1&token=k7Qp2x
define('EXPIRE_DAYS', 7);     // self-disable this many days after upload (file mtime)
define('SELF_REQUESTS', 10);  // number of server-side timing self-requests
// -------------------------------------------------------------------

error_reporting(E_ALL);
@ini_set('display_errors', '0');
header('X-Robots-Tag: noindex, nofollow');
header('Cache-Control: no-store, no-cache, must-revalidate');
header('Referrer-Policy: no-referrer');
header('X-Content-Type-Options: nosniff');

$T0 = microtime(true);
$VERSION = '1.0 (2026-10-01)';

function h($s) { return htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8'); }
function safe_equals($a, $b) {
    if (function_exists('hash_equals')) return hash_equals((string)$a, (string)$b);
    return (string)$a === (string)$b;
}

// ---- 1. Expiry check (runs before anything else) ------------------
$mtime = @filemtime(__FILE__);
$expiresAt = $mtime ? $mtime + EXPIRE_DAYS * 86400 : 0;
if ($mtime && time() > $expiresAt) {
    if (isset($_GET['ping'])) { header('HTTP/1.1 410 Gone'); exit; }
    header('HTTP/1.1 410 Gone');
    header('Content-Type: text/html; charset=utf-8');
    echo '<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1">'
       . '<title>Test expired</title><body style="font:20px/1.5 system-ui,sans-serif;max-width:40em;margin:2em auto;padding:1em">'
       . '<div style="background:#b00020;color:#fff;padding:1em;border-radius:12px;font-size:1.4em;font-weight:bold;text-align:center">'
       . 'This test page has expired and is switched off.</div>'
       . '<p>It turned itself off ' . (int)EXPIRE_DAYS . ' days after it was uploaded (on '
       . h(gmdate('Y-m-d H:i', $mtime)) . ' UTC).</p>'
       . '<p><b>Please delete this file (amp-test.php) and the <code>rangertest</code> folder from the website.</b></p>'
       . '<p>If Jerod needs a new test, upload a fresh copy of the file.</p></body>';
    exit;
}

// ---- 2. Ping mode: tiny response used for timing + clock sync -----
if (isset($_GET['ping'])) {
    header('Content-Type: application/json; charset=utf-8');
    echo '{"t":' . sprintf('%.6F', microtime(true)) . ',"php":"' . PHP_VERSION . '"}';
    exit;
}

// ---- 3. Optional full phpinfo() behind a token --------------------
if (isset($_GET['full'])) {
    $tok = isset($_GET['token']) ? (string)$_GET['token'] : '';
    if (FULL_TOKEN !== '' && $tok !== '' && safe_equals(FULL_TOKEN, $tok)) {
        phpinfo();
        exit;
    }
    header('HTTP/1.1 403 Forbidden');
    header('Content-Type: text/plain; charset=utf-8');
    echo "Full phpinfo() is disabled. (Set FULL_TOKEN at the top of the file and pass &token=...)\n";
    exit;
}

// ===================================================================
//  Helpers
// ===================================================================
$rows = array();      // each: array(section, label, status, detail)
$report = array();    // plain-text lines for the copy box
function row($section, $label, $status, $detail) {
    global $rows;
    $rows[] = array($section, $label, $status, $detail);
}
function to_bytes($v) {
    $v = trim((string)$v);
    if ($v === '' ) return 0;
    if ($v === '-1') return -1;
    $n = (float)$v;
    $u = strtolower(substr($v, -1));
    if ($u === 'g') $n *= 1073741824; elseif ($u === 'm') $n *= 1048576; elseif ($u === 'k') $n *= 1024;
    return (int)$n;
}
function rand_hex($n) {
    if (function_exists('random_bytes')) return bin2hex(random_bytes($n));
    if (function_exists('openssl_random_pseudo_bytes')) return bin2hex(openssl_random_pseudo_bytes($n));
    return substr(md5(uniqid('', true) . mt_rand()), 0, $n * 2);
}
function is_https() {
    if (!empty($_SERVER['HTTPS']) && strtolower($_SERVER['HTTPS']) !== 'off') return true;
    if (isset($_SERVER['SERVER_PORT']) && (int)$_SERVER['SERVER_PORT'] === 443) return true;
    if (!empty($_SERVER['HTTP_X_FORWARDED_PROTO']) && strtolower($_SERVER['HTTP_X_FORWARDED_PROTO']) === 'https') return true;
    if (!empty($_SERVER['REQUEST_SCHEME']) && strtolower($_SERVER['REQUEST_SCHEME']) === 'https') return true;
    return false;
}
// Base URL of this script's folder (host taken from SERVER_NAME when possible, sanitised).
function self_base() {
    $host = !empty($_SERVER['HTTP_HOST']) ? $_SERVER['HTTP_HOST'] : (isset($_SERVER['SERVER_NAME']) ? $_SERVER['SERVER_NAME'] : 'localhost');
    if (!preg_match('/^[A-Za-z0-9.\-\[\]:]+$/', $host)) $host = 'localhost';
    if (!empty($_SERVER['SERVER_NAME']) && preg_match('/^[A-Za-z0-9.\-]+$/', $_SERVER['SERVER_NAME'])) {
        // Only trust HTTP_HOST if its hostname part equals SERVER_NAME (prevents pointing self-requests elsewhere).
        $hn = preg_replace('/:\d+$/', '', $host);
        if (strcasecmp($hn, $_SERVER['SERVER_NAME']) !== 0 && $_SERVER['SERVER_NAME'] !== '0.0.0.0') {
            $port = isset($_SERVER['SERVER_PORT']) ? (int)$_SERVER['SERVER_PORT'] : 80;
            $host = $_SERVER['SERVER_NAME'] . (($port === 80 || $port === 443) ? '' : ':' . $port);
        }
    }
    $dir = str_replace('\\', '/', dirname(isset($_SERVER['SCRIPT_NAME']) ? $_SERVER['SCRIPT_NAME'] : '/amp-test.php'));
    if ($dir === '/' || $dir === '.') $dir = '';
    return (is_https() ? 'https' : 'http') . '://' . $host . $dir;
}
// Minimal HTTP GET: curl if present, else raw socket. Returns array(status, body, ms, error).
function http_get($url, $timeout) {
    $t = microtime(true);
    if (function_exists('curl_init')) {
        $ch = curl_init($url);
        curl_setopt_array($ch, array(
            CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => $timeout, CURLOPT_CONNECTTIMEOUT => $timeout,
            CURLOPT_FOLLOWLOCATION => false, CURLOPT_SSL_VERIFYPEER => false, CURLOPT_SSL_VERIFYHOST => 0,
            CURLOPT_USERAGENT => 'amp-test-selfcheck',
        ));
        $body = curl_exec($ch);
        $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $err = $body === false ? curl_error($ch) : '';
        curl_close($ch);
        return array($code, $body === false ? '' : $body, (microtime(true) - $t) * 1000, $err);
    }
    $p = parse_url($url);
    if (!$p || empty($p['host'])) return array(0, '', 0, 'bad url');
    $https = $p['scheme'] === 'https';
    $port = isset($p['port']) ? $p['port'] : ($https ? 443 : 80);
    $ctx = stream_context_create(array('ssl' => array('verify_peer' => false, 'verify_peer_name' => false)));
    $fp = @stream_socket_client(($https ? 'ssl://' : 'tcp://') . $p['host'] . ':' . $port, $en, $es, $timeout, STREAM_CLIENT_CONNECT, $ctx);
    if (!$fp) return array(0, '', (microtime(true) - $t) * 1000, "socket: $es");
    stream_set_timeout($fp, $timeout);
    $path = (isset($p['path']) ? $p['path'] : '/') . (isset($p['query']) ? '?' . $p['query'] : '');
    $hostHdr = $p['host'] . (isset($p['port']) ? ':' . $p['port'] : '');
    fwrite($fp, "GET $path HTTP/1.0\r\nHost: $hostHdr\r\nUser-Agent: amp-test-selfcheck\r\nConnection: close\r\n\r\n");
    $resp = stream_get_contents($fp);
    fclose($fp);
    $code = 0;
    if (preg_match('#^HTTP/\S+\s+(\d{3})#', (string)$resp, $m)) $code = (int)$m[1];
    $parts = explode("\r\n\r\n", (string)$resp, 2);
    return array($code, isset($parts[1]) ? $parts[1] : '', (microtime(true) - $t) * 1000, $code ? '' : 'no response');
}

// ===================================================================
//  Checks
// ===================================================================

// ---- Sessions first (must happen before any output) ---------------
$sessPath = session_save_path();
$sessDir = $sessPath !== '' ? preg_replace('/^.*;/', '', $sessPath) : sys_get_temp_dir();
$sessOk = false; $sessErr = '';
if (function_exists('session_start')) {
    $sessOk = @session_start();
    if ($sessOk) {
        $_SESSION['amp_test'] = time();
        @session_write_close();
        // clean up: destroy the test session again
        @session_start(); $_SESSION = array(); @session_destroy();
        if (ini_get('session.use_cookies')) {
            $cp = session_get_cookie_params();
            @setcookie(session_name(), '', time() - 3600, $cp['path'], $cp['domain'], $cp['secure'], $cp['httponly']);
        }
    } else {
        $e = error_get_last(); $sessErr = $e ? $e['message'] : 'session_start() returned false';
    }
}

// ---- PHP ----------------------------------------------------------
$S = 'PHP';
if (version_compare(PHP_VERSION, '8.1.0', '>=')) row($S, 'PHP version', 'PASS', PHP_VERSION . ' (8.1+ preferred)');
elseif (version_compare(PHP_VERSION, '8.0.0', '>=')) row($S, 'PHP version', 'WARN', PHP_VERSION . ' works, but 8.1+ preferred (8.0 is end-of-life)');
else row($S, 'PHP version', 'FAIL', PHP_VERSION . ' is too old - need 8.0 or newer (ask host to switch PHP version)');
row($S, 'PHP mode (SAPI)', 'INFO', PHP_SAPI . ' on ' . PHP_OS . (PHP_INT_SIZE === 8 ? ' (64-bit)' : ' (32-bit)'));

$required = array('pdo', 'pdo_mysql', 'mysqli', 'json', 'mbstring', 'openssl', 'session');
$missing = array();
foreach ($required as $ext) {
    if (extension_loaded($ext)) row($S, "Extension: $ext", 'PASS', 'loaded' . (phpversion($ext) ? ' (' . phpversion($ext) . ')' : ''));
    else { row($S, "Extension: $ext", 'FAIL', 'MISSING (required)'); $missing[] = $ext; }
}
foreach (array('curl', 'intl') as $ext) {
    row($S, "Extension: $ext", extension_loaded($ext) ? 'PASS' : 'WARN', extension_loaded($ext) ? 'loaded (optional)' : 'not loaded (optional, nice to have)');
}
$opc = function_exists('opcache_get_status') ? @opcache_get_status(false) : false;
row($S, 'OPcache', ($opc && !empty($opc['opcache_enabled'])) ? 'PASS' : 'WARN', ($opc && !empty($opc['opcache_enabled'])) ? 'enabled (faster)' : 'not enabled or not visible (optional)');

if (function_exists('password_hash') && defined('PASSWORD_DEFAULT')) {
    $hsh = @password_hash('ranger-test', PASSWORD_DEFAULT);
    $ok = $hsh && password_verify('ranger-test', $hsh) && !password_verify('wrong', $hsh);
    row($S, 'password_hash()', $ok ? 'PASS' : 'FAIL', $ok ? 'works (' . substr($hsh, 0, 4) . '...)' : 'present but not working');
} else row($S, 'password_hash()', 'FAIL', 'not available');
row($S, 'Secure random', function_exists('random_bytes') ? 'PASS' : 'WARN', function_exists('random_bytes') ? 'random_bytes() available' : 'random_bytes() missing');

$de = ini_get('display_errors');
row($S, 'display_errors', ($de && strtolower($de) !== 'off' && $de !== '0') ? 'WARN' : 'PASS', ($de && strtolower($de) !== 'off' && $de !== '0') ? 'ON - errors shown to visitors (app will turn it off itself)' : 'off (good)');
$df = trim((string)ini_get('disable_functions'));
row($S, 'disable_functions', 'INFO', $df === '' ? '(none)' : (strlen($df) > 300 ? substr($df, 0, 300) . '...' : $df));
$ob = (string)ini_get('open_basedir');
row($S, 'open_basedir', 'INFO', $ob === '' ? '(not set)' : 'set (restricted paths)');
row($S, 'allow_url_fopen', 'INFO', ini_get('allow_url_fopen') ? 'on' : 'off');

// ---- Web server ---------------------------------------------------
$S = 'Web server';
$sw = isset($_SERVER['SERVER_SOFTWARE']) ? $_SERVER['SERVER_SOFTWARE'] : '';
if (stripos($sw, 'apache') !== false) row($S, 'Server software', 'PASS', $sw);
elseif (stripos($sw, 'litespeed') !== false) row($S, 'Server software', 'PASS', $sw . ' (Apache-compatible, reads .htaccess)');
elseif ($sw === '') row($S, 'Server software', 'WARN', 'not reported by server (unknown)');
else row($S, 'Server software', 'WARN', $sw . ' (not Apache - .htaccess may not work)');

row($S, 'HTTPS', is_https() ? 'PASS' : 'WARN', is_https() ? 'page loaded over HTTPS' : 'page loaded over plain HTTP - try https:// in the address bar; site needs an SSL certificate');

if (function_exists('apache_get_modules')) {
    $mods = apache_get_modules();
    row($S, 'mod_rewrite (module list)', in_array('mod_rewrite', $mods) ? 'PASS' : 'WARN', in_array('mod_rewrite', $mods) ? 'mod_rewrite is loaded' : 'mod_rewrite not in Apache module list');
}

// .htaccess + mod_rewrite live test: temp subfolder with a rewrite rule, fetched via self-request.
$base = self_base();
$rwDir = __DIR__ . '/amp-rw-test-' . rand_hex(4);
$rwStatus = 'WARN'; $rwDetail = 'unknown';
if (@mkdir($rwDir, 0755)) {
    $tokenRw = 'rw-ok-' . rand_hex(6);
    $okW = @file_put_contents($rwDir . '/.htaccess', "RewriteEngine On\nRewriteRule ^probe-me$ probe.txt [L]\n") !== false
        && @file_put_contents($rwDir . '/probe.txt', $tokenRw) !== false;
    if ($okW) {
        $r = http_get($base . '/' . basename($rwDir) . '/probe-me', 5);
        if ($r[0] === 200 && trim($r[1]) === $tokenRw) { $rwStatus = 'PASS'; $rwDetail = '.htaccess is read and mod_rewrite works (pretty URLs OK)'; }
        elseif ($r[0] === 500) { $rwDetail = '.htaccess is read, but RewriteEngine is not allowed/installed (HTTP 500 in test folder)'; }
        elseif ($r[0] === 404) { $rwDetail = '.htaccess appears to be ignored, or mod_rewrite is off (HTTP 404 in test folder)'; }
        elseif ($r[0] === 0) { $rwDetail = 'unknown - server cannot call itself (' . $r[3] . '). Not a problem for the game.'; }
        else { $rwDetail = 'unknown - test returned HTTP ' . $r[0]; }
    } else $rwDetail = 'unknown - could not write test files';
    @unlink($rwDir . '/.htaccess'); @unlink($rwDir . '/probe.txt'); @rmdir($rwDir);
} else $rwDetail = 'unknown - could not create a test subfolder';
row($S, '.htaccess + mod_rewrite', $rwStatus, $rwDetail);

// ---- Files & folders ----------------------------------------------
$S = 'Files';
$tmp = sys_get_temp_dir();
$tf = @tempnam($tmp, 'amp');
$tmpOk = $tf && @file_put_contents($tf, 'x') === 1 && @unlink($tf);
row($S, 'Temp folder writable', $tmpOk ? 'PASS' : 'FAIL', ($tmpOk ? 'yes: ' : 'NO: ') . $tmp);
if ($sessOk) row($S, 'Sessions work', 'PASS', 'session_start() OK (save path ' . ($sessPath !== '' ? 'set' : 'default') . ', ' . (@is_writable($sessDir) ? 'writable' : 'not checkable') . ')');
else row($S, 'Sessions work', 'FAIL', 'session_start() failed: ' . $sessErr);

$wf = __DIR__ . '/amp-write-check-' . rand_hex(4) . '.tmp';
$w1 = @file_put_contents($wf, 'hello ranger');
$w2 = $w1 !== false && @file_get_contents($wf) === 'hello ranger';
$w3 = $w1 !== false && @unlink($wf);
if ($w2 && $w3) row($S, 'Create + delete file here', 'PASS', 'script can write and delete files in its own folder');
elseif ($w1 === false) row($S, 'Create + delete file here', 'WARN', 'cannot write in its own folder (OK if the app stores everything in MySQL)');
else row($S, 'Create + delete file here', 'WARN', 'wrote a file but could not read/delete it - please delete any amp-write-check-*.tmp');
$free = @disk_free_space(__DIR__);
row($S, 'Free disk space', 'INFO', $free ? round($free / 1073741824, 1) . ' GB (as reported; shared hosts may show the whole disk)' : 'not reported');
$owner = function_exists('posix_geteuid') && function_exists('posix_getpwuid') ? @posix_getpwuid(posix_geteuid()) : null;
row($S, 'PHP runs as user', 'INFO', $owner && isset($owner['name']) ? $owner['name'] : (function_exists('get_current_user') ? get_current_user() . ' (file owner)' : 'unknown'));

// ---- Limits -------------------------------------------------------
$S = 'Limits';
$ml = ini_get('memory_limit'); $mlb = to_bytes($ml);
row($S, 'memory_limit', ($mlb === -1 || $mlb >= 128 * 1048576) ? 'PASS' : ($mlb >= 64 * 1048576 ? 'WARN' : 'FAIL'), $ml . ' (want 128M+)');
$met = (int)ini_get('max_execution_time');
row($S, 'max_execution_time', ($met === 0 || $met >= 30) ? 'PASS' : 'WARN', ($met === 0 ? '0 (unlimited)' : $met . ' s') . ' (want 30+)');
$pm = ini_get('post_max_size'); $pmb = to_bytes($pm);
row($S, 'post_max_size', ($pmb <= 0 || $pmb >= 8 * 1048576) ? 'PASS' : 'WARN', $pm . ' (want 8M+)');
$um = ini_get('upload_max_filesize'); $umb = to_bytes($um);
row($S, 'upload_max_filesize', ($umb >= 8 * 1048576) ? 'PASS' : 'WARN', $um . ' (want 8M+)' . (ini_get('file_uploads') ? '' : ' - file uploads are OFF'));
$miv = (int)ini_get('max_input_vars');
row($S, 'max_input_vars', ($miv === 0 || $miv >= 1000) ? 'PASS' : 'WARN', ($miv ?: 'default') . ' (want 1000+)');
row($S, 'session.gc_maxlifetime', 'INFO', (int)ini_get('session.gc_maxlifetime') . ' s');

// ---- Clock --------------------------------------------------------
$S = 'Clock';
$tzIni = (string)ini_get('date.timezone');
$tz = date_default_timezone_get();
row($S, 'Server time', 'INFO', date('Y-m-d H:i:s T') . ' / UTC ' . gmdate('Y-m-d H:i:s'));
row($S, 'PHP timezone', $tzIni === '' ? 'WARN' : 'PASS', $tz . ($tzIni === '' ? ' (date.timezone not set in php.ini; app will set its own)' : ''));
$mt = microtime(true);
row($S, 'microtime(true)', 'INFO', sprintf('%.6F', $mt) . '  (unix seconds; compare with your phone clock)');

// ---- Speed (server -> itself) --------------------------------------
$S = 'Speed';
$times = array(); $selfErr = '';
for ($i = 0; $i < SELF_REQUESTS; $i++) {
    $r = http_get($base . '/' . basename(__FILE__) . '?ping=1&n=' . $i, 4);
    if ($r[0] !== 200 || strpos($r[1], '"t":') === false) { $selfErr = $r[0] ? 'HTTP ' . $r[0] : $r[3]; break; }
    $times[] = $r[2];
}
if (count($times) === SELF_REQUESTS) {
    sort($times);
    $avg = array_sum($times) / count($times);
    $st = $avg < 300 ? 'PASS' : ($avg < 1000 ? 'WARN' : 'FAIL');
    row($S, SELF_REQUESTS . ' self-requests', $st, sprintf('avg %.0f ms, min %.0f ms, max %.0f ms (via %s)', $avg, $times[0], end($times), function_exists('curl_init') ? 'curl' : 'socket'));
} else {
    row($S, SELF_REQUESTS . ' self-requests', 'INFO', 'skipped - server cannot call itself (' . ($selfErr ?: 'unknown') . '). The browser test below still works.');
}
$loopT = microtime(true); $x = 0; for ($i = 0; $i < 1000000; $i++) { $x += $i % 7; } $loopMs = (microtime(true) - $loopT) * 1000;
row($S, 'CPU loop (1M iterations)', $loopMs < 200 ? 'PASS' : 'WARN', sprintf('%.0f ms', $loopMs));

// ---- MySQL (only when the form is submitted) ----------------------
$mysqlRan = false;
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['mysql_test'])) {
    $mysqlRan = true;
    $S = 'MySQL';
    $dbHost = trim(isset($_POST['db_host']) ? (string)$_POST['db_host'] : '');
    $dbPort = (int)(isset($_POST['db_port']) ? $_POST['db_port'] : 0);
    $dbName = trim(isset($_POST['db_name']) ? (string)$_POST['db_name'] : '');
    $dbUser = trim(isset($_POST['db_user']) ? (string)$_POST['db_user'] : '');
    $dbPass = isset($_POST['db_pass']) ? (string)$_POST['db_pass'] : '';
    if ($dbHost === '') $dbHost = 'localhost';
    if ($dbPort <= 0 || $dbPort > 65535) $dbPort = 3306;
    $secrets = array_filter(array($dbUser, $dbName, $dbHost), function ($v) { return strlen($v) >= 3; });
    if ($dbPass !== '') $secrets[] = $dbPass;
    usort($secrets, function ($a, $b) { return strlen($b) - strlen($a); });
    $clean = function ($msg) use ($secrets) {
        foreach ($secrets as $s) $msg = str_replace($s, '[hidden]', $msg);
        return $msg;
    };
    if (!extension_loaded('pdo_mysql')) {
        row($S, 'Connect (PDO)', 'FAIL', 'pdo_mysql extension missing');
    } else {
        try {
            $dsn = 'mysql:host=' . $dbHost . ';port=' . $dbPort . ($dbName !== '' ? ';dbname=' . $dbName : '') . ';charset=utf8mb4';
            $t = microtime(true);
            $pdo = new PDO($dsn, $dbUser, $dbPass, array(PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_TIMEOUT => 5, PDO::ATTR_EMULATE_PREPARES => false));
            row($S, 'Connect (PDO)', 'PASS', sprintf('connected in %.0f ms (utf8mb4)', (microtime(true) - $t) * 1000));
            $ver = $pdo->query('SELECT VERSION()')->fetchColumn();
            $isMaria = stripos($ver, 'mariadb') !== false;
            $vnum = preg_replace('/[^0-9.].*$/', '', $ver);
            $vok = $isMaria ? version_compare($vnum, '10.3', '>=') : version_compare($vnum, '5.7', '>=');
            row($S, 'Server version', $vok ? 'PASS' : 'WARN', ($isMaria ? 'MariaDB ' : 'MySQL ') . $ver . ($vok ? '' : ' (old - MySQL 5.7+/8 or MariaDB 10.3+ preferred)'));
            if ($dbName === '') row($S, 'Database selected', 'WARN', 'no database name given - some tests skipped');

            $eng = $pdo->query("SELECT SUPPORT FROM information_schema.ENGINES WHERE ENGINE='InnoDB'")->fetchColumn();
            row($S, 'InnoDB engine', ($eng === 'YES' || $eng === 'DEFAULT') ? 'PASS' : 'FAIL', 'support: ' . ($eng ?: 'not listed'));

            if ($dbName !== '') {
                try {
                    $pdo->exec('CREATE TEMPORARY TABLE amp_test_tmp (id INT AUTO_INCREMENT PRIMARY KEY, v VARCHAR(64) NOT NULL, t DATETIME(3) NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4');
                    row($S, 'CREATE TEMPORARY TABLE', 'PASS', 'OK (InnoDB, utf8mb4, DATETIME(3))');
                    $st = $pdo->prepare('INSERT INTO amp_test_tmp (v, t) VALUES (?, NOW(3))');
                    $st->execute(array('Ranger ñ 🌵'));
                    $got = $pdo->query('SELECT v FROM amp_test_tmp WHERE id=' . (int)$pdo->lastInsertId())->fetchColumn();
                    row($S, 'INSERT + SELECT (utf8mb4)', $got === 'Ranger ñ 🌵' ? 'PASS' : 'WARN', $got === 'Ranger ñ 🌵' ? 'round-trip OK incl. emoji' : 'text came back changed (charset issue)');

                    $pdo->beginTransaction(); $pdo->exec("INSERT INTO amp_test_tmp (v) VALUES ('rollback-me')"); $pdo->rollBack();
                    $c1 = (int)$pdo->query("SELECT COUNT(*) FROM amp_test_tmp WHERE v='rollback-me'")->fetchColumn();
                    $pdo->beginTransaction(); $pdo->exec("INSERT INTO amp_test_tmp (v) VALUES ('commit-me')"); $pdo->commit();
                    $c2 = (int)$pdo->query("SELECT COUNT(*) FROM amp_test_tmp WHERE v='commit-me'")->fetchColumn();
                    row($S, 'Transactions', ($c1 === 0 && $c2 === 1) ? 'PASS' : 'FAIL', ($c1 === 0 && $c2 === 1) ? 'rollback and commit both behave correctly' : "rollback left $c1 row(s), commit gave $c2");

                    try { $pdo->beginTransaction(); $pdo->query('SELECT id FROM amp_test_tmp LIMIT 1 FOR UPDATE')->fetchAll(); $pdo->commit();
                          row($S, 'SELECT ... FOR UPDATE', 'PASS', 'row locking OK'); }
                    catch (Exception $e) { if ($pdo->inTransaction()) $pdo->rollBack(); row($S, 'SELECT ... FOR UPDATE', 'WARN', $clean($e->getMessage())); }
                    $pdo->exec('DROP TEMPORARY TABLE amp_test_tmp');
                } catch (Exception $e) {
                    if ($pdo->inTransaction()) $pdo->rollBack();
                    row($S, 'Temporary table tests', 'FAIL', $clean($e->getMessage()));
                }
                // Real table create/drop (the app needs CREATE/ALTER/DROP for its own tables)
                $rt = 'amp_test_' . rand_hex(3);
                try {
                    $pdo->exec("CREATE TABLE `$rt` (id INT PRIMARY KEY) ENGINE=InnoDB");
                    $pdo->exec("ALTER TABLE `$rt` ADD COLUMN n INT NULL");
                    $pdo->exec("DROP TABLE `$rt`");
                    row($S, 'CREATE / ALTER / DROP TABLE', 'PASS', 'user can manage its own tables');
                } catch (Exception $e) {
                    try { $pdo->exec("DROP TABLE IF EXISTS `$rt`"); } catch (Exception $e2) {}
                    row($S, 'CREATE / ALTER / DROP TABLE', 'FAIL', $clean($e->getMessage()));
                }
            }
            $vars = $pdo->query("SELECT @@sql_mode, @@max_connections, @@time_zone, @@system_time_zone, NOW(3), UTC_TIMESTAMP(3)")->fetch(PDO::FETCH_NUM);
            row($S, 'max_connections', ((int)$vars[1] >= 50) ? 'PASS' : 'WARN', (int)$vars[1]);
            row($S, 'sql_mode', 'INFO', $vars[0] === '' ? '(empty)' : $vars[0]);
            row($S, 'MySQL clock', 'INFO', 'NOW ' . $vars[4] . ' / UTC ' . $vars[5] . ' (tz ' . $vars[2] . ', system ' . $vars[3] . ')');
            $skew = abs(strtotime($vars[5] . ' UTC') - time());
            row($S, 'MySQL vs PHP clock', $skew <= 2 ? 'PASS' : 'WARN', $skew . ' s difference (UTC)');
            $pdo = null;
        } catch (Exception $e) {
            row($S, 'Connect (PDO)', 'FAIL', $clean($e->getMessage()));
        }
    }
    if (extension_loaded('mysqli')) {
        if (function_exists('mysqli_report')) mysqli_report(MYSQLI_REPORT_OFF);
        $mi = @mysqli_init();
        if ($mi) {
            @mysqli_options($mi, MYSQLI_OPT_CONNECT_TIMEOUT, 5);
            $ok = false;
            try { $ok = @mysqli_real_connect($mi, $dbHost, $dbUser, $dbPass, $dbName !== '' ? $dbName : null, $dbPort); } catch (Exception $e) { $ok = false; }
            row($S, 'Connect (mysqli)', $ok ? 'PASS' : 'WARN', $ok ? 'OK' : 'failed: ' . $clean((string)mysqli_connect_error()));
            if ($ok) @mysqli_close($mi);
        }
    }
    unset($dbPass, $_POST['db_pass'], $dbUser, $dbHost, $dbName, $secrets);
}

// ===================================================================
//  Build report text
// ===================================================================
$counts = array('PASS' => 0, 'WARN' => 0, 'FAIL' => 0, 'INFO' => 0);
foreach ($rows as $r) $counts[$r[2]]++;
$overall = $counts['FAIL'] ? 'FAIL' : ($counts['WARN'] ? 'WARN' : 'PASS');
$lines = array();
$lines[] = 'DESERT RANGER - AMP HOST TEST REPORT  (amp-test.php v' . $VERSION . ')';
$lines[] = 'Generated: ' . gmdate('Y-m-d H:i:s') . ' UTC   Host: ' . preg_replace('/[^A-Za-z0-9.\-:]/', '', isset($_SERVER['HTTP_HOST']) ? $_SERVER['HTTP_HOST'] : '?');
$lines[] = 'Summary: ' . $counts['PASS'] . ' pass, ' . $counts['WARN'] . ' warn, ' . $counts['FAIL'] . ' fail  => ' . $overall;
$lines[] = 'MySQL test: ' . ($mysqlRan ? 'run (credentials NOT included)' : 'not run');
$cur = '';
foreach ($rows as $r) {
    if ($r[0] !== $cur) { $cur = $r[0]; $lines[] = ''; $lines[] = '[' . strtoupper($cur) . ']'; }
    $lines[] = str_pad($r[2], 5) . ' ' . str_pad($r[1], 28) . ' ' . $r[3];
}
$lines[] = '';
$lines[] = 'Page built in ' . sprintf('%.0f', (microtime(true) - $T0) * 1000) . ' ms. Expires ' . gmdate('Y-m-d H:i', $expiresAt) . ' UTC.';
$reportText = implode("\n", $lines);

$daysLeft = $expiresAt ? max(0, ceil(($expiresAt - time()) / 86400)) : '?';
header('Content-Type: text/html; charset=utf-8');
?><!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Desert Ranger - Host Test</title>
<style>
*{box-sizing:border-box}
body{margin:0;font:18px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;background:#f6f1e7;color:#222}
.wrap{max-width:960px;margin:0 auto;padding:12px}
.danger{background:#c00;color:#fff;text-align:center;font-weight:800;font-size:1.5em;padding:14px 10px;letter-spacing:.5px;border-bottom:6px solid #800}
.danger small{display:block;font-size:.55em;font-weight:600;letter-spacing:0}
h1{font-size:1.7em;margin:.6em 0 .2em}
h2{font-size:1.3em;margin:1.4em 0 .4em;border-bottom:3px solid #c9a96e;padding-bottom:4px}
.summary{display:flex;flex-wrap:wrap;gap:10px;margin:10px 0}
.pill{flex:1 1 140px;border-radius:14px;padding:14px;text-align:center;font-size:1.4em;font-weight:800;color:#fff}
.pill span{display:block;font-size:.55em;font-weight:600}
.big{font-size:1.4em;font-weight:800;padding:16px;border-radius:14px;text-align:center;margin:10px 0;color:#fff}
.PASS{background:#1b8a3a}.FAIL{background:#c62828}.WARN{background:#f2b705;color:#222!important}.INFO{background:#5b6b7a}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.12)}
td{padding:10px 12px;border-bottom:1px solid #eee;vertical-align:top}
td.s{width:92px}
.badge{display:inline-block;min-width:72px;text-align:center;padding:5px 8px;border-radius:8px;color:#fff;font-weight:800;font-size:.95em}
td.l{font-weight:700;width:34%}
td.d{word-break:break-word}
form{background:#fff;border-radius:12px;padding:14px;box-shadow:0 1px 3px rgba(0,0,0,.12)}
label{display:block;font-weight:700;margin-top:10px}
input[type=text],input[type=password],input[type=number]{width:100%;font-size:1.05em;padding:10px;border:2px solid #bbb;border-radius:8px}
button{font-size:1.15em;font-weight:800;padding:14px 20px;border:0;border-radius:10px;background:#2d5b8a;color:#fff;margin-top:14px;cursor:pointer;width:100%}
.note{background:#fff8d6;border-left:6px solid #f2b705;padding:10px 12px;border-radius:8px;margin:10px 0}
pre{background:#111;color:#e8e8e8;padding:14px;border-radius:12px;overflow:auto;font-size:13px;line-height:1.35;white-space:pre-wrap;word-break:break-word}
.muted{color:#666;font-size:.9em}
@media (max-width:600px){body{font-size:17px}td.l{width:auto}td{display:block;border:0;padding:4px 10px}tr{display:block;border-bottom:1px solid #ddd;padding:6px 0}td.s{width:auto}}
</style>
</head>
<body>
<div class="danger">&#9888; DELETE THIS FILE WHEN DONE &#9888;
<small>This is a temporary test page. When you have sent the results to Jerod, delete amp-test.php and the rangertest folder. (It switches itself off in <?php echo h($daysLeft); ?> day(s).)</small></div>
<div class="wrap">
<h1>Desert Ranger &ndash; Web Host Test</h1>
<div class="big <?php echo $overall; ?>"><?php
  echo $overall === 'PASS' ? '&#10004; Everything passed!' : ($overall === 'WARN' ? '&#9888; Mostly OK &ndash; a few warnings' : '&#10008; Some checks FAILED');
?></div>
<div class="summary">
  <div class="pill PASS"><?php echo $counts['PASS']; ?><span>PASS</span></div>
  <div class="pill WARN"><?php echo $counts['WARN']; ?><span>WARN</span></div>
  <div class="pill FAIL"><?php echo $counts['FAIL']; ?><span>FAIL</span></div>
</div>
<p class="note"><b>What to do:</b> scroll to the bottom, press <b>&ldquo;Copy this report&rdquo;</b>, and paste it in a text or email to Jerod. Or take screenshots of the whole page. Don&rsquo;t worry about yellow or red rows &ndash; Jerod will read them.</p>

<?php
$cur = '';
foreach ($rows as $r) {
    if ($r[0] !== $cur) {
        if ($cur !== '') echo "</table>\n";
        $cur = $r[0];
        echo '<h2>' . h($cur) . "</h2>\n<table>\n";
    }
    echo '<tr><td class="s"><span class="badge ' . h($r[2]) . '">' . h($r[2]) . '</span></td><td class="l">' . h($r[1]) . '</td><td class="d">' . h($r[3]) . "</td></tr>\n";
}
if ($cur !== '') echo "</table>\n";
?>

<h2>Browser &rarr; server speed &amp; clock (polling test)</h2>
<table id="bt"><tr><td class="s"><span class="badge INFO" id="btBadge">...</span></td><td class="l">10 polls from this device</td><td class="d" id="btDetail">running&hellip; (needs JavaScript)</td></tr>
<tr><td class="s"><span class="badge INFO">INFO</span></td><td class="l">Device vs server clock</td><td class="d" id="ckDetail">running&hellip;</td></tr></table>

<h2>MySQL database test <span class="muted">(only if Jerod asks)</span></h2>
<div class="note"><b>Jeffery:</b> leave this empty unless Jerod is on the phone with you and asks you to fill it in. Nothing typed here is saved or shown.</div>
<form method="post" action="<?php echo h(basename(__FILE__)); ?>" autocomplete="off">
  <input type="hidden" name="mysql_test" value="1">
  <label for="db_host">Database host <span class="muted">(often &ldquo;localhost&rdquo;)</span></label>
  <input type="text" id="db_host" name="db_host" placeholder="localhost" autocomplete="off" autocapitalize="off" spellcheck="false">
  <label for="db_port">Port <span class="muted">(leave empty for 3306)</span></label>
  <input type="number" id="db_port" name="db_port" placeholder="3306" min="1" max="65535">
  <label for="db_name">Database name</label>
  <input type="text" id="db_name" name="db_name" autocomplete="off" autocapitalize="off" spellcheck="false">
  <label for="db_user">Database user</label>
  <input type="text" id="db_user" name="db_user" autocomplete="off" autocapitalize="off" spellcheck="false">
  <label for="db_pass">Database password</label>
  <input type="password" id="db_pass" name="db_pass" autocomplete="new-password">
  <button type="submit">Test the database</button>
  <p class="muted">Runs: connect, version, CREATE TEMPORARY TABLE, insert/select (with emoji), InnoDB transactions (rollback + commit), row lock, create/alter/drop a scratch table, clock compare. Credentials are used once and never stored or shown.</p>
</form>

<h2>Copy this report</h2>
<p>Press the button, then paste into a text message or email to Jerod. No passwords are included.</p>
<button type="button" id="copyBtn">&#128203; Copy this report</button>
<pre id="report"><?php echo h($reportText); ?></pre>
<p class="muted">Test kit v<?php echo h($VERSION); ?>. Full phpinfo() is <?php echo FULL_TOKEN === '' ? 'disabled' : 'available with the secret token'; ?>.</p>
</div>
<script>
(function(){
  var url = <?php echo json_encode(basename(__FILE__)); ?> + '?ping=1';
  var pre = document.getElementById('report');
  var n = 10, i = 0, rtts = [], offs = [];
  function done(){
    var b = document.getElementById('btBadge'), d = document.getElementById('btDetail'), c = document.getElementById('ckDetail');
    if (!rtts.length){ b.textContent='WARN'; b.className='badge WARN'; d.textContent='could not reach the server from the browser'; return; }
    var s = rtts.slice().sort(function(a,b){return a-b;});
    var avg = s.reduce(function(a,b){return a+b;},0)/s.length;
    var best = 0; for (var k=1;k<rtts.length;k++) if (rtts[k]<rtts[best]) best=k;
    var off = offs[best];
    var st = avg < 400 ? 'PASS' : (avg < 1200 ? 'WARN' : 'FAIL');
    b.textContent = st; b.className = 'badge ' + st;
    d.textContent = 'avg ' + avg.toFixed(0) + ' ms, min ' + s[0].toFixed(0) + ' ms, max ' + s[s.length-1].toFixed(0) + ' ms (' + rtts.length + '/' + n + ' OK)';
    c.textContent = 'device is ' + Math.abs(off).toFixed(0) + ' ms ' + (off >= 0 ? 'ahead of' : 'behind') + ' the server (best of ' + rtts.length + ' samples)';
    pre.textContent += '\n\n[BROWSER POLLING]\n' + st + '  10 polls from device          ' + d.textContent + '\nINFO  Device vs server clock       ' + c.textContent + '\nUser agent: ' + navigator.userAgent;
  }
  function next(){
    if (i >= n) return done();
    i++;
    var t0 = Date.now(), p0 = (window.performance && performance.now) ? performance.now() : t0;
    var x = new XMLHttpRequest();
    x.open('GET', url + '&b=' + i + '&r=' + Math.random(), true);
    x.timeout = 5000;
    x.onload = function(){
      var p1 = (window.performance && performance.now) ? performance.now() : Date.now();
      var rtt = p1 - p0;
      try { var j = JSON.parse(x.responseText); rtts.push(rtt); offs.push((t0 + rtt/2) - j.t*1000); } catch(e){}
      next();
    };
    x.onerror = x.ontimeout = function(){ next(); };
    x.send();
  }
  next();
  document.getElementById('copyBtn').onclick = function(){
    var txt = pre.textContent, btn = this;
    function ok(){ btn.textContent = '\u2714 Copied! Now paste it to Jerod'; }
    function fallback(){
      var r = document.createRange(); r.selectNodeContents(pre);
      var sel = window.getSelection(); sel.removeAllRanges(); sel.addRange(r);
      try { document.execCommand('copy'); ok(); } catch(e){ btn.textContent = 'Text selected - press Copy'; }
    }
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(txt).then(ok, fallback); else fallback();
  };
})();
</script>
</body>
</html>
