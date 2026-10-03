// Headless Chrome end-to-end run: 3 player "phones" + 1 board screen.
// node e2e.js [baseUrl]
const { chromium } = require('playwright-core');
const BASE = process.argv[2] || 'http://localhost:8098/desertranger/';
// Chrome path and screenshot folder can be overridden with env vars.
const CHROME = process.env.CHROME || '/usr/bin/google-chrome';
const SHOTS = process.env.SHOTS || '/workspace/boardgame/proto-shots/';
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch({ executablePath: CHROME, headless: true,
    args: ['--autoplay-policy=no-user-gesture-required', '--no-sandbox'] });
  const errors = [];
  const phone = { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true };
  async function newPage(opts, label) {
    const ctx = await browser.newContext(opts);
    const page = await ctx.newPage();
    page.on('console', m => { if (m.type() === 'error') errors.push(label + ': ' + m.text()); });
    page.on('pageerror', e => errors.push(label + ' pageerror: ' + e.message));
    // Record every scheduled cue as an absolute wall-clock time (server clock).
    await page.addInitScript(() => {
      window.__cues = [];
      document.addEventListener('DOMContentLoaded', () => {
        // Crowd cues are scheduled through Sound.at (tag = cue name) since the audio build; record those.
        const S = window.DRSound, C = window.DRClock, orig = S.at.bind(S);
        S.at = (buf, playAt, o) => {
          const w = orig(buf, playAt, o);
          if (o && (o.tag === 'cheer' || o.tag === 'aww')) window.__cues.push({ name: o.tag, playAt, ok: !!w, offset: C.offset, leadMs: Math.round(playAt - C.serverNow()) });
          return w;
        };
      });
    });
    return page;
  }

  const players = [
    { name: 'Marigold', vehicle: 'bronco-orange' },
    { name: 'Jeff', vehicle: 'jeep-red' },
    { name: 'Rosa', vehicle: 'cruiser-teal' },
  ];
  const pages = [];
  for (let i = 0; i < players.length; i++) pages.push(await newPage(phone, players[i].name));

  // Host creates
  const p1 = pages[0];
  await p1.goto(BASE + '?debug=1');
  await p1.fill('#in-name', players[0].name);
  await p1.click(`.vehicle:has(img[src*="${players[0].vehicle}"])`);
  await p1.screenshot({ path: SHOTS + 'home-phone-390x844.png' });
  await p1.click('#btn-create');
  await p1.waitForSelector('#screen-lobby:not([hidden])');
  const code = (await p1.textContent('#lobby-code')).trim();
  console.log('room code', code);

  // Others join through the share link
  for (let i = 1; i < players.length; i++) {
    const p = pages[i];
    await p.goto(BASE + '?g=' + code + '&debug=1');
    await p.waitForSelector('#screen-home:not([hidden])');
    await p.fill('#in-name', players[i].name);
    await p.waitForTimeout(400); // peek of taken vehicles
    await p.click(`.vehicle:has(img[src*="${players[i].vehicle}"])`);
    await p.click('#btn-join');
    await p.waitForSelector('#screen-lobby:not([hidden])');
  }
  await sleep(1500);
  await p1.screenshot({ path: SHOTS + 'lobby-phone-390x844.png' });

  // Shared board screen
  const board = await newPage({ viewport: { width: 1280, height: 800 } }, 'board');
  await board.goto(BASE + '?g=' + code + '&board=1&debug=1');
  await board.waitForSelector('#sound-overlay:not([hidden])');
  await board.click('#btn-sound');

  await p1.click('#btn-start');
  await p1.waitForSelector('#screen-game:not([hidden])');
  for (const p of pages.slice(1)) {
    await p.waitForSelector('#screen-game:not([hidden])');
    if (await p.isVisible('#btn-sound')) await p.click('#btn-sound');
  }

  // Play a few turns: whoever has an enabled ROLL button (or a choice) taps it.
  let actions = 0;
  const t0 = Date.now();
  while (actions < 10 && Date.now() - t0 < 120000) {
    let acted = false;
    for (let i = 0; i < pages.length; i++) {
      const p = pages[i];
      const choice = await p.$('#choices button');
      if (choice) {
        await p.screenshot({ path: SHOTS + 'choice-phone-390x844.png' });
        await choice.click(); acted = true;
      } else if (await p.isEnabled('#btn-roll')) {
        await p.click('#btn-roll'); acted = true;
      }
      if (acted) { actions++; console.log('action', actions, 'by', players[i].name); break; }
    }
    await sleep(acted ? 900 : 400);
    if (actions === 4) {
      await sleep(1500); // mid-hop is fine too, but let the first ones settle
    }
  }
  await sleep(3500); // let the last animation finish

  // Resume test: reload Jeff's page; he must land back in his seat.
  const jeff = pages[1];
  const beforeYou = await jeff.textContent('#player-list');
  await jeff.reload();
  await jeff.waitForSelector('#screen-game:not([hidden])');
  await sleep(1200);
  const afterYou = await jeff.textContent('#player-list');
  console.log('resume after reload:', /Jeff \(you\)/.test(afterYou) ? 'OK (same seat)' : 'FAILED', '| before had (you):', /Jeff \(you\)/.test(beforeYou));

  // Resume test 2: clear localStorage, cookie alone must restore the seat.
  await jeff.evaluate(() => localStorage.clear());
  await jeff.reload();
  await sleep(2000);
  console.log('resume via cookie only:', /Jeff \(you\)/.test(await jeff.textContent('#player-list').catch(() => '')) ? 'OK' : 'FAILED');

  // Screenshots
  await p1.screenshot({ path: SHOTS + 'player-phone-390x844.png' });
  await p1.screenshot({ path: SHOTS + 'player-phone-390x844-full.png', fullPage: true });
  await board.screenshot({ path: SHOTS + 'board-1280x800.png' });
  await p1.click('#btn-zoom'); await sleep(800);
  await p1.screenshot({ path: SHOTS + 'player-phone-390x844-zoomed.png' });

  // Debug footers + cue timing across devices
  for (const [label, p] of [['Marigold', p1], ['Jeff', pages[1]], ['Rosa', pages[2]], ['board', board]]) {
    console.log(`[${label}] debug: ` + (await p.textContent('#debug')));
    console.log(`[${label}] cues: ` + JSON.stringify(await p.evaluate(() => window.__cues)));
  }
  console.log('log (newest first):\n  ' + (await board.$$eval('#log li', ls => ls.slice(0, 12).map(l => l.textContent))).join('\n  '));
  console.log('console errors:', errors.length ? errors : 'none');
  await browser.close();
  if (errors.length) process.exitCode = 1;   // zero console errors is part of the audio build's definition of done
})().catch(e => { console.error(e); process.exit(1); });
