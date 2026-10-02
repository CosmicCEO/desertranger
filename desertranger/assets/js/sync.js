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
 *   The server stamps cue events with playAt (server ms). We convert that to
 *   our clock (playAt - offset) and schedule the clip on the Web Audio clock,
 *   so every device starts it at the same wall-clock moment. If we hear about
 *   a cue too late (more than LATE_LIMIT_MS after its time) we skip it rather
 *   than play it out of sync.
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
  var CLIPS = {
    cheer: 'assets/audio/crowd-cheer-v2.mp3',
    aww: 'assets/audio/crowd-aww-v2.mp3'
  };

  var Sound = {
    ctx: null,
    buffers: {},
    unlocked: false,
    muted: localStorage.getItem('dr_muted') === '1',
    stats: { played: 0, skipped: 0, lastLateMs: null },

    /** Must be called from a tap/click handler (iOS rule). Safe to call repeatedly. */
    unlock: function () {
      var AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return;
      if (!this.ctx) {
        this.ctx = new AC();
        this.load();
      }
      if (this.ctx.state === 'suspended') this.ctx.resume();
      // Play one silent sample: some iOS versions only unlock on an actual start().
      var b = this.ctx.createBuffer(1, 1, 22050), s = this.ctx.createBufferSource();
      s.buffer = b; s.connect(this.ctx.destination); s.start(0);
      this.unlocked = true;
    },

    load: function () {
      var self = this;
      Object.keys(CLIPS).forEach(function (name) {
        fetch(CLIPS[name]).then(function (r) { return r.arrayBuffer(); })
          .then(function (data) {
            // Old Safari only has the callback form of decodeAudioData.
            return new Promise(function (ok, fail) { self.ctx.decodeAudioData(data, ok, fail); });
          })
          .then(function (buf) { self.buffers[name] = buf; })
          .catch(function (e) { console.warn('audio load failed', name, e); });
      });
    },

    setMuted: function (m) { this.muted = m; localStorage.setItem('dr_muted', m ? '1' : '0'); },

    /** Play clip `name` when the SERVER clock reads playAtServerMs. */
    schedule: function (name, playAtServerMs) {
      if (!this.ctx || !this.buffers[name] || this.muted) return false;
      var delayMs = (playAtServerMs - Clock.offset) - localNow();
      this.stats.lastLateMs = Math.round(-delayMs);
      if (delayMs < -LATE_LIMIT_MS) { this.stats.skipped++; return false; }
      if (this.ctx.state === 'suspended') this.ctx.resume();
      var src = this.ctx.createBufferSource();
      src.buffer = this.buffers[name];
      src.connect(this.ctx.destination);
      // outputLatency (where supported) = time from "start" to sound leaving the speaker.
      var lat = this.ctx.outputLatency || 0;
      if (delayMs >= 0) {
        src.start(this.ctx.currentTime + Math.max(0, delayMs / 1000 - lat));
      } else {
        // Slightly late: start now but skip into the clip so we stay in sync with the others.
        src.start(0, -delayMs / 1000);
      }
      this.stats.played++;
      return true;
    }
  };

  window.DRClock = Clock;
  window.DRSound = Sound;
})();
