# Web Board Game: Build Plan (v0)

Hand-off doc for the builder (Grok CLI on the lab Mac). Starting from nothing. Original game, turn-based, Candy Land style, 2 to 8 players.

## Product summary
- Players join from their phone's browser. No app install.
- Two ways to play, same build:
  - **Same room:** everyone has a phone, plus an optional shared "board screen" (a TV or laptop at `/board/<gameId>`).
  - **Remote:** each phone shows the board as well as its own controls. Players talk on a regular phone call; the game doesn't handle voice chat.
- Accounts: simple sign-up with a username and password.
- Saved games: resume any game later, even days later.
- Audio: packaged voices, sound effects, laugh track, sad track. **Every device plays each cue at the same time.**
- v1 gameplay: roll a die, move forward or back. Challenges come later.

## Stack (decided: the client's AMP host, which runs Apache, MySQL, and PHP)
- **Server:** PHP 8.x API under `/api/` (plain PHP or Slim), with PDO and prepared statements.
- **Database:** MySQL or MariaDB.
- **Client:** Vite + TypeScript (React or Svelte), built to static files and uploaded alongside the PHP. The board is drawn with Canvas or SVG.
- **Live updates:** shared hosting usually can't hold WebSockets open, so clients **poll** `GET /api/games/<id>/events?since=<lastEventId>` every 1 s (about 3 s when it isn't their turn; long-polling up to about 20 s if the host allows it). A dice game doesn't need anything faster.
- **Audio:** Web Audio API, through a thin wrapper of our own (or Howler.js).
- **Auth:** PHP `password_hash`/`password_verify`, PHP sessions with secure, httpOnly, SameSite cookies, and CSRF tokens on POST requests.
- **HTTPS required** (phones need it for audio and cookies). Most AMP hosts offer free Let's Encrypt certificates.
- **Local development:** run a matching PHP/MySQL setup on the lab Mac (Docker or MAMP), then deploy by SFTP or git.
- **Concurrency:** wrap each turn in a MySQL transaction with `SELECT ... FOR UPDATE` on the game row, so two taps on ROLL can't both count.

## Data model (first pass)
- `User { id, username (unique), passwordHash, createdAt }`
- `Game { id, code (6 chars), status: lobby|active|finished, boardId, currentTurnSeat, turnNumber, createdBy, createdAt, updatedAt }`
- `Seat { gameId, seat (0-7), userId, color, position, connected }`
- `GameEvent { gameId, turnNumber, type, payload JSON, createdAt }` (append only)
- `Board` is a JSON file in the repo, not in the database (see below).

## Board as data
```json
{
  "id": "board-01",
  "squares": [
    { "i": 0, "type": "start" },
    { "i": 5, "type": "move", "delta": 3, "cue": "laugh" },
    { "i": 9, "type": "move", "delta": -4, "cue": "sad" },
    { "i": 40, "type": "finish", "cue": "win" }
  ],
  "length": 41,
  "die": { "sides": 6 },
  "layout": "path-01.svg"
}
```
- Squares that aren't listed are plain.
- Each square type is a small rule function: `(state, square) => { newState, events[], cues[] }`.
- **Adding challenges later:** add a `"type": "challenge"` square and a challenge handler. Nothing else changes.
- Board art and some color images already exist. First task: put them in `/client/public/art/`, then trace the path over the board image to make the `squares` list. Each square stores its pixel center (`x`, `y`) on the art so pieces line up with it. A small dev-only tool for clicking square centers on the image is worth building for this.

## Turn flow (v1)
1. The server tells everyone whose turn it is (`turn_start`). The current player's phone shows a big ROLL button.
2. The player taps ROLL and sends `{type:"roll"}`.
3. The server checks it's really that player's turn, rolls the die, moves the piece, and applies the square's rule (which can chain).
4. The server saves the result, then broadcasts `{events:[roll, move, squareEffect], state, cues:[...]}`.
5. The win check: reaching or passing the last square wins. Optional rule: you must land on it exactly.
6. Next seat's turn, skipping disconnected players after a timeout (default 60 s, configurable).

## Synchronized audio (the important part)
- **Clock sync:** each client calls `GET /api/time` about 5 times when it joins and every 60 s after that. It works out the gap between its clock and the server's from the round-trip times, using the median.
- **Cues:** because of polling, set the play-at time **far enough ahead that every phone has polled first**: `{cue:"laugh_03", at: serverNow + 1500ms}` while polling every 1 s. A phone that learns about a cue after its play-at time skips that sound rather than playing it late. Each client converts that to its own clock and schedules playback with `AudioContext.currentTime` (sample-accurate).
- **Preloading:** right after login, each client downloads and decodes the audio pack (`/audio/manifest.json` plus files). Show a loading bar.
- **iOS and Android unlock:** browsers block sound until the user taps something, so the Join or Enter Game button must call `audioCtx.resume()`.
- **Voice lines:** the same mechanism, plus a priority rule so a voice line ducks or interrupts the laugh track.
- **Manifest format:** `{ "laugh": ["laugh_01.mp3", ...], "sad": [...], "voice.roll": [...] }`. The server picks one of the variants so all devices play the same file.
- **Volume:** a mute and volume control on each device.
- Check the slot machine project for audio code to reuse (manifest, preloading, the player wrapper).

## Screens
- **Phone:** login or sign-up, my games (resume or create), lobby (room code, seats, color picks, Start), in game (board view, ROLL button, whose turn, event feed), game over.
- **Board screen** (`/board/<id>`, no login, view only, needs the room code): the big board, all pieces, the roll animation, the turn banner.

## Security basics
- Passwords hashed (argon2 or bcrypt). Rate-limit login attempts. httpOnly, SameSite cookies.
- Check every API request against the logged-in user and their seat. Use prepared statements everywhere.
- Room codes are for joining only; a seat is tied to a user account.
- Nothing secret gets stored on the client.

## Milestones
> **Status note (Oct 3, 2026):** this is the original engineering breakdown (M0 to M6). What was built differs: a plain-JavaScript client with no build step, and a PHP/MySQL polling server. The client-facing milestones on the pitch sheet are **1 Playable prototype (complete, tag `milestone-1`)**, 2 Accounts & saved games, 3 Synchronized sound & voices (first pass done), 4 Launch. Current status, test results and gaps are in `docs/PROTOTYPE.md`.

1. **M0 setup:** repo with `/api` (PHP) and `/client` (Vite), a local PHP/MySQL setup, SQL migration files, PHPUnit and Vitest.
2. **M1 game rules in PHP:** pure functions (board JSON in, turn results out), with PHPUnit tests including chained squares and the win rule.
3. **M2 accounts:** sign-up, login, logout, sessions, CSRF, and the MySQL tables.
4. **M3 lobby and live play:** create or join with a room code, seats, a full game played through POST requests and polling, saved after each turn, resume after reload.
5. **M4 audio:** manifest, preload, unlock, clock sync, scheduled cues. Test with 3 or more phones in one room and confirm they play together.
6. **M5 board screen and polish:** shared screen view, animations, turn timeout, game over and rematch.
7. **M6 deploy:** upload to the client's AMP host with HTTPS, then set up the database and run the migrations. Check the PHP version and confirm `.htaccess` rewrites work first.
8. **Later:** challenge squares, more boards, spectators, admin tools.

## Done criteria for v1
- 2 to 8 players complete a game across separate phones, both in one room and remotely.
- Reloading or reconnecting mid-game restores the exact state.
- Laugh and sad cues sound simultaneous on at least 3 phones in one room (by ear; aim for within 20 ms).
- A game can be closed and resumed the next day.

## Open questions for Jerod (defaults are used until he answers)
- Board size and layout come from the existing board art (trace the squares from the image).
- Art and audio delivery: file formats and naming. Default: MP3 or AAC, with names matching the manifest.
- Audience: private friends and family or public release. This affects sign-up, moderation, and licensing.
- AMP host details: PHP version, MySQL version, whether SSH or cron is available, and whether long-polling requests get killed.
- Exact-landing rule to win? Default: no.
- Turn timeout length. Default: 60 s, configurable.
