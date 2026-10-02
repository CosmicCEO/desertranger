<?php
/**
 * One-time installer: creates the database tables.
 *
 *   1. Create the database + user (Network Solutions: Database Manager).
 *   2. Copy config.sample.php to config.php and fill in the details.
 *   3. Open https://your-site/desertranger/install.php once.
 *
 * It REFUSES to run again once the tables exist, so it can't wipe a live game.
 * (You may delete this file after installing.)
 */
header('Content-Type: text/html; charset=utf-8');
$checks = array();
$ok = true;

function row($label, $good, $detail = '')
{
    global $checks, $ok;
    $checks[] = array($label, $good, $detail);
    if (!$good) {
        $ok = false;
    }
}

row('PHP version ' . PHP_VERSION . ' (need 7.4+)', version_compare(PHP_VERSION, '7.4.0', '>='));
row('PDO MySQL driver', extension_loaded('pdo_mysql'));
row('JSON extension', function_exists('json_encode'));
row('mbstring (optional, nicer name trimming)', true, extension_loaded('mbstring') ? 'present' : 'missing - OK');
row('config.php present', is_file(__DIR__ . '/config.php'), 'copy config.sample.php to config.php');

$message = '';
if ($ok) {
    require __DIR__ . '/lib/db.php';
    try {
        $db = dr_db();
        $ver = $db->query('SELECT VERSION()')->fetchColumn();
        row('Database connection', true, 'server ' . htmlspecialchars($ver));
        $exists = $db->query("SHOW TABLES LIKE 'games'")->fetchColumn();
        if ($exists) {
            $message = 'Already installed: the tables exist. Refusing to run again. (Delete this file if you like.)';
            $ok = false;
        } else {
            $sql = file_get_contents(__DIR__ . '/lib/schema.sql');
            // Strip "--" comment lines, then split on lines that contain only ";".
            $sql = preg_replace('/^\s*--.*$/m', '', $sql);
            foreach (preg_split('/^\s*;\s*$/m', $sql) as $stmt) {
                if (trim($stmt) !== '') {
                    $db->exec($stmt);
                }
            }
            $message = 'Installed! Tables created. Open the game: <a href="./">Desert Ranger</a>';
        }
    } catch (Exception $e) {
        row('Database connection', false, htmlspecialchars($e->getMessage()));
        $message = 'Fix config.php and reload this page.';
    }
} else {
    $message = 'Fix the items marked ✗ and reload.';
}
?>
<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Desert Ranger installer</title>
<style>body{font-family:system-ui,sans-serif;background:#F4ECD8;color:#3A2A1E;max-width:640px;margin:2rem auto;padding:0 1rem}
td{padding:.3rem .6rem;border-bottom:1px solid #E8D7B4}.g{color:#5c7a3e}.b{color:#C3623B;font-weight:bold}
.msg{margin-top:1.5rem;padding:1rem;background:#fffaf0;border:2px solid #E9A23B;border-radius:12px}</style></head>
<body><h1>Desert Ranger installer</h1>
<table><?php foreach ($checks as $c): ?>
<tr><td class="<?php echo $c[1] ? 'g' : 'b'; ?>"><?php echo $c[1] ? '✓' : '✗'; ?></td>
<td><?php echo $c[0]; ?></td><td><?php echo $c[2]; ?></td></tr>
<?php endforeach; ?></table>
<div class="msg"><?php echo $message; ?></div>
</body></html>
