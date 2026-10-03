#!/usr/bin/env python3
"""Generate desertranger/audio/review.html: one page listing every shipped clip with a play button,
script text, what Whisper heard, QA status, length, loudness and size, plus stitched radio-call demos.
Open: http://localhost:8888/desertranger/audio/review.html"""
import json, os, html
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
            ("Phase 4: Dispatch / R55 / 273 chatter", lambda c, l: c.get("kind") == "chatter")]
tot = sum(c["bytes"] for c in man.values())
h = [f"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Desert Ranger audio review</title><style>
body{{font:15px/1.4 system-ui;margin:16px;background:#faf6ef;color:#2b2118}} table{{border-collapse:collapse;width:100%;margin-bottom:24px}}
td,th{{border-bottom:1px solid #ddd;padding:4px 6px;text-align:left;vertical-align:top}} th{{background:#eadcc8;position:sticky;top:0}}
.FAIL{{background:#ffd9d0}} .pass{{}} button{{font-size:15px}} textarea{{width:100%;height:2.2em}} .small{{color:#776;font-size:12px}}
</style><h1>Desert Ranger audio review</h1>
<p>{len(man)} clips, {tot/1024:.0f} KB total. Rows in red failed the Whisper word-check after all retakes. Notes save in this browser;
<button onclick="exportNotes()">Export notes (JSON)</button> <button onclick="playAll(this)">Play section-by-section</button></p>
<h2>Stitched landing-call demos (runtime stitching: click + opener + place + squelch over hiss)</h2><p>"""]
for v in ("sr", "r273"):
    for op, sq in [(1, 39), (2, 43), (3, 12), (4, 32), (5, 18), (6, 33)]:
        h.append(f"<button onclick=\"stitch('op-{v}-{op:02d}','pl-{v}-{sq:02d}')\">{v} op{op} + sq{sq}</button> ")
h.append("</p>")
for title, f in SECTIONS:
    rows = [(cid, c) for cid, c in sorted(man.items()) if f(c, lines.get(cid))]
    if not rows: continue
    h.append(f"<h2>{title} ({len(rows)})</h2><table><tr><th>play</th><th>id</th><th>character</th><th>sq</th><th>script</th><th>Whisper heard</th><th>s</th><th>LUFS</th><th>KB</th><th>notes</th></tr>")
    for cid, c in rows:
        q = qa.get(cid, {}); st = c.get("qa", q.get("status", ""))
        h.append(f"<tr class='{html.escape(st)}'><td><button data-src='{html.escape(c['file'])}' onclick='play(this)'>&#9654;</button></td>"
                 f"<td>{cid}</td><td>{c.get('character','')}</td><td>{'' if c.get('square') is None else c.get('square')}</td>"
                 f"<td>{html.escape(c.get('text', c.get('note','')))}</td><td class=small>{html.escape(q.get('heard',''))}</td>"
                 f"<td>{c['sec']}</td><td>{c.get('lufs','')}</td><td>{c['bytes']//1024}</td>"
                 f"<td><textarea data-id='{cid}'></textarea></td></tr>")
    h.append("</table>")
h.append("""<script>
var M=%s, ctx, cur;
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
