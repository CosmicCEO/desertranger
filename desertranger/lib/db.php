<?php
/**
 * Config + database connection helpers. Plain PDO, no framework.
 */

/** Load config.php once. Dies with a clear message if it is missing. */
function dr_config()
{
    static $cfg = null;
    if ($cfg === null) {
        $file = __DIR__ . '/../config.php';
        if (!is_file($file)) {
            throw new RuntimeException('config.php is missing. Copy config.sample.php to config.php and edit it.');
        }
        $cfg = require $file;
        $cfg += array('db_port' => 3306, 'db_socket' => '', 'cue_lead_ms' => 1500, 'debug' => false);
    }
    return $cfg;
}

/** Shared PDO connection (one per request). */
function dr_db()
{
    static $pdo = null;
    if ($pdo === null) {
        $c = dr_config();
        if (!empty($c['db_socket'])) {
            // Unix socket (e.g. MAMP: /Applications/MAMP/tmp/mysql/mysql.sock).
            // When a socket is given, host and port are ignored.
            $dsn = 'mysql:unix_socket=' . $c['db_socket'];
        } else {
            // TCP. Use 127.0.0.1 rather than "localhost" when you need a
            // non-standard port: PHP treats "localhost" as "use the default
            // socket" and silently ignores the port.
            $dsn = 'mysql:host=' . $c['db_host'] . ';port=' . (int)$c['db_port'];
        }
        $dsn .= ';dbname=' . $c['db_name'] . ';charset=utf8mb4';
        $pdo = new PDO($dsn, $c['db_user'], $c['db_pass'], array(
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES   => false,
        ));
        // Store DATETIMEs in UTC regardless of the host's time zone.
        $pdo->exec("SET time_zone = '+00:00'");
    }
    return $pdo;
}

/** Server clock in integer milliseconds since the Unix epoch (used for clock sync + cues). */
function dr_now_ms()
{
    return (int)round(microtime(true) * 1000);
}

/** UTC timestamp string for DATETIME columns. */
function dr_now_sql()
{
    return gmdate('Y-m-d H:i:s');
}
