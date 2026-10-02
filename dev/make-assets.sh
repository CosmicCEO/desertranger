#!/usr/bin/env bash
# Rebuild the BINARY assets of desertranger/ (they are not in git: the GitHub
# connector used for this repo only accepts text files), and copy the board
# JSON into desertranger/board/. Run this before uploading to the host.
#
# Run from a folder that has the original art/audio/fonts, laid out like the
# design workspace:   art/board-flat.jpg  art/pieces/*.png
#                     audio/samples/crowd/crowd-{cheer,aww}-v2.mp3  pitch/fonts/*.ttf
#                     board/desert-ranger.json   (a repo checkout has this one too)
#   bash dev/make-assets.sh /path/to/boardgame-workspace  desertranger
# Needs python3 with Pillow (pip install pillow).
set -euo pipefail
SRC=${1:?source workspace}; DST=${2:-desertranger}
A="$DST/assets"
mkdir -p "$A/img/pieces" "$A/audio" "$A/fonts"
python3 - "$SRC" "$A" <<'PY'
import sys, glob, os
from PIL import Image
src, a = sys.argv[1], sys.argv[2]
im = Image.open(os.path.join(src, 'art/board-flat.jpg'))            # 4372x3321
im = im.resize((2000, round(2000 * im.height / im.width)), Image.LANCZOS)
im.save(os.path.join(a, 'img/board-2000.jpg'), quality=80, optimize=True, progressive=True)
for f in glob.glob(os.path.join(src, 'art/pieces/*.png')):
    if 'preview' in f: continue
    p = Image.open(f); p.thumbnail((200, 200), Image.LANCZOS)
    p.save(os.path.join(a, 'img/pieces', os.path.basename(f)), optimize=True)
PY
cp "$SRC"/audio/samples/crowd/crowd-cheer-v2.mp3 "$SRC"/audio/samples/crowd/crowd-aww-v2.mp3 "$A/audio/"
for f in Bungee-Regular BungeeShade-Regular Nunito Caveat; do cp "$SRC/pitch/fonts/$f.ttf" "$A/fonts/"; done
# Deploy copy of the board data (master: /board/desert-ranger.json in the repo / workspace).
mkdir -p "$DST/board" && cp "$SRC/board/desert-ranger.json" "$DST/board/"
echo "Assets + board written to $DST"
