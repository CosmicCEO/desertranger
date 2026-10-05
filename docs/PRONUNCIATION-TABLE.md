# Pronunciation table (issue #28)

`docs/audio-lines.json` key `pronunciations`: written word -> `{default, senior_ranger?, ranger_273?}`. The spelling sent to the voice is the
per-voice override, else the default. `gen_lines.py` substitutes it into every generation; `qa_check.py` accepts the written word or the
respelling when Whisper listens.

Format rules (checked by `python3 tools/audio/pron.py --check`, proven by `--selftest`): letters a-z only, lowercase or Title-case. No hyphens,
no capital runs, no digits, no apostrophes. Chatterbox spells a capital run letter by letter and pauses at a hyphen, so syllables are written
with letters (`vayaseetoe`), not punctuation. Legacy per-line `pronounce` dicts are only used with `gen_lines.py --pron` and are skipped if they
break the rules (`pron.py --check --lines` lists them).

Tools (all local, free): `word_lab.py` renders candidate spellings x seeds inside the real clip text (Chatterbox venv);
`word_metrics.py --lab / --old / --old-pass / --report / --selftest` scores them (Whisper venv; pause, fragmentation, spelled letters,
duration, length) and writes `audio-work/wordlab/report.md` plus the table winners; `word_check_page.py` builds the owner's OK / Not OK page.
The judge is Whisper small.en: it spells "o-co-TIL-lo" and "o-co-TEE-yo" the same, so the owner's listen is the final gate.

## Owner verdicts (word check, round 1) and what shipped
OK: Ocotillo (both voices, `Ocotiyo`), Vallecito ranger_273 (`vayaseetoe`), Olla ranger_273 (`oya`), Cholla both (`choya`), Salado both (plain), Cabezas both (plain), Cafe both (plain), Burro Bend both (plain).
Not OK: Vallecito senior_ranger, Olla senior_ranger, Yaqui senior_ranger and ranger_273 (round 2 page in `audio-work/wordcheck2/`). Those voices stay on their Wave 1 (plain) sound: the table has
`senior_ranger: Vallecito` / `olla` overrides and Yaqui stays `Yaqui` until round 2 is answered. Table entries only change what a *regeneration* sends; `pron.py --check` enforces the format.
Lines whose word is not approved (other voices, plant names) are not regenerated. Leading-artifact check: `tools/audio/word_lead.py` (burst, click, stray sound, long lead-in, onset < 30 ms, stray first token),
part of the `qa_check.py` gate for table-word lines; a fixable artifact gets a trimmed `_lf.wav` copy (starts 35 ms before the word, 8 ms fade-in, the word itself untouched).
