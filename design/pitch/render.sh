#!/bin/bash
cd "$(dirname "$0")"
python3 build.py
F="file://$PWD/desert-ranger-pitch.html"
google-chrome --headless=new --no-sandbox --disable-gpu --allow-file-access-from-files --hide-scrollbars --window-size=816,1056 --force-device-scale-factor=2.7 --virtual-time-budget=3000 --screenshot="$PWD/desert-ranger-pitch.png" "$F" 2>/dev/null
google-chrome --headless=new --no-sandbox --disable-gpu --allow-file-access-from-files --no-pdf-header-footer --virtual-time-budget=3000 --print-to-pdf="$PWD/desert-ranger-pitch.pdf" "$F" 2>/dev/null
python3 -c "from PIL import Image;print(Image.open('desert-ranger-pitch.png').size)"; pdfinfo desert-ranger-pitch.pdf | grep -E 'Pages|Page size'
