# Desert Ranger: Milestone 1 prototype

A playable web version of the board for 2 to 8 players. It uses plain PHP,
MySQL/MariaDB through PDO, and vanilla JavaScript with no build step and
no Composer. Clients poll the server about once a second.
Challenges and accounts are out of scope for this milestone (accounts are milestone 2).

## What's in the box

```
desertranger/                 <- upload this folder to htdocs/desertranger
  index.html                  one page: home / lobby / game (+ ?board=1 big-screen mode)
  api.php                     JSON API, routed by ?a=action (no URL rewriting needed)
  install.php                 one-time table creation; refuses to run once tables exist
  config.sample.php           copy to config.php (gitignored) and fill in DB details
  .htaccess                   blocks config/sql/md files, no directory listings
  board/desert-ranger.json    deploy COPY of /board/desert-ranger.json (not in git; made by
                              dev/make-assets.sh). In a repo checkout the code falls back to
                              /board/, so there is one master copy. Clients load it via api.php?a=board
  audio/                      shipped sound (mp3 + manifest.json) and the listening sheet audio/review.html.
                              review.html is DELIBERATELY part of the deploy (the whole desertranger/ folder is
                              uploaded; .htaccess only blocks config/sql/md files): open /desertranger/audio/review.html
                              to audition every clip. CREDITS.md in the same folder is not served (md is blocked).
  lib/rules.php               PURE rules engine (no DB/HTTP), all game rules live here
  lib/game.php                DB layer: loads state, calls the engine, saves in one transaction
  lib/db.php                  config + PDO connection
  lib/schema.sql              tables (users, games, players, events)
  assets/js/sync.js           clock sync (NTP-style) + Web Audio scheduling
  assets/js/board.js          piece placement (photo coordinates -> flat board) + hop animation
  assets/js/app.js            screens, API calls, 1 s polling
  assets/css/style.css        pitch-sheet palette + local fonts
  assets/img|audio|fonts/     BINARY, not in git (see "Binary assets")
  tests/rules_test.php        CLI rules tests (php tests/rules_test.php)
  tests/simulate_game.php     full game over HTTP, incl. double-tap / parallel-tap checks
  tests/poll_load.sh          N clients polling 1/s, prints req/s + latency + MySQL q/s
dev/e2e/                      headless-Chrome smoke test (Node + playwright-core), not deployed
dev/make-assets.sh            rebuilds the binary assets from the design workspace
board/desert-ranger.json      MASTER board data (squares, types, x,y in photo pixels)
docs/                         plan, rules notes (incl. the client's confirmed answers), audio research, this file
design/                       text sources of the design work (board-photo extraction, icon
                              extraction, crowd-audio mixing, pitch sheet). Their binaries are
                              in the assets zip under art-binaries/. See design/README.md
host-test/                    the earlier Network Solutions host test kit (amp-test.php + SOP)
```

`lib/` and `tests/` each have an `.htaccess` that denies web access.

## Binary assets and the board copy (not in git)

The GitHub connector used to commit this repo can only push text, so images, audio,
fonts and the deploy copy of the board JSON are **not in the repository**. Get them from
**`desertranger-assets-for-mac.zip`** (delivered separately, about 50 MB) and
**unzip it at the repo root**, i.e. the folder that contains `desertranger/`, `board/` and `docs/`:

```bash
cd ~/code/anza-borrego-challenge
unzip -o ~/Downloads/desertranger-assets-for-mac.zip
```

That creates:
- `desertranger/assets/img/`, `assets/audio/`, `assets/fonts/` and `desertranger/board/desert-ranger.json`.
  These are what the game needs, about 1.7 MB.
- `art-binaries/`: design originals that the game does **not** need. That covers the original
  board photo (4913×3583, the space of the JSON x,y), the flattened board, the full-size
  pieces, the icons (PNG and SVG), the line art, and the pitch sheet PDF/PNG with its fonts and
  images. See `ASSETS-README.txt` inside the zip.

All of these paths are in `.gitignore`, so they can't be committed by accident. If you'd rather
version them from the Mac, remove the lines from `.gitignore` and commit with plain git, or use
git LFS (`git lfs track "*.jpg" "*.png" "*.mp3" "*.ttf" "*.pdf"`).

You can also rebuild the game's assets with
`bash dev/make-assets.sh /path/to/design-workspace desertranger` (needs Python with Pillow).
The same script copies `board/desert-ranger.json` into `desertranger/board/` for upload.

| File | Source |
|---|---|
| `assets/img/board-2000.jpg` (560 KB) | `art-binaries/art/board-flat.jpg` resized to 2000 px wide, JPEG q80 |
| `assets/img/pieces/*.png` (8 files, about 50 KB each) | `art-binaries/art/pieces/*.png`, at most 200 px |
| `assets/audio/crowd-cheer-v2.mp3`, `crowd-aww-v2.mp3` | design workspace `audio/samples/crowd/` (made by `design/scripts/crowd_v2_*.py`) |
| `assets/fonts/Bungee-Regular.ttf`, `BungeeShade-Regular.ttf`, `Nunito.ttf`, `Caveat.ttf` | `art-binaries/pitch/fonts/` |

## Run it locally

Any Apache + PHP 7.4+ + MySQL 5.7+/MariaDB setup works. For a Mac, see
**Run it on a Mac with MAMP** below. On Debian or Ubuntu:

```bash
sudo apt-get install apache2 libapache2-mod-php php-mysql mariadb-server
sudo mariadb -e "CREATE DATABASE desertranger CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
  CREATE USER 'desertranger'@'localhost' IDENTIFIED BY 'pick-a-password';
  GRANT ALL ON desertranger.* TO 'desertranger'@'localhost';"
unzip -o desertranger-assets-for-mac.zip    # at the repo root: binary assets + board copy
cp -r desertranger /var/www/html/
cp /var/www/html/desertranger/config.sample.php /var/www/html/desertranger/config.php   # edit it
# browse to http://localhost/desertranger/install.php once, then http://localhost/desertranger/
```

For a quick run without Apache, use `cd desertranger && php -S 0.0.0.0:8099`. The
built-in server ignores `.htaccess`, so use it for development only.

On the build box the game is at **http://localhost:8098/desertranger/**. That
Apache listens on port 8098, and the database is `desertranger`, user
`desertranger`.

### URLs
- `/desertranger/` is the home screen. Enter a name, pick a rig, and either create a game or join one with a room code.
- `/desertranger/?g=ABCD` opens or resumes game ABCD. A refresh puts you back in the same seat.
- `/desertranger/?g=ABCD&board=1` is the shared TV/laptop view: board, turn banner, players, and log, with no controls.
- Add `&debug=1` to show the clock-sync footer (offset, best RTT, polls/s, audio state, cue lead).

### Tests
```bash
php desertranger/tests/rules_test.php                                       # 45 checks, exit 0 = pass
php desertranger/tests/simulate_game.php http://localhost:8098/desertranger 4
bash desertranger/tests/poll_load.sh http://localhost:8098/desertranger ABCD 8 60
cd dev/e2e && npm install && CHROME=/path/to/chrome node e2e.js http://localhost:8098/desertranger/
```

## Run it on a Mac with MAMP

Tested setup this targets: free MAMP 6 or 7 with default ports (Apache **8888**, MySQL **8889**),
MySQL user `root` / password `root`, and document root `/Applications/MAMP/htdocs`.
The build box emulated it with MySQL 8.0 on 127.0.0.1:8889 and root/root, plus a symlinked checkout. It was not run on a real Mac.

### 1. Clone and add the assets
```bash
mkdir -p ~/code && cd ~/code
git clone https://github.com/CosmicCEO/anza-borrego-challenge.git
cd anza-borrego-challenge
git checkout prototype-m1          # until the PR is merged; afterwards use main
unzip -o ~/Downloads/desertranger-assets-for-mac.zip    # AT THE REPO ROOT
ls desertranger/assets/img/board-2000.jpg desertranger/board/desert-ranger.json   # both must exist
```
Clone into a folder like `~/code`, **not** `~/Documents`, `~/Desktop` or `~/Downloads`.
macOS privacy protection can stop MAMP's Apache from reading those folders through a symlink,
and you get a 403.

### 2. Put the game in MAMP's htdocs (pick one)
- **Symlink**. Recommended, because edits in the repo are live:
  ```bash
  ln -s ~/code/anza-borrego-challenge/desertranger /Applications/MAMP/htdocs/desertranger
  ```
  With a symlink the code finds the board data in the repo's `board/` folder even without the
  zip's `desertranger/board/` copy.
- **Copy** (re-copy after every pull):
  ```bash
  rsync -a --exclude config.php ~/code/anza-borrego-challenge/desertranger/ /Applications/MAMP/htdocs/desertranger/
  ```
  A copy needs `desertranger/board/desert-ranger.json` from the zip.

### 3. Start MAMP and create the database
Start the servers in MAMP. In **Preferences → Ports**, keep 8888/8889, or note your own ports.
In **Preferences → PHP**, pick a PHP 8.x version (7.4 also works).

Use either phpMyAdmin or the CLI:
- **phpMyAdmin**: open the MAMP WebStart page (`http://localhost:8888/MAMP/`) → Tools → phpMyAdmin.
  Go to Databases, create `desertranger`, and choose collation `utf8mb4_unicode_ci`.
- **CLI**: the client lives inside MAMP. The path depends on the version, so `ls /Applications/MAMP/Library/bin/` to find it:
  ```bash
  /Applications/MAMP/Library/bin/mysql -h 127.0.0.1 -P 8889 -u root -proot \
    -e "CREATE DATABASE desertranger CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
  # MAMP 7 with MySQL 8 may use /Applications/MAMP/Library/bin/mysql80/bin/mysql
  ```
root/root is fine on a lab Mac. If you prefer a dedicated user, create one and use it in `config.php`.

### 4. config.php
```bash
cd ~/code/anza-borrego-challenge/desertranger      # or /Applications/MAMP/htdocs/desertranger for a copy
cp config.sample.php config.php
```
Set these values:
```php
'db_host'   => '127.0.0.1',   // NOT 'localhost': with 'localhost' PHP uses a socket and ignores the port
'db_port'   => 8889,
'db_socket' => '',            // or '/Applications/MAMP/tmp/mysql/mysql.sock' (then host/port are ignored)
'db_name'   => 'desertranger',
'db_user'   => 'root',
'db_pass'   => 'root',
'debug'     => true,          // fine on a lab Mac; shows error details in API responses
```
`config.php` is in `.gitignore`.

### 5. Install, then play
1. Open **http://localhost:8888/desertranger/install.php**. Every row should be ✓, followed by
   "Installed! Tables created". Reloading it shows "Already installed … Refusing to run again".
2. Open **http://localhost:8888/desertranger/**, create a game, and open `?g=CODE&board=1`
   in another window for the big-screen view.

### 6. Phones on the same Wi-Fi
- Find the Mac's IP with `ipconfig getifaddr en0`, or look in System Settings → Wi-Fi → Details. It's often `en1` on Macs with Ethernet.
- On each phone, open **http://<mac-ip>:8888/desertranger/**.
- If macOS asks whether to accept incoming connections for `httpd`, click **Allow**. If phones
  can't connect, check System Settings → Network → Firewall.
- **Plain HTTP on the LAN is fine for this prototype**:
  - **Audio**: the iOS audio unlock is a user-gesture rule ("Tap to enable sound"), not a secure-context rule. Web Audio works over http.
  - **Other browser APIs**: nothing the game uses needs a secure context. That covers `fetch`, `localStorage`, cookies, `crypto.getRandomValues`, Web Audio and `performance.now`.
  - **Cookie**: the seat cookie sets `Secure` only when the page is served over HTTPS, so resume works on http too.
  - **Avoid**: features like `crypto.randomUUID`, the clipboard API, service workers, and wake lock would need HTTPS (or `localhost`). The prototype avoids them on purpose.
- Make sure the phone isn't on a guest or "isolated" Wi-Fi network. Many of those block device-to-device traffic.
- **No sound on an iPhone?** The first thing to check is the **silent switch** on the side of the phone (orange showing = muted): iPhones
  silence web audio when it is on, and games and web pages are expected to respect it. (This was the cause of the one "no sound" report
  during the demo-mode test.) Then volume, and tap "Tap to enable sound" if it is shown. The ⚙ panel in the game has a **Test sound**
  button: it plays a dice sound and shows the audio state ("Audio is running, N clips loaded"), which tells you at once whether the page
  or the phone is the problem. `?debug=1` adds a footer with the same information plus the last landing pick.

### Troubleshooting (MAMP)
| Symptom | Fix |
|---|---|
| install.php: "Database connection ✗ … Connection refused" or "No such file or directory" | MySQL isn't running, or the port isn't 8889 (check MAMP → Preferences → Ports). Use `127.0.0.1`, not `localhost`, or set `db_socket` to `/Applications/MAMP/tmp/mysql/mysql.sock`. |
| "Access denied for user 'root'" | The MAMP root password was changed. Use the current one, or a dedicated user. |
| "Unknown database 'desertranger'" | Create the database (step 3). |
| 403 Forbidden on the symlink | The checkout is under Documents, Desktop or Downloads (macOS privacy), or Apache isn't following symlinks. Move the clone to `~/code`, or use the copy method. |
| 500 Internal Server Error | `.htaccess` isn't allowed. MAMP's default `AllowOverride All` handles it. If you changed `httpd.conf`, restore it, or delete the offending `.htaccess` lines. |
| Board image or pieces missing, fonts look plain | The zip wasn't unzipped at the repo root. Check `desertranger/assets/img/board-2000.jpg`. |
| "board/desert-ranger.json not found" | For a copied install, add `desertranger/board/desert-ranger.json` from the zip. |
| "Server error." in the game | Set `'debug' => true` and retry. Also look at `/Applications/MAMP/logs/php_error.log`. |
| No sound | Tap "Tap to enable sound". On iPhone, turn off the silent switch and raise the volume. Sounds only play on wins, roll-again and big setbacks. |
| Phones can't reach the Mac | Same Wi-Fi (not guest), correct IP and `:8888`, macOS firewall allows `httpd`. |
| Port 8888 already in use | Change it in MAMP → Preferences → Ports, and use that port in the URLs. |

Quick health checks: `http://localhost:8888/desertranger/api.php?a=time` should return
`{"ok":true,"t":...}` (no DB involved), and reloading `install.php` re-runs its checks (PHP version,
PDO driver, DB connection and server version) before saying "Already installed".

## Deploy to Network Solutions (shared Linux hosting)

1. **Check PHP**: in the hosting control panel, make sure PHP is **7.4 or newer**.
   8.x is better. `install.php` also checks this.
2. **Create the database**: in Database Manager, create a MySQL database and a user.
   Note the **host name**, which is often something like `xxxxx.mysql.netsol.com`
   and not `localhost`. Also note the database name, user, and password.
3. **Upload**: first unzip the assets zip at the repo root, or run `dev/make-assets.sh`. Then use
   SFTP (FileZilla, Cyberduck, or similar) to upload the whole `desertranger/` folder,
   including `assets/img`, `assets/audio`, `assets/fonts`, and `board/`, to
   `htdocs/desertranger/`.
4. **Configure**: on the server, copy `config.sample.php` to `config.php` and enter the DB
   host, port (usually 3306), name, user, and password. Leave `db_socket` empty. Leave `'debug' => false`. You can also edit
   `config.php` locally and upload it.
5. **Install**: open `https://yourdomain/desertranger/install.php` once. It checks the
   PHP version, the PDO MySQL driver, and the DB connection, then creates the tables. If you
   open it again, it refuses to run because the tables already exist. You may delete the file afterwards.
6. **HTTPS**: turn on the free SSL certificate for the domain. Phones need HTTPS to keep
   cookies reliably, and it is good practice for audio unlock too.
7. **Smoke test**: open the site on two phones, create and join a game, and play a few turns.
   Then open `?g=CODE&board=1` on a laptop. If something fails, open `api.php?a=time` (it should
   return `{"ok":true,"t":...}`) and `api.php?a=info` (it should list the vehicles). A "Server error." message means
   the details are in the host's PHP error log. You can also set `'debug' => true` briefly.

If the host still runs Apache 2.2, the `.htaccess` files include 2.2-style deny rules.

**For the client's Network Solutions account, follow `docs/DEPLOY-NS.md`** (shared-account safe, a clean upload folder from `dev/make-deploy-folder.sh`, and `dev/verify-deploy.sh` to check the live site). `docs/HANDOFF-NS-DEPLOY.md` is the hand-off for an AI assistant helping with it.

## How it works

### Rules engine (`lib/rules.php`)
- `roll($state, $dieFn)` and `choose($state, $choice, $dieFn)` return the new state, the
  animation steps, the log lines, and a sound cue. The engine never rolls dice itself. The server passes
  `random_int`, and tests pass scripted dice.
- **Confirmed rules** (client, Oct 1, 2026):
  - Effects chain.
  - Roll again keeps the turn, with no limit.
  - 44 rolls again and moves back that many squares, and chaining applies.
  - Swap is optional and can target any player. It is skipped in solo play.
  - The 6 → 33 shortcut is optional and only applies on an exact landing.
  - Overshooting FINISH wins.
  - Lose N turns means you skip your next N turns.
  - Moves never go below START.
- **Open rules** (marked `TODO(rules)` in code): the goto targets and square 48 (a plain −9)
  come straight from the JSON. Change the JSON, not the code.
- **Prototype decisions** (also `TODO(rules)`):
  - After a swap, neither player triggers the square they land on.
  - The extra die for square 44 is rolled automatically.
  - For roll again, the player taps ROLL again.
- `MAX_CHAIN_DEPTH = 20` stops any effect loop. The tests use a goto 1↔2 board to prove it.

### A turn on the server (`lib/game.php: dr_take_action`)
One transaction does all of this:
1. `SELECT … FROM games WHERE code=? FOR UPDATE` locks the game row.
2. If `last_action_key` equals this request's key, the request is a retry. It returns OK and does nothing.
3. The `turn` sent by the client must equal `games.turn_number`. If not, the server returns 409.
   A double tap sends the same turn number twice, so the second tap is rejected.
4. The server checks that the token belongs to the current player, runs the engine, and saves the
   players, the game, and the events. Then it commits.
The simulation fires two taps at the same instant from separate processes, and exactly one is accepted.

### Polling and the event log
- Clients call `api.php?a=state&code=ABCD&since=<lastEventId>` about once a second (every 4 s
  when the tab is hidden). Each poll runs 3 small SELECTs plus `SET time_zone`. The poll writes only
  when it updates `last_seen_at`, at most once every 20 s per player.
- Every action writes event rows: one log line, plus the animation steps (walk path, jump,
  swap, die value), plus the cue. A "loses this turn" skip gets its own line.

### Solo demo mode

In the lobby, the host alone sees a **PLAY SOLO DEMO** button under the "Need 2+ players" button (hidden from everyone
else, and hidden once a second player has joined). It starts the game at once with just the host plus two computer rivals
(`?demobots=0` or `1` on the page URL changes the number of rivals); everything else is the normal game: rolls, moves,
square events, radio calls, crowd cheers, ambience. A small **DEMO** tag shows in the game header. **End demo** (or **Back to
lobby** after the finish) returns the same room to a clean lobby.

- The 2-player minimum is skipped **only** for the demo start (`api.php?a=start` with `demo: true`, host alone in the lobby).
  A normal start still answers 409 "Need at least 2 players".
- No schema change: the demo flag is the payload of the game's `start` event; the state response reports `game.demo` and flags
  the rivals with `players[].bot`.
- The rivals are ordinary player rows. Their seat tokens are returned once, to the host, in the `start` response; the host's page
  keeps them in `localStorage` (`dr_rivals_<CODE>`) and rolls for them through the normal `roll`/`choose` actions after a short
  pause (they take shortcuts and never swap). If the host clears localStorage mid-demo the rivals stop moving; End demo still works.
- `api.php?a=enddemo` (host only) deletes the rivals and the demo's log, puts the host back on the start square and sets the room
  back to `lobby`. It refuses (409) on any game that was not started as a demo, so a normal game can never be reset.
- Tests: `php tests/demo_game.php <baseUrl>` (API, includes the 2-player-minimum checks) and
  `node dev/audio/demo_browser_test.js <baseUrl>` (one phone in headless Chrome).

### Sound settings (⚙ panel next to the speaker button)

Saved per device in `localStorage`; 🔊 mutes everything.
- **Ambience** on/off and **Ambience volume** (default **20 %**, `dr_amb_vol`): the desert bed, the critters and the background
  radio chatter. It starts on the **first tap** (on the home screen too, then the lobby and the game) and keeps playing after a
  win; the bed starts within a second or two and the critters and chatter load behind it. The board view is 6 dB louder. The
  background chatter scales with this slider. If the phone pauses the audio (call, lock screen, another app) a **"Sound paused.
  Tap here to resume."** bar appears and any tap resumes it; the bed restarts.
- **Game sounds volume** (default **50 %**, `dr_game_vol`): the turn-based sounds, meaning dice, landing radio calls, quotable
  lines and the crowd cheer/aww. 100 % is the level the clips were mastered at; 50 % is half of that.
- **Radio chatter** on/off (`dr_radio_on`): off = no landing calls, quotables or background chatter (dice and crowd stay).
- **Test sound**: plays a dice sound through the game's audio and shows the audio state.

### Synced audio
- **Cues**:
  - A win plays `cheer`.
  - A roll again plays `cheer`.
  - A "big setback" plays `aww`. That means any lose-turn, or being pushed back 5 or more squares in one action.
  - Tune this in `DesertRangerRules::BIG_SETBACK_SQUARES` / `finishAction()`.
- The server writes `play_at_ms = now + cue_lead_ms` (1500 ms, set in config) on the event.
- **Clock sync** (`assets/js/sync.js`):
  - At start-up the client sends 6 quick pings to `api.php?a=time`. That endpoint skips the DB.
  - After that it pings every 30 s, and every poll also counts as a sample.
  - For each sample, `offset = serverTime − (t0+t1)/2`.
  - The client keeps the last 40 samples and uses the median offset of the 5 with the lowest RTT.
- **Playback**:
  - The cue is scheduled on the Web Audio clock at `playAt − offset`, minus `outputLatency` where the browser reports it.
  - A cue that arrives up to 250 ms late starts immediately, skipping into the clip so it stays in sync.
  - A cue later than that is skipped.
- **Unlock**: a "Tap to enable sound" overlay appears after a refresh or resume. Creating, joining, or tapping ROLL also unlocks audio, as iOS requires.

### Piece placement
The JSON's x,y values are in **original photo** pixels (4913×3583). The displayed image is the
perspective-flattened board, so `board.js` applies the same 3×3 homography that produced
`art/board-flat.jpg` (from `design/art/_work/warp.py`). A plain scale would be off by up to about 2
squares near the corners. Positions are stored as percentages, so they hold at any zoom. If squares are
re-traced on the flat image, set the matrix to identity (there is a comment in `board.js`).

### Resume
Create and join return a secret seat token. The DB stores only its sha256. The client keeps the token in
`localStorage` (`dr_token_<CODE>`), and the server also sets an httpOnly cookie `dr_<CODE>`
that lasts 60 days. Either one restores the seat. POSTs must be `application/json`, so the
cookie fallback can't be abused by cross-site forms.

### Ready for milestone 2 (accounts)
The `users` table already exists, and `players.user_id` and `games.created_by_user_id` are
nullable foreign keys. Milestone 2 adds sign-up and login, sets `user_id` on join, and
lets a logged-in user reclaim their seat without the token.

## Test results (Oct 2, 2026, build box)
- `rules_test.php`: **45/45 pass** on PHP 8.4.26, and also on PHP 7.4.33 in Docker. The tests cover:
  - every chain, including 41→12, 44→41→12, 44→40→34, and 48→39
  - roll-again streaks
  - shortcut exact landing, accepted and declined
  - swaps with players ahead and behind, and solo play
  - lose 1 and lose 2 turns
  - overshoot win, clamping at START, and the chain-depth guard
  - an exhaustive pass over every square × die × 44-die (1836 cases)
  - 3000 random 2–8 player games, all finished, with invariants holding
- `simulate_game.php`: full games to the finish with 2, 3, 4, and 8 players against Apache + PHP 8.4 +
  MariaDB 11.8, all passing. A 3-player and a 4-player game also passed against **PHP 7.4.33 + MariaDB 11.8**
  and **PHP 7.4.33 + MySQL 5.7.44**. The MySQL 5.7 run used a fresh `install.php` run, and the rerun was refused as intended.
- **Port/socket config** (added for MAMP, Oct 2, 2026):
  - A fresh `install.php` plus 4- and 8-player simulations passed against **MySQL 8.0.46 on 127.0.0.1:8889 with root/root**, the MAMP defaults (Docker).
  - That run used a symlinked checkout without `desertranger/board/`, so it relied on the repo `board/` fallback.
  - The headless-Chrome e2e passed on the same setup.
  - A 4-player simulation passed with `db_socket` set to the MariaDB socket and a bogus host/port, which proves the socket wins.
  - An old `config.php` without `db_socket` still works, and the rules tests still pass 45/45.
- **Polling load**, 8 clients polling 1/s for 60 s while a game was played:
  - Requests: 8.0 req/s, with 8–10 req/s per second in the Apache log including the rolling player.
  - Latency: average 1.9 ms, p95 3.2 ms.
  - MySQL: about 46 queries/s. Apache CPU stayed under 1 s over the 60 s.
- **Headless Chrome**:
  - Setup: 3 phone contexts at 390×844 plus a board view at 1280×800.
  - Flow: create, join by link, start, 10 actions including a shortcut choice, then resume after reload and resume with only the cookie (localStorage cleared). No console errors.
  - Cue scheduling: all three unlocked devices scheduled the cue for the same server time, with clock offsets of 0–2 ms (same machine).

### Test results (Oct 3, 2026, lab Mac: MAMP + MySQL, one iPhone)
The code at tag `milestone-1`, served by MAMP on the lab Mac:
- `rules_test.php`: **45/45** on PHP 8.3.30 (MAMP) and on PHP 7.4.33 (MAMP's older PHP); every PHP file passes `php -l` under 7.4.
- `simulate_game.php` with **4 and with 8 players: ALL PASSED** against MAMP's PHP + MySQL. `tests/demo_game.php` (solo demo, plus the check that normal games still need 2 players): **ALL PASSED**, 36 checks. `dev/audio/play_at_test.php`: 4/4.
- Headless Chrome: `dev/audio/browser_test.js` **48/48** (host phone, guest phone and board view, against the mock API in `dev/audio/mock_server.js`); `dev/audio/demo_browser_test.js` **34/34** (real MAMP, one 390x844 phone plus a regular two-phone game); `dev/e2e/e2e.js` 10 turns with zero console errors (mock API); `dev/audio/review_check.js` 6/6 (all 233 clips decode).
- Audio: 233 clips, 3.45 MB. The speech-recognition check passes 161 of 216 lines; the other 55 are length-only (the words are right). Loudness is within 1 LU of target.
- **Real iPhone over Wi-Fi** (`http://<mac-ip>:8888/desertranger/`): the solo demo was played and the game timing was judged well paced. The first run had no sound because of the iPhone silent switch (expected: web audio respects it). Playtest findings are tracked as issues #5 to #8.

## Known gaps / not yet done
- **Verified on one real iPhone only** (the solo demo, over Wi-Fi). Not yet verified: **two or more real phones playing together**, the original v1 criterion "laugh and sad cues sound simultaneous on at least 3 phones, by ear", Android, Safari on a computer, Bluetooth speaker latency, and cellular. Cross-device clock sync is implemented but has only been exercised on one machine.
- **The sounds have not been fully auditioned.** The three CC0 critter clips (crow, coyote, hawk), the plant-name nature walks (chatter exchanges 9 to 12) and the stitched radio calls were checked by loudness, length and speech recognition only. 55 clips run longer than their length caps (words correct), and the written lines and the sound files still need a perfecting pass.
- **iPhone sound polish (Wave 2, needs a phone check):** the late start (#6), the stop after a win (#7) and sound after returning to the page (#8) were changed in Wave 2 and tested in headless Chrome only (it cannot produce the iPhone's "interrupted" state; that is simulated). They need a real iPhone check. The ghost shadow behind pieces (#5) has had a drawing change and still needs a phone check. The iPhone silent switch mutes the game, as intended.
- **Not tested on the Network Solutions host itself (the largest open item).** The account's reported specs (Oct 3, 2026): Debian, **PHP 7.4.10**, **MySQL 5.7.44**, SFTP on a non-standard port, CGI active. That is the stack already emulated in Docker (PHP 7.4 + MySQL 5.7.44), so version compatibility is expected to be fine. What is still unknown: the `.htaccess` limits, the database host name and connection limits, HTTPS, and the final URL and folder.
  The `.htaccess` options (`Options -Indexes`, `FilesMatch`) may be restricted on some shared plans.
  If you get a 500 error, remove the offending lines. Since then the code was also checked on the Mac under PHP 7.4.33 (syntax of every PHP file, `rules_test.php` 45/45, `play_at_test.php` 4/4).
- No turn timeout or skipping of absent players. Nobody can leave, kick, or rematch. A stalled player blocks the game.
- You can't join after the game starts. Spectators can use the board view.
- **No rate limiting on game creation and no cleanup of old games:** finished and test rooms accumulate. `dev/cleanup-test-rooms.sql` previews old rooms and removes them by date.
- **Solo demo:** the computer rivals' controls live in the host's browser storage, so clearing it mid-demo stops the rivals (End demo still works).
- `aww` fires fairly often (about 1 in 3 actions in simulations, because every lose-turn counts). Tune it with the client.
- Tabs that are hidden or slow to poll skip cues that arrive more than 250 ms late. That is intended.
- Board coordinates are still "approximate, to be re-traced". The pieces line up well on the flat image.
- Only one board. The rules engine accepts any board JSON with the same square types.
- Local Apache on the build box serves plain HTTP on 8098. HTTPS on 8443 was not configured.
- **A self-contained Xcode app** is an open decision: issue #11.
