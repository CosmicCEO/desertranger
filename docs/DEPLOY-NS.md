# Deploy to the client's Network Solutions host: runbook

Extends the short "Deploy to Network Solutions" section of `docs/PROTOTYPE.md` with this account's facts, a clean upload folder, and a checker. The person at the keyboard types every credential; nobody pastes them into chat, a ticket or the repo.

## What we know about the host (from the account panel, Oct 3, 2026)
- Debian, **PHP 7.4.10**, **MySQL 5.7.44**, CGI active, **SFTP on a non-standard port (2222)**.
- A **shared account**: the folders under `htdocs` are other websites. The game goes in **its own new folder, `htdocs/desertranger/`**, and nothing else is touched. The top-level `.htaccess` only says `DirectoryIndex index.html index.php`, so it does not interfere.
- This is the stack already tested: PHP 7.4 + MySQL 5.7.44 in Docker, and PHP 7.4.33 on the lab Mac (syntax of every PHP file, `rules_test.php` 45/45).
- **There is a cache in front of the site** (seen on a test file: `Cache-Control: max-age=14400`, an `Age` header, and a `request_id` cookie added by the host). `api.php` sends `no-store`, and the game's `.htaccess` asks for HTML and JSON to be re-checked every time; `dev/verify-deploy.sh` tests both.
- **On this host a PHP file that does not exist answers 500, not 404** (checked before anything was uploaded; missing `.txt`, `.html`, `.sql` answer 404). So a 500 on `api.php` before the upload is normal. After the upload, read it like this: if `index.html` loads but `api.php` gives 500, PHP or `config.php` is the problem; if static files give 500 too, suspect `.htaccess`.
- HTTPS is already on for the site's address (the `hello.txt` test worked over https).
- Unknown until we try: the final domain and HTTPS, the database host name, `.htaccess` limits, and MySQL connection limits.
(Keep hostnames, account paths and logins in your password manager, not here.)

## Tools
Cyberduck (installed on the lab Mac). Open Connection: protocol **SFTP**, port **2222**, your host and login; tick "Add to Keychain". Show hidden files with Cmd+Shift+. so `.htaccess` is visible.

## Steps
1. **Create the folder.** In `htdocs`, create `desertranger` (only if it does not exist yet). If it already exists, stop and pick another name.
2. **Learn the address (tiny test).** `echo ok > ~/Desktop/hello.txt`, drag it into `htdocs/desertranger/`, open `http://YOURDOMAIN/desertranger/hello.txt`. "ok" means that is the game's address. Delete `hello.txt`.
3. **Create the database** in the account's Database Manager: a **new** MySQL database and a **new** user with rights on that database only. Do not reuse another site's user. Note the **host name** (usually not `localhost`), database, user and password.
4. **Build the upload folder** on the lab Mac clone (on `main`, with the binary assets present):
   `bash dev/make-deploy-folder.sh` → `deploy/desertranger/` (about 267 files, 6 MB) and `deploy/DEPLOY-MANIFEST.txt`. It never copies `config.php`, tests or markdown, and it checks PHP syntax.
5. **Create `config.php` locally**, inside `deploy/desertranger/` only: copy `config.sample.php` to `config.php`, fill the host, port (3306), database, user and password, leave `db_socket` empty and `'debug' => false`. It is never committed.
6. **Upload.** In Cyberduck, drag the **`desertranger` folder itself** (from `deploy/`) onto `htdocs`: it merges into the existing `desertranger` folder and, unlike dragging the folder's contents, it takes the hidden `.htaccess` along (Finder hides dotfiles, so "select all" skips them). When Cyberduck asks about existing files choose **Skip**. Then check the server's `desertranger` folder shows `.htaccess` (Cyberduck: View, Show Hidden Files) and that the file count matches the manifest (plus `config.php`). If `.htaccess` is missing, `verify-deploy.sh` will warn that `config.sample.php` and the `.sql` file are readable.
7. **Install.** Open `http://YOURDOMAIN/desertranger/install.php` once: it checks PHP, the driver and the database, then creates the tables (it refuses a second run). Then **delete `install.php` from the server**.
8. **HTTPS.** Turn on the free SSL certificate for the domain in the control panel, if it is not already on.
9. **Check it.** `bash dev/verify-deploy.sh https://YOURDOMAIN/desertranger` reads pages only (no game created). Fix every FAIL. Once, also run it with `--full` (plays whole games through the live API; leaves finished test rooms, see step 11).
10. **Play it.** Two phones: create, join, play a few turns; add `?debug=1` to see the audio state; try **PLAY SOLO DEMO**; open `?g=CODE&board=1` on a laptop. iPhone silent switch off for sound.
11. **Clean up.** Remove test rooms with `dev/cleanup-test-rooms.sql` (preview first). Confirm `install.php` is gone and `debug` is false.

## If something fails
| Symptom | Likely cause and fix |
|---|---|
| 500 on every page, static files too | The host rejects a directive in `.htaccess` (most likely `Options -Indexes`). On the server, comment out that line and retry. If still 500, use the fallback below. |
| 500 only on `.php` addresses (static files load) | On this host a missing PHP file also gives 500, so first check the PHP file was uploaded. If it is there: a PHP error or a bad `config.php`; set `'debug' => true` briefly. |
| `api.php?a=time` works, `a=info` says "Server error." | Database login or host wrong, tables not installed, or the user lacks rights. Set `'debug' => true` briefly, read the message, then set it back to false. |
| install.php shows a red cross for PHP | Choose PHP 7.4 or newer in the control panel. |
| Page shows PHP source or blank | PHP is not running in that folder: ask the host. |
| Sound silent on iPhone | The silent switch (expected), or tap **Test sound** in the gear panel. |
| mp3 served with the wrong type | `.htaccess` `AddType audio/mpeg .mp3` was blocked: ask the host to allow it or add the MIME type in the control panel. |
| Polling errors or "too many connections" | Shared MySQL connection limit. Ask the host for `max_user_connections`; tell us before changing the polling interval. |
| Game state looks frozen or stale | A cache is answering instead of PHP: `dev/verify-deploy.sh` says so (FAIL on the two-calls test or an `Age` header). Ask the host to exclude `api.php` from caching. |
| Old files after an update | The host caches static files for hours; HTML and JSON are set to re-check, scripts use `?v=` numbers. Hard-refresh; if `index.html` still lags, the verify script's caching lines show the cache time. |

Fallback `.htaccess` (only if the full one gives a 500; keeps the secrets blocked):
```
DirectoryIndex index.html
<FilesMatch "^(config\.php|config\.sample\.php|.*\.sql|.*\.md)$">
  <IfModule mod_authz_core.c>
    Require all denied
  </IfModule>
  <IfModule !mod_authz_core.c>
    Order allow,deny
    Deny from all
  </IfModule>
</FilesMatch>
```

## Roll back
Delete `htdocs/desertranger/` and drop the one database created for the game. Nothing else was touched.

## Updating later
Rebuild `deploy/`, upload changed files only (Cyberduck compare/sync), and never overwrite the server's `config.php`.
