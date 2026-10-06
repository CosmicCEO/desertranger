#!/usr/bin/env node
// Test double for desertranger/api.php (dev only, no dependencies, no database, no config.php).
//   node dev/audio/mock_server.js [port] [assetsFallbackDir]
// Serves desertranger/ as static files and implements the endpoints the client uses (info, board, time, peek,
// create, join, start, state, roll, choose) with a small JS port of the rules engine (move, goto, dice, loseTurn,
// rollAgain, swap, shortcut). Like the real server after hand-off 5.1, EVERY turn/win event carries playAt.
// Test hooks:  GET api.php?a=_force&dice=3,5,2        queues the next die values (otherwise random)
//              GET api.php?a=_setpos&code=ABCD&i=1&pos=38   puts player i on a square
// Binary assets that are not in git (crowd clips, board image, fonts) are served from assetsFallbackDir if given.
'use strict';
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '../../desertranger');
const BOARD = JSON.parse(fs.readFileSync(path.join(__dirname, '../../board/desert-ranger.json'), 'utf8'));
const SQ = BOARD.squares, FINISH = SQ.length - 1, LEAD_MS = 1500;
const VEHICLES = { 'bronco-orange': 'Marigold', 'scout-butter': 'Butter Scout', 'jeep-red': 'Red Rocket', 'ranger-green': 'Ranger Green',
  'buggy-blue': 'Blue Buggy', 'rail-purple': 'Purple Rail', 'cruiser-teal': 'Teal Cruiser', 'blazer-twotone': 'Two-Tone' };
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.mp3': 'audio/mpeg',
  '.jpg': 'image/jpeg', '.png': 'image/png', '.ttf': 'font/ttf', '.md': 'text/plain' };
const games = {}, forced = [];
let nextPlayer = 1, nextEvent = 1;

function die() { return forced.length ? forced.shift() : 1 + Math.floor(Math.random() * 6); }
function addEvent(g, type, msg, data, cue, force) {
  g.events.push({ id: nextEvent++, type: type, msg: msg, data: data || null, cue: cue || null,
                  playAt: (cue || force) ? Date.now() + LEAD_MS : null });
}
function range(a, b) { const out = []; if (b >= a) for (let i = a; i <= b; i++) out.push(i); else for (let i = a; i >= b; i--) out.push(i); return out; }

function resolve(g, pl, steps, out, byRoll) {
  for (let depth = 1; depth <= 8; depth++) {
    if (pl.pos >= FINISH) { pl.pos = FINISH; out.win = true; return; }
    const sq = SQ[pl.pos];
    const go = (to, kind) => { const from = pl.pos; pl.pos = Math.max(0, Math.min(FINISH, to));
      const e = { type: kind, player: pl.id, from: from, to: pl.pos }; if (kind === 'walk') e.path = range(from, pl.pos).slice(1);
      steps.push(e); if (pl.pos < from) out.setback += from - pl.pos; };
    if (sq.type === 'move') { go(pl.pos + sq.delta, 'walk'); byRoll = false; continue; }
    if (sq.type === 'goto') { go(sq.target, 'jump'); byRoll = false; continue; }
    if (sq.type === 'dice') { const r = die(); steps.push({ type: 'roll', player: pl.id, value: r, reason: 'dice' }); go(pl.pos - r, 'walk'); byRoll = false; continue; }
    if (sq.type === 'loseTurn') { pl.skip += sq.turns || 1; out.lose += sq.turns || 1; steps.push({ type: 'loseTurn', player: pl.id, turns: sq.turns || 1 }); return; }
    if (sq.type === 'rollAgain') { out.again = true; steps.push({ type: 'rollAgain', player: pl.id }); return; }
    if (sq.type === 'swap') { if (g.players.length > 1) g.pending = { type: 'swap', playerId: pl.id }; return; }
    if (sq.type === 'shortcut') { if (byRoll) g.pending = { type: 'shortcut', playerId: pl.id, target: sq.target }; return; }
    return;
  }
  steps.push({ type: 'chainGuard', player: pl.id });
}
function finish(g, pl, steps, out, text) {
  let cue = null;
  if (out.win) { g.status = 'finished'; g.winnerId = pl.id; cue = 'cheer'; }
  else if (out.again) cue = 'cheer';
  else if (out.lose || out.setback >= 5) cue = 'aww';
  addEvent(g, out.win ? 'win' : 'turn', text, { steps: steps }, cue, true);   // 5.1: first line always carries playAt
  g.turn++;
  if (g.status === 'active' && !out.again && !g.pending) {
    for (let n = 0; n < g.players.length; n++) {
      g.cur = (g.cur + 1) % g.players.length;
      const nx = g.players[g.cur];
      if (nx.skip >= 100) continue;   // sitting out (the host's choice): passed over silently
      if (nx.skip > 0) { nx.skip--; addEvent(g, 'skip', nx.name + ' skips a turn.'); } else break;
    }
  }
}
function newGame() {
  let code; do { code = ''; for (let i = 0; i < 4; i++) code += String.fromCharCode(65 + Math.floor(Math.random() * 26)); } while (games[code]);
  return (games[code] = { code: code, status: 'lobby', turn: 0, cur: 0, hostId: null, winnerId: null, pending: null, players: [], events: [] });
}
function addPlayer(g, name, vehicle) {
  let seat = 0; while (g.players.some(x => x.seat === seat)) seat++;   // first free seat (after a removal there is a gap to reuse)
  const p = { id: nextPlayer++, name: name || 'Player', vehicle: vehicle, seat: seat, pos: 0, skip: 0,
              token: Math.random().toString(16).slice(2) + Math.random().toString(16).slice(2) };
  g.players.push(p); if (g.hostId === null) g.hostId = p.id;
  addEvent(g, 'join', p.name + ' joined.');
  return p;
}
function stateOf(g, me, since) {
  const ev = since > 0 ? g.events.filter(e => e.id > since) : g.events.slice(-40);
  return { ok: true, serverNow: Date.now(),
    game: { code: g.code, status: g.status, turn: g.turn, currentId: g.status === 'active' ? g.players[g.cur].id : null,
            hostId: g.hostId, winnerId: g.winnerId, pending: g.pending ? { type: g.pending.type, playerId: g.pending.playerId } : null },
    players: g.players.map(p => ({ id: p.id, name: p.name, vehicle: p.vehicle, seat: p.seat, pos: p.pos, skip: p.skip, out: p.skip >= 100 })),
    meId: me ? me.id : null, events: ev };
}

function api(action, q, body, token, res) {
  const j = (o, s) => { o.serverNow = o.serverNow || Date.now(); res.writeHead(s || 200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' }); res.end(JSON.stringify(o)); };
  const err = (m, s) => j({ ok: false, error: m }, s || 400);
  const code = String(body.code || q.get('code') || '').toUpperCase(), g = games[code], me = g && g.players.find(p => p.token === token);
  switch (action) {
    case 'time': return j({ ok: true, t: Date.now() });
    case 'info': return j({ ok: true, vehicles: VEHICLES });
    case 'board': res.writeHead(200, { 'Content-Type': 'application/json' }); return res.end(JSON.stringify(BOARD));
    case '_force': forced.length = 0; (q.get('dice') || '').split(',').filter(Boolean).forEach(d => forced.push(+d)); return j({ ok: true, queued: forced.length });
    case '_setpos': { const gg = games[String(q.get('code') || '').toUpperCase()]; if (!gg) return err('no game', 404);
      gg.players[+q.get('i')].pos = +q.get('pos'); return j({ ok: true }); }
    case 'peek': if (!g) return err('No game with that code.', 404); return j({ ok: true, code: g.code, status: g.status, taken: g.players.map(p => p.vehicle) });
    case 'create': { const gg = newGame(), p = addPlayer(gg, body.name, body.vehicle); return j({ ok: true, code: gg.code, token: p.token }); }
    case 'join': if (!g) return err('No game with that code.', 404); { const p = addPlayer(g, body.name, body.vehicle); return j({ ok: true, code: g.code, token: p.token }); }
    case 'start': if (!g || !me) return err('Not allowed.', 403); g.status = 'active'; g.turn = 1; addEvent(g, 'start', 'Game on! ' + g.players[0].name + ' rolls first.'); return j({ ok: true });
    case 'stats': return j({ ok: true, games: Object.keys(games).filter(k => games[k].status !== 'finished').length });
    case 'nudge':   // "Knock, knock": every phone plays it at the same server time; one per 5 s
      if (!g || !me) return err('Join the game first.', 403);
      if (g.status !== 'active') return err('Knock, knock works during a game.', 409);
      if (g.lastNudge && Date.now() - g.lastNudge < 5000) return err('Easy there: wait a few seconds before knocking again.', 429);
      g.lastNudge = Date.now(); addEvent(g, 'nudge', me.name + ' knocked: knock, knock!', { from: me.id }, 'nudge-01', true); return j({ ok: true });
    case 'rematch':   // host only, finished games only: back to the lobby with the same players
      if (!g || !me || me.id !== g.hostId) return err('Only the host can start a rematch.', 403);
      if (g.status === 'lobby') return j({ ok: true });
      if (g.status !== 'finished') return err('The game is not over yet.', 409);
      g.players.forEach(p => { p.pos = 0; p.skip = 0; }); g.events = g.events.filter(e => e.type === 'join');
      g.status = 'lobby'; g.turn = 0; g.cur = 0; g.winnerId = null; g.pending = null;
      addEvent(g, 'join', 'Rematch: back in the lobby with the same players.'); return j({ ok: true });
    case 'remove': {   // host only, lobby only; frees the vehicle, renumbers seats
      if (!g || !me || me.id !== g.hostId) return err('Only the host can remove a player.', 403);
      if (g.status !== 'lobby') return err('Players can only be removed before the game starts.', 409);
      const t = g.players.find(p => p.id === +body.playerId); if (!t) return j({ ok: true });
      if (t.id === g.hostId) return err('The host cannot be removed.', 409);
      g.players.splice(g.players.indexOf(t), 1); g.players.forEach(p => { if (p.seat > t.seat) p.seat--; });
      addEvent(g, 'removed', t.name + ' was removed by the host.'); return j({ ok: true }); }
    case 'skip': {     // host only: pass the turn on without the current player acting
      if (!g || !me || me.id !== g.hostId) return err('Only the host can skip a turn.', 403);
      if (g.status !== 'active') return err('The game is not in progress.', 409);
      if (+body.turn !== g.turn) return err('That turn already happened.', 409);
      if (!g.players.some((p, i) => i !== g.cur && p.skip < 100)) return err('There is nobody else to hand the turn to.', 409);
      const was = g.players[g.cur]; g.pending = null; g.turn++;
      for (let n = 0; n < g.players.length; n++) { g.cur = (g.cur + 1) % g.players.length; const nx = g.players[g.cur];
        if (nx.skip >= 100) continue; if (nx.skip > 0) { nx.skip--; continue; } break; }
      addEvent(g, 'hostskip', was.name + ' was skipped by the host.'); return j({ ok: true }); }
    case 'sitout': {   // host only: a player's turns pass silently until the host brings them back
      if (!g || !me || me.id !== g.hostId) return err('Only the host can make a player sit out.', 403);
      if (g.status !== 'active') return err('The game is not in progress.', 409);
      const t = g.players.find(p => p.id === +body.playerId); if (!t) return err('No such player.', 404);
      const on = !!body.on; if (on && t.id === g.hostId) return err('The host cannot sit out.', 409);
      if (on === (t.skip >= 100)) return j({ ok: true });
      t.skip = on ? 100 : 0;
      if (on && g.players[g.cur] === t) { g.pending = null; g.turn++; for (let n = 0; n < g.players.length; n++) { g.cur = (g.cur + 1) % g.players.length; if (g.players[g.cur].skip < 100) break; } }
      addEvent(g, 'sitout', t.name + (on ? ' is sitting out.' : ' is back in the game.')); return j({ ok: true }); }
    case 'state': if (!g) return err('No game with that code.', 404); return j(stateOf(g, me, +(q.get('since') || 0)));
    case 'roll': case 'choose': {
      if (!g || !me) return err('You are not in this game.', 403);
      if (g.status !== 'active') return err('The game is not in progress.', 409);
      if (+body.turn !== g.turn) return err('That turn already happened.', 409);
      if (g.players[g.cur].id !== me.id) return err("It's not your turn.", 409);
      const steps = [], out = { win: false, again: false, lose: 0, setback: 0 };
      if (action === 'roll') {
        if (g.pending) return err('Make your choice first.', 409);
        const d = die(), from = me.pos; steps.push({ type: 'roll', player: me.id, value: d });
        me.pos = Math.min(FINISH, from + d); steps.push({ type: 'walk', player: me.id, from: from, to: me.pos, path: range(from, me.pos).slice(1) });
        resolve(g, me, steps, out, true);
        return finish(g, me, steps, out, me.name + ' rolled ' + d + ' -> ' + SQ[me.pos].name), j({ ok: true, duplicate: false });
      }
      const pend = g.pending; if (!pend) return err('Nothing to choose.', 409); g.pending = null;
      if (body.action === 'shortcut' && pend.type === 'shortcut') { const from = me.pos; me.pos = pend.target; steps.push({ type: 'jump', player: me.id, from: from, to: me.pos, reason: 'shortcut' }); resolve(g, me, steps, out, false); }
      else if (body.action === 'swap' && pend.type === 'swap') { const o = g.players.find(p => p.id === +body.target); if (o) { const a = me.pos, b = o.pos; me.pos = b; o.pos = a; steps.push({ type: 'swap', player: me.id, other: o.id, playerTo: b, otherTo: a }); } }
      finish(g, me, steps, out, me.name + ' chose: ' + body.action);
      return j({ ok: true, duplicate: false });
    }
    default: return err('Unknown action.', 404);
  }
}

function serve(req, res, fallback) {
  const u = new URL(req.url, 'http://x');
  if (u.pathname.endsWith('/api.php')) {
    let raw = ''; req.on('data', c => raw += c);
    return req.on('end', () => { let body = {}; try { body = raw ? JSON.parse(raw) : {}; } catch (e) { /* ignore */ }
      api(u.searchParams.get('a'), u.searchParams, body, req.headers['x-player-token'] || null, res); });
  }
  let rel = decodeURIComponent(u.pathname.replace(/^\/desertranger\/?/, '')) || 'index.html';
  if (rel.endsWith('/')) rel += 'index.html';
  const tries = [path.join(ROOT, rel)]; if (fallback) tries.push(path.join(fallback, rel));
  for (const f of tries) {
    if (!f.startsWith(ROOT) && !(fallback && f.startsWith(fallback))) continue;
    if (/config\.php/i.test(f)) break;                       // never serve a config file, even by accident
    if (fs.existsSync(f) && fs.statSync(f).isFile()) {
      res.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream', 'Cache-Control': 'no-cache' });
      return fs.createReadStream(f).pipe(res);
    }
  }
  res.writeHead(404); res.end('not found');
}

module.exports = function start(port, fallback) {
  const server = http.createServer((req, res) => serve(req, res, fallback));
  return new Promise(ok => server.listen(port, '127.0.0.1', () => ok(server)));
};
if (require.main === module) {
  const port = +process.argv[2] || 8899;
  module.exports(port, process.argv[3]).then(() => console.log('mock desertranger on http://127.0.0.1:' + port + '/desertranger/'));
}
