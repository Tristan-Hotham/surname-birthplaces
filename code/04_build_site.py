"""Step 4. Fill code/page_template.html with numbers from data/results.json to make index.html.

A few page-level numbers derived from results.json are stored under "page" first, so that results.json holds every
number on the page. Facts the text states in words are checked against the data here.
Run: python3 code/04_build_site.py
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

RP = os.path.join(DATA, "results.json")
R = json.load(open(RP))
ov = R["overview"]["eras"]; rg = R["regional"]; W = R["welsh"]; C = R["cornish"]; PN = R["placenames"]; N = R["nrs"]
home = {r[0]: r for r in PN["home_1800s"]}
R["page"] = dict(
    excess_drop=-rg["excess_change_pct"], excess_1800s_pts=f"{rg['excess_1800s_median'] * 100:.1f}", excess_since1950_pts=f"{rg['excess_since1950_median'] * 100:.1f}",
    women_1800s=ov["1800s"]["women"], women_since1950=ov["since1950"]["women"], men_1800s=ov["1800s"]["men"],
    london_1800s=ov["1800s"]["london"], london_since1950=ov["since1950"]["london"], grid_lat=0.25, grid_lon=0.4, n_welsh=len(W["names"]),
    welsh_london=W["since1950_outside_wales_top"]["London"], welsh_nw=W["since1950_outside_wales_top"]["North West"],
    corn_lift_1800s=C["eras"]["1800s"]["share_cornwall"] / C["eras"]["1800s"]["base_cornwall"],
    haigh_n=home["Haigh"][2], haigh_near=home["Haigh"][3], lees_n=home["Lees"][2], lees_near=home["Lees"][3],
    le2_share=R["hotham"]["n_surnames_le2"], n_regions=len(REGIONS))
json.dump(R, open(RP, "w"), indent=1, ensure_ascii=False)

# words in the text, checked
top1800 = [r[0] for r in rg["most_regional_1800s"]]; topnow = [r[0] for r in rg["most_regional_now"]]
assert top1800[:4] == ["Rees", "Davies", "Owen", "Jones"] and {"McKenzie", "Reid", "McLean", "Cameron"} <= set(top1800)
assert {"Paterson", "Thomson", "Robertson", "Robson", "Parkinson"} <= set(topnow)
assert home["Haigh"][5] == 0 and home["Lees"][5] == 0
import pandas as _pd
_pn = _pd.read_csv(os.path.join(DATA, "placename_surnames.csv")).set_index("surname")
assert _pn.loc["Haigh", "namesake_places"] == "Haigh (Barnsley)" and _pn.loc["Lees", "namesake_places"] == "Lees (Oldham); Lees (Derbyshire)"
assert list(W["since1950_outside_wales_top"])[:2] == ["London", "North West"]
assert 5 <= W["eras"]["since1950"]["share_wales"] / W["eras"]["since1950"]["base_wales"] < 7
assert R["top_surnames"][0][0] == "Jones" and W["jones_n"] == R["top_surnames"][0][1]
assert ov["since1950"]["regions"]["Scotland"] < ov["1800s"]["regions"]["Scotland"]
assert [o[0] for o in N["over"][:4]] == ["Mckenzie", "Kerr", "Mclaughlin", "Gibson"] and [u[0] for u in N["under"][:4]] == ["Johnstone", "Dickson", "Green", "Hill"] and N["under"][0][2] == 0
assert max(N["scatter"], key=lambda r: r[2])[0] == "Smith" and N["scatter"][0][0] == "Smith"
assert C["eras"]["1800s"]["base_cornwall"] < .01 and all(ov[e]["regions"]["South West"] >= 0 for e in ERAS)
assert all(R["cornish"]["eras"][e]["base_cornwall"] < .015 for e in ERAS)
assert R["hotham"]["n_gb"] == 2 and all(b["era"] == "1800s" for b in R["hotham"]["births"])

def get(path):
    cur = R
    for k in path.split("."):
        cur = cur[int(k)] if isinstance(cur, list) else cur[k]
    return cur
def f(m):
    path, _, fm = m.group(1).partition("|")
    v = get(path.strip())
    if fm == "int": return f"{round(v):,}"
    if fm == "pct": return f"{round(v * 100)}%"
    if fm == "pct1": return f"{v * 100:.1f}%"
    if fm == "f1": return f"{v:.1f}"
    if fm == "f2": return f"{v:.2f}"
    if fm == "date":
        y, mo, dd = map(int, v.split("-")); return f"{dd} {['January','February','March','April','May','June','July','August','September','October','November','December'][mo - 1]} {y}"
    return str(v)

if __name__ == "__main__":
    t = open(os.path.join(HERE, "page_template.html")).read()
    t = t.replace("{{meta.retrieved}}", "{{meta.retrieved|date}}")
    t = re.sub(r"\{\{([^}]+)\}\}", f, t)
    sc = [r for r in rg["scatter"]]
    emb = dict(regions=REGIONS, ov={str(i): ov[e]["regions"] for i, e in enumerate(ERAS)},
               scatter=[[r[0], r[1], r[2], r[3], r[4]] for r in sc], scat_labels=["Rees", "Jones", "Davies", "Paterson", "Thomson", "McKenzie", "Robson", "Smith", "Campbell", "Cameron", "Williams"],
               signature=R["signature"], welsh=[[W["eras"][e]["share_wales"], W["eras"][e]["base_wales"]] for e in ERAS], welsh_names=W["by_name"],
               corn=[[C["eras"][e]["share_cornwall"], C["eras"][e]["base_cornwall"]] for e in ERAS],
               pn=[[PN["eras"][e]["near_share"], PN["eras"][e]["expected_share"]] for e in ERAS],
               nrs=N["scatter"], nrs_labels=["Smith", "Brown", "Wilson", "Campbell", "Robertson", "Kerr", "Johnstone", "Mckenzie", "Murray", "Thomson"],
               quick=["Jones", "Campbell", "Davies", "Smith", "Trevelyan", "Haigh", "Robson", "Paterson", "Hotham"], default_surname="Jones")
    import pandas as pd
    S = pd.read_csv(os.path.join(DATA, "surname_regional.csv"))
    emb["reg"] = {r.surname: [round(r.excess_1800s * 100, 1), round(r.excess_since1950 * 100, 1), int(round(r.centroid_shift_km))] for r in S.itertuples()}
    emb["ov"] = [ov[e]["regions"] for e in ERAS]
    t = t.replace("/*R*/", json.dumps(emb, ensure_ascii=False, separators=(",", ":")))
    assert "{{" not in t
    vis = re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t, flags=re.S))
    for bad in ("—", "–", "--"): assert bad not in vis, bad
    js = re.search(r"<script>\nconst R.*?</script>", t, flags=re.S).group(0)
    for bad in ("—", "–"): assert bad not in js, bad
    open(os.path.join(ROOT, "index.html"), "w").write(t)
    print("index.html", os.path.getsize(os.path.join(ROOT, "index.html")))
