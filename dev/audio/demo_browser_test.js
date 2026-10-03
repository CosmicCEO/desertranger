#!/usr/bin/env node
// Solo demo mode in headless Chrome against a REAL server (MAMP + MySQL): one 390x844 "phone" for the demo, plus a
// second phone and a board screen for the regular-game checks.
//   cd dev/e2e && npm install      (once)
//   node dev/audio/demo_browser_test.js [baseUrl]        default http://localhost:8888/desertranger/
// env: CHROME (default Chrome Canary), SHOTS (screenshot folder). Exit code 0 = all checks passed and 0 console errors.
// (Creates a few finished test rooms in the database, like simulate_game.php.)
'use strict';
const fs = require('fs'), path = require('path');
const { chromium } = require('../e2e/node_modules/playwright-core');
const BASE = (process.argv[2] || 'http://localhost:8888/desertranger/').replace(/\/?$/, '/');
const CHROME = process.env.CHROME || '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary';
const SHOTS = process.env.SHOTS || path.join(__dirname, '../../audio-work/shots/');
fs.mkdirSync(SHOTS, { recursive: true });
const sleep = ms => new Promise(r => setTimeout(r, ms));
let pass = 0, fail = 0;
const check = (n, ok, d) => { ok ? pass++ : fail++; console.log((ok ? 'ok   ' : 'FAIL ') + n + (!ok && d !== undefined ? '\n       ' + JSON.stringify(d).slice(0, 500) : '')); };
const phone = { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true };

(async () => {
  const browser = await chromium.launch({ executablePath: CHROME, headless: true, args: ['--autoplay-policy=no-user-gesture-required', '--no-sandbox'] });
  const errors = [], httpErrs = [];
  async function open(label, opts) {
    const ctx = await browser.newContext(opts), page = await ctx.newPage();
    page.on('console', m => { if (m.type() === 'error') errors.push(label + ': ' + m.text() + ' @ ' + (m.location().url || '')); });
    page.on('pageerror', e => errors.push(label + ' pageerror: ' + e.message));
    page.on('response', r => { if (r.status() >= 400) httpErrs.push(label + ' ' + r.status() + ' ' + r.url()); });
    page.on('dialog', d => d.accept());                       // "End the demo and go back to the lobby?"
    await page.addInitScript(() => {                          // record every scheduled sound + landing pick
      window.__rec = { at: [], turns: [] };
      document.addEventListener('DOMContentLoaded', () => {
        const S = window.DRSound, R = window.DRRadio, orig = S.at.bind(S);
        S.at = function (buf, serverMs, o) { const w = orig(buf, serverMs, o); o = o || {}; window.__rec.at.push({ tag: o.tag || '', bus: o.bus || 'cue', ok: !!w }); return w; };
        const onTurn = R.onTurn;
        R.onTurn = function (ev, T, tl) { const rec = { id: ev.id, T: T }; window.__rec.turns.push(rec); const r = onTurn.apply(this, arguments); setTimeout(() => { rec.landing = R.last.text; }, 900); return r; };
      });
    });
    return page;
  }
  const rec = p => p.evaluate(() => window.__rec);
  const text = (p, sel) => p.evaluate(s => { const e = document.querySelector(s); return e ? e.textContent.trim() : null; }, sel);
  const visible = (p, sel) => p.isVisible(sel);
  async function createGame(page, name, vehicle, qs) {
    await page.goto(BASE + (qs || ''));
    await page.waitForSelector('#screen-home:not([hidden])');
    await page.fill('#in-name', name);
    await page.click(`.vehicle:has(img[src*="${vehicle}"])`);
    await page.click('#btn-create');
    await page.waitForSelector('#screen-lobby:not([hidden])');
    return (await text(page, '#lobby-code'));
  }
  /** The host's next action: roll, or answer a pending choice (take the trail, never the shortcut/swap, so the test is simple). */
  async function hostRolls(page, timeout) {
    const deadline = Date.now() + (timeout || 60000);
    while (Date.now() < deadline) {
      const choice = await page.$('#choices button');
      if (choice) { const all = await page.$$('#choices button'); await all[all.length - 1].click(); await sleep(1500); continue; }
      if (await page.isEnabled('#btn-roll')) { await page.click('#btn-roll'); return; }
      await sleep(400);
    }
    throw new Error('host never got an enabled ROLL button or a choice within ' + (timeout || 60000) + ' ms');
  }

  // ================================================================ regular game: the minimum still applies
  console.log('Regular 2-phone game on ' + BASE);
  const h1 = await open('host', phone), g1 = await open('guest', phone);
  const code1 = await createGame(h1, 'Marigold', 'bronco-orange');
  await sleep(1200);
  check('lobby, host alone: the Start button says "Need 2+ players" and is disabled', (await text(h1, '#btn-start')).toLowerCase().includes('need 2+') && await h1.isDisabled('#btn-start'));
  check('lobby, host alone: PLAY SOLO DEMO is shown, under the Start button', await visible(h1, '#btn-demo') && (await text(h1, '#btn-demo')) === 'PLAY SOLO DEMO');
  const yStart = (await h1.locator('#btn-start').boundingBox()).y, yDemo = (await h1.locator('#btn-demo').boundingBox()).y;
  check('the demo button sits below the Start button', yDemo > yStart, [yStart, yDemo]);
  await h1.screenshot({ path: SHOTS + 'lobby-demo-phone-390x844.png', fullPage: true });
  await g1.goto(BASE + '?g=' + code1);
  await g1.waitForSelector('#screen-home:not([hidden])');
  await g1.fill('#in-name', 'Jeff'); await sleep(400);
  await g1.click('.vehicle:has(img[src*="jeep-red"])');
  await g1.click('#btn-join');
  await g1.waitForSelector('#screen-lobby:not([hidden])');
  await sleep(2500);
  check('guest never sees the demo button or the Start button', !(await visible(g1, '#btn-demo')) && !(await visible(g1, '#btn-start')));
  check('host, 2 players in the lobby: demo button gone, Start enabled', !(await visible(h1, '#btn-demo')) && !(await h1.isDisabled('#btn-start')) && (await text(h1, '#btn-start')) === 'Start game');
  await h1.click('#btn-start');
  await h1.waitForSelector('#screen-game:not([hidden])'); await g1.waitForSelector('#screen-game:not([hidden])');
  await sleep(1500);
  check('regular game: no DEMO tag, no End demo button', !(await visible(h1, '#demo-tag')) && !(await visible(h1, '#btn-end-demo')) && !(await visible(g1, '#demo-tag')));
  check('regular game: no computer players', (await text(h1, '#player-list')).indexOf('computer') < 0 && (await h1.locator('#player-list li').count()) === 2);

  // ================================================================ the demo
  console.log('\nSolo demo, one phone');
  const d1 = await open('demo', phone);
  const code2 = await createGame(d1, 'Marigold', 'bronco-orange');
  await sleep(1000);
  await d1.click('#btn-demo');
  await d1.waitForSelector('#screen-game:not([hidden])');
  await sleep(1500);
  check('demo starts with only the host (no second player needed)', await visible(d1, '#screen-game'));
  check('DEMO tag is shown on the game screen', await visible(d1, '#demo-tag') && (await text(d1, '#demo-tag')) === 'DEMO');
  const names = await d1.locator('#player-list li').allTextContents();
  check('player list: Marigold (you) + 2 computer rivals', names.length === 3 && /Marigold \(you\)/.test(names[0]) && /Rival 1 \(computer\)/.test(names[1]) && /Rival 2 \(computer\)/.test(names[2]), names);
  check('End demo button shown (and not "New game")', await visible(d1, '#btn-end-demo') && (await text(d1, '#btn-end-demo')) === 'End demo' && !(await visible(d1, '#btn-new')));
  await d1.screenshot({ path: SHOTS + 'demo-game-phone-390x844.png' });

  await hostRolls(d1);                                        // the host plays; the rivals must roll by themselves
  let logTxt = '', waited = 0;
  while (!(/Rival 1/.test(logTxt) && /Rival 2/.test(logTxt)) && waited < 70000) { await sleep(1500); waited += 1500; logTxt = (await d1.locator('#log li').allTextContents()).join(' | '); }
  check('both rivals rolled by themselves (no taps) within ' + Math.round(waited / 1000) + ' s', /Rival 1 rolled/.test(logTxt) && /Rival 2 rolled/.test(logTxt), logTxt.slice(0, 300));
  let turnsPlayed = 1;
  for (let i = 0; i < 3; i++) { await hostRolls(d1, 90000); turnsPlayed++; await sleep(500); }
  await sleep(9000);
  const r = await rec(d1);
  const dice = r.at.filter(x => x.tag === 'dice' && x.ok).length;
  check('dice clatter played for the host and rival rolls (' + dice + ' clatters)', dice >= 6, dice);
  check('local dice shake played on the host\'s roll taps', r.at.filter(x => x.tag === 'shake').length >= 4);
  check('landing radio calls / quotables ran for turns in the demo (' + r.turns.map(t => t.landing).filter(Boolean).slice(0, 4).join(' ; ') + ')', r.turns.length >= 5 && r.turns.filter(t => /^(generic|quote)/.test(t.landing || '')).length >= 2, r.turns);
  check('crowd cheer/aww or ambience also behave: the ambience bed is playing', await d1.evaluate(() => !!window.DRAmbience.state.bed));
  const piecesBefore = await d1.locator('#board .piece').count();
  check('board shows the host + 2 rivals', piecesBefore === 3, piecesBefore);

  // board screen sees the demo tag, and does not drive the rivals
  const b1 = await open('board', { viewport: { width: 1280, height: 800 } });
  await b1.goto(BASE + '?g=' + code2 + '&board=1');
  await b1.waitForSelector('#sound-overlay:not([hidden])'); await b1.click('#btn-sound'); await sleep(2500);
  check('board view shows the DEMO tag and no End demo / Roll controls', await visible(b1, '#demo-tag') && !(await visible(b1, '#btn-end-demo')) && !(await visible(b1, '#btn-roll')));

  // end the demo -> same room, lobby again
  await d1.click('#btn-end-demo');
  await d1.waitForSelector('#screen-lobby:not([hidden])', { timeout: 15000 });
  await sleep(1500);
  check('End demo returns to the lobby (same room code)', (await text(d1, '#lobby-code')) === code2);
  check('lobby after the demo: 1 player, PLAY SOLO DEMO available again', (await d1.locator('#lobby-players li').count()) === 1 && await visible(d1, '#btn-demo'));
  const after = { log: await d1.locator('#log li').count(), bed: await d1.evaluate(() => !!window.DRAmbience.state.bed), pieces: await d1.locator('#board .piece').count() };
  check('game screen was reset: the log is empty', after.log === 0, after);
  check('the ambience bed stopped in the lobby', after.bed === false, after);
  check('only the host piece is left on the board', after.pieces === 1, after);
  await d1.screenshot({ path: SHOTS + 'lobby-after-demo-phone-390x844.png' });

  // restart in the same room, then finish by ending
  await d1.click('#btn-demo');
  await d1.waitForSelector('#screen-game:not([hidden])');
  await sleep(1500);
  check('the same room starts a second demo (3 pieces again)', (await d1.locator('#board .piece').count()) === 3 && await visible(d1, '#demo-tag'));
  await hostRolls(d1); await sleep(7000);
  await d1.click('#btn-end-demo');
  await d1.waitForSelector('#screen-lobby:not([hidden])', { timeout: 15000 });
  check('ending the second demo mid-game also returns to the lobby', await visible(d1, '#btn-demo'));

  // pure solo: ?demobots=0
  const s1 = await open('solo', phone);
  await createGame(s1, 'Marigold', 'bronco-orange', '?demobots=0');
  await sleep(800);
  await s1.click('#btn-demo');
  await s1.waitForSelector('#screen-game:not([hidden])'); await sleep(1500);
  check('?demobots=0: a pure solo game with just the host', (await s1.locator('#player-list li').count()) === 1 && await visible(s1, '#demo-tag'));
  await hostRolls(s1); await sleep(7000);
  const soloNames = await s1.locator('#player-list li').allTextContents();
  await hostRolls(s1, 45000);
  check('solo: the host can act again right after their own turn (nobody else to wait for)', soloNames.length === 1);

  check('zero console errors / page errors on all pages', errors.length === 0, errors.slice(0, 6));
  check('zero HTTP 4xx/5xx on all pages', httpErrs.length === 0, httpErrs.slice(0, 6));
  console.log('\n' + pass + ' passed, ' + fail + ' failed');
  await browser.close();
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('TEST CRASHED', e); process.exit(2); });
