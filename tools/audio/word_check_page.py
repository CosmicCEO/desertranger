#!/usr/bin/env python3
"""Build the owner's "word check" page for issue #28 (pure Python + ffmpeg, no models).
usage: python3 tools/audio/word_check_page.py [--lab audio-work/wordlab] [--out audio-work/wordcheck]
Reads <lab>/winners.json (written by word_metrics.py --report): one card per word per voice with the winning spelling, plus the NEXT-ranked
candidate rendered to <word>-<voice>-next.mp3 (not linked from the page: it is the quick answer when a word is marked Not OK).
Writes mp3 (64 kbps mono) and a self-contained index.html (relative mp3 paths) into <out>; nothing goes into desertranger/audio."""
import argparse, html, json, os, re, subprocess

VOICE_LABEL = {"senior_ranger": "Senior Ranger", "ranger_273": "Ranger 273"}
TARGET_TEXT = {"Burro": "Burro Bend"}

def mp3(src, dst):
    af = "silenceremove=start_periods=1:start_threshold=-45dB:stop_periods=1:stop_threshold=-45dB:stop_duration=0.3,loudnorm=I=-18:TP=-2:LRA=7"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", af, "-ac", "1", "-ar", "24000", "-b:a", "64k", dst], check=True)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--lab", default="audio-work/wordlab"); ap.add_argument("--out", default="audio-work/wordcheck"); a = ap.parse_args()
    W = json.load(open(f"{a.lab}/winners.json")); man = [json.loads(x) for x in open(f"{a.lab}/manifest.jsonl")]
    os.makedirs(a.out, exist_ok=True); cards = []
    for k, x in W.items():
        base = f"{re.sub(r'[^a-z0-9]', '', x['word'].lower())}-{x['voice'].replace('_', '')}"
        mp3(f"{a.lab}/takes/{x['file']}", f"{a.out}/{base}.mp3")
        if x.get("next"): mp3(f"{a.lab}/takes/{x['next']['file']}", f"{a.out}/{base}-next.mp3")
        clip = next(m for m in man if m["file"] == x["file"])
        cards.append(dict(word=TARGET_TEXT.get(x["word"], x["word"]), key=x["word"], voice=x["voice"], voice_label=VOICE_LABEL[x["voice"]], spelling=x["spelling"], mp3=f"{base}.mp3",
                          clip_text=clip["real_text"], next_spelling=(x["next"] or {}).get("spelling"), no_passing=x["no_passing"]))
    json.dump(cards, open(f"{a.out}/cards.json", "w"), indent=1)
    open(f"{a.out}/index.html", "w").write(PAGE.replace("__CARDS__", json.dumps(cards)))
    print(len(cards), "cards;", len(os.listdir(a.out)), "files in", a.out)

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Desert Ranger word check</title>
<style>
:root{--bg:#f6f1e7;--card:#fffdf8;--ink:#2b2418;--mute:#6b6252;--line:#d9cfba;--ok:#1f7a3d;--okbg:#e3f3e8;--bad:#b3261e;--badbg:#fbe7e5;--play:#2b2418;--playink:#fffdf8}
@media (prefers-color-scheme:dark){:root{--bg:#1b1812;--card:#26221a;--ink:#f1ead9;--mute:#b4aa94;--line:#41392a;--ok:#6fd08c;--okbg:#17301f;--bad:#ff8a80;--badbg:#3a1c19;--play:#f1ead9;--playink:#1b1812}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.4 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding:16px;max-width:640px;margin-inline:auto}
h1{font-size:22px;margin:4px 0 6px}
p.lead{color:var(--mute);margin:0 0 14px}
#bar{position:sticky;top:0;background:var(--bg);padding:8px 0;border-bottom:1px solid var(--line);margin-bottom:12px;z-index:2;display:flex;justify-content:space-between;align-items:center;gap:8px}
.card{background:var(--card);border:2px solid var(--line);border-radius:16px;padding:14px;margin:0 0 14px}
.card.ok{border-color:var(--ok);background:var(--okbg)}.card.not_ok{border-color:var(--bad);background:var(--badbg)}
.word{font-size:26px;font-weight:700}.voice{font-size:14px;color:var(--mute);text-transform:uppercase;letter-spacing:.06em}
.sp{font-size:15px;color:var(--mute);margin:2px 0 10px}.sp b{color:var(--ink)}
button{font:inherit;border:0;border-radius:14px;cursor:pointer;touch-action:manipulation}
.play{display:block;width:100%;min-height:64px;font-size:22px;font-weight:700;background:var(--play);color:var(--playink);margin-bottom:10px}
.play.on{outline:4px solid var(--ok)}
.row{display:flex;gap:10px}.row button{flex:1;min-height:60px;font-size:20px;font-weight:700;border:3px solid var(--line);background:var(--card);color:var(--ink)}
.row .yes.sel{background:var(--ok);border-color:var(--ok);color:#fff}.row .no.sel{background:var(--bad);border-color:var(--bad);color:#fff}
.tools{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0 8px}.tools button{min-height:54px;padding:0 18px;font-size:18px;font-weight:700;background:var(--play);color:var(--playink)}
textarea{width:100%;min-height:150px;font:13px/1.35 ui-monospace,Menlo,monospace;background:var(--card);color:var(--ink);border:2px solid var(--line);border-radius:12px;padding:10px}
#stop{min-height:40px;font-size:15px;padding:0 14px;border-radius:10px;background:var(--play);color:var(--playink)}
.note{font-size:13px;color:var(--mute)}.warn{color:var(--bad);font-size:13px;margin-top:6px}
</style></head><body>
<h1>Word check</h1>
<p class="lead">Tap <b>Play</b>. Does the voice say the word the way a person would? Tap <b>OK</b> or <b>Not OK</b>. Only the word matters, not the voice or the radio sound. Your answers are saved on this device as you go.</p>
<div id="bar"><span id="count">0 of 0 answered</span><button id="stop">Stop sound</button></div>
<div id="cards"></div>
<div class="tools"><button id="copy">Copy my results</button><button id="dl">Download word-verdicts.json</button></div>
<p class="note" id="msg">When you are done, tap <b>Copy my results</b> and paste the text back to Claude. If copying is blocked, select the box below and copy it by hand.</p>
<textarea id="out" readonly aria-label="Your results as JSON"></textarea>
<script>
const CARDS = __CARDS__;
const KEY = "desertranger-wordcheck-v1";
let V = {};
try { V = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) { V = {}; }
function save(){ try { localStorage.setItem(KEY, JSON.stringify(V)); } catch (e) {} }
const id = c => c.key + "|" + c.voice;
const cur = new Audio(); let curBtn = null;
cur.addEventListener("ended", () => { if (curBtn) { curBtn.classList.remove("on"); curBtn.textContent = "▶ Play"; } });
function results(){ return CARDS.filter(c => V[id(c)]).map(c => ({word: c.word, voice: c.voice, spelling: c.spelling, verdict: V[id(c)]})); }
function refresh(){
  CARDS.forEach(c => { const el = document.getElementById("c-" + id(c).replace(/\W/g, "_")); el.className = "card" + (V[id(c)] ? " " + V[id(c)] : "");
    el.querySelector(".yes").classList.toggle("sel", V[id(c)] === "ok"); el.querySelector(".no").classList.toggle("sel", V[id(c)] === "not_ok"); });
  const r = results(); document.getElementById("count").textContent = r.length + " of " + CARDS.length + " answered";
  document.getElementById("out").value = JSON.stringify(r, null, 1);
}
CARDS.forEach(c => {
  const d = document.createElement("div"); d.className = "card"; d.id = "c-" + id(c).replace(/\W/g, "_");
  const esc = s => String(s).replace(/[&<>"]/g, m => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[m]));
  d.innerHTML = '<div class="voice">' + esc(c.voice_label) + '</div><div class="word">' + esc(c.word) + '</div>' +
    '<div class="sp">clip: “' + esc(c.clip_text) + '” &middot; heard as written spelling: <b>' + esc(c.spelling) + '</b></div>' +
    '<button class="play">▶ Play</button><div class="row"><button class="yes">OK</button><button class="no">Not OK</button></div>' +
    (c.no_passing ? '<div class="warn">The automatic checks found no clean take for this one; your ear decides.</div>' : '');
  const pb = d.querySelector(".play");
  pb.onclick = () => { if (curBtn === pb && !cur.paused) { cur.pause(); pb.classList.remove("on"); pb.textContent = "▶ Play"; return; }
    if (curBtn) { curBtn.classList.remove("on"); curBtn.textContent = "▶ Play"; }
    cur.src = c.mp3; cur.currentTime = 0; cur.play(); curBtn = pb; pb.classList.add("on"); pb.textContent = "■ Playing"; };
  d.querySelector(".yes").onclick = () => { V[id(c)] = "ok"; save(); refresh(); };
  d.querySelector(".no").onclick = () => { V[id(c)] = "not_ok"; save(); refresh(); };
  document.getElementById("cards").appendChild(d);
});
document.getElementById("stop").onclick = () => { cur.pause(); if (curBtn) { curBtn.classList.remove("on"); curBtn.textContent = "▶ Play"; } };
document.getElementById("copy").onclick = async () => {
  const t = JSON.stringify(results(), null, 1), ta = document.getElementById("out"), m = document.getElementById("msg");
  try { await navigator.clipboard.writeText(t); m.innerHTML = "<b>Copied.</b> Paste it back to Claude."; }
  catch (e) { ta.focus(); ta.select(); try { document.execCommand("copy"); m.innerHTML = "<b>Copied.</b> Paste it back to Claude."; } catch (e2) { m.textContent = "Copy was blocked: press and hold in the box below, Select All, Copy."; } }
};
document.getElementById("dl").onclick = () => {
  const b = new Blob([JSON.stringify(results(), null, 1)], {type: "application/json"}), a = document.createElement("a");
  a.href = URL.createObjectURL(b); a.download = "word-verdicts.json"; document.body.appendChild(a); a.click(); a.remove();
};
refresh();
</script></body></html>
"""
if __name__ == "__main__": main()
