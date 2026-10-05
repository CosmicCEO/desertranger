# design/: text sources of the design work

These scripts produced the board data, the art and the crowd sounds before the
prototype was built. **The game does not need anything in this folder.** It is
kept so the work can be redone or tweaked. The folder mirrors the original design
workspace (`/workspace/boardgame` on the build box), so relative paths in the scripts still work.

Binaries are not in git. Their originals are in `desertranger-assets-for-mac.zip`
under `art-binaries/`. To rerun scripts here, unzip the zip at the repo root, then:

```bash
cp -R art-binaries/art/.   design/art/
cp -R art-binaries/pitch/. design/pitch/
cp art-binaries/board-photo-original-4913x3583.jpg design/orig.jpg
```
These paths are gitignored (`design/**/*.jpg|png|pdf|...`).

| Path | What it is |
|---|---|
| `build.py` | First pass of the board data. It holds 52 squares with x,y read at 1024 px and writes `board/desert-ranger.json` scaled to photo pixels (4913×3583). **The master is now `/board/desert-ranger.json` at the repo root**, which was edited after this pass. Don't rerun this over it blindly. |
| `crop.py`, `lcrop.py` | Crop regions of the board photo (`orig.jpg`) and the left-half close-up (`left_t.jpg`, not in the zip) into `crops/` to read the squares. |
| `art/_work/*.py` | Board art pipeline (OpenCV, run from `art/`). `detect.py` finds the board quad and `warp.py` flattens it to `board-flat.jpg`. That warp's matrix is what `desertranger/assets/js/board.js` uses to place pieces. `lineart.py`, `thresh.py`, `masks.py`, `track*.py`, `lettering.py` make line art and layers; `extract_icons.py` / `icons_spec.py` cut the doodles into icons; `sheet.py` makes the icon preview. `quad.npy` is in the zip. |
| `art/icons/manifest.json` | Icon index: slug, label, the square(s) it belongs to, its bounding box on the flat board, and its PNG/SVG files. `_original/` is the first extraction. The icon PNG/SVG files are in the zip; the SVGs are about 3 MB, too big to push through the connector. |
| `scripts/*.py` | Crowd-sound pipeline. `crowd_*` is v1 and `crowd_v2_*` made the `crowd-cheer-v2.mp3` / `crowd-aww-v2.mp3` the game uses (generation, screening, mixing, loudness normalising). `kokoro_candidates.py`, `cb_*.py` are the voice-line experiments. See `docs/AUDIO-RESEARCH.md`. |
| `audio/samples/crowd/mixlog*.json` | Mix recipes (which takes, gains, offsets) behind each crowd clip. |
| `pitch/build.py`, `render.sh`, `render.js`, `desert-ranger-pitch.html` | Client pitch sheet, now **two pages**: page 1 is the pitch (with the plan's status), page 2 is the status report (what was delivered, what changed, how it was checked, what is next). `build.py` writes the HTML; `render.sh` renders the PNG and PDF with headless Chrome on Linux; `render.js` does the same with Playwright on a Mac (`node design/pitch/render.js [outBase]`, needs `cd dev/e2e && npm install`; it also writes `<outBase>-status.png` for page 2). It also checks the layout (text past a card, overlap with the footer). `pitch/make.sh [name]` does it all in one command: render to new dated files, layout check, PDF page count (`make.sh wave2` renders `build-wave2.py`, the Wave 2 plan sheet, which reuses `build.py`'s look). It needs `pitch/fonts/` and `pitch/img/` from the zip. The colours and fonts in `desertranger/assets/css/style.css` come from here. |

Note: a few scripts contain absolute paths from the build box (`/home/box/...`
attachment folder, `/workspace/boardgame`, `/tmp` scratch files). Adjust them if
you rerun the scripts elsewhere.
