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
| ☐ | **Transmit** on your Mac | In your Applications folder |

> **Use this exact file name:** `amp-test.php` (all lowercase). Don't rename it. Don't open or edit it.
> **Use a fresh copy:** upload it within 3 days of when Jerod sends it. (Old copies can switch off right away.)

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

## Part C: Connect with Transmit

7. ☐ Open **Transmit**. You see two sides. The **left side** is your Mac. The **right side** is where the website will show.
    (Right side shows files, not a form? Click the small icon at its top right.)
8. ☐ On the right side, click the **Quick Connect** tab. Fill in the form:

| In Transmit | What to choose or type |
|-----|--------------|
| **Protocol** menu | **SFTP** (best). Only if SFTP won't connect, pick **FTP**. |
| Server address | Your FTP / SFTP host from Part A |
| User name | Your FTP username |
| Password | Your FTP password |
| Port | The port from Part A. Usually **22** for SFTP, **21** for FTP. |

9. ☐ Click **Connect**. The first time, Transmit may ask if you trust this new server. If the name matches your host, say yes / connect.
10. ☐ **Check:** the **right side** now shows folders. That's your website.

> **Stop and call Jerod** if it still won't connect after trying SFTP and then FTP.

---

## Part D: Make the folder

11. ☐ On the right side, double-click the web folder.
    **On Network Solutions it is usually `htdocs`.** (On other hosts: `public_html`, `www`, or `htdocs`.)
    Don't see one of these? **Stop and call Jerod.**
12. ☐ Click once in an empty spot on the right side. Then choose **File > New Folder**. Name it exactly: **`rangertest`** and press Return.
13. ☐ Double-click **rangertest** to open it. It should be empty.

---

## Part E: Upload the file

14. ☐ On the **left side**, double-click **Desktop** and find **amp-test.php**.
    (Or drag it straight from a Finder window. That works too.)
15. ☐ **Drag amp-test.php to the right side**, into the empty `rangertest` folder.
16. ☐ **Check:** the right side shows `amp-test.php`, and the path at the top ends in `htdocs/rangertest` (or your web folder, then `rangertest`).

---

## Part F: Open the test page

17. ☐ Open your web browser and type:
    **https://______________________/rangertest/amp-test.php**
    (put your domain in the blank, for example `example.com`)
18. ☐ **Check:** you see a page with a big **red "DELETE THIS FILE WHEN DONE"** bar at the top, and green / yellow / red rows.
    Red and yellow rows are OK. Jerod will read them. **Don't change anything.**
19. ☐ Don't fill in the **MySQL / database** boxes. **Leave the database password empty** unless Jerod is on the phone and asks you to.

> **Page looks different?** Code text, a download, or an error? Look at the **Troubleshooting** table below, then call Jerod.

---

## Part G: Send it to Jerod

20. ☐ Scroll to the bottom. Click **"Copy this report"**. Paste it into a text or email to Jerod.
    **Or:** take screenshots of the **whole page**, top to bottom, and send them all.
21. ☐ Also tell Jerod: did the address start with **https** and show a padlock? Yes / No

---

## Part H: Clean up (do this the same day if you can)

22. ☐ Wait until Jerod says "Got it." Then, in Transmit, go back up to `htdocs` (or your web folder): choose **Go > Enclosing Folder**.
23. ☐ Click the **rangertest** folder once to select it. Press **Command (⌘) + Delete**. Confirm the delete. This deletes the file inside it too. (Server files don't go to your Trash. They are gone.)
24. ☐ **Final check:** open **https://______________________/rangertest/amp-test.php** again.
    It should now say **Not Found** (404). **That means you're done.**
    If the test page still shows, delete again or call Jerod. (Forgot? It switches itself off after 7 days, but please still delete it.)

---

## Troubleshooting

| What you see | What it probably means | What to do |
|---|---|---|
| **Transmit can't connect** ("timed out", "refused", "authentication failed") | Wrong protocol, server, port, username or password | Check each box for typos. Try Protocol **FTP** with port **21**. Reset the FTP password in the Account Manager. Still stuck? Call Jerod. |
| **404 Not Found** in the browser | The file isn't where the address points | Check spelling: `rangertest` and `amp-test.php`, all lowercase. Make sure `rangertest` is inside `htdocs` (or your web folder), not next to it. |
| **The page shows code** (text starting with `<?php`) | The host isn't running PHP there | **Stop.** Don't try to fix it. Call Jerod. (Maybe Windows or builder-only hosting.) |
| **500 Internal Server Error** | The server had a problem running it | Take a screenshot and call Jerod. |
| **Permission denied** in Transmit | You're in the wrong folder, or the login can't write there | Go into `htdocs` (or your web folder) first, then make `rangertest`. Still denied? Call Jerod. |
| **The browser downloads the file** instead of showing a page | PHP isn't turned on for this site | **Don't open the downloaded file.** Delete it. Call Jerod. |
| **Big red "This test page has expired"** | Right after uploading: the copy was too old (Transmit can keep old file dates). A week later: normal. | Delete the folder (Part H). If it expired right away, ask Jerod for a fresh copy and upload it the same day. |

---

## What to send back to Jerod

- ☐ The **copied report** (or screenshots of the whole test page)
- ☐ Your **website address**
- ☐ Host name: Network Solutions? **Yes / No / Not sure.** Plan name if you saw it: ____________
- ☐ Transmit protocol: **SFTP (port 22)** or **FTP (port 21)**?
- ☐ The web folder name you used: **htdocs / public_html / www / other:** ________
- ☐ Did the address show **https** + padlock? **Yes / No**
- ☐ **"I deleted rangertest and the check showed Not Found"**: Yes / No
- **Never send passwords** by text or email.
