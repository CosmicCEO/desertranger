# Wave 2 pitch sheet (2 pages). Reuses the look of build.py: runs it, then borrows its <style>, SVG filters
# and helper functions (starburst, balloon, droopy) so the two sheets never drift apart.
# Output: desert-ranger-wave2.html  (render with: SHEET=wave2 node design/pitch/render.js <outBase>)
import pathlib, runpy
HERE = pathlib.Path(__file__).parent
base = runpy.run_path(str(HERE / "build.py"))
starburst, balloon, A, html = base["starburst"], base["balloon"], base["A"], base["html"]
style = html[html.index("<style>"):html.index("</style>") + len("</style>")]
defs = html[html.index('<svg width="0"'):html.index("</defs></svg>") + len("</defs></svg>")]
head = html[:html.index("<style>")]
CHECK = '<svg width="22" height="22" viewBox="0 0 22 22"><path d="M4 11.5 L9 16.5 L18 5.5" fill="none" stroke="#fff" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/></svg>'
FRAME = '''<div class="paper"></div>
<svg class="grain" width="816" height="1056"><rect width="100%" height="100%" filter="url(#noise)"/></svg>
<div class="frame"></div><div class="frame2"></div>'''
FOOT = "Invented by Jeffery Price, R273. &nbsp;·&nbsp; © 2026 Jerod Price. All rights reserved. Wave 2 plan as of Oct 5, 2026."

def miles(items):
    out = ""
    for i, (done, t, t2) in enumerate(items):
        dot = CHECK if done else str(i + 1)
        out += f'<div class="m{" done" if done else ""}"><div class="dot">{dot}</div><div class="t">{t}</div>' + (f'<div class="t2">{t2}</div>' if t2 else "") + '</div>'
    return f'<div class="miles"><div class="track"></div><div class="mrow">{out}</div></div>'

page1 = f'''<section class="sheet">
{FRAME}
<div class="page">
  <div class="kicker">NEXT UP · BUILT FROM YOUR PLAY-TEST</div>
  <h1>WAVE 2<br>PLAN</h1>
  <div class="sub">Sixteen improvements from playing Wave 1 on real phones, in four small batches. Voice changes are on hold.</div>
  {starburst(468, -6, 268, 196, "YOU PLAYED IT.<br>NOW WE<br>TUNE IT!", rot=4, fs=25)}
  <div class="tech p2plan"><div class="bg"></div>
    <h3>WHAT YOU TOLD US WORKS</h3>
    <ul class="w2ok">
      <li><b>The timing is tight</b> on the phones and on the shared screen, with barely any offset.</li>
      <li><b>The sounds land:</b> the coyote, the hawk, the wind, the dice. <b>The player pieces are excellent.</b></li>
      <li><b>The look and feel</b> on a PC screen.</li>
    </ul>
  </div>
  <div class="p2cols">
    <div class="card done"><div class="bg"></div>
      <h2><img src="{A}/icons/signpost-color.png">A &middot; Sound that just works</h2>
      <ul>
        <li><b>Starts in a second or two</b> on iPhone, not 20 seconds.</li>
        <li><b>Stays on</b> after a win, in the lobby, and when you switch away and come back, with a "tap to resume" bar if the phone pauses it.</li>
        <li><b>Desert sound on the homepage</b> too, after your first tap.</li>
        <li><b>A bit more</b> radio chatter and wildlife.</li>
      </ul>
    </div>
    <div class="card chg"><div class="bg"></div>
      <h2><img src="{A}/icons/dice-color.png">B &middot; Screens, made friendlier</h2>
      <ul>
        <li><b>Lobby:</b> a Home button, and a proper button for the shared-screen link.</li>
        <li><b>On a PC or Mac:</b> big rig pictures in a 2 &times; 4 grid.</li>
        <li><b>An About page</b> on the homepage: the game, the ranger who invented it, park details and photos.</li>
        <li><b>Little things:</b> placeholder text, and the piece-shadow check on iPhone.</li>
      </ul>
    </div>
    <div class="card chk"><div class="bg"></div>
      <h2><img src="{A}/icons/star-color.png">C &middot; Voices and radio</h2>
      <ul>
        <li><b>Say where you ended up:</b> after a funny quote on a shortcut square, the radio also names the square you land on, like "Fish Creek".</li>
        <li><b>On hold: voice changes</b> (the R273 and R55 call signs, the Spanish place words). The Wave 1 voices stay as they are until you give specific instructions.</li>
      </ul>
    </div>
    <div class="card nxt"><div class="bg"></div>
      <h2><img src="{A}/icons/olla-color.png">D &middot; New things to do</h2>
      <ul>
        <li><b>Play again:</b> when someone wins, one button takes the same room and players back to the lobby.</li>
        <li><b>Knock, knock:</b> nudge a slow player. Every phone hears it at the same moment.</li>
        <li><b>Games being played</b> counter on the homepage.</li>
        <li><b>Credits:</b> every sound source is named on the About page.</li>
        
      </ul>
    </div>
  </div>
  <div class="footer">{FOOT}</div>
</div>
</section>'''

page2 = f'''<section class="sheet">
{FRAME}
<div class="page">
  <div class="kicker">THE ROAD AHEAD</div>
  <h1>HOW WE<br>GET THERE</h1>
  <div class="sub">Small updates to your own hosting, each one checked on the live site before the next.</div>
  <div class="stamp" style="top:6px"><b>BUILT, TESTED</b><span>NOT LIVE YET</span></div>
  <div class="tech p2plan"><div class="bg"></div>
    <h3>THE ORDER · EACH BATCH IS ITS OWN UPDATE</h3>
    {miles([(True, "Wave 1", "live now!"), (False, "A &middot; Sound reliability", "first, biggest win"), (False, "B, C &middot; Screens, voices", None), (False, "D &middot; New features", None)])}
  </div>
  <div class="p2cols">
    <div class="card done"><div class="bg"></div>
      <h2><img src="{A}/icons/court-gavel-color.png">Calls already made</h2>
      <ul>
        <li><b>Play again</b> comes first. Keep-playing-for-places, with the winner watching as monitor, comes later.</li>
        <li><b>Knock, knock</b> plays on every phone at the same moment; its sound is on hold with the voices.</li>
        <li><b>Lobby Home</b> keeps your seat, so Resume brings you back.</li>
        <li><b>Homepage counter</b> shows games only, no names or room codes.</li>
        <li><b>Rig grid</b> is 2 columns by 4 rows on a computer.</li>
      </ul>
    </div>
    <div class="card chg"><div class="bg"></div>
      <h2><img src="{A}/icons/signpost-color.png">What we need from you</h2>
      <ul>
        <li><b>About page words and pictures:</b> the story of the game and the ranger, park details, photos, links, and who may be named.</li>
        <li><b>An iPhone look</b> at the piece shadow, and a note if sound is still silent (check the side switch first).</li>
        <li><b>Your instructions for the voices:</b> which clips to change and how. Wave 1 sounds are back in place until then.</li>
        <li><b>"Clear the room code":</b> tell us what you had in mind.</li>
      </ul>
    </div>
    <div class="card chk"><div class="bg"></div>
      <h2><img src="{A}/icons/dice-color.png">How we keep it safe</h2>
      <ul>
        <li><b>No database changes.</b> Your host is updated by copying files; nothing in the database changes.</li>
        <li><b>Same checks as Wave 1:</b> the rules tests, full 4- and 8-player games, and the live-site check with zero failures.</li>
        <li><b>Your phones last:</b> after every update you try it on iPhone and the shared screen.</li>
        <li><b>New sounds</b> are free to use or made for the game, and listed in the credits.</li>
      </ul>
    </div>
    <div class="card nxt"><div class="bg"></div>
      <h2><img src="{A}/icons/olla-color.png">After Wave 2</h2>
      <ul>
        <li><b>Places and winner as monitor:</b> the others keep racing for second and third.</li>
        <li><b>Self-contained app:</b> a decision still open, a Mac or iPhone app that runs the game without a server.</li>
        <li><b>Then:</b> a last sound and voice polish pass, and launch.</li>
      </ul>
      <div class="p2note">Not confirmed yet: Android phones, and Safari on a computer.</div>
    </div>
  </div>
  <div class="footer">{FOOT}</div>
</div>
</section>'''

extra = '''<style>
.w2ok{margin-top:6px}.w2ok li{font-size:12.2px;margin-bottom:3px}
.p2plan .m div.t{font-size:11px}
.p2plan{height:134px}
.p2cols{top:372px}
.p2cols .card{height:282px}
.p2cols li{font-size:13.5px;line-height:1.38;margin-bottom:8px}
.p2cols h2{font-size:16.5px}
</style>'''
out = head + style + extra.replace("<style>", "<style>", 1) + "</head><body>\n" + defs + "\n" + page1 + "\n" + page2 + "\n</body></html>"
(HERE / "desert-ranger-wave2.html").write_text(out)
print("wrote desert-ranger-wave2.html")
