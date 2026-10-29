"""Step 6. Static figures for the blog and the paper (release/blog/b_*.png, 1520 px wide), from data/ files only.
Fonts: FONT_DIR as in step 5 (falls back to DejaVu). Run: FONT_DIR=/path/to/fonts python3 code/06_figures.py
"""
import json, math, os, sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

FD = os.environ.get("FONT_DIR", "")
SER, MONO = "DejaVu Serif", "DejaVu Sans Mono"
if FD:
    for f in ("SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
        if os.path.exists(os.path.join(FD, f)): fm.fontManager.addfont(os.path.join(FD, f))
    SER, MONO = "Source Serif 4", "IBM Plex Mono"
BG, FG, MUT, RULE, LAND = "#F6F2EA", "#1C1B19", "#5F5A52", "#DCD4C4", "#E4DCCB"
EC = ["#8A6A3F", "#2C5A8C", "#5E8A3A", "#C4513A"]
plt.rcParams.update({"font.family": MONO, "font.size": 15, "axes.edgecolor": MUT, "axes.labelcolor": FG, "xtick.color": MUT, "ytick.color": MUT,
                     "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG, "axes.spines.top": False, "axes.spines.right": False})
OUT = os.path.join(ROOT, "release", "blog"); os.makedirs(OUT, exist_ok=True)
R = json.load(open(os.path.join(DATA, "results.json")))
PL = json.load(open(os.path.join(DATA, "page", "places.json"))); SN = json.load(open(os.path.join(DATA, "page", "surnames.json")))
OL = json.load(open(os.path.join(DATA, "page", "outline.json")))
K = math.cos(math.radians(54.5))
ERAL = ["1700s", "1800s", "1900 to 1949", "Since 1950"]
def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=150); plt.close(fig); print(name)

def land(ax, lw=.6):
    g = OL["land"]
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        ring = np.array(poly[0]); ax.add_patch(Polygon(np.c_[ring[:, 0] * K, ring[:, 1]], closed=True, fc=LAND, ec="#C9BFAC", lw=lw, zorder=1))
def births(names, eras):
    idx = {s: i for i, s in enumerate(SN["s"])}; c = {}
    for s in names:
        if s not in idx: continue
        f = SN["p"][idx[s]]
        for k in range(0, len(f), 3):
            if f[k + 1] in eras: c[(f[k], f[k + 1])] = c.get((f[k], f[k + 1]), 0) + f[k + 2]
    return c

# 1. Welsh patronymics, then and now
W = R["welsh"]
fig, axs = plt.subplots(1, 2, figsize=(10.13, 7.6))
for ax, e in zip(axs, (1, 3)):
    land(ax); c = births(W["names"], [e])
    for (p, _), n in sorted(c.items(), key=lambda kv: -kv[1]):
        ax.scatter(PL["lo"][p] / 1e4 * K, PL["la"][p] / 1e4, s=10 + n * 9, color=EC[e], alpha=.6, lw=.4, ec=BG, zorder=3)
    ax.set_xlim(-6.0 * K, 1.9 * K); ax.set_ylim(50.0, 55.9); ax.set_aspect("equal"); ax.axis("off")
    k = "1800s" if e == 1 else "since1950"
    ax.text(.02, .99, ("Born 1800 to 1899" if e == 1 else "Born 1950 or later"), transform=ax.transAxes, fontsize=19, family=SER, weight="semibold", color=EC[e], va="top")
    ax.text(.02, .925, f"{W['eras'][k]['n']:,} notable people\n{round(W['eras'][k]['share_wales'] * 100)}% born in Wales", transform=ax.transAxes, fontsize=14, color=FG, va="top", linespacing=1.4)
fig.text(.5, .02, "England and Wales. Circle area: notable births at each birthplace.", ha="center", fontsize=12, color=MUT)
fig.subplots_adjust(left=.01, right=.99, top=.99, bottom=.06, wspace=.02)
save(fig, "b_welsh_map.png")

# 2. where notable people were born
ov = R["overview"]["eras"]
order = sorted(REGIONS, key=lambda r: ov["1800s"]["regions"][r])
fig, ax = plt.subplots(figsize=(10.13, 6.6)); y = np.arange(len(order))
for k, (e, col, off) in enumerate((("1800s", EC[1], .2), ("since1950", EC[3], -.2))):
    v = [ov[e]["regions"][r] for r in order]; ax.barh(y + off, v, height=.38, color=col, label="Born 1800 to 1899" if k == 0 else "Born 1950 or later")
    for yy, vv in zip(y + off, v): ax.text(vv + .003, yy, f"{round(vv * 100)}%", va="center", fontsize=12, color=FG)
ax.set_yticks(y); ax.set_yticklabels([REGION_SHORT.get(r, r) for r in order], fontsize=14, color=FG)
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{round(v * 100)}%")); ax.set_xlim(0, .27)
ax.grid(axis="x", color=RULE); ax.set_axisbelow(True); ax.legend(frameon=False, loc="lower right", fontsize=13)
ax.set_xlabel("Share of each era's notable births in Great Britain", fontsize=13, color=MUT)
fig.tight_layout(); save(fig, "b_regions.png")

# 3. scatter of regional clustering
S = pd.read_csv(os.path.join(DATA, "surname_regional.csv"))
fig, ax = plt.subplots(figsize=(10.13, 8.6))
lo, hi = -6, 62
ax.plot([lo, hi], [lo, hi], ls="--", color=FG, lw=1)
col = np.where(S.excess_since1950 < S.excess_1800s, EC[1], EC[3])
ax.scatter(S.excess_1800s * 100, S.excess_since1950 * 100, s=12 + np.sqrt(S.n_1800s + S.n_since1950) * 3.2, c=col, alpha=.55, lw=.5, ec=BG)
lab = {"Rees": (6, -2), "Jones": (6, -10), "Davies": (6, 4), "Paterson": (6, 2), "Thomson": (6, -12), "McKenzie": (6, -10), "Robson": (6, 0), "Smith": (8, -14), "Cameron": (6, -10), "Campbell": (6, 4), "Parkinson": (6, 0), "Owen": (6, -2)}
for r in S.itertuples():
    if r.surname in lab: ax.annotate(r.surname, (r.excess_1800s * 100, r.excess_since1950 * 100), xytext=lab[r.surname], textcoords="offset points", fontsize=12.5, color=FG)
ax.set_xlim(lo, hi); ax.set_ylim(lo, hi); ax.set_aspect("equal")
ax.set_xlabel("Regional clustering beyond chance, born 1800 to 1899 (points)", fontsize=13)
ax.set_ylabel("Born 1950 or later (points)", fontsize=13)
ax.grid(color=RULE); ax.set_axisbelow(True)
ax.text(45, 6, "less regional now", color=EC[1], fontsize=14, ha="center"); ax.text(10, 50, "more regional now", color=EC[3], fontsize=14, ha="center")
fig.tight_layout(); save(fig, "b_scatter.png")

# 4. three tests
C = R["cornish"]; PN = R["placenames"]
tests = [("Welsh patronymics\nborn in Wales", [W["eras"][e]["share_wales"] for e in ERAS], [W["eras"][e]["base_wales"] for e in ERAS]),
         ("Tre-, Pol-, Pen- names\nborn in Cornwall", [C["eras"][e]["share_cornwall"] for e in ERAS], [C["eras"][e]["base_cornwall"] for e in ERAS]),
         (f"Place-name surnames born\nwithin {int(PN['radius_km'])} km of the place", [PN["eras"][e]["near_share"] for e in ERAS], [PN["eras"][e]["expected_share"] for e in ERAS])]
fig, axs = plt.subplots(1, 3, figsize=(10.13, 5.4))
for ax, (t, v, b) in zip(axs, tests):
    x = np.arange(4); ax.bar(x, v, color=EC, width=.68)
    ax.scatter(x, b, marker="_", s=900, color=FG, lw=2.6, zorder=4)
    for xx, vv in zip(x, v): ax.text(xx, vv * 1.02 + max(v) * .01, f"{vv * 100:.0f}%" if max(v) > .2 else f"{vv * 100:.1f}%", ha="center", va="bottom", fontsize=11.5)
    ax.set_xticks(x); ax.set_xticklabels(["1700s", "1800s", "1900\nto 1949", "Since\n1950"], fontsize=11)
    ax.set_title(t, fontsize=13.5, family=SER, color=FG, loc="left")
    ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(.2 if max(v) > .5 else .05 if max(v) > .1 else .01))
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v * 100:.0f}%")); ax.set_ylim(0, max(v) * 1.2)
    ax.grid(axis="y", color=RULE); ax.set_axisbelow(True); ax.tick_params(axis="y", labelsize=11)
fig.text(.5, .015, "Bars: notable people with these surnames. Black line: all notable births of the era.", ha="center", fontsize=11.5, color=MUT)
fig.tight_layout(rect=(0, .05, 1, 1)); save(fig, "b_tests.png")

# 5. Scotland's registers
N = pd.read_csv(os.path.join(DATA, "nrs_scotland_comparison.csv"))
fig, ax = plt.subplots(figsize=(10.13, 7.2))
ax.scatter(N.nrs_entries_2025, N.notable_born_scotland_since1950, s=55, color=EC[3], alpha=.65, lw=.5, ec=BG)
for r in N.itertuples():
    if r.surname in ("Smith", "Brown", "Wilson", "Robertson", "Campbell", "Kerr", "Johnstone", "Mckenzie", "Murray", "Thomson", "Taylor"):
        ax.annotate(r.surname, (r.nrs_entries_2025, r.notable_born_scotland_since1950), xytext=(6, 3), textcoords="offset points", fontsize=12.5)
ax.set_xscale("log"); ax.set_xticks([200, 300, 500, 1000, 2000]); ax.get_xaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
ax.set_xlabel("Entries in Scotland's birth, marriage and death registers, 2025", fontsize=13); ax.set_ylabel("Notable people born in Scotland since 1950", fontsize=13)
ax.grid(color=RULE); ax.set_axisbelow(True)
ax.text(.02, .96, f"Spearman correlation {R['nrs']['spearman_since1950']:.2f}", transform=ax.transAxes, fontsize=14, va="top")
fig.tight_layout(); save(fig, "b_nrs.png")

# 6. Hotham and Haigh: the namesake and the births
H = R["hotham"]
fig, axs = plt.subplots(1, 2, figsize=(10.13, 6.4))
for ax, (s, box) in zip(axs, (("Hotham", (-2.6, 1.9, 51.9, 54.6)), ("Haigh", (-3.4, -0.7, 52.75, 54.4)))):
    land(ax, .8); i = SN["s"].index(s)
    for e in (1, 3, 2, 0):
        c = births([s], [e])
        for (p, _), n in c.items():
            x, y = PL["lo"][p] / 1e4 * K, PL["la"][p] / 1e4
            ax.scatter(x + (e - 2) * .012, y, s=40 + n * 40, color=EC[e], alpha=.8, lw=.6, ec=BG, zorder=4)
    for la, lo, nm, ar in SN["ns"][str(i)]:
        ax.scatter(lo * K, la, marker="D", s=120, fc=BG, ec=FG, lw=2.2, zorder=5); ax.annotate(nm + " (village)", (lo * K, la), xytext=(9, -4), textcoords="offset points", fontsize=12.5, weight="medium", zorder=6)
    ax.set_xlim(box[0] * K, box[1] * K); ax.set_ylim(box[2], box[3]); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_visible(True); sp.set_color(RULE)
    ax.set_title(s, fontsize=19, family=SER, weight="semibold", loc="left", color=FG)
for b in H["births"]:
    axs[0].annotate(f"born {b['year']}\nnear {b['near']}", (b["lon"] * K, b["lat"]), xytext=(-10, 6) if b["lon"] > 0 else (10, 6), ha="right" if b["lon"] > 0 else "left", textcoords="offset points", fontsize=11.5, color=EC[1])
hd = [h for h in SN["s"]]
handles = [plt.Line2D([], [], marker="o", ls="", color=EC[e], ms=10, label=lab) for e, lab in ((0, "born 1700s"), (1, "born 1800s"), (2, "born 1900 to 1949"), (3, "born since 1950"))]
fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=12)
fig.tight_layout(rect=(0, .07, 1, 1)); save(fig, "b_hotham_haigh.png")
