"""Step 8. README, blog post and metadata, and the Zenodo folder.
Writes README.md, release/blog/post.html and meta.json, release/zenodo/ (paper, key data files, code-and-data zip, meta.json).
Run after 07_paper.py: python3 code/08_release.py
"""
import importlib.util, json, os, re, shutil, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "04_build_site.py")); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
R = b.R
SLUG, DOI, PDF = "surname-birthplaces", "10.5281/zenodo.23761427", "Hotham_Surname_Birthplaces.pdf"
assert R["hotham"]["births"][0]["area"] == "Suffolk"
fill = lambda t: re.sub(r"\{\{(?!IMG\|)([^}]+)\}\}", b.f, t.replace("{{meta.retrieved}}", "{{meta.retrieved|date}}"))
rd = fill(open(os.path.join(HERE, "README_template.md")).read())
open(os.path.join(ROOT, "README.md"), "w").write(rd)
blog = os.path.join(ROOT, "release", "blog")
t = fill(open(os.path.join(HERE, "blog_template.html")).read())
for img in re.findall(r"\{\{IMG\|([^|]+)\|", t): assert os.path.exists(os.path.join(blog, img)), img
assert "{{" not in re.sub(r"\{\{IMG\|[^}]*\}\}", "", t)
open(os.path.join(blog, "post.html"), "w").write(t)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", t).split())
meta = dict(title="Has your surname left home?", slug=SLUG,
            excerpt=f"Where {R['overview']['n_people']:,} notable Britons with each surname were born, 1800s against since 1950. Welsh Joneses, Cornish Tre- names and place-name surnames are all leaving home, though not as fast as you might think.",
            seo_description="Where notable people with each British surname were born, 1800s against since 1950, from Wikidata. Search your surname. Notable people only.",
            tags=["surnames", "family history", "Wikidata", "maps", "Wales", "Cornwall", "Scotland", "open data"],
            header_alt="Social card reading 'Has your surname left home?' beside a map of Great Britain with blue dots packed into Wales for notable people with Welsh patronymic surnames born in the 1800s, and terracotta dots spread across England for those born since 1950.")
json.dump(meta, open(os.path.join(blog, "meta.json"), "w"), indent=1, ensure_ascii=False)
print("post.html words", words)

z = os.path.join(ROOT, "release", "zenodo"); os.makedirs(z, exist_ok=True)
shutil.copy(os.path.join(ROOT, "release", PDF), os.path.join(z, PDF))
for fn in ["surname_era_region.csv", "surname_regional.csv", "region_signature_surnames.csv", "placename_surnames.csv", "welsh_patronymics.csv", "nrs_scotland_comparison.csv", "eras_overview.csv", "results.json"]:
    shutil.copy(os.path.join(DATA, fn), os.path.join(z, fn))
zp = os.path.join(z, f"{SLUG}_code_and_data.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as zf:
    for base in ["code", "data"]:
        for dp, _, fs in os.walk(os.path.join(ROOT, base)):
            for fn in fs:
                if fn.endswith(".pyc") or "__pycache__" in dp: continue
                p = os.path.join(dp, fn); zf.write(p, os.path.relpath(p, ROOT))
    for fn in ["README.md", "LICENSE"]: zf.write(os.path.join(ROOT, fn), fn)
tex = open(os.path.join(ROOT, "release", "paper", PDF.replace(".pdf", ".tex"))).read()
ab = re.search(r"\\textbf\{Abstract\}\\end\{center\}(.*?)\\textbf\{Keywords", tex, re.S).group(1).strip()
ab = ab.replace("\\%", "%").replace("~", " ").replace("\\&", "&")
title = re.search(r"pdftitle=\{(.*?)\},pdfauthor", tex).group(1)
zmeta = dict(title=title,
             description_html=f"<p>{ab}</p><p>Interactive version: https://maps.tristanhotham.com/{SLUG}/. Data and code: https://github.com/Tristan-Hotham/{SLUG}. Blog post: to follow.</p>",
             keywords=["surnames", "family names", "Wikidata", "regional geography", "Great Britain", "Welsh surnames", "Cornish surnames", "toponymic surnames", "notability bias", "open data"],
             licence="cc-by-4.0",
             related=[dict(identifier=f"https://github.com/Tristan-Hotham/{SLUG}", relation="issupplementedby", resource_type="software"),
                      dict(identifier=f"https://maps.tristanhotham.com/{SLUG}/", relation="issupplementedby", resource_type="other"),
                      dict(identifier="https://www.wikidata.org/", relation="isderivedfrom", resource_type="dataset"),
                      dict(identifier="https://www.ordnancesurvey.co.uk/products/os-open-names", relation="isderivedfrom", resource_type="dataset"),
                      dict(identifier="https://nrscotland.gov.uk/publications/most-common-surnames-2025/", relation="isderivedfrom", resource_type="dataset")])
for v in (zmeta["title"], zmeta["description_html"], json.dumps(meta, ensure_ascii=False)): assert nodash(v)
json.dump(zmeta, open(os.path.join(z, "meta.json"), "w"), indent=1, ensure_ascii=False)
for fn in sorted(os.listdir(z)): print(fn, os.path.getsize(os.path.join(z, fn)))
