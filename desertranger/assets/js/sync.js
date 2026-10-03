/*
 * sync.js - clock sync + synchronized sound.
 *
 * CLOCK SYNC (NTP-style):
 *   For each request we note the local send time t0 and receive time t1, and
 *   the server's time ts from the response.
 *       rtt    = t1 - t0
 *       offset = ts - (t0 + t1) / 2      (server clock minus our clock)
 *   Samples with a small RTT are the most trustworthy (less room for the
 *   request/response to be lopsided), so we keep the last 40 samples and use
 *   the median offset of the 5 LOWEST-RTT ones.
 *   Samples come from a burst of tiny ?a=time pings at start-up, a ping every
 *   30 s, and every regular state poll (each response carries serverNow).
 *
 * SOUND:
 *   The server stamps every turn event with playAt (server ms). We convert that to
 *   our clock (playAt - offset) and schedule clips on the Web Audio clock,
 *   so every device starts them at the same wall-clock moment. If we hear about
 *   a cue too late (more than LATE_LIMIT_MS after its time) we skip it rather
 *   than play it out of sync.
 *
 *   Audio graph (all behind one master gain = the 🔊 mute):
 *     cue     crowd cheer/aww + dice                    (synced)
 *     voice   landing radio calls + quotables           (synced)
 *     amb     desert bed + critters  -> amb duck        (local only)
 *     chatter background radio chatter -> chatter duck  (local only)
 *   The two duck gains dip while any cue/voice sound is scheduled (see duckApply).
 *
 *   Clips: lazy-loaded through Sound.clip(id) from audio/manifest.json (ids ->
 *   file + content hash for cache busting). A missing clip resolves to null:
 *   silence, never an error. Nothing is fetched before the audio-unlock tap.
 */
(function () {
  'use strict';

  // Monotonic local clock in "epoch ms" (Date.now can jump when the OS adjusts time).
  var base = Date.now() - performance.now();
  function localNow() { return base + performance.now(); }

  var Clock = {
    samples: [],
    offset: 0,          // server - local, ms
    rtt: null,          // best (lowest) RTT among kept samples, ms
    ready: false,

    localNow: localNow,
    serverNow: function () { return localNow() + this.offset; },

    /** Add one measurement. t0/t1 are localNow() before/after the request, ts the server's ms. */
    add: function (t0, ts, t1) {
      if (typeof ts !== 'number' || !isFinite(ts)) return;
      var rtt = t1 - t0;
      if (rtt < 0 || rtt > 10000) return;
      this.samples.push({ rtt: rtt, offset: ts - (t0 + t1) / 2 });
      if (this.samples.length > 40) this.samples.shift();
      var best = this.samples.slice().sort(function (a, b) { return a.rtt - b.rtt; }).slice(0, 5);
      var offs = best.map(function (s) { return s.offset; }).sort(function (a, b) { return a - b; });
      this.offset = offs[Math.floor(offs.length / 2)];
      this.rtt = best[0].rtt;
      this.ready = this.samples.length >= 3;
    },

    /** Ping the tiny time endpoint (no DB). */
    ping: function () {
      var self = this, t0 = localNow();
      return fetch('api.php?a=time&_=' + Math.random(), { cache: 'no-store' })
        .then(function (r) { return r.json(); })
        .then(function (j) { self.add(t0, j.t, localNow()); })
        .catch(function () {});
    },

    /** A burst of n pings spaced 150 ms apart, then one every 30 s. */
    start: function () {
      var self = this, n = 6;
      (function next() {
        self.ping().then(function () { if (--n > 0) setTimeout(next, 150); });
      })();
      setInterval(function () { self.ping(); }, 30000);
    }
  };

  var LATE_LIMIT_MS = 250;
  // The two original crowd clips (binaries delivered separately, not in git).
  var CLIPS = {
    cheer: 'assets/audio/crowd-cheer-v2.mp3',
    aww: 'assets/audio/crowd-aww-v2.mp3'
  };
  // Tier A: loaded at the unlock tap (small and always needed).
  var TIER_A = ['radio-click-01', 'radio-squelch-01', 'radio-squelch-02', 'radio-squelch-03', 'radio-hiss-loop',
                'dice-shake-01', 'dice-clatter-01', 'dice-clatter-02', 'dice-clatter-03', 'dice-clatter-04'];
  var DUCK_DB = { amb: -12, chatter: -18 };
  var DUCK_LEAD = 0.15, DUCK_TAIL = 0.4, DUCK_TC = 0.08;   // seconds

  function dbToGain(db) { return Math.pow(10, db / 20); }
  function lsGet(k, d) { try { var v = localStorage.getItem(k); return v === null ? d : v; } catch (e) { return d; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* private mode: fine */ } }

  var Sound = {
    ctx: null,
    bus: {},
    buffers: {},
    clipP: {},          // id -> promise of AudioBuffer|null (cache)
    manifest: null,     // id -> {file, v, sec, treatment, ...}
    manifestP: null,
    wins: [],           // scheduled cue/voice/chatter windows {start, end, bus, tag} in ctx time
    unlocked: false,
    muted: lsGet('dr_muted', '0') === '1',
    boardMode: false,
    listeners: [],      // called after unlock
    settings: {
      ambOn: lsGet('dr_amb_on', '1') === '1',
      ambVol: Math.max(0, Math.min(100, parseInt(lsGet('dr_amb_vol', '20'), 10) || 0)),     // background sound: default 20 %
      gameVol: Math.max(0, Math.min(100, parseInt(lsGet('dr_game_vol', '50'), 10) || 0)),   // turn-based sounds: default 50 %
      radioOn: lsGet('dr_radio_on', '1') === '1'
    },
    settingListeners: [],
    stats: { played: 0, skipped: 0, lastLateMs: null },

    /** Must be called from a tap/click handler (iOS rule). Safe to call repeatedly. */
    unlock: function () {
      var AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return;
      var first = false;
      if (!this.ctx) {
        this.ctx = new AC();
        this.buildGraph();
        first = true;
      }
      if (this.ctx.state === 'suspended') this.ctx.resume();
      // Play one silent sample: some iOS versions only unlock on an actual start().
      var b = this.ctx.createBuffer(1, 1, 22050), s = this.ctx.createBufferSource();
      s.buffer = b; s.connect(this.ctx.destination); s.start(0);
      this.unlocked = true;
      if (first) {
        this.load();
        this.listeners.forEach(function (fn) { try { fn(); } catch (e) { console.warn('unlock listener', e); } });
      }
    },

    buildGraph: function () {
      var ctx = this.ctx, bus = this.bus;
      function gain(v, to) { var g = ctx.createGain(); g.gain.value = v; if (to) g.connect(to); return g; }
      bus.master = gain(this.muted ? 0 : 1, ctx.destination);
      bus.game = gain(this.gameGain(), bus.master);   // volume slider for the turn-based sounds (cue + voice)
      bus.cue = gain(1, bus.game);
      bus.voice = gain(1, bus.game);
      bus.ambDuck = gain(1, bus.master);
      bus.amb = gain(this.ambGain(), bus.ambDuck);
      bus.chatterDuck = gain(1, bus.master);
      bus.chatter = gain(this.chatterGain(), bus.chatterDuck);   // chatter sits well below game cues; follows the ambience slider
    },

    /** Tier A: crowd clips + manifest + radio fx + dice. */
    load: function () {
      var self = this;
      Object.keys(CLIPS).forEach(function (name) { self.clip(name); });
      this.preload(TIER_A, 4);
    },

    manifestReady: function () {
      if (!this.manifestP) {
        var self = this;
        this.manifestP = fetch('audio/manifest.json', { cache: 'no-cache' })
          .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
          .then(function (j) { self.manifest = j.clips || {}; return self.manifest; })
          .catch(function (e) { console.warn('audio manifest unavailable', e && e.message); self.manifest = {}; return self.manifest; });
      }
      return this.manifestP;
    },

    /** Promise of the decoded AudioBuffer for a clip id, or null if it is missing. Never rejects. */
    clip: function (id) {
      var self = this;
      if (!this.ctx) return Promise.resolve(null);
      if (this.buffers[id]) return Promise.resolve(this.buffers[id]);
      if (this.clipP[id]) return this.clipP[id];
      var p = this.manifestReady().then(function (man) {
        var url;
        if (CLIPS[id]) url = CLIPS[id];
        else if (man[id]) url = 'audio/' + man[id].file + '?v=' + man[id].v;   // v = content hash: Apache caches mp3 for 30 days
        else return null;
        return fetch(url).then(function (r) {
          if (!r.ok) throw new Error('HTTP ' + r.status);
          return r.arrayBuffer();
        }).then(function (data) {
          // Old Safari only has the callback form of decodeAudioData.
          return new Promise(function (ok, fail) { self.ctx.decodeAudioData(data, ok, fail); });
        }).then(function (buf) { self.buffers[id] = buf; return buf; });
      }).catch(function (e) {
        console.warn('audio clip unavailable:', id, e && e.message);
        return null;
      });
      this.clipP[id] = p;
      return p;
    },

    /** Load many clips, n at a time. Resolves when all are done (missing ones are just null). */
    preload: function (ids, n) {
      var self = this, queue = ids.slice(), running = 0, done;
      var all = new Promise(function (ok) { done = ok; });
      if (!queue.length) return Promise.resolve();
      function next() {
        if (!queue.length) { if (!running) done(); return; }
        running++;
        self.clip(queue.shift()).then(function () { running--; next(); });
      }
      for (var i = 0; i < (n || 4); i++) next();
      return all;
    },

    setMuted: function (m) {
      this.muted = m; lsSet('dr_muted', m ? '1' : '0');
      if (this.bus.master) this.bus.master.gain.value = m ? 0 : 1;
    },

    // ---- settings (ambience on/off + volume, radio chatter on/off) ----
    ambGain: function () { return this.settings.ambVol / 100 * 1.4 * (this.boardMode ? 2 : 1); },   // board view: +6 dB
    /** Background radio chatter is part of the background sound: 0.35 at the old default slider (60), scaling with it. */
    chatterGain: function () { return 0.35 * (this.settings.ambVol / 60) * (this.boardMode ? 2 : 1); },
    /** Turn-based sounds (dice, radio calls, quotes, crowd): 100 % = the level the clips were mastered at, 50 % = half. */
    gameGain: function () { return this.settings.gameVol / 100; },
    setSetting: function (key, val) {
      this.settings[key] = val;
      lsSet({ ambOn: 'dr_amb_on', ambVol: 'dr_amb_vol', gameVol: 'dr_game_vol', radioOn: 'dr_radio_on' }[key], typeof val === 'boolean' ? (val ? '1' : '0') : String(val));
      if (key === 'ambVol' && this.bus.amb) {
        this.bus.amb.gain.setTargetAtTime(this.ambGain(), this.ctx.currentTime, 0.05);
        this.bus.chatter.gain.setTargetAtTime(this.chatterGain(), this.ctx.currentTime, 0.05);
      }
      if (key === 'gameVol' && this.bus.game) this.bus.game.gain.setTargetAtTime(this.gameGain(), this.ctx.currentTime, 0.05);
      this.settingListeners.forEach(function (fn) { try { fn(key, val); } catch (e) { console.warn('setting listener', e); } });
    },
    setBoardMode: function (on) {
      this.boardMode = !!on;
      if (this.bus.amb) { this.bus.amb.gain.value = this.ambGain(); this.bus.chatter.gain.value = this.chatterGain(); }
    },

    // ---- time helpers ----
    /** How many ms after server time `serverMs` it is now on this device (negative = still in the future). */
    lateBy: function (serverMs) { return localNow() - (serverMs - Clock.offset); },

    /** Web Audio (ctx) time at which the SERVER clock reads serverMs (never earlier than now). */
    ctxTimeFor: function (serverMs) {
      var delayMs = (serverMs - Clock.offset) - localNow(), lat = this.ctx.outputLatency || 0;
      return this.ctx.currentTime + Math.max(0, delayMs / 1000 - lat);
    },

    /** Leading/trailing near-silence of a decoded buffer (MP3 adds encoder padding): {off, dur} in seconds. */
    trim: function (buf) {
      if (!buf) return null;
      if (buf._drTrim) return buf._drTrim;
      var d = buf.getChannelData(0), s = 0, e = d.length - 1, th = 0.003;
      while (s < e && Math.abs(d[s]) < th) s++;
      while (e > s && Math.abs(d[e]) < th) e--;
      buf._drTrim = { off: s / buf.sampleRate, dur: Math.max(0.02, (e - s + 1) / buf.sampleRate) };
      return buf._drTrim;
    },

    /**
     * Play a buffer when the SERVER clock reads serverMs (null = right now, local only).
     * opts: bus (cue|voice|amb|chatter, default cue), gain, rate, offset, duration (buffer seconds), pan (-1..1), tag.
     * Returns {start, end} in ctx time, or null if skipped (muted / not unlocked / too late).
     * Slightly late (<= LATE_LIMIT_MS): starts now and skips into the clip so everyone stays in sync.
     */
    at: function (buf, serverMs, o) {
      o = o || {};
      if (!this.ctx || !buf || this.muted) return null;
      var ctx = this.ctx, delayMs = serverMs == null ? 0 : (serverMs - Clock.offset) - localNow();
      if (serverMs != null) this.stats.lastLateMs = Math.round(-delayMs);
      if (delayMs < -LATE_LIMIT_MS) { this.stats.skipped++; return null; }
      if (ctx.state !== 'running') ctx.resume();   // 'suspended', or 'interrupted' on iOS after a call / lock screen
      var busName = o.bus || 'cue', rate = o.rate || 1, off = o.offset || 0;
      var src = ctx.createBufferSource(), node = src;
      src.buffer = buf;
      src.playbackRate.value = rate;
      if (o.gain != null && o.gain !== 1) { var g = ctx.createGain(); g.gain.value = o.gain; node.connect(g); node = g; }
      if (o.pan && ctx.createStereoPanner) { var pn = ctx.createStereoPanner(); pn.pan.value = o.pan; node.connect(pn); node = pn; }
      node.connect(this.bus[busName]);
      var lat = ctx.outputLatency || 0, when, skip = 0;   // outputLatency: time from "start" to sound leaving the speaker
      if (delayMs >= 0) when = ctx.currentTime + Math.max(0, delayMs / 1000 - lat);
      else { when = ctx.currentTime; skip = (-delayMs / 1000) * rate; }
      var avail = (o.duration != null ? o.duration : buf.duration - off) - skip;
      if (avail <= 0) { this.stats.skipped++; return null; }
      src.start(when, off + skip, avail);
      var win = { start: when, end: when + avail / rate, bus: busName, tag: o.tag || '' };
      this.wins.push(win);
      if (this.wins.length > 60) { var now = ctx.currentTime; this.wins = this.wins.filter(function (w) { return w.end > now - 2; }); }
      this.stats.played++;
      if (busName === 'cue' || busName === 'voice') this.duckApply();
      return win;
    },

    /** Original API, kept for the crowd cues: play clip `name` when the SERVER clock reads playAtServerMs. */
    schedule: function (name, playAtServerMs) {
      if (!this.buffers[name]) return false;
      return !!this.at(this.buffers[name], playAtServerMs, { bus: 'cue', tag: name });
    },

    /** True if any cue/voice sound overlaps [t0, t1] (ctx time). Used to skip calls and postpone chatter. */
    busy: function (t0, t1, includeChatter) {
      var now = this.ctx ? this.ctx.currentTime : 0;
      this.wins = this.wins.filter(function (w) { return w.end > now - 2; });
      return this.wins.some(function (w) {
        return (w.bus === 'cue' || w.bus === 'voice' || (includeChatter && w.bus === 'chatter')) && w.start < t1 && w.end > t0;
      });
    },

    /** Dip the ambience (and chatter) under every cue/voice window; merged windows, smooth ramps. */
    duckApply: function () {
      var ctx = this.ctx, t = ctx.currentTime, self = this;
      var ws = this.wins.filter(function (w) { return (w.bus === 'cue' || w.bus === 'voice') && w.end + DUCK_TAIL > t; })
        .sort(function (a, b) { return a.start - b.start; });
      var merged = [];
      ws.forEach(function (w) {
        var s = Math.max(t, w.start - DUCK_LEAD), e = w.end + DUCK_TAIL, last = merged[merged.length - 1];
        if (last && s <= last.e) last.e = Math.max(last.e, e); else merged.push({ s: s, e: e });
      });
      ['amb', 'chatter'].forEach(function (k) {
        var p = self.bus[k + 'Duck'].gain, v = p.value;
        p.cancelScheduledValues(t);
        p.setValueAtTime(v, t);
        merged.forEach(function (m) {
          p.setTargetAtTime(dbToGain(DUCK_DB[k]), m.s, DUCK_TC);
          p.setTargetAtTime(1, m.e, DUCK_TC);
        });
      });
    },

    /**
     * A looping bed made of overlapping sources with an equal-power crossfade at the loop point
     * (MP3 has encoder padding, so loop=true on a raw MP3 clicks). Buffers are trimmed first.
     * opts: bus (default amb), gain, xfade (s), fadeIn (s), startAt (ctx time), endAt (ctx time, optional).
     * Returns {stop(fadeSec)}.
     */
    loopBed: function (buf, o) {
      o = o || {};
      var self = this, ctx = this.ctx, tr = this.trim(buf);
      var x = Math.min(o.xfade || 1.5, tr.dur / 3), fadeIn = Math.min(o.fadeIn != null ? o.fadeIn : 0.03, tr.dur / 3);
      var out = ctx.createGain(), nodes = [], done = false, timer = null, first = true;
      out.gain.value = o.gain != null ? o.gain : 1;
      out.connect(this.bus[o.bus || 'amb']);
      var nextStart = o.startAt != null ? o.startAt : ctx.currentTime + 0.05;
      function curve(up) {
        var n = 32, a = new Float32Array(n);
        for (var i = 0; i < n; i++) { var p = i / (n - 1); a[i] = up ? Math.sin(p * Math.PI / 2) : Math.cos(p * Math.PI / 2); }
        return a;
      }
      var UP = curve(true), DOWN = curve(false);
      function addSeg() {
        var st = nextStart, g = ctx.createGain(), s = ctx.createBufferSource();
        s.buffer = buf; s.connect(g); g.connect(out);
        g.gain.value = 0;
        var fin = first ? fadeIn : x;
        g.gain.setValueCurveAtTime(UP, st, Math.max(0.01, fin));
        first = false;
        var segEnd = st + tr.dur;
        if (o.endAt != null && o.endAt <= segEnd) {   // last segment: fade out at endAt and stop
          var fo = Math.min(0.03, Math.max(0.01, o.endAt - st - fin));
          g.gain.setValueCurveAtTime(DOWN, Math.max(st + fin, o.endAt - fo), fo);
          s.start(st, tr.off, tr.dur);
          s.stop(o.endAt + 0.05);
          done = true;
        } else {
          g.gain.setValueCurveAtTime(DOWN, segEnd - x, x);
          s.start(st, tr.off, tr.dur);
          s.stop(segEnd + 0.05);
          nextStart = segEnd - x;
        }
        nodes.push(s);
        if (nodes.length > 6) nodes.shift();
      }
      function tick() {
        if (done) { clearInterval(timer); return; }
        while (!done && nextStart < ctx.currentTime + 6) addSeg();
        if (done) clearInterval(timer);
      }
      tick();
      if (!done) timer = setInterval(tick, 1000);
      return {
        stop: function (fade) {
          done = true; clearInterval(timer);
          var f = fade == null ? 0.4 : fade;
          out.gain.cancelScheduledValues(ctx.currentTime);
          out.gain.setTargetAtTime(0, ctx.currentTime, f / 3);
          setTimeout(function () { nodes.forEach(function (n) { try { n.stop(); } catch (e) { /* already stopped */ } }); out.disconnect(); }, f * 1000 + 200);
        }
      };
    },

    loadedCount: function () { return Object.keys(this.buffers).length; }
  };

  window.DRClock = Clock;
  window.DRSound = Sound;
})();
