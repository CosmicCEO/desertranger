<?php
/**
 * Desert Ranger configuration.
 *
 * Copy this file to config.php and fill in your database details.
 * config.php is NOT in git (it holds the password).
 * On Network Solutions: Database Manager shows the host name, database name,
 * user and password after you create the database.
 */
return array(
    // --- MySQL / MariaDB ---
    'db_host' => 'localhost',     // NetSol often uses a host like "xxxxx.mysql.netsol.com"
    'db_port' => 3306,
    'db_name' => 'desertranger',
    'db_user' => 'desertranger',
    'db_pass' => 'change-me',

    // --- Game tuning ---
    // How far in the future synced sounds are scheduled (ms). Must be longer
    // than the poll interval + network time, so every device hears about the
    // cue before it is due. 1500 ms with 1 s polling is the plan default.
    'cue_lead_ms' => 1500,

    // Show PHP error details in API responses. Keep false on the live site.
    'debug' => false,
);
