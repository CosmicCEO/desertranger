# Hand-off: build the Desert Ranger audio (for Claude Code)

**Audience:** Claude Code, running unattended for several hours on the user's lab Mac (Apple Silicon).
**Repo:** `CosmicCEO/anza-borrego-challenge`. **Work branch:** `audio-build` (made from `prototype-m1`). **Draft PR:** `audio-build` → `main`.
**Source of truth for content:** `docs/AUDIO-PLAN-AMBIENCE-RADIO.md` (sections A ambience, B landing radio, C dice, D square quotables, E Dispatch/R55/273 chatter). Every script line from that plan is already in **`docs/audio-lines.json`**, so you don't need to parse prose.
**Written:** Oct 2, 2026 (CT). The tool recipes below were run on the build box (Linux, CPU) that evening: Kokoro references → Chatterbox takes → Whisper check → radio/clean mastering → MP3 → manifest → review page, end to end on 5 sample lines.

---

## 0. How to start (the user pastes this into Claude Code)

> You are working in my clone of CosmicCEO/anza-borrego-challenge on this Mac. First run `git fetch origin && git checkout audio-build && git pull --ff-only`, then read `docs/HANDOFF-CLAUDE-AUDIO.md` from top to bottom and follow it as your instructions. Its guardrails override anything else: work only on the `audio-build` branch, never push to `main`, never force-push, commit small and often, use only CC0 third-party sounds (each one logged in `desertranger/audio/CREDITS.md`) and free/open-source tools, never add secrets, and stop and write down the question instead of guessing on anything destructive. Work through the phases in order and tick the checkboxes as you go. Keep `docs/AUDIO-BUILD-LOG.md` updated after every task, and push to `origin audio-build` after each commit. I'm away for several hours, so don't wait for me: when something is blocked, log it as an open question, skip it, and carry on. When you finish or run out of time, update the draft PR description with the summary described in section 11.

---

## 1. Mission

Implement the whole audio plan for the Desert Ranger web game on branch `audio-build`:

1. **Dice** (plan C): a local shake when ROLL is tapped, plus a synchronized clatter when the result appears.
2. **Ambience** (plan A): a quiet looping desert bed and random critter/distance one-shots. These are local only, never synchronized.
3. **Landing radio calls** (plan B): click → short ranger call (opener + square name, stitched in the browser) → squelch tail. They are synced through the existing `play_at` event timing.
4. **Square quotables** (plan D): one dedicated character line on the 27 quotable squares, replacing the generic call.
5. **Background chatter** (plan E): occasional Dispatch↔R55 / Dispatch↔273 exchanges. These are local, quiet, random, and sit behind the radio-chatter toggle.
6. **Client integration**: `ambience.js` and the radio-call sequencing on top of `sync.js`, plus ducking, toggles, volume, the ~3 s landing cap, lazy loading and size budgets.
7. **QA and review**: a Whisper word-check of every generated line, a one-page listening sheet, the rules tests, the end-to-end simulation, and a check for zero console errors.

Definition of done: every checkbox in section 9 is ticked or explicitly logged as skipped with a reason; the game runs on MAMP at `http://localhost:8888/desertranger/` with all audio features working and no console errors; `review.html` lists every clip; the draft PR description holds the final summary.

---

## 2. Guardrails (hard rules. If a rule conflicts with anything else, the rule wins)

- **Branch:** work only on `audio-build`. Check with `git branch --show-current` before every commit. **Never push to `main`.** Never merge the PR. Never rebase or rewrite pushed history. **Never force-push** (`--force`, `--force-with-lease`, `+refspec` are all forbidden).
- **Commits:** commit small and often (one logical step per commit, at least every ~30-45 min of work). Use clear messages, e.g. `audio: phase 2 radio fx assets`. Push with plain `git push origin audio-build`. If a push is rejected (non-fast-forward), run `git pull --rebase origin audio-build` only if you have **unpushed local commits and no conflicts**. Otherwise stop and log it. If push fails for authentication, don't touch credentials: keep committing locally and log it.
- **No secrets:** don't create, read, print, or commit API keys, tokens, passwords, `.env` files or `config.php`. Don't create accounts on any website. (Freesound originals need a login: use the public preview files instead, see Phase 1.)
- **Licensing:** third-party sounds must be **CC0 only**. Each one gets a row in `desertranger/audio/CREDITS.md` with the source page URL, the direct file URL, the author, `CC0 1.0`, the date retrieved, and what you changed. **Sonniss GDC bundles are royalty-free but not CC0, so don't use them.** Log that as an open question for the user. Sounds you synthesize yourself and voices generated with Chatterbox are fine; list them in CREDITS.md as "original, generated with …".
- **Voices:** never clone a real person's voice. That includes the client, Jeffery Price, and anyone else. Reference voices come only from Kokoro preset voices (section 7).
- **Tools:** use free/open-source tools only: ffmpeg, Python, Chatterbox (MIT), Kokoro (Apache-2.0), faster-whisper (MIT), numpy/librosa/scipy, Node and Playwright that are already in `dev/e2e`. Use no paid APIs and no cloud TTS.
- **Destructive actions: stop rather than guess.** Don't delete or overwrite anything you didn't create on this branch. Don't drop or alter database tables, don't edit MAMP's config, don't `rm -rf` outside `audio-work/`, and don't run `git reset --hard` or `git clean`. Don't change game rules (`lib/rules.php`) or the board JSON. If a step seems to need any of these, write the question in the log, skip it, and continue with the next task.
- **Allowed server change (exactly one):** stamping `play_at_ms` on every turn/win event in `lib/game.php` (Phase 5, task 5.1). There are no schema changes and no new endpoints. Anything beyond that is an open question, not an action.
- **Binary hygiene:** commit only the **shipped** MP3s under `desertranger/audio/` plus their `manifest.json`. **Never commit** WAV masters, takes, reference clips, model files or venvs. They live in `audio-work/` and `.venv-*`, which you add to `.gitignore` in Phase 0. Re-commit an MP3 only when its final version changes, to keep history small.
- **Resource rule:** **never run Chatterbox and Whisper at the same time.** That means one heavy model process at a time. Don't run two generators in parallel either.
- **Time-box:** if one item eats more than ~45 minutes without progress, log it, skip it, and move on.

---

## 3. Read first, and what you need to know about the code

Read these on `audio-build`: `docs/AUDIO-PLAN-AMBIENCE-RADIO.md`, `docs/PROTOTYPE.md`, `docs/AUDIO-RESEARCH.md`, `docs/audio-lines.json`, `desertranger/assets/js/{sync,app,board}.js`, `desertranger/lib/{game,rules}.php`, `desertranger/index.html`, `desertranger/tests/*`, `dev/e2e/*`, and `design/scripts/*` (the crowd-audio scripts. Section 8 reuses their recipes).

Facts that shape the work:

- **No build step.** The client is plain ES5-style JavaScript in IIFEs, loaded by `<script>` tags in `index.html` with `?v=1` cache-busters. Keep that style: no modules, no bundler, no npm runtime dependencies.
- **Synced cues today:** `lib/rules.php::finishAction()` returns one cue per action (`cheer` for a win or roll-again, `aww` for any lose-turn or a setback of ≥5). `lib/game.php::dr_add_event()` writes `play_at_ms = now + cue_lead_ms` (1500 ms) **only when a cue is set**. The first log line of the turn carries `payload.steps` (animation steps) plus `cue`/`play_at_ms`. `assets/js/app.js::onState()` calls `Sound.schedule(ev.cue, ev.playAt)`. `sync.js` converts server time to local time with the NTP-style offset (`DRClock`), schedules on the Web Audio clock, starts up to 250 ms late with an offset into the clip, and skips anything later than that.
- **Animation:** `board.js` queues steps as they arrive by poll. These step types matter: `roll` (550 ms), each `walk` hop (`HOP_MS` 260, then 250 ms after the walk), and `jump`/`swap` (`JUMP_MS` 750). Pieces snap to the server position whenever the queue is empty, so if you delay an animation, push a wait task into the queue first (see 5.2).
- **Audio files today:** `desertranger/assets/audio/crowd-{cheer,aww}-v2.mp3` (gitignored binaries delivered in a zip). **New audio goes in `desertranger/audio/`**, which is *not* gitignored, so the shipped MP3s get committed. Leave the two crowd files where they are and keep using them.
- **Apache caches MP3 for 30 days** (`.htaccess`). Always load clips as `audio/<file>?v=<manifest v-hash>`. `.htaccess` blocks `*.md`, so `CREDITS.md` isn't web-served. That's fine.
- **Tests:** `php desertranger/tests/rules_test.php` (45 checks, exit 0), `php desertranger/tests/simulate_game.php http://localhost:8888/desertranger 4`, and the headless-Chrome e2e in `dev/e2e` (`npm install`, then `CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" node e2e.js http://localhost:8888/desertranger/`).
- **The board:** 52 squares (0-51) in `board/desert-ranger.json`. In a repo checkout, `api.php?a=board` serves it.

---
## 4. Environment setup (macOS, Apple Silicon)

Run everything from the repo root (e.g. `~/code/anza-borrego-challenge`). The first runs download models from Hugging Face without a token (Chatterbox ≈ 3 GB, Kokoro ≈ 330 MB, faster-whisper `small.en` ≈ 470 MB). Make sure you have about 15 GB free.

### 4.1 Homebrew packages
```bash
brew install ffmpeg espeak-ng python@3.11 python@3.12
ffmpeg -version | head -1          # need ffmpeg >= 6: the recipes use asoftclip, acrusher, alimiter, ebur128, acrossfade
ffmpeg -hide_banner -filters | grep -E " (asoftclip|acrusher|alimiter|ebur128|acrossfade|silenceremove) " | wc -l   # expect 6
```
`espeak-ng` is Kokoro's fallback phonemizer for out-of-vocabulary words.

### 4.2 Chatterbox venv (Python 3.11, `setuptools<81`)
These versions are the exact set that worked on the build box: chatterbox-tts 0.1.7, torch 2.6.0, torchaudio 2.6.0, transformers 5.2.0, diffusers 0.29.0, numpy 1.26.4, librosa 0.11.0, safetensors 0.5.3, resemble-perth 1.0.1, s3tokenizer 0.3.0, conformer 0.3.2, setuptools 80.10.2.
```bash
/opt/homebrew/bin/python3.11 -m venv .venv-cb
source .venv-cb/bin/activate
python -m pip install --upgrade pip wheel "setuptools<81"
pip install "chatterbox-tts==0.1.7"        # pins torch/torchaudio 2.6.0, transformers 5.2.0, diffusers 0.29.0, numpy<2
pip install "setuptools<81"                # re-assert: resemble-perth (the watermarker) imports pkg_resources,
                                           # which setuptools 81 removed -> "No module named pkg_resources"
python - <<'PY'
import pkg_resources, perth, torch, torchaudio
from chatterbox.tts import ChatterboxTTS
print("torch", torch.__version__, "| mps available:", torch.backends.mps.is_available())
PY
deactivate
```
If `chatterbox-tts==0.1.7` can't be resolved, install the newest `chatterbox-tts`, keep `setuptools<81`, and record the versions (`pip freeze > audio-work/pip-freeze-cb.txt`) in the log.

**MPS vs CPU:**
- Chatterbox 0.1.7's `from_pretrained(device="mps")` loads weights on CPU and moves them to MPS. It falls back to CPU by itself if MPS isn't built or available.
- Always `export PYTORCH_ENABLE_MPS_FALLBACK=1` (`gen_lines.py` sets it), so ops that aren't implemented run on CPU instead of crashing.
- `gen_lines.py --device auto` tries MPS first. If a generation throws (`RuntimeError`/`NotImplementedError`, "MPS backend out of memory"), it reloads on CPU and carries on.
- Also switch to `--device cpu` by hand if MPS output is garbled. A sign of that: in the first ~10 lines, more than half the MPS takes fail the Whisper check, but the same lines pass on CPU.
- Seeds don't reproduce across devices. The device is recorded per take in `audio-work/takes.jsonl`.
- Speed reference: on the build box's CPU (4 threads), a short line took 9-22 s per take. Budget about 2-2.5 h of CPU for all ~216 lines × 3 takes. MPS is usually faster.

### 4.3 Kokoro + Whisper venv (backup TTS, reference voices, QA)
This set worked on the build box: Python 3.12, kokoro 0.9.4, misaki 0.9.4, faster-whisper 1.2.1, ctranslate2 4.8.2. Python 3.11 works too.
```bash
/opt/homebrew/bin/python3.12 -m venv .venv-tts
source .venv-tts/bin/activate
python -m pip install --upgrade pip wheel
pip install "kokoro==0.9.4" "misaki[en]==0.9.4" soundfile librosa scipy "faster-whisper==1.2.1"
python -c "from kokoro import KPipeline; from faster_whisper import WhisperModel; print('ok')"
deactivate
```
- Kokoro runs fine on CPU and is fast (82M parameters). You don't need MPS for it.
- faster-whisper (CTranslate2) is CPU-only on macOS. Use `device="cpu", compute_type="int8"`.
- Keep the two venvs separate: Chatterbox needs `numpy<2`, while the Kokoro/Whisper stack resolves numpy 2.x.
- **Kokoro is also the backup TTS.** If Chatterbox can't produce a passing take for a line after the retake ladder (section 10), you may ship a Kokoro take of that line with the character's Kokoro voice and speed from `cast.json`. Run it through the same mastering chain and mark it `engine: kokoro` in the log.

### 4.4 One heavy model at a time
**Never run Chatterbox (`gen_lines.py`) and Whisper (`qa_check.py`) at the same time.** Both are memory- and CPU-heavy (unified memory on Apple Silicon). Running them together risks swapping and slows both down. Work in batches instead: generate a batch → QA the batch → master the batch → commit.

### 4.5 The game on MAMP
- The game runs at **http://localhost:8888/desertranger/** (MAMP Apache 8888, MySQL 8889; see `docs/PROTOTYPE.md` → "Run it on a Mac with MAMP").
- Health check: `curl -s http://localhost:8888/desertranger/api.php?a=time` should return `{"ok":true,...}`.
- If MAMP isn't running, `open -a MAMP` and start the servers.
- If the database or `config.php` is missing, don't create or edit them. Log it, skip the in-browser checks, and keep doing the offline audio work.
- The review page will be at **http://localhost:8888/desertranger/audio/review.html**.

### 4.6 Scratch space and `.gitignore` (Phase 0 does this)
Add these lines to `.gitignore` and commit:
```
# audio build scratch (takes, refs, masters, QA) and Python venvs
audio-work/
.venv-cb/
.venv-tts/
__pycache__/
```

---

## 5. Folder layout and file naming

```
docs/
  audio-lines.json            every script line (machine-readable; see "Fields" below). Source of truth for text.
  HANDOFF-CLAUDE-AUDIO.md     this file
  AUDIO-BUILD-LOG.md          your running log (create in Phase 0)
tools/audio/                  build scripts (section 8): cast.json, make_refs.py, gen_lines.py, qa_check.py,
                              master.py, build_review.py, make_ambience.py, make_dice.py
audio-work/                   GITIGNORED scratch: refs/, takes/<id>/s<seed>.wav, qa/<id>.json, master/, src/ (downloads)
desertranger/audio/           SHIPPED (committed) web assets, all mono MP3
  manifest.json               id -> {file, sec, bytes, v(hash), character, text, square, kind, lufs, ...}
  CREDITS.md                  every third-party source + generated-content notes
  review.html                 listening sheet (generated)
  dice/    dice-shake-01.mp3, dice-clatter-01..04.mp3
  amb/     amb-bed-01.mp3, amb-crow-01.mp3, amb-crickets-01.mp3, amb-rattle-01.mp3, amb-coyote-01.mp3,
           amb-quail-01.mp3, amb-hawk-01.mp3, amb-truck-01.mp3 (…-02 for extra variants)
  radio/fx/       radio-click-01.mp3, radio-squelch-01..03.mp3, radio-hiss-loop.mp3
  radio/openers/  op-sr-01..08.mp3 (Senior Ranger), op-r273-01..08.mp3 (Ranger 273)
  radio/places/   pl-sr-00..51.mp3, pl-r273-00..51.mp3   (two-digit square index)
  radio/replies/  rp-dis-01..03.mp3 (optional)
  quotes/  q01a.mp3, q01b.mp3 … q51b.mp3                 (q + 2-digit square + variant a/b)
  chatter/ ch01-1.mp3 … ch12-4.mp3                       (ch + 2-digit exchange + line number)
desertranger/assets/js/
  sync.js       (extend: buses, ducking, lazy clip loader, generic scheduleBuffer)
  ambience.js   (new: bed + critters + background chatter scheduler)
  radio.js      (new: landing-call picker + stitcher + dice clatter scheduling)
```
**Naming rules:** lowercase, hyphens, no spaces. The ID equals the file stem (`q22a` → `quotes/q22a.mp3`). Square numbers are always 2-digit. Variants are `-01`, `-02`… for SFX and `a`/`b` for quotables. Don't rename IDs from `audio-lines.json`. If you add lines (e.g. extra crowd sweeteners), use new IDs and log them.

**`audio-lines.json` fields:**
- `id`, `character`, `text` (exact script text, used for display and the Whisper check)
- `square` (0-51 or null), `cue` (`radio`/`cheer`/`aww`/`chatter`), `phase` (2/3/4)
- `kind`: `opener`, `place`, `reply`, `quotable` or `chatter`
- `treatment`: `radio`, `clean` or `crowd`
- `file` (relative to `desertranger/audio/`), `max_sec` (voice length ceiling after trimming)
- optional fields:
  - `tts_text`: the TTS input with numbers and codes spelled out (e.g. "10-4" → "ten-four", "R55" → "R fifty-five", "273" → "two seventy-three")
  - `pronounce`: respellings to try only if the plain text is mispronounced
  - `whisper_ignore`: Latin words Whisper can't spell, so the check skips them
  - `note`, `exchange`, `line_no`, `tie_in_square`, `optional`, `proposed_phrase` (action-square place phrase to review)
- The top-level `squares` array marks which squares are quotable. `chatter_exchanges` groups chatter lines in order.

---

## 6. Loudness, formats and size budgets

| Asset class | Target (integrated) | True peak | Notes |
|---|---|---|---|
| Voice cues: quotables, openers, place names, replies | **−16 LUFS** | ≤ −1.5 dBTP | after the radio/clean chain |
| Crowd group line (q51) | −14 LUFS | ≤ −1.5 dBTP | layered voices |
| Existing crowd cheer/aww (`crowd-*-v2.mp3`) | **−12 LUFS** (as shipped) | ≤ −1.0 dBTP | don't re-master them |
| Dice clatter / shake | −18 / −20 LUFS | ≤ −1.5 dBTP | peak mode (−6 dBFS) if a clip is < 0.4 s |
| Ambience bed | **−28 LUFS** | ≤ −6 dBTP | runtime volume slider on top |
| Critter one-shots | −26 LUFS | ≤ −3 dBTP | runtime random −8…0 dB, random pan |
| Background chatter lines | −16 LUFS baked | ≤ −1.5 dBTP | played at runtime gain ≈ 0.35 (≈ −25 LUFS effective) |
| Radio hiss loop | −40 LUFS | — | played under each call at gain ≈ 0.5 |
| Radio click / squelch | peak ≈ −6 dBFS | — | too short for LUFS gating |

- **Measuring:** use `ffmpeg -af ebur128=peak=true` on the **final MP3**, not the WAV. `master.py` iterates gain plus a 4×-oversampled limiter until the MP3 is within ±0.3 LU of target. That's the `design/scripts/crowd_norm.py` method, generalized. Don't use one-pass `loudnorm` on short clips: its dynamic mode pumps on clips under 3 s.
- **Format:** **mono MP3, 44.1 kHz, 64 kbps** (`libmp3lame -b:a 64k -ac 1`) for everything new. 96 kbps is allowed for the ambience bed or critters if 64 kbps swirls audibly.
- **Opus is optional:** only if a budget below can't be met at 64 kbps MP3. Then ship `.ogg` Opus at 48 kbps **plus** the MP3. The client tries `decodeAudioData` on the Opus file and falls back to the MP3 on error, because older Safari can't decode Ogg Opus. Log it if you do this.
- **MP3 padding:** MP3 adds ~25-50 ms of encoder padding. **Never rely on MP3 for gapless joins:**
  - trim leading and trailing near-silence from decoded buffers at runtime (threshold ≈ 0.003) before stitching opener + place;
  - loop the ambience bed and the hiss with overlapping sources and a short equal-power crossfade (1.5 s for the bed, 0.2 s for the hiss), not `loop=true` on a raw MP3.

**Size budgets** (new files under `desertranger/audio/`; check with `du -k`):

| Group | Budget |
|---|---|
| Dice (all files) | ≤ 250 KB, **each < 50 KB** |
| Ambience bed + critters | **≤ 1.5 MB** (bed ≈ 90 s × 8 KB/s ≈ 720 KB) |
| Radio FX | ≤ 60 KB |
| Openers + 104 place names | ≤ 1.1 MB |
| Quotables (54) | ≤ 1.3 MB |
| Chatter (39 lines) | ≤ 0.9 MB |
| Replies (optional) | ≤ 60 KB |
| **Total new audio** | **≤ 5 MB** |
| Tier A (loaded on audio unlock: dice, radio fx) | ≤ 300 KB |

---
## 7. Voice casting

**Reference-voice approach** (the one used for the earlier samples in `design/scripts/cb_refs.py` and `crowd_v2_refs.py`):
1. Synthesize a 10-17 s reference clip per character with a **Kokoro preset voice** (`make_refs.py`). Each reference reads an in-character paragraph (`ref_text` in `cast.json`) at a set speed, with optional librosa pitch shift.
2. **Clone** that clip zero-shot with Chatterbox (`audio_prompt_path=<ref>`) and generate every line with that character's `exaggeration` / `cfg_weight` / `temperature`.
3. Never use recordings of real people as references.

Chatterbox knobs: higher `exaggeration` makes delivery more emphatic and a little faster. Lower `cfg_weight` makes pacing slower and more deliberate, which also helps when a reference talks fast. Use `temperature` 0.8 (the default) except for the Judge (0.7). Every other `generate()` setting stays at the 0.1.7 defaults (`repetition_penalty=1.2, min_p=0.05, top_p=1.0`). Output is 24 kHz mono and carries Resemble's inaudible Perth watermark, which is fine for a game. Note it in CREDITS.md.

| Character | Plan direction (sections D/E) | Kokoro reference (voice · speed · pitch) | Chatterbox `ex` / `cfg` / `temp` | Alt reference | Lines |
|---|---|---|---|---|---|
| **Dispatch** | Calm adult, clipped professional, low-mid, lightly amused; must survive the band-pass | `af_sarah` · 1.05 · 0 st | 0.40 / 0.50 / 0.8 | `af_nova` −0.5 st | replies, chatter |
| **Senior Ranger (female)** | **Calm, commanding, no-nonsense, dry humor; mature alto, steady pace, clipped radio delivery, moderate exaggeration.** Authoritative field ranger, *not* Dispatch | `af_kore` · 0.92 · **−2 st** | **0.50 / 0.50** / 0.8 | `af_river` −2 st | 12 quotable squares (24 lines), generic-call rotation (8 openers + 52 places) |
| **Ranger 273 / field ranger** (Jeffery Price is Ranger 1, badge #273, but the voice is *not* his) | Warm outdoorsy, grounded mid-range, efficient, dry; names plants by family/genus/species | `am_michael` · 1.00 · 0 st | 0.50 / 0.50 / 0.8 | `am_adam` 0 st | generic-call rotation (8 openers + 52 places), nature-walk chatter |
| **R55** | Male ranger, distinct from Senior Ranger, Dispatch and 273 | `am_liam` · 1.00 · −0.5 st | 0.55 / 0.45 / 0.8 | `am_echo` 0 st | chatter |
| **HR representative** | Bright, polished, quick corporate cadence, delighted by policy | `af_heart` · 0.90 · 0 st (the `cb_refs.py` "hr" ref) | 0.45 / 0.50 / 0.8 | `af_bella` | 3, 31, 44 |
| **Tow-truck guy** | Warm gravelly baritone, road-weary, kind, unflappable | `am_fenrir` · 0.95 · −1 st (the "rough" ref) | 0.60 / 0.40 / 0.8 (tested in `cb_gen.py`) | `am_onyx` −1 st | 23, 30, 42 |
| **Nerdy ranger** | Youthful precise tenor, earnest, over-explains | `am_eric` · 1.15 · +0.5 st (the "ranger" ref) | 0.70 / 0.40 / 0.8 (tested) | `am_puck` +1 st | 6, 26, 35 |
| **Supervisor** | Relaxed, distracted sunny vacation tone | `am_puck` · 0.95 · −0.5 st | 0.45 / 0.50 / 0.8 | `am_adam` | 27, 28, 36 |
| **Judge** | Older authoritative, measured courtroom diction, long dry pauses | `am_onyx` · 0.85 · −2 st | 0.35 / **0.30** / 0.7 | `am_michael` −3 st | 34, 40 |
| **Ranger crowd** | 2-3 short mixed voices, restrained, intelligible | refs `w_bella` (af_bella +1 st), `m_michael` (0), `m_fenrir` (−1.5 st), speed 1.15, energetic text (`make_refs.py --crowd`) | 0.70 / 0.40 / 0.8 | the other 7 `crowd_v2_refs.py` refs | 51 (layered); sweetener under 35 |

**Distinctness check (Phase 0):** median F0 between **Dispatch** and the **Senior Ranger** must differ by ≥ 20 Hz. The same goes for **R55** vs **Ranger 273**. Measure with `design/scripts/analyze.py`'s pyin method on 3 takes each. If two voices fail the check, regenerate that character's reference with `make_refs.py <char> --alt` and log which one you picked.

**Generic-call rotation:** successive generic landings alternate Senior Ranger and Ranger 273 (section 9, Phase 5). Dispatch is never part of that rotation.

---
## 8. Tools and exact recipes

Create these files under `tools/audio/` in Phase 0 by copying the code blocks verbatim, then commit them. Run them from the repo root. The scripts were run on the build box on Oct 2, 2026: 5 sample lines went through every step, and the issues found (a long Whisper prompt caused hallucinations, short clips fall under the LUFS gate, openers were too long) are already fixed below.

### 8.1 The radio DSP chain (ffmpeg)
Voice clips get the band-limited "radio" color baked in offline. The hiss bed, key-up click and squelch tail are **shared assets added at runtime**, so stitched opener + place calls have no seams and FX aren't duplicated per phrase.
```bash
RADIO="highpass=f=300:poles=2,highpass=f=300:poles=2,lowpass=f=3000:poles=2,lowpass=f=3000:poles=2,\
acompressor=threshold=-20dB:ratio=4:attack=5:release=90:makeup=2,equalizer=f=1700:t=q:w=1.0:g=4,\
volume=8dB,asoftclip=type=tanh,volume=-8dB,acrusher=bits=12:mix=0.25:mode=log,highpass=f=300,lowpass=f=3200"
TRIM="silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02,areverse,\
silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.04,areverse"
ffmpeg -y -i take.wav -af "aresample=48000,$TRIM,$RADIO" -ac 1 voice_radio.wav     # then loudness-normalise (master.py)
```
- Band-pass ≈ 300-3000 Hz: two cascaded 2-pole high-pass and low-pass filters give a 24 dB/oct skirt.
- Light overdrive: +8 dB into `asoftclip` tanh, then −8 dB.
- Grit: `acrusher` at a 25 % mix.
- Nasal presence: +4 dB at 1.7 kHz.

Shared FX (`master.py --fx` builds these; the recipes are in the script):
- **key-up click:** 6 ms of high-passed white noise followed by a 30 ms 1.2 kHz blip.
- **squelch tail:** a 0.18-0.26 s white-noise burst, band-passed 500-4000 Hz, +6 dB at 2.5 kHz, exponential decay. There are 3 variants.
- **hiss:** a 4 s pink-noise loop band-passed 300-3000 Hz at −40 LUFS.

The runtime call is: click → (voice clips over hiss at gain ≈ 0.5) → squelch.

### 8.2 Clean (in-person) chain
`highpass=f=80,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=1,equalizer=f=3500:t=q:w=1:g=1.5`

Which chain a line gets is set by `treatment` in `audio-lines.json`. Dispatch, Senior Ranger, 273 and R55 lines always get the radio chain, as do lines whose plan cue is `radio` (34 Judge, 50). HR, tow-truck, nerdy ranger, supervisor and Judge-on-40 get the clean chain. That's one reading of plan D ("a line tagged `radio` may retain the key-up/squelch treatment"). Log it as a decision the user can flip.

### 8.3 Ambience bed (synthesized, so it's license-clean) and the loop crossfade
This produces a 90 s loop at ≈ −28 LUFS that was tested on the build box. It mixes wind (modulated brown noise), gusts (band-passed pink) and two distant cricket layers.
```bash
mkdir -p audio-work/amb
ffmpeg -y -f lavfi -i "anoisesrc=d=92:c=brown:a=0.5:r=44100:s=7" -f lavfi -i "anoisesrc=d=92:c=pink:a=0.3:r=44100:s=11" \
  -f lavfi -i "sine=f=4400:d=92:r=44100" -f lavfi -i "sine=f=5100:d=92:r=44100" -filter_complex \
"[0]lowpass=f=380,highpass=f=40,volume='0.55+0.3*sin(2*PI*t/13)+0.15*sin(2*PI*t/5.3)':eval=frame[w];\
[1]bandpass=f=1400:w=1800,volume='0.12*pow(0.5+0.5*sin(2*PI*t/9.1),3)':eval=frame[g];\
[2]tremolo=f=32:d=1,volume='0.03*gt(sin(2*PI*t*1.3),0.2)':eval=frame[c1];\
[3]tremolo=f=27:d=1,volume='0.02*gt(sin(2*PI*t*0.9+1),0.3)':eval=frame[c2];\
[w][g][c1][c2]amix=inputs=4:normalize=0,aformat=channel_layouts=mono" audio-work/amb/bed_raw.wav
# seamless loop: crossfade the last 2 s into the first 2 s (two inputs; a single-input asplit version hangs)
ffmpeg -y -i audio-work/amb/bed_raw.wav -i audio-work/amb/bed_raw.wav -filter_complex \
"[0]atrim=start=2,asetpts=N/SR/TB[body];[1]atrim=end=2,asetpts=N/SR/TB[head];[body][head]acrossfade=d=2:c1=tri:c2=tri" audio-work/amb/bed_loop.wav
```
- ffmpeg's `tremolo` can't go below 0.1 Hz, so slow LFOs use `volume=…:eval=frame` expressions instead.
- You may replace or blend in a CC0 field recording of desert wind if you find a good one, logged in CREDITS.md. Keep the result under budget.

### 8.4 Synthesized critters (tested); use CC0 recordings for animals that can't be synthesized
```bash
# rattlesnake rattle (rare): 52 Hz amplitude-modulated hiss
ffmpeg -y -f lavfi -i "anoisesrc=d=1.4:c=white:a=0.8:r=44100:s=3" -af "highpass=f=3500,lowpass=f=9000,volume='0.5+0.5*sin(2*PI*52*t)':eval=frame,afade=t=in:d=0.08,afade=t=out:st=0.9:d=0.5" -ac 1 audio-work/amb/rattle.wav
# distant truck pass-by: low rumble + engine hum with a Gaussian swell
ffmpeg -y -f lavfi -i "anoisesrc=d=7:c=brown:a=0.9:r=44100:s=4" -f lavfi -i "sine=f=55:d=7:r=44100" -filter_complex "[0]lowpass=f=260,highpass=f=35[n];[1]volume=0.15,vibrato=f=0.3:d=0.3[e];[n][e]amix=inputs=2:normalize=0,volume='exp(-pow((t-3.5)/1.6,2))':eval=frame" -ac 1 audio-work/amb/truck.wav
# cricket burst
ffmpeg -y -f lavfi -i "sine=f=4600:d=3:r=44100" -af "tremolo=f=38:d=1,volume='gt(sin(2*PI*2.2*t),0.35)':eval=frame,afade=t=in:d=0.2,afade=t=out:st=2.5:d=0.5,highpass=f=2500" -ac 1 audio-work/amb/crickets.wav
```
- The crow/raven caw, coyote yip, quail and hawk screech need real recordings. Source them under CC0 (Phase 1).
- If you can't find a good CC0 recording for one of them, skip it and log it. Don't fake it badly.

### 8.5 Loudness normalization
`master.py::norm_mp3()` applies static gain, then `aresample=176400,alimiter=limit=<tp-0.5>dB:attack=1:release=50:level=false,aresample=44100`, encodes the MP3, re-measures the MP3 with `ebur128=peak=true`, and repeats up to 10× until it's within ±0.3 LU and under the true-peak limit. Clips too short for the 400 ms LUFS gate (FX, some dice) are peak-normalized instead. For non-voice assets, call it from a one-liner:
```bash
python3 -c "import sys; sys.argv=['x']; exec(open('tools/audio/master.py').read().split('MAN =')[0]); print(norm_mp3('audio-work/amb/bed_loop.wav','desertranger/audio/amb/amb-bed-01.mp3',-28,64,-6))"
```
Or factor `norm_mp3` into `tools/audio/audiolib.py`, which is cleaner. Either way, register every shipped file in `manifest.json` (`kind`: `dice`/`amb`/`critter`/`fx`) so the review page and the client can see it.

### 8.6 Crowd group line (q51) and the crowd sweetener (q35)
- **q51:** `gen_lines.py --ids q51a,q51b` generates every `ranger_crowd` line once per crowd ref (`_v0/_v1/_v2`). `master.py` layers the best take per voice with 0/25/55 ms onset offsets at gains 1.0/0.8/0.7, then applies the clean chain at −14 LUFS. The existing `crowd-cheer-v2.mp3` follows on the win cue.
- **q35 sweetener:** layer 3-4 short "whoa!"/"woo!" takes under the last ~0.6 s of q35a/b at −12 dB. Get them from the crowd refs with `gen_lines.py`-style calls (`ex=1.0, cfg=0.3`, text like `"Whoa!!!"`, truncated at 3 s like `crowd_v2_cb.py`), or from Kokoro excited takes as in `crowd_v2_refs.py`. Keep it subtle and log the takes used.
- The full stadium mix recipe (pitch/time variation, distance low-pass, claps, IR reverb, parallel compression, −12 LUFS) is `design/scripts/crowd_v2_mix.py` + `crowd_v2_norm.py`. You **don't** need it unless you remake cheer/aww, which isn't in scope.

### 8.7 `tools/audio/cast.json`
```json
{
 "_about": "Voice casting for the Desert Ranger audio build. ref = Kokoro voice used to synthesise a ~10-12 s reference clip (make_refs.py), which Chatterbox then clones zero-shot (gen_lines.py). speed/pitch_st shape the reference; ex/cfg/temp are Chatterbox generate() params. 'alt' is the fallback reference if the main one fails the distinctness or QA checks. Do NOT clone any real person's voice.",
 "dispatch":      {"ref": "af_sarah",   "speed": 1.05, "pitch_st": 0.0,  "ex": 0.40, "cfg": 0.50, "temp": 0.8, "alt": {"ref": "af_nova", "pitch_st": -0.5},
                   "ref_text": "Copy that, unit two. Your location is logged. Fire crew is staging at the north gate, tow is en route from Borrego, and the road past mile marker nine stays closed until further notice. Advise when clear."},
 "senior_ranger": {"ref": "af_kore",    "speed": 0.92, "pitch_st": -2.0, "ex": 0.50, "cfg": 0.50, "temp": 0.8, "alt": {"ref": "af_river", "pitch_st": -2.0},
                   "ref_text": "Listen up. The wash is closed past the second marker, and I mean closed. Turn your vehicles around, check your water, and report back to me in ten minutes. No exceptions. No excuses. And yes, I did see that cactus. Everybody saw that cactus."},
 "ranger_273":    {"ref": "am_michael", "speed": 1.00, "pitch_st": 0.0,  "ex": 0.50, "cfg": 0.50, "temp": 0.8, "alt": {"ref": "am_adam", "pitch_st": 0.0},
                   "ref_text": "Alright folks, gather in close. This tall one with the red tips is the ocotillo. It looks dead most of the year, but give it one good rain and it leafs out in a couple of days. Family first, common name second. Watch your step on the way back."},
 "r55":           {"ref": "am_liam",    "speed": 1.00, "pitch_st": -0.5, "ex": 0.55, "cfg": 0.45, "temp": 0.8, "alt": {"ref": "am_echo", "pitch_st": 0.0},
                   "ref_text": "Yeah, Dispatch, I copy. I'm crossing the highway now, should be back in service in about twenty. It's a hundred and nine out here and the truck's air conditioning is making a noise I don't love. Over."},
 "hr_rep":        {"ref": "af_heart",   "speed": 0.90, "pitch_st": 0.0,  "ex": 0.45, "cfg": 0.50, "temp": 0.8, "alt": {"ref": "af_bella", "pitch_st": 0.0},
                   "ref_text": "Thank you for your patience. After careful review of the submitted documentation, the committee has reached a decision. Please direct any further questions to the human resources portal."},
 "tow_guy":       {"ref": "am_fenrir",  "speed": 0.95, "pitch_st": -1.0, "ex": 0.60, "cfg": 0.40, "temp": 0.8, "alt": {"ref": "am_onyx", "pitch_st": -1.0},
                   "ref_text": "Yeah, well, look, these things happen, buddy. The engine's shot, the tires are bald, and frankly I don't see it getting fixed anytime soon. Real shame."},
 "nerdy_ranger":  {"ref": "am_eric",    "speed": 1.15, "pitch_st": 0.5,  "ex": 0.70, "cfg": 0.40, "temp": 0.8, "alt": {"ref": "am_puck", "pitch_st": 1.0},
                   "ref_text": "Oh gosh, okay, so, um, technically the trail is closed! I did put up a sign. Actually I put up three signs. Did nobody read the signs? Oh no."},
 "supervisor":    {"ref": "am_puck",    "speed": 0.95, "pitch_st": -0.5, "ex": 0.45, "cfg": 0.50, "temp": 0.8, "alt": {"ref": "am_adam", "pitch_st": 0.0},
                   "ref_text": "Hey team, quick update from the beach. Signal's kind of spotty out here, so I'll keep it short. Everybody just do whatever the schedule says. Unless the schedule changed. Did the schedule change? Anyway, great work, see you Monday."},
 "judge":         {"ref": "am_onyx",    "speed": 0.85, "pitch_st": -2.0, "ex": 0.35, "cfg": 0.30, "temp": 0.7, "alt": {"ref": "am_michael", "pitch_st": -3.0},
                   "ref_text": "The court has reviewed the record. The defendant was observed... departing the designated trail. Twice. Counsel will refrain from describing the cactus as a witness. We will reconvene after lunch."},
 "ranger_crowd":  {"refs": ["w_bella", "m_michael", "m_fenrir"], "ex": 0.70, "cfg": 0.40, "temp": 0.8,
                   "_note": "Group lines (q51a/b). Build these three refs with the crowd_v2_refs.py recipe (Kokoro af_bella +1 st, am_michael 0 st, am_fenrir -1.5 st, speed 1.15, energetic text). Generate each voice separately, then layer (see master.py --crowd)."}
}
```

### 8.8 `tools/audio/make_refs.py` (`.venv-tts`)
```python
#!/usr/bin/env python3
"""Kokoro venv. Build ~10-12 s reference clips for Chatterbox cloning.
usage: python tools/audio/make_refs.py [character ...] [--alt]    |    --crowd  (w_bella, m_michael, m_fenrir)
writes audio-work/refs/<character>.wav (or <character>.alt.wav with --alt)"""
import json, sys, os, warnings; warnings.filterwarnings("ignore")
import numpy as np, soundfile as sf, librosa
from kokoro import KPipeline
CAST = json.load(open("tools/audio/cast.json")); OUT = "audio-work/refs"; os.makedirs(OUT, exist_ok=True)
alt = "--alt" in sys.argv; want = [a for a in sys.argv[1:] if not a.startswith("--")] or [k for k in CAST if not k.startswith("_") and "ref" in CAST[k]]
pipes = {}
def kk(text, voice, speed):
    lc = voice[0]
    if lc not in pipes: pipes[lc] = KPipeline(lang_code=lc, repo_id="hexgrad/Kokoro-82M")
    return np.concatenate([x.numpy() if hasattr(x, "numpy") else x for _, _, x in pipes[lc](text, voice=voice, speed=speed)])
if "--crowd" in sys.argv:   # ranger_crowd refs: the design/scripts/crowd_v2_refs.py recipe (energetic text, speed 1.15)
    TXT = ("Yes! Yes! Did you see that? That was incredible! Oh my goodness, we actually did it! "
           "Come on, everybody, let's go! That's what I'm talking about! Unbelievable!")
    for k, (v, st) in {"w_bella": ("af_bella", 1.0), "m_michael": ("am_michael", 0.0), "m_fenrir": ("am_fenrir", -1.5)}.items():
        x = kk(TXT, v, 1.15); x = librosa.effects.pitch_shift(x, sr=24000, n_steps=st) if st else x
        sf.write(f"{OUT}/{k}.wav", x / np.abs(x).max() * 0.9, 24000); print("crowd ref", k, flush=True)
    sys.exit(0)
for ch in want:
    c = CAST[ch]; v, st = (c["alt"]["ref"], c["alt"]["pitch_st"]) if alt else (c["ref"], c["pitch_st"])
    a = kk(c["ref_text"], v, c["speed"])
    if abs(st) > 0.05: a = librosa.effects.pitch_shift(a, sr=24000, n_steps=st)
    a = a / (np.abs(a).max() + 1e-9) * 0.9
    fn = f"{OUT}/{ch}{'.alt' if alt else ''}.wav"; sf.write(fn, a, 24000)
    print(ch, v, st, round(len(a) / 24000, 2), "s ->", fn, flush=True)
```

### 8.9 `tools/audio/gen_lines.py` (`.venv-cb`)
```python
#!/usr/bin/env python3
"""Chatterbox venv (Python 3.11). Generate N takes per line from docs/audio-lines.json.
usage: python tools/audio/gen_lines.py [--phase 2|3|4] [--ids q01a,q01b] [--chars senior_ranger] [--takes 3]
                                       [--seed0 1] [--device auto|mps|cpu] [--alt] [--pron] [--force]
writes audio-work/takes/<id>/s<seed>.wav (24 kHz mono) + takes.jsonl. Resumable: existing takes are skipped."""
import argparse, json, os, re, sys, time, warnings; warnings.filterwarnings("ignore")
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
import torch, torchaudio as ta
from chatterbox.tts import ChatterboxTTS
p = argparse.ArgumentParser()
p.add_argument("--phase", type=int); p.add_argument("--ids"); p.add_argument("--chars")
p.add_argument("--takes", type=int, default=3); p.add_argument("--seed0", type=int, default=1)
p.add_argument("--device", default="auto"); p.add_argument("--alt", action="store_true")
p.add_argument("--pron", action="store_true", help="substitute 'pronounce' respellings into the TTS text")
p.add_argument("--ex", type=float); p.add_argument("--cfg", type=float); p.add_argument("--force", action="store_true")
a = p.parse_args()
L = json.load(open("docs/audio-lines.json"))["lines"]; CAST = json.load(open("tools/audio/cast.json"))
sel = [l for l in L if (a.phase is None or l["phase"] == a.phase)
       and (not a.ids or l["id"] in a.ids.split(","))
       and (not a.chars or l["character"] in a.chars.split(","))]
torch.set_num_threads(max(4, (os.cpu_count() or 8) // 2))
def load(dev):
    return ChatterboxTTS.from_pretrained(device=dev)
dev = a.device if a.device != "auto" else ("mps" if torch.backends.mps.is_available() else "cpu")
m = load(dev); print("device", dev, "lines", len(sel), flush=True)
log = open("audio-work/takes.jsonl", "a")
def tts_text(l):
    t = l.get("tts_text", l["text"])
    if a.pron:
        for k, v in l.get("pronounce", {}).items(): t = re.sub(r"\b" + k + r"\b", v, t, flags=re.I)
    return t
for l in sel:
    c = CAST[l["character"]]
    refs = [f"audio-work/refs/{r}.wav" for r in c["refs"]] if "refs" in c else \
           [f"audio-work/refs/{l['character']}{'.alt' if a.alt else ''}.wav"]
    ex = a.ex if a.ex is not None else c["ex"]; cfg = a.cfg if a.cfg is not None else c["cfg"]
    cap = l.get("max_sec", 3.0) * 1.8 + 0.5           # runaway guard (Chatterbox occasionally babbles on)
    for ri, ref in enumerate(refs):
        os.makedirs(f"audio-work/takes/{l['id']}", exist_ok=True)
        for s in range(a.seed0, a.seed0 + a.takes):
            tag = f"s{s}" + (f"_v{ri}" if len(refs) > 1 else "") + ("_alt" if a.alt else "") + ("_pron" if a.pron else "")
            fn = f"audio-work/takes/{l['id']}/{tag}.wav"
            if os.path.exists(fn) and not a.force: continue
            torch.manual_seed(s); t0 = time.time()
            try:
                w = m.generate(tts_text(l), audio_prompt_path=ref, exaggeration=ex, cfg_weight=cfg, temperature=c.get("temp", 0.8))
            except (RuntimeError, NotImplementedError) as e:
                if dev != "mps": raise
                print("MPS failed -> falling back to CPU:", repr(e)[:200], flush=True)
                dev = "cpu"; del m; m = load("cpu"); torch.manual_seed(s)
                w = m.generate(tts_text(l), audio_prompt_path=ref, exaggeration=ex, cfg_weight=cfg, temperature=c.get("temp", 0.8))
            w = w[:, :int(m.sr * cap)].cpu()
            ta.save(fn, w, m.sr)
            rec = dict(id=l["id"], take=tag, file=fn, ref=ref, ex=ex, cfg=cfg, seed=s, device=dev,
                       sec=round(w.shape[-1] / m.sr, 2), gen_s=round(time.time() - t0, 1), text=tts_text(l))
            log.write(json.dumps(rec) + "\n"); log.flush(); print(rec, flush=True)
```

### 8.10 `tools/audio/qa_check.py` (`.venv-tts`)
```python
#!/usr/bin/env python3
"""Whisper venv (faster-whisper). Word-check every take against its script line and pick a keeper.
usage: python tools/audio/qa_check.py [--ids ...] [--phase N] [--model small.en]
reads audio-work/takes/<id>/*.wav, writes audio-work/qa/<id>.json and audio-work/qa/summary.json.
A take PASSES when (after trimming silence) word errors <= allowed and duration <= max_sec.
NEVER run this while gen_lines.py (Chatterbox) is running: one heavy model at a time."""
import argparse, glob, json, os, re, unicodedata, warnings; warnings.filterwarnings("ignore")
import numpy as np, librosa
from faster_whisper import WhisperModel
p = argparse.ArgumentParser(); p.add_argument("--ids"); p.add_argument("--phase", type=int)
p.add_argument("--model", default="small.en"); a = p.parse_args()
L = {l["id"]: l for l in json.load(open("docs/audio-lines.json"))["lines"]}
ids = a.ids.split(",") if a.ids else [i for i, l in L.items() if a.phase is None or l["phase"] == a.phase]
ids = [i for i in ids if glob.glob(f"audio-work/takes/{i}/*.wav")]
m = WhisperModel(a.model, device="cpu", compute_type="int8", cpu_threads=max(4, (os.cpu_count() or 8) // 2))
TEMPO_MAX = 1.15   # master.py may speed a clip up by at most this (pitch-preserving atempo) to fit max_sec
def hint(l):      # SHORT prompt with only this line's proper nouns; a long vocabulary prompt makes Whisper hallucinate
    w = re.findall(r"\b[A-Z][a-z]+(?:'s)?\b", l["text"]) + list(l.get("pronounce", {}))
    return ", ".join(dict.fromkeys(w)) + "." if w else None
ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
def n2w(n):
    n = int(n)
    if n < 20: return ONES[n]
    if n < 100: return TENS[n // 10] + ("" if n % 10 == 0 else " " + ONES[n % 10])
    return ONES[n // 100] + " " + ("" if n % 100 == 0 else n2w(n % 100))
DROP = {"hundred", "and", "uh", "um"}
def norm(t, ignore=()):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"\d+", lambda x: " " + n2w(x.group()) + " ", t)
    t = re.sub(r"[^a-z' ]+", " ", t.replace("-", " ")).replace("'", "")
    return [w for w in t.split() if w not in DROP and w not in ignore]
def edits(r, h):
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (r[i - 1] != h[j - 1])); prev, d[j] = d[j], cur
    return d[len(h)]
os.makedirs("audio-work/qa", exist_ok=True)
summ = json.load(open("audio-work/qa/summary.json")) if os.path.exists("audio-work/qa/summary.json") else {}
for i in ids:
    l = L[i]; ign = set(l.get("whisper_ignore", [])); ref = norm(l["text"], ign)
    allowed = 0 if len(ref) < 6 else max(1, len(ref) // 10)
    res = []
    for f in sorted(glob.glob(f"audio-work/takes/{i}/*.wav")):
        y, sr = librosa.load(f, sr=16000); yt, _ = librosa.effects.trim(y, top_db=40); dur = len(yt) / sr
        x = np.pad(yt, (4000, 4000)).astype(np.float32)
        for prompt in (None, hint(l)):          # pass 1: no prompt; pass 2 (only if needed): proper-noun hint
            segs, _ = m.transcribe(x, beam_size=5, language="en", initial_prompt=prompt, condition_on_previous_text=False)
            hyp_t = "".join(s.text for s in segs).strip(); hyp = norm(hyp_t, ign); e = edits(ref, hyp)
            if e <= allowed or not hint(l): break
        ok = e <= allowed and 0.3 <= dur <= l.get("max_sec", 9) * TEMPO_MAX and float(np.abs(y).max()) > 0.02
        res.append(dict(file=f, heard=hyp_t, errors=e, allowed=allowed, sec=round(dur, 2), ok=ok))
    good = [r for r in res if r["ok"]]
    if good:
        med = float(np.median([r["sec"] for r in good]))
        pick = min(good, key=lambda r: (r["errors"], abs(r["sec"] - med)))
    else:
        pick = min(res, key=lambda r: (r["errors"], r["sec"]))
    out = dict(id=i, text=l["text"], status="pass" if good else "FAIL", pick=pick["file"], takes=res)
    json.dump(out, open(f"audio-work/qa/{i}.json", "w"), indent=1)
    summ[i] = dict(status=out["status"], pick=pick["file"], heard=pick["heard"], errors=pick["errors"], sec=pick["sec"])
    print(i, out["status"], pick["errors"], pick["sec"], "|", pick["heard"], flush=True)
json.dump(summ, open("audio-work/qa/summary.json", "w"), indent=1)
print("FAILS:", [k for k, v in summ.items() if v["status"] != "pass"])
```

### 8.11 `tools/audio/master.py` (any Python 3 + ffmpeg)
```python
#!/usr/bin/env python3
"""Any Python 3 + ffmpeg. Turn QA-picked takes into shipped MP3s and keep desertranger/audio/manifest.json current.
usage: python tools/audio/master.py --fx                 # build shared radio click / squelch / hiss assets
       python tools/audio/master.py [--ids ...|--phase N] # master voice lines (uses audio-work/qa/<id>.json pick)
Chains: radio = band-pass 300-3000 Hz + compression + presence + light tanh overdrive + mild bit grit;
        clean = 80 Hz high-pass + gentle compression;  crowd = 3 voices layered (q51*)."""
import argparse, glob, hashlib, json, os, re, subprocess, sys
OUT = "desertranger/audio"; WORK = "audio-work/master"; os.makedirs(WORK, exist_ok=True)
TRIM = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02,areverse,"
        "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.04,areverse")
RADIO = ("highpass=f=300:poles=2,highpass=f=300:poles=2,lowpass=f=3000:poles=2,lowpass=f=3000:poles=2,"
         "acompressor=threshold=-20dB:ratio=4:attack=5:release=90:makeup=2,equalizer=f=1700:t=q:w=1.0:g=4,"
         "volume=8dB,asoftclip=type=tanh,volume=-8dB,acrusher=bits=12:mix=0.25:mode=log,highpass=f=300,lowpass=f=3200")
CLEAN = "highpass=f=80,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=1,equalizer=f=3500:t=q:w=1:g=1.5"
TARGET = {"radio": -16.0, "clean": -16.0, "crowd": -14.0}
def sh(*a): subprocess.run(a, check=True)
def ff(*a): sh("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *a)
def meas(f):
    o = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", f, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    s = o[o.rfind("Summary"):]
    return float(re.search(r"I:\s+(-?[\d.]+)", s).group(1)), float(re.search(r"Peak:\s+(-?[\d.inf]+)", s).group(1))
def dur(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f],
                                capture_output=True, text=True).stdout.strip())
def norm_mp3(src, out, tgt, kbps=64, tp=-1.5):
    """crowd_norm.py recipe generalised: static gain -> 4x oversampled limiter -> MP3, re-measure the MP3, iterate."""
    os.makedirs(os.path.dirname(out), exist_ok=True)
    I0, P0 = meas(src)
    if I0 < -60:   # shorter than the 400 ms LUFS gate: peak-normalise instead
        ff("-i", src, "-af", f"volume={tp - 4.5 - P0:.2f}dB", "-ac", "1", "-ar", "44100", "-c:a", "libmp3lame", "-b:a", f"{kbps}k", out)
        return dict(mode="peak", tp=meas(out)[1])
    g, lim = tgt - I0, tp - 0.5
    for it in range(10):
        ff("-i", src, "-af", f"volume={g:.2f}dB,aresample=176400,alimiter=limit={lim}dB:attack=1:release=50:level=false,aresample=44100",
           "-ac", "1", "-c:a", "libmp3lame", "-b:a", f"{kbps}k", out)
        I, P = meas(out)
        if abs(I - tgt) <= 0.3 and P <= tp: break
        if P > tp: lim -= 0.3
        g += tgt - I
    return dict(lufs=I, tp=P)
MAN = f"{OUT}/manifest.json"
man = json.load(open(MAN)) if os.path.exists(MAN) else {"version": 1, "clips": {}}
def save(): json.dump(man, open(MAN, "w"), indent=1, ensure_ascii=False)
def register(cid, rel, **kw):
    f = f"{OUT}/{rel}"
    kw.update(file=rel, sec=round(dur(f), 3), bytes=os.path.getsize(f), v=hashlib.sha1(open(f, "rb").read()).hexdigest()[:8])
    man["clips"][cid] = kw; save()          # client fetches  audio/<file>?v=<v>  (Apache caches mp3 for 30 days)
    print(cid, kw, flush=True)
p = argparse.ArgumentParser(); p.add_argument("--fx", action="store_true"); p.add_argument("--ids"); p.add_argument("--phase", type=int)
a = p.parse_args()
if a.fx:
    w = WORK
    ff("-f", "lavfi", "-i", "anoisesrc=d=0.006:c=white:a=0.9:r=48000", "-f", "lavfi", "-i", "sine=f=1200:d=0.03:r=48000", "-filter_complex",
       "[0]highpass=f=800,afade=t=out:st=0.002:d=0.004[a];[1]volume=0.25,afade=t=in:d=0.003,afade=t=out:st=0.012:d=0.018[b];"
       "[a][b]concat=n=2:v=0:a=1,highpass=f=300,lowpass=f=3500,apad=pad_dur=0.02", "-ac", "1", f"{w}/click.wav")
    for n, (d, seed) in enumerate([(0.22, 1), (0.18, 2), (0.26, 3)], 1):
        ff("-f", "lavfi", "-i", f"anoisesrc=d={d}:c=white:a=0.6:r=48000:s={seed}", "-af",
           f"highpass=f=500,lowpass=f=4000,equalizer=f=2500:t=q:w=1:g=6,afade=t=in:d=0.004,afade=t=out:st=0.03:d={d-0.03:.2f}:curve=exp",
           "-ac", "1", f"{w}/squelch{n}.wav")
    ff("-f", "lavfi", "-i", "anoisesrc=d=4:c=pink:a=0.5:r=48000:s=5", "-af", "highpass=f=300,lowpass=f=3000", "-ac", "1", f"{w}/hiss.wav")
    norm_mp3(f"{w}/click.wav", f"{OUT}/radio/fx/radio-click-01.mp3", -20); register("radio-click-01", "radio/fx/radio-click-01.mp3", kind="fx")
    for n in (1, 2, 3):
        norm_mp3(f"{w}/squelch{n}.wav", f"{OUT}/radio/fx/radio-squelch-0{n}.mp3", -20); register(f"radio-squelch-0{n}", f"radio/fx/radio-squelch-0{n}.mp3", kind="fx")
    norm_mp3(f"{w}/hiss.wav", f"{OUT}/radio/fx/radio-hiss-loop.mp3", -40); register("radio-hiss-loop", "radio/fx/radio-hiss-loop.mp3", kind="fx",
             note="loop under the whole call at runtime gain ~0.5; crossfade-loop it (MP3 has encoder padding)")
    sys.exit(0)
L = {l["id"]: l for l in json.load(open("docs/audio-lines.json"))["lines"]}
ids = a.ids.split(",") if a.ids else [i for i, l in L.items() if a.phase is None or l["phase"] == a.phase]
for i in ids:
    qf = f"audio-work/qa/{i}.json"
    if not os.path.exists(qf): print("skip (no QA yet)", i); continue
    q = json.load(open(qf)); l = L[i]; t = l["treatment"]; tmp = f"{WORK}/{i}.wav"
    if t == "crowd":   # layer the best take of each voice (_v0/_v1/_v2) with small onset offsets
        picks = []
        for v in range(3):
            c = [r for r in q["takes"] if f"_v{v}" in r["file"]]
            if c: picks.append(min(c, key=lambda r: (not r["ok"], r["errors"]))["file"])
        ins = sum([["-i", f] for f in picks], [])
        fc = "".join(f"[{k}]{TRIM},adelay={[0, 25, 55][k]},volume={[1, 0.8, 0.7][k]}[x{k}];" for k in range(len(picks)))
        ff(*ins, "-filter_complex", fc + "".join(f"[x{k}]" for k in range(len(picks))) +
           f"amix=inputs={len(picks)}:normalize=0,{CLEAN}", "-ac", "1", "-ar", "44100", tmp)
    else:
        ff("-i", q["pick"], "-af", f"aresample=48000,{TRIM}", "-ac", "1", f"{WORK}/{i}.trim.wav")
        d0 = dur(f"{WORK}/{i}.trim.wav"); mx = l.get("max_sec", 9)
        tempo = f"atempo={min(1.15, d0 / mx):.3f}," if d0 > mx else ""      # pitch-preserving speed-up, max +15 %
        ff("-i", f"{WORK}/{i}.trim.wav", "-af", f"{tempo}{RADIO if t == 'radio' else CLEAN}", "-ac", "1", tmp)
    r = norm_mp3(tmp, f"{OUT}/{l['file']}", TARGET[t])
    register(i, l["file"], character=l["character"], text=l["text"], square=l["square"], kind=l["kind"], treatment=t,
             qa=q["status"], take=os.path.basename(q["pick"]), **r)
```

### 8.12 `tools/audio/build_review.py` (any Python 3)
```python
#!/usr/bin/env python3
"""Generate desertranger/audio/review.html: one page listing every shipped clip with a play button,
script text, what Whisper heard, QA status, length, loudness and size, plus stitched radio-call demos.
Open: http://localhost:8888/desertranger/audio/review.html"""
import json, os, html
OUT = "desertranger/audio"
man = json.load(open(f"{OUT}/manifest.json"))["clips"]
L = json.load(open("docs/audio-lines.json"))
qa = json.load(open("audio-work/qa/summary.json")) if os.path.exists("audio-work/qa/summary.json") else {}
lines = {l["id"]: l for l in L["lines"]}
SECTIONS = [("Phase 1: dice, ambience, critters", lambda c, l: c.get("kind") in ("dice", "amb", "critter")),
            ("Phase 2: radio FX", lambda c, l: c.get("kind") == "fx"),
            ("Phase 2: openers", lambda c, l: c.get("kind") == "opener"),
            ("Phase 2: place names", lambda c, l: c.get("kind") == "place"),
            ("Phase 2: dispatch replies", lambda c, l: c.get("kind") == "reply"),
            ("Phase 3: square quotables", lambda c, l: c.get("kind") == "quotable"),
            ("Phase 4: Dispatch / R55 / 273 chatter", lambda c, l: c.get("kind") == "chatter")]
tot = sum(c["bytes"] for c in man.values())
h = [f"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Desert Ranger audio review</title><style>
body{{font:15px/1.4 system-ui;margin:16px;background:#faf6ef;color:#2b2118}} table{{border-collapse:collapse;width:100%;margin-bottom:24px}}
td,th{{border-bottom:1px solid #ddd;padding:4px 6px;text-align:left;vertical-align:top}} th{{background:#eadcc8;position:sticky;top:0}}
.FAIL{{background:#ffd9d0}} .pass{{}} button{{font-size:15px}} textarea{{width:100%;height:2.2em}} .small{{color:#776;font-size:12px}}
</style><h1>Desert Ranger audio review</h1>
<p>{len(man)} clips, {tot/1024:.0f} KB total. Rows in red failed the Whisper word-check after all retakes. Notes save in this browser;
<button onclick="exportNotes()">Export notes (JSON)</button> <button onclick="playAll(this)">Play section-by-section</button></p>
<h2>Stitched landing-call demos (runtime stitching: click + opener + place + squelch over hiss)</h2><p>"""]
for v in ("sr", "r273"):
    for op, sq in [(1, 39), (2, 43), (3, 12), (4, 32), (5, 18), (6, 33)]:
        h.append(f"<button onclick=\"stitch('op-{v}-{op:02d}','pl-{v}-{sq:02d}')\">{v} op{op} + sq{sq}</button> ")
h.append("</p>")
for title, f in SECTIONS:
    rows = [(cid, c) for cid, c in sorted(man.items()) if f(c, lines.get(cid))]
    if not rows: continue
    h.append(f"<h2>{title} ({len(rows)})</h2><table><tr><th>play</th><th>id</th><th>character</th><th>sq</th><th>script</th><th>Whisper heard</th><th>s</th><th>LUFS</th><th>KB</th><th>notes</th></tr>")
    for cid, c in rows:
        q = qa.get(cid, {}); st = c.get("qa", q.get("status", ""))
        h.append(f"<tr class='{html.escape(st)}'><td><button data-src='{html.escape(c['file'])}' onclick='play(this)'>&#9654;</button></td>"
                 f"<td>{cid}</td><td>{c.get('character','')}</td><td>{'' if c.get('square') is None else c.get('square')}</td>"
                 f"<td>{html.escape(c.get('text', c.get('note','')))}</td><td class=small>{html.escape(q.get('heard',''))}</td>"
                 f"<td>{c['sec']}</td><td>{c.get('lufs','')}</td><td>{c['bytes']//1024}</td>"
                 f"<td><textarea data-id='{cid}'></textarea></td></tr>")
    h.append("</table>")
h.append("""<script>
var M=%s, ctx, cur;
function play(b){ if(cur){cur.pause();} cur=new Audio(b.dataset.src); cur.play(); }
function buf(id){ return fetch(M[id].file).then(r=>r.arrayBuffer()).then(a=>new Promise((ok,no)=>ctx.decodeAudioData(a,ok,no))); }
function trim(b){ var d=b.getChannelData(0),s=0,e=d.length-1,t=0.003; while(s<e&&Math.abs(d[s])<t)s++; while(e>s&&Math.abs(d[e])<t)e--; return {b:b,off:s/b.sampleRate,dur:(e-s)/b.sampleRate}; }
function stitch(op,pl){ ctx=ctx||new (window.AudioContext||window.webkitAudioContext)();
  Promise.all(['radio-click-01',op,pl,'radio-squelch-01','radio-hiss-loop'].map(buf)).then(function(x){
    var t=ctx.currentTime+0.1, c=x[0], o=trim(x[1]), p=trim(x[2]), q=x[3];
    function at(b,when,off,d,g){var s=ctx.createBufferSource(),G=ctx.createGain();G.gain.value=g||1;s.buffer=b;s.connect(G).connect(ctx.destination);s.start(when,off||0,d);}
    at(c,t); var v=t+c.duration; at(o.b,v,o.off,o.dur); at(p.b,v+o.dur+0.06,p.off,p.dur); var end=v+o.dur+0.06+p.dur;
    var h=ctx.createBufferSource(),hg=ctx.createGain();h.buffer=x[4];h.loop=true;hg.gain.value=0.5;h.connect(hg).connect(ctx.destination);h.start(t);h.stop(end+0.02);
    at(q,end+0.02);
  });}
document.querySelectorAll('textarea').forEach(function(t){t.value=localStorage.getItem('rv_'+t.dataset.id)||'';t.oninput=function(){localStorage.setItem('rv_'+t.dataset.id,t.value);};});
function exportNotes(){var o={};document.querySelectorAll('textarea').forEach(function(t){if(t.value)o[t.dataset.id]=t.value;});
  var a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(o,null,1)],{type:'application/json'}));a.download='audio-review-notes.json';a.click();}
function playAll(btn){var bs=[].slice.call(document.querySelectorAll('button[data-src]')),i=0;(function nx(){if(i>=bs.length)return;var a=new Audio(bs[i++].dataset.src);cur=a;a.onended=function(){setTimeout(nx,500)};a.play();})();}
</script>""" % json.dumps(man))
open(f"{OUT}/review.html", "w").write("\n".join(h)); print("wrote", f"{OUT}/review.html", len(man), "clips")
```

### 8.13 The batch loop (use this for every voice phase)
```bash
source .venv-tts/bin/activate && python tools/audio/make_refs.py && python tools/audio/make_refs.py --crowd && deactivate   # once
source .venv-cb/bin/activate  && python tools/audio/gen_lines.py --phase 3 --takes 3 --device auto && deactivate         # GENERATE
source .venv-tts/bin/activate && python tools/audio/qa_check.py --phase 3 && deactivate                                  # CHECK (never concurrently)
# retake ladder for FAIL ids (section 10), then:
python3 tools/audio/master.py --phase 3 && python3 tools/audio/build_review.py                                           # MASTER + REVIEW
git add desertranger/audio tools/audio docs/AUDIO-BUILD-LOG.md && git commit -m "audio: phase 3 quotables" && git push origin audio-build
```

---
## 9. Phased task list (tick the boxes in this file as you go, and commit the ticks)

Work in order. Each phase ends with a commit and push, plus a log update. If a phase is blocked, log it and continue with the next phase where possible. Phase 5 depends on the assets, but it can start with whatever exists, because the client must degrade gracefully when a clip is missing.

### Phase 0: setup and a sample set (≈ 45 min)
- [x] 0.1 Check out `audio-build`, pull, confirm `git branch --show-current` = `audio-build`.
- [x] 0.2 Add the `.gitignore` lines (4.6). Create `tools/audio/` with the files from section 8. Create `docs/AUDIO-BUILD-LOG.md` from the template in section 11. Create `desertranger/audio/CREDITS.md` with the header table (Phase 1.6). **Commit.**
- [x] 0.3 Set up both venvs and brew packages (4.1-4.3). Record `python --version`, `ffmpeg -version | head -1`, the torch version and MPS availability in the log.
- [x] 0.4 Smoke test: `make_refs.py` (all characters + `--crowd`), then `gen_lines.py --ids q22a,q23a,op-sr-01,pl-sr-39,rp-dis-01,ch02-2,ch09-2 --takes 2`, then `qa_check.py` on those IDs, then `master.py --fx` and `master.py --ids …`, then `build_review.py`. The pipeline must run end to end.
- [x] 0.5 Distinctness check (section 7). Fix with `--alt` refs if needed.
- [x] 0.6 **Sample set** (the plan's checkpoint, "Review those samples before committing to the complete voice set"). Build a small representative set:
  - one opener+place stitch per rotation voice
  - one hazard reply
  - one quotable per character
  - one chatter exchange
  - the ambience bed plus one critter
  - the dice clatter

  Put it in `review.html` and **commit and push it**, so the user can listen first if they check in.
  The user is away, so **continue to full production after that commit.** Note in the log that full production went ahead before the user reviewed the samples, and that everything is regenerable from `audio-lines.json` + `cast.json` with the scripts.

**Acceptance:** the pipeline works; the sample set is committed and listed in `review.html`; versions are logged.

### Phase 1: dice, ambience bed, critters (plan A + C) (≈ 1 h)
- [x] 1.1 **Dice (CC0, Kenney "Casino Audio" 1.1, checked Oct 2, 2026):**
  - Download `https://kenney.nl/media/pages/assets/casino-audio/2472606a04-1721639069/kenney_casino-audio.zip` (page: https://kenney.nl/assets/casino-audio; `License.txt` inside says CC0). If the URL has changed, take the zip link from the page.
  - Use `Audio/dice-shake-1..3.ogg` (1.4-1.5 s) for the **shake** and `Audio/die-throw-1..4.ogg` (0.47-0.73 s, a single die, which matches the game) for the **clatter**.
  - Make `dice/dice-shake-01.mp3`: trim to ≈ 0.7 s with a 120 ms fade-out, mono, −20 LUFS. You may also make a seamless loop version, `dice-shake-loop.mp3`, for hold-to-shake.
  - Make `dice/dice-clatter-01..04.mp3` from die-throw-1..4: mono, −18 LUFS or peak mode.
  - Every file must be < 50 KB. Add a CREDITS row for each.
- [x] 1.2 **Ambience bed:** `amb/amb-bed-01.mp3`. Use the 8.3 recipe (90 s loop, −28 LUFS, 64 kbps mono ≈ 720 KB). You may blend in a CC0 wind recording if it clearly sounds better.
- [x] 1.3 **Critters** (one-shots, each ≤ 6 s, −26 LUFS):
  - Synthesize crickets, the rattlesnake rattle (rare) and the distant truck with the 8.4 recipes.
  - Source the crow/raven caw, coyote yip, quail and hawk screech as **CC0** recordings:
    - **Freesound:** search with the CC0 filter (`https://freesound.org/search/?q=coyote&f=license:%22Creative+Commons+0%22`). Open the sound page and confirm the license box says **Creative Commons 0**. Downloading the original needs a login, so **don't log in**. Use the public HQ preview MP3 linked from the page's player (`https://cdn.freesound.org/previews/...-hq.mp3`). Record the page URL, preview URL, author and "CC0 1.0".
    - **OpenGameArt:** CC0-filtered assets only.
    - **Kenney** packs.
  - Trim, de-noise lightly if needed (`afftdn=nf=-25`), mono, and normalize.
  - If you can't find a clean CC0 recording for a sound, skip it and log it.
- [ ] 1.4 Optional square tie-in assets: a water trickle for Palm Canyon (square 2) and a second rattle variant for hazard squares. These are local only and low priority.
- [x] 1.5 Register every file in `manifest.json` (`kind` `dice`/`amb`/`critter`). Check the budgets: dice ≤ 250 KB, ambience ≤ 1.5 MB.
- [x] 1.6 `desertranger/audio/CREDITS.md` has one row per third-party file:
  `| file | source page URL | direct file URL | author | license | retrieved (CT) | changes |`.
  Add a "Generated / original" section that covers:
  - Chatterbox voices: model `ResembleAI/chatterbox`, MIT, Perth watermark
  - Kokoro-82M reference voices: Apache-2.0, used as references only (not shipped)
  - ffmpeg-synthesized bed, critters and radio FX: original
- [x] 1.7 **Commit + push.**

**Acceptance:** all files exist, play, meet their loudness targets (±1 LU) and stay inside the budgets. Every third-party file has a CC0 credits row with its URL. Nothing is non-CC0.

### Phase 2: radio DSP chain and landing calls (plan B) (≈ 1-1.5 h of generation)
- [x] 2.1 `master.py --fx` → `radio/fx/radio-click-01.mp3`, `radio-squelch-01..03.mp3`, `radio-hiss-loop.mp3` (≤ 60 KB total).
- [x] 2.2 Generate **openers**: 8 per rotation voice (`op-sr-*`, `op-r273-*`, 16 total).
  - Each must be ≤ 1.5 s after trimming (master may apply up to 1.15× atempo).
  - Delivery should keep an upward "continuing" intonation.
  - If they run long, rerun with `--ex <base+0.15>` for brisker delivery.
- [x] 2.3 Generate **place names**: all 52 squares × 2 voices (`pl-sr-00..51`, `pl-r273-00..51`, 104 clips), each ≤ 1.2 s.
  - The spoken phrases are in `text`; e.g. square 43 is spoken "Font's Point" while the board prints FONTS POINT.
  - Action squares have **proposed** location phrases. Mark them for review in the log.
  - Pronunciation: run the plain text first. Only if a name fails the check (or obviously sounds wrong), retake with `--pron`, which substitutes the respellings from `pronounce` (Ocotillo "oh-koh-TEE-yoh", Yaqui "YAH-kee", Vallecito "vy-yeh-SEE-toh", olla "OY-yah", cholla "CHOY-yah", …).
- [x] 2.4 Optional **dispatch replies** `rp-dis-01..03`. Plan D forbids stacking them after a quotable on the same landing, so they're only for chatter or future use. Generate them if time allows.
- [x] 2.5 QA → retake ladder → master → `build_review.py`. The review page has stitched-call demo buttons; check that a few stitches sound continuous (no clicks, gaps < 80 ms).
- [x] 2.6 **Commit + push.**

**Acceptance:**
- 16 openers and 104 places are shipped, each passing the Whisper check or explicitly flagged.
- opener + place + click + squelch ≤ ~3.0 s for at least the shortest 4 openers with every place.
- Budget: openers + places ≤ 1.1 MB.

### Phase 3: square quotables (plan D) (≈ 1 h of generation)
- [ ] 3.1 Generate all 54 quotable lines (`--phase 3`): 27 squares × variants a/b, with characters and directions as in section 7. The **Senior Ranger** voices squares 1, 9, 12, 14, 16, 22, 29, 41, 46, 48, 49 and 50. Her delivery should be authoritative and clipped (calm, commanding, dry), not shouted.
- [ ] 3.2 The crowd lines q51a/b are layered from 3 voices (8.6). For q35a/b, add the crowd sweetener (8.6).
- [ ] 3.3 Each line ≤ 2.7 s after trimming, with atempo allowed up to 1.15×.
  - Known long lines: q03a "Congratulations! Your promotion comes with a Sacramento transfer.", q14a, q27a, q28a, q31b, q41a. If one still won't fit, keep its best take, flag it in the log as `OVER-CAP`, and have the client prefer the other variant (see 5.4).
  - **Don't rewrite the script text.** Put shorter wording suggestions in the log's open questions.
- [ ] 3.4 QA → retake ladder → master → review. **Commit + push.**

**Acceptance:** 54 quotables are shipped (or flagged), loudness is −16 ±1 LU, the treatment matches `audio-lines.json`, and the budget is ≤ 1.3 MB.

### Phase 4: Dispatch / R55 / 273 chatter (plan E) (≈ 45 min of generation)
- [ ] 4.1 Generate all 39 chatter lines (`--phase 4`), 12 exchanges. Each line is a separate clip; the client stitches them.
  - Dispatch is the separate operator voice. R55 is a male ranger distinct from the Senior Ranger and 273. Ranger 273 runs the nature walks.
  - Use **Burro Bend Cafe** exactly as written: it's the client's real 1980-82 hangout in Ocotillo Wells, across the highway from the ranger station.
- [ ] 4.2 The Latin plant names in exchanges 9-12 can't be word-checked, because `whisper_ignore` skips them. Listen for gross failures in the review sheet instead: half a word missing, or the line running long. Try `--pron` takes and keep the better one. Taxonomy as given in the plan:
  - *Larrea tridentata* / Zygophyllaceae (creosote)
  - *Fouquieria splendens* / Fouquieriaceae (ocotillo)
  - *Bursera microphylla* / Burseraceae (elephant tree)
  - *Washingtonia filifera* / Arecaceae (fan palm)
  - *Agave deserti* / Asparagaceae (desert agave)
- [ ] 4.3 QA → master → review (the review page shows lines grouped by exchange). **Commit + push.**

**Acceptance:** all 12 exchanges are complete, the budget is ≤ 0.9 MB, and no line exceeds its `max_sec` × 1.15.

### Phase 5: client integration (≈ 2-3 h)
Keep the existing style: ES5, IIFEs, no dependencies. Bump `?v=` on every script/CSS you change in `index.html`. Add `<script src="assets/js/ambience.js?v=1">` and `radio.js` **after** `sync.js` and before `app.js`.

- [x] **5.1 Server, the one allowed change:** in `lib/game.php::dr_take_action`, the first log line of each action (types `turn`/`win`) must always get `play_at_ms`, even when `cue` is null. Do it by adding an optional `$forcePlayAt = false` parameter to `dr_add_event()` and passing `true` for that first line. Leave `cue` semantics, the schema and the API shape unchanged.
  - Then rerun `rules_test.php` (pure engine, should stay 45/45) and `simulate_game.php`.
  - If `simulate_game.php` asserts that `playAt` is null without a cue, **don't weaken the test silently.** Update the assertion to the new contract and explain it in the log and the commit message.
- [x] **5.2 One shared timeline per turn event:** every device must compute the same audio timeline from the same event.
  - When a turn event arrives with `playAt` (T, server ms), push a **wait-until-T** task into the BoardView queue *before* its steps. Pushing it immediately keeps the queue non-empty, so `setPlayers()` doesn't snap the piece early.
  - That way the die reveal and the hops start at T on every device.
  - Add `BoardView.prototype.timeline(steps)`. It returns the offsets (ms from T) of each `roll` step and the end of movement, using the same constants as `animate()`: roll 550; walk = hops × `HOP_MS` + 250; jump/swap = `JUMP_MS`.
  - If the event is already late (local time > T + 250 ms, e.g. a hidden tab), animate immediately as today and **skip** its audio. That's the existing late rule.
  - Keep a constant `SYNC_ANIM = true` so this can be turned off. If the e2e test breaks because of the delay, fix the test's waits, don't drop the feature. If you can't, set it to `false`, schedule audio at T + offsets anyway, and log it.
- [x] **5.3 Audio graph and lazy loader (`sync.js`):**
  - Add buses: `master` (the existing mute) → `cue` (crowd + dice), `voice` (landing calls), `amb` (bed + critters) and `chatter`. `amb` and `chatter` each pass through a duck gain.
  - Add `Sound.clip(id)`: it reads `audio/manifest.json` once and fetches `audio/<file>?v=<v>` on demand. It decodes with the callback form of `decodeAudioData` (old Safari) and caches the promise. A missing clip resolves to `null`; never throw, and never log an error for an optional asset (a single `console.warn` is fine).
  - Add `Sound.at(buffer, serverMs, opts)`: a generic version of `schedule()` with bus, gain, playbackRate, offset and duration. It returns the scheduled ctx-time window `{start, end}`.
  - Keep `Sound.schedule(name, playAt)` working for cheer/aww.
  - **Loading tiers:**
    - Tier A, on unlock: radio fx, dice, `manifest.json`.
    - Tier B, right after the game starts (status `active`), throttled 4 at a time: openers, all places for both voices, quotables.
    - Tier C, 20 s after start, or idle: ambience bed, critters, chatter.
  - Never fetch audio before the audio-unlock tap, and never on the home/lobby screen.
- [x] **5.4 Landing-call picker (`radio.js`), a pure function that's easy to test:**
  ```js
  // Inputs every device shares: ev.id, ev.type, ev.data.steps, the quotable set from audio-lines.json squares[].
  function pickLanding(ev, Q) {
    var steps = (ev.data && ev.data.steps) || [], mover = null, first = null, fin = null, seen = [];
    if (steps.some(function (s) { return s.type === 'swap'; })) return null;      // swap choice: HR line already played on 31
    steps.forEach(function (s) {
      if (s.type === 'roll' && mover === null) mover = s.player;
      if ((s.type === 'walk' || s.type === 'jump') && (mover === null || s.player === mover)) {
        if (mover === null) mover = s.player;
        if (first === null) first = s.to;
        fin = s.to; seen.push(s.to);
      }
    });
    if (first === null) return null;                     // "decided not to swap" / "stayed on the trail"
    var sq = ev.type === 'win' ? 51 : first;             // resolve chains BEFORE choosing: 41->12 uses 41's line
    if (first === 44) for (var k = 1; k < seen.length; k++)   // 44: use the final roll-back outcome's quotable, if any
      if (Q[seen[k]] && seen[k] !== 44) { sq = seen[k]; break; }
    var v = ev.id % 2 ? 'b' : 'a';
    if (Q[sq]) return { kind: 'quote', square: sq, ids: ['q' + ('0' + sq).slice(-2) + v, 'q' + ('0' + sq).slice(-2) + (v === 'a' ? 'b' : 'a')] };
    var voice = ev.id % 2 ? 'r273' : 'sr';               // alternate Senior Ranger / Ranger 273; never Dispatch
    return { kind: 'generic', square: fin, voice: voice, opener: 1 + (Math.floor(ev.id / 2) % 8) };
  }
  ```
  - Cases: a shortcut jump (choose → 33) gives a generic call at 33. A roll landing on 6 or 31 plays q06/q31. An overshoot win plays q51. 40→34 plays q40 (not the Court line). 44 then back 3 → 41 → 12 plays q41. 44 then back 5 → 39 plays q44.
  - All inputs are shared, so every device picks the same clip.
  - Strict alternation across *eligible* landings would need shared state. Parity of `ev.id` is the deterministic approximation; log it as a decision.
  - **The ~3 s cap:** voice window = click + clips (+ 60 ms gap between opener and place) + squelch.
    - For quotes: use the first ID whose clip fits in ≤ 3.0 s; if neither fits, use the shorter one.
    - For generic calls: start at `opener` and try the next openers in order (wrapping) until opener + place fits. If none fits, play the place name alone (click + place + squelch). If even that doesn't fit, skip the call.
    - Never stack a generic call, a quotable and a reply.
  - **Timing:** the landing call starts at T + `timeline.end` (when the piece stops moving).
  - **Busy rule:** if any voice is already scheduled to overlap the window, or a quotable or dice clip is playing, skip the call ("skip the call if another cue is already playing").
  - **Crowd cue:** the server's cheer/aww (`ev.cue`) still decides *whether* a crowd clip plays; that keeps the gameplay meaning. Move its start from T to the end of the voice window minus 150 ms, or to T + `timeline.end` when there's no voice. If radio chatter is off, play only the crowd cue (plan D).
  - **Radio treatment at runtime:** for clips with `treatment: radio`:
    - play click (≈ 0.1 s), then the voice, then `radio-squelch-0{1 + ev.id % 3}`;
    - loop the hiss under the voice section at gain 0.5, with a 30 ms fade in/out;
    - trim the decoded buffers' leading and trailing near-silence first (threshold 0.003) so the stitches are tight.
  
    Clean clips play dry with no click or squelch.
- [x] **5.5 Dice:**
  - **Local shake:** on the ROLL tap (inside the existing handler, after `Sound.unlock()`), play `dice-shake-01` immediately, local only. It's optional to loop it while the button is held or until the turn's T arrives, then fade it out over 80 ms.
  - **Synced clatter:** for each `roll` step, schedule `dice-clatter-0{1 + (ev.id + i) % 4}` at T + its timeline offset (the 44 extra die gets its own). Use `playbackRate = 1 + ((ev.id * 7 + i) % 9 - 4) * 0.01` (±4 %, deterministic, so every device matches).
  - The clatter belongs to the `cue` bus and is **not** subject to the radio toggle.
- [x] **5.6 Ambience (`ambience.js`):**
  - Start only after unlock + Tier C has loaded the bed. Play the bed as two overlapping sources with a 1.5 s equal-power crossfade at the loop point.
  - **Critters:**
    - random interval 20-60 s (`Math.random`; local, never synced);
    - random gain −8…0 dB and random pan (StereoPanner where available, else none);
    - never repeat the same sound twice in a row;
    - the rattle is rare (weight 0.3);
    - optional local tie-ins: favor the rattle when this device's own piece sits on a hazard square, and water near Palm Canyon.
  - **Ducking:** when any `cue`/`voice` sound is scheduled, ramp the `amb` duck gain to −12 dB from (start − 0.15 s) and back to 0 dB at (end + 0.4 s) with `setTargetAtTime` (time constant ≈ 0.08 s). Chatter ducks to −18 dB or is skipped (5.7).
  - **Board view (`?board=1`):** the ambience default is +6 dB louder (the room speaker), and ambience defaults to on. Keep the normal player mix separate.
- [x] **5.7 Background chatter (in `ambience.js`, behind the radio-chatter toggle):**
  - The first exchange comes no sooner than 90 s after unlock; after that the gap is random, 150-330 s (unpredictable).
  - Pick a random exchange with no immediate repeat. Weight Burro Bend exchanges 1, 3, 6 and 7 ×3 for 2 minutes after this device's own piece lands on Ocotillo Wells (12) (plan E tie-in), but never within 10 s of that square's quotable.
  - **Playback:** for each line, click → line over hiss → squelch, with 350-600 ms between lines. Use the `chatter` bus at gain ≈ 0.35, quieter than game cues.
  - **Skip or duck rule:** if any game cue, landing call, dice sound or quotable is scheduled within the exchange's window, postpone the exchange 20-40 s. If one arrives mid-exchange, duck chatter to −18 dB until it ends. Chatter never reserves synchronized timing.
- [x] **5.8 Toggles and volume UI:**
  - Add a ⚙ button next to 🔊 in `.game-head`. It opens a small panel with:
    - **Ambience** on/off (default on)
    - **Ambience volume** slider 0-100 (default 60; maps to bus gain 0-1.4)
    - **Radio chatter** on/off (default on). It covers landing calls, quotables and background chatter. Crowd cues and dice still follow 🔊.
  - Persist in `localStorage` as `dr_amb_on`, `dr_amb_vol`, `dr_radio_on`. Ambience and radio work independently of each other. 🔊 mute (`dr_muted`) still silences everything.
  - It must be usable at 390×844, and the panel closes on outside tap. Match `style.css` palette.
  - Open question for the log: should character quotables have their own toggle separate from "radio chatter"? Plan D implies radio off → crowd cue only, so that's what to implement.
- [x] **5.9 Robustness:**
  - The first poll after load replays no history (the existing `wasFirst`).
  - Hidden tabs skip late audio.
  - A missing clip means silence, not an error.
  - iOS: everything starts only after unlock; resume the `AudioContext` if it's suspended.
  - No timers run before unlock. Stop critter and chatter timers on `game.status === 'finished'` plus 30 s.
- [x] **5.10 Debug footer (`&debug=1`):** append the last landing pick (`quote q41a` / `generic sr op3 pl39` / `skipped: busy`), the bus states and the loaded-clip count.
- [x] **5.11 Tests:**
  - Add `dev/audio/landing_test.js` (plain Node, no deps). It loads `radio.js`'s `pickLanding` (export it on `window.DRRadio`; the test can eval the file with a fake `window`) and checks the cases listed in 5.4, plus the 3 s fitting logic with fake durations.
  - Run it with `node dev/audio/landing_test.js`.
- [ ] 5.12 **Commit + push** after each sub-step that works (5.1, 5.2-5.3, 5.4-5.5, 5.6-5.7, 5.8-5.10).

**Acceptance (all in the browser on MAMP, with two windows plus `?board=1`):**
- Audio begins only after the audio-unlock tap.
- Ambience controls work independently of radio-chatter controls.
- Ambience ducks under voice/crowd cues, and the board view has its louder mix.
- One-shots vary timing, volume and pan without immediate repeats.
- Landing calls fire on move completion through `play_at`, are skipped while another cue plays, use opener+place stitching with the two rotation voices, and stay ≤ ~3 s.
- Quotables replace generic calls on the 27 squares, chained effects get one line, and radio off means crowd cue only.
- Dice: the local shake is instant, and the synced clatter varies between 4 takes with slight pitch variation.
- Chatter is occasional, quiet, behind the radio toggle, and never collides with cues.
- Everything is lazy-loaded (the Network tab shows no audio requests before unlock), and the budgets in section 6 are met.
- No console errors.

### Phase 6: QA, review sheet and wrap-up (≈ 45 min)
- [ ] 6.1 Rerun `qa_check.py` over **all** IDs. Every line is either `pass` or listed in the log as `FAIL-after-ladder` with what was tried.
- [ ] 6.2 `build_review.py`. Open `http://localhost:8888/desertranger/audio/review.html` and confirm that every clip plays and that the stitch demos work.
- [ ] 6.3 `php desertranger/tests/rules_test.php` (45/45), `php desertranger/tests/simulate_game.php http://localhost:8888/desertranger 4` (and 8), `node dev/audio/landing_test.js`, and the e2e (`dev/e2e`, see section 3). All must pass. Paste the summary lines into the log.
- [ ] 6.4 **Console check:**
  - Run the e2e with console capture. If it doesn't already collect `console.error` and `pageerror`, add that to `e2e.js`.
  - Also play 10+ turns by hand in Chrome and Safari if available. Expect zero errors; a `console.warn` for a deliberately missing optional asset is acceptable.
  - Also check the MAMP Apache access log for 404s on `/desertranger/audio/`.
- [ ] 6.5 Size report: `du -ck desertranger/audio/*/ desertranger/audio/radio/*/` against the budgets. Put it in the log.
- [ ] 6.6 Final log update and PR description (section 11). **Commit + push.**

---
## 10. QA rules

**Whisper word-check (every generated line):**
- Use `qa_check.py` with faster-whisper `small.en` (CPU, int8; `base.en` is OK if `small.en` won't download).
- It trims silence, transcribes with **no prompt first** (a long vocabulary prompt made Whisper hallucinate on the build box), and retries once with a short hint made of only that line's proper nouns.
- Numbers are normalized on both sides ("10-4" = "ten four"; "hundred"/"and" fillers are dropped), and the `whisper_ignore` Latin words are skipped.
- Pass criteria:
  - lines under 6 words need **zero** word errors; longer lines may have up to 10 % (at least 1);
  - 0.3 s ≤ trimmed length ≤ `max_sec` × 1.15;
  - the take isn't near-silent.

  The check catches the failure modes seen on the box: a dropped first word ("Dispatch" heard as "Patch"/"Badge"), babble before the line, and a near-silent 0.3 s take.
- **Retake ladder for a failing ID** (stop at the first rung that passes):
  1. 3 more seeds (`--seed0 4 --takes 3`).
  2. Brisker or calmer pacing (`--ex base±0.15`, or `--cfg 0.3` if it's rushed).
  3. `--pron` respellings (names), or a manual tts_text tweak passed with a temporary override. Only change pronunciation, never wording.
  4. The `--alt` reference.
  5. The Kokoro backup (4.3).
  6. Ship the best take flagged `FAIL-after-ladder` in the log and on the review page (red row).

  Keep at most 9 Chatterbox takes per line. Retake *failures*, not passes.
- **Loudness check:** `manifest.json` records `lufs`/`tp` for every voice clip; all must be within ±1 LU of target and under the TP limit. Run `ebur128` spot checks on 5 random MP3s and log them.
- **Listening sheet:** `desertranger/audio/review.html` (generated) lists **every clip** grouped by phase. Each row shows:
  - a ▶ button
  - the ID, character and square
  - the script text and what Whisper heard
  - length, LUFS and KB
  - a notes box saved in localStorage, with an "Export notes" button

  The page also has stitched landing-call demo buttons and a "play section-by-section" button, so the user can review everything in one sitting. Regenerate it after every mastering batch and commit it.
- **Game tests:** `rules_test.php` (45/45), `simulate_game.php` (4 and 8 players), `dev/audio/landing_test.js`, and the e2e with **zero console errors**.

---

## 11. Progress reporting

Keep **`docs/AUDIO-BUILD-LOG.md`** current. Update it after every task, commit it with the work, and push. Template:
```markdown
# Audio build log (branch audio-build)
_Last updated: <YYYY-MM-DD HH:MM CT> by Claude Code_

## Status
| Phase | State | Notes |
|---|---|---|
| 0 Setup + samples | done / in progress / blocked | |
| 1 Dice + ambience + critters | | |
| 2 Radio + landing calls | | |
| 3 Quotables | | |
| 4 Chatter | | |
| 5 Client integration | | |
| 6 QA + wrap-up | | |

## Environment
macOS …, Python 3.11.x (.venv-cb) / 3.12.x (.venv-tts), ffmpeg …, torch …, MPS: yes/no, device used: …

## Done (newest first)
- <time CT> <what> (<commit sha>)

## Skipped / deferred (with reason)
- …

## QA
- Whisper: <n> pass / <n> FAIL-after-ladder (ids …)
- Loudness spot checks: …
- Tests: rules_test 45/45 · simulate_game 4p/8p OK · landing_test OK · e2e OK, console errors: 0
- Sizes: dice … KB · ambience … KB · radio … KB · quotes … KB · chatter … KB · total … MB

## Decisions I made (user may want to revisit)
- …

## Open questions for the user
- …
```

Include the timezone (CT, the user's zone) for every time you write.

**At the end** (or when you stop), **edit the draft PR's description**. Use `gh pr edit <number> --body-file …` if `gh` is installed and authenticated; don't log in or create tokens. If `gh` isn't available, put the summary at the top of the log and say so there. The description should cover:
1. What shipped, per phase (counts of clips, sizes vs budget).
2. How to review: the `review.html` URL and what to listen for.
3. Test results (the four test commands and console errors).
4. Skipped items and FAIL-after-ladder lines.
5. Decisions made and open questions (copied from the log).
6. How to regenerate (`audio-lines.json` + `cast.json` + `tools/audio/*`).

Leave the PR **draft** and don't merge it.

---

## 12. Decisions already made for you (on plan points that were ambiguous) and stop conditions

Decisions (log any you change):
- **Synced landing timing** needs a shared time on every turn event, so `play_at_ms` is stamped on every turn/win event (5.1). That's the only server change, with no schema change. Animation start is aligned to T so that "when a piece finishes moving" is the same moment on every device.
- **Line selection for chains:** use the first triggering square's line, except 44, which uses the final roll-back outcome's quotable if there is one. A win always plays q51. A swap choice plays nothing new.
- **Rotation and variants** are deterministic from `ev.id` parity, so every device agrees.
- **Radio vs clean treatment** follows `treatment` in `audio-lines.json` (8.2).
- **"Radio chatter" off** silences landing calls, quotables and background chatter. Dice and crowd cues remain.
- **Sonniss** is excluded under the user's CC0-only rule, even though the plan lists it as a candidate source.
- **Place phrases for action squares** (e.g. "the cholla patch", "the records office") are proposals flagged for review. They're rarely heard, because quotables replace generic calls on those squares.
- **Hazard dispatch replies** aren't wired into landings, because that would stack (plan D). They're available for chatter or future use.

**Stop and log a question (don't guess) if:**
- a step would delete or overwrite files you didn't create, or rewrite git history;
- you need credentials, an account, a paid tool or a non-CC0 asset;
- a test fails and the fix would change game rules, the board JSON or the DB schema;
- MAMP or the database isn't set up;
- `main` or `prototype-m1` would be touched in any way;
- disk space drops below 5 GB.

---

## 13. How to start (paste this into Claude Code)

> You are working in my clone of CosmicCEO/anza-borrego-challenge on this Mac. First run `git fetch origin && git checkout audio-build && git pull --ff-only`, then read `docs/HANDOFF-CLAUDE-AUDIO.md` from top to bottom and follow it as your instructions. Its guardrails override anything else: work only on the `audio-build` branch, never push to `main`, never force-push, commit small and often, use only CC0 third-party sounds (each one logged in `desertranger/audio/CREDITS.md`) and free/open-source tools, never add secrets, and stop and write down the question instead of guessing on anything destructive. Work through the phases in order and tick the checkboxes as you go. Keep `docs/AUDIO-BUILD-LOG.md` updated after every task, and push to `origin audio-build` after each commit. I'm away for several hours, so don't wait for me: when something is blocked, log it as an open question, skip it, and carry on. When you finish or run out of time, update the draft PR description with the summary described in section 11.
