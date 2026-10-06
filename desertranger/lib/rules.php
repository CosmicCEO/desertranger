<?php
/**
 * Desert Ranger rules engine.
 *
 * PURE PHP: no database, no HTTP, no globals, no randomness of its own.
 * You hand it a game state array plus a "die roller" function, and it hands
 * back the new state, a list of events (for animation), log lines, and an
 * optional sound cue. That makes it easy to unit test (see tests/rules_test.php)
 * and keeps all game rules in ONE file.
 *
 * Compatible with PHP 7.4+ and 8.x (no match(), no enums, no typed properties).
 *
 * ---------------------------------------------------------------------------
 * STATE SHAPE (plain array, players listed in TURN ORDER = join order):
 *   [
 *     'status'  => 'active' | 'finished',
 *     'turn'    => int,            // action counter; +1 on every roll / choice
 *     'current' => int,            // index into 'players' of whose turn it is
 *     'players' => [ ['id'=>int, 'name'=>string, 'pos'=>int, 'skip'=>int], ... ],
 *     'pending' => null | ['type'=>'swap'|'shortcut', 'player'=>int, 'square'=>int, 'target'=>int],
 *     'winner'  => null | int,     // index into 'players'
 *   ]
 *
 * CONFIRMED RULES (client answers Oct 1, 2026, see docs/RULES-NOTES.md):
 *   - One d6. Overshooting FINISH counts as a win (no exact roll needed).
 *   - Effects CHAIN: if a move/goto/dice result lands on another special
 *     square, that square triggers too (e.g. 41 -> 12 also loses a turn).
 *   - Roll again: no limit on consecutive extra rolls.
 *   - 44 "Reports overdue": roll again and move BACK that many; chaining applies.
 *   - 31 Swap: optional, player may pick ANY other player.
 *   - 6 -> 33 shortcut: optional, exact landing only.
 *   - Lose N turns: skip your next N turns.
 *   - Host controls: skipTurn() passes the turn on; sitOut() makes a player's turns pass silently (skip >= SIT_OUT) until brought back.
 *   - Moves never go below START (0).
 *
 * STILL OPEN (we use whatever is in board/desert-ranger.json):
 *   - TODO(rules): goto targets (e.g. 49 -> 17 Palms (38), not Palm Canyon) are
 *     taken straight from the JSON 'target' field. Change the JSON, not this code.
 *   - TODO(rules): square 48 "Sheep Canyon closure, go back 9" is a plain
 *     'move' with delta -9 in the JSON (lands on Fish Creek 39), not a goto 24.
 *
 * PROTOTYPE DECISIONS (not confirmed by the client yet):
 *   - TODO(rules): after a swap, NEITHER player triggers the square they land on.
 *   - Roll-again keeps the turn; the player taps Roll again (server rolls again).
 *   - The extra die for square 44 is rolled automatically by the server.
 * ---------------------------------------------------------------------------
 */

class DesertRangerRules
{
    /** Hard stop for effect chains, so bad board data can never loop forever. */
    const MAX_CHAIN_DEPTH = 20;

    /** A player whose 'skip' count is at least this is SITTING OUT (the host's choice): passed over silently, nothing is burned. */
    const SIT_OUT = 100;

    /** "Big setback" (plays the 'aww' clip): pushed back at least this many squares in one action, or any lose-turn square. */
    const BIG_SETBACK_SQUARES = 5;

    /** @var array<int,array> squares indexed by square number */
    private $squares = array();
    /** @var int index of the FINISH square */
    private $finish = 0;
    /** @var int die sides */
    private $sides = 6;
    /** @var callable die roller for the action in progress (also used by square 44) */
    private $die;

    public function __construct(array $board)
    {
        foreach ($board['squares'] as $sq) {
            $this->squares[(int)$sq['i']] = $sq;
            if ($sq['type'] === 'finish') {
                $this->finish = (int)$sq['i'];
            }
        }
        if (!$this->finish) {
            $this->finish = max(array_keys($this->squares));
        }
        if (isset($board['die']['sides'])) {
            $this->sides = (int)$board['die']['sides'];
        }
    }

    /** Load a board JSON file and build the engine. */
    public static function fromFile($path)
    {
        $board = json_decode(file_get_contents($path), true);
        if (!is_array($board) || empty($board['squares'])) {
            throw new RuntimeException("Bad board file: $path");
        }
        return new self($board);
    }

    public function finishSquare() { return $this->finish; }
    public function dieSides()     { return $this->sides; }
    public function squareName($i) { return isset($this->squares[$i]['name']) ? $this->squares[$i]['name'] : ('Square ' . $i); }

    /** Fresh state for a game that is just starting. $players = [['id'=>..,'name'=>..], ...] in turn order. */
    public function newGameState(array $players)
    {
        $list = array();
        foreach ($players as $p) {
            $list[] = array('id' => $p['id'], 'name' => $p['name'], 'pos' => 0, 'skip' => 0);
        }
        return array('status' => 'active', 'turn' => 1, 'current' => 0,
                     'players' => $list, 'pending' => null, 'winner' => null);
    }

    // =====================================================================
    //  PUBLIC ACTIONS
    // =====================================================================

    /**
     * The current player rolls the die.
     * @param array    $state
     * @param callable $rollDie  function(int $sides): int   (server passes random_int)
     * @return array ['state'=>array, 'events'=>array, 'log'=>string[], 'cue'=>null|'cheer'|'aww']
     */
    public function roll(array $state, callable $rollDie)
    {
        if ($state['status'] !== 'active') {
            throw new RuleError('The game is not active.');
        }
        if (!empty($state['pending'])) {
            throw new RuleError('Make your choice first.');
        }

        $p = $state['current'];
        $name = $state['players'][$p]['name'];
        $from = $state['players'][$p]['pos'];
        $this->die = $rollDie;
        $die = $this->rollDie($rollDie);

        $out = $this->blankOutcome();
        $out['events'][] = array('type' => 'roll', 'player' => $p, 'value' => $die);

        // Walk forward square by square (the client animates every hop).
        $to = min($this->finish, $from + $die);
        $state['players'][$p]['pos'] = $to;
        $out['events'][] = array('type' => 'walk', 'player' => $p, 'from' => $from, 'to' => $to,
                                 'path' => range($from + 1, $to));
        $out['text'] = $name . ' rolled ' . $die . ' → ' . $this->squareName($to);

        $this->resolveChain($state, $p, $out, true);
        return $this->finishAction($state, $p, $out);
    }

    /**
     * The current player answers a pending optional choice.
     * $choice = ['action'=>'swap', 'target'=>playerIndex]
     *         | ['action'=>'shortcut']
     *         | ['action'=>'skip']           (decline either option)
     */
    public function choose(array $state, array $choice, callable $rollDie)
    {
        if ($state['status'] !== 'active' || empty($state['pending'])) {
            throw new RuleError('There is no choice to make right now.');
        }
        $pend = $state['pending'];
        $p = $pend['player'];
        $name = $state['players'][$p]['name'];
        $action = isset($choice['action']) ? $choice['action'] : '';
        $this->die = $rollDie;
        $state['pending'] = null;
        $out = $this->blankOutcome();

        if ($action === 'skip') {
            $out['text'] = $name . ($pend['type'] === 'swap' ? ' decided not to swap.' : ' stayed on the trail.');
        } elseif ($pend['type'] === 'swap' && $action === 'swap') {
            $t = isset($choice['target']) ? (int)$choice['target'] : -1;
            if ($t === $p || !isset($state['players'][$t])) {
                $state['pending'] = $pend; // put it back
                throw new RuleError('Pick another player to swap with.');
            }
            $a = $state['players'][$p]['pos'];
            $b = $state['players'][$t]['pos'];
            $state['players'][$p]['pos'] = $b;
            $state['players'][$t]['pos'] = $a;
            $out['events'][] = array('type' => 'swap', 'player' => $p, 'other' => $t, 'playerTo' => $b, 'otherTo' => $a);
            $out['text'] = $name . ' swapped places with ' . $state['players'][$t]['name']
                . ' (' . $this->squareName($b) . ' ⇄ ' . $this->squareName($a) . ')';
            // TODO(rules): unconfirmed - swapped players do NOT trigger the squares they land on.
        } elseif ($pend['type'] === 'shortcut' && $action === 'shortcut') {
            $from = $state['players'][$p]['pos'];
            $to = (int)$pend['target'];
            $state['players'][$p]['pos'] = $to;
            $out['events'][] = array('type' => 'jump', 'player' => $p, 'from' => $from, 'to' => $to, 'reason' => 'shortcut');
            $out['text'] = $name . ' took the Cut Across Trail → ' . $this->squareName($to);
            // The landing square could be special in a future board, so run the chain.
            $this->resolveChain($state, $p, $out, false);
        } else {
            $state['pending'] = $pend;
            throw new RuleError('That choice is not allowed here.');
        }
        return $this->finishAction($state, $p, $out);
    }

    /**
     * HOST ACTION: pass the turn on without the current player acting (they are away, or not really playing).
     * A pending swap/shortcut choice is dropped without being applied. Same return shape as roll(); no cue.
     */
    public function skipTurn(array $state)
    {
        if ($state['status'] !== 'active') {
            throw new RuleError('The game is not active.');
        }
        if ($this->othersIn($state, $state['current']) < 1) {
            throw new RuleError('There is nobody else to hand the turn to.');
        }
        $out = $this->blankOutcome();
        $log = array($state['players'][$state['current']]['name'] . ' was skipped by the host.');
        $state['pending'] = null;
        $state['turn']++;
        $this->advanceTurn($state, $out, $log);
        return array('state' => $state, 'events' => $out['events'], 'log' => $log, 'cue' => null);
    }

    /**
     * HOST ACTION: make player index $idx sit out (their turns are passed over silently) or bring them back.
     * At least one other player must stay in. If the player sitting out is the one on turn, the turn moves on
     * (and 'turn' increases, so a stale tap from them is refused). Same return shape as roll(); no cue.
     */
    public function sitOut(array $state, $idx, $on)
    {
        if ($state['status'] !== 'active') {
            throw new RuleError('The game is not active.');
        }
        if (!isset($state['players'][$idx])) {
            throw new RuleError('No such player.');
        }
        $out = $this->blankOutcome();
        $name = $state['players'][$idx]['name'];
        if ($on) {
            if ($this->othersIn($state, $idx) < 1) {
                throw new RuleError('At least one player has to stay in the game.');
            }
            $state['players'][$idx]['skip'] = self::SIT_OUT;
            $log = array($name . ' is sitting out.');
            if ($state['current'] === $idx) {
                $state['pending'] = null;
                $state['turn']++;
                $this->advanceTurn($state, $out, $log);
            }
        } else {
            $state['players'][$idx]['skip'] = 0;
            $log = array($name . ' is back in the game.');
        }
        return array('state' => $state, 'events' => $out['events'], 'log' => $log, 'cue' => null);
    }

    /** How many players OTHER than $idx are still in the game (not sitting out). */
    private function othersIn(array $state, $idx)
    {
        $n = 0;
        foreach ($state['players'] as $i => $pl) {
            if ($i !== $idx && $pl['skip'] < self::SIT_OUT) {
                $n++;
            }
        }
        return $n;
    }

    // =====================================================================
    //  INTERNALS
    // =====================================================================

    private function blankOutcome()
    {
        return array('events' => array(), 'text' => '', 'rollAgain' => false, 'win' => false,
                     'setback' => 0, 'loseTurn' => 0, 'log' => array());
    }

    private function rollDie(callable $rollDie)
    {
        $v = (int)call_user_func($rollDie, $this->sides);
        if ($v < 1 || $v > $this->sides) {
            throw new RuntimeException("Die returned $v");
        }
        return $v;
    }

    private function clamp($pos)
    {
        return max(0, min($this->finish, $pos));
    }

    /**
     * Apply the effect of the square player $p is standing on, then keep going
     * while effects land on more special squares. Stops at MAX_CHAIN_DEPTH.
     * $byRoll = true when the player arrived by a normal die walk (needed for
     * "exact landing only" on the shortcut).
     */
    private function resolveChain(array &$state, $p, array &$out, $byRoll)
    {
        for ($depth = 1; ; $depth++) {
            if ($depth > self::MAX_CHAIN_DEPTH) {
                $out['events'][] = array('type' => 'chainGuard', 'player' => $p);
                $out['text'] .= ' (chain stopped)';
                return;
            }
            $pos = $state['players'][$p]['pos'];
            if ($pos >= $this->finish) {
                $state['players'][$p]['pos'] = $this->finish;
                $out['win'] = true;
                $fin = $this->squareName($this->finish);
                $endsWithFinish = substr($out['text'], -strlen($fin)) === $fin;
                $out['text'] .= $endsWithFinish ? ' 🏁' : ' → ' . $fin . ' 🏁';
                return;
            }
            $sq = $this->squares[$pos];
            $type = $sq['type'];

            if ($type === 'move') {
                $to = $this->clamp($pos + (int)$sq['delta']);
                $this->moveTo($state, $p, $out, $pos, $to, 'walk');
                $d = (int)$sq['delta'];
                $out['text'] .= ': ' . ($d < 0 ? 'back ' . (-$d) : 'ahead ' . $d) . ' → ' . $this->squareName($to);
                $byRoll = false;
                continue;
            }
            if ($type === 'goto') {
                // TODO(rules): goto targets still open with the client; we trust the JSON.
                $to = $this->clamp((int)$sq['target']);
                $this->moveTo($state, $p, $out, $pos, $to, 'jump');
                $out['text'] .= ' → ' . $this->squareName($to);
                $byRoll = false;
                continue;
            }
            if ($type === 'dice') {
                // 44 "Reports overdue": roll again and go back that many.
                $r = $this->rollDie($this->die);
                $out['events'][] = array('type' => 'roll', 'player' => $p, 'value' => $r, 'reason' => 'dice');
                $to = $this->clamp($pos - $r);
                $this->moveTo($state, $p, $out, $pos, $to, 'walk');
                $out['text'] .= ': rolled ' . $r . ', back ' . $r . ' → ' . $this->squareName($to);
                $byRoll = false;
                continue;
            }
            if ($type === 'loseTurn') {
                $n = isset($sq['turns']) ? (int)$sq['turns'] : 1;
                $state['players'][$p]['skip'] += $n;
                $out['loseTurn'] += $n;
                $out['events'][] = array('type' => 'loseTurn', 'player' => $p, 'turns' => $n);
                $out['text'] .= ': lose ' . $n . ' turn' . ($n > 1 ? 's' : '') . '!';
                return;
            }
            if ($type === 'rollAgain') {
                $out['rollAgain'] = true;
                $out['events'][] = array('type' => 'rollAgain', 'player' => $p);
                $out['text'] .= ': roll again!';
                return;
            }
            if ($type === 'swap') {
                if (count($state['players']) > 1) { // skipped in solo play
                    $state['pending'] = array('type' => 'swap', 'player' => $p, 'square' => $pos, 'target' => null);
                    $out['text'] .= ': may swap places with another player…';
                }
                return;
            }
            if ($type === 'shortcut') {
                $exactOnly = !isset($sq['exactLandingOnly']) || $sq['exactLandingOnly'];
                if ($byRoll || !$exactOnly) {
                    $state['pending'] = array('type' => 'shortcut', 'player' => $p, 'square' => $pos,
                                              'target' => (int)$sq['target']);
                    $out['text'] .= ': may take the shortcut to ' . $this->squareName((int)$sq['target']) . '…';
                }
                return;
            }
            // start, plain, or unknown type: nothing happens.
            return;
        }
    }

    /** Move with an animation event and keep a running tally of backward movement. */
    private function moveTo(array &$state, $p, array &$out, $from, $to, $kind)
    {
        $state['players'][$p]['pos'] = $to;
        $ev = array('type' => $kind, 'player' => $p, 'from' => $from, 'to' => $to);
        if ($kind === 'walk') {
            $ev['path'] = range($from, $to); // works both directions
            array_shift($ev['path']);         // path excludes the starting square
        }
        $out['events'][] = $ev;
        if ($to < $from) {
            $out['setback'] += ($from - $to);
        }
    }

    /** Common tail of roll()/choose(): win check, turn passing, cue, log. */
    private function finishAction(array $state, $p, array $out)
    {
        $state['turn']++;
        $log = array($out['text']);

        if ($out['win']) {
            $state['status'] = 'finished';
            $state['winner'] = $p;
            $state['pending'] = null;
            $log[0] .= ' ' . $state['players'][$p]['name'] . ' wins!';
        } elseif (!empty($state['pending'])) {
            // Same player must answer the choice; turn does not pass.
        } elseif ($out['rollAgain']) {
            // Same player rolls again; turn does not pass.
        } else {
            $this->advanceTurn($state, $out, $log);
        }

        // One sound cue per action. Priority: win > big setback > roll again.
        $cue = null;
        if ($out['win']) {
            $cue = 'cheer';
        } elseif ($out['setback'] >= self::BIG_SETBACK_SQUARES || $out['loseTurn'] > 0) {
            $cue = 'aww';
        } elseif ($out['rollAgain']) {
            $cue = 'cheer';
        }
        return array('state' => $state, 'events' => $out['events'], 'log' => $log, 'cue' => $cue);
    }

    /** Pass the turn to the next player, skipping anyone who owes lost turns. */
    private function advanceTurn(array &$state, array &$out, array &$log)
    {
        $n = count($state['players']);
        $cur = $state['current'];
        // Everyone sitting out (the server never allows it): leave the turn where it is.
        $anyIn = false;
        foreach ($state['players'] as $pl) {
            if ($pl['skip'] < self::SIT_OUT) {
                $anyIn = true;
            }
        }
        if (!$anyIn) {
            return;
        }
        // Each skipped seat burns one owed turn, so this always ends;
        // the cap is just belt-and-braces.
        for ($guard = 0; $guard < 1000; $guard++) {
            $cur = ($cur + 1) % $n;
            if ($state['players'][$cur]['skip'] >= self::SIT_OUT) {
                continue;   // sitting out (host's choice): passed over silently, nothing burned, no log line
            }
            if ($state['players'][$cur]['skip'] > 0) {
                $state['players'][$cur]['skip']--;
                $out['events'][] = array('type' => 'skipped', 'player' => $cur);
                $log[] = $state['players'][$cur]['name'] . ' loses this turn.';
                continue;
            }
            break;
        }
        $state['current'] = $cur;
    }
}

/** Thrown for player mistakes (not your turn, bad choice...). Safe to show to users. */
class RuleError extends Exception {}
