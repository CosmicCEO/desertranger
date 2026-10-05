#!/usr/bin/env node
// Headless Chrome smoke test of a word-check page (issue #28): node tools/audio/word_check_smoke.js <url> <1|2>
// Opens the page, checks the cards, plays every clip (the mp3 must return 200), taps every verdict button, checks the saved results JSON, the Copy and Download buttons, and that there were no console errors.
'use strict';
const path = require('path');
const { chromium } = require(path.join(__dirname, '../../dev/e2e/node_modules/playwright-core'));
const CHROME = process.env.CHROME || '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary';
const url = process.argv[2], round = process.argv[3] || '1';
let pass = 0, fail = 0; const check = (n, ok, d) => { ok ? pass++ : fail++; console.log((ok ? 'ok   ' : 'FAIL ') + n + (!ok && d !== undefined ? ' ' + JSON.stringify(d) : '')); };
(async () => {
  const b = await chromium.launch({ executablePath: CHROME, headless: true, args: ['--autoplay-policy=no-user-gesture-required', '--no-sandbox'] });
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, permissions: ['clipboard-read', 'clipboard-write'], acceptDownloads: true }), page = await ctx.newPage();
  const errs = [], mp3 = [];
  page.on('console', m => { if (m.type() === 'error' && !/play\(\) request was interrupted/.test(m.text())) errs.push(m.text()); });   // tapping Play on the next clip interrupts the previous one: not an error page.on('pageerror', e => errs.push(e.message));
  page.on('response', r => { if (/\.mp3/.test(r.url())) mp3.push([r.url().split('/').pop(), r.status(), r.headers()['content-type']]); });
  await page.goto(url, { waitUntil: 'load' });
  const n = await page.locator('.card').count(); check('cards rendered', n > 0, n);
  check('horizontal scroll absent (phone width)', await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1));
  const plays = page.locator('.play'); const np = await plays.count(); check('play buttons', np === (round === '2' ? 2 * n : n), np);
  for (let i = 0; i < np; i++) { await plays.nth(i).click(); await page.waitForTimeout(250); }
  check('every mp3 returned 200/206 audio/mpeg (206 = browser range request)', mp3.length >= np && mp3.every(m => (m[1] === 200 || m[1] === 206) && /audio\/mpeg/.test(m[2] || '')), mp3.filter(m => (m[1] !== 200 && m[1] !== 206) || !/audio\/mpeg/.test(m[2] || '')));
  if (round === '2') { for (let i = 0; i < n; i++) await page.locator('.card').nth(i).locator([ '.b1', '.b2', '.bn' ][i % 3]).click(); }
  else { for (let i = 0; i < n; i++) await page.locator('.card').nth(i).locator(i % 2 ? '.no' : '.yes').click(); }
  const res = JSON.parse(await page.inputValue('#out')); check('results JSON has one entry per card', res.length === n, res.length);
  check('results have the right keys', res.every(r => round === '2' ? ['word', 'voice', 'choice', 'spelling1', 'spelling2'].every(k => k in r) : ['word', 'voice', 'spelling', 'verdict'].every(k => k in r)), res[0]);
  await page.reload({ waitUntil: 'load' }); check('verdicts survive a reload (localStorage)', JSON.parse(await page.inputValue('#out')).length === n);
  await page.click('#copy'); await page.waitForTimeout(300);
  const clip = await page.evaluate(() => navigator.clipboard.readText().catch(() => null)); check('Copy my results put the JSON on the clipboard', clip && JSON.parse(clip).length === n, clip && clip.slice(0, 80));
  const [dl] = await Promise.all([page.waitForEvent('download'), page.click('#dl')]); check('download file name', /word-verdicts/.test(dl.suggestedFilename()), dl.suggestedFilename());
  check('no console errors', errs.length === 0, errs);
  await page.screenshot({ path: path.join(__dirname, `../../audio-work/shots/wordcheck-round${round}.png`), fullPage: false }).catch(() => {});
  await b.close(); console.log(`${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
