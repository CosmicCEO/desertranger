#!/usr/bin/env node
// Headless-Chrome check of the audio client against the mock API (no database, no config.php).
//   cd dev/e2e && npm install      (once; playwright-core)
//   node dev/audio/browser_test.js
// env: CHROME (browser binary; default Chrome Canary), ASSETS (dir holding the gitignored binaries: crowd clips, board image, fonts),
//      SHOTS (screenshot folder), PORT.  Exit code 0 = every check passed and there were zero console errors / HTTP 4xx.
'use strict';
const fs = require('fs'), os = require('os'), path = require('path');
const { chromium } = require('../e2e/node_modules/playwright-core');
const startMock = require('./mock_server');
const PORT = +process.env.PORT || 8899, BASE = 'http://127.0.0.1:' + PORT + '/desertranger/';
const CHROME = process.env.CHROME || '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary';
const ASSETS = process.env.ASSETS || path.join(os.homedir(), 'Developer/anza-borrego-challenge/desertranger');
const SHOTS = process.env.SHOTS || path.join(__dirname, '../../audio-work/shots/');
fs.mkdirSync(SHOTS, { recursive: true });
const sleep = ms => new Promise(r => setTimeout(r, ms));
let pass = 0, fail = 0;
function check(name, ok, detail) { ok ? pass++ : fail++; console.log((ok ? 'ok   ' : 'FAIL ') + name + (!ok && detail !== undefined ? '\n       ' + JSON.stringify(detail) : '')); }
const group = u => /manifest\.json/.test(u) ? 'manifest' : /assets\/audio\//.test(u) ? 'crowd' : /audio\/(radio\/fx|dice)\//.test(u) ? 'A'
  : /audio\/(radio\/(openers|places|replies)|quotes)\//.test(u) ? 'B' : /audio\/(amb|chatter)\//.test(u) ? 'C' : null;

(async () => {
  const server = await startMock(PORT, ASSETS);
  const browser = await chromium.launch({ executablePath: CHROME, headless: true, args: ['--autoplay-policy=no-user-gesture-required', '--no-sandbox'] });
  const errors = [], httpErrs = [], pages = {}, reqs = {}, inflightB = {};
  async function open(label, opts) {
    const ctx = await browser.newContext(opts), page = await ctx.newPage();
    reqs[label] = [];
    page.on('console', m => { if (m.type() === 'error') errors.push(label + ': ' + m.text()); });
    page.on('pageerror', e => errors.push(label + ' pageerror: ' + e.message));
    page.on('response', r => { if (r.status() >= 400) httpErrs.push(label + ' ' + r.status() + ' ' + r.url()); });
    inflightB[label] = { now: 0, max: 0 };
    const doneB = r => { if (group(r.url()) === 'B') inflightB[label].now--; };
    page.on('request', r => { const g = group(r.url()); if (g) reqs[label].push({ t: Date.now(), g, url: r.url() }); if (g === 'B') { const f = inflightB[label]; f.now++; f.max = Math.max(f.max, f.now); } });
    page.on('requestfinished', doneB); page.on('requestfailed', doneB);
    await page.addInitScript(() => {
      window.__rec = { at: [], turns: [], die: [], duck: [] };
      document.addEventListener('DOMContentLoaded', () => {
        const S = window.DRSound, R = window.DRRadio, C = window.DRClock, orig = S.at.bind(S);
        S.at = function (buf, serverMs, o) {
          const w = orig(buf, serverMs, o); o = o || {};
          window.__rec.at.push({ tag: o.tag || '', bus: o.bus || 'cue', serverMs: serverMs, rate: o.rate || 1, ok: !!w, dur: buf && +buf.duration.toFixed(3) });
          return w;
        };
        const onTurn = R.onTurn;
        R.onTurn = function (ev, T, tl) {
          const rec = { id: ev.id, T: T, rolls: tl.rolls, end: tl.end, cue: ev.cue, leadMs: T - C.serverNow() };
          window.__rec.turns.push(rec);
          const r = onTurn.apply(this, arguments);
          setTimeout(() => { rec.landing = R.last.text; }, 900);
          return r;
        };
        new MutationObserver(() => window.__rec.die.push({ txt: document.getElementById('die').textContent, serverMs: C.serverNow() }))
          .observe(document.getElementById('die'), { childList: true, characterData: true, subtree: true });
        setInterval(() => { if (S.bus.ambDuck) window.__rec.duck.push({ ms: C.serverNow(), amb: S.bus.ambDuck.gain.value, chat: S.bus.chatterDuck.gain.value }); }, 40);
      });
    });
    pages[label] = page;
    return page;
  }
  const phone = { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true };
  const rec = p => p.evaluate(() => window.__rec);
  const force = d => fetch(BASE + 'api.php?a=_force&dice=' + d);
  const setpos = (code, i, pos) => fetch(BASE + 'api.php?a=_setpos&code=' + code + '&i=' + i + '&pos=' + pos);
  const counts = label => reqs[label].reduce((a, r) => (a[r.g] = (a[r.g] || 0) + 1, a), {});
  async function rollAs(label, dice) {   // roll on the named page once it is that player's turn
    await force(dice);
    const p = pages[label];
    await p.waitForFunction(() => { const b = document.getElementById('btn-roll'); return b && !b.disabled; }, null, { timeout: 15000 });
    await p.click('#btn-roll');
    await sleep(7000);   // lead 1.5 s + animation + call + tail
  }
  async function turnOf(label, n) { return (await rec(pages[label])).turns[n]; }

  // ---------------------------------------------------------------- loading discipline
  const A = await open('host', phone);
  await A.goto(BASE + '?debug=1');
  await A.waitForSelector('#screen-home:not([hidden])');
  await sleep(1500);
  check('nothing audio is fetched on the home screen before the first tap', counts('host').A === undefined && counts('host').B === undefined && counts('host').crowd === undefined && counts('host').manifest === undefined, counts('host'));

  await A.tap('#in-name');   // a touch on the home screen is the audio-unlock gesture: desert sound starts on the home screen too
  let hw = 0; while (!(await A.evaluate(() => !!window.DRAmbience.state.bed)) && hw < 8000) { await sleep(250); hw += 250; }
  check('home screen: the first touch starts the background sound within ' + hw + ' ms (bed first, <= 5 s)', hw <= 5000 && await A.evaluate(() => !!window.DRAmbience.state.bed && !document.getElementById('screen-home').hidden), hw);
  await A.fill('#in-name', 'Marigold');
  await A.click('.vehicle:has(img[src*="bronco-orange"])');
  await A.click('#btn-create');
  await A.waitForSelector('#screen-lobby:not([hidden])');
  const code = (await A.textContent('#lobby-code')).trim();
  await sleep(2500);
  let c = counts('host');
  check('after the unlock tap: manifest + tier A (radio fx, dice) + crowd clips load', c.manifest >= 1 && c.A >= 10 && c.crowd >= 2, c);
  check('lobby: no tier B (the radio-call voices) yet; the background sound (tier C) may already load', !c.B, c);
  let lw = 0; while (!(await A.evaluate(() => !!window.DRAmbience.state.bed)) && lw < 8000) { await sleep(250); lw += 250; }
  check('the background sound is still playing in the LOBBY (before any game has started)', await A.evaluate(() => !!window.DRAmbience.state.bed), lw);
  check('lobby background volume defaults to 20 % (bus gain 0.28)', await A.evaluate(() => Math.abs(DRSound.bus.amb.gain.value - 0.28) < 0.01 && DRSound.settings.ambVol === 20));

  const B = await open('guest', phone);
  await B.goto(BASE + '?g=' + code + '&debug=1');
  await B.waitForSelector('#screen-home:not([hidden])');
  await B.fill('#in-name', 'Jeff');
  await sleep(400);
  await B.click('.vehicle:has(img[src*="jeep-red"])');
  await B.click('#btn-join');
  await B.waitForSelector('#screen-lobby:not([hidden])');

  const C = await open('board', { viewport: { width: 1280, height: 800 } });
  await C.goto(BASE + '?g=' + code + '&board=1&debug=1');
  await C.waitForSelector('#sound-overlay:not([hidden])');
  check('board view is silent until its audio-unlock tap (overlay shown)', !counts('board').A && !counts('board').manifest, counts('board'));
  await C.click('#btn-sound');
  await sleep(2000);
  check('board view: tier A after its tap, no radio-call voices (tier B) in the lobby', counts('board').A >= 10 && !counts('board').B, counts('board'));

  // ---------------------------------------------------------------- game starts: tiers B and C
  await A.click('#btn-start');
  await A.waitForSelector('#screen-game:not([hidden])');
  await B.waitForSelector('#screen-game:not([hidden])');
  const tStart = Date.now();
  await sleep(4000);
  c = counts('host');
  const man = JSON.parse(fs.readFileSync(path.join(__dirname, '../../desertranger/audio/manifest.json'), 'utf8')).clips;
  const wantB = Object.values(man).filter(m => ['opener', 'place', 'quotable'].includes(m.kind)).length;   // only clips that exist in the manifest are requested
  check('game active: tier B (openers, place names, quotables) is fetched - every shipped one, nothing else (' + wantB + ' clips)', c.B === wantB, { got: c.B, want: wantB });
  check('tier B is throttled: never more than 4 clips in flight at once (peak ' + inflightB.host.max + ')', inflightB.host.max >= 1 && inflightB.host.max <= 4, inflightB.host);
  const waited = 0;
  check('tier C (ambience, chatter) was fetched at the unlock tap, long before the game starts', !!counts('host').C && Date.now() - tStart < 32000, { c: counts('host') });
  await sleep(2500);
  const recA0 = await rec(A);
  check('ambience bed is playing on the phone (bed started, amb bus alive)', await A.evaluate(() => !!window.DRAmbience.state.bed), null);
  const gPhone = await A.evaluate(() => DRSound.bus.amb.gain.value), gBoard = await C.evaluate(() => DRSound.bus.amb.gain.value);
  check('board view ambience defaults +6 dB (x2) louder than a phone, both on by default', Math.abs(gBoard / gPhone - 2) < 0.02 && Math.abs(gPhone - 0.28) < 0.02, { gPhone: gPhone, gBoard: gBoard });
  await A.screenshot({ path: SHOTS + 'game-phone-390x844.png' });

  // ---------------------------------------------------------------- turn 1: plain landing, synced across devices
  await A.evaluate(() => { window.__t0 = performance.now(); });
  await rollAs('host', 4);   // 0 -> 4 (plain square)
  const rA = await rec(A), rB = await rec(B), rC = await rec(C);
  const tA = rA.turns[0], tB = rB.turns[0], tC = rC.turns[0];
  check('every device got the same turn time T', tA && tA.T === tB.T && tA.T === tC.T, [tA && tA.T, tB && tB.T, tC && tC.T]);
  check('T is stamped on this event even though it has no crowd cue', !!tA && tA.cue === null && tA.T > 0, tA);
  check('local dice shake played instantly on the roller only', rA.at.some(x => x.tag === 'shake') && !rB.at.some(x => x.tag === 'shake'));
  const dice = r => r.at.filter(x => x.tag === 'dice');
  check('dice clatter scheduled at T + roll offset (0 ms) on every device', [rA, rB, rC].every(r => dice(r).length === 1 && dice(r)[0].serverMs === tA.T + tA.rolls[0] && dice(r)[0].ok), [rA, rB, rC].map(r => dice(r)));
  check('clatter variant and pitch are identical on every device', JSON.stringify(dice(rA)[0].rate) === JSON.stringify(dice(rB)[0].rate) && dice(rA)[0].rate === dice(rC)[0].rate && Math.abs(dice(rA)[0].rate - 1) <= 0.0401, dice(rA)[0]);
  const reveal = r => r.die.find(d => d.txt === '4');
  const dev = [rA, rB, rC].map(r => reveal(r) ? reveal(r).serverMs - tA.T : null);
  check('the die is revealed at T (within 200 ms) on all three devices: animation is synced', dev.every(d => d !== null && d > -60 && d < 200), dev);
  const calls = r => r.at.filter(x => x.tag === 'call' || x.tag === 'sq');
  check('landing call timing is identical on every device (same clips, same server times)', JSON.stringify(calls(rA).map(x => [x.serverMs, x.dur])) === JSON.stringify(calls(rB).map(x => [x.serverMs, x.dur])) && JSON.stringify(calls(rA).map(x => [x.serverMs, x.dur])) === JSON.stringify(calls(rC).map(x => [x.serverMs, x.dur])), [calls(rA).length, calls(rB).length, calls(rC).length]);
  console.log('       landing on A:', tA.landing, '| calls:', calls(rA).length, '| first call at T+' + (calls(rA)[0] ? calls(rA)[0].serverMs - tA.T : '-') + ' ms (movement ends T+' + tA.end + ')');
  check('a landing call was scheduled at the end of movement (or a logged skip reason)', /^(generic|quote)/.test(tA.landing || '') ? calls(rA)[0].serverMs === tA.T + tA.end : /^skipped|^none/.test(tA.landing || ''), tA.landing);
  const maxDuck = ds => ds.reduce((m, d) => Math.min(m, d.amb), 1);
  check('ambience ducks (about -12 dB) while the call plays', maxDuck(rA.duck) < 0.4, maxDuck(rA.duck));

  // ---------------------------------------------------------------- turn 2: shortcut-free landing on 39 via _setpos (generic call at a known name)
  await setpos(code, 1, 38);
  await rollAs('guest', 1);   // 38 -> 39
  const t2 = (await rec(B)).turns[1];
  console.log('       landing on B (square 39):', t2 && t2.landing);
  check('square 39 gets a generic call naming Fish Creek (or a logged skip reason)', !!t2 && /(pl-(sr|r273)-39|^skipped)/.test(t2.landing || ''), t2 && t2.landing);

  // ---------------------------------------------------------------- turn 3: a quotable square
  await setpos(code, 0, 20);
  await rollAs('host', 2);   // 20 -> 22 (Grievance upheld: quotable q22)
  const t3 = (await rec(A)).turns[2];
  console.log('       landing on A (square 22):', t3 && t3.landing);
  check('square 22 plays its quotable line (q22), not the generic call', !!t3 && /^quote q22[ab]/.test(t3.landing || ''), t3 && t3.landing);
  check('22 sends the piece on to 32: after the quote the radio names the final square (Yaqui Pass, pl-*-32)', !!t3 && /^quote q22[ab] \+ pl-(sr|r273)-32$/.test(t3.landing || ''), t3 && t3.landing);
  const t3b = (await rec(B)).turns[2];
  check('both phones pick the same quotable', t3 && t3b && t3.landing === t3b.landing, [t3 && t3.landing, t3b && t3b.landing]);

  // ---------------------------------------------------------------- settings panel
  await A.click('#btn-audio');
  await A.waitForSelector('#audio-panel:not([hidden])');
  await A.screenshot({ path: SHOTS + 'settings-phone-390x844.png' });
  const pb = await A.evaluate(() => { const r = document.getElementById('audio-panel').getBoundingClientRect(); return { l: r.left, r: r.right, w: innerWidth }; });
  check('settings panel fits inside a 390 px phone screen', pb.l >= 0 && pb.r <= pb.w, pb);
  check('settings default: ambience on, ambience volume 20, game sounds volume 50, radio on', await A.evaluate(() => document.getElementById('set-amb').checked && document.getElementById('set-vol').value === '20' && document.getElementById('set-game-vol').value === '50' && document.getElementById('set-radio').checked));
  check('game sounds default: bus gain 0.5 (half of the mastered level)', await A.evaluate(() => Math.abs(DRSound.bus.game.gain.value - 0.5) < 1e-6 && DRSound.settings.gameVol === 50));
  await A.click('body', { position: { x: 5, y: 600 } });
  check('tapping outside closes the panel', await A.evaluate(() => document.getElementById('audio-panel').hidden));
  await A.click('#btn-audio');
  await A.fill('#set-vol', '0');
  check('volume slider drives the ambience bus (0 -> silent) and persists', await A.evaluate(() => { return new Promise(r => setTimeout(() => r(DRSound.bus.amb.gain.value < 0.01 && localStorage.getItem('dr_amb_vol') === '0'), 300)); }));
  await A.fill('#set-vol', '100');
  check('volume 100 maps to bus gain 1.4', await A.evaluate(() => new Promise(r => setTimeout(() => r(Math.abs(DRSound.bus.amb.gain.value - 1.4) < 0.02), 300))));
  await A.fill('#set-game-vol', '100');
  check('game sounds slider 100 = the mastered level (gain 1.0), saved as dr_game_vol', await A.evaluate(() => new Promise(r => setTimeout(() => r(Math.abs(DRSound.bus.game.gain.value - 1) < 0.02 && localStorage.getItem('dr_game_vol') === '100'), 300))));
  await A.fill('#set-game-vol', '0');
  check('game sounds slider 0 silences the turn-based sounds but not the ambience', await A.evaluate(() => new Promise(r => setTimeout(() => r(DRSound.bus.game.gain.value < 0.01 && DRSound.bus.amb.gain.value > 0.5), 300))));
  await A.fill('#set-game-vol', '50');
  await A.fill('#set-vol', '20');
  await A.uncheck('#set-radio');
  check('radio toggle persists (dr_radio_on = 0)', await A.evaluate(() => localStorage.getItem('dr_radio_on') === '0'));
  await A.click('body', { position: { x: 5, y: 600 } });
  const before = (await rec(A)).turns.length;
  await rollAs('guest', 3);   // turn order is host, guest, host, guest: the guest rolls now; the host phone's own setting decides what it plays
  await sleep(500);
  const rAx = await rec(A);
  const tOff = rAx.turns[before];
  console.log('       with radio chatter OFF:', tOff && tOff.landing);
  check('radio off: no landing call or quotable, but dice and crowd cue still follow the 🔊 button', !!tOff && tOff.landing === 'radio off' && rAx.at.filter(x => x.tag === 'dice' && x.serverMs >= tOff.T).length >= 1, tOff);
  await A.click('#btn-audio');
  await A.waitForSelector('#audio-panel:not([hidden])');
  await A.check('#set-radio');
  await A.uncheck('#set-amb');
  check('ambience off stops the bed independently of radio', await A.evaluate(() => new Promise(r => setTimeout(() => r(!DRAmbience.state.bed && localStorage.getItem('dr_amb_on') === '0'), 600))));
  await A.check('#set-amb');
  check('ambience back on restarts the bed', await A.evaluate(() => new Promise(r => setTimeout(() => r(!!DRAmbience.state.bed), 600))));
  await A.click('body', { position: { x: 5, y: 700 } });   // close the settings panel so it cannot cover the ROLL button

  // ---------------------------------------------------------------- the ~3 s cap, late rule, chatter, finish
  const rAll = await rec(A);
  const perTurn = rAll.turns.map(t => rAll.at.filter(x => x.tag === 'call' && x.serverMs >= t.T + t.end - 1 && x.serverMs < t.T + t.end + 3500));
  const callLen = cs => cs.length ? (cs[cs.length - 1].serverMs + cs[cs.length - 1].dur * 1000) - cs[0].serverMs : 0;
  const overCap = perTurn.map((cs, k) => { const t = rAll.turns[k], chain = /^quote q\d+[ab] \+ pl-/.test((t && t.landing) || ''); const len = callLen(cs); return len > (chain ? 5600 : 3100) ? [t && t.landing, Math.round(len)] : null; }).filter(Boolean);
  check('every landing call stays within ~3 s; a quote + the final square after a chain within 5.5 s (real clip lengths)', overCap.length === 0, overCap);
  check('a sound that is more than 250 ms late is skipped, not played out of sync', await A.evaluate(() => { const b = DRSound.buffers['dice-clatter-01']; const sk = DRSound.stats.skipped; const w = DRSound.at(b, DRClock.serverNow() - 1000, { bus: 'cue' }); return w === null && DRSound.stats.skipped === sk + 1; }));
  check('slightly late (<250 ms) still plays, starting inside the clip', await A.evaluate(() => { const b = DRSound.buffers['dice-clatter-01']; const w = DRSound.at(b, DRClock.serverNow() - 120, { bus: 'cue' }); return !!w && (w.end - w.start) < b.duration - 0.05; }));

  await sleep(11000);   // clear of this phone's own landing (chatter keeps 10 s away from a Burro Bend landing)
  await A.evaluate(() => { DRAmbience.state.landedAt = null; });
  const nAt = (await rec(A)).at.length;
  await A.evaluate(() => DRAmbience.chatterNow());
  await sleep(500);
  const ch = (await rec(A)).at.slice(nAt).filter(x => x.tag === 'chatter');
  check('background chatter plays (click + line + squelch per line) on the chatter bus', ch.length >= 3 && ch.every(x => x.bus === 'chatter' && x.ok), ch.length);
  check('chatter follows the ambience slider (0.5 x ambience volume / 60)', await A.evaluate(() => Math.abs(DRSound.bus.chatter.gain.value - 0.5 * DRSound.settings.ambVol / 60) < 1e-6));
  const ductMin = (await rec(A)).duck.reduce((m, d) => Math.min(m, d.chat), 1);
  check('chatter ducks to about -18 dB (0.126) while a game cue/call plays', ductMin < 0.2, ductMin);

  // chatter is postponed (not played over it) while a game cue/voice is scheduled in its window
  await A.evaluate(() => { const S = DRSound; S.at(S.buffers['dice-clatter-01'], DRClock.serverNow() + 300, { bus: 'voice', tag: 'probe' }); });
  const n2 = (await rec(A)).at.length;
  await A.evaluate(() => DRAmbience.chatterNow());
  await sleep(300);
  check('chatter is postponed when a cue/voice sound is scheduled in its window', (await rec(A)).at.slice(n2).filter(x => x.tag === 'chatter').length === 0);

  // a win: 49 + 6 overshoots to 51; the background sound keeps playing afterwards (it stops only when the page is left)
  await setpos(code, 0, 49); await setpos(code, 1, 49);
  await A.evaluate(() => { window.__finishAt = null; });
  await rollAs('host', 6);   // host's turn after the radio-off roll by the guest
  const fin = await A.evaluate(() => document.getElementById('turn-banner').textContent);
  check('the game finishes with a win', /wins/.test(fin), fin);
  await sleep(3000);
  check('after the win the bed, critter and chatter timers keep running (no stop timer)', await A.evaluate(() => !!DRAmbience.state.bed && !!DRAmbience.state.critterTimer && !!DRAmbience.state.chatterTimer), await A.evaluate(() => JSON.stringify({ b: !!DRAmbience.state.bed, c: !!DRAmbience.state.critterTimer, h: !!DRAmbience.state.chatterTimer })));

  // the phone pauses the audio (call, lock screen): the 'Sound paused' bar appears; when it runs again the bed restarts
  await A.evaluate(() => { window.__fake = 'interrupted'; Object.defineProperty(DRSound.ctx, 'state', { get: () => window.__fake, configurable: true }); window.__bedBefore = DRAmbience.state.bed; DRSound.ctx.onstatechange(); });
  await sleep(200);
  check('audio interrupted: the "Sound paused. Tap here to resume." bar is shown', await A.evaluate(() => !document.getElementById('sound-bar').hidden));
  await A.evaluate(() => { window.__fake = 'running'; DRSound.ctx.onstatechange(); });
  await sleep(300);
  check('audio running again: the bar is hidden and the bed was restarted', await A.evaluate(() => document.getElementById('sound-bar').hidden && !!DRAmbience.state.bed && DRAmbience.state.bed !== window.__bedBefore));
  await A.evaluate(() => { delete DRSound.ctx.state; });

  // ---------------------------------------------------------------- errors
  check('zero console errors / page errors on all pages', errors.length === 0, errors.slice(0, 8));
  check('zero HTTP 4xx/5xx responses on all pages', httpErrs.length === 0, httpErrs.slice(0, 8));
  const unavailable = []; // optional assets that were missing show up as console.warn, which is allowed
  console.log('\n' + pass + ' passed, ' + fail + ' failed');
  await browser.close(); server.close();
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('TEST CRASHED', e); process.exit(2); });
