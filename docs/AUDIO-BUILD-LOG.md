# Audio build log (branch audio-build)
_Last updated: 2026-10-03 03:10 CT by Claude Code_

## Status
| Phase | State | Notes |
|---|---|---|
| 0 Setup + samples | in progress | scaffold pushed; brew done; refs done; Chatterbox smoke test (0.4) waiting on a slow model download |
| 1 Dice + ambience + critters | in progress | dice + bed + synth critters done; CC0 animal recordings (1.3) and tie-ins (1.4) pending |
| 2 Radio + landing calls | not started | |
| 3 Quotables | not started | |
| 4 Chatter | not started | |
| 5 Client integration | not started | |
| 6 QA + wrap-up | not started | |

## Environment
macOS 27.0 (arm64, Apple Silicon), 26 GiB free at start. Work done in a git worktree, `~/Developer/anza-borrego-challenge-audio`, on branch `audio-build` (the user's own clone stays on `main`). Homebrew installed: ffmpeg 9.0.2 (all 6 required filters present), espeak-ng, Python 3.11.17 (.venv-cb) and 3.12.15 (.venv-tts), node 26.10.0. PHP for the tests will be MAMP's own (`/Applications/MAMP/bin/php/`), not a brew install. Venvs: `.venv-cb` Python 3.11.17, chatterbox-tts 0.1.7, torch 2.6.0, **MPS available: yes** (freeze in `audio-work/pip-freeze-cb.txt`); `.venv-tts` Python 3.12.15, kokoro 0.9.4, faster-whisper 1.2.1 (`audio-work/pip-freeze-tts.txt`). Kokoro also auto-installed spaCy `en_core_web_sm` 3.8.0 via pip (MIT, free). Model downloads are slow here (~0.5 MB/s inbound); the Chatterbox weights were still downloading at 02:15 CT.

## Done (newest first)
- 2026-10-03 03:10 CT Phase 0 finished: 0.5 voice distinctness fixed (see Decisions) and 0.6 sample set committed. The sample set in `review.html` has: opener+place for Senior Ranger (op-sr-01 + pl-sr-39) and Ranger 273 (op-r273-01 + pl-r273-39), hazard reply rp-dis-01, one quotable per character (q22a SR, q23a tow, q03a HR, q06a nerdy, q27a supervisor, q34a judge, q51a crowd), chatter exchange 2 (ch02-1/2/3), the ambience bed + critters and the dice. **Full production goes ahead before the user has reviewed the samples**, as the hand-off instructs; everything is regenerable from `audio-lines.json` + `cast.json` + `tools/audio/*`.
- 2026-10-03 02:46 CT Phase 1 so far: dice (shake + 4 clatters, CC0 Kenney, 28 KB total, all within 0.2 LU of target), 90 s ambience bed (704 KB, -28.0 LUFS), synthesized rattle/truck/crickets (truck trimmed to 6 s to meet the <=6 s rule). CC0 animal recordings (crow, coyote, quail, hawk) still to source. Scripts: tools/audio/make_dice.py, make_ambience.py
- 2026-10-03 02:46 CT Phase 0.4 smoke test ran end to end (refs -> Chatterbox on MPS -> Whisper -> master -> review): 6/7 pass. `op-sr-01` is FAIL after 5 takes (0 word errors but 1.76 s vs 1.725 s cap; brisker `--ex 0.65` retakes drop the first word "Dispatch"). Deferred to the Phase 2 retake ladder; the best take (s1, 1.51 s after atempo) is what is mastered for now.
- 2026-10-03 02:15 CT Kokoro reference voices built for all 9 characters + 3 crowd refs (`audio-work/refs/`, gitignored); Chatterbox smoke-test generation started (waiting on model download)
- 2026-10-03 02:15 CT both venvs built and import-checked
- 2026-10-03 00:04 CT brew toolchain installed (ffmpeg, espeak-ng, python 3.11/3.12, node); venv builds started
- 2026-10-03 00:01 CT hand-off docs committed and pushed (ee82685); draft PR #3 opened into main
- 2026-10-03 00:01 CT `tools/audio/` scripts extracted verbatim from section 8 of the hand-off, `.gitignore` block added, log + CREDITS.md created

## Skipped / deferred (with reason)
- **Flagged after the retake ladder (sample set):** `op-sr-01` (best take 1.76 s raw, 0 word errors; 1.51 s after atempo; cap 1.5 s, drops the first word "Dispatch" when brisker), `op-r273-01` (new deeper 273 voice speaks the opener slowly: best 0-error take 3.04 s raw, 2.64 s mastered; needs more takes/another rung in Phase 2), `q03a` (3.71 s raw, hr_rep; OVER-CAP, 3.17 s mastered), `q27a` (3.78 s raw, supervisor; OVER-CAP, 3.29 s mastered). q03a and q27a are on the hand-off's known-long list; the client should prefer variant b (5.4). Ladder used so far: more seeds (rung 1) and faster pacing `--ex 0.6 --cfg 0.65-0.7` (rung 2). Rungs 3-5 (`--pron`, `--alt`, Kokoro backup) are not tried yet.
- 1.4 optional square tie-in assets (water trickle, 2nd rattle): low priority, not started
- `dice-shake-loop.mp3` (optional hold-to-shake loop in 1.1): not made

## QA
- (not run yet)

## Decisions I made (user may want to revisit)
- **Pitch shift for R55 and Ranger 273 (changes `tools/audio/cast.json`):** the 0.5 check found R55 vs 273 only 9.5 Hz apart (needs >= 20). The `--alt` references did not fix it (am_echo 104 Hz, am_adam 116 Hz vs 115 Hz for 273). I changed `pitch_st`: R55 -0.5 -> **+2.0**, Ranger 273 0.0 -> **-3.0**; reference F0 is now 143 Hz vs 95 Hz (gap 48 Hz). Dispatch vs Senior Ranger is 34 Hz (OK). Side effects: 273 now sounds deeper and speaks a bit slower (ch09-2 5.4 s -> 6-7.6 s), R55 is about the same pitch as the Senior Ranger (143 Hz) but male. Easy to flip back in cast.json; the stale takes are in `audio-work/takes-old/`.
- Worked in a separate git worktree instead of checking out `audio-build` in the user's clone: the user's global rules say never to work in their own checkout. The clone is untouched.

## Open questions for the user
- **Browser testing target (affects Phase 5/6 acceptance):** MAMP's `htdocs/desertranger` is a symlink to the user's own clone (`~/Developer/anza-borrego-challenge`, on `main`), and the gitignored `config.php` lives there. The guardrails forbid reading/creating `config.php` and editing MAMP's config, so I will not repoint the symlink or copy it. Offline work (audio, `landing_test.js`, `rules_test.php`) is unaffected. Options for the user: (a) check out `audio-build` in the clone when ready, or (b) repoint the symlink. Will decide how far to go in Phase 5.
