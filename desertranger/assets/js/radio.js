/*
 * radio.js - per-turn audio on top of sync.js: dice clatter, the landing radio call (or a square's
 * quotable line), and when the crowd cue plays.
 *
 * Every device computes the same thing from the same server event:
 *   T = ev.playAt (server ms, stamped on every turn event) is when the turn animation starts everywhere.
 *   BoardView.timeline(steps) gives the offsets of each die reveal and of the end of movement.
 *   dice clatter  -> T + roll offset                  (cue bus, not affected by the radio toggle)
 *   landing call  -> T + end of movement              (voice bus; skipped if another cue is playing)
 *   crowd cue     -> end of the call minus 150 ms, or T + end of movement when there is no call
 * pickLanding() uses only shared inputs (event id, step list, the quotable-square set), so every device
 * picks the same clip. The ~3 s cap is applied with the real clip lengths.
 * After a chain (a move/goto/shortcut square that carries the piece on) a quotable line is followed by the short
 * place name of the square the piece finally stops on ("Fish Creek"); that follow-up may stretch the call to
 * CAP_CHAIN_S, and is dropped if it would not fit.
 */
(function () {
  'use strict';

  var SYNC_ANIM = true;       // align the turn animation start to T; false = animate on arrival (audio still uses T)
  var CAP_S = 3.0;            // longest landing call: click + clips + squelch
  var CAP_CHAIN_S = 5.5;      // longest call when a quote is followed by the final square's place name (a chain)
  var FOLLOW_GAP_S = 0.3;     // pause between a dry (clean) quote and the radio place-name follow-up
  var VOICE_AT = 0.1;         // voice starts this long after the key-up click
  var GAP_S = 0.06;           // between opener and place name
  var SQ_GAP = 0.02;          // voice end -> squelch tail
  var LATE_MS = 250;
  var HISS_GAIN = 0.5;

  // Squares with a dedicated character line (docs/audio-lines.json "squares" where quotable = true).
  var QUOTABLE = {};
  [1, 3, 6, 9, 12, 14, 16, 22, 23, 26, 27, 28, 29, 30, 31, 34, 35, 36, 40, 41, 42, 44, 46, 48, 49, 50, 51]
    .forEach(function (n) { QUOTABLE[n] = true; });

  function pad2(n) { return ('0' + n).slice(-2); }
  function snd() { return window.DRSound; }

  /**
   * Pure: which landing audio does this turn event get?  ev = {id, type, data: {steps}}, Q = quotable set.
   * -> null | {kind:'quote', square, ids:[preferred, other variant], final?, fvoice?} | {kind:'generic', square, voice, opener}
   *    (final/fvoice: the square a chain ended on and the voice for its place name, only when it differs from `square`)
   */
  function pickLanding(ev, Q) {
    var steps = (ev.data && ev.data.steps) || [], mover = null, first = null, fin = null, seen = [];
    if (steps.some(function (s) { return s.type === 'swap'; })) return null;      // swap choice: HR line already played on 31
    steps.forEach(function (s) {
      if (s.type === 'roll' && mover === null) mover = s.player;
      if ((s.type === 'walk' || s.type === 'jump') && (mover === null || s.player === mover)) {
        if (mover === null) mover = s.player;
        if (first === null) first = s.to;
        fin = s.to; seen.push(s.to);
      }
    });
    if (first === null) return null;                     // "decided not to swap" / "stayed on the trail"
    var sq = ev.type === 'win' ? 51 : first;             // resolve chains BEFORE choosing: 41->12 uses 41's line
    if (first === 44) for (var k = 1; k < seen.length; k++)   // 44: use the final roll-back outcome's quotable, if any
      if (Q[seen[k]] && seen[k] !== 44) { sq = seen[k]; break; }
    var v = ev.id % 2 ? 'b' : 'a';
    var voice = ev.id % 2 ? 'r273' : 'sr';               // alternate Senior Ranger / Ranger 273; never Dispatch
    if (Q[sq]) {
      var qp = { kind: 'quote', square: sq, ids: ['q' + pad2(sq) + v, 'q' + pad2(sq) + (v === 'a' ? 'b' : 'a')] };
      if (fin !== null && fin !== sq) { qp.final = fin; qp.fvoice = voice; }   // a chain moved the piece on: name where it ended up
      return qp;
    }
    return { kind: 'generic', square: fin, voice: voice, opener: 1 + (Math.floor(ev.id / 2) % 8) };
  }

  /**
   * Pure: turn a pick into a timed plan that fits CAP_S, using real clip lengths.
   * durOf(id) -> trimmed seconds, or null if the clip is missing; treatOf(id) -> 'radio' | 'clean' | 'crowd'.
   * -> null | {ids, radio, squelch, parts:[{id, at}], voiceEnd, total}   (seconds from the start of the call)
   */
  function planCall(pick, evId, durOf, treatOf) {
    if (!pick) return null;
    var sq = 'radio-squelch-0' + (1 + evId % 3);
    function build(ids, radio) {
      for (var i = 0; i < ids.length; i++) if (durOf(ids[i]) == null) return null;
      var t = radio ? VOICE_AT : 0, parts = [];
      ids.forEach(function (id, n) { if (n) t += GAP_S; parts.push({ id: id, at: t }); t += durOf(id); });
      var voiceEnd = t;
      if (radio) t += SQ_GAP + (durOf(sq) || 0.22);
      return { ids: ids, radio: radio, squelch: sq, parts: parts, voiceEnd: voiceEnd, total: t };
    }
    // After a chain: append "<place name of the final square>" when the whole call still fits CAP_CHAIN_S.
    // A radio quote just continues the same transmission; a dry quote is followed by its own short radio transmission.
    function withFollow(c) {
      if (pick.final == null) return c;
      var pl = 'pl-' + pick.fvoice + '-' + pad2(pick.final), dp = durOf(pl);
      if (dp == null) return c;
      var at, voiceEnd, follow = null;
      if (c.radio) { at = c.voiceEnd + GAP_S; }
      else { var ck = c.voiceEnd + FOLLOW_GAP_S; at = ck + VOICE_AT; follow = { clickAt: ck }; }
      voiceEnd = at + dp;
      var total = voiceEnd + SQ_GAP + (durOf(sq) || 0.22);
      if (total > CAP_CHAIN_S) return c;
      var out = { ids: c.ids.concat([pl]), radio: c.radio, squelch: sq, parts: c.parts.concat([{ id: pl, at: at }]), voiceEnd: voiceEnd, total: total };
      if (follow) { follow.voiceEnd = voiceEnd; out.follow = follow; }
      return out;
    }
    var c, best = null;
    if (pick.kind === 'quote') {            // first variant that fits; if neither does, the shorter one
      for (var k = 0; k < pick.ids.length; k++) {
        c = build([pick.ids[k]], treatOf(pick.ids[k]) === 'radio');
        if (!c) continue;
        if (c.total <= CAP_S) return withFollow(c);
        if (!best || c.total < best.total) best = c;
      }
      return best ? withFollow(best) : null;
    }
    var pl = 'pl-' + pick.voice + '-' + pad2(pick.square);
    for (var j = 0; j < 8; j++) {           // try the next openers (wrapping) until opener + place fits
      c = build(['op-' + pick.voice + '-' + pad2(((pick.opener - 1 + j) % 8) + 1), pl], true);
      if (c && c.total <= CAP_S) return c;
    }
    c = build([pl], true);                  // place name alone
    return c && c.total <= CAP_S ? c : null;
  }

  /** Every clip id a pick might need (so they can all be loaded before planning). */
  function idsFor(pick, evId) {
    var ids = ['radio-click-01', 'radio-squelch-0' + (1 + evId % 3)];
    if (pick.kind === 'quote') {
      if (pick.final != null) ids.push('pl-' + pick.fvoice + '-' + pad2(pick.final));
      return ids.concat(pick.ids);
    }
    ids.push('pl-' + pick.voice + '-' + pad2(pick.square));
    for (var o = 1; o <= 8; o++) ids.push('op-' + pick.voice + '-' + pad2(o));
    return ids;
  }

  var last = { text: '-' };
  function setLast(t) { last.text = t; }
  function withClip(id, fn) {
    var S = snd();
    if (!S || !S.ctx) return;
    if (S.buffers[id]) fn(S.buffers[id]); else S.clip(id).then(function (b) { if (b) fn(b); });
  }
  function durOf(id) { var S = snd(), b = S.buffers[id]; return b ? S.trim(b).dur : null; }
  function treatOf(id) { var m = snd().manifest; return m && m[id] ? m[id].treatment : 'clean'; }

  /** Schedule a plan: click, voice clips over a looped hiss, squelch. baseMs = server ms of the call start. */
  function playPlan(plan, baseMs, bus, gain, tag) {
    var S = snd(), wins = [];
    function put(id, atSec, extra) {
      var b = S.buffers[id];
      if (!b) return null;
      var tr = S.trim(b), o = { bus: bus, offset: tr.off, duration: tr.dur, gain: gain, tag: tag };
      for (var k in extra) o[k] = extra[k];
      var w = S.at(b, baseMs + atSec * 1000, o);
      if (w) wins.push(w);
      return w;
    }
    if (plan.radio) {
      put('radio-click-01', 0);
      var hiss = S.buffers['radio-hiss-loop'], t0 = S.ctxTimeFor(baseMs);
      if (hiss && !S.muted) S.loopBed(hiss, { bus: bus, gain: HISS_GAIN * (gain || 1), xfade: 0.2, fadeIn: 0.03, startAt: t0, endAt: t0 + plan.voiceEnd });
    }
    plan.parts.forEach(function (p) { put(p.id, p.at); });
    if (plan.radio) put(plan.squelch, plan.voiceEnd + SQ_GAP);
    if (plan.follow) {   // a dry quote, then its own short radio transmission with the final place name
      var f = plan.follow, hiss2 = S.buffers['radio-hiss-loop'], t1 = S.ctxTimeFor(baseMs + f.clickAt * 1000);
      put('radio-click-01', f.clickAt);
      if (hiss2 && !S.muted) S.loopBed(hiss2, { bus: bus, gain: HISS_GAIN * (gain || 1), xfade: 0.2, fadeIn: 0.03, startAt: t1, endAt: t1 + (f.voiceEnd - f.clickAt) });
      put(plan.squelch, f.voiceEnd + SQ_GAP);
    }
    return wins;
  }

  /** Called by app.js for every NEW turn event that has steps. T = ev.playAt, tl = BoardView.timeline(steps). */
  function onTurn(ev, T, tl) {
    var S = snd();
    if (!S || !S.ctx || !S.unlocked) return;
    if (S.lateBy(T) > LATE_MS) { S.stats.skipped++; setLast('skipped: late'); return; }   // hidden tab etc.: animate, no audio

    // Dice: one clatter per die reveal, deterministic variant + ±4 % pitch so every device matches.
    (tl.rolls || []).forEach(function (off, i) {
      var id = 'dice-clatter-0' + (1 + (ev.id + i) % 4), rate = 1 + (((ev.id * 7 + i) % 9) - 4) * 0.01;
      withClip(id, function (b) { S.at(b, T + off, { bus: 'cue', rate: rate, tag: 'dice' }); });
    });

    var callAt = T + tl.end;
    function crowd(ms) { if (ev.cue) withClip(ev.cue, function (b) { S.at(b, ms, { bus: 'cue', tag: ev.cue }); }); }
    var pick = S.settings.radioOn ? pickLanding(ev, QUOTABLE) : null;
    if (!pick) { setLast(S.settings.radioOn ? 'none' : 'radio off'); crowd(callAt); return; }

    Promise.all(idsFor(pick, ev.id).map(function (id) { return S.clip(id); })).then(function () {
      var plan = planCall(pick, ev.id, durOf, treatOf);
      if (!plan) { setLast('skipped: no clip fits (' + pick.kind + ' ' + pick.square + ')'); crowd(callAt); return; }
      if (S.lateBy(callAt) > LATE_MS) { setLast('skipped: late'); crowd(callAt); return; }
      var t0 = S.ctxTimeFor(callAt);
      if (S.busy(t0, t0 + plan.total)) { setLast('skipped: busy'); crowd(callAt); return; }
      playPlan(plan, callAt, 'voice', 1, 'call');
      setLast(pick.kind === 'quote' ? 'quote ' + plan.ids[0] + (plan.ids.length > 1 ? ' + ' + plan.ids[1] : '') : 'generic ' + pick.voice + ' ' + plan.ids.join('+') + ' (' + plan.total.toFixed(2) + ' s)');
      crowd(callAt + plan.total * 1000 - 150);       // crowd comes in as the squelch tail ends
    });
  }

  /** ROLL tap: instant local dice shake (the synced clatter comes with the result). */
  function localShake() {
    var S = snd();
    if (!S || !S.ctx || !S.unlocked) return;
    withClip('dice-shake-01', function (b) { S.at(b, null, { bus: 'cue', tag: 'shake' }); });
  }

  // ---- lazy loading, tier B: openers, place names (both voices), quotables - once the game is active ----
  var active = false, tierBStarted = false;
  function tierB() {
    var S = snd();
    if (tierBStarted || !active || !S || !S.unlocked || !S.settings.radioOn) return;
    tierBStarted = true;
    var ids = [], i;
    ['sr', 'r273'].forEach(function (v) {
      for (i = 1; i <= 8; i++) ids.push('op-' + v + '-' + pad2(i));
      for (i = 0; i < 52; i++) ids.push('pl-' + v + '-' + pad2(i));
    });
    Object.keys(QUOTABLE).forEach(function (sq) { ids.push('q' + pad2(sq) + 'a', 'q' + pad2(sq) + 'b'); });
    S.preload(ids, 4);
  }
  function setActive(on) { active = !!on; tierB(); }
  (function hook() {
    var S = snd();
    if (!S) return;
    S.listeners.push(tierB);
    S.settingListeners.push(function (k) { if (k === 'radioOn') tierB(); });
  })();

  window.DRRadio = {
    SYNC_ANIM: SYNC_ANIM, QUOTABLE: QUOTABLE, CAP_S: CAP_S, last: last,
    pickLanding: pickLanding, planCall: planCall, idsFor: idsFor,
    onTurn: onTurn, localShake: localShake, setActive: setActive, playPlan: playPlan,
    durOf: durOf, treatOf: treatOf, withClip: withClip
  };
})();
