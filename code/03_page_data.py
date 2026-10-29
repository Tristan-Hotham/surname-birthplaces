"""Step 3. Compact data files for the interactive page (data/page/). Aggregates only: counts of notable births by
surname, era and birthplace, for surnames with at least two notable births in Great Britain.

  places.json    every birthplace in the data: position, a readable nearby place name, region, and births in each era
  surnames.json  for each surname: births by era, and births by birthplace and era; namesake places from OS Open Names
  names.json     cities, towns and villages from OS Open Names for map labels and the place search
  outline.json   land and nation borders (simplified) for the plain base map and the borders layer
Run: python3 code/03_page_data.py
"""
import json, os, sys
import numpy as np, pandas as pd
import shapely
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

OUT = os.path.join(DATA, "page"); os.makedirs(OUT, exist_ok=True)
LTLA = os.environ.get("LTLA", "/home/claude/hist/how-roman-is-your-road/data/ons/ltla.geojson")
d = pd.read_pickle(os.path.join(WORK, "people.pkl")).drop_duplicates(["pid", "surname"])
bp = pd.read_pickle(os.path.join(WORK, "places.pkl"))
OSP = pd.read_pickle(os.path.join(WORK, "os_places.pkl"))
EI = {e: i for i, e in enumerate(ERAS)}; RI = {r: i for i, r in enumerate(REGIONS)}
d["ei"] = d.era.map(EI)

# birthplaces, renumbered to those used
used = sorted(d.place.unique()); PI = {p: i for i, p in enumerate(used)}
pp = d.drop_duplicates("pid")
allc = pp.groupby(["place", "ei"]).pid.nunique().unstack(fill_value=0).reindex(columns=range(4), fill_value=0)
b = bp.set_index("place").loc[used]
places = dict(la=(b.lat * 1e4).round().astype(int).tolist(), lo=(b.lon * 1e4).round().astype(int).tolist(), nm=b.label.tolist(),
              rg=b.os_region.map(RI).tolist(), c=allc.reindex(used, fill_value=0).values.tolist(), regions=REGIONS, eras=ERAS,
              tot=[int((pp.ei == i).sum()) for i in range(4)])
json.dump(places, open(os.path.join(OUT, "places.json"), "w"), separators=(",", ":"), ensure_ascii=False)

# surnames with at least two notable births
tot = d.groupby("surname").pid.nunique()
keep = tot[tot >= 2].index
x = d[d.surname.isin(keep)].groupby(["surname", "place", "ei"]).pid.nunique().reset_index()
te = d[d.surname.isin(keep)].groupby(["surname", "ei"]).pid.nunique().unstack(fill_value=0).reindex(columns=range(4), fill_value=0)
names = sorted(keep, key=lambda s: (-int(tot[s]), s))
NI = {s: i for i, s in enumerate(names)}
flat = [[] for _ in names]
for r in x.itertuples(): flat[NI[r.surname]] += [PI[r.place], r.ei, r.pid]
# namesake places (cities, towns and villages with exactly the surname's spelling; at most three)
opn = OSP[OSP.kind.isin(["City", "Town", "Village"])]
ns = {}
for r in opn.itertuples():
    for nm in (r.name, r.name2):
        if nm: ns.setdefault(nm, []).append([round(r.lat, 4), round(r.lon, 4), r.name, r.area.split(" - ")[-1]])
nsk = {NI[s]: ns[s] for s in names if s in ns and len(ns[s]) <= 3 and len(s) >= 4}
json.dump(dict(s=names, t=te.loc[names].values.tolist(), p=flat, ns=nsk), open(os.path.join(OUT, "surnames.json"), "w"), separators=(",", ":"), ensure_ascii=False)

# labels and search: cities, towns and villages
MAJOR = {"London", "Birmingham", "Manchester", "Glasgow", "Edinburgh", "Cardiff", "Leeds", "Newcastle upon Tyne", "Bristol", "Liverpool", "Sheffield",
         "Aberdeen", "Inverness", "Norwich", "Plymouth", "Southampton", "Nottingham", "Leicester", "York", "Dundee", "Swansea", "Kingston upon Hull",
         "Carlisle", "Exeter", "Cambridge", "Oxford", "Lincoln", "Truro"}
lab = OSP[OSP.kind.isin(["City", "Town", "Village"])].copy()
lab["r"] = lab.kind.map({"City": 4, "Town": 3, "Village": 1}); lab.loc[lab.name.isin(MAJOR) & (lab.r >= 3), "r"] = 5
lab = lab.drop_duplicates(["name", "area"])
json.dump(dict(n=lab.name.tolist(), la=(lab.lat * 1e4).round().astype(int).tolist(), lo=(lab.lon * 1e4).round().astype(int).tolist(),
               r=lab.r.tolist(), a=[a.split(" - ")[-1] for a in lab.area]), open(os.path.join(OUT, "names.json"), "w"), separators=(",", ":"), ensure_ascii=False)

# outline: nations of the UK from ONS local authority districts (OGL)
def rnd(geom, tol):
    return shapely.set_precision(shapely.simplify(geom, tol, preserve_topology=True), 0.0001)
lj = json.load(open(LTLA)); parts = {"E": [], "W": [], "S": [], "N": []}
for f in lj["features"]:
    p = f["properties"]
    if p.get("end") is None: parts[p["areacd"][0]].append(shapely.make_valid(shape(f["geometry"])).buffer(0))
nat = {k: unary_union(v) for k, v in parts.items()}
land = unary_union(list(nat.values()))
borders = unary_union([nat["E"].boundary.intersection(nat["W"].buffer(0.002)), nat["E"].boundary.intersection(nat["S"].buffer(0.002))])
json.dump(dict(land=mapping(rnd(land, 0.004)), borders=mapping(rnd(borders, 0.002))), open(os.path.join(OUT, "outline.json"), "w"), separators=(",", ":"))
# region label anchors: the mean position of each region's birthplaces, weighted by births
rl = {}
for r, z in pp.groupby("region"): rl[r] = [round(float(z.lat.median()), 3), round(float(z.lon.median()), 3)]
json.dump(rl, open(os.path.join(WORK, "region_anchor.json"), "w"))
for f in os.listdir(OUT): print(f, os.path.getsize(os.path.join(OUT, f)))
print("surnames on the page", len(names))
