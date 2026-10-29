"""Step 2. All the numbers: who is in the data, how regional each surname was, Welsh patronymics, Cornish Tre, Pol and Pen,
surnames that are also place names, the Hotham example and the check against Scotland's registers.

Writes data/results.json (every number used anywhere) and the reusable CSV files in data/ (aggregates only: counts of
notable births by surname, era and region or place; no individual people).
Run: python3 code/02_analyse.py
"""
import gzip, json, os, re, sys
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from scipy.stats import spearmanr
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

rng = np.random.default_rng(20261029)
d = pd.read_pickle(os.path.join(WORK, "people.pkl"))
d["area"] = d.area.map(lambda a: a.split(" - ")[-1] if " - " in a else a)
places = pd.read_pickle(os.path.join(WORK, "places.pkl"))
OSP = pd.read_pickle(os.path.join(WORK, "os_places.pkl"))
meta = json.load(open(os.path.join(WORK, "meta.json")))
BUN = json.load(gzip.open(WD_BUNDLE)); WIKI = BUN["wikipedia"]["articles"]
RI = {r: i for i, r in enumerate(REGIONS)}
d["ri"] = d.region.map(RI)
# one row per person and surname label (a person with two family-name items of the same spelling counts once)
d = d.drop_duplicates(["pid", "surname"])
R = {"meta": meta}

# ---------- 1. who is in the data ----------
pp = d.drop_duplicates("pid")
ov = {}
for e in ERAS:
    x = pp[pp.era == e]
    ov[e] = dict(n=int(len(x)), women=float((x.sex == "f").mean()), men=float((x.sex == "m").mean()), london=float((x.region == "London").mean()),
                 regions={r: float((x.region == r).mean()) for r in REGIONS})
R["overview"] = dict(eras=ov, n_people=int(len(pp)), n_rows=int(len(d)), n_surnames=int(d.surname.nunique()),
                     n_birthplaces=int(d.place.nunique()), women_all=float((pp.sex == "f").mean()),
                     london_all=float((pp.region == "London").mean()),
                     n_ab=int(len(pp[pp.era.isin([A, B])])))
pd.DataFrame([dict(era=e, people=ov[e]["n"], share_women=round(ov[e]["women"], 4), share_men=round(ov[e]["men"], 4),
                   **{"share_" + r.lower().replace(" ", "_"): round(ov[e]["regions"][r], 4) for r in REGIONS}) for e in ERAS]).to_csv(os.path.join(DATA, "eras_overview.csv"), index=False)

# counts by surname, era and region (the main reusable table)
cnt = d.groupby(["surname", "era", "region"]).pid.nunique().rename("births").reset_index()
cnt.to_csv(os.path.join(DATA, "surname_era_region.csv"), index=False)
base = {e: np.bincount(pp[pp.era == e].ri, minlength=len(REGIONS)) / (pp.era == e).sum() for e in ERAS}

# ---------- 2. how regional is each surname, then and now ----------
g = {s: x for s, x in d[d.era.isin([A, B])].groupby("surname")}
NMIN = 15
eligible = [s for s, x in g.items() if (x.era == A).sum() >= NMIN and (x.era == B).sum() >= NMIN]
ri_era = {e: pp[pp.era == e].ri.values for e in (A, B)}
def dis(ri, e):
    s = np.bincount(ri, minlength=len(REGIONS)) / len(ri)
    return 0.5 * np.abs(s - base[e]).sum()
NULL = {}
def null(m, e, reps=300):
    k = (m, e)
    if k not in NULL: NULL[k] = float(np.mean([dis(rng.choice(ri_era[e], m, replace=False), e) for _ in range(reps)]))
    return NULL[k]
CA = {e: xy(pp[pp.era == e].lat, pp[pp.era == e].lon).mean(0) for e in (A, B)}
base_shift = float(np.linalg.norm(CA[B] - CA[A]))
rows = []
for s in eligible:
    x = g[s]; a = x[x.era == A]; b = x[x.era == B]; m = min(len(a), len(b), 60)
    da = float(np.mean([dis(rng.choice(a.ri.values, m, replace=False), A) for _ in range(200)]))
    db = float(np.mean([dis(rng.choice(b.ri.values, m, replace=False), B) for _ in range(200)]))
    na, nb = null(m, A), null(m, B)
    def top(z, e):
        c = np.bincount(z.ri, minlength=len(REGIONS)); lq = (c / len(z)) / base[e]; lq[c < 3] = 0
        return REGIONS[int(np.argmax(lq))] if lq.max() > 0 else "", float(lq.max())
    ta, la = top(a, A); tb, lb = top(b, B)
    ca, cb = xy(a.lat, a.lon).mean(0), xy(b.lat, b.lon).mean(0)
    rows.append(dict(surname=s, n_1800s=len(a), n_since1950=len(b), sample=m, D_1800s=round(da, 4), D_since1950=round(db, 4),
                     null_1800s=round(na, 4), null_since1950=round(nb, 4), excess_1800s=round(da - na, 4), excess_since1950=round(db - nb, 4),
                     top_region_1800s=ta, lq_1800s=round(la, 2), top_region_since1950=tb, lq_since1950=round(lb, 2),
                     centroid_shift_km=round(float(np.linalg.norm(cb - ca)), 1)))
S = pd.DataFrame(rows).sort_values("excess_1800s", ascending=False)
S.to_csv(os.path.join(DATA, "surname_regional.csv"), index=False)
both_top = S[(S.top_region_1800s != "") & (S.top_region_since1950 != "")]
R["regional"] = dict(
    n_surnames=len(S), nmin=NMIN, cap=60,
    D_1800s_median=float(S.D_1800s.median()), D_since1950_median=float(S.D_since1950.median()),
    excess_1800s_median=float(S.excess_1800s.median()), excess_since1950_median=float(S.excess_since1950.median()),
    excess_drop_share=float((S.excess_since1950 < S.excess_1800s).mean()),
    excess_change_pct=float(S.excess_since1950.median() / S.excess_1800s.median() - 1),
    same_top_share=float((both_top.top_region_1800s == both_top.top_region_since1950).mean()), n_top=len(both_top),
    shift_median_km=float(S.centroid_shift_km.median()), base_shift_km=base_shift,
    most_regional_1800s=S.head(12)[["surname", "excess_1800s", "excess_since1950", "top_region_1800s", "top_region_since1950", "n_1800s", "n_since1950"]].values.tolist(),
    most_regional_now=S.sort_values("excess_since1950", ascending=False).head(12)[["surname", "excess_1800s", "excess_since1950", "top_region_1800s", "top_region_since1950", "n_1800s", "n_since1950"]].values.tolist(),
    scatter=S[["surname", "excess_1800s", "excess_since1950", "n_1800s", "n_since1950"]].values.tolist())
R["regional"]["excess_by_region_1800s"] = {r: [int((S.top_region_1800s == r).sum()), int(((S.top_region_1800s == r) & (S.top_region_since1950 == r)).sum())] for r in REGIONS}

# ---------- 3. signature surnames of each region, then and now ----------
sig = {}
sig_rows = []
for e in (A, B):
    x = d[d.era == e]; N = x.pid.nunique(); tot = x.groupby("surname").pid.nunique()
    reg = x.groupby(["region", "surname"]).pid.nunique()
    rt = x.groupby("region").pid.nunique()
    sig[e] = {}
    for r in REGIONS:
        c = reg[r]; c = c[(c >= 6) & (tot[c.index] >= 8)]
        lq = (c / rt[r]) / (tot[c.index] / N)
        top = lq.sort_values(ascending=False).head(5)
        sig[e][r] = [[s, int(c[s]), int(tot[s]), round(float(v), 1)] for s, v in top.items()]
        for k, (s, v) in enumerate(top.items()): sig_rows.append(dict(era=e, region=r, rank=k + 1, surname=s, births_in_region=int(c[s]), births_all_gb=int(tot[s]), location_quotient=round(float(v), 2)))
pd.DataFrame(sig_rows).to_csv(os.path.join(DATA, "region_signature_surnames.csv"), index=False)
R["signature"] = sig

# ---------- 4. Welsh patronymic surnames ----------
WT = WIKI["Welsh surnames"]["text"]
WELSH = ["Jones", "Williams", "Davies", "Evans", "Thomas", "Roberts", "Edwards", "Powell", "Price", "Pryce", "Pugh", "Pritchard", "Bowen", "Upjohn"]
assert all(w in WT for w in WELSH)
def share_in(names, test, e):
    x = d[(d.era == e) & d.surname.isin(names)].drop_duplicates("pid")
    return int(len(x)), float(test(x).mean()) if len(x) else 0.0
wales = lambda x: x.region == "Wales"
W = {"names": WELSH, "eras": {}}
for e in ERAS:
    n, sh = share_in(WELSH, wales, e); W["eras"][e] = dict(n=n, share_wales=sh, base_wales=float(base[e][RI["Wales"]]))
W["by_name"] = []
for w in WELSH:
    r = [w]
    for e in (A, B):
        n, sh = share_in([w], wales, e); r += [n, sh]
    W["by_name"].append(r)
W["by_name"].sort(key=lambda r: -(r[1] + r[3]))
x = d[(d.era == B) & d.surname.isin(WELSH)].drop_duplicates("pid")
W["since1950_outside_wales_top"] = x[x.region != "Wales"].region.value_counts().head(3).to_dict()
W["jones_n"] = int(d[d.surname == "Jones"].pid.nunique())
R["welsh"] = W
pd.DataFrame([dict(surname=r[0], births_1800s=r[1], share_wales_1800s=round(r[2], 4), births_since1950=r[3], share_wales_since1950=round(r[4], 4)) for r in W["by_name"]]).to_csv(os.path.join(DATA, "welsh_patronymics.csv"), index=False)

# ---------- 5. Cornish Tre, Pol and Pen ----------
corn = lambda x: x.area == "Cornwall"
C = {"eras": {}, "prefix": {}}
pref = {p: sorted({s for s in d.surname.unique() if re.match(rf"^{p}[a-z]", s)}) for p in ("Tre", "Pol", "Pen")}
allc = pref["Tre"] + pref["Pol"] + pref["Pen"]
basec = {e: float(corn(pp[pp.era == e]).mean()) for e in ERAS}
for e in ERAS:
    n, sh = share_in(allc, corn, e); C["eras"][e] = dict(n=n, share_cornwall=sh, base_cornwall=basec[e])
for p, names in pref.items():
    C["prefix"][p] = {"n_names": len(names)}
    for e in ERAS:
        n, sh = share_in(names, corn, e); C["prefix"][p][e] = [n, sh]
tre = d[d.surname.isin(pref["Tre"])].drop_duplicates(["pid"])
tc = tre.groupby("surname").agg(n=("pid", "nunique"), corn=("area", lambda a: (a == "Cornwall").sum())).sort_values("n", ascending=False)
C["tre_top"] = [[s, int(r.n), int(r.corn)] for s, r in tc.head(12).iterrows()]
pen = d[d.surname.isin(pref["Pen"])].drop_duplicates(["pid"])
pc = pen.groupby("surname").agg(n=("pid", "nunique"), corn=("area", lambda a: (a == "Cornwall").sum())).sort_values("n", ascending=False)
C["pen_top"] = [[s, int(r.n), int(r.corn)] for s, r in pc.head(8).iterrows()]
C["pen_wales"] = float((pen.region == "Wales").mean())
C["n_cornwall_births_all"] = int(corn(pp).sum())
C["wiki_rhyme_ok"] = "By Tre Pol and Pen" in WIKI["Tre, Pol and Pen"]["text"]
R["cornish"] = C

# ---------- 6. surnames that are also place names ----------
KINDS = {"City", "Town", "Village"}
opn = OSP[OSP.kind.isin(KINDS)]
ns = {}
for r in opn.itertuples():
    for nm in (r.name, r.name2):
        if nm: ns.setdefault(nm, []).append((r.lat, r.lon, r.name, r.area, r.kind))
cands = [s for s in d.surname.unique() if s in ns and len(ns[s]) <= 3 and len(s) >= 4]
samp = {e: pp[pp.era == e].sample(min(8000, (pp.era == e).sum()), random_state=1) for e in ERAS}
sampxy = {e: xy(samp[e].lat, samp[e].lon) for e in ERAS}
RAD = 25.0
pn_rows = []
for s in cands:
    t = cKDTree(xy([q[0] for q in ns[s]], [q[1] for q in ns[s]]))
    x = d[d.surname == s].drop_duplicates("pid")
    row = dict(surname=s, namesakes=len(ns[s]), namesake_places="; ".join(f"{q[2]} ({q[3]})" for q in ns[s]))
    for e in ERAS:
        xe = x[x.era == e]
        if len(xe):
            dd, _ = t.query(xy(xe.lat, xe.lon)); row[f"n_{e}"] = len(xe); row[f"near_{e}"] = int((dd <= RAD).sum()); row[f"median_km_{e}"] = round(float(np.median(dd)), 1)
        else: row[f"n_{e}"] = 0; row[f"near_{e}"] = 0; row[f"median_km_{e}"] = None
        bd, _ = t.query(sampxy[e]); row[f"base_{e}"] = round(float((bd <= RAD).mean()), 5)
    pn_rows.append(row)
PN = pd.DataFrame(pn_rows)
PN.to_csv(os.path.join(DATA, "placename_surnames.csv"), index=False)
pn = {"n_surnames": len(PN), "radius_km": RAD, "eras": {}}
for e in ERAS:
    z = PN[PN[f"n_{e}"] > 0]
    obs = z[f"near_{e}"].sum() / z[f"n_{e}"].sum(); exp = (z[f"base_{e}"] * z[f"n_{e}"]).sum() / z[f"n_{e}"].sum()
    pn["eras"][e] = dict(n_births=int(z[f"n_{e}"].sum()), n_surnames=len(z), near_share=float(obs), expected_share=float(exp), lift=float(obs / exp))
z = PN[(PN[f"n_{A}"] >= 5) & (PN[f"n_{B}"] >= 5)].copy()
z["lift_A"] = (z[f"near_{A}"] / z[f"n_{A}"]) / z[f"base_{A}"].clip(lower=1e-4); z["lift_B"] = (z[f"near_{B}"] / z[f"n_{B}"]) / z[f"base_{B}"].clip(lower=1e-4)
pn["n_both5"] = len(z)
pn["home_1800s"] = [[r.surname, r.namesake_places.split(" (")[0], int(r[f"n_{A}"]), int(r[f"near_{A}"]), int(r[f"n_{B}"]), int(r[f"near_{B}"])]
                    for _, r in z.assign(sh=z[f"near_{A}"] / z[f"n_{A}"]).sort_values(["sh", f"n_{A}"], ascending=False).head(10).iterrows()]
pn["example_names"] = sorted(PN.sort_values(f"n_{A}", ascending=False).surname.head(12).tolist())
R["placenames"] = pn

# ---------- 7. Hotham ----------
h = d[d.surname == "Hotham"].drop_duplicates("pid").sort_values("year")
hv = OSP[(OSP.name == "Hotham")]
dis_txt = WIKI["Hotham"]["text"]; ppl = dis_txt.split("==People==")[1].split("==Ships==")[0]
n_wiki_people = len(re.findall(r"^\*\[\[", ppl, flags=re.M))
hrows = []
for r in h.itertuples():
    pl = places.loc[r.place]
    hrows.append(dict(year=int(r.year), era=r.era, near=pl.label, area=r.area, lat=float(r.lat), lon=float(r.lon),
                      km_from_village=round(km(r.lat, r.lon, float(hv.lat.iloc[0]), float(hv.lon.iloc[0])), 1)))
hall = d[d.surname == "Hotham"]
R["hotham"] = dict(n_gb=int(hall.pid.nunique()), births=hrows, village=dict(name="Hotham", lat=float(hv.lat.iloc[0]), lon=float(hv.lon.iloc[0]), area=hv.area.iloc[0], kind=hv.kind.iloc[0]),
                   n_village_matches=len(hv), wiki_people_listed=n_wiki_people, wiki_village_pop2011=233,
                   wiki_url=WIKI["Hotham"]["url"], village_url=WIKI["Hotham, East Riding of Yorkshire"]["url"],
                   n_raw=sum(1 for r in BUN["rows"] if BUN["familynames"][str(r[1])] == "Hotham"))
assert "population               = 233" in WIKI["Hotham, East Riding of Yorkshire"]["text"]
# compare with surnames of similar size
R["hotham"]["n_surnames_le2"] = float((d.groupby("surname").pid.nunique() <= 2).mean())

# ---------- 8. Scotland's registers ----------
ts = pd.read_excel(NRS_XLSX, sheet_name="Surnames TimeSeries 1975to2025", header=3)
ts.columns = ["year", "surname", "number", "rank"]
ts["rank"] = ts["rank"].astype(str).str.rstrip("=").astype(int)   # ties are written as "18="
y25 = ts[ts.year == 2025].sort_values("rank").head(100)
sc = d[(d.region == "Scotland")].copy()
sc["key"] = sc.surname.str.lower()   # the registers write Mcdonald, Wikidata McDonald
nb = sc[sc.era == B].groupby("key").pid.nunique(); na_ = sc[sc.era == A].groupby("key").pid.nunique()
nrs_rows = []
for r in y25.itertuples():
    nrs_rows.append(dict(surname=r.surname, nrs_rank_2025=int(r.rank), nrs_entries_2025=int(r.number), notable_born_scotland_1800s=int(na_.get(r.surname.lower(), 0)), notable_born_scotland_since1950=int(nb.get(r.surname.lower(), 0))))
NR = pd.DataFrame(nrs_rows)
NR.to_csv(os.path.join(DATA, "nrs_scotland_comparison.csv"), index=False)
rho, pv = spearmanr(NR.nrs_entries_2025, NR.notable_born_scotland_since1950)
rho_a, _ = spearmanr(NR.nrs_entries_2025, NR.notable_born_scotland_1800s)
tot_reg = NR.nrs_entries_2025.sum(); tot_not = NR.notable_born_scotland_since1950.sum()
NR["ratio"] = (NR.notable_born_scotland_since1950 / tot_not) / (NR.nrs_entries_2025 / tot_reg)
big = NR[NR.nrs_rank_2025 <= 100]
R["nrs"] = dict(spearman_since1950=float(rho), p=float(pv), spearman_1800s=float(rho_a), n=len(NR),
                top10=NR.head(10)[["surname", "nrs_entries_2025", "notable_born_scotland_since1950"]].values.tolist(),
                over=big.sort_values("ratio", ascending=False).head(5)[["surname", "nrs_rank_2025", "notable_born_scotland_since1950", "ratio"]].values.tolist(),
                under=big.sort_values("ratio").head(5)[["surname", "nrs_rank_2025", "notable_born_scotland_since1950", "ratio"]].values.tolist(),
                top100_share_notables=float(tot_not / sc[sc.era == B].pid.nunique()),
                smith_rank=1, smith_notable=int(nb.get("smith", 0)),
                scatter=NR[["surname", "nrs_entries_2025", "notable_born_scotland_since1950"]].values.tolist(),
                url="https://nrscotland.gov.uk/publications/most-common-surnames-2025/")
R["nrs"]["mac_share_since1950"] = float(sc[sc.era == B].drop_duplicates("pid").surname.str.match(r"^(Mac|Mc)[A-Z]").mean())
R["nrs"]["mac_share_1800s"] = float(sc[sc.era == A].drop_duplicates("pid").surname.str.match(r"^(Mac|Mc)[A-Z]").mean())

# ---------- 9. common surnames overall ----------
top = d.groupby("surname").pid.nunique().sort_values(ascending=False)
R["top_surnames"] = [[s, int(n)] for s, n in top.head(15).items()]
R["n_surnames_ge15_both"] = len(eligible)
R["n_surnames_1"] = int((top == 1).sum())

json.dump(R, open(os.path.join(DATA, "results.json"), "w"), indent=1, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else str(o))
print(json.dumps({k: R[k] for k in ["overview"]}, indent=0)[:1500])
for k in ["regional", "welsh", "cornish", "placenames", "hotham", "nrs"]:
    print(k, json.dumps({a: b for a, b in R[k].items() if a not in ("scatter",)}, default=str)[:1800])
