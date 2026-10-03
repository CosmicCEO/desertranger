#!/usr/bin/env node
// Phase 6.2: open desertranger/audio/review.html in headless Chrome and check every shipped clip.
//   node dev/audio/review_check.js        (needs dev/e2e `npm install`; serves the repo through dev/audio/mock_server.js)
// - every clip in manifest.json fetches (200) and decodes through Web Audio, and its decoded length matches the manifest
// - no clip is clipped at full scale after decoding
// - the page has one play button per clip, and every stitched landing-call demo button runs without an error
'use strict';
const fs = require('fs'), path = require('path');
const { chromium } = require('../e2e/node_modules/playwright-core');
const startMock = require('./mock_server');
const PORT = +process.env.PORT || 8897;
const CHROME = process.env.CHROME || '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary';
let pass = 0, fail = 0;
const check = (n, ok, d) => { ok ? pass++ : fail++; console.log((ok ? 'ok   ' : 'FAIL ') + n + (!ok && d !== undefined ? '\n       ' + JSON.stringify(d).slice(0, 600) : '')); };
(async () => {
  const server = await startMock(PORT, null);
  const browser = await chromium.launch({ executablePath: CHROME, headless: true, args: ['--autoplay-policy=no-user-gesture-required', '--no-sandbox'] });
  const page = await (await browser.newContext()).newPage(), errors = [], http = [];
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text() + ' @ ' + (m.location().url || '?')); });
  page.on('response', r => { if (r.status() >= 400) http.push(r.status() + ' ' + r.url()); });
  await page.goto('http://127.0.0.1:' + PORT + '/desertranger/audio/review.html');
  const man = JSON.parse(fs.readFileSync(path.join(__dirname, '../../desertranger/audio/manifest.json'), 'utf8')).clips;
  const n = Object.keys(man).length;
  check('review page lists a play button for every clip (' + n + ')', (await page.$$('button[data-src]')).length === n, (await page.$$('button[data-src]')).length);
  const r = await page.evaluate(async () => {
    ctx = ctx || new (window.AudioContext || window.webkitAudioContext)();
    const bad = [], clipped = [], off = [];
    for (const id of Object.keys(M)) {
      try {
        const b = await buf(id), d = b.getChannelData(0);
        let pk = 0; for (let i = 0; i < d.length; i++) { const a = Math.abs(d[i]); if (a > pk) pk = a; }
        if (pk >= 0.999) clipped.push(id);
        if (Math.abs(b.duration - M[id].sec) > 0.12) off.push([id, +b.duration.toFixed(3), M[id].sec]);
      } catch (e) { bad.push(id + ': ' + e); }
    }
    return { bad, clipped, off };
  });
  check('every clip fetches and decodes', r.bad.length === 0, r.bad);
  check('decoded length matches the manifest (within 120 ms: MP3 encoder padding)', r.off.length === 0, r.off);
  check('no clip is clipped at full scale after decoding', r.clipped.length === 0, r.clipped);
  const demos = await page.$$('button[onclick^="stitch("]');
  for (const d of demos) { await d.click(); await page.waitForTimeout(150); }
  await page.waitForTimeout(4000);
  check('all ' + demos.length + ' stitched landing-call demo buttons ran without an error', demos.length >= 12 && errors.length === 0, errors.slice(0, 5));
  check('no HTTP 4xx/5xx', http.length === 0, http.slice(0, 5));
  console.log('\n' + pass + ' passed, ' + fail + ' failed');
  await browser.close(); server.close();
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('CRASHED', e); process.exit(2); });
