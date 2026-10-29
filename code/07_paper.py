"""Step 7. Fill code/paper_template.tex from data/results.json and compile with xelatex (figures from step 6).
Writes release/paper/ (tex and figures) and release/Hotham_Surname_Birthplaces.pdf. Run: python3 code/07_paper.py
"""
import importlib.util, json, os, re, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "04_build_site.py")); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
R = b.R
OUT = os.path.join(ROOT, "release", "paper"); os.makedirs(OUT, exist_ok=True)
NAME = "Hotham_Surname_Birthplaces"
tex = lambda s: str(s).replace("&", r"\&").replace("%", r"\%").replace("_", r"\_").replace("#", r"\#")
def sub(m):
    path, _, fm = m.group(1).partition("|"); v = b.get(path.strip())
    if fm == "pct": return f"{round(v * 100)}\\%"
    if fm == "pct1": return f"{v * 100:.1f}\\%"
    if fm == "date": return b.f(m)
    if fm in ("int", "f1", "f2"): return b.f(m)
    return tex(v)
ov = R["overview"]["eras"]
_s = R["signature"]["1800s"]   # names the text gives in words
assert [x[0] for x in _s["Yorkshire and the Humber"][:3]] == ["Stansfield", "Lupton", "Firth"] and [x[0] for x in _s["North West"][:2]] == ["Ashworth", "Royle"]
assert _s["Wales"][0][0] == "Rees" and [x[0] for x in _s["North East"][:3]] == ["Elliot", "Headlam", "Liddell"]
EL = {"1700s": "1700 to 1799", "1800s": "1800 to 1899", "1900to1949": "1900 to 1949", "since1950": "1950 onwards"}
rows = "".join(f"{EL[e]} & {ov[e]['n']:,} & {round(ov[e]['women'] * 100)}\\% & {round(ov[e]['london'] * 100)}\\% & {round(ov[e]['regions']['Scotland'] * 100)}\\% & {round(ov[e]['regions']['Wales'] * 100)}\\%\\\\\n" for e in ERAS)
T_ERAS = ("\\begin{table}[H]\\centering\\small\\caption{Notable people born in Great Britain in the sample, by era of birth: number, share women, and share born in London, Scotland and Wales.}\\label{tab:eras}"
          "\\begin{tabular}{lrrrrr}\\toprule Born & People & Women & London & Scotland & Wales\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rs = lambda r: REGION_SHORT.get(r, r)
rows = "".join(f"{tex(r[0])} & {r[5]} & {r[6]} & {tex(rs(r[3]))} & {r[1] * 100:.0f} & {r[2] * 100:.0f}\\\\\n" for r in R["regional"]["most_regional_1800s"])
T_TOP = ("\\begin{table}[H]\\centering\\small\\caption{The twelve most regional surnames among people born in the 1800s: notable births in each era, the region of greatest over-representation in the 1800s, and regional clustering beyond chance (percentage points) in each era.}\\label{tab:top}"
         "\\begin{tabular}{lrrlrr}\\toprule Surname & Born 1800s & Since 1950 & Home region & Clustering 1800s & Since 1950\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
sg = R["signature"]
rows = "".join(f"{tex(rs(r))} & {tex(', '.join(x[0] for x in sg['1800s'][r][:3]))} & {tex(', '.join(x[0] for x in sg['since1950'][r][:3]))}\\\\\n" for r in REGIONS)
T_SIG = ("\\begin{table}[H]\\centering\\small\\caption{Signature surnames: the three surnames most over-represented among each region's notable births (location quotient; at least six births in the region and eight in Great Britain).}\\label{tab:sig}"
         "\\begin{tabular}{l>{\\raggedright\\arraybackslash}p{5.6cm}>{\\raggedright\\arraybackslash}p{5.6cm}}\\toprule Region & Born 1800 to 1899 & Born 1950 onwards\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(HERE, "paper_template.tex")).read()
t = t.replace("{{meta.retrieved}}", "{{meta.retrieved|date}}")
t = t.replace("{{TABLE_ERAS}}", T_ERAS).replace("{{TABLE_TOP}}", T_TOP).replace("{{TABLE_SIG}}", T_SIG)
t = re.sub(r"\{\{([^}]+)\}\}", sub, t)
assert "{{" not in t and "--" not in t and "—" not in t and "–" not in t
open(os.path.join(OUT, NAME + ".tex"), "w").write(t)
for f in ["b_regions.png", "b_scatter.png", "b_welsh_map.png", "b_tests.png", "b_hotham_haigh.png", "b_nrs.png"]:
    shutil.copy(os.path.join(ROOT, "release", "blog", f), os.path.join(OUT, f))
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
if r.returncode: print(r.stdout[-3000:])
shutil.copy(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
for ext in [".aux", ".log", ".out", ".pdf"]:
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
print("paper written", r.returncode)
