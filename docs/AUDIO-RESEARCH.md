# Audio Research: SFX + Voice Lines for the Candy-Land-style Web Board Game

*Researched Oct 1, 2026. Licenses were checked against the primary source (repo README/LICENSE, the Hugging Face model card/license tag, or the vendor's license page). Links are inline. Anything I couldn't confirm is marked **⚠ unverified**. This isn't legal advice. Before shipping commercially, re-read the license of the exact checkpoint you use.*

---

## TL;DR: Recommended stack

| Need | Pick | Why |
|---|---|---|
| **Narrator / character voice lines (commercial-safe, clean)** | **Kokoro-82M** (Apache-2.0 code + weights) | Very clean, studio-like output. Tiny (82M) and fast on a Mac CPU or MPS. 54 preset voices. Trained only on permissive/public-domain/synthetic data. This is the most likely candidate for the "open source software that yielded good clean content" Jerod remembers. |
| **Expressive lines (laughs, "aww!", gasps, cheering)** | **Chatterbox / Chatterbox-Turbo** (MIT code + weights) | Supports `[laugh]`, `[chuckle]`, `[cough]` tags (Turbo), emotion/exaggeration control, and zero-shot voice cloning. Runs on `mps`. Note: it embeds an inaudible Perth watermark in every output. |
| Backup expressive option | **Dia-1.6B** (Apache-2.0) | Generates dialogue with `(laughs)`, `(gasps)`, `(applause)`, and similar. Lower fidelity than Kokoro, and outputs need cherry-picking. |
| **UI / game SFX (dice, pawn hops, card flips, win jingles)** | **ChipTone** or **jsfxr** for stylized/retro, plus **Kenney.nl CC0 packs** for "real" sounds | Zero license risk. ChipTone output is explicitly CC0. Kenney assets are CC0. |
| **Laugh track, sad trombone, crowd "aww", applause** | **Freesound with the CC0 filter**, **Sonniss GDC bundles** (royalty-free, no attribution) | Generative models handle these poorly. Real recordings sound better. |
| AI-generated SFX (optional) | **Stable Audio 3.0 Small-SFX** or **Stable Audio Open 1.0** | Commercial use is free under the Stability AI Community License while annual revenue is under $1M. |
| **Cleanup / mastering** | **ffmpeg `loudnorm`** (batch normalize to about −16 LUFS), **Audacity** (trim/fade), **DeepFilterNet** (denoise if needed) | All free/open source. |

**Avoid for a possibly-commercial game:** Coqui XTTS-v2 (non-commercial CPML, and Coqui is defunct so you can't buy a license), F5-TTS weights (CC-BY-NC), AudioCraft/AudioGen weights (CC-BY-NC), Tango/Tango2/TangoFlux, AudioLDM2, MMAudio, AudioX (all NC), Spark-TTS weights (CC-BY-NC-SA), and some Piper voices (check each voice's dataset license).

---

## 1. TTS / Voice comparison

| Tool | Code license | Weights license | Commercial OK? | Clean/quality | Expressiveness | Apple Silicon | Voice cloning |
|---|---|---|---|---|---|---|---|
| **Kokoro-82M** (hexgrad) | Apache-2.0 | **Apache-2.0** ([HF card](https://huggingface.co/hexgrad/Kokoro-82M)) | ✅ Yes | ⭐⭐⭐⭐⭐ very clean, consistent | Low–medium (no laugh tags; prosody follows punctuation) | ✅ CPU, or MPS with `PYTORCH_ENABLE_MPS_FALLBACK=1` ([README](https://github.com/hexgrad/kokoro)) | ❌ (54 preset voices across 8 languages; voices can be blended) |
| **Chatterbox / -Turbo / -Nano** (Resemble AI) | MIT ([repo](https://github.com/resemble-ai/chatterbox)) | **MIT** ([HF chatterbox](https://huggingface.co/ResembleAI/chatterbox), [HF turbo](https://huggingface.co/ResembleAI/chatterbox-turbo)) | ✅ Yes | ⭐⭐⭐⭐½ | **High**: `[laugh]`, `[chuckle]`, `[cough]` tags in Turbo/Nano, plus an exaggeration knob | ✅ README lists `device="mps"` | ✅ zero-shot from a short clip |
| **Dia-1.6B** (Nari Labs) | Apache-2.0 ([HF](https://huggingface.co/nari-labs/Dia-1.6B-0626), [README](https://github.com/nari-labs/dia)) | **Apache-2.0** | ✅ Yes | ⭐⭐⭐½ (varies; seed-dependent) | **Very high**: `(laughs)`, `(sighs)`, `(gasps)`, `(applause)`, `(screams)`, … and 2-speaker dialogue | ⚠ CPU/MPS works per community reports; the README lists "MacOS support" as a TODO | ✅ via audio prompt |
| **Orpheus 3B** (Canopy Labs) | Apache-2.0 ([repo](https://github.com/canopyai/Orpheus-TTS)) | HF tag says Apache-2.0, **but it's built on a Llama-3.2-3B backbone**. ⚠ It's unverified whether Llama Community License terms also apply. The HF repo is gated. | ⚠ Probably yes; verify | ⭐⭐⭐⭐ | **High**: `<laugh>`, `<chuckle>`, `<sigh>`, `<gasp>`, `<groan>`, `<yawn>` | ✅ via llama.cpp/GGUF (README "No GPU inference") | ✅ (fine-tune) |
| **Bark** (Suno) | MIT | **MIT** since 2023-05-01 ([README](https://github.com/suno-ai/bark)) | ✅ Yes | ⭐⭐½: noisy, unpredictable, hallucinates | Very high (`[laughs]`, `[sighs]`, music) | ✅ (slow) | Voice prompts only |
| **OpenVoice V2** (MyShell) | MIT ([repo](https://github.com/myshell-ai/OpenVoice)) | **MIT** since Apr 2024 ([README](https://github.com/myshell-ai/OpenVoice)) | ✅ Yes | ⭐⭐⭐ | Medium (style control) | ✅ | ✅ (tone-color converter; often paired with MeloTTS) |
| **Parler-TTS mini/large v1** (HF) | Apache-2.0 | **Apache-2.0** ([HF mini](https://huggingface.co/parler-tts/parler-tts-mini-v1)) | ✅ Yes | ⭐⭐⭐½ | Medium: describe the voice in text ("a cheerful woman, fast, close mic") | ✅ (README has Apple Silicon notes) | ❌ (prompt-described voices) |
| **StyleTTS 2** | MIT | Pretrained models carry a custom condition: you must tell listeners the speech is synthetic unless you have the speaker's permission ([README](https://github.com/yl4579/StyleTTS2)) | ⚠ Yes, with a disclosure requirement | ⭐⭐⭐⭐½ | Medium | ✅ CPU | ✅ (some inference deps are GPL) |
| **Piper** (OHF-Voice/Rhasspy) | Original `rhasspy/piper`: MIT (**archived**). Active fork `OHF-Voice/piper1-gpl`: **GPL-3.0** ([repo](https://github.com/OHF-Voice/piper1-gpl)) | **Per voice.** Repo is tagged MIT, but each voice's MODEL_CARD names its dataset license. Examples: `en_US-joe` = CC0 ✅, `libritts_r` = CC BY 4.0 ✅, `en_GB-alba` = CC BY 4.0 ✅, `en_US-ryan` = **CC BY-NC-SA** ❌, `hfc_female` = **CC BY-NC-SA** ❌, `lessac` = Blizzard 2013 license ⚠ (restrictive) ([voices](https://huggingface.co/rhasspy/piper-voices)) | ⚠ Depends on the voice | ⭐⭐⭐ (clean but a bit robotic) | Low | ✅ very fast, even on a Raspberry Pi | ❌ (train your own) |
| **Coqui XTTS-v2** | MPL-2.0 (now maintained at [idiap/coqui-ai-TTS](https://github.com/idiap/coqui-ai-TTS)) | **Coqui Public Model License**: "allows only non-commercial use of a machine learning model **and its outputs**" ([LICENSE](https://huggingface.co/coqui/XTTS-v2/blob/main/LICENSE.txt)) | ❌ **No.** Coqui shut down, so no commercial license can be bought | ⭐⭐⭐⭐ | Medium | ✅ | ✅ |
| **F5-TTS** | MIT | **CC-BY-NC** (Emilia dataset) ([README](https://github.com/SWivid/F5-TTS)) | ❌ No | ⭐⭐⭐⭐½ | Medium | ✅ (README has an Apple Silicon section) | ✅ excellent |
| **Spark-TTS** | Apache-2.0 | **CC-BY-NC-SA-4.0** ([HF](https://huggingface.co/SparkAudio/Spark-TTS-0.5B)) | ❌ No | ⭐⭐⭐⭐ | Medium | ⚠ | ✅ |
| Zonos v0.1 (Zyphra) | Apache-2.0 | Apache-2.0 ([HF](https://huggingface.co/Zyphra/Zonos-v0.1-transformer)) | ✅ | ⭐⭐⭐⭐ | High (emotion sliders) | ⚠ Mac support was limited at launch | ✅ |
| Sesame CSM-1B | Apache-2.0 | Apache-2.0 ([HF](https://huggingface.co/sesame/csm-1b)) | ✅ (gated; also uses a Llama backbone, ⚠) | ⭐⭐⭐½ | Conversational | ⚠ | ✅ |
| Kyutai TTS 1.6B | Apache-2.0 (code) | CC-BY-4.0 ([HF](https://huggingface.co/kyutai/tts-1.6b-en_fr)) | ✅ with attribution | ⭐⭐⭐⭐ | Medium | ✅ (MLX build per Kyutai repo, ⚠) | Limited |
| CosyVoice2-0.5B | Apache-2.0 | Apache-2.0 ([HF](https://huggingface.co/FunAudioLLM/CosyVoice2-0.5B)) | ✅ | ⭐⭐⭐⭐ | Medium–high | ⚠ | ✅ |
| NeuTTS Air / KittenTTS | Apache-2.0 | Apache-2.0 ([neutts](https://huggingface.co/neuphonic/neutts-air), [kitten](https://huggingface.co/KittenML/kitten-tts-nano-0.2)) | ✅ | ⭐⭐⭐ / ⭐⭐½ (tiny models) | Low | ✅ CPU | NeuTTS ✅ / Kitten ❌ |
| Microsoft VibeVoice | MIT | MIT, but **Microsoft removed the TTS code (2025-09-05) and does not recommend commercial use** ([README](https://github.com/microsoft/VibeVoice)) | ⚠ Avoid | — | — | — | — |

Quality star ratings are my qualitative summary of community consensus (TTS Arena-style comparisons and demo samples), not measurements. ⚠ Listen to the samples yourself.

### Voice notes for this game
- **Kids'/family tone:** Kokoro voices such as `af_heart`, `af_bella`, and `am_puck` give clean, upbeat narration ("Roll again!", "You landed on Gumdrop Pass!"). Generate the full line list offline as WAV files, then ship small OGG/MP3/Opus files. **Don't run TTS in the browser at runtime.** (A browser build, kokoro-js, does exist if that's ever needed.)
- **Character moments** (giggles, a sad "awww", cheering): use Chatterbox-Turbo with `[laugh]` / `[chuckle]` tags, or Dia `(laughs)`. Generate 5–10 takes per line and keep the best one.
- **Voice cloning ethics/legal:** only clone voices you own or have written permission to use, such as Jerod's own voice or a hired actor with a release.
- **Watermark:** Chatterbox embeds an imperceptible Perth watermark. That's harmless for a game, but be aware of it.

---

## 2. SFX generation

| Tool | License | Commercial OK? | Quality / fit | Notes |
|---|---|---|---|---|
| **ChipTone** (SFBGames) | Free tool. Outputs are **CC0**: "All sounds created using ChipTone are FREE to use for any purpose, commercial or otherwise, under the CC0 licence" ([itch.io](https://sfbgames.itch.io/chiptone)) | ✅ | ⭐⭐⭐⭐ for cartoony/retro UI blips, jumps, coins, power-ups | HTML5, plus Windows and Mac builds. Very friendly UI. |
| **jsfxr** | **Unlicense** (public domain) ([GitHub](https://github.com/chr15m/jsfxr)) | ✅ | ⭐⭐⭐ retro 8-bit | Runs in the browser at sfxr.me. Can also generate sounds at runtime in JS. |
| **bfxr** (increpare) | ⚠ No license detected on GitHub; the site has historically said generated sounds are free to use ([bfxr.net](https://www.bfxr.net/)) | ✅ outputs (⚠ verify) | ⭐⭐⭐ | Superseded by ChipTone. |
| sfxr (original) | MIT (DrPetter) ⚠ unverified in this pass | ✅ | ⭐⭐½ | The original from 2007. |
| **Stable Audio 3.0 Small-SFX** (Stability AI, 2026) | **Stability AI Community License** ([HF](https://huggingface.co/stabilityai/stable-audio-3-small-sfx), [license FAQ](https://stability.ai/license)) | ✅ **if annual revenue < $1M**; Enterprise license above that. You own the outputs. | ⭐⭐⭐⭐ realistic foley; runs on a MacBook (card says "less than a few seconds on a MacBook Pro M4") | Newest, SFX-specific, 0.6B. Trained on licensed and CC data. |
| **Stable Audio Open 1.0** | Stability AI Community License ([HF](https://huggingface.co/stabilityai/stable-audio-open-1.0)) | ✅ under $1M revenue | ⭐⭐⭐½; card says it is "better at generating sound effects and field recordings than music" | Up to 47 s of 44.1 kHz stereo. Trained on CC0/CC-BY/CC-Sampling+ Freesound and FMA audio. |
| **AudioCraft (AudioGen / MusicGen / MAGNeT)** (Meta) | Code MIT. **Weights CC-BY-NC 4.0** ([README](https://github.com/facebookresearch/audiocraft), [audiogen HF](https://huggingface.co/facebook/audiogen-medium)) | ❌ No | ⭐⭐⭐ (16 kHz mono for AudioGen) | Prototyping only. |
| **Tango / Tango2** | Weights **CC-BY-NC-SA-4.0** ([HF](https://huggingface.co/declare-lab/tango2)) | ❌ | ⭐⭐⭐½ | |
| **TangoFlux** | "Non-commercial research use only" ([README](https://github.com/declare-lab/TangoFlux)) | ❌ | ⭐⭐⭐⭐ | |
| **AudioLDM 2** | Weights **CC-BY-NC-SA-4.0** ([HF](https://huggingface.co/cvssp/audioldm2)) | ❌ | ⭐⭐⭐ | Supports MPS but needs about 20 GB RAM. |
| MMAudio / AudioX | **CC-BY-NC-4.0** ([MMAudio](https://huggingface.co/hkchengrex/MMAudio), [AudioX](https://huggingface.co/HKUSTAudio/AudioX)) | ❌ | ⭐⭐⭐⭐ | |

**Bottom line on SFX:** for a candy-themed board game, ChipTone/jsfxr (stylized) plus Kenney/Freesound CC0 (organic sounds like dice, pops, chimes) cover about 95% of needs with zero license risk. Use Stable Audio 3.0 Small-SFX only for one-off textures you can't find, and keep a note of the revenue threshold.

---

## 3. Laugh track / sad trombone / crowd reactions (CC0 & royalty-free libraries)

| Source | License | Notes |
|---|---|---|
| **Kenney.nl audio packs** (Interface Sounds, UI Audio, Impact Sounds, Casino Audio [dice/chips/cards!], Digital Audio, Music Jingles) | **CC0**. "game assets on the asset pages are public domain licensed (CC0). You're free to use them, even in commercial projects" ([kenney.nl/support](https://kenney.nl/support)) | Best first stop. "Casino Audio" and "Music Jingles" fit a board game well. ⚠ The pack names are from memory; browse [kenney.nl/assets](https://kenney.nl/assets). |
| **Freesound.org** with the **license filter set to "Creative Commons 0"** | Per-sound: CC0, CC-BY, or CC-BY-NC | Search "sad trombone", "wah wah", "sitcom laugh", "crowd aww", "applause", "kids cheer". **Only take CC0** (or CC-BY with a credits screen); **skip NC**. |
| **Sonniss #GameAudioGDC bundles** (2015–2026, about 200+ GB total; 2026 = 7.47 GB) | Royalty-free, commercial use, **no attribution**, unlimited projects. **Can't resell the raw files; AI/ML training prohibited** ([license](https://sonniss.com/gdc-bundle-license/), [archive](https://sonniss.com/gameaudiogdc/), [2026](https://gdc.sonniss.com/)) | Pro-grade crowd/applause/foley. Not CC0, but fine for shipping in a game. |
| **OpenGameArt.org** | Mixed (CC0, CC-BY, CC-BY-SA, GPL…) per asset | Filter to CC0. Check each asset. |
| Sad trombone / laugh track via TTS models | Bark/Dia can produce `[laughs]` / `(applause)` | Usually lower quality than real recordings. Use only as a fallback. |

*Caution:* the iconic "wah-wah-wah-waaah" is a short musical phrase and is generally considered too short or generic to be copyrightable. ⚠ That's not legal advice. The safest route is to use a CC0 recording, or play it yourself / synthesize it (ChipTone can approximate it, and an actual trombone sample from Freesound CC0 can be pitch-bent in Audacity).

---

## 4. Cleanup & mastering tools

| Tool | License | Use |
|---|---|---|
| **ffmpeg `loudnorm`** (EBU R128) | LGPL/GPL | Batch-normalize every clip so voice and SFX sit at a consistent level. Example: `ffmpeg -i in.wav -af "silenceremove=start_periods=1:start_threshold=-50dB,loudnorm=I=-16:TP=-1.5:LRA=11" -ar 44100 out.wav`, then encode with `-c:a libopus -b:a 64k out.ogg` (or MP3 for Safari fallback). Two-pass loudnorm is more accurate. |
| **Audacity** | GPL-2.0/3.0 | Trim, fade, pitch-shift (sad trombone), compressor, Noise Reduction. Batch processing via Macros. |
| **DeepFilterNet** | MIT / Apache-2.0 dual ([README](https://github.com/Rikorose/DeepFilterNet)) | AI denoise for recorded or cloned voices. Runs on macOS. Usually unnecessary for Kokoro output, which is already clean. |
| **RNNoise** (Xiph) | BSD-3-Clause ([GitHub](https://github.com/xiph/rnnoise)) | Lightweight denoise. Also available inside ffmpeg as the `arnndn` filter. |

---

## 5. Suggested pipeline (Mac)

1. `pip install kokoro soundfile` (plus `brew install espeak-ng`). Script all voice lines from a CSV (`id,voice,text`) into `audio/vo/*.wav`.
2. For emotive lines: `pip install chatterbox-tts`, use `device="mps"`, and generate several takes with `[laugh]` / `[chuckle]` tags.
3. SFX: design them in ChipTone (export WAV), and pull Kenney CC0 packs plus Freesound CC0 items. Log every source and license in `audio/CREDITS.md`.
4. Batch-process: ffmpeg trim silence, `loudnorm` (about −16 LUFS for VO and −18 to −20 LUFS for SFX beds), encode to Opus/OGG plus MP3/AAC fallback.
5. In the web app, play through the Web Audio API or Howler.js (MIT) with audio sprites.

## Open questions / unverified items
- Orpheus: whether Llama 3.2 Community License terms apply on top of the Apache-2.0 tag (the HF repo is gated, so I couldn't read the full card).
- bfxr: the GitHub repo shows no license file. Output usage terms are from historical site wording.
- Dia on Apple Silicon: works per community reports, but the official README lists Mac support as a TODO.
- Exact Kenney pack names: browse the site.
- Stability Community License: it's revocable if violated, and requires registration/Enterprise once revenue exceeds $1M. Re-read the **full community license** before commercial launch.
