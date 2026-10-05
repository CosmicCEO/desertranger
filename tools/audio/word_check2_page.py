#!/usr/bin/env python3
"""Build the owner's ROUND 2 word check page (issue #28): only the cards he marked Not OK, two new clips each (1 and 2), buttons "1 is OK" / "2 is OK" / "Neither".
usage: python3 tools/audio/word_check2_page.py <round2.json> [--lab audio-work/wordlab] [--out audio-work/wordcheck2]
round2.json = [{word, voice, clip_text, c1: {file, spelling, lead_note}, c2: {...}}] with lab take files from <lab>/takes. mp3 64 kbps mono, relative paths, self-contained page.
Copy results JSON: [{word, voice, choice: "1"|"2"|"neither", spelling1, spelling2}]."""
import argparse, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from word_check_page import mp3, VOICE_LABEL

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cards"); ap.add_argument("--lab", default="audio-work/wordlab"); ap.add_argument("--out", default="audio-work/wordcheck2"); a = ap.parse_args()
    C = json.load(open(a.cards)); os.makedirs(a.out, exist_ok=True); cards = []
    for c in C:
        base = f"{re.sub(r'[^a-z0-9]', '', c['word'].lower())}-{c['voice'].replace('_', '')}"
        for k in ("1", "2"): mp3(f"{a.lab}/takes/{c['c' + k]['file']}", f"{a.out}/{base}-{k}.mp3")
        cards.append(dict(word=c["word"], voice=c["voice"], voice_label=VOICE_LABEL[c["voice"]], clip_text=c["clip_text"], mp3_1=f"{base}-1.mp3", mp3_2=f"{base}-2.mp3",
                          spelling1=c["c1"]["spelling"], spelling2=c["c2"]["spelling"], note1=c["c1"].get("lead_note", ""), note2=c["c2"].get("lead_note", "")))
    json.dump(cards, open(f"{a.out}/cards.json", "w"), indent=1)
    open(f"{a.out}/index.html", "w").write(PAGE.replace("__CARDS__", json.dumps(cards)))
    print(len(cards), "cards;", len(os.listdir(a.out)), "files in", a.out)

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Desert Ranger word check, round 2</title>
<style>
:root{--bg:#f6f1e7;--card:#fffdf8;--ink:#2b2418;--mute:#6b6252;--line:#d9cfba;--ok:#1f7a3d;--okbg:#e3f3e8;--bad:#b3261e;--badbg:#fbe7e5;--play:#2b2418;--playink:#fffdf8}
@media (prefers-color-scheme:dark){:root{--bg:#1b1812;--card:#26221a;--ink:#f1ead9;--mute:#b4aa94;--line:#41392a;--ok:#6fd08c;--okbg:#17301f;--bad:#ff8a80;--badbg:#3a1c19;--play:#f1ead9;--playink:#1b1812}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.4 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding:16px;max-width:640px;margin-inline:auto}
h1{font-size:22px;margin:4px 0 6px}
p.lead{color:var(--mute);margin:0 0 14px}
#bar{position:sticky;top:0;background:var(--bg);padding:8px 0;border-bottom:1px solid var(--line);margin-bottom:12px;z-index:2;display:flex;justify-content:space-between;align-items:center;gap:8px}
.card{background:var(--card);border:2px solid var(--line);border-radius:16px;padding:14px;margin:0 0 14px}
.card.c1,.card.c2{border-color:var(--ok);background:var(--okbg)}.card.neither{border-color:var(--bad);background:var(--badbg)}
.word{font-size:26px;font-weight:700}.voice{font-size:14px;color:var(--mute);text-transform:uppercase;letter-spacing:.06em}
.sp{font-size:15px;color:var(--mute);margin:2px 0 10px}
button{font:inherit;border:0;border-radius:14px;cursor:pointer;touch-action:manipulation}
.clip{margin:0 0 10px}.clip .lab{font-size:14px;color:var(--mute);margin-bottom:4px}.clip .lab b{color:var(--ink)}
.play{display:block;width:100%;min-height:64px;font-size:22px;font-weight:700;background:var(--play);color:var(--playink)}
.play.on{outline:4px solid var(--ok)}
.row{display:flex;gap:8px}.row button{flex:1;min-height:60px;font-size:18px;font-weight:700;border:3px solid var(--line);background:var(--card);color:var(--ink)}
.row .sel1,.row .sel2{background:var(--ok);border-color:var(--ok);color:#fff}.row .seln{background:var(--bad);border-color:var(--bad);color:#fff}
.tools{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0 8px}.tools button{min-height:54px;padding:0 18px;font-size:18px;font-weight:700;background:var(--play);color:var(--playink)}
textarea{width:100%;min-height:150px;font:13px/1.35 ui-monospace,Menlo,monospace;background:var(--card);color:var(--ink);border:2px solid var(--line);border-radius:12px;padding:10px}
#stop{min-height:40px;font-size:15px;padding:0 14px;border-radius:10px;background:var(--play);color:var(--playink)}
.note{font-size:13px;color:var(--mute)}
</style></head><body>
<h1>Word check, round 2</h1>
<p class="lead">These are the words that were Not OK. Each has two new tries, <b>1</b> and <b>2</b>. Tap Play on each. If one of them says the word right, tap <b>1 is OK</b> or <b>2 is OK</b>. If neither does, tap <b>Neither</b>. Only the word matters. Answers are saved on this device as you go.</p>
<div id="bar"><span id="count">0 of 0 answered</span><button id="stop">Stop sound</button></div>
<div id="cards"></div>
<div class="tools"><button id="copy">Copy my results</button><button id="dl">Download word-verdicts-round2.json</button></div>
<p class="note" id="msg">When you are done, tap <b>Copy my results</b> and paste the text back to Claude. If copying is blocked, select the box below and copy it by hand.</p>
<textarea id="out" readonly aria-label="Your results as JSON"></textarea>
<script>
const CARDS = __CARDS__;
const KEY = "desertranger-wordcheck-round2-v1";
let V = {};
try { V = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) { V = {}; }
function save(){ try { localStorage.setItem(KEY, JSON.stringify(V)); } catch (e) {} }
const id = c => c.word + "|" + c.voice;
const cur = new Audio(); let curBtn = null;
function idle(b){ if (b) { b.classList.remove("on"); b.textContent = "▶ Play " + b.dataset.n; } }
cur.addEventListener("ended", () => idle(curBtn));
function results(){ return CARDS.filter(c => V[id(c)]).map(c => ({word: c.word, voice: c.voice, choice: V[id(c)], spelling1: c.spelling1, spelling2: c.spelling2})); }
function refresh(){
  CARDS.forEach(c => { const el = document.getElementById("c-" + id(c).replace(/\W/g, "_")), v = V[id(c)];
    el.className = "card" + (v ? " " + (v === "neither" ? "neither" : "c" + v) : "");
    el.querySelector(".b1").classList.toggle("sel1", v === "1"); el.querySelector(".b2").classList.toggle("sel2", v === "2"); el.querySelector(".bn").classList.toggle("seln", v === "neither"); });
  const r = results(); document.getElementById("count").textContent = r.length + " of " + CARDS.length + " answered";
  document.getElementById("out").value = JSON.stringify(r, null, 1);
}
const esc = s => String(s).replace(/[&<>"]/g, m => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[m]));
CARDS.forEach(c => {
  const d = document.createElement("div"); d.className = "card"; d.id = "c-" + id(c).replace(/\W/g, "_");
  const clip = (n, sp, note, src) => '<div class="clip"><div class="lab"><b>' + n + '</b> &middot; heard as written spelling: <b>' + esc(sp) + '</b>' + (note ? ' &middot; ' + esc(note) : '') +
    '</div><button class="play" data-n="' + n + '" data-src="' + src + '">▶ Play ' + n + '</button></div>';
  d.innerHTML = '<div class="voice">' + esc(c.voice_label) + '</div><div class="word">' + esc(c.word) + '</div><div class="sp">clip: “' + esc(c.clip_text) + '”</div>' +
    clip("1", c.spelling1, c.note1, c.mp3_1) + clip("2", c.spelling2, c.note2, c.mp3_2) +
    '<div class="row"><button class="b1">1 is OK</button><button class="b2">2 is OK</button><button class="bn">Neither</button></div>';
  d.querySelectorAll(".play").forEach(pb => pb.onclick = () => {
    if (curBtn === pb && !cur.paused) { cur.pause(); idle(pb); return; }
    idle(curBtn); cur.src = pb.dataset.src; cur.currentTime = 0; cur.play(); curBtn = pb; pb.classList.add("on"); pb.textContent = "■ Playing " + pb.dataset.n; });
  d.querySelector(".b1").onclick = () => { V[id(c)] = "1"; save(); refresh(); };
  d.querySelector(".b2").onclick = () => { V[id(c)] = "2"; save(); refresh(); };
  d.querySelector(".bn").onclick = () => { V[id(c)] = "neither"; save(); refresh(); };
  document.getElementById("cards").appendChild(d);
});
document.getElementById("stop").onclick = () => { cur.pause(); idle(curBtn); };
document.getElementById("copy").onclick = async () => {
  const t = JSON.stringify(results(), null, 1), ta = document.getElementById("out"), m = document.getElementById("msg");
  try { await navigator.clipboard.writeText(t); m.innerHTML = "<b>Copied.</b> Paste it back to Claude."; }
  catch (e) { ta.focus(); ta.select(); try { document.execCommand("copy"); m.innerHTML = "<b>Copied.</b> Paste it back to Claude."; } catch (e2) { m.textContent = "Copy was blocked: press and hold in the box below, Select All, Copy."; } }
};
document.getElementById("dl").onclick = () => {
  const b = new Blob([JSON.stringify(results(), null, 1)], {type: "application/json"}), a = document.createElement("a");
  a.href = URL.createObjectURL(b); a.download = "word-verdicts-round2.json"; document.body.appendChild(a); a.click(); a.remove();
};
refresh();
</script></body></html>
"""
if __name__ == "__main__": main()
