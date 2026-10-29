"""Step 1. Read the Wikidata people bundle, keep births in Great Britain and attach each birthplace to OS Open Names.

Each row of the bundle is one (person, family name) pair: a human in Wikidata with a family name (P734), a place of
birth (P19) with coordinates and a birth year from 1700. A birthplace counts as in Great Britain when an OS Open Names
populated place lies within 10 km of its coordinates; its region, county and nearest place name come from that place.
Northern Ireland, the Isle of Man and the Channel Islands are not in OS Open Names, so they drop out here.
Output (temporary): WORK/people.pkl, WORK/places.pkl, WORK/os_places.pkl, WORK/meta.json
Run: python3 code/01_prepare.py
"""
import csv, gzip, json, os, sys
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

B = json.load(gzip.open(WD_BUNDLE))
fn = {int(k): v for k, v in B["familynames"].items()}
d = pd.DataFrame(B["rows"], columns=["pid", "fn", "year", "lat", "lon", "sex"])
d["surname"] = d.fn.map(fn)
n_raw, n_people_raw = len(d), d.pid.nunique()

# OS Open Names populated places
os_rows = []
with open(OSNAMES, encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        if r["type"] != "populatedPlace": continue
        os_rows.append((r["name1"], r["name2"], r["local_type"], float(r["lat"]), float(r["lon"]), r["district"], r["county"], r["region"], r["country"]))
P = pd.DataFrame(os_rows, columns=["name", "name2", "kind", "lat", "lon", "district", "county", "region", "country"])
P["area"] = np.where(P.county != "", P.county, P.district)
P.to_pickle(os.path.join(WORK, "os_places.pkl"))
tree = cKDTree(xy(P.lat, P.lon))

# unique birthplaces
bp = d[["lat", "lon"]].drop_duplicates().reset_index(drop=True)
dist, idx = tree.query(xy(bp.lat, bp.lon))
bp["dist_km"] = dist
for c in ["name", "kind", "area", "region", "country"]: bp["os_" + c] = P[c].values[idx]
bp = bp[bp.dist_km <= 10].reset_index(drop=True)
# a readable label: the nearest city or town within 5 km, else the nearest village within 3 km, else the nearest place
lab = bp.os_name.copy()
for kinds, rad in ((["Village"], 3.0), (["City", "Town"], 5.0)):
    sub = P[P.kind.isin(kinds)].reset_index(drop=True); t = cKDTree(xy(sub.lat, sub.lon))
    dd, ii = t.query(xy(bp.lat, bp.lon)); ok = dd <= rad
    lab[ok] = sub.name.values[ii[ok]]
bp["label"] = lab
bp["place"] = bp.index
d = d.merge(bp, on=["lat", "lon"], how="inner")
d["era"] = d.year.map(era_of)
d = d.rename(columns={"os_region": "region", "os_area": "area", "os_country": "country"})
assert set(d.region) <= set(REGIONS), set(d.region) - set(REGIONS)
d[["pid", "fn", "surname", "year", "era", "sex", "place", "lat", "lon", "region", "area", "country"]].to_pickle(os.path.join(WORK, "people.pkl"))
bp.to_pickle(os.path.join(WORK, "places.pkl"))
meta = dict(retrieved=B["retrieved"], source=B["source"], query=B["query"], n_rows_raw=n_raw, n_people_raw=n_people_raw,
            n_rows_gb=len(d), n_people_gb=int(d.pid.nunique()), n_surnames_gb=int(d.fn.nunique()), n_birthplaces=len(bp),
            n_rows_dropped=n_raw - len(d))
json.dump(meta, open(os.path.join(WORK, "meta.json"), "w"), indent=1)
print(meta)
print(d.groupby("era").pid.nunique())
