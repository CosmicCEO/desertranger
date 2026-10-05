#!/usr/bin/env python3
"""Pronunciation helpers shared by gen_lines.py and build_review.py (pure Python, no torch).
Chatterbox reads an ALL-CAPS syllable letter by letter ("sah-LAH-doh" -> "L A H", "OYA" -> "O Y A"), so speak() rewrites every
respelling before it reaches the TTS: any hyphen part with 2+ capitals becomes Title-Case ("LAH" -> "Lah", "VAYA-SEE-TOE" -> "Vaya-See-Toe").
Everything else is sent as written. Applies to the shared table, the per-line "pronounce" dicts and the alternatives.
usage: python3 tools/audio/pron.py --check     # exit 1 if any respelling that would be sent to TTS still has 2+ consecutive capitals"""
import json, re, sys
def speak(v):
    return "-".join(p.capitalize() if re.search(r"[A-Z]{2,}", p) else p for p in v.split("-"))
def apply(text, table):
    for k, v in table.items(): text = re.sub(r"\b" + re.escape(k) + r"\b", speak(v), text, flags=re.I)
    return text
if __name__ == "__main__":
    D = json.load(open("docs/audio-lines.json")); bad = []
    sets = [("pronunciations", D.get("pronunciations", {})), ("pronunciation_alternatives", D.get("pronunciation_alternatives", {}))]
    sets += [(l["id"] + ".pronounce", l["pronounce"]) for l in D["lines"] if l.get("pronounce")]
    n = 0
    for name, t in sets:
        for k, v in t.items():
            n += 1
            if re.search(r"[A-Z]{2,}", speak(v)): bad.append((name, k, v, speak(v)))
    for l in D["lines"]:   # also any all-caps run left in tts_text/text-derived input after the table is applied (acronyms like VIP are spelled "V I P" on purpose)
        t = apply(l.get("tts_text", l["text"]), D.get("pronunciations", {}))
        for m in re.finditer(r"\b[A-Z]{2,}\b", t):
            if m.group() not in ("OK",): bad.append((l["id"], "tts", m.group(), t))
    print(n, "respellings checked;", "FAIL" if bad else "OK")
    for b in bad: print("  ", b)
    sys.exit(1 if bad else 0)
