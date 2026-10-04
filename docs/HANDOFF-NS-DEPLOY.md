# Hand-off: help deploy Desert Ranger to the client's Network Solutions host (for Claude or Grok)

**Audience:** an AI assistant helping the person (Jerod) who has the server login. **Runbook:** `docs/DEPLOY-NS.md` (read it first, top to bottom). **Repo:** `CosmicCEO/anza-borrego-challenge`, work on a branch, never push to `main`.

## Your role
You **guide and verify**. The person at the keyboard does every action on the host (Cyberduck/SFTP, Database Manager, control panel). You prepare and check things on the lab Mac, read results, and diagnose.

## Guardrails (these override everything else)
- **No credentials, ever.** Do not ask for, accept, store or repeat passwords, tokens, SFTP/DB logins, or the contents of `config.php`. If a secret appears in the chat, say so, tell the person to change it, and do not repeat it. Never create, read, print or commit `config.php`.
- **One folder only.** The host is a shared account: other folders are other people's sites. Everything happens inside a new `htdocs/desertranger/`. Never suggest editing, renaming or deleting anything outside it, and never suggest overwriting (upload conflicts: **Skip**).
- **Ask before any write on the host,** and before any destructive step (deleting files, dropping a database, running SQL that deletes). Test-room cleanup uses only `dev/cleanup-test-rooms.sql`, preview first.
- Only the database created for the game. Never touch another site's database or user.
- No `sudo`, no machine-wide changes, no system installs without a yes.
- Stop and ask when a step needs something you do not have (a login, a decision, a host setting) instead of guessing.

## Facts
Debian, PHP 7.4.10, MySQL 5.7.44, SFTP port 2222, a shared account with other sites under `htdocs`, top-level `.htaccess` is only `DirectoryIndex index.html index.php`. Tested on exactly this stack (PHP 7.4 + MySQL 5.7.44) plus PHP 7.4.33 on the Mac. Unknown: final domain and HTTPS, database host name, `.htaccess` limits, connection limits.

## What you can do
- [ ] Build the clean upload folder: `bash dev/make-deploy-folder.sh` (lab Mac clone on `main`); check the manifest.
- [ ] Walk the person through `docs/DEPLOY-NS.md` steps 1 to 11, one at a time, confirming each before the next.
- [ ] Run `bash dev/verify-deploy.sh https://THEIR-DOMAIN/desertranger` and explain every line; then once with `--full` after they agree.
- [ ] Diagnose from **exact error text with secrets removed** (the table in the runbook).
- [ ] Record what happened in `docs/NS-DEPLOY-LOG.md` (date and time CT, step, result, verify output; no secrets) and open a PR.

## Stop conditions
A step would touch anything outside `htdocs/desertranger/`; a credential is needed; the host shows a security warning you cannot explain; a check shows `config.php` readable (tell the person to change the database password and fix `.htaccess` first); disk, time or access problems you cannot resolve in two attempts (log the open question and hand back).

## Done when
`verify-deploy.sh` shows no FAIL on the live address (with HTTPS), two phones played a game, the solo demo works, `install.php` is deleted, `debug` is false, test rooms are cleaned, and the log is committed.

## How to start (paste this)
> You are helping me deploy Desert Ranger to my client's Network Solutions host. Read `docs/HANDOFF-NS-DEPLOY.md` and `docs/DEPLOY-NS.md` in the repo first. Never ask for or repeat any password or the contents of config.php; I will type credentials myself. Everything happens inside a new `htdocs/desertranger/` folder. Ask before every write or delete. Guide me one step at a time and run the checks on my Mac.
