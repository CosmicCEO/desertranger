# Desert Ranger — rules notes (transcribed from photo)

Source: hand-drawn board photo (`art/desert-ranger-photo.jpg`, downscaled to 2000px wide). Board data: `board/desert-ranger.json`. Left column and inner loop re-verified against a higher-resolution left-half closeup photo. All 52 squares were legible; no low-confidence readings.

## Square count
**52 squares**, indices 0–51: START (0) … FINISH (51). One die, d6.

## Square summary by type
| Type | Count | Squares |
|---|---|---|
| start / finish | 2 | 0, 51 |
| plain (place name) | 25 | 2, 4, 5, 7, 8, 10, 11, 13, 15, 17–21, 24, 25, 32–34, 37–39, 43, 45, 47 |
| move | 7 | 9 (−1), 16 (−6), 22 (+10), 23 (−10), 28 (+5), 35 (+4), 48 (−9) |
| goto | 7 | 1→20 Hawk Canyon, 3→21 Sacramento, 27→17 Middle Willows, 40→34 Court, 41→12 Ocotillo Wells, 49→38 17 Palms, 50→19 Arroyo Salado |
| loseTurn | 5 | 12 (1), 30 (2), 36 (1), 42 (1), 46 (1) |
| rollAgain | 3 | 14, 26, 29 |
| swap | 1 | 31 |
| shortcut | 1 | 6 → 33 Una Palma |
| dice | 1 | 44 (roll and go back # shown) |

## Special mechanics
- **Shortcut (6 "Land here and you may use cut across trail")**: an orange arrow is drawn from square 6 up across the path into **Una Palma (33)**. Optional, and only if you land on 6 exactly. Takes you forward 27 squares.
- **Swap (31 "Affirmative action says swap places with another player")**: you pick another player and swap positions with them.
- **Go back # shown (44 "Reports overdue roll dice and go back # shown")**: roll again and move back that many (1–6 → lands on 38–43).
- **Roll again**: 14, 26, 29.
- **Lose turn**: 1 turn at 12, 36, 42, 46; **2 turns** at 30 ("ouch!").
- **Chained effects**:
  - 41 "Go to Ocotillo Wells" → 12, which is itself "Ocotillo Wells lose 1 turn" (back 29 *and* lose a turn).
  - 44 "go back # shown" outcomes: 1→43 Fonts Point; 2→42 Stuck in Pinyon (lose 1 turn); 3→41 Go to Ocotillo Wells (→12, lose 1 turn); 4→40 Subpoena (→34 Court); 5→39 Fish Creek; 6→38 17 Palms.
  - No `move` square lands on another special square (9→8, 16→10, 22→32, 23→13, 28→33, 35→39, 48→39 are all plain), and every goto target is plain except 41→12.
- **Big back-jumps near the end**: 41 (→12), 48 (−9), 49 (→38), 50 (→19, one square before FINISH).

## Ambiguities / questions for Jerod
1. **Shortcut** — confirmed it goes to Una Palma (33)? Exact landing only, or also if you pass it? (Default: exact landing, optional.)
2. **Chained effects** — when a move/goto lands on another special square, does that square trigger too? (Matters for 41→12 lose-turn and 44 dice landing on 40/41/42.)
3. **"Go back # shown" (44)** — roll once more and go back that number? Does a second special square trigger?
4. **Swap (31)** — can you choose anyone (including someone behind you)? Must you swap, or is it optional? What if you're the only player / 1-player game?
5. **FINISH** — exact roll needed, or does overshooting count? (Board is 51 steps; squares 48–50 are all penalties, so exact-roll would make the ending very punishing.)
6. **Goto targets** — confirm: "Go to Hawk Canyon" (1) → Hawk Canyon (20, forward); "Promoted go to Sacramento" (3) → Sacramento (21, forward); VIP → Middle Willows (17); "Go to 17 Palms" (49) → 17 Palms (38), not Palm Canyon (2).
7. "Sheep Canyon closure — go back 9" (48) is treated as a plain −9 (lands on Fish Creek 39), *not* a goto Sheep Canyon (24). Correct?
8. Spelling: board says "FONTS POINT" (real name Font's Point) — keep as drawn or correct?
9. Roll-again squares — any limit on consecutive extra rolls? Do extra rolls apply if you arrive on a roll-again square via a move/goto?

## Suggested default rules
- 2–4 players, d6, everyone starts on START; highest roll goes first.
- Land on a square → apply its effect **once**. Effects **do chain** if a move/goto/dice result lands you on another special square (except rollAgain only triggers from a normal roll — prevents infinite loops). Simpler alternative if wanted: no chaining.
- Shortcut at 6: optional, exact landing only; if taken, move to 33 (no effect, Una Palma is plain).
- Swap at 31: optional; choose any other player. Skipped in solo play.
- Dice square 44: roll once, move back that many, then apply chaining rule.
- Lose N turns: skip your next N turns.
- FINISH: **overshoot allowed** (any roll reaching or passing 51 wins) — keeps the end fun given 48–50 penalties. Option: "exact roll" variant.
- Moves never go below START (0) or past FINISH.

## Art file
`board/desert-ranger.json` points at `art/desert-ranger-photo.jpg` (full photo downscaled to 2000×1459, JPEG q85). The GitHub connector used for this commit only accepts text content, so the photo was **not** committed here and still needs to be added (e.g. `git add art/desert-ranger-photo.jpg` from a local clone). x,y values in the JSON are approximate centers in the original 4913×3583 photo; multiply by 2000/4913 ≈ 0.4071 for the downscaled art.
