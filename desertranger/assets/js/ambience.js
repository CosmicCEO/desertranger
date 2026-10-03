/*
 * ambience.js - local-only desert sound: a quiet looping bed, random critter one-shots, and occasional
 * background radio chatter (Dispatch <-> R55 / Ranger 273). Never synchronized between devices.
 *
 * Starts only after the audio-unlock tap AND once the game is active; the bed, critters and chatter lines
 * are "tier C": fetched about 20 s after the game starts (or when the browser is idle), never in the lobby.
 *   bed        crossfade-looped (1.5 s equal-power) on the amb bus; ducks under cues/voice (see sync.js)
 *   critters   one every 20-60 s, random -8..0 dB, random pan, never the same twice, rattle is rare
 *   chatter    first exchange >= 90 s after unlock, then every 150-330 s; behind the "Radio chatter" toggle;
 *              postponed 20-40 s if a game cue is playing; ducked to -18 dB if one arrives mid-exchange
 * Timers stop 30 s after the game finishes.
 */
(function () {
  'use strict';

  var CRITTERS = [   // id stem -> weight; "-02" variants are picked up automatically if they exist in the manifest
    { stem: 'amb-crow', w: 1 }, { stem: 'amb-crickets', w: 1 }, { stem: 'amb-rattle', w: 0.3 },
    { stem: 'amb-coyote', w: 1 }, { stem: 'amb-quail', w: 1 }, { stem: 'amb-hawk', w: 1 }, { stem: 'amb-truck', w: 1 }
  ];
  var BURRO = { 1: true, 3: true, 6: true, 7: true };   // exchanges set at Burro Bend (tie-in: Ocotillo Wells, square 12)
  var FIRST_CHATTER_MS = 90000;
  var VOICE_AT = 0.1, SQ_GAP = 0.02;

  var st = {
    active: false, finished: false, startedC: false, unlockAt: null,
    bed: null, critterTimer: null, chatterTimer: null, stopTimer: null,
    lastCritter: null, lastExchange: null, landedAt: null, landedSq: null, hazard: false,
    nextChatterAt: null, chatterCount: 0, critterCount: 0
  };
  function snd() { return window.DRSound; }
  function rand(a, b) { return a + Math.random() * (b - a); }
  function dbToGain(db) { return Math.pow(10, db / 20); }
  function ready() { var S = snd(); return !!(S && S.ctx && S.unlocked); }

  function critterIds() {
    var S = snd(), m = S.manifest || {}, out = [];
    CRITTERS.forEach(function (c) {
      Object.keys(m).filter(function (id) { return id.indexOf(c.stem + '-') === 0 && S.buffers[id]; })
        .forEach(function (id) { out.push({ id: id, w: c.w, stem: c.stem }); });
    });
    return out;
  }
  function exchanges() {   // { n: [id, id, ...] } from the manifest, only exchanges whose lines are all loaded
    var S = snd(), m = S.manifest || {}, ex = {};
    Object.keys(m).forEach(function (id) {
      var r = /^ch(\d\d)-(\d+)$/.exec(id);
      if (r && m[id].kind === 'chatter') (ex[+r[1]] = ex[+r[1]] || []).push({ id: id, n: +r[2] });
    });
    var out = {};
    Object.keys(ex).forEach(function (k) {
      var lines = ex[k].sort(function (a, b) { return a.n - b.n; }).map(function (x) { return x.id; });
      if (lines.every(function (id) { return S.buffers[id]; })) out[k] = lines;
    });
    return out;
  }

  // ---------------------------------------------------------------- bed + critters
  function startBed() {
    var S = snd();
    if (st.bed || !ready() || !S.settings.ambOn || st.finished || !S.buffers['amb-bed-01']) return;
    st.bed = S.loopBed(S.buffers['amb-bed-01'], { bus: 'amb', gain: 1, xfade: 1.5, fadeIn: 1.5 });
    scheduleCritter();
  }
  function stopBed() {
    if (st.bed) { st.bed.stop(0.6); st.bed = null; }
    clearTimeout(st.critterTimer); st.critterTimer = null;
  }

  function scheduleCritter() {
    clearTimeout(st.critterTimer);
    if (!st.bed || st.finished) return;
    st.critterTimer = setTimeout(playCritter, rand(20, 60) * 1000);
  }
  function playCritter() {
    var S = snd();
    if (!ready() || !st.bed || st.finished) return;
    if (!document.hidden && !S.muted) {
      var pool = critterIds().filter(function (c) { return c.id !== st.lastCritter; });
      pool.forEach(function (c) { c.ww = c.w * (st.hazard && c.stem === 'amb-rattle' ? 4 : 1); });   // local tie-in: rattle near hazards
      var total = pool.reduce(function (a, c) { return a + c.ww; }, 0);
      if (total > 0) {
        var r = Math.random() * total, pick = pool[pool.length - 1];
        for (var i = 0; i < pool.length; i++) { r -= pool[i].ww; if (r <= 0) { pick = pool[i]; break; } }
        st.lastCritter = pick.id;
        st.critterCount++;
        S.at(S.buffers[pick.id], null, { bus: 'amb', gain: dbToGain(rand(-8, 0)), pan: rand(-0.8, 0.8), tag: 'critter' });
      }
    }
    scheduleCritter();
  }

  // ---------------------------------------------------------------- background chatter
  function scheduleChatter(delayMs) {
    clearTimeout(st.chatterTimer);
    if (st.finished || !st.startedC) return;
    st.nextChatterAt = Date.now() + delayMs;
    st.chatterTimer = setTimeout(tryChatter, delayMs);
  }
  function postpone(minS, maxS) { scheduleChatter(rand(minS, maxS) * 1000); }

  function tryChatter() {
    var S = snd();
    if (!ready() || st.finished) return;
    if (!S.settings.radioOn) { postpone(60, 120); return; }                 // toggle off: check again later
    if (S.muted || document.hidden) { postpone(20, 40); return; }
    var now = Date.now();
    if (st.landedAt !== null && now - st.landedAt < 10000) { scheduleChatter(10000 - (now - st.landedAt) + 500); return; }  // not on top of square 12's quotable
    var ex = exchanges(), keys = Object.keys(ex);
    if (!keys.length) { postpone(60, 120); return; }
    var nearBurro = st.landedSq === 12 && st.landedAt !== null && now - st.landedAt < 120000;
    var pool = keys.filter(function (k) { return +k !== st.lastExchange; });
    if (!pool.length) pool = keys;
    var weights = pool.map(function (k) { return nearBurro && BURRO[+k] ? 3 : 1; });
    var tot = weights.reduce(function (a, b) { return a + b; }, 0), r = Math.random() * tot, chosen = pool[pool.length - 1];
    for (var i = 0; i < pool.length; i++) { r -= weights[i]; if (r <= 0) { chosen = pool[i]; break; } }
    if (!playExchange(+chosen, ex[chosen])) { postpone(20, 40); return; }
    st.lastExchange = +chosen;
    st.chatterCount++;
    scheduleChatter(rand(150, 330) * 1000);
  }

  /** Click -> line over hiss -> squelch for each line, 350-600 ms apart. Returns false if a game cue is in the way. */
  function playExchange(n, ids) {
    var S = snd(), R = window.DRRadio;
    if (!R) return false;
    var plans = [], t = 0.15;
    ids.forEach(function (id) {
      var tr = S.trim(S.buffers[id]), voiceEnd = VOICE_AT + tr.dur;
      var plan = { radio: true, parts: [{ id: id, at: VOICE_AT }], voiceEnd: voiceEnd,
                   squelch: 'radio-squelch-0' + (1 + Math.floor(Math.random() * 3)) };
      plan.total = voiceEnd + SQ_GAP + (R.durOf(plan.squelch) || 0.22);
      plans.push({ plan: plan, at: t });
      t += plan.total + rand(0.35, 0.6);
    });
    var t0 = S.ctx.currentTime;
    if (S.busy(t0, t0 + t, false)) return false;           // a cue/voice sound is scheduled in this window: try later
    var base = window.DRClock.serverNow();
    plans.forEach(function (p) { R.playPlan(p.plan, base + p.at * 1000, 'chatter', 1, 'chatter'); });
    return true;
  }

  // ---------------------------------------------------------------- loading (tier C) and lifecycle
  function loadTierC() {
    var S = snd();
    if (st.startedC || !ready() || !st.active || st.finished) return;
    st.startedC = true;
    S.manifestReady().then(function (m) {
      var ids = Object.keys(m).filter(function (id) { return m[id].kind === 'amb' || m[id].kind === 'critter' || m[id].kind === 'chatter'; });
      ids.sort(function (a, b) { return (m[a].kind === 'amb' ? 0 : 1) - (m[b].kind === 'amb' ? 0 : 1); });   // bed first
      return S.preload(ids, 4);
    }).then(function () {
      if (S.settings.ambOn) startBed();
      var since = st.unlockAt === null ? 0 : Date.now() - st.unlockAt;
      scheduleChatter(Math.max(FIRST_CHATTER_MS - since, 5000) + rand(0, 30) * 1000);
    });
  }
  function maybeStart() {
    if (!ready() || !st.active || st.finished || st.startedC) return;
    // "20 s after start, or idle": wait for an idle moment, but never longer than 20 s.
    if (window.requestIdleCallback) window.requestIdleCallback(loadTierC, { timeout: 20000 });
    else setTimeout(loadTierC, 20000);
  }

  function setActive(on) { st.active = !!on; if (on) maybeStart(); }

  /** Game finished: let everything wind down, then stop all timers 30 s later. */
  function finish() {
    if (st.finished || st.stopTimer) return;
    st.stopTimer = setTimeout(function () {
      st.finished = true;
      stopBed();
      clearTimeout(st.chatterTimer); st.chatterTimer = null;
    }, 30000);
  }

  function noteLanding(sq) { st.landedSq = sq; st.landedAt = Date.now(); }
  function setMyPos(pos, hazard) { st.hazard = !!hazard; }

  (function hook() {
    var S = snd();
    if (!S) return;
    S.listeners.push(function () { st.unlockAt = Date.now(); maybeStart(); });
    S.settingListeners.push(function (k, v) {
      if (k === 'ambOn') { if (v) startBed(); else stopBed(); }
      if (k === 'radioOn' && v && st.startedC && !st.chatterTimer) scheduleChatter(rand(60, 120) * 1000);
    });
  })();

  window.DRAmbience = {
    setActive: setActive, finish: finish, noteLanding: noteLanding, setMyPos: setMyPos,
    chatterNow: tryChatter,   // test/debug hook: run the chatter scheduler's decision now
    state: st,
    debugLine: function () {
      return 'bed ' + (st.bed ? 'on' : 'off') + ' · critters ' + st.critterCount + ' · chatter ' + st.chatterCount +
        (st.nextChatterAt ? ' (next in ' + Math.max(0, Math.round((st.nextChatterAt - Date.now()) / 1000)) + ' s)' : '');
    }
  };
})();
