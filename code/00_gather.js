// Step 0. How the inputs were gathered (run in a browser console on any web page; retrieved 29 October 2026).
// Wikidata through the QLever SPARQL endpoint (CORS-open), plus a few English Wikipedia articles for context.
// The result was saved as surname_birthplaces_wd.json.gz. The NRS spreadsheet was downloaded from
// https://nrscotland.gov.uk/publications/most-common-surnames-2025/ (Open Government Licence v3.0).
const P = 'PREFIX wdt: <http://www.wikidata.org/prop/direct/> PREFIX wd: <http://www.wikidata.org/entity/> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> ';
const Q = P + `SELECT ?p ?fn ?fnL (MIN(?y0) AS ?y) (SAMPLE(?c) AS ?co) (SAMPLE(?s) AS ?sx) WHERE {
  ?p wdt:P31 wd:Q5 ; wdt:P734 ?fn ; wdt:P19 ?pl ; wdt:P569 ?d .
  ?pl wdt:P625 ?c . ?pl wdt:P17 ?cty .
  VALUES ?cty { wd:Q145 wd:Q174193 wd:Q179876 wd:Q230791 wd:Q161885 }
  ?fn rdfs:label ?fnL . FILTER(LANG(?fnL)="en")
  BIND(YEAR(?d) AS ?y0) FILTER(?y0>=1700)
  OPTIONAL { ?p wdt:P21 ?s }
} GROUP BY ?p ?fn ?fnL`;
(async () => {
  const t = await (await fetch('https://qlever.cs.uni-freiburg.de/api/wikidata?query=' + encodeURIComponent(Q), { headers: { Accept: 'text/tab-separated-values' } })).text();
  const fn = {}, rows = [];
  for (const line of t.split('\n').slice(1)) {
    const c = line.split('\t'); if (c.length < 5) continue;
    const m = c[4].match(/POINT\(([-\d.eE]+) ([-\d.eE]+)\)/); if (!m) continue;
    const p = +c[0].match(/Q(\d+)/)[1], f = +c[1].match(/Q(\d+)/)[1]; fn[f] = c[2].replace(/^"(.*)"@en$/, '$1');
    const s = c[5] || ''; const sx = s.includes('Q6581097') ? 'm' : s.includes('Q6581072') ? 'f' : s ? 'o' : '';
    rows.push([p, f, +c[3], +(+m[2]).toFixed(4), +(+m[1]).toFixed(4), sx]);
  }
  const B = { source: 'Wikidata via QLever', licence: 'CC0 1.0', retrieved: '2026-10-29', cols: ['person_qid', 'familyname_qid', 'birth_year', 'lat', 'lon', 'sex'], familynames: fn, rows, wikipedia: { licence: 'CC BY-SA 4.0', articles: {} } };
  for (const title of ['Welsh surnames', 'Cornish surnames', 'Hotham', 'Tre, Pol and Pen', 'Toponymic surname', 'Patronymic surname', 'Surname', 'Hotham, East Riding of Yorkshire']) {
    const j = await (await fetch('https://en.wikipedia.org/w/api.php?action=query&prop=revisions|info&inprop=url&rvprop=content|ids&rvslots=main&redirects=1&format=json&formatversion=2&origin=*&titles=' + encodeURIComponent(title))).json();
    const pg = j.query.pages[0]; B.wikipedia.articles[title] = { title: pg.title, url: pg.fullurl, revid: pg.revisions && pg.revisions[0].revid, text: pg.revisions ? pg.revisions[0].slots.main.content : null };
  }
  const blob = await new Response(new Blob([JSON.stringify(B)]).stream().pipeThrough(new CompressionStream('gzip'))).blob();
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'surname_birthplaces_wd.json.gz'; a.textContent = 'Download'; document.body.appendChild(a);
})();
