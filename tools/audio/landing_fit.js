#!/usr/bin/env node
// Do the radio landing calls still fit with the new clip lengths?  (issue #28)
// usage: node tools/audio/landing_fit.js <old-manifest.json> <new-manifest.json> [ids,of,changed,clips]
// Loads desertranger/assets/js/radio.js against a fake window and runs the REAL planCall() with the real clip lengths from both manifests:
//  - generic call (opener + place name) for every opener 1-8 and both voices, for each changed place clip: full / place name only / skipped
//  - quote call (variant a and b) for each changed quote, and the chain follow-up (quote + final square's place name, cap CAP_CHAIN_S) where one exists
'use strict';
const fs = require('fs'), path = require('path');
const win = {};
new Function('window', fs.readFileSync(path.join(__dirname, '../../desertranger/assets/js/radio.js'), 'utf8'))(win);
const R = win.DRRadio, Q = R.QUOTABLE;
const load = f => JSON.parse(fs.readFileSync(f, 'utf8')).clips;
const OLD = load(process.argv[2]), NEW = load(process.argv[3]);
const changed = process.argv[4] ? process.argv[4].split(',') : Object.keys(NEW).filter(k => !OLD[k] || OLD[k].v !== NEW[k].v);
const mk = M => ({ dur: id => (M[id] ? M[id].sec : null), treat: id => (M[id] ? M[id].treatment : null) });
const pad2 = n => ('0' + n).slice(-2);
const plan = (M, pick, evId) => { const m = mk(M); return R.planCall(pick, evId, m.dur, m.treat); };
const describe = p => (!p ? 'SKIPPED' : p.ids.length === 1 ? 'place/quote only' : p.ids.join(' + ')) + (p ? ' ' + p.total.toFixed(2) + 's' : '');
const rows = []; let worse = 0;
for (const id of changed) {
  const mp = id.match(/^pl-(sr|r273)-(\d+)$/), mq = id.match(/^q(\d+)([ab])$/);
  if (mp) {                                    // place name: generic call at that square (if it is a generic square) and as a chain follow-up
    const voice = mp[1], sq = +mp[2];
    if (!Q[sq]) for (let op = 1; op <= 8; op++) {
      const pick = { kind: 'generic', square: sq, voice, opener: op }, evId = voice === 'sr' ? 2 * (op - 1) : 2 * (op - 1) + 1;
      const o = plan(OLD, pick, evId), n = plan(NEW, pick, evId), full = p => p && p.ids.length === 2;
      const note = (full(o) && !full(n)) ? 'WORSE: falls back' : (!o && n) ? 'better' : (o && !n) ? 'WORSE: skipped' : '';
      if (note.startsWith('WORSE')) worse++;
      rows.push([`generic sq${sq} ${voice} opener ${op}`, o && o.total, n && n.total, describe(o), describe(n), note]);
    }
    for (const qs of Object.keys(Q).map(Number)) {   // chain: any quote followed by this place name (only chains that exist in the game are 40->34, 41->12, 44->39/..., 35->39; all combinations shown for the changed place)
      if (qs === sq) continue;
      const pick = { kind: 'quote', square: qs, ids: ['q' + pad2(qs) + 'a', 'q' + pad2(qs) + 'b'], final: sq, fvoice: voice };
      const o = plan(OLD, pick, voice === 'sr' ? 0 : 1), n = plan(NEW, pick, voice === 'sr' ? 0 : 1); if (!o || !n) continue;
      const fo = o.ids.length > 1, fn = n.ids.length > 1;
      if (fo && !fn) { worse++; rows.push([`chain q${qs} -> ${sq} (${voice})`, o.total, n.total, describe(o), describe(n), 'WORSE: follow-up dropped']); }
    }
  } else if (mq) {
    const sq = +mq[1];
    for (const evId of [0, 1]) {
      const pick = { kind: 'quote', square: sq, ids: ['q' + pad2(sq) + (evId ? 'b' : 'a'), 'q' + pad2(sq) + (evId ? 'a' : 'b')] };
      const o = plan(OLD, pick, evId), n = plan(NEW, pick, evId);
      const note = (o && !n) ? 'WORSE: skipped' : (o && n && o.ids[0] !== n.ids[0]) ? 'variant order changed (first did not fit)' : '';
      if (note.startsWith('WORSE')) worse++;
      rows.push([`quote sq${sq} ev${evId} ids ${pick.ids.join('/')}`, o && o.total, n && n.total, describe(o), describe(n), note]);
    }
    if (sq === 41) for (const voice of ['sr', 'r273']) {    // 41 -> 12 is the one real chain involving a changed quote
      const pick = { kind: 'quote', square: 41, ids: ['q41a', 'q41b'], final: 12, fvoice: voice };
      const o = plan(OLD, pick, voice === 'sr' ? 0 : 1), n = plan(NEW, pick, voice === 'sr' ? 0 : 1);
      const note = (o && o.ids.length > 1 && !(n && n.ids.length > 1)) ? 'WORSE: place-name follow-up dropped' : '';
      if (note) worse++;
      rows.push([`chain q41 -> 12 (${voice})`, o && o.total, n && n.total, describe(o), describe(n), note]);
    }
  }
}
const f = x => (x == null ? '-' : x.toFixed(2));
console.log('| call | old total s | new total s | old plan | new plan | note |\n|---|---|---|---|---|---|');
rows.forEach(r => console.log(`| ${r[0]} | ${f(r[1])} | ${f(r[2])} | ${r[3]} | ${r[4]} | ${r[5]} |`));
console.log(`\n${rows.length} calls checked for ${changed.length} changed clips; ${worse} got worse (fall back to place-name-only, lose a chain follow-up, or are skipped).`);
