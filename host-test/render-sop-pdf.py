import markdown,re,sys
fs=float(sys.argv[1]) if len(sys.argv)>1 else 10.8
md=open('/workspace/boardgame/host-test/SOP-upload-amp-test.md').read()
md=re.sub(r'_{4,}','@@BLANK@@',md)
body=markdown.markdown(md,extensions=['tables','sane_lists'])
body=body.replace('☐','<span class="cb"></span>').replace('@@BLANK@@','<span class="blank"></span>')
i=body.index('<h2>Troubleshooting')
h1end=body.index('</h1>')+5
body=body[:h1end]+'<div class="cols">'+body[h1end:i]+'</div><div class="full">'+body[i:]+'</div>'
css="""
@page{size:Letter;margin:0.32in 0.4in}
*{box-sizing:border-box}
body{font-family:'DejaVu Sans',Arial,sans-serif;font-size:FSpt;line-height:1.23;color:#1a1a1a;margin:0}
.cols{column-count:2;column-gap:18pt;column-rule:1px solid #ddd}
h1{font-size:20pt;margin:0 0 4pt;color:#7a3e00;border-bottom:4px solid #c9a96e;padding-bottom:3pt}
h2{font-size:1.22em;margin:6pt 0 3pt;background:#7a3e00;color:#fff;padding:3pt 8pt;border-radius:6px;break-after:avoid}
p{margin:3pt 0}
hr{display:none}
ol,ul{margin:3pt 0;padding-left:22pt}
li{margin:1.5pt 0;break-inside:avoid}
ol>li::marker{font-weight:bold;font-size:1.1em;color:#7a3e00}
blockquote{margin:5pt 0;padding:4pt 9pt;background:#fff3cd;border-left:6px solid #e0a800;border-radius:6px;break-inside:avoid}
blockquote p{margin:0}
table{border-collapse:collapse;width:100%;margin:4pt 0;font-size:.93em;break-inside:avoid}
th{background:#efe4cf;text-align:left}
th,td{border:1px solid #bbb;padding:3pt 5pt;vertical-align:top}
code{font-family:'DejaVu Sans Mono',monospace;background:#eee;padding:0 3px;border-radius:3px;font-size:.92em}
.cb{display:inline-block;width:1.15em;height:1.15em;border:2px solid #333;border-radius:3px;vertical-align:-.2em;margin-right:3pt;background:#fff}
.blank{display:inline-block;min-width:11em;border-bottom:1.5px solid #333;height:1em}
td .blank{min-width:9em}
.full li .blank{min-width:6em}
.full ul{columns:2;column-gap:18pt;list-style:none;padding-left:4pt}
.full{break-before:auto}
.full table{font-size:.86em}
.full th,.full td{padding:2pt 5pt}
""".replace('FS',str(fs))
open('/tmp/sop.html','w').write(f'<!doctype html><html><head><meta charset="utf-8"><title>SOP: Upload the web host test</title><style>{css}</style></head><body>{body}</body></html>')
