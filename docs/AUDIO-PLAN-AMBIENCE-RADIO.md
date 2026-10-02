# Audio plan: ambience and landing radio

Plan notes for the Desert Ranger game. This document describes a possible audio pass only: it does not add code, generate audio, or change the server/database.

## Scope and principles

- Client-side ambience is continuous but does not need to be synchronized.
- Landing radio calls use the existing `play_at` event system so the call is synchronized with the move result.
- Keep the download small, lazy-load audio after game start, and avoid server or database changes.
- Use CC0 sources only. Record every source, license, and attribution detail in the project's credits file.

## A. Continuous ambience (client-side only)

### Base loop

- Start a quiet 60–90 second desert bed (wind and distant insects) after the audio-unlock tap.
- Duck the bed beneath voice and crowd cues, then restore it smoothly.
- Provide separate ambience on/off and ambience-volume controls.
- The board view (`?board=1`) may play the ambience louder because it acts as the room speaker; keep this separate from the normal player mix.

### Random critter and distance one-shots

Schedule a one-shot at a random interval of 20–60 seconds, with randomized volume and stereo pan. Do not immediately repeat the same sound. Candidate sounds:

- crow/raven caw
- crickets
- rattlesnake rattle (rare)
- coyote yip
- quail
- hawk screech
- distant truck

Optional square tie-ins can add a little context without making ambience dependent on synchronization: a rattle near hazards and water near Palm Canyon.

### Asset and implementation constraints

- Source assets from CC0 material only (candidate sources: Sonniss GDC bundles, the Freesound CC0 filter, and Kenney).
- Log selected sources and license information in the credits file.
- Target a total ambience payload below approximately 1.5 MB; use mono assets at about 64 kbps where practical.
- Lazy-load ambience after game start.
- Keep the client implementation small (for example, a small `ambience.js` module); this plan does not call for server or database work.

## B. Landing radio call (synced)

### Trigger and mix behavior

When a piece finishes moving, emit the landing call through the existing `play_at` event system:

1. key/squelch click
2. a short ranger call, such as “Dispatch, I’m 10-8 at Fish Creek” or “On scene, Font’s Point”
3. radio squelch tail

Skip the call if another cue is already playing. Add a dedicated “radio chatter” toggle. Hazard squares may optionally get a dispatch reply, for example: “Copy, Ranger. Tow is en route.”

Player call signs may use badge numbers. Jeffery Price is Ranger 1, badge #273.

### Voice and DSP plan

- Generate the spoken material with Chatterbox voices, using 2–3 ranger voices.
- Apply a radio DSP chain: roughly 300–3000 Hz band-pass, light distortion, crackle/hiss, key-up click, and squelch tail.
- Prepare 6–8 opener templates and all 52 square names.
- Prefer recording/generating openers and place names as separate assets and stitching them in the browser to keep the download small.
- Keep optional dispatch replies similarly modular where possible.

### Asset sizing and sequencing

- Keep the radio payload small enough for a responsive first load; lazy-load it with the post-start audio pass rather than adding it to the initial page load.
- Reuse common click, hiss, and squelch assets instead of duplicating them per phrase.
- Reserve synchronization for the existing event system; no new server or database state is required by this plan.

## Open question and next checkpoint

The user has not heard samples yet. Generate a small representative sample set before full production, including at least one opener/place-name stitch, one hazard reply, and the ambience bed/one-shot mix. Review those samples before committing to the complete voice set, DSP settings, and final asset budget.

## Acceptance checklist for a future implementation

- [ ] Audio begins only after the audio-unlock tap.
- [ ] Ambience controls work independently of radio-chatter controls.
- [ ] Ambience ducks under voice/crowd cues and board mode has its intended louder mix.
- [ ] One-shots vary timing, volume, and pan without immediate repeats.
- [ ] Radio calls trigger on move completion through `play_at`, and are skipped while another cue plays.
- [ ] Radio call assets use the planned opener/place-name stitching and 2–3 voices.
- [ ] All source/license entries are recorded in the credits file.
- [ ] Ambience stays under approximately 1.5 MB and audio remains lazy-loaded.
- [ ] Samples are reviewed before full production.

## C) Dice roll sound

### Local roll feedback

- As soon as the active player taps **Roll**, play a short shake/rattle locally for immediate feedback (approximately 0.4–0.8 seconds).
- Optionally loop the shake/rattle while the Roll control is held, stopping when the hold ends or the roll is committed.
- This initial feedback is local-only and should not wait for the network or the synchronized result.

### Synchronized landing sound

- When the result appears, play a clatter/landing sound through the existing `play_at` event system so all devices hear the roll together.
- Use 3–4 take variants, rotate them randomly, and apply slight pitch variation to keep repeated rolls from sounding identical.

### Asset constraints and sourcing

- Use CC0 sources only, such as the Kenney casino/dice pack, the Freesound CC0 filter, and Sonniss.
- Log each selected source, license, and attribution detail in the credits file.
- Keep the files tiny: target less than 50 KB per sound file.

## D) Square quotables

Plan-only voice-line map derived from `board/desert-ranger.json` and `docs/RULES-NOTES.md`. A square is “quotable” when its printed text creates a distinct story beat or joke worth a dedicated line. The other squares remain **radio call only**. The lines below are short, family-friendly samples for later review; no audio is generated by this plan.

### Character cast for Chatterbox

| Character | Chatterbox voice direction | Typical use |
|---|---|---|
| Dispatch | Calm adult, clipped professional delivery, low-mid register, lightly amused under pressure; designed to survive the radio band-pass. | Movement directions, fire calls, reroutes, and radio-only landings. |
| Ranger 1 / field ranger | Warm outdoorsy adult, grounded mid-range, efficient phrasing, dry humor; badge #273 can be used for Jeffery Price. | General ranger reactions and place/effect confirmations. |
| HR representative | Bright, polished alto or tenor, quick corporate cadence, friendly but delighted by policy language. | Grievances, promotions, affirmative action, and overdue paperwork. |
| Tow-truck guy | Warm gravelly baritone, road-weary but kind, unflappable comic timing. | Breakdowns, backing accidents, flats, and being stuck. |
| Nerdy ranger | Youthful precise tenor, earnest enthusiasm, slightly over-explains ecology and archaeology. | Olla, elephant trees, shortcuts, and field observations. |
| Supervisor | Relaxed adult alto or baritone, distracted sunny vacation tone, authoritative only when remembered. | Vacation, schedule, and VIP ride-along jokes. |
| Judge | Older authoritative baritone or contralto, measured courtroom diction, long dry pauses. | Court and subpoena moments. |
| Ranger crowd | Two or three short mixed-voice exclamations, restrained and intelligible rather than a stadium roar. | Finish, roll-again wins, promotions, and stampede/shortcut reactions. |

### Landing and timing rules

- On a quotable landing, replace the generic landing radio call with one dedicated line by default. A line tagged `radio` may retain the key-up/squelch treatment; it still counts as the one landing call.
- Do not stack a generic radio opener, a quotable line, and a reply. Allow one short line plus the necessary click/tail, with a target ceiling of about 3 seconds for all landing voice audio.
- Resolve chained effects before choosing the line. For example, `41 -> 12` should get one primary Ocotillo Wells/lose-turn line, not a line for both squares; `44` should get one line for the final roll-back outcome.
- If a line would exceed the ceiling, prefer the effect line and suppress the generic radio call. If radio chatter is off, play only a non-radio cheer/aww cue when enabled.
- Squares marked “radio call only” have no dedicated character line; they use the existing generic place-name radio call (or silence when radio is disabled).

### Square-by-square line map

| Index | Square name | Board text | Effect | Proposed character | Proposed short lines | Cue |
|---:|---|---|---|---|---|---|
| 0 | Start | `START` | Start; no effect | — | **Radio call only; no dedicated line.** | radio |
| 1 | Go to Hawk Canyon | `GO TO HAWK CANYON` | Go to 20, Hawk Canyon | Dispatch | “Dispatch, rerouting to Hawk Canyon.”<br>“Copy. Scenic route, mandatory.” | radio |
| 2 | Palm Canyon | `PALM CANYON` | Place only | — | **Radio call only; no dedicated line.** | radio |
| 3 | Promoted | `PROMOTED GO TO SACRAMENTO` | Go to 21, Sacramento | HR representative | “Congratulations! Your promotion comes with a Sacramento transfer.”<br>“Upward and westward—please pack light.” | cheer |
| 4 | Sandstone Canyon | `SANDSTONE CANYON` | Place only | — | **Radio call only; no dedicated line.** | radio |
| 5 | Turkey Track | `TURKEY TRACK` | Place only | — | **Radio call only; no dedicated line.** | radio |
| 6 | Cut Across Trail | `LAND HERE AND YOU MAY USE CUT ACROSS TRAIL` | Optional exact-landing shortcut to 33, Una Palma | Nerdy ranger | “Shortcut unlocked. I love a legal trail hack.”<br>“Cut across? Efficient and dusty.” | cheer |
| 7 | Harper Flat | `HARPER FLAT` | Place only | — | **Radio call only; no dedicated line.** | radio |
| 8 | Coyote Canyon | `COYOTE CANYON` | Place only | — | **Radio call only; no dedicated line.** | radio |
| 9 | Vandalized Sign | `VANDALIZED SIGN - GO BACK 1 SPACE` | Go back 1 to Coyote Canyon (8) | Nerdy ranger | “Someone edited the sign with a very permanent marker.”<br>“Back one. Art class is over.” | aww |
| 10 | Grapevine Canyon | `GRAPEVINE CANYON` | Place only | — | **Radio call only; no dedicated line.** | radio |
| 11 | Dos Cabezas | `DOS CABEZAS` | Place only | — | **Radio call only; no dedicated line.** | radio |
| 12 | Ocotillo Wells | `OCOTILLO WELLS LOSE 1 TURN` | Lose 1 turn | Tow-truck guy | “The well has water; the schedule doesn't.”<br>“One turn cooling off—hydrate.” | aww |
| 13 | Garage | `GARAGE` | Place only | — | **Radio call only; no dedicated line.** | radio |
| 14 | Off-Road Bust | `YOU CATCH TWO OFF-ROAD MOTORCYCLES ~ ROLL AGAIN!` | Catch two off-road motorcycles; roll again | Ranger 1 / field ranger | “Two bikes, zero permits, one more roll.”<br>“Off-road? More like off-the-hook—roll again.” | cheer |
| 15 | Fault Wash | `FAULT WASH` | Place only | — | **Radio call only; no dedicated line.** | radio |
| 16 | No Extra Water | `NO EXTRA DRINKING WATER GO BACK 6 SPACES` | Go back 6 to Grapevine Canyon (10) | Dispatch | “Water check failed. Back six and refill.”<br>“No extra water? That is a six-space thirst trap.” | aww |
| 17 | Middle Willows | `MIDDLE WILLOWS` | Place only | — | **Radio call only; no dedicated line.** | radio |
| 18 | Vallecito | `VALLECITO` | Place only | — | **Radio call only; no dedicated line.** | radio |
| 19 | Arroyo Salado | `ARROYO SALADO` | Place only | — | **Radio call only; no dedicated line.** | radio |
| 20 | Hawk Canyon | `HAWK CANYON` | Place only | — | **Radio call only; no dedicated line.** | radio |
| 21 | Sacramento | `SACRAMENTO` | Place only | — | **Radio call only; no dedicated line.** | radio |
| 22 | Grievance Upheld | `GRIEVANCE UPHELD MOVE AHEAD 10` | Move ahead 10 to Una Palma (32) | HR representative | “Grievance upheld. Your paperwork just got a turbo boost.”<br>“HR says: move ahead ten—no appeal needed.” | cheer |
| 23 | Vehicle Breaks Down | `VEHICLE BREAKS DOWN GO BACK 10` | Go back 10 to Garage (13) | Tow-truck guy | “Your vehicle has filed for a ten-space retreat.”<br>“Tow truck guy says: I can be there after ten spaces.” | aww |
| 24 | Sheep Canyon | `SHEEP CANYON` | Place only | — | **Radio call only; no dedicated line.** | radio |
| 25 | Tamarisk Grove | `TAMARISK GROVE` | Place only | — | **Radio call only; no dedicated line.** | radio |
| 26 | Found an Olla | `YOU FOUND AN OLLA ROLL AGAIN` | Found an olla; roll again | Nerdy ranger | “Ancient pot, modern bonus: roll again.”<br>“Olla found! Please admire it from a respectful distance.” | cheer |
| 27 | VIP Ride Along | `V.I.P. RIDE ALONG - BACK TO MIDDLE WILLOWS` | Go back to 17, Middle Willows | Supervisor | “VIP ride along complete. Please return to Middle Willows.”<br>“Very Important Passenger, very ordinary detour.” | aww |
| 28 | Supervisor on Vacation | `MOVE AHEAD 5 SUPERVISOR ON VACATION` | Move ahead 5 to Una Palma (33) | Supervisor | “Supervisor's on vacation; the paperwork says go five.”<br>“No boss, no brakes—move ahead five.” | cheer |
| 29 | Shooters Cited | `SHOOTERS CITED - ROLL AGAIN` | Roll again | Dispatch | “Citations issued. Roll again, carefully.”<br>“That's one way to get a second chance.” | cheer |
| 30 | Backing Accident | `BACKING ACCIDENT LOSE 2 TURNS (OUCH!)` | Lose 2 turns | Tow-truck guy | “Backing accident. Everybody take two deep breaths.”<br>“Ouch! Two turns in the slow lane.” | aww |
| 31 | Affirmative Action | `AFFIRMATIVE ACTION SAYS SWAP PLACES WITH ANOTHER PLAYER` | Choose another player and swap places; optional in solo play | HR representative | “Affirmative Action says: pick a partner and swap.”<br>“A fair exchange—please keep hands inside the board.” | cheer |
| 32 | Yaqui Pass | `YAQUI PASS` | Place only | — | **Radio call only; no dedicated line.** | radio |
| 33 | Una Palma | `UNA PALMA` | Place only | — | **Radio call only; no dedicated line.** | radio |
| 34 | Court | `COURT` | Place only | Judge | “Court is in session. Please bring your best alibi.”<br>“Next case: one ranger, zero shortcuts.” | radio |
| 35 | Elephant Trees Stampede | `ELEPHANT TREES ON STAMPEDE MOVE AHEAD 4 SPACES` | Move ahead 4 to Fish Creek (39) | Nerdy ranger and ranger crowd | “Elephant trees on stampede—botany is moving!”<br>“Please do not stand under the shrubbery.” | cheer |
| 36 | Schedule Changed | `SCHEDULE CHANGED - LOSE 1 TURN` | Lose 1 turn | Supervisor | “Schedule changed. The schedule regrets nothing.”<br>“One turn off; your calendar is winning.” | aww |
| 37 | Bow Willow | `BOW WILLOW` | Place only | — | **Radio call only; no dedicated line.** | radio |
| 38 | 17 Palms | `17 PALMS` | Place only | — | **Radio call only; no dedicated line.** | radio |
| 39 | Fish Creek | `FISH CREEK` | Place only | — | **Radio call only; no dedicated line.** | radio |
| 40 | Subpoena | `SUBPOENA GO TO COURT` | Go to 34, Court | Judge | “Subpoena served. Court is not optional.”<br>“Please report to Court—bring your indoor voice.” | aww |
| 41 | Go to Ocotillo Wells | `GO TO OCOTILLO WELLS` | Go to 12, then trigger Ocotillo Wells lose 1 turn | Dispatch | “Dispatch: Ocotillo Wells, and yes, the extra penalty is real.”<br>“Go to Ocotillo Wells; one turn stays behind.” | aww |
| 42 | Stuck in Pinyon | `STUCK IN PINYON DROP OFF LOSE 1 TURN` | Drop off; lose 1 turn | Tow-truck guy | “Pinyon wins. We are officially parked.”<br>“Drop-off complete; one turn in the shade.” | aww |
| 43 | Fonts Point | `FONTS POINT` | Place only; board text intentionally has no apostrophe | — | **Radio call only; no dedicated line.** | radio |
| 44 | Reports Overdue | `REPORTS OVERDUE ROLL DICE AND GO BACK # SHOWN` | Roll again and move back that many; chained effects apply | HR representative | “Reports overdue. Roll for the size of your retreat.”<br>“The paperwork moved first—back we go.” | aww |
| 45 | Barrel Springs | `BARREL SPRINGS` | Place only | — | **Radio call only; no dedicated line.** | radio |
| 46 | Cholla Flat Tire | `CHOLLA CAUSES FLAT TIRE LOSE 1 TURN` | Lose 1 turn | Tow-truck guy | “Cholla: one, tire: zero.”<br>“Flat tire. One turn for roadside service.” | aww |
| 47 | Sunset Mountain | `SUNSET MOUNTAIN` | Place only | — | **Radio call only; no dedicated line.** | radio |
| 48 | Sheep Canyon Closure | `SHEEP CANYON CLOSURE - GO BACK 9` | Go back 9 to Fish Creek (39) | Dispatch | “Sheep Canyon is closed. Turn around nine spaces.”<br>“The trail is closed; the detour is not subtle.” | aww |
| 49 | Go to 17 Palms | `GO TO 17 PALMS` | Go to 38, 17 Palms | Dispatch | “Dispatch, redirecting to 17 Palms.”<br>“Not Palm Canyon—17 Palms. The map is very specific.” | aww |
| 50 | Ground Fire Report | `REPORT OF A GROUND FIRE AT ARROYO SALADO - GO CHECK!` | Go to 19, Arroyo Salado | Dispatch | “Ground fire at Arroyo Salado. Ranger 1, go check.”<br>“Copy. One square before the finish, naturally.” | radio |
| 51 | Finish | `FINISH !!!` | Win; overshooting counts as a win | Ranger crowd | “Finish! Nice work, Ranger.”<br>“Case closed, boots up.” | cheer |

### Selection summary

- 27 squares have dedicated quotable/story lines: 1, 3, 6, 9, 12, 14, 16, 22, 23, 26–31, 34–36, 40–42, 44, 46, 48–51.
- The remaining 25 squares are intentionally **radio call only**; their place-name landings should stay uncluttered.
- The cast is Dispatch, Ranger 1/field ranger, HR representative, tow-truck guy, nerdy ranger, supervisor, judge, and ranger crowd.
- Review a small sample set with the user before full Chatterbox production, especially the HR, tow-truck, judge, and crowd voices.
