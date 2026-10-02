/*
 * app.js - screens, API calls and the 1-second polling loop.
 *
 * Flow:  home (create / join)  ->  lobby (host taps Start)  ->  game.
 * The server is the only source of truth; this page just polls
 * api.php?a=state about once a second and redraws.
 *
 * Seat token: create/join returns a secret token. We keep it in localStorage
 * ("dr_token_<CODE>") and the server also sets a cookie, so a refresh or
 * reopening the link puts you back in the same seat.
 */
(function () {
  'use strict';

  var Q = new URLSearchParams(location.search);
  var BOARD_MODE = Q.get('board') === '1';
  var DEBUG = Q.get('debug') === '1';
  var POLL_MS = 1000, POLL_HIDDEN_MS = 4000;

  var Clock = window.DRClock, Sound = window.DRSound;
  var $ = function (id) { return document.getElementById(id); };

  var S = {
    code: null, token: null, vehicles: {}, board: null, bv: null,
    state: null, lastEventId: 0, firstLoad: true,
    pollTimer: null, inflight: false, selVehicle: null,
    polls: 0, pollTimes: [], lastPollRtt: null
  };

  // ------------------------------------------------------------------ helpers

  function newKey() { // idempotency key for one tap
    if (window.crypto && crypto.getRandomValues) {
      var a = new Uint8Array(12); crypto.getRandomValues(a);
      return Array.prototype.map.call(a, function (b) { return ('0' + b.toString(16)).slice(-2); }).join('');
    }
    return Date.now().toString(36) + Math.random().toString(36).slice(2);
  }

  /** Call the API. GET when body is undefined. Every response is also a clock-sync sample. */
  function api(action, body, query) {
    var url = 'api.php?a=' + action + (query || '');
    var opt = { headers: {}, cache: 'no-store', credentials: 'same-origin' };
    if (S.token) opt.headers['X-Player-Token'] = S.token;
    if (body !== undefined) {
      opt.method = 'POST';
      opt.headers['Content-Type'] = 'application/json';
      opt.body = JSON.stringify(body);
    }
    var t0 = Clock.localNow();
    return fetch(url, opt).then(function (r) {
      return r.json().catch(function () { return { ok: false, error: 'Server error (' + r.status + ')' }; });
    }).then(function (j) {
      var t1 = Clock.localNow();
      if (j.serverNow) Clock.add(t0, j.serverNow, t1);
      j._rtt = t1 - t0;
      if (!j.ok) { var e = new Error(j.error || 'Something went wrong'); e.data = j; throw e; }
      return j;
    });
  }

  function show(screen) {
    ['home', 'lobby', 'game'].forEach(function (s) { $('screen-' + s).hidden = (s !== screen); });
  }

  function pieceImg(vehicle) {
    var img = document.createElement('img');
    img.src = 'assets/img/pieces/' + vehicle + '.png';
    img.alt = '';
    return img;
  }

  function playerById(id) {
    var ps = S.state ? S.state.players : [];
    for (var i = 0; i < ps.length; i++) if (ps[i].id === id) return ps[i];
    return null;
  }

  function gameUrl(extra) {
    return location.origin + location.pathname + '?g=' + S.code + (extra || '');
  }

  function rememberSeat(code, token) {
    S.code = code; S.token = token;
    localStorage.setItem('dr_token_' + code, token);
    localStorage.setItem('dr_last_code', code);
    history.replaceState(null, '', '?g=' + code + (DEBUG ? '&debug=1' : ''));
  }

  // ------------------------------------------------------------------ home

  function renderVehicles(taken) {
    var grid = $('vehicle-grid');
    grid.textContent = '';
    taken = taken || [];
    if (S.selVehicle && taken.indexOf(S.selVehicle) >= 0) S.selVehicle = null;
    Object.keys(S.vehicles).forEach(function (key) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'vehicle' + (S.selVehicle === key ? ' sel' : '');
      b.disabled = taken.indexOf(key) >= 0;
      b.appendChild(pieceImg(key));
      b.appendChild(document.createTextNode(S.vehicles[key]));
      b.onclick = function () { S.selVehicle = key; renderVehicles(taken); };
      grid.appendChild(b);
    });
  }

  function onCodeInput() {
    var code = $('in-code').value.toUpperCase().replace(/[^A-Z]/g, '');
    $('home-error').textContent = '';
    $('btn-join').hidden = code.length !== 4;
    $('btn-create').hidden = code.length > 0;
    if (code.length !== 4) { renderVehicles([]); return; }
    api('peek', undefined, '&code=' + code).then(function (j) {
      if (j.status !== 'lobby') $('home-error').textContent = 'That game has already started.';
      renderVehicles(j.taken);
    }).catch(function (e) { $('home-error').textContent = e.message; });
  }

  function homeSubmit(kind) {
    Sound.unlock(); // this tap counts as the iOS "user gesture"
    var name = $('in-name').value.trim();
    var code = $('in-code').value.toUpperCase().replace(/[^A-Z]/g, '');
    if (!name) { $('home-error').textContent = 'Please enter your name.'; return; }
    if (!S.selVehicle) { $('home-error').textContent = 'Pick your rig.'; return; }
    localStorage.setItem('dr_name', name);
    var btn = $(kind === 'create' ? 'btn-create' : 'btn-join');
    btn.disabled = true;
    api(kind, { name: name, vehicle: S.selVehicle, code: code }).then(function (j) {
      rememberSeat(j.code, j.token);
      startPolling();
    }).catch(function (e) {
      $('home-error').textContent = e.message;
      if (kind === 'join') onCodeInput();
    }).then(function () { btn.disabled = false; });
  }

  function showHome(prefillCode) {
    show('home');
    $('in-name').value = localStorage.getItem('dr_name') || '';
    $('in-code').value = prefillCode || '';
    var last = localStorage.getItem('dr_last_code');
    if (last && localStorage.getItem('dr_token_' + last) && last !== prefillCode) {
      $('resume-box').hidden = false;
      $('btn-resume').textContent = 'Resume game ' + last;
      $('btn-resume').onclick = function () { location.href = '?g=' + last + (DEBUG ? '&debug=1' : ''); };
    }
    onCodeInput();
  }

  // ------------------------------------------------------------------ polling

  function startPolling() {
    S.stopPolling = false;
    clearTimeout(S.pollTimer);
    poll();
  }

  function poll() {
    clearTimeout(S.pollTimer);
    api('state', undefined, '&code=' + S.code + '&since=' + S.lastEventId).then(function (j) {
      S.polls++;
      S.pollTimes.push(Date.now());
      S.lastPollRtt = j._rtt;
      onState(j);
      if (!S.stopPolling) S.pollTimer = setTimeout(poll, document.hidden ? POLL_HIDDEN_MS : POLL_MS);
    }).catch(function (e) {
      if (e.data && /No game/.test(e.data.error || '')) { // bad link
        localStorage.removeItem('dr_token_' + S.code);
        showHome('');
        $('home-error').textContent = 'No game with code ' + S.code + '.';
        return;
      }
      S.pollTimer = setTimeout(poll, 3000); // network blip: back off a little
    });
  }

  function onState(j) {
    var wasFirst = S.firstLoad;
    S.state = j;

    // Not seated (and not a board screen)? -> home with the code filled in.
    if (!BOARD_MODE && !j.meId) {
      S.token = null;
      S.stopPolling = true;
      if (wasFirst) showHome(j.game.code);
      return;
    }

    // New events -> log, animation, sound.
    j.events.forEach(function (ev) {
      if (ev.id <= S.lastEventId) return;
      S.lastEventId = ev.id;
      addLog(ev);
      if (wasFirst) return; // history: no replays
      if (ev.data && ev.data.steps) {
        S.bv.animate(ev.data.steps, showDie, renderGame);
        if (!BOARD_MODE && ev.data.steps.length && ev.data.steps[0].player === j.meId) {
          S.bv.scrollTo(j.meId, $('board-wrap'));
        }
      }
      if (ev.cue && ev.playAt) Sound.schedule(ev.cue, ev.playAt);
    });
    S.firstLoad = false;

    var status = j.game.status;
    if (status === 'lobby' && !BOARD_MODE) {
      show('lobby');
      renderLobby();
    } else {
      show('game');
      S.bv.setPlayers(j.players, j.game.currentId);
      renderGame();
    }
    if (wasFirst && !Sound.unlocked) $('sound-overlay').hidden = false;
  }

  // ------------------------------------------------------------------ lobby

  function renderLobby() {
    var st = S.state, me = st.meId, isHost = me === st.game.hostId;
    $('lobby-code').textContent = st.game.code;
    $('lobby-link').textContent = location.host + location.pathname;
    $('lobby-board-link').textContent = gameUrl('&board=1').replace(/^https?:\/\//, '');
    $('lobby-count').textContent = st.players.length;
    var ul = $('lobby-players');
    ul.textContent = '';
    st.players.forEach(function (p) {
      var li = document.createElement('li');
      li.appendChild(pieceImg(p.vehicle));
      li.appendChild(document.createTextNode(p.name + (p.id === me ? ' (you)' : '')));
      if (p.id === st.game.hostId) {
        var t = document.createElement('span'); t.className = 'tag'; t.textContent = 'HOST'; li.appendChild(t);
      }
      var w = document.createElement('span'); w.className = 'where'; w.textContent = S.vehicles[p.vehicle] || '';
      li.appendChild(w);
      ul.appendChild(li);
    });
    $('btn-start').hidden = !isHost;
    $('btn-start').disabled = st.players.length < 2;
    $('btn-start').textContent = st.players.length < 2 ? 'Need 2+ players' : 'Start game';
    $('lobby-wait').hidden = isHost;
  }

  // ------------------------------------------------------------------ game

  function animating() { return S.bv.busy || S.bv.queue.length > 0; }

  function renderGame() {
    var st = S.state;
    if (!st) return;
    var g = st.game, me = st.meId, cur = playerById(g.currentId);
    var mine = !BOARD_MODE && g.status === 'active' && g.currentId === me;
    var pendingMine = mine && g.pending && g.pending.playerId === me;

    $('game-code').textContent = g.code;
    var banner = $('turn-banner');
    banner.className = 'turn-banner';
    if (g.status === 'lobby') {
      banner.textContent = 'Waiting for players… join with code ' + g.code;
    } else if (g.status === 'finished') {
      var w = playerById(g.winnerId);
      banner.textContent = '🏁 ' + (w ? w.name : '?') + ' wins!';
      banner.classList.add('won');
    } else if (pendingMine) {
      banner.textContent = 'Your choice!';
      banner.classList.add('mine');
    } else if (mine) {
      banner.textContent = 'Your turn, ' + cur.name + '!';
      banner.classList.add('mine');
    } else if (cur) {
      banner.textContent = cur.name + (g.pending ? ' is deciding…' : "'s turn");
    }

    // Roll button
    var roll = $('btn-roll');
    roll.disabled = !mine || !!g.pending || S.inflight || animating();
    roll.textContent = mine && lastTurnWasRollAgain() ? 'ROLL AGAIN!' : 'ROLL';

    // Optional choices (swap / shortcut) for the active player only
    var box = $('choices');
    box.textContent = '';
    if (pendingMine && !animating()) {
      if (g.pending.type === 'shortcut') {
        addChoice(box, 'Take the shortcut to Una Palma', 'mari', { action: 'shortcut' });
        addChoice(box, 'Stay on the trail', 'sage', { action: 'skip' });
      } else if (g.pending.type === 'swap') {
        st.players.forEach(function (p) {
          if (p.id === me) return;
          addChoice(box, 'Swap with ' + p.name + ' (' + S.bv.squareName(p.pos) + ')', 'mari', { action: 'swap', target: p.id });
        });
        addChoice(box, "Don't swap", 'sage', { action: 'skip' });
      }
    }

    // Player list
    var ul = $('player-list');
    ul.textContent = '';
    st.players.forEach(function (p) {
      var li = document.createElement('li');
      if (p.id === g.currentId) li.className = 'current';
      li.appendChild(pieceImg(p.vehicle));
      li.appendChild(document.createTextNode(p.name + (p.id === me ? ' (you)' : '')));
      var wh = document.createElement('span');
      wh.className = 'where';
      wh.textContent = p.pos + ' · ' + S.bv.squareName(p.pos) + (p.skip ? ' · skips ' + p.skip : '');
      li.appendChild(wh);
      ul.appendChild(li);
    });
    $('btn-new').hidden = g.status !== 'finished';
  }

  function lastTurnWasRollAgain() {
    var items = $('log').querySelectorAll('li');
    return items.length && items[0].getAttribute('data-rollagain') === '1';
  }

  function addChoice(box, label, cls, choice) {
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'btn ' + cls;
    b.textContent = label;
    b.onclick = function () { act('choose', choice); };
    box.appendChild(b);
  }

  /** Send a roll or choice. turn + key protect against double taps / retries. */
  function act(kind, extra) {
    if (S.inflight) return;
    S.inflight = true;
    renderGame();
    var body = { code: S.code, turn: S.state.game.turn, key: newKey() };
    for (var k in extra) body[k] = extra[k];
    $('game-error').textContent = '';
    api(kind, body).catch(function (e) {
      $('game-error').textContent = e.message;
    }).then(function () {
      S.inflight = false;
      poll(); // fetch the result right away
    });
  }

  function showDie(v) {
    var d = $('die');
    d.textContent = v;
    d.classList.remove('shake');
    void d.offsetWidth; // restart the CSS animation
    d.classList.add('shake');
  }

  function addLog(ev) {
    var li = document.createElement('li');
    li.textContent = ev.msg;
    if (ev.type === 'win') li.className = 'win';
    else if (ev.cue === 'aww') li.className = 'sad';
    var ra = ev.data && ev.data.steps && ev.data.steps.some(function (s) { return s.type === 'rollAgain'; });
    li.setAttribute('data-rollagain', ra ? '1' : '0');
    var log = $('log');
    log.insertBefore(li, log.firstChild);
    while (log.children.length > 60) log.removeChild(log.lastChild);
  }

  // ------------------------------------------------------------------ debug footer

  function debugFooter() {
    var f = $('debug');
    f.hidden = false;
    setInterval(function () {
      var now = Date.now();
      S.pollTimes = S.pollTimes.filter(function (t) { return now - t < 10000; });
      f.textContent = 'clock offset ' + Math.round(Clock.offset) + ' ms · best RTT ' +
        (Clock.rtt === null ? '?' : Math.round(Clock.rtt)) + ' ms · samples ' + Clock.samples.length +
        ' · last poll ' + (S.lastPollRtt === null ? '?' : Math.round(S.lastPollRtt)) + ' ms · ' +
        (S.pollTimes.length / 10).toFixed(1) + ' polls/s · audio ' + (Sound.ctx ? Sound.ctx.state : 'locked') +
        ' (latency ' + Math.round(((Sound.ctx && Sound.ctx.outputLatency) || 0) * 1000) + ' ms) · cues played ' +
        Sound.stats.played + ' skipped ' + Sound.stats.skipped +
        (Sound.stats.lastLateMs === null ? '' : ' · last cue lead ' + (-Sound.stats.lastLateMs) + ' ms');
    }, 500);
  }

  // ------------------------------------------------------------------ start-up

  function wireUp() {
    $('in-code').addEventListener('input', onCodeInput);
    $('btn-create').onclick = function () { homeSubmit('create'); };
    $('btn-join').onclick = function () { homeSubmit('join'); };
    $('btn-start').onclick = function () {
      Sound.unlock();
      $('btn-start').disabled = true;
      api('start', { code: S.code }).catch(function (e) { $('lobby-error').textContent = e.message; }).then(poll);
    };
    $('btn-roll').onclick = function () { Sound.unlock(); act('roll', {}); };
    $('btn-sound').onclick = function () { Sound.unlock(); $('sound-overlay').hidden = true; };
    $('sound-overlay').onclick = function () { Sound.unlock(); $('sound-overlay').hidden = true; };
    $('btn-mute').onclick = function () {
      Sound.unlock();
      Sound.setMuted(!Sound.muted);
      $('btn-mute').textContent = Sound.muted ? '🔇' : '🔊';
    };
    $('btn-mute').textContent = Sound.muted ? '🔇' : '🔊';
    $('btn-zoom').onclick = function () {
      $('board').classList.toggle('zoomed');
      if (S.state && S.state.meId) setTimeout(function () { S.bv.scrollTo(S.state.meId, $('board-wrap')); }, 50);
    };
    document.addEventListener('visibilitychange', function () { if (!document.hidden && S.code) poll(); });
  }

  function init() {
    if (BOARD_MODE) document.body.classList.add('board-mode');
    wireUp();
    if (DEBUG) debugFooter();
    Clock.start();

    Promise.all([
      api('info'),
      fetch('api.php?a=board', { cache: 'no-cache' }).then(function (r) { return r.json(); })
    ]).then(function (res) {
      S.vehicles = res[0].vehicles;
      S.board = res[1];
      S.bv = new window.BoardView($('board'), S.board, S.vehicles);

      var code = (Q.get('g') || '').toUpperCase().replace(/[^A-Z]/g, '');
      if (BOARD_MODE && !code) {
        code = (prompt('Room code for the board screen?') || '').toUpperCase().replace(/[^A-Z]/g, '');
        if (code) { location.search = '?g=' + code + '&board=1'; return; }
      }
      if (code) {
        S.code = code;
        S.token = BOARD_MODE ? null : localStorage.getItem('dr_token_' + code); // cookie is the fallback
        startPolling();
      } else {
        showHome('');
      }
    }).catch(function (e) {
      document.body.textContent = 'Could not load the game: ' + e.message;
    });
  }

  init();
})();
