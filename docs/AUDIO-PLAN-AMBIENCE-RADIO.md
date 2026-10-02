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
