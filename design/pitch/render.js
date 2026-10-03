// Renders the pitch sheet with Playwright (macOS / any machine with Node + a Chromium-based browser).
//   node design/pitch/build.py is run first by this script; then:
//   CHROME=/path/to/browser node design/pitch/render.js [outBase]      (needs `cd dev/e2e && npm install` once)
// Writes <outBase>.pdf (all pages) and <outBase>.png (page 1) plus <outBase>-status.png (page 2, if the sheet has one).
// Default outBase: design/pitch/desert-ranger-pitch. (The old render.sh does the same with google-chrome on Linux.)
'use strict';
const { execFileSync } = require('child_process');
const path = require('path');
const { chromium } = require('../../dev/e2e/node_modules/playwright-core');
(async () => {
  const dir = __dirname;
  execFileSync('python3', [path.join(dir, 'build.py')], { cwd: dir, stdio: 'inherit' });
  const out = process.argv[2] || path.join(dir, 'desert-ranger-pitch');
  const chrome = process.env.CHROME || '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary';
  const browser = await chromium.launch({ executablePath: chrome, headless: true, args: ['--allow-file-access-from-files', '--hide-scrollbars'] });
  const ctx = await browser.newContext({ viewport: { width: 816, height: 1056 }, deviceScaleFactor: 2.7 });
  const page = await ctx.newPage();
  await page.goto('file://' + path.join(dir, 'desert-ranger-pitch.html'));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(1500);
  const sheets = await page.$$('.sheet');
  if (sheets.length === 0) await page.screenshot({ path: out + '.png' });
  else for (let i = 0; i < sheets.length; i++) await sheets[i].screenshot({ path: i === 0 ? out + '.png' : out + '-status.png' });
  await page.pdf({ path: out + '.pdf', width: '8.5in', height: '11in', printBackground: true, preferCSSPageSize: true });
  console.log('rendered', sheets.length || 1, 'page(s) ->', out + '.{png,pdf}');
  await browser.close();
})();
