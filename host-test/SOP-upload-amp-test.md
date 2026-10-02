# Web Host Test: Upload One File

**For:** Jeffery Price  **From:** Jerod  **Takes:** about 20 minutes

**Why:** This tells Jerod if your website host can run the Desert Ranger game. You upload **one file**, open it, send Jerod what it shows, then delete it.

> **The golden rule:** If anything looks weird, **stop and call Jerod.** You can't break anything by stopping.

---

## Part A: What you need

| ☐ | Item | Write it here |
|---|------|---------------|
| ☐ | Your website address (domain) | ______________________ |
| ☐ | FTP host / server | ______________________ |
| ☐ | FTP username | ______________________ |
| ☐ | FTP password | (keep it private, don't write it here) |
| ☐ | The file **amp-test.php** (Jerod sends it) | Saved on your Desktop |

> **Use this exact file name:** `amp-test.php` (all lowercase). Don't rename it. Don't open it in Word.

---

## Part B: Check who your host is (we think Network Solutions)

1. ☐ Go to **networksolutions.com** and log in. (Click **Account Manager** or go to networksolutions.com/my-account/login.)
2. ☐ On the left side, click **Hosting**.
3. ☐ **Do you see a hosting plan or a "hosting control panel"?** Then your host is Network Solutions. Good. Keep going.
4. ☐ **STOP and call Jerod if:**
    - you can't log in, or there's no **Hosting** on the left, **or**
    - you only see **Website Builder**, **or**
    - the plan says **Windows**.
    - (Some plans can't run our game. Jerod needs to know first.)
5. ☐ In the control panel, find **FTP & Content Publishing** (or **SFTP & Content Publishing**). Click **SFTP Account Manager** (or **FTP Account Manager**).
6. ☐ Copy down the **Host / Server**, **Username** and **Port** into Part A. Set or reset the password there if you need to.
   This FTP login is **not** the same as your Network Solutions login.

> **Not on Network Solutions?** Ask your host's support: "What are my FTP or SFTP host, username and password?" Then keep going.

---

## Part C: Get FileZilla (free)

7. ☐ Go to **https://filezilla-project.org** (official site only).
8. ☐ Click **Download FileZilla Client**. Pick the plain, free **FileZilla Client**. (Not "Pro", not "Server".)
9. ☐ Install it. **If the installer offers extra programs, click Decline / Skip.**

---

## Part D: Connect

10. ☐ Open FileZilla. At the top is the **Quickconnect** bar. Fill in:

| Box | What to type |
|-----|--------------|
| **Host** | Your FTP host from Part A. For secure SFTP, type `sftp://` in front. |
| **Username** | Your FTP username |
| **Password** | Your FTP password |
| **Port** | The port from your Account Manager. Usually **22** for SFTP (best, if offered) or **21** for plain FTP. |

11. ☐ Click **Quickconnect**. If a box asks about an "unknown key" or "certificate", tick **Always trust** and click **OK**.
12. ☐ **Check:** the **right side** now shows folders. That's your website.
    The **left side** is your own computer.

> **Stop and call Jerod** if you see red error lines and no folders on the right after two tries.

---

## Part E: Make the folder and upload

13. ☐ On the right side, double-click the web folder.
    **On Network Solutions it is usually `htdocs`.** (On other hosts: `public_html`, `www`, or `htdocs`.)
    Don't see one of these? **Stop and call Jerod.**
14. ☐ Right-click empty space on the right side, then **Create directory**. Name it exactly: **`rangertest`**
15. ☐ Double-click **rangertest** to open it. It should be empty.
16. ☐ On the left side, find **amp-test.php** on your Desktop. **Drag it to the right side.** (Leave transfer type on the default "Auto". That's fine.)
17. ☐ **Check:** the right side now shows `amp-test.php` inside `rangertest`. The bottom of the window says "successful".

---

## Part F: Open the test page

18. ☐ Open your web browser and type:
    **https://______________________/rangertest/amp-test.php**
    (put your domain in the blank, for example `example.com`)
19. ☐ **Check:** you see a page with a big **red "DELETE THIS FILE WHEN DONE"** bar at the top, and green / yellow / red rows.
    Red and yellow rows are OK. Jerod will read them. **Don't change anything.**
20. ☐ Don't fill in the **MySQL / database** boxes. **Leave the database password empty** unless Jerod is on the phone and asks you to.

> **Page looks different?** Code text, a download, or an error? Look at the **Troubleshooting** table below, then call Jerod.

---

## Part G: Send it to Jerod

21. ☐ Scroll to the bottom. Click **"Copy this report"**. Paste it into a text or email to Jerod.
    **Or:** take screenshots of the **whole page**, top to bottom, and send them all.
22. ☐ Also tell Jerod: did the address start with **https** and show a padlock? Yes / No

---

## Part H: Clean up (do this the same day if you can)

23. ☐ Wait until Jerod says "Got it." Then, in FileZilla, go back up to `htdocs` (or your web folder).
24. ☐ Right-click the **rangertest** folder, then **Delete**, then **Yes**. This deletes the file too.
25. ☐ **Final check:** open **https://______________________/rangertest/amp-test.php** again.
    It should now say **Not Found** (404). **That means you're done.**
    If the test page still shows, delete again or call Jerod.

> **Forgot to delete it?** It switches itself off after 7 days. But please still delete it.

---

## Troubleshooting

| What you see | What it probably means | What to do |
|---|---|---|
| **FileZilla can't connect** ("timed out", "refused", "authentication failed") | Wrong host, port, username or password | Check each box for typos. Try port 21 without `sftp://`. Reset the FTP password in the Account Manager. Still stuck? Call Jerod. |
| **404 Not Found** in the browser | The file isn't where the address points | Check spelling: `rangertest` and `amp-test.php`, all lowercase. Make sure `rangertest` is inside `htdocs` (or your web folder), not next to it. |
| **The page shows code** (text starting with `<?php`) | The host isn't running PHP there | **Stop.** Don't try to fix it. Call Jerod. (Maybe Windows or builder-only hosting.) |
| **500 Internal Server Error** | The server had a problem running it | Take a screenshot and call Jerod. |
| **Permission denied** in FileZilla | You're in the wrong folder, or the login can't write there | Go into `htdocs` (or your web folder) first, then make `rangertest`. Still denied? Call Jerod. |
| **The browser downloads the file** instead of showing a page | PHP isn't turned on for this site | **Don't open the downloaded file.** Delete it. Call Jerod. |
| **Big red "This test page has expired"** | More than 7 days passed | Normal. Delete the folder (Part H). Ask Jerod for a fresh copy if needed. |

---

## What to send back to Jerod

- ☐ The **copied report** (or screenshots of the whole test page)
- ☐ Your **website address**
- ☐ Host name: Network Solutions? **Yes / No / Not sure.** Plan name if you saw it: ____________
- ☐ **SFTP (port 22)** or **FTP (port 21)**?
- ☐ The web folder name you used: **htdocs / public_html / www / other:** ________
- ☐ Did the address show **https** + padlock? **Yes / No**
- ☐ **"I deleted rangertest and the check showed Not Found"**: Yes / No

**Never send passwords by text or email.** Jerod will ask on the phone if he needs one.
