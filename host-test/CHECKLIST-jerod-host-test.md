# Host test: developer checklist (Jerod)

Goal: confirm that Jeffery's Network Solutions (NS) hosting runs PHP 8 + MySQL, and set up dev access. Kit: `host-test/amp-test.php`.

## 0. Before you start
- [ ] **Preferred over sharing his password:** have Jeffery invite you as a **Tech** user (name menu → **Accounts & Users** → Manage → **+ Add User** → role **Tech** → Invite). Tech can manage sites and DNS, with no billing access, and you use your own login and 2FA.
- [ ] **2FA:** each login sends a code to the trusted email (fallbacks: trusted phone text, recovery email, recovery key; max 5 attempts). Book a time when Jeffery can read it to you.
- [ ] If an "Additional Security" setup screen appears, click **Skip**. Don't add your own phone or email without his OK.

## 1. Account and plan
- [ ] Log in at `networksolutions.com/my-account/login` → **Hosting** (left nav).
- [ ] Confirm a **Linux/UNIX hosting** package exists. **Stop** if it's Website Builder-only, WordPress-only, or **Windows** (Windows plans have no PHP; webroot is `www`).
- [ ] Note the plan name ______ and domain ______.

## 2. SFTP user
- [ ] Control panel → *FTP/SFTP & Content Publishing* → **SFTP Account Manager** (or FTP Account Manager).
- [ ] Create a dedicated user for yourself (don't reuse the master login). Note host ______ and port ______ (SFTP usually 22; one legacy NS doc says 2222).

## 3. PHP
- [ ] *Configurations* → Show All → **PHP Manager**. Set the newest **8.x** offered (8.1+ preferred, 8.0 minimum). Note the version ______.

## 4. Database
- [ ] *Configurations* → **Database Manager**. Create a MySQL DB and user for the game.
- [ ] Note DB name ______, user ______, **server host** ______ (often a remote hostname, not `localhost`), and the version if shown.

## 5. Upload and run
- [ ] SFTP (Transmit, FileZilla, Cyberduck, or CLI) to `htdocs/rangertest/amp-test.php`.
  `sftp -P <port> <user>@<host>` → `cd htdocs` → `mkdir rangertest` → `put amp-test.php rangertest/`
- [ ] **Expiry:** the page turns itself off 7 days after the file's mtime. `touch amp-test.php` first, or don't preserve timestamps (no `put -p`, Transmit's "Preserve Modification Dates" off).
- [ ] Open `https://<domain>/rangertest/amp-test.php`. Check: red banner and PASS/WARN/FAIL rows (not raw PHP, not a download).
- [ ] Submit the MySQL form with the new DB host, name, user and password. Expect PASS on connect, temp table, insert/select, transactions, and CREATE/ALTER/DROP.
- [ ] After the browser polling rows fill in, click **Copy this report** (it then includes timing and clock offset).

## 6. Clean up
- [ ] Delete `htdocs/rangertest/` (`rm rangertest/amp-test.php` then `rmdir rangertest`). Verify the URL now returns **404**.

## 7. Send back to Grok (chat)
- [ ] The pasted **Copy this report** text (it contains no secrets; still check before pasting).
- [ ] Plan name, PHP versions offered and chosen, DB host type (localhost or remote), SFTP port, webroot, anything odd.
- [ ] **No passwords, usernames, or 2FA codes** in chat.

## 8. Credentials
- [ ] Store the NS login (if shared), recovery key, SFTP user and DB credentials in **your password manager** only. Never in the repo, `/workspace`, the shared box, or chat.

## 9. Future support (optional)
- [ ] If not done in step 0, get added as a **Tech** user. For phone support, NS may verify the account holder (security PIN), so have Jeffery on the call or ask support what they accept for a Tech contact.
