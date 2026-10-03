#!/usr/bin/env node
// Plain-Node test (no dependencies) for desertranger/assets/js/radio.js:  node dev/audio/landing_test.js
// Loads radio.js against a fake `window` and checks pickLanding() (which clip a landing gets) and planCall()
// (the ~3 s cap) using fake clip lengths. Exit code 0 = all pass.
'use strict';
const fs = require('fs'), path = require('path');
const win = {};
new Function('window', fs.readFileSync(path.join(__dirname, '../../desertranger/assets/js/radio.js'), 'utf8'))(win);
const R = win.DRRadio, Q = R.QUOTABLE;
let pass = 0, fail = 0;
function eq(name, got, want) {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  ok ? pass++ : fail++;
  console.log((ok ? 'ok   ' : 'FAIL ') + name + (ok ? '' : '\n       got  ' + JSON.stringify(got) + '\n       want ' + JSON.stringify(want)));
}
const roll = (p, v) => ({ type: 'roll', player: p, value: v });
const walk = (p, from, to) => ({ type: 'walk', player: p, from: from, to: to, path: [] });
const jump = (p, from, to) => ({ type: 'jump', player: p, from: from, to: to });
const ev = (id, steps, type) => ({ id: id, type: type || 'turn', data: { steps: steps } });
const quote = (sq, v) => ({ kind: 'quote', square: sq, ids: ['q' + ('0' + sq).slice(-2) + v, 'q' + ('0' + sq).slice(-2) + (v === 'a' ? 'b' : 'a')] });

// ---- quotable set matches docs/audio-lines.json ----
const lines = JSON.parse(fs.readFileSync(path.join(__dirname, '../../docs/audio-lines.json'), 'utf8'));
eq('quotable set == audio-lines.json squares[].quotable',
   Object.keys(Q).map(Number).sort((a, b) => a - b),
   lines.squares.filter(s => s.quotable).map(s => s.square).sort((a, b) => a - b));

// ---- pickLanding: the cases in hand-off 5.4 ----
eq('plain roll onto a generic square (even id) -> Senior Ranger, opener from id', R.pickLanding(ev(10, [roll(1, 3), walk(1, 4, 7)]), Q),
   { kind: 'generic', square: 7, voice: 'sr', opener: 1 + (5 % 8) });
eq('plain roll onto a generic square (odd id) -> Ranger 273', R.pickLanding(ev(11, [roll(1, 3), walk(1, 4, 7)]), Q),
   { kind: 'generic', square: 7, voice: 'r273', opener: 1 + (5 % 8) });
eq('shortcut jump (choose -> 33) gives a generic call at 33', R.pickLanding(ev(20, [jump(2, 18, 33)]), Q),
   { kind: 'generic', square: 33, voice: 'sr', opener: 1 + (10 % 8) });
eq('roll landing on 6 plays q06 (even id -> variant a first)', R.pickLanding(ev(30, [roll(1, 2), walk(1, 4, 6)]), Q), quote(6, 'a'));
eq('roll landing on 31 plays q31 (odd id -> variant b first)', R.pickLanding(ev(31, [roll(1, 5), walk(1, 26, 31)]), Q), quote(31, 'b'));
eq('overshoot win plays q51', R.pickLanding(ev(40, [roll(3, 6), walk(3, 49, 51)], 'win'), Q), quote(51, 'a'));
eq('40 -> 34 plays q40, not the Court line', R.pickLanding(ev(42, [roll(1, 4), walk(1, 36, 40), jump(1, 40, 34)]), Q), quote(40, 'a'));
eq('44, back 3 -> 41 -> 12 plays q41', R.pickLanding(ev(44, [roll(1, 2), walk(1, 42, 44), roll(1, 3), walk(1, 44, 41), jump(1, 41, 12)]), Q), quote(41, 'a'));
eq('44, back 5 -> 39 plays q44', R.pickLanding(ev(44, [roll(1, 2), walk(1, 42, 44), roll(1, 5), walk(1, 44, 39)]), Q), quote(44, 'a'));
eq('swap choice plays nothing new', R.pickLanding(ev(50, [{ type: 'swap', player: 1, other: 2, playerTo: 9, otherTo: 31 }]), Q), null);
eq('"decided not to swap" (no moves) plays nothing', R.pickLanding(ev(52, []), Q), null);
eq('only loseTurn/skipped steps plays nothing', R.pickLanding(ev(54, [{ type: 'skipped', player: 1 }]), Q), null);
eq('steps by another player (swap partner) are ignored for the mover', R.pickLanding(ev(56, [roll(1, 2), walk(1, 4, 6), walk(2, 9, 12)]), Q), quote(6, 'a'));
eq('same event -> same pick every time (deterministic)', R.pickLanding(ev(77, [roll(1, 2), walk(1, 4, 6)]), Q), R.pickLanding(ev(77, [roll(1, 2), walk(1, 4, 6)]), Q));

// ---- planCall: the ~3 s cap with fake durations ----
const dur = (table) => (id) => table[id] == null ? null : table[id];
const rad = () => 'radio';
const SQ = 0.22;   // squelch tail length used by the fake clips
function d(t) { t['radio-squelch-01'] = t['radio-squelch-02'] = t['radio-squelch-03'] = SQ; return dur(t); }
const near = (a, b) => Math.abs(a - b) < 1e-6;

let p = R.planCall(quote(41, 'a'), 44, d({ q41a: 2.0, q41b: 2.4 }), rad);
eq('quote that fits: first variant, with click offset and squelch', p && [p.ids, near(p.parts[0].at, 0.1), near(p.total, 0.1 + 2.0 + 0.02 + SQ), p.radio], [['q41a'], true, true, true]);
p = R.planCall(quote(41, 'a'), 44, d({ q41a: 3.4, q41b: 2.4 }), rad);
eq('first variant too long -> the other one is used', p && p.ids, ['q41b']);
p = R.planCall(quote(41, 'a'), 44, d({ q41a: 3.4, q41b: 3.1 }), rad);
eq('neither fits -> the shorter one still plays', p && p.ids, ['q41b']);
p = R.planCall(quote(41, 'a'), 44, d({ q41b: 2.4 }), rad);
eq('first variant missing -> the other one', p && p.ids, ['q41b']);
p = R.planCall(quote(41, 'a'), 44, d({}), rad);
eq('both variants missing -> no call (silence, no error)', p, null);
p = R.planCall(quote(51, 'a'), 44, d({ q51a: 2.0, q51b: 2.0 }), () => 'crowd');
eq('crowd/clean quote plays dry: no click, no squelch', p && [p.radio, p.parts[0].at, near(p.total, 2.0)], [false, 0, true]);

const gen = { kind: 'generic', square: 39, voice: 'sr', opener: 3 };
p = R.planCall(gen, 10, d({ 'op-sr-03': 1.2, 'pl-sr-39': 0.9 }), rad);
eq('generic: opener + place with a 60 ms gap, total under the cap', p && [p.ids, near(p.parts[1].at, 0.1 + 1.2 + 0.06), p.total <= 3.0], [['op-sr-03', 'pl-sr-39'], true, true]);
p = R.planCall(gen, 10, d({ 'op-sr-03': 1.9, 'op-sr-04': 1.1, 'pl-sr-39': 0.9 }), rad);
eq('generic: opener too long -> next opener tried', p && p.ids, ['op-sr-04', 'pl-sr-39']);
p = R.planCall({ kind: 'generic', square: 39, voice: 'sr', opener: 8 }, 10, d({ 'op-sr-08': 1.9, 'op-sr-01': 1.0, 'pl-sr-39': 0.9 }), rad);
eq('generic: openers wrap around after 8', p && p.ids, ['op-sr-01', 'pl-sr-39']);
p = R.planCall(gen, 10, d({ 'op-sr-03': 2.5, 'op-sr-04': 2.5, 'op-sr-05': 2.5, 'op-sr-06': 2.5, 'op-sr-07': 2.5, 'op-sr-08': 2.5, 'op-sr-01': 2.5, 'op-sr-02': 2.5, 'pl-sr-39': 0.9 }), rad);
eq('generic: no opener fits -> place name alone', p && p.ids, ['pl-sr-39']);
p = R.planCall(gen, 10, d({ 'pl-sr-39': 3.0 }), rad);
eq('generic: even the place alone is over the cap -> skip', p, null);
p = R.planCall(gen, 10, d({ 'op-sr-03': 1.0 }), rad);
eq('generic: place clip missing -> skip', p, null);
p = R.planCall(gen, 10, d({ 'op-sr-03': 1.2, 'pl-sr-39': 0.9, 'op-sr-04': 0.5 }), rad);
eq('squelch variant follows the event id', p && p.squelch, 'radio-squelch-0' + (1 + 10 % 3));
eq('planCall(null) -> null', R.planCall(null, 1, d({}), rad), null);

console.log('\n' + pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
