# Has your surname left home?

Where notable people with each surname were born in Great Britain: born 1800 to 1899 against born 1950 or later, from Wikidata.

Interactive page: https://maps.tristanhotham.com/surname-birthplaces/
Paper: https://doi.org/10.5281/zenodo.23761427
Blog post: https://blog.tristanhotham.com/2026/10/29/surname-birthplaces/

**Read this first.** There is no open dataset of surnames by place for Britain (the 1881 census with names is available only under a UK Data Service special licence, and modern name registers are not open). This study uses the open alternative: notable people in Wikidata with a family name and a birthplace. That sample is skewed towards men, London and elites. It shows where notable bearers of a surname were born, not where most bearers lived.

## Headline results

- {{overview.n_people|int}} notable people born in Great Britain since 1700, with {{overview.n_surnames|int}} surnames: {{overview.eras.1800s.n|int}} born in the 1800s and {{overview.eras.since1950.n|int}} born since 1950.
- The sample is skewed: women are {{page.women_1800s|pct}} of those born in the 1800s and {{page.women_since1950|pct}} of those born since 1950; {{page.london_1800s|pct}} of 1800s births were in London.
- For {{regional.n_surnames|int}} surnames with at least {{regional.nmin}} notable births in both eras, regional clustering beyond chance fell from {{page.excess_1800s_pts}} to {{page.excess_since1950_pts}} percentage points at the median ({{page.excess_drop|pct}} lower); {{regional.excess_drop_share|pct}} of surnames became less regional.
- Welsh patronymic surnames (Jones, Davies, Evans and 11 more): {{welsh.eras.1800s.share_wales|pct}} of 1800s notables born in Wales, {{welsh.eras.since1950.share_wales|pct}} of those born since 1950 (all notables: {{welsh.eras.1800s.base_wales|pct}} and {{welsh.eras.since1950.base_wales|pct}}).
- Tre-, Pol- and Pen- surnames: {{cornish.eras.1800s.share_cornwall|pct1}} born in Cornwall in the 1800s, {{cornish.eras.since1950.share_cornwall|pct1}} since 1950 (all notables: under 1%).
- Surnames that are British place names: born within {{placenames.radius_km|int}} km of a namesake {{placenames.eras.1800s.lift|f1}} times as often as chance in the 1800s, {{placenames.eras.since1950.lift|f1}} times since 1950.
- Scotland's {{nrs.n}} commonest surnames in the 2025 registers against notable births since 1950: Spearman correlation {{nrs.spearman_since1950|f2}}.
- Hotham: {{hotham.n_gb|int}} notable births in Great Britain, both in the 1800s; Hotham village is in the East Riding of Yorkshire.

## Files

- `index.html`: the interactive page (single file; loads `data/page/*.json`). `header.png`: social card.
- `data/results.json`: every number used in the page, paper, blog and collage.
- `data/surname_era_region.csv`: notable births by surname, era and region (aggregate counts).
- `data/surname_regional.csv`: regional clustering, home region and centre-of-gravity shift for the {{regional.n_surnames|int}} surnames with at least {{regional.nmin}} births in both eras.
- `data/region_signature_surnames.csv`: the five most over-represented surnames in each region, 1800s and since 1950.
- `data/welsh_patronymics.csv`, `data/placename_surnames.csv`, `data/nrs_scotland_comparison.csv`, `data/eras_overview.csv`.
- `data/page/`: compact files for the map (births by surname, era and birthplace for surnames with at least two notable births; birthplaces; place labels; outline).
- `code/`: the scripts, run in order (below). `release/`: paper, blog post and Zenodo files. `reddit/`: collage.

No file lists individual people: everything published is a count of notable births.

## How to rerun

Inputs (paths can be changed with environment variables, see `code/common.py`): the Wikidata bundle made by `code/00_gather.js` (run in a browser), the NRS spreadsheet, OS Open Names as a tab separated file, and ONS local authority boundaries (`LTLA`).

```
python3 code/01_prepare.py      # Wikidata people to Great Britain birthplaces (OS Open Names)
python3 code/02_analyse.py      # all measures, data/results.json and CSVs
python3 code/03_page_data.py    # data/page/
python3 code/04_build_site.py   # index.html
FONT_DIR=... python3 code/05_header.py
FONT_DIR=... python3 code/06_figures.py
python3 code/07_paper.py        # xelatex
python3 code/08_release.py      # README, blog post, Zenodo folder
python3 reddit/collage.py
```

## Sources and licences

- Wikidata, CC0 1.0, queried through QLever (University of Freiburg) on {{meta.retrieved}}.
- OS Open Names, Ordnance Survey: contains OS data © Crown copyright and database right 2026, Open Government Licence v3.0.
- National Records of Scotland, Most common surnames 2025, © Crown copyright, Open Government Licence v3.0.
- ONS local authority district boundaries (outline), Open Government Licence v3.0.
- English Wikipedia articles (Welsh surnames; Tre, Pol and Pen; Hotham; Hotham, East Riding of Yorkshire), CC BY-SA 4.0, used for context and for the list of Welsh patronymic surnames.

Code: MIT. Data, text and figures: CC BY 4.0 (keep the source credits above). See `LICENSE`.

## Citation

Hotham, T. (2026) Has Your Surname Left Home? Birthplaces of Notable People by Surname in Great Britain, 1800 to 1899 and 1950 Onwards. Zenodo. https://doi.org/10.5281/zenodo.23761427

Dr Tristan Hotham, Independent researcher, ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
