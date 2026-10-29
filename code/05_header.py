"""Step 5. Render header.png (1200x630 social card) with Playwright Chromium.

The map shows notable births with the Welsh patronymic surnames: born in the 1800s (blue) and since 1950 (terracotta).
Fonts: FONT_DIR holding FrauncesVar.ttf, SourceSerif4-Regular.ttf, IBMPlexMono-Regular.ttf, IBMPlexMono-Medium.ttf
(from github.com/google/fonts); otherwise system serif is used.
Run: FONT_DIR=/path/to/fonts python3 code/05_header.py
"""
import json, math, os, sys
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

R = json.load(open(os.path.join(DATA, "results.json")))
PL = json.load(open(os.path.join(DATA, "page", "places.json"))); SN = json.load(open(os.path.join(DATA, "page", "surnames.json")))
OL = json.load(open(os.path.join(DATA, "page", "outline.json")))
FD = os.environ.get("FONT_DIR", "")
K = math.cos(math.radians(54.5))
X0, X1, Y0, Y1 = -7.7 * K, 1.9 * K, -58.75, -49.85
Hh = 610; Ww = Hh * (X1 - X0) / (Y1 - Y0)
pr = lambda lat, lon: ((lon * K - X0) / (Y1 - Y0) * Hh, (-lat - Y0) / (Y1 - Y0) * Hh)
land = ""
g = OL["land"]
for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
    ring = poly[0]
    if len(ring) < 12: continue
    land += "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in (pr(q[1], q[0]) for q in ring)) + "Z"
idx = {s: i for i, s in enumerate(SN["s"])}
cnt = {}
for s in R["welsh"]["names"]:
    if s not in idx: continue
    f = SN["p"][idx[s]]
    for k in range(0, len(f), 3):
        if f[k + 1] in (1, 3): cnt[(f[k], f[k + 1])] = cnt.get((f[k], f[k + 1]), 0) + f[k + 2]
dots = ""
for e, col in ((3, "#C4513A"), (1, "#2C5A8C")):
    for (p, ee), n in sorted(cnt.items(), key=lambda kv: -kv[1]):
        if ee != e: continue
        x, y = pr(PL["la"][p] / 1e4, PL["lo"][p] / 1e4); r = 2.2 + math.sqrt(n) * 1.9
        dots += f'<circle cx="{x + (-1.5 if e == 1 else 1.5):.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{col}" fill-opacity=".55" stroke="#F6F2EA" stroke-width=".6"/>'
ff = ""
if FD:
    ff = "".join(f"@font-face{{font-family:'{n}';src:url('file://{FD}/{f}');font-weight:{w};}}" for n, f, w in [
        ("Fraunces", "FrauncesVar.ttf", "100 900"), ("Source Serif 4", "SourceSerif4-Regular.ttf", "400"),
        ("IBM Plex Mono", "IBMPlexMono-Regular.ttf", "400"), ("IBM Plex Mono", "IBMPlexMono-Medium.ttf", "500")])
W = R["welsh"]["eras"]
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{ff}
body{{margin:0;width:1200px;height:630px;background:radial-gradient(circle at 80% 45%,#FFFDF7 0%,#F6F2EA 50%,#E9E2D3 100%);color:#1C1B19;overflow:hidden;position:relative;font-family:'Source Serif 4',Georgia,serif}}
.k{{position:absolute;left:70px;top:58px;font:500 15px/1 'IBM Plex Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:#5F5A52;display:flex;gap:12px;align-items:center}}
.k b{{background:#1C1B19;color:#fff;padding:7px 9px;font-weight:500}}
h1{{position:absolute;left:64px;top:94px;margin:0;font:900 84px/.94 Fraunces,Georgia,serif;letter-spacing:-.02em;width:760px}}
h1 em{{font-style:normal;color:#C4513A}}
p{{position:absolute;left:70px;top:300px;width:600px;margin:0;font-size:25px;line-height:1.36}}
p b{{color:#2C5A8C}} p i{{font-style:normal;color:#C4513A;font-weight:600}}
.f{{position:absolute;left:70px;bottom:38px;font:400 14px/1 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:#5F5A52}}
svg{{position:absolute;right:24px;top:10px}}
.lg{{position:absolute;right:30px;top:24px;font:500 13px/1.5 'IBM Plex Mono',monospace;color:#1C1B19;text-align:right}}
.lg span{{display:inline-block;width:11px;height:11px;border-radius:50%;margin:0 6px 0 14px;vertical-align:-1px}}
</style></head><body>
<div class="k"><b>Data study</b><span>Surnames · Great Britain</span></div>
<h1>Has your surname left <em>home?</em></h1>
<p>Where notable people with each surname were born, 1800s against since 1950. Of notable Joneses, Davieses, Evanses and other Welsh patronymic names, <b>{round(W['1800s']['share_wales'] * 100)}%</b> born in the 1800s were born in Wales; since 1950, <i>{round(W['since1950']['share_wales'] * 100)}%</i>.</p>
<div class="f">Dr Tristan Hotham · Independent researcher</div>
<svg width="{Ww:.0f}" height="{Hh}" viewBox="0 0 {Ww:.0f} {Hh}"><path d="{land}" fill="#E4DCCB" stroke="#C9BFAC" stroke-width="1"/>{dots}</svg>
<div class="lg">Welsh patronymic surnames<span style="background:#2C5A8C"></span>born 1800s<span style="background:#C4513A"></span>since 1950</div>
</body></html>"""
tmp = os.path.join(WORK, "header.html"); open(tmp, "w").write(html)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.goto("file://" + os.path.abspath(tmp)); pg.wait_for_timeout(600)
    pg.screenshot(path=os.path.join(ROOT, "header.png")); b.close()
os.remove(tmp)
print("header.png written")
