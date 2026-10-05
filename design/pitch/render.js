// Renders the pitch sheet with Playwright (macOS / any machine with Node + a Chromium-based browser).
//   node design/pitch/build.py is run first by this script; then:
//   CHROME=/path/to/browser node design/pitch/render.js [outBase]      (needs `cd dev/e2e && npm install` once)
//   SHEET=wave2 node design/pitch/render.js [outBase]   renders build-wave2.py -> desert-ranger-wave2.html instead
// Writes <outBase>.pdf (all pages) and <outBase>.png (page 1) plus <outBase>-status.png (page 2, if the sheet has one).
// Default outBase: design/pitch/desert-ranger-pitch. (The old render.sh does the same with google-chrome on Linux.)
'use strict';
const { execFileSync } = require('child_process');
const path = require('path');
const { chromium } = require('../../dev/e2e/node_modules/playwright-core');
(async () => {
  const dir = __dirname;
  const sheet = process.env.SHEET || '';
  execFileSync('python3', [path.join(dir, sheet ? 'build-' + sheet + '.py' : 'build.py')], { cwd: dir, stdio: 'inherit' });
  const out = process.argv[2] || path.join(dir, sheet ? 'desert-ranger-' + sheet : 'desert-ranger-pitch');
  const chrome = process.env.CHROME || '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary';
  const browser = await chromium.launch({ executablePath: chrome, headless: true, args: ['--allow-file-access-from-files', '--hide-scrollbars'] });
  const ctx = await browser.newContext({ viewport: { width: 816, height: 1056 }, deviceScaleFactor: 2.7 });
  const page = await ctx.newPage();
  await page.goto('file://' + path.join(dir, sheet ? 'desert-ranger-' + sheet + '.html' : 'desert-ranger-pitch.html'));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(1500);
  // Automatic layout check: text running out of a card, a card running into the footer, or a card left mostly empty.
  const problems = await page.evaluate(() => {
    const out = [];
    document.querySelectorAll('.sheet').forEach((sh, si) => {
      const footer = sh.querySelector('.footer'); const ft = footer ? footer.getBoundingClientRect().top : 1e9;
      sh.querySelectorAll('.card').forEach((c) => {
        const cr = c.getBoundingClientRect(); const ul = c.querySelector('ul'); const name = ((c.querySelector('h2') || {}).textContent || '?').trim();
        const note = c.querySelector('.p2note');
        const used = ul ? ul.getBoundingClientRect().bottom : cr.top; const limit = (note ? note.getBoundingClientRect().top : cr.bottom) - 6;
        if (used > limit) out.push('page ' + (si + 1) + ' card "' + name + '": text runs ' + Math.round(used - limit) + 'px past its box');
        else if (cr.bottom - used > 95) out.push('page ' + (si + 1) + ' card "' + name + '": ' + Math.round(cr.bottom - used) + 'px empty at the bottom (loose)');
        if (cr.bottom > ft - 4) out.push('page ' + (si + 1) + ' card "' + name + '": overlaps the footer');
      });
    });
    return out;
  });
  console.log(problems.length ? 'LAYOUT WARNINGS:\n  ' + problems.join('\n  ') : 'layout check: no overflow, no overlap');
  const sheets = await page.$$('.sheet');
  if (sheets.length === 0) await page.screenshot({ path: out + '.png' });
  else for (let i = 0; i < sheets.length; i++) await sheets[i].screenshot({ path: i === 0 ? out + '.png' : out + '-status.png' });
  await page.pdf({ path: out + '.pdf', width: '8.5in', height: '11in', printBackground: true, preferCSSPageSize: true });
  console.log('rendered', sheets.length || 1, 'page(s) ->', out + '.{png,pdf}');
  await browser.close();
})();
