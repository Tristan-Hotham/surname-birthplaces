"""Reddit collage: run from this folder (python3 collage.py). Reads ../data/results.json and ../data/page/*.json only."""
import json, os
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.collections import PolyCollection
F = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts/")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]: fm.fontManager.addfont(os.path.join(F, f))
DISP = fm.FontProperties(fname=os.path.join(F, "FrauncesVar.ttf"), weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"
BG, FG, MUT, LAND, EDGE = "#F5F0E6", "#1C1B19", "#5F5A52", "#E3DACA", "#C9BFAC"
B1, B3 = "#2C5A8C", "#C4513A"
R = json.load(open("../data/results.json")); PL = json.load(open("../data/page/places.json")); SN = json.load(open("../data/page/surnames.json"))
ol = json.load(open("../data/page/outline.json"))
K = np.cos(np.radians(54.5))
P = []
g = ol["land"]
for p in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
    a = np.array(p[0]); P.append(np.column_stack([a[:, 0] * K, a[:, 1]]))
IDX = {s: i for i, s in enumerate(SN["s"])}
def births(names, e):
    c = {}
    for s in names:
        f = SN["p"][IDX[s]]
        for k in range(0, len(f), 3):
            if f[k + 1] == e: c[f[k]] = c.get(f[k], 0) + f[k + 2]
    return c
def base(ax, box, lw=.5):
    ax.add_collection(PolyCollection(P, facecolors=LAND, edgecolors=EDGE, linewidths=lw, zorder=0))
    ax.set_xlim(box[0] * K, box[1] * K); ax.set_ylim(box[2], box[3]); ax.set_aspect("equal"); ax.axis("off")
def dots(ax, names, e, col, k=7.5, s0=6):
    c = births(names, e)
    for p, n in sorted(c.items(), key=lambda kv: -kv[1]):
        ax.scatter(PL["lo"][p] / 1e4 * K, PL["la"][p] / 1e4, s=s0 + n * k, color=col, alpha=.62, lw=.35, ec=BG, zorder=3)

W, ov, rg, PN = R["welsh"], R["overview"], R["regional"], R["placenames"]
fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
fig.text(.04, .969, "Has your surname left home?", fontproperties=DISP, fontsize=50, color=FG, va="top")
fig.text(.04, .912, f"Where {ov['n_people']:,} notable Britons in Wikidata were born, by surname: born in the 1800s against born since 1950.\nBelow: Jones, Davies, Evans and the other Welsh patronymic surnames.", family=SER, fontsize=15.5, color=FG, va="top", linespacing=1.4)
BOX = (-5.6, 1.85, 50.0, 55.2)
for i, (e, col, lab, key) in enumerate(((1, B1, "Born 1800 to 1899", "1800s"), (3, B3, "Born 1950 or later", "since1950"))):
    ax = fig.add_axes([.02 + i * .49, .385, .47, .47]); base(ax, BOX); dots(ax, W["names"], e, col)
    ax.text(.03, .985, lab, transform=ax.transAxes, fontsize=21, family=SER, weight="semibold", color=col, va="top")
    ax.text(.03, .925, f"{round(W['eras'][key]['share_wales'] * 100)}% born in Wales", transform=ax.transAxes, fontsize=30, fontproperties=DISP, color=FG, va="top")
    ax.text(.03, .845, f"{W['eras'][key]['n']:,} notable people", transform=ax.transAxes, fontsize=13, family=MONO, color=MUT, va="top")
# big numbers
NUM = [(f"{round(rg['excess_1800s_median'] * 100)} to {round(rg['excess_since1950_median'] * 100)}", f"points of regional clustering\nbeyond chance, median of\n{rg['n_surnames']} common surnames", FG),
       (f"{round(rg['excess_drop_share'] * 100)}%", "of those surnames became\nless regional since\nthe 1800s", B3),
       (f"{PN['eras']['1800s']['lift']:.1f}x to {PN['eras']['since1950']['lift']:.1f}x", f"place-name surnames born\nwithin {int(PN['radius_km'])} km of the place,\nagainst chance", B1),
       (f"{round(ov['eras']['1800s']['men'] * 100)}%", "of notable people born\nin the 1800s are men:\nthe well-recorded only", MUT)]
for i, (big, txt, col) in enumerate(NUM):
    x = .04 + i * .238
    fig.text(x, .368, big, fontproperties=DISP, fontsize=27, color=col, va="top")
    fig.text(x, .326, txt, family=MONO, fontsize=10.6, color=FG, va="top", linespacing=1.4)
# small multiples
fig.text(.04, .262, "Four more surnames, 1800s (blue) and since 1950 (terracotta)", family=SER, fontsize=16, weight="semibold", color=FG, va="top")
SM = [("Campbell", (-7.2, 1.85, 50.0, 58.8), "Scotland, then spreading south"), ("Robson", (-5.4, 1.85, 50.0, 56.2), "the North East holds on"),
      ("Haigh", (-4.2, 0.9, 51.4, 55.0), "near its village, then not"), ("Davies", (-5.6, 1.85, 50.0, 55.2), "Wales to Cardiff and London")]
for i, (s, box, cap) in enumerate(SM):
    ax = fig.add_axes([.03 + i * .243, .092, .225, .1]); base(ax, box, .35)
    k = 7 if s != "Haigh" else 22
    dots(ax, [s], 1, B1, k=k, s0=5); dots(ax, [s], 3, B3, k=k, s0=5)
    t = SN["t"][IDX[s]]
    fig.text(.035 + i * .243, .238, s, family=SER, fontsize=17, weight="semibold", color=FG, va="top")
    fig.text(.035 + i * .243, .221, f"{t[1]} then, {t[3]} now\n{cap}", family=MONO, fontsize=9.6, color=MUT, va="top", linespacing=1.35)
    if s == "Haigh":
        ns = SN["ns"][str(IDX[s])][0]; ax.scatter(ns[1] * K, ns[0], marker="D", s=46, fc=BG, ec=FG, lw=1.6, zorder=5)
fig.text(.04, .086, "Caveat: notable people only (Wikidata), skewed to men, London and elites: where notable bearers were born,\nnot where most bearers lived. Circle area: notable births at each birthplace. Clustering: dissimilarity index over 11 regions\nand nations against all notable births, minus chance.",
         family=MONO, fontsize=9.6, color=MUT, va="top", linespacing=1.3)
fig.text(.04, .01, "Data: Wikidata (CC0), OS Open Names (OGL v3), ONS boundaries (OGL v3). Analysis and chart: Tristan Hotham, with Python and matplotlib.\nInteractive: maps.tristanhotham.com/surname-birthplaces",
         family=MONO, fontsize=9.6, color=FG, va="bottom")
fig.savefig("surname_left_home.png", dpi=200, facecolor=BG)
print("ok")
