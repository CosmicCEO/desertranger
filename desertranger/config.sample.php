<?php
/**
 * Desert Ranger configuration.
 *
 * Copy this file to config.php and fill in your database details.
 * config.php is NOT in git (it holds the password).
 *
 * Network Solutions: Database Manager shows the host name, database name,
 * user and password after you create the database.
 *
 * MAMP on a Mac (default ports 8888/8889, user root / password root):
 *     'db_host' => '127.0.0.1',  'db_port' => 8889,
 *     'db_user' => 'root',       'db_pass' => 'root',
 *   or, instead of host/port, the socket:
 *     'db_socket' => '/Applications/MAMP/tmp/mysql/mysql.sock',
 *   Use 127.0.0.1, not "localhost", with a port: PHP turns "localhost" into
 *   "use the default socket" and ignores the port.
 */
return array(
    // --- MySQL / MariaDB ---
    'db_host'   => 'localhost',   // NetSol often uses a host like "xxxxx.mysql.netsol.com"; MAMP: '127.0.0.1'
    'db_port'   => 3306,          // MAMP: 8889
    'db_socket' => '',            // Optional Unix socket path; when set, host and port are ignored
    'db_name'   => 'desertranger',
    'db_user'   => 'desertranger',
    'db_pass'   => 'change-me',

    // --- Game tuning ---
    // How far in the future synced sounds are scheduled (ms). Must be longer
    // than the poll interval + network time, so every device hears about the
    // cue before it is due. 1500 ms with 1 s polling is the plan default.
    'cue_lead_ms' => 1500,

    // Show PHP error details in API responses. Keep false on the live site.
    'debug' => false,
);
