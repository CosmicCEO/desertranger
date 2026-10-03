/*
 * board.js - draws the pieces on the board image and animates them.
 *
 * COORDINATES: board/desert-ranger.json stores square centres (x, y) in
 * pixels of the ORIGINAL board photo (4913 x 3583). The image we show,
 * board-2000.jpg, is a resized copy of art/board-flat.jpg, which was made by
 * perspective-correcting ("flattening") that photo. A plain scale would be
 * off by up to ~2 squares near the corners, so we apply the same 3x3
 * perspective matrix (homography) that produced board-flat.jpg, then divide
 * by the flat image size to get percentages. Percentages keep pieces in the
 * right place at any zoom level or screen size.
 *
 * If the board art is ever re-flattened, update FLAT below (the matrix is
 * printed by art/_work/warp.py: cv2.getPerspectiveTransform, normalised).
 * If squares are re-traced directly on the flat image, set FLAT.H to the
 * identity [1,0,0, 0,1,0, 0,0,1] and FLAT.w/h to that image's size.
 */
(function () {
  'use strict';

  var FLAT = {
    w: 4372, h: 3321, // size of art/board-flat.jpg
    H: [1.0733108383997176, 0.08223336430667229, -386.8857136745453,
        0.017300226477827578, 1.139770690834811, -137.3968248144172,
        1.0090351956215486e-06, 3.9462533805769657e-05, 1.0]
  };

  // Where extra pieces sit when several share a square (% of board width/height).
  var STACK = [[0, 0], [-2.4, -1.8], [2.4, -1.8], [-2.4, 1.8], [2.4, 1.8], [0, -3.4], [0, 3.4], [-4.4, 0]];

  var HOP_MS = 260;   // one square of a walk
  var JUMP_MS = 750;  // goto / shortcut / swap
  var ROLL_MS = 550;  // die reveal
  var WALK_END_MS = 250; // pause after a walk

  function BoardView(boardEl, board, vehicles) {
    this.el = boardEl;
    this.board = board;
    this.vehicles = vehicles;
    this.pieces = {};    // playerId -> element
    this.shown = {};     // playerId -> square index currently drawn
    this.players = [];
    this.activeId = null;
    this.queue = [];     // pending animation tasks
    this.busy = false;
    this.xy = board.squares.map(function (s) { return toPercent(s.x, s.y); });
  }

  /** Photo pixel -> % position on the flat image. */
  function toPercent(x, y) {
    var H = FLAT.H, w = H[6] * x + H[7] * y + H[8];
    var fx = (H[0] * x + H[1] * y + H[2]) / w;
    var fy = (H[3] * x + H[4] * y + H[5]) / w;
    return { x: fx / FLAT.w * 100, y: fy / FLAT.h * 100 };
  }

  BoardView.prototype.squareName = function (i) {
    var s = this.board.squares[i];
    return s ? s.name : '?';
  };

  /** Latest players from the server. Pieces not currently animating snap to their real square. */
  BoardView.prototype.setPlayers = function (players, activeId) {
    var self = this;
    this.players = players;
    this.activeId = activeId;
    players.forEach(function (p) {
      if (!self.pieces[p.id]) {
        var el = document.createElement('div');
        el.className = 'piece';
        var img = document.createElement('img');
        img.src = 'assets/img/pieces/' + p.vehicle + '.png';
        img.alt = '';
        var nm = document.createElement('span');
        nm.className = 'nm';
        nm.textContent = p.name;
        el.appendChild(img);
        el.appendChild(nm);
        self.el.appendChild(el);
        self.pieces[p.id] = el;
        self.shown[p.id] = p.pos;
      }
      if (!self.busy && !self.queue.length) self.shown[p.id] = p.pos;
      self.pieces[p.id].classList.toggle('active', p.id === activeId);
    });
    this.layout();
  };

  /** Place every piece at its shown square, fanning out pieces that share a square. */
  BoardView.prototype.layout = function (skipId) {
    var self = this, groups = {};
    this.players.forEach(function (p) {
      var sq = self.shown[p.id];
      (groups[sq] = groups[sq] || []).push(p.id);
    });
    Object.keys(groups).forEach(function (sq) {
      groups[sq].forEach(function (id, k) {
        if (id === skipId) return;
        var o = groups[sq].length > 1 ? STACK[k % STACK.length] : [0, 0];
        self.place(id, +sq, o);
      });
    });
  };

  BoardView.prototype.place = function (id, sq, off) {
    var p = this.xy[sq], el = this.pieces[id];
    if (!p || !el) return;
    off = off || [0, 0];
    el.style.left = (p.x + off[0]) + '%';
    el.style.top = (p.y + off[1] * 1.3166) + '%';
  };

  /**
   * Offsets (ms after the animation starts) of every die reveal and of the moment the piece stops moving.
   * Uses the same constants as animate(), so audio scheduled from it lines up with the pictures.
   * Returns {rolls: [ms, ...], end: ms}.
   */
  BoardView.prototype.timeline = function (steps) {
    var t = 0, rolls = [];
    (steps || []).forEach(function (s) {
      if (s.type === 'roll') { rolls.push(t); t += ROLL_MS; }
      else if (s.type === 'walk') { t += (s.path || []).length * HOP_MS + WALK_END_MS; }
      else if (s.type === 'jump' || s.type === 'swap') { t += JUMP_MS; }
    });
    return { rolls: rolls, end: t };
  };

  /**
   * Queue the animation steps of one turn (from the server event payload).
   * Step types: roll, walk {path}, jump {to}, swap {player, other, playerTo, otherTo},
   * loseTurn, rollAgain, skipped, chainGuard.  onRoll(value) is called for die steps.
   * startAt (optional, local epoch ms): a wait task goes in the queue FIRST, so the whole turn starts at that
   * moment on every device (the server's shared time T). Because the queue is then non-empty, setPlayers()
   * does not snap the piece to its new square early.
   */
  BoardView.prototype.animate = function (steps, onRoll, onDone, startAt) {
    var self = this;
    if (startAt) {
      self.queue.push(function (next) {
        var d = startAt - (window.DRClock ? window.DRClock.localNow() : Date.now()); // same clock the sync offset uses
        setTimeout(next, Math.max(0, d));
      });
    }
    (steps || []).forEach(function (s) {
      if (s.type === 'roll') {
        self.queue.push(function (next) { if (onRoll) onRoll(s.value); setTimeout(next, ROLL_MS); });
      } else if (s.type === 'walk') {
        (s.path || []).forEach(function (sq) {
          self.queue.push(function (next) { self.moveOne(s.player, sq, 'hop', HOP_MS, next); });
        });
        self.queue.push(function (next) { setTimeout(next, WALK_END_MS); });
      } else if (s.type === 'jump') {
        self.queue.push(function (next) { self.moveOne(s.player, s.to, 'jump', JUMP_MS, next); });
      } else if (s.type === 'swap') {
        self.queue.push(function (next) {
          self.moveOne(s.other, s.otherTo, 'jump', JUMP_MS, function () {});
          self.moveOne(s.player, s.playerTo, 'jump', JUMP_MS, next);
        });
      }
    });
    if (onDone) self.queue.push(function (next) { onDone(); next(); });
    this.run();
  };

  BoardView.prototype.moveOne = function (id, sq, cls, ms, next) {
    var el = this.pieces[id], self = this;
    if (!el) { next(); return; }
    this.shown[id] = sq;
    el.classList.add('moving', cls);
    this.place(id, sq, [0, 0]);
    setTimeout(function () {
      el.classList.remove('moving', cls);
      self.layout();
      next();
    }, ms);
  };

  BoardView.prototype.run = function () {
    var self = this;
    if (this.busy) return;
    var task = this.queue.shift();
    if (!task) {
      // All done: make sure everything matches the server's truth.
      this.players.forEach(function (p) { self.shown[p.id] = p.pos; });
      this.layout();
      return;
    }
    this.busy = true;
    task(function () { self.busy = false; self.run(); });
  };

  /** Scroll the zoomed board so a player's piece is visible. */
  BoardView.prototype.scrollTo = function (id, wrap) {
    var el = this.pieces[id];
    if (!el || !wrap || wrap.scrollWidth <= wrap.clientWidth + 2) return;
    wrap.scrollTo({ left: el.offsetLeft - wrap.clientWidth / 2, top: el.offsetTop - wrap.clientHeight / 2, behavior: 'smooth' });
  };

  window.BoardView = BoardView;
})();
