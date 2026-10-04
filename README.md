# Anza-Borrego State Park Challenge (Desert Ranger)

A turn-based web board game for 2 to 8 players, played from phones in the same room or remotely, with a solo demo against computer rivals. **Wave 1 (Milestone 1) is complete and live** on the client's own PHP/MySQL hosting (tag `milestone-1`, Oct 2026).

## Docs
- [Prototype: run locally, MAMP, test results, known gaps](docs/PROTOTYPE.md)
- [Deploy to the client's Network Solutions host](docs/DEPLOY-NS.md) and the [hand-off for an AI assistant doing it](docs/HANDOFF-NS-DEPLOY.md)
- Sound: [build log](docs/AUDIO-BUILD-LOG.md), [plan](docs/AUDIO-PLAN-AMBIENCE-RADIO.md), [research](docs/AUDIO-RESEARCH.md), [original hand-off](docs/HANDOFF-CLAUDE-AUDIO.md), the script in `docs/audio-lines.json`; every clip can be auditioned on `desertranger/audio/review.html`
- [Build plan (the original M0 to M6 breakdown)](docs/PLAN.md) and [rules notes](docs/RULES-NOTES.md)
- Open work and feedback are tracked as GitHub issues (the Wave 1 playtest list is issue #31).

## What is where
| Folder | What |
|---|---|
| `desertranger/` | The game: plain PHP + MySQL + vanilla JavaScript (no build step); `audio/` holds the shipped sound |
| `board/` | Master board data (`desert-ranger.json`) |
| `tools/audio/` | The sound build: voice generation, speech check, mastering, review page |
| `dev/` | Tests and helpers: browser tests, a mock API, the deploy folder builder and live-site checker, the test-room cleanup SQL |
| `design/` | Design sources, including the **pitch sheet** generator (`design/pitch/`, two pages, `render.js`) |
| `host-test/` | A hosting-capability probe, for checking a new host before deploying |

Images, fonts and the crowd clips are not in git: unzip `desertranger-assets-for-mac.zip` at the repo root (or run `dev/make-assets.sh`).
