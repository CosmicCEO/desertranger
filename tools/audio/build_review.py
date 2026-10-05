#!/usr/bin/env python3
"""Generate desertranger/audio/review.html: one page listing every shipped clip with a play button,
script text, what Whisper heard, QA status, length, loudness and size, plus stitched radio-call demos.
Open: http://localhost:8888/desertranger/audio/review.html"""
import json, os, html, re, glob
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
            ("Phase 4: Dispatch / R55 / 273 chatter", lambda c, l: c.get("kind") == "chatter"),
            ("Wave 2: cue clips (nudge)", lambda c, l: c.get("kind") == "cue")]
tot = sum(c["bytes"] for c in man.values())
PRON = L.get("pronunciations", {})
W2 = [l for l in L["lines"] if "wave2" in l]                      # clips re-recorded or added in Wave 2 (see "wave2" in audio-lines.json)
W2IDS = {l["id"] for l in W2}
# landing calls after a chain square play the quote, then the FINAL square's place name (pl-* clip): quote square -> final square
CHAIN = {1: 20, 3: 21, 9: 8, 16: 10, 22: 32, 23: 13, 27: 17, 28: 33, 35: 39, 40: 34, 41: 12, 48: 39}
def spoken(l):                                                    # the TTS text exactly as gen_lines.py sends it (shared table applied)
    t = l.get("tts_text", l["text"])
    for k, v in PRON.items(): t = re.sub(r"\b" + k + r"\b", v if re.search(r"[a-z]", v) else "-".join(p.capitalize() for p in v.split("-")), t, flags=re.I)   # same as gen_lines.speak()
    return t
def qa_info(cid):
    f = f"audio-work/qa/{cid}.json"
    if not os.path.exists(f): return ""
    q = json.load(open(f)); m = re.search(r"s(\d+)", os.path.basename(q["pick"])); n = int(m.group(1)) if m else 0
    rung = "pass 1 (seeds 1-3)" if n <= 3 else "rung 1 (seeds 4-6)" if n <= 6 else "rung 2 (seeds 7-9, faster pacing)"
    return f"{q['status']}, take {os.path.basename(q['pick'])[:-4]}, {rung}, {len(q['takes'])} takes, {min(t['errors'] for t in q['takes'] if t['file'] == q['pick'])} word errors"
def play_id(cid, label="&#9654;"):
    return f"<button onclick=\"playId('{cid}')\">{label}</button>"
def place_cell(sq):
    if sq == 44: return "depends on the roll (back 5 &rarr; 39, back 3 &rarr; 41 &rarr; 12): see those place clips"
    if sq not in CHAIN: return ""
    f = CHAIN[sq]; cells = []
    for v in ("sr", "r273"):
        pid = f"pl-{v}-{f:02d}"
        if pid in man: cells.append(f"{play_id(pid)} {pid} ({man[pid]['sec']} s)")
    return f"then square {f}: " + " &middot; ".join(cells)
h = [f"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><link rel=icon href="data:,">
<title>Desert Ranger audio review</title><style>
body{{font:15px/1.4 system-ui;margin:16px;background:#faf6ef;color:#2b2118}} table{{border-collapse:collapse;width:100%;margin-bottom:24px}}
.wrap{{overflow-x:auto}} .badge{{background:#c4581f;color:#fff;border-radius:4px;padding:0 5px;font-size:11px;font-weight:600;margin-left:4px;white-space:nowrap}}
.box{{background:#fff;border:1px solid #d8c7ad;border-radius:6px;padding:8px 12px;margin:12px 0}} .over{{color:#b00020;font-weight:600}} .w2 td{{background:#fff7e8}} td:target{{outline:2px solid #c4581f}} tr:target td{{outline:2px solid #c4581f}}
td,th{{border-bottom:1px solid #ddd;padding:4px 6px;text-align:left;vertical-align:top}} th{{background:#eadcc8;position:sticky;top:0}}
.FAIL{{background:#ffd9d0}} .pass{{}} button{{font-size:15px}} textarea{{width:100%;height:2.2em}} .small{{color:#776;font-size:12px}}
</style><h1>Desert Ranger audio review</h1>
<p>{len(man)} clips, {tot/1024:.0f} KB total ({tot/1048576:.2f} MB). Rows in red failed the Whisper word-check after all retakes. Notes save in this browser;
<button onclick="exportNotes()">Export notes (JSON)</button> <button onclick="playAll(this)">Play section-by-section</button></p>
"""]
# ---- Wave 2: what changed ----
GROUPS = [("Call sign R273 (was 273 / Ranger 1)", lambda l: l["wave2"]["change"].startswith("call sign R273")),
          ("R55 drawn out (Rrrrrrr, fiiive, fiiive)", lambda l: l["wave2"]["change"].startswith("R55")),
          ("Spanish words (shared respelling table)", lambda l: l["wave2"]["change"].startswith("Spanish")),
          ("New: Knock, knock nudge", lambda l: l["wave2"]["change"].startswith("new clip"))]
if W2:
    h.append(f"<h2 id=wave2>Changed in Wave 2 ({len(W2)} clips)</h2><div class=box><b>Listen to these.</b> Nobody has heard any of them (Whisper, lengths and this page are the only checks). "
             "Priorities: the R55 drawn-out call sign, and the Spanish words (Vallecito, Cholla, Ocotillo, Olla, Yaqui).<br>")
    for title, f in GROUPS:
        ls = [l for l in W2 if f(l)]
        if ls: h.append(f"<b>{html.escape(title)}:</b> " + " ".join(f"<a href='#c-{l['id']}'>{l['id']}</a>" for l in ls) + "<br>")
    h.append("</div><div class=wrap><table><tr><th>play</th><th>id</th><th>old text &rarr; new text</th><th>spoken (TTS input)</th><th>QA</th><th>length vs cap</th><th>Whisper heard</th></tr>")
    for title, f in GROUPS:
        ls = [l for l in W2 if f(l)]
        if not ls: continue
        h.append(f"<tr><th colspan=7>{html.escape(title)}</th></tr>")
        for l in ls:
            cid = l["id"]; c = man.get(cid); w = l["wave2"]
            if not c: continue
            ot = w.get("old_text"); txt = html.escape(l["text"]) if ot is None else (html.escape(ot) + " &rarr; " + html.escape(l["text"]) if ot != l["text"] else html.escape(l["text"]) + " <span class=small>(written text unchanged)</span>")
            ots = w.get("old_tts"); sp = html.escape(spoken(l))
            if ots is not None and ots != spoken(l): sp = f"<span class=small>was: {html.escape(ots)}</span><br>" + sp
            cap = l.get("max_sec", 9); cls = " class=over" if c["sec"] > cap * 1.15 else ""
            ln_ = f"<span{cls}>{c['sec']} s</span> / cap {cap} s"
            if "old_sec" in w:
                d = c["sec"] - w["old_sec"]; big = abs(d) > 0.3 and cid[:2] in ("pl", "q0", "q1", "q2", "q3", "q4", "q5")
                ln_ += f"<br><span class=small>was {w['old_sec']} s ({d:+.2f} s)</span>" + (" <span class=over>&gt;0.3 s change</span>" if big else "")
            qs = html.escape(qa_info(cid)) or html.escape(c.get("qa", ""))
            h.append(f"<tr class='w2 {html.escape(c.get('qa', ''))}' id='c-{cid}'><td>{play_id(cid)}</td><td>{cid}<span class=badge>Wave 2</span><br><span class=small>{html.escape(c.get('character', ''))}</span></td>"
                     f"<td>{txt}</td><td>{sp}</td><td class=small>{qs}</td><td>{ln_}</td><td class=small>{html.escape(qa.get(cid, {}).get('heard', ''))}</td></tr>")
    h.append("</table></div><p class=small>Old versions for comparison are not shipped (they would add mp3s to desertranger/audio): the previous clips are in git history, e.g. <code>git show origin/main:desertranger/audio/chatter/ch01-1.mp3</code>.</p>")
h.append("<h2>Pronunciation table</h2><div class=box>Shared respellings sent to the voice model on every generation (docs/audio-lines.json, <code>pronunciations</code>); "
         "the Whisper check accepts the written word or the respelling. New in Wave 2: " + ", ".join(f"<b>{k.upper()}</b> = {html.escape(PRON[k])}" for k in ("Vallecito", "Cholla", "Ocotillo", "Olla", "Yaqui") if k in PRON) +
         ".<br><span class=small>Existing: " + ", ".join(f"{k} = {html.escape(v)}" for k, v in PRON.items() if k not in ("Vallecito", "Cholla", "Ocotillo", "Olla", "Yaqui")) + "</span></div>")
h.append("<div class=box><b>Landing calls after a chain square.</b> Squares 1, 3, 9, 16, 22, 23, 27, 28, 35, 40, 41, 44 and 48 chain to another square. "
         "The call now plays the quote and then the <b>final</b> square's place name (a pl-* clip), still within the 3.0 s cap. "
         "In the quotables table below each of those rows has a play button for the place clips (Senior Ranger and Ranger 273) that can follow it.</div>")
h.append("""<h2>Stitched landing-call demos (runtime stitching: click + opener + place + squelch over hiss)</h2><p>""")
for v in ("sr", "r273"):
    for op, sq in [(1, 39), (2, 43), (3, 12), (4, 32), (5, 18), (6, 33)]:
        h.append(f"<button onclick=\"stitch('op-{v}-{op:02d}','pl-{v}-{sq:02d}')\">{v} op{op} + sq{sq}</button> ")
h.append("</p>")
for title, f in SECTIONS:
    rows = [(cid, c) for cid, c in sorted(man.items()) if f(c, lines.get(cid))]
    if not rows: continue
    quot = rows[0][1].get("kind") == "quotable"
    h.append(f"<h2>{title} ({len(rows)})</h2><div class=wrap><table><tr><th>play</th><th>id</th><th>character</th><th>sq</th><th>script</th><th>Whisper heard</th><th>s</th><th>LUFS</th><th>KB</th>"
             + ("<th>place clip that follows (chain squares)</th>" if quot else "") + "<th>notes</th></tr>")
    for cid, c in rows:
        q = qa.get(cid, {}); st = c.get("qa", q.get("status", ""))
        h.append(f"<tr class='{html.escape(st)}' id='r-{cid}'><td><button data-src='{html.escape(c['file'])}' onclick='play(this)'>&#9654;</button></td>"
                 f"<td>{cid}{'<a class=badge href=#c-' + cid + ' style=text-decoration:none>Wave 2</a>' if cid in W2IDS else ''}</td><td>{c.get('character','')}</td><td>{'' if c.get('square') is None else c.get('square')}</td>"
                 f"<td>{html.escape(c.get('text', c.get('note','')))}</td><td class=small>{html.escape(q.get('heard',''))}</td>"
                 f"<td>{c['sec']}</td><td>{c.get('lufs','')}</td><td>{c['bytes']//1024}</td>"
                 + (f"<td class=small>{place_cell(c.get('square'))}</td>" if quot else "") + f"<td><textarea data-id='{cid}'></textarea></td></tr>")
    h.append("</table></div>")
h.append("""<script>
var M=%s, ctx, cur;
function playId(id){ if(cur){cur.pause();} cur=new Audio(M[id].file); cur.play(); }
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
