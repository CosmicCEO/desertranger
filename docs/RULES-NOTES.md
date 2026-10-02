# Desert Ranger: rules notes (transcribed from photo)

Source: hand-drawn board photo (`art/desert-ranger-photo.jpg`, downscaled to 2000px wide). Board data: `board/desert-ranger.json`. Left column and inner loop re-verified against higher-resolution closeup photos. All 52 squares were legible; no low-confidence readings.

## Confirmed rules (client answers, Oct 1, 2026)
- **Players:** 2 to 8, one d6.
- **Shortcut (6 -> 33 Una Palma):** optional, exact landing only.
- **Effects chain:** yes. If a move, goto, or dice result lands on another special square, that square triggers too (e.g. 41 -> 12 also loses a turn).
- **Reports overdue (44):** roll again and move back that many; chaining applies.
- **Swap (31):** optional; the player may pick any other player. Skipped in solo play.
- **FINISH:** no exact roll needed; overshooting counts as a win.
- **Roll again:** no limit on consecutive extra rolls. (No move/goto/dice result currently lands on a roll-again square, so chaining can't loop.)
- **Lose N turns:** skip your next N turns.
- Moves never go below START (0).

## Still open (defaults in use)
1. Goto targets: 1 -> Hawk Canyon (20), 3 -> Sacramento (21), 27 -> Middle Willows (17), 40 -> Court (34), 41 -> Ocotillo Wells (12), 49 -> 17 Palms (38, not Palm Canyon), 50 -> Arroyo Salado (19).
2. 48 "Sheep Canyon closure, go back 9" is a plain -9 (lands on Fish Creek 39), not a goto Sheep Canyon (24).
3. "FONTS POINT" kept as drawn (real name is Font's Point).
4. Turn order: default highest roll goes first.

## Square count
**52 squares**, indices 0-51: START (0) ... FINISH (51).

## Square summary by type
| Type | Count | Squares |
|---|---|---|
| start / finish | 2 | 0, 51 |
| plain (place name) | 25 | 2, 4, 5, 7, 8, 10, 11, 13, 15, 17-21, 24, 25, 32-34, 37-39, 43, 45, 47 |
| move | 7 | 9 (-1), 16 (-6), 22 (+10), 23 (-10), 28 (+5), 35 (+4), 48 (-9) |
| goto | 7 | 1->20 Hawk Canyon, 3->21 Sacramento, 27->17 Middle Willows, 40->34 Court, 41->12 Ocotillo Wells, 49->38 17 Palms, 50->19 Arroyo Salado |
| loseTurn | 5 | 12 (1), 30 (2), 36 (1), 42 (1), 46 (1) |
| rollAgain | 3 | 14, 26, 29 |
| swap | 1 | 31 |
| shortcut | 1 | 6 -> 33 Una Palma |
| dice | 1 | 44 (roll and go back # shown) |

## Special mechanics
- **Shortcut (6 "Land here and you may use cut across trail")**: an orange arrow is drawn from square 6 across the path into **Una Palma (33)**. Takes you forward 27 squares.
- **Swap (31 "Affirmative action says swap places with another player")**: pick another player and swap positions.
- **Go back # shown (44 "Reports overdue roll dice and go back # shown")**: roll again and move back that many (1-6 -> lands on 38-43).
- **Roll again**: 14, 26, 29.
- **Lose turn**: 1 turn at 12, 36, 42, 46; **2 turns** at 30 ("ouch!").
- **Chained effects**:
  - 41 "Go to Ocotillo Wells" -> 12, which is itself "Ocotillo Wells lose 1 turn" (back 29 *and* lose a turn).
  - 44 outcomes: 1->43 Fonts Point; 2->42 Stuck in Pinyon (lose 1 turn); 3->41 Go to Ocotillo Wells (->12, lose 1 turn); 4->40 Subpoena (->34 Court); 5->39 Fish Creek; 6->38 17 Palms.
  - No `move` square lands on another special square, and every goto target is plain except 41->12.
- **Big back-jumps near the end**: 41 (->12), 48 (-9), 49 (->38), 50 (->19, one square before FINISH).

## Art file
`board/desert-ranger.json` points at `art/desert-ranger-photo.jpg` (full photo downscaled to 2000x1459). The photo still needs to be committed from a local clone. x,y values in the JSON are approximate centers in the original 4913x3583 photo; multiply by 2000/4913 (about 0.4071) for the downscaled art.
