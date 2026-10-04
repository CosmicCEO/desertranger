import math, random, pathlib
random.seed(7)
OUT = pathlib.Path(__file__).parent
A = "../art"

def ellipse_pts(cx, cy, rx, ry, n=72, wob=0.0):
    pts=[]
    for i in range(n):
        t=2*math.pi*i/n
        k=1+wob*math.sin(3*t+0.7)+wob*0.5*math.sin(5*t)
        pts.append((cx+rx*k*math.cos(t), cy+ry*k*math.sin(t)))
    return pts

def path(pts): return "M"+" L".join(f"{x:.1f},{y:.1f}" for x,y in pts)+"Z"

def smooth(pts):
    # catmull-rom -> bezier closed
    n=len(pts); d=f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(n):
        p0,p1,p2,p3=pts[i-1],pts[i],pts[(i+1)%n],pts[(i+2)%n]
        c1=(p1[0]+(p2[0]-p0[0])/6,p1[1]+(p2[1]-p0[1])/6)
        c2=(p2[0]-(p3[0]-p1[0])/6,p2[1]-(p3[1]-p1[1])/6)
        d+=f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d+"Z"

def balloon(left, top, w, h, html, tail=None, rot=0, fs=19, fill="#fff", cls=""):
    """tail = (tx,ty) target in coordinates relative to balloon box top-left (unrotated)."""
    cx,cy,rx,ry=w/2,h/2,w/2-4,h/2-4
    shapes=[smooth(ellipse_pts(cx,cy,rx,ry,24,0.02))]
    if tail:
        tx,ty=tail
        a=math.atan2((ty-cy)/ry,(tx-cx)/rx)
        def on(aa,s=0.8): return (cx+rx*s*math.cos(aa), cy+ry*s*math.sin(aa))
        p1,p2=on(a-0.32),on(a+0.12)
        # slightly curved tail
        mx,my=(p1[0]+tx)/2+6,(p1[1]+ty)/2
        shapes.append(f"M{p1[0]:.1f},{p1[1]:.1f} Q{mx:.1f},{my:.1f} {tx:.1f},{ty:.1f} L{p2[0]:.1f},{p2[1]:.1f}Z")
    strokes="".join(f'<path d="{s}" fill="none" stroke="#1d1712" stroke-width="7" stroke-linejoin="round"/>' for s in shapes)
    fills="".join(f'<path d="{s}" fill="{fill}"/>' for s in shapes)
    return f'''<div class="bal {cls}" style="left:{left}px;top:{top}px;width:{w}px;height:{h}px;transform:rotate({rot}deg)">
<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">{strokes}{fills}</svg>
<div class="baltxt" style="font-size:{fs}px">{html}</div></div>'''

def starburst(left, top, w, h, html, rot=0, fs=22):
    cx,cy=w/2,h/2; pts=[]; n=26
    for i in range(n):
        t=2*math.pi*i/n
        r=1.0 if i%2==0 else 0.70
        r*=random.uniform(0.9,1.0) if i%2==0 else random.uniform(0.95,1.05)
        pts.append((cx+(w/2-5)*r*math.cos(t), cy+(h/2-5)*r*math.sin(t)))
    d=path(pts)
    return f'''<div class="bal" style="left:{left}px;top:{top}px;width:{w}px;height:{h}px;transform:rotate({rot}deg)">
<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}"><path d="{d}" fill="#C3623B" transform="translate(5,6)"/><path d="{d}" fill="#F2B640" stroke="#1d1712" stroke-width="3.5" stroke-linejoin="round"/></svg>
<div class="baltxt burst" style="font-size:{fs}px">{html}</div></div>'''

def droopy(left, top, w, h, html, rot=0, fs=20):
    cx,cy=w/2,h*0.42; rx,ry=w/2-6,h*0.36; pts=[]; n=90
    for i in range(n):
        t=2*math.pi*i/n
        x=cx+rx*math.cos(t); y=cy+ry*math.sin(t)
        if math.sin(t)>0:
            # drips on bottom
            u=(math.cos(t)+1)/2  # 0..1 across
            drip=max(0,math.sin(u*math.pi*3.0+0.5))**4
            y+= drip*h*0.30*math.sin(t) + 0.06*h*math.sin(t)
        pts.append((x,y))
    d=smooth(pts)
    return f'''<div class="bal" style="left:{left}px;top:{top}px;width:{w}px;height:{h}px;transform:rotate({rot}deg)">
<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}"><path d="{d}" fill="#D6E3E6" stroke="#1d1712" stroke-width="3.5" stroke-linejoin="round"/></svg>
<div class="baltxt droop" style="font-size:{fs}px;height:{h*0.84:.0f}px">{html}</div></div>'''

rigs=[("bronco-orange","Marigold"),("scout-butter","Butter Scout"),("jeep-red","Red Rocket"),("ranger-green","Ranger Green"),
      ("buggy-blue","Blue Buggy"),("rail-purple","Purple Rail"),("cruiser-teal","Teal Cruiser"),("blazer-twotone","Two-Tone")]
rig_html="".join(f'<div class="rig"><img src="{A}/pieces/{s}.png"><span>{n}</span></div>' for s,n in rigs)

# balloon stage is 744 wide; each rig slot = 93px, rig image top at stage y=STAGE_H
SL=744/8
def slot_x(i): return SL*i+SL/2
VT=150  # vehicle top in stage coords
def sag(word, start=0, step=2.2, rot=4):
    out=""
    for i,c in enumerate(word):
        k=start+i
        out+=f'<span style="transform:translateY({k*step:.1f}px) rotate({rot+k*1.5:.0f}deg)">{c if c!=" " else "&nbsp;"}</span>'
    return out
droop_txt = sag("Awww...",0,3.2,4) + "<br>" + sag("Oh no!",1,3.0,4)
stage = "".join([
    starburst(4, 2, 178, 128, "YEAH!<br>WOOT!<br>HUZZAH!", rot=-6, fs=22),
    balloon(186, 14, 172, 82, "Backed into<br>a cactus!", tail=(slot_x(3)-186-4, VT+8-14), rot=-3, fs=21),
    droopy(372, 8, 168, 104, droop_txt, rot=2, fs=23),
    balloon(552, 6, 190, 92, "Truck broke down.<br>Have to tow it.", tail=(slot_x(7)-552+6, VT+10-6), rot=3, fs=19),
])
labels = f'''
<div class="who" style="left:40px;top:128px">the cheering crowd</div>
<div class="who" style="left:200px;top:100px">nerdy ranger</div>
<div class="who" style="left:398px;top:116px">the sympathy crowd</div>
<div class="who" style="left:556px;top:102px">tow truck guy</div>'''

hr = balloon(0, 0, 170, 58, "Grievance upheld.", tail=(-24, 44), rot=-3, fs=21)

page2 = f'''<section class="sheet">
<div class="paper"></div>
<svg class="grain" width="816" height="1056"><rect width="100%" height="100%" filter="url(#noise)"/></svg>
<div class="frame"></div><div class="frame2"></div>
<div class="page">
  <div class="kicker">STATUS REPORT · OCT 4, 2026</div>
  <h1>WAVE 1<br>COMPLETE</h1>
  <div class="sub">Wave 1 (Milestone 1) is built, live on the client's own hosting, and play-tested on the web.</div>
  {starburst(468, -6, 268, 196, "WAVE 1<br>LIVE!", rot=4, fs=29)}
  <div class="tech p2plan"><div class="bg"></div>
    <h3>THE PLAN · WHERE WE ARE</h3>
    <div class="miles"><div class="track"></div><div class="mrow">
      <div class="m done"><div class="dot"><svg width="22" height="22" viewBox="0 0 22 22"><path d="M4 11.5 L9 16.5 L18 5.5" fill="none" stroke="#fff" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/></svg></div><div class="t">Playable prototype</div><div class="t2">live now!</div></div>
      <div class="m"><div class="dot">2</div><div class="t">Accounts &amp; saved games</div><div class="t2">up next</div></div>
      <div class="m"><div class="dot">3</div><div class="t">Synchronized sound &amp; voices</div><div class="t2">first pass is in!</div></div>
      <div class="m"><div class="dot">4</div><div class="t">Launch!</div></div>
    </div></div>
  </div>
  <div class="p2cols">
    <div class="card done"><div class="bg"></div>
      <h2><img src="{A}/icons/dice-color.png">Delivered in Wave 1</h2>
      <ul>
        <li><b>2 to 8 phones, one game.</b> Open a link, pick a rig, join with a 4-letter room code.</li>
        <li><b>All 52 squares and the rules</b> of the hand-drawn board: shortcuts, swaps, roll again, lose a turn.</li>
        <li><b>Your seat is remembered.</b> Reload or reopen the link and you are back in the race.</li>
        <li><b>Big-screen board view</b> for a TV or tablet, and a <b>solo demo</b> with computer rivals.</li>
        <li><b>Live on the client's own hosting:</b> plain Apache / MySQL / PHP, over HTTPS.</li>
      </ul>
    </div>
    <div class="card chg"><div class="bg"></div>
      <h2><img src="{A}/icons/star-color.png">What changed since the concept sheet</h2>
      <ul>
        <li><b>Sound and voices arrived early:</b> 233 clips in all, with ten character voices, 54 lines on 27 squares and 104 radio place-name calls.</li>
        <li><b>Same moment on every phone:</b> dice, radio calls and the crowd are timed to the server clock, and the moves start together.</li>
        <li><b>Desert atmosphere:</b> wind, crickets, a coyote, a hawk, a rare rattlesnake, and 12 radio chatter conversations. It plays in the lobby too.</li>
        <li><b>Live and tunable:</b> solo demo, two volume sliders, radio chatter on or off, a Test sound button.</li>
      </ul>
    </div>
    <div class="card chk"><div class="bg"></div>
      <h2><img src="{A}/icons/signpost-color.png">How we checked it</h2>
      <ul>
        <li><b>45 rule checks</b>, plus full 4- and 8-player games played through the live server.</li>
        <li><b>Automated browser tests</b> with several phones and a board screen, plus 29 checks of the live site: same timing everywhere, no errors.</li>
        <li><b>Played on the live site</b> on phones and the shared screen (after a real iPhone trial over Wi-Fi). Sync is tight, with barely any offset.</li>
        <li><b>Every voice clip</b> was checked by speech recognition for the right words.</li>
      </ul>
      <div class="p2note">Not confirmed yet: Android phones, and Safari on a computer.</div>
    </div>
    <div class="card nxt"><div class="bg"></div>
      <h2><img src="{A}/icons/olla-color.png">What's next</h2>
      <ul>
        <li><b>Wave 2, sound:</b> iPhone sound that starts sooner and stays on, radio reports of the final square after a move, the spoken name "R273", Spanish place words.</li>
        <li><b>Wave 2, screens:</b> ambient sound on the homepage, an About page, game counts, a way back from the lobby, bigger rigs on a PC.</li>
        <li><b>To decide:</b> how a won game ends (rematch, winner as monitor), a buzzer nudge, and a self-contained app.</li>
        <li><b>Then:</b> Milestone 2, accounts and saved games, and launch.</li>
      </ul>
    </div>
  </div>
  <div class="footer">Invented by Jeffery Price, R273. &nbsp;·&nbsp; © 2026 Jerod Price. All rights reserved. Status as of Oct 4, 2026.</div>
</div>
</section>'''

html=f'''<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:Bungee;src:url(fonts/Bungee-Regular.ttf)}}
@font-face{{font-family:BungeeShade;src:url(fonts/BungeeShade-Regular.ttf)}}
@font-face{{font-family:Nunito;src:url(fonts/Nunito.ttf);font-weight:200 1000}}
@font-face{{font-family:Caveat;src:url(fonts/Caveat.ttf);font-weight:400 700}}
@font-face{{font-family:Bangers;src:url(fonts/Bangers-Regular.ttf)}}
@page{{size:8.5in 11in;margin:0}}
:root{{--cream:#F4ECD8;--ink:#3A2A1E;--terra:#C3623B;--mari:#E9A23B;--sage:#7E9168;--sagel:#C9D3B4;--sand:#E8D7B4}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:816px}}
body{{background:var(--cream);font-family:Nunito,sans-serif;color:var(--ink);-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.paper{{position:absolute;inset:0;background:
 radial-gradient(ellipse at 15% 10%,rgba(255,250,235,.7),transparent 55%),
 radial-gradient(ellipse at 90% 95%,rgba(214,186,140,.35),transparent 60%);}}
.grain{{position:absolute;inset:0;opacity:.18;mix-blend-mode:multiply}}
.frame{{position:absolute;inset:14px;border:2.5px solid var(--ink);border-radius:14px;filter:url(#rough)}}
.frame2{{position:absolute;inset:20px;border:1.2px solid var(--terra);border-radius:10px;filter:url(#rough)}}
.page{{position:absolute;inset:36px;}}
/* header */
.kicker{{font-family:Bungee;font-size:11px;letter-spacing:3px;color:var(--sage)}}
h1{{font-family:Bungee;font-size:56px;line-height:.9;color:var(--terra);text-shadow:3px 3px 0 var(--mari),5.5px 5.5px 0 var(--ink);letter-spacing:1px;margin-top:6px}}
.sub{{font-family:Nunito;font-weight:800;font-size:16.5px;line-height:1.25;margin-top:13px;color:var(--ink);max-width:330px}}
.intro{{position:absolute;top:214px;left:0;right:0;font-size:12.6px;line-height:1.5}}
.intro b{{color:var(--terra)}}
.intro i{{font-family:Caveat;font-style:normal;font-weight:700;font-size:16px;color:#6d4a2f}}
.photo{{position:absolute;right:4px;top:6px;width:212px;transform:rotate(2.5deg);background:#fffaf0;padding:9px 9px 34px;box-shadow:2px 4px 10px rgba(60,40,20,.28);}}
.photo img{{width:100%;display:block;border-radius:3px}}
.photo{{padding:8px 8px 30px}}
.photo .cap{{position:absolute;bottom:5px;left:0;right:0;text-align:center;font-family:Caveat;font-weight:700;font-size:15px;color:#5a3d26}}
.tape{{position:absolute;width:64px;height:20px;background:rgba(233,162,59,.55);top:-10px;left:74px;transform:rotate(-4deg)}}
.sun{{position:absolute;right:250px;top:-14px;width:70px;height:70px}}
.r1{{position:absolute;left:340px;top:0;width:184px;text-align:center}}
.r1 .lbl{{font-family:Bungee;font-size:11px;letter-spacing:1px;color:var(--terra)}}
.r1 .pola{{position:relative;width:118px;margin:7px auto 0;background:#fffaf0;padding:6px 6px 8px;transform:rotate(-3deg);box-shadow:2px 3px 8px rgba(60,40,20,.28)}}
.r1 .pola img{{width:106px;height:106px;display:block;object-fit:cover}}
.r1 .tape2{{position:absolute;width:46px;height:16px;background:rgba(126,145,104,.5);top:-8px;left:36px;transform:rotate(5deg)}}
.r1 .badge{{position:absolute;right:-18px;bottom:-10px;width:54px;height:30px;border-radius:15px;background:var(--mari);border:2px solid var(--ink);font-family:Bungee;font-size:14px;line-height:26px;color:var(--ink);transform:rotate(8deg)}}
.r1 .rcap{{font-size:10.6px;line-height:1.35;margin-top:12px;color:var(--ink)}}
.r1 .rcap b{{font-weight:800}}
/* columns */
.cols{{position:absolute;top:284px;left:0;right:0;display:grid;grid-template-columns:1fr 1fr;gap:22px}}
.card{{position:relative;padding:16px 16px 12px 18px;border-radius:12px;height:258px}}
.card .bg{{position:absolute;inset:0;border:2px solid var(--ink);border-radius:12px;filter:url(#rough)}}
.card.plays .bg{{background:rgba(201,211,180,.45)}}
.card.special .bg{{background:rgba(233,162,59,.16)}}
h2{{font-family:Bungee;font-size:17px;letter-spacing:.5px;color:var(--ink);display:flex;align-items:center;gap:8px;position:relative}}
h2 img{{height:30px}}
ul{{list-style:none;margin-top:9px;position:relative}}
li{{font-size:12.4px;line-height:1.38;padding-left:22px;position:relative;margin-bottom:7px}}
li::before{{content:"";position:absolute;left:2px;top:4px;width:11px;height:11px;border-radius:50%;background:var(--terra);box-shadow:inset -2px -2px 0 rgba(0,0,0,.18)}}
.plays li::before{{background:var(--sage)}}
li b{{font-weight:800}}
.cicon{{position:absolute;opacity:.95}}
.special li{{margin-bottom:5px}}
/* rig stage */
.rigzone{{position:absolute;top:556px;left:0;right:0;height:262px}}
.rigtitle{{position:absolute;left:0;top:0;font-family:Bungee;font-size:15px;color:var(--terra)}}
.stage{{position:absolute;left:0;top:22px;width:744px;height:150px}}
.road{{position:absolute;left:-6px;right:-6px;top:{22+VT+48}px;height:40px;background:var(--sand);border-radius:20px;filter:url(#rough);border:2px dashed rgba(58,42,30,.35)}}
.rigs{{position:absolute;left:0;top:{22+VT}px;width:744px;display:grid;grid-template-columns:repeat(8,1fr)}}
.rig{{text-align:center}}
.rig img{{width:86px;height:60px;object-fit:contain;filter:drop-shadow(1px 2px 0 rgba(58,42,30,.25))}}
.rig span{{display:block;font-family:Bungee;font-size:9.4px;letter-spacing:.3px;margin-top:6px;color:var(--ink)}}
.bal{{position:absolute;transform-origin:50% 50%}}
.bal svg{{position:absolute;left:0;top:0;overflow:visible}}
.baltxt{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;text-align:center;font-family:Bangers;letter-spacing:.8px;line-height:1.02;color:#1d1712}}
.burst{{color:#1d1712;transform:rotate(-2deg)}}
.droop{{color:#3c5560;display:block;padding-top:24px;line-height:1.05}}
.droop span{{display:inline-block}}
.who{{position:absolute;font-family:Caveat;font-weight:700;font-size:15px;color:#6d4a2f;white-space:nowrap}}
/* bottom */
.bottom{{position:absolute;top:828px;left:0;right:0;height:132px;display:grid;grid-template-columns:1fr 1fr;gap:22px}}
.tech{{position:relative;padding:13px 16px}}
.tech .bg{{position:absolute;inset:0;border:2px solid var(--ink);border-radius:12px;background:rgba(255,250,238,.75);filter:url(#rough)}}
h3{{font-family:Bungee;font-size:13.5px;position:relative;color:var(--sage);letter-spacing:.4px}}
.tech ul{{margin-top:7px}}
.tech li{{font-size:11.6px;margin-bottom:4px}}
.tech li::before{{background:var(--mari);width:9px;height:9px;top:4px}}
.miles{{position:relative;margin-top:14px}}
.track{{position:absolute;left:18px;right:18px;top:17px;border-top:3px dashed var(--terra)}}
.mrow{{display:grid;grid-template-columns:repeat(4,1fr);position:relative}}
.m{{text-align:center}}
.m .dot{{width:36px;height:36px;margin:0 auto;border-radius:50%;background:var(--mari);border:2.5px solid var(--ink);font-family:Bungee;font-size:15px;line-height:31px;color:var(--ink)}}
.m:last-child .dot{{background:var(--terra);color:#fff}}
.m div.t{{font-size:11.2px;font-weight:800;line-height:1.2;margin-top:6px}}
.footer{{position:absolute;left:0;right:0;bottom:-8px;text-align:center;font-size:10px;color:#6d5a48;letter-spacing:.3px}}
.hrwrap{{position:relative;height:72px;margin-top:4px}}

.sheet{{position:relative;width:816px;height:1056px;overflow:hidden;break-after:page}}
.sheet:last-of-type{{break-after:auto}}
.stamp{{position:absolute;right:14px;top:-9px;transform:rotate(4deg);border:2.5px solid var(--terra);border-radius:9px;padding:3px 10px 4px;color:var(--terra);font-family:Bungee;text-align:center;line-height:1.1;background:rgba(244,236,216,.55);box-shadow:inset 0 0 0 2px rgba(195,98,59,.22);filter:url(#rough)}}
.stamp b{{display:block;font-size:11.5px;letter-spacing:.8px;font-weight:normal}}
.stamp span{{font-size:8px;letter-spacing:1.6px}}
.m.done .dot{{background:var(--sage);font-size:0}}
.m.done .dot svg{{display:block;margin:5px auto 0}}
.m .t2{{font-family:Caveat;font-weight:700;font-size:13.5px;line-height:1;color:var(--terra);margin-top:2px}}
/* page 2: status report */
.p2plan{{position:absolute;top:226px;left:0;right:0;height:132px}}
.p2cols{{position:absolute;top:374px;left:0;right:0;display:grid;grid-template-columns:1fr 1fr;gap:18px 22px}}
.p2cols .card{{height:286px;padding:15px 15px 10px 17px}}
.p2cols li{{font-size:12.3px;line-height:1.34;margin-bottom:6px}}
.card.done .bg{{background:rgba(201,211,180,.45)}}
.card.chg .bg{{background:rgba(233,162,59,.16)}}
.card.chk .bg{{background:rgba(214,227,230,.55)}}
.card.nxt .bg{{background:rgba(255,250,238,.8)}}
.card.chk li::before{{background:#5f8693}}
.card.nxt li::before{{background:var(--mari)}}
.p2note{{font-family:Caveat;font-weight:700;font-size:15px;color:#6d4a2f;position:absolute;left:19px;right:12px;bottom:9px;line-height:1.05}}
</style></head><body>
<svg width="0" height="0" style="position:absolute"><defs>
<filter id="rough"><feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="3"/><feDisplacementMap in="SourceGraphic" scale="3.2"/></filter>
<filter id="noise"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" seed="5"/><feColorMatrix values="0 0 0 0 0.45  0 0 0 0 0.35  0 0 0 0 0.2  0 0 0 1.2 -0.35"/></filter>
</defs></svg>
<section class="sheet">
<div class="paper"></div>
<svg class="grain" width="816" height="1056"><rect width="100%" height="100%" filter="url(#noise)"/></svg>
<div class="frame"></div><div class="frame2"></div>
<div class="page">
  <div class="kicker">A WEB BOARD GAME · ANZA-BORREGO</div>
  <h1>DESERT<br>RANGER</h1>
  <div class="sub">The hand-drawn family board game, now playable on any phone.</div>
  <div class="intro">An original Anza-Borrego race from <b>Start</b> to <b>Finish</b> across <b>52 real places</b>: Font's Point, Fish Creek, Hawk Canyon, Ocotillo Wells, Una Palma. Packed with ranger-life mishaps like <i>"Backing accident, lose 2 turns (ouch!)"</i> and <i>"Supervisor on vacation, move ahead 5."</i></div>
  <div class="r1"><div class="lbl">MEET R273</div>
    <div class="pola"><div class="tape2"></div><img src="img/ranger1.jpg" alt="Jeffery Price"><div class="badge">#273</div></div>
    <div class="rcap"><b>Jeffery Price</b> ·<br>R273, the inventor ·<br>Badge #273 ·<br>Anza-Borrego ranger, <span style="white-space:nowrap">1980–1982</span></div></div>
  <div class="photo"><div class="tape"></div><img src="img/board-thumb.jpg"><div class="cap">From the original hand-drawn board</div></div>

  <div class="cols">
    <div class="card plays"><div class="bg"></div>
      <h2><img src="{A}/icons/dice-color.png">How it plays</h2>
      <ul>
        <li><b>2 to 8 players</b>, each on their own phone.</li>
        <li><b>Same room or remote</b>: play together over a phone call.</li>
        <li><b>One six-sided die.</b> Roll and race, with shortcuts, swaps and lose-a-turn hazards.</li>
        <li><b>Saved games</b>: pick up right where you left off.</li>
        <li><b>Solo demo</b>: try it alone, with computer rivals.</li>
      </ul>
      <div class="stamp"><b>WAVE 1<br>COMPLETE</b><span>LIVE · OCT 4, 2026</span></div>
      <img class="cicon" src="{A}/icons/signpost-color.png" style="right:14px;bottom:12px;height:58px;transform:rotate(4deg)">
      <img class="cicon" src="{A}/icons/olla-color.png" style="right:78px;bottom:12px;height:34px">
    </div>
    <div class="card special"><div class="bg"></div>
      <h2><img src="{A}/icons/star-color.png">What makes it special</h2>
      <ul>
        <li><b>Shared moments:</b> every phone hears the same dice, radio call, cheer or "awww" at the same instant.</li>
        <li><b>Character voices on 27 squares</b>: the HR rep, tow truck guy, nerdy ranger, judge and more.</li>
        <li><b>Original artwork</b> preserved from the hand-drawn board.</li>
        <li><b>Choose your rig</b> from eight 1980s off-roaders.</li>
      </ul>
      <img class="cicon" src="{A}/icons/court-gavel-color.png" style="left:20px;bottom:10px;height:46px;transform:rotate(-4deg)">
      <div class="who" style="left:278px;bottom:22px">the HR rep</div>
      <div style="position:absolute;left:96px;bottom:10px;width:176px;height:56px">{hr}</div>
    </div>
  </div>

  <div class="rigzone">
    <div class="rigtitle">PICK YOUR RIG · HEAR IT TOGETHER</div>
    <div class="road"></div>
    <div class="stage">{stage}{labels}</div>
    <div class="rigs">{rig_html}</div>
  </div>

  <div class="bottom">
    <div class="tech"><div class="bg"></div>
      <h3>UNDER THE HOOD</h3>
      <ul>
        <li><b>Web app</b>, no download. Just open a link.</li>
        <li>Runs on the client's existing <b>Apache / MySQL / PHP</b> hosting.</li>
        <li>Simple <b>username and password</b> accounts.</li>
      </ul>
    </div>
    <div class="tech"><div class="bg"></div>
      <h3>THE PLAN · 1 OF 4 DONE</h3>
      <div class="miles"><div class="track"></div><div class="mrow">
        <div class="m done"><div class="dot"><svg width="22" height="22" viewBox="0 0 22 22"><path d="M4 11.5 L9 16.5 L18 5.5" fill="none" stroke="#fff" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/></svg></div><div class="t">Playable prototype</div><div class="t2">live now!</div></div>
        <div class="m"><div class="dot">2</div><div class="t">Accounts &amp; saved games</div><div class="t2">up next</div></div>
        <div class="m"><div class="dot">3</div><div class="t">Synchronized sound &amp; voices</div><div class="t2">first pass is in!</div></div>
        <div class="m"><div class="dot">4</div><div class="t">Launch!</div></div>
      </div></div>
    </div>
  </div>
  <div class="footer">Invented by Jeffery Price, R273. &nbsp;·&nbsp; © 2026 Jerod Price. All rights reserved. Status as of Oct 4, 2026: Wave 1 complete and live.</div>
</div>
</section>
{page2}
</body></html>'''
(OUT/"desert-ranger-pitch.html").write_text(html)
print("ok")
