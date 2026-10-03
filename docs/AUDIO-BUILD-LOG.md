# Audio build log (branch audio-build)
_Last updated: 2026-10-03 02:46 CT by Claude Code_

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
- 2026-10-03 02:46 CT Phase 1 so far: dice (shake + 4 clatters, CC0 Kenney, 28 KB total, all within 0.2 LU of target), 90 s ambience bed (704 KB, -28.0 LUFS), synthesized rattle/truck/crickets (truck trimmed to 6 s to meet the <=6 s rule). CC0 animal recordings (crow, coyote, quail, hawk) still to source. Scripts: tools/audio/make_dice.py, make_ambience.py
- 2026-10-03 02:46 CT Phase 0.4 smoke test ran end to end (refs -> Chatterbox on MPS -> Whisper -> master -> review): 6/7 pass. `op-sr-01` is FAIL after 5 takes (0 word errors but 1.76 s vs 1.725 s cap; brisker `--ex 0.65` retakes drop the first word "Dispatch"). Deferred to the Phase 2 retake ladder; the best take (s1, 1.51 s after atempo) is what is mastered for now.
- 2026-10-03 02:15 CT Kokoro reference voices built for all 9 characters + 3 crowd refs (`audio-work/refs/`, gitignored); Chatterbox smoke-test generation started (waiting on model download)
- 2026-10-03 02:15 CT both venvs built and import-checked
- 2026-10-03 00:04 CT brew toolchain installed (ffmpeg, espeak-ng, python 3.11/3.12, node); venv builds started
- 2026-10-03 00:01 CT hand-off docs committed and pushed (ee82685); draft PR #3 opened into main
- 2026-10-03 00:01 CT `tools/audio/` scripts extracted verbatim from section 8 of the hand-off, `.gitignore` block added, log + CREDITS.md created

## Skipped / deferred (with reason)
- 1.4 optional square tie-in assets (water trickle, 2nd rattle): low priority, not started
- `dice-shake-loop.mp3` (optional hold-to-shake loop in 1.1): not made

## QA
- (not run yet)

## Decisions I made (user may want to revisit)
- Worked in a separate git worktree instead of checking out `audio-build` in the user's clone: the user's global rules say never to work in their own checkout. The clone is untouched.

## Open questions for the user
- **Browser testing target (affects Phase 5/6 acceptance):** MAMP's `htdocs/desertranger` is a symlink to the user's own clone (`~/Developer/anza-borrego-challenge`, on `main`), and the gitignored `config.php` lives there. The guardrails forbid reading/creating `config.php` and editing MAMP's config, so I will not repoint the symlink or copy it. Offline work (audio, `landing_test.js`, `rules_test.php`) is unaffected. Options for the user: (a) check out `audio-build` in the clone when ready, or (b) repoint the symlink. Will decide how far to go in Phase 5.
