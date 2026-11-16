// Report card: the gaps worth fixing, in one place, for Canada or your province.
//   Report card  — each gap graded by where your province ranks among the ten (top two A, next two B, … last two F).
//   Hours of work — rent, groceries, gasoline and a new home priced in hours at the median wage, against a year you choose.
//   Who fixed it — for each gap: who is best now, who improved most, and dated changes that happened (sourced).
//   What would it take — what-if arithmetic with numbers you can change (not forecasts).
//   Canada vs peers — output per worker against ten countries and the OECD, and productivity and pay by province.
// Every value is read from the data files; the only arithmetic is ratios, differences, ranks and the what-if sums shown on screen.
// Dated events are listed because they happened; this page does not claim they caused any change in the numbers.
const BASE = document.documentElement.dataset.base || '..';
const J = u => window.__DATA?.[u] ? Promise.resolve(window.__DATA[u]) : fetch(u.replace(/^\.\.\//, BASE + '/')).then(r => { if (!r.ok) throw new Error(u); return r.json(); });
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
const T = window.T || ((e) => e), FR = window.LANG === 'fr';
const PROVS = ['NL', 'PE', 'NS', 'NB', 'QC', 'ON', 'MB', 'SK', 'AB', 'BC'];
const NAMES = FR ? { CAN: 'Canada', NL: 'Terre-Neuve-et-Labrador', PE: 'Île-du-Prince-Édouard', NS: 'Nouvelle-Écosse', NB: 'Nouveau-Brunswick', QC: 'Québec', ON: 'Ontario', MB: 'Manitoba', SK: 'Saskatchewan', AB: 'Alberta', BC: 'Colombie-Britannique', YT: 'Yukon', NT: 'Territoires du Nord-Ouest', NU: 'Nunavut' }
  : { CAN: 'Canada', NL: 'Newfoundland and Labrador', PE: 'Prince Edward Island', NS: 'Nova Scotia', NB: 'New Brunswick', QC: 'Quebec', ON: 'Ontario', MB: 'Manitoba', SK: 'Saskatchewan', AB: 'Alberta', BC: 'British Columbia', YT: 'Yukon', NT: 'Northwest Territories', NU: 'Nunavut' };
const SHORT = { NL: 'N.L.', PE: 'P.E.I.', NS: 'N.S.', NB: 'N.B.', QC: FR ? 'Qc' : 'Que.', ON: 'Ont.', MB: 'Man.', SK: 'Sask.', AB: 'Alta.', BC: FR ? 'C.-B.' : 'B.C.', CAN: 'Canada' };
const COUNTRY = { CAN: T('Canada', 'Canada'), USA: T('United States', 'États-Unis'), AUS: T('Australia', 'Australie'), GBR: T('United Kingdom', 'Royaume-Uni'), DEU: T('Germany', 'Allemagne'), FRA: T('France', 'France'), JPN: T('Japan', 'Japon'),
  NOR: T('Norway', 'Norvège'), NLD: T('Netherlands', 'Pays-Bas'), SWE: T('Sweden', 'Suède'), NZL: T('New Zealand', 'Nouvelle-Zélande'), OED: T('OECD members (average)', 'Membres de l’OCDE (moyenne)') };
const LOC = FR ? 'fr-CA' : 'en-CA';
const nf = (v, d = 0) => v == null || !isFinite(v) ? '—' : v.toLocaleString(LOC, { minimumFractionDigits: d, maximumFractionDigits: d });
const pctS = (v, d = 0) => (v > 0 ? '+' : v < 0 ? '−' : '') + nf(Math.abs(v), d) + (FR ? ' %' : '%');
const pctU = (v, d = 0) => nf(v, d) + (FR ? ' %' : '%');
const money = v => FR ? nf(v) + ' $' : '$' + nf(v);

let D = null, el, ready, prevHash = '';
let place = {}; try { place = JSON.parse(localStorage.getItem('ct.place') || '{}'); } catch (e) { place = {}; }
const S = { tab: 'card', g: PROVS.includes(place.g) ? place.g : 'CAN', base: 1997, city: null, panel: 1200, pph: null, peer: 'USA' };

// ---------------------------------------------------------------- data accessors
const pop = (g, y) => { const i = D.pop.dates.indexOf(`${y}-07-01`); return i < 0 ? null : D.pop.series[g]?.[i] ?? null; };
const doc = (g, y) => D.more.doctor[g]?.[y]?.v ?? null;
const docE = (g, y) => D.more.doctor[g]?.[y] ?? null;
const starts = (g, y) => D.hc.data[g]?.starts_total?.[y] ?? null;
const hpr = (g, y) => { let s = 0; for (let k = y - 4; k <= y; k++) { const v = starts(g, k); if (v == null) return null; s += v; } const a = pop(g, y), b = pop(g, y - 5); return a && b && a - b > 0 ? s / (a - b) : null; };
const H = g => D.hours.data[g];
const hoursX = (g, item, y, base) => { const h = H(g); const p1 = h?.[item]?.[y], p0 = h?.[item]?.[base], w1 = h?.wage?.[y], w0 = h?.wage?.[base]; return p1 && p0 && w1 && w0 ? (p1 / p0) / (w1 / w0) : null; };
const mainCity = g => D.calc.main_city[g] || null;
const rentH = (city, y) => D.hours.rent[city]?.y?.[y] ?? null;     // [rent $, hours]
const lp = (g, y) => D.prod.prov[g]?.lp?.[y] ?? null, comp = (g, y) => D.prod.prov[g]?.comp?.[y] ?? null;
const ur = (g, y) => D.lfs.data[g]?.[y]?.ur ?? null, csi = (g, y) => D.crime.data[g]?.[y]?.csi ?? null;
const peer = (c, k, y) => D.prod.peers[c]?.[k]?.[y] ?? null;
const lastY = (fn, g, from = 2026, to = 1990) => { for (let y = from; y >= to; y--) if (fn(g, y) != null) return y; return null; };

// ---------------------------------------------------------------- the gaps (report card rows)
// dir: +1 higher is better, −1 lower is better. y0: the year the trend is measured from.
const GAPS = () => [
  { id: 'nodoc', map: 'nodoc', t: T('No regular family doctor or nurse practitioner', 'Sans médecin de famille ni infirmière praticienne'), dir: -1, y: 2022, y0: 2015, v: doc, f: v => pctU(v, 1), u: T('of people 12+', 'des personnes de 12 ans et plus'), src: 'Statistics Canada 13-10-0096' },
  { id: 'hpr', map: 'hpr', t: T('Homes started per person added', 'Logements mis en chantier par personne ajoutée'), dir: 1, y: 2025, y0: 2020, v: hpr, f: v => nf(v, 2), u: T('homes per new resident, last 5 years', 'logement par nouveau résident, 5 dernières années'), src: 'Statistics Canada 34-10-0126, 17-10-0009' },
  { id: 'renth', map: 'renth', t: T('Rent in hours of work', 'Le loyer en heures de travail'), dir: -1, y: 2025, y0: 2020, v: (g, y) => rentH(mainCity(g), y)?.[1] ?? null, f: v => nf(v, 1) + ' h', u: g => T(`a month for an average 2-bedroom in ${mainCity(g) || '—'}`, `par mois pour un 2 chambres moyen à ${mainCity(g) || '—'}`), src: 'CMHC via Statistics Canada 34-10-0133; 14-10-0064' },
  { id: 'foodh', map: 'foodh', t: T('Groceries in hours of work, vs 1997', 'L’épicerie en heures de travail, par rapport à 1997'), dir: -1, y: 2025, y0: 2020, v: (g, y) => hoursX(g, 'food', y, 1997), f: v => '×' + nf(v, 2), u: T('1997 = ×1.00', '1997 = ×1,00'), src: 'Statistics Canada 18-10-0005, 14-10-0064' },
  { id: 'homeh', map: 'homeh', t: T('A new home in hours of work, vs 1997', 'Une maison neuve en heures de travail, par rapport à 1997'), dir: -1, y: 2025, y0: 2020, v: (g, y) => hoursX(g, 'home', y, 1997), f: v => '×' + nf(v, 2), u: T('1997 = ×1.00 · new houses only', '1997 = ×1,00 · maisons neuves seulement'), src: 'Statistics Canada 18-10-0205, 14-10-0064' },
  { id: 'lp', map: 'lp', t: T('Output per hour worked (business sector)', 'Production par heure travaillée (secteur des entreprises)'), dir: 1, y: 2024, y0: 2019, v: lp, f: v => money(v), u: T('chained 2017 dollars per hour', 'dollars enchaînés de 2017 par heure'), src: 'Statistics Canada 36-10-0480' },
  { id: 'ur', map: 'ur', t: T('Unemployment rate', 'Taux de chômage'), dir: -1, y: 2025, y0: 2020, v: ur, f: v => pctU(v, 1), u: T('of the labour force', 'de la population active'), src: 'Statistics Canada 14-10-0327' },
  { id: 'csi', map: 'csi', t: T('Police-reported crime severity', 'Gravité de la criminalité déclarée par la police'), dir: -1, y: 2024, y0: 2019, v: csi, f: v => nf(v, 1), u: T('index, Canada 2006 = 100', 'indice, Canada 2006 = 100'), src: 'Statistics Canada 35-10-0026' },
];
const GRADES = ['A', 'B', 'C', 'D', 'F'];
function ranked(gp, y) { return PROVS.map(g => [g, gp.v(g, y)]).filter(r => r[1] != null).sort((a, b) => gp.dir * (b[1] - a[1])); }
function gradeOf(gp, g) { const r = ranked(gp, gp.y), i = r.findIndex(x => x[0] === g); if (i < 0) return null; return { rank: i + 1, n: r.length, grade: GRADES[Math.min(4, Math.floor(i / r.length * 5))] }; }
const better = (gp, a, b) => a == null || b == null ? null : Math.abs(a - b) < 1e-9 ? 0 : gp.dir * (a - b) > 0 ? 1 : -1;

// ---------------------------------------------------------------- small SVG line chart
function lines(series, { w = 440, h = 180, fmt = v => nf(v), x0, x1, base, yLab = '' } = {}) {
  const pts = series.flatMap(s => s.pts.filter(p => p[1] != null)); if (!pts.length) return '';
  x0 ??= Math.min(...pts.map(p => p[0])); x1 ??= Math.max(...pts.map(p => p[0]));
  let lo = Math.min(...pts.map(p => p[1])), hi = Math.max(...pts.map(p => p[1])); if (base != null) { lo = Math.min(lo, base); hi = Math.max(hi, base); }
  const pad = (hi - lo) * 0.08 || 1; lo -= pad; hi += pad;
  const L = 44, R = 104, X = x => L + (x - x0) / Math.max(1, x1 - x0) * (w - L - R), Y = v => 8 + (hi - v) / (hi - lo) * (h - 30);
  const path = s => { let d = '', pen = false; for (const [x, v] of s.pts) { if (v == null) { pen = false; continue; } d += (pen ? 'L' : 'M') + X(x).toFixed(1) + ' ' + Y(v).toFixed(1); pen = true; } return d; };
  const last = s => s.pts.filter(p => p[1] != null).at(-1);
  const tick = [lo + pad, (lo + hi) / 2, hi - pad];
  return `<svg class="rc-chart" viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(yLab)}">
    ${tick.map(v => `<line x1="${L}" x2="${w - R}" y1="${Y(v)}" y2="${Y(v)}" class="gr"/><text x="${L - 6}" y="${Y(v) + 4}" text-anchor="end" class="ax">${fmt(v)}</text>`).join('')}
    ${base != null ? `<line x1="${L}" x2="${w - R}" y1="${Y(base)}" y2="${Y(base)}" class="base"/>` : ''}
    <text x="${L}" y="${h - 4}" class="ax">${x0}</text><text x="${w - R}" y="${h - 4}" text-anchor="end" class="ax">${x1}</text>
    ${series.map(s => `<path d="${path(s)}" class="ln ${s.cls || ''}" ${s.col ? `style="stroke:${s.col}"` : ''}/>`).join('')}
    ${(() => { const L = series.map(s => ({ s, p: last(s) })).filter(o => o.p && o.s.lab).map(o => ({ ...o, ly: Y(o.p[1]) + 4 })).sort((a, b) => a.ly - b.ly);
      for (let i = 1; i < L.length; i++) if (L[i].ly - L[i - 1].ly < 13) L[i].ly = L[i - 1].ly + 13;   // keep end labels from overlapping
      return L.map(({ s, p, ly }) => `<circle cx="${X(p[0])}" cy="${Y(p[1])}" r="3.5" class="dot ${s.cls || ''}" ${s.col ? `style="fill:${s.col}"` : ''}/><text x="${X(p[0]) + 7}" y="${ly}" class="lb ${s.cls || ''}">${esc(s.lab)}</text>`).join(''); })()}
  </svg>`;
}
const yrs = (a, b) => Array.from({ length: b - a + 1 }, (_, i) => a + i);

// ---------------------------------------------------------------- tabs
const TABS = [['card', T('Report card', 'Bulletin')], ['hours', T('Hours of work', 'Heures de travail')], ['fixed', T('Who fixed it', 'Qui a comblé l’écart')], ['take', T('What would it take', 'Ce qu’il faudrait')], ['peers', T('Canada vs peers', 'Le Canada et ses pairs')]];
const provSel = id => `<label class="rc-sel">${T('Province', 'Province')} <select id="${id}" data-rcg>${['CAN', ...PROVS].map(g => `<option value="${g}" ${g === S.g ? 'selected' : ''}>${NAMES[g]}</option>`).join('')}</select></label>`;
const mapLink = (m, y, g) => `<a class="rc-map" href="#${m}-${y}${g && g !== 'CAN' ? '-' + g : ''}" data-rcmap>${T('On the map →', 'Sur la carte →')}</a>`;

function cardTab() {
  const g = S.g, rows = GAPS();
  const body = rows.map(gp => {
    const v = gp.v(g, gp.y), v0 = gp.v(g, gp.y0), gr = g === 'CAN' ? null : gradeOf(gp, g), r = ranked(gp, gp.y), best = r[0], b = better(gp, v, v0);
    const unit = typeof gp.u === 'function' ? gp.u(g) : gp.u;
    const trend = b == null ? '' : b > 0 ? `<span class="tr up">▲ ${T('better than', 'mieux qu’en')} ${gp.y0}</span>` : b < 0 ? `<span class="tr dn">▼ ${T('worse than', 'moins bien qu’en')} ${gp.y0}</span>` : `<span class="tr">= ${gp.y0}</span>`;
    const strip = `<div class="rc-strip" aria-hidden="true">${r.map(([k], i) => `<i class="${k === g ? 'me' : ''}" title="${NAMES[k]}: ${gp.f(r[i][1])}">${SHORT[k]}</i>`).join('')}</div>`;
    return `<article class="rc-row"><div class="rc-grade ${gr ? 'g' + gr.grade : 'gn'}">${gr ? gr.grade : g === 'CAN' ? 'CA' : '—'}</div>
      <div class="rc-main"><h3>${gp.t}</h3>
        <p class="rc-v"><b>${v == null ? T('no value', 'aucune valeur') : gp.f(v)}</b> <span>${unit} · ${gp.y}</span> ${v0 != null && v != null ? `<span class="was">(${gp.f(v0)} ${T('in', 'en')} ${gp.y0})</span>` : ''} ${trend}</p>
        <p class="rc-rank">${gr ? T(`${gr.rank === 1 ? 'Best' : 'Ranked ' + gr.rank + ' of ' + gr.n} among the provinces.`, `${gr.rank === 1 ? 'Au 1er rang' : 'Au ' + gr.rank + 'e rang sur ' + gr.n} parmi les provinces.`) : ''} ${best ? T(`Best: ${NAMES[best[0]]}, ${gp.f(best[1])}.`, `Meilleur : ${NAMES[best[0]]}, ${gp.f(best[1])}.`) : ''}</p>
        ${strip}<p class="rc-src">${esc(gp.src)} ${mapLink(gp.map, gp.y, g)}</p></div></article>`;
  }).join('');
  const W = D.water, gradeCount = g === 'CAN' ? null : GRADES.map(x => rows.filter(gp => gradeOf(gp, g)?.grade === x).length);
  return `<div class="rc-top">${provSel('rc-g')}<p class="rc-how">${T('Grades are a rank among the ten provinces on the latest year: top two A, next two B, then C, D, F. Lower is better for doctors, rent, groceries, homes, unemployment and crime; higher is better for homes built and output per hour. Territories are missing from most of these tables.', 'Les notes correspondent au rang parmi les dix provinces pour la dernière année : les deux premières A, les deux suivantes B, puis C, D, F. Plus bas est mieux pour les médecins, le loyer, l’épicerie, les maisons, le chômage et la criminalité; plus haut est mieux pour les logements construits et la production par heure. Les territoires manquent dans la plupart de ces tableaux.')}</p></div>
    ${gradeCount ? `<div class="rc-sum"><b>${NAMES[g]}</b>: ${GRADES.map((x, i) => gradeCount[i] ? `${gradeCount[i]} × ${x}` : '').filter(Boolean).join(' · ')}</div>` : `<div class="rc-sum">${T('Canada as a whole: national values with the best province on each. Choose a province to see its grades.', 'Le Canada dans son ensemble : valeurs nationales et meilleure province pour chacune. Choisissez une province pour voir ses notes.')}</div>`}
    <article class="rc-row"><div class="rc-grade gn">💧</div><div class="rc-main"><h3>${T('Long-term drinking water advisories on First Nations public systems', 'Avis à long terme sur l’eau potable des réseaux publics des Premières Nations')}</h3>
      <p class="rc-v"><b>${W.active}</b> <span>${T('still in place', 'toujours en vigueur')}</span> <span class="was">(${W.in_effect[0][1]} ${T('in', 'en')} ${W.in_effect[0][0].slice(0, 4)})</span> <span class="tr up">▲ ${W.lifted} ${T('lifted', 'levés')}</span></p>
      <p class="rc-rank">${g !== 'CAN' ? T(`${W.advisories.filter(a => a.active && a.prov === g).length} of them in ${NAMES[g]}.`, `Dont ${W.advisories.filter(a => a.active && a.prov === g).length} : ${NAMES[g]}.`) : T('Not graded: a count of advisories does not compare provinces fairly.', 'Non noté : un nombre d’avis ne compare pas équitablement les provinces.')}</p>
      <p class="rc-src">Indigenous Services Canada <a class="rc-map" href="#wa=now" data-rcmap>${T('Open the map →', 'Ouvrir la carte →')}</a></p></div></article>
    ${body}`;
}

const ITEMS = () => [['food', T('Groceries', 'Épicerie'), T('Consumer Price Index, food', 'Indice des prix à la consommation, aliments')], ['gas', T('Gasoline', 'Essence'), T('Consumer Price Index, gasoline', 'Indice des prix à la consommation, essence')], ['home', T('A new house', 'Une maison neuve'), T('New Housing Price Index, house and land (new single-family houses only)', 'Indice des prix des logements neufs, maison et terrain (maisons unifamiliales neuves seulement)')]];
function hoursTab() {
  const g = S.g, base = S.base, YL = 2025, cities = Object.keys(D.hours.rent).filter(c => g === 'CAN' || D.hours.rent[c].prov === g).sort((a, b) => a.localeCompare(b, LOC));
  const city = cities.includes(S.city) ? S.city : (mainCity(g) && cities.includes(mainCity(g)) ? mainCity(g) : cities[0]);
  const rr = rentH(city, YL), r0 = rentH(city, base), rentSeries = yrs(1997, YL).map(y => [y, rentH(city, y)?.[1] ?? null]);
  const card = ([k, lab, src]) => { const x = hoursX(g, k, YL, base); if (x == null) return '';
    const ser = yrs(base, YL).map(y => [y, hoursX(g, k, y, base)]);
    return `<article class="hw-card"><h3>${lab}</h3><div class="hw-big ${x > 1.005 ? 'worse' : x < 0.995 ? 'better' : ''}">×${nf(x, 2)}</div>
      <p>${x > 1.005 ? T(`It takes <b>${pctU((x - 1) * 100)} more</b> hours of work at the median wage than in ${base}.`, `Il faut <b>${pctU((x - 1) * 100)} d’heures de plus</b> au salaire médian qu’en ${base}.`) : x < 0.995 ? T(`It takes <b>${pctU((1 - x) * 100)} fewer</b> hours of work at the median wage than in ${base}.`, `Il faut <b>${pctU((1 - x) * 100)} d’heures de moins</b> au salaire médian qu’en ${base}.`) : T(`About the same hours of work as in ${base}.`, `À peu près les mêmes heures de travail qu’en ${base}.`)}</p>
      ${lines([{ pts: ser, lab: '×' + nf(x, 2), cls: 'me' }], { h: 120, w: 360, fmt: v => '×' + nf(v, 2), base: 1 })}<p class="rc-src">${src}</p></article>`; };
  return `<div class="rc-top">${provSel('rc-g2')}<label class="rc-sel">${T('Compared with', 'Par rapport à')} <select id="rc-base">${yrs(1997, 2024).map(y => `<option ${y === base ? 'selected' : ''}>${y}</option>`).join('')}</select></label>
    <p class="rc-how">${T('Pick a year you remember: your first job, your first apartment. Prices are turned into hours at the median hourly wage, so inflation drops out. Above ×1.00, prices outran wages.', 'Choisissez une année marquante : votre premier emploi, votre premier appartement. Les prix sont convertis en heures au salaire horaire médian, ce qui neutralise l’inflation. Au-dessus de ×1,00, les prix ont dépassé les salaires.')}</p></div>
    <article class="hw-rent"><div><h3>${T('Rent: one month of an average 2-bedroom', 'Loyer : un mois pour un 2 chambres moyen')}</h3>
      <label class="rc-sel">${T('City', 'Ville')} <select id="rc-city">${cities.map(c => `<option ${c === city ? 'selected' : ''}>${esc(c)}</option>`).join('')}</select></label>
      ${rr ? `<div class="hw-big ${r0 && rr[1] > r0[1] ? 'worse' : 'better'}">${nf(rr[1], 1)} h</div><p>${T(`of work at the ${NAMES[D.hours.rent[city].prov]} median wage in ${YL} (${money(rr[0])} a month).`, `de travail au salaire médian de/du ${NAMES[D.hours.rent[city].prov]} en ${YL} (${money(rr[0])} par mois).`)}${r0 ? ' ' + T(`In ${base}: ${nf(r0[1], 1)} hours (${money(r0[0])}).`, `En ${base} : ${nf(r0[1], 1)} heures (${money(r0[0])}).`) : ''}</p>` : `<p>${T('No published rent for this city in that year.', 'Aucun loyer publié pour cette ville cette année-là.')}</p>`}</div>
      ${lines([{ pts: rentSeries, lab: nf(rr?.[1], 1) + ' h', cls: 'me' }], { h: 150, w: 420, fmt: v => nf(v) + ' h' })}
      <p class="rc-src">${T('Average rent in purpose-built rental apartments (CMHC October survey, via Statistics Canada 34-10-0133; existing tenants included, so new leases are often higher) ÷ median hourly wage of all employees in the province (14-10-0064).', 'Loyer moyen des appartements locatifs d’initiative privée (enquête d’octobre de la SCHL, via Statistique Canada 34-10-0133; locataires existants inclus, les nouveaux baux sont souvent plus chers) ÷ salaire horaire médian de tous les employés de la province (14-10-0064).')} ${mapLink('renth', YL)}</p></article>
    <div class="hw-grid">${ITEMS().map(card).join('')}</div>
    <p class="rc-note">${T('Price indexes follow the same goods over time, so each place is compared with its own past, not with other places. Wages: Statistics Canada 14-10-0064, median hourly wage, all employees.', 'Les indices de prix suivent les mêmes biens dans le temps : chaque lieu est comparé à son propre passé, pas aux autres. Salaires : Statistique Canada 14-10-0064, salaire horaire médian, tous les employés.')}</p>`;
}

// Dated events: what happened, with its source. Not a claim about cause.
const EVENTS = () => ({
  water: [
    ['2016-03-22', T('Budget 2016 commits $1.8 billion over five years to water and wastewater on reserves, with a goal of ending all long-term advisories on public systems by March 2021.', 'Le budget de 2016 engage 1,8 milliard de dollars sur cinq ans pour l’eau et les eaux usées dans les réserves, avec l’objectif d’éliminer tous les avis à long terme sur les réseaux publics d’ici mars 2021.'), 'https://www.canada.ca/en/indigenous-services-canada/news/2019/04/monthly-progress-update-through-march-2019-on-long-term-drinking-water-advisories-on-public-systems-on-reserve.html', 'Indigenous Services Canada'],
    ['2020-11-30', T('A further $1.5 billion is announced for clean drinking water in First Nations communities.', 'Un montant supplémentaire de 1,5 milliard de dollars est annoncé pour l’eau potable dans les communautés des Premières Nations.'), 'https://search.open.canada.ca/qpnotes/record/isc-sac%2CISC-2020-10090', 'Indigenous Services Canada (Question Period note)'],
    ['2021-03-31', T('The March 2021 goal is missed; the Parliamentary Budget Officer reviews the spending.', 'L’objectif de mars 2021 n’est pas atteint; le directeur parlementaire du budget examine les dépenses.'), 'https://publications.gc.ca/collections/collection_2022/dpb-pbo/YN5-236-2021-eng.pdf', 'Parliamentary Budget Officer'],
    ['2023-12-11', T('Bill C-61, a First Nations clean water act, is introduced. It passes the House of Commons but dies when Parliament is prorogued in January 2025.', 'Le projet de loi C-61 sur l’eau potable des Premières Nations est déposé. Il franchit la Chambre des communes mais meurt au Feuilleton à la prorogation de janvier 2025.'), 'https://ablawg.ca/2025/07/17/whos-afraid-of-the-proposed-first-nations-clean-water-act/', 'ABlawg (University of Calgary)'],
    ['2026-06-16', T('Bill C-37, the proposed First Nations Clean Water Act, is introduced in the House of Commons.', 'Le projet de loi C-37, Loi sur l’eau potable des Premières Nations, est déposé à la Chambre des communes.'), 'https://sac-isc.gc.ca/eng/1697555066364/1697555089256', 'Indigenous Services Canada'],
  ],
  nodoc: [
    ['2016-04-12', T('Quebec creates a single province-wide waiting list for a family doctor (Guichet d’accès à un médecin de famille).', 'Le Québec crée une liste d’attente unique pour un médecin de famille (Guichet d’accès à un médecin de famille).'), 'https://protecteurducitoyen.qc.ca/sites/default/files/pdf/rapports_d_intervention/ameliorer-processus-inscription-medecin-famille.pdf', 'Protecteur du citoyen (Québec)'],
    ['2016-11-01', T('Nova Scotia launches the Need a Family Practice registry, the first provincial count of people looking for a provider.', 'La Nouvelle-Écosse lance le registre Need a Family Practice, premier décompte provincial des personnes qui cherchent un prestataire.'), 'https://www.nshealth.ca/sites/default/files/documents/Need%20a%20Family%20Practice%20Registry%20February%202018.pdf', 'Nova Scotia Health'],
    ['2023-02-01', T('British Columbia starts a new way to pay family doctors (the Longitudinal Family Physician model): paid for time, visits and the size and complexity of their patient list, instead of per visit only.', 'La Colombie-Britannique adopte un nouveau mode de rémunération des médecins de famille (modèle LFP) : temps, visites, taille et complexité de la patientèle, plutôt que la seule rémunération à l’acte.'), 'https://news.gov.bc.ca/releases/2023HLTH0011-000127', 'Government of British Columbia'],
    ['2026-03-01', T('Nova Scotia’s registry lists 63,221 people waiting, down from 160,234 on June 1, 2024 (after the survey years shown on the map).', 'Le registre de la Nouvelle-Écosse compte 63 221 personnes en attente, contre 160 234 le 1er juin 2024 (après les années d’enquête montrées sur la carte).'), 'https://nshealth.ca/news-and-notices/need-family-practice-registry-update-march-2026', 'Nova Scotia Health'],
  ],
  hpr: [
    ['2023-03-17', T('The federal Housing Accelerator Fund opens: $4 billion to cities that change rules to allow more homes.', 'Ouverture du Fonds pour accélérer la construction de logements : 4 milliards de dollars aux villes qui modifient leurs règles pour permettre plus de logements.'), 'https://www.cmhc-schl.gc.ca/en/professionals/project-funding-and-mortgage-financing/funding-programs/all-funding-programs/housing-accelerator-fund/housing-accelerator-fund-backgrounder', 'CMHC'],
    ['2024-01-01', T('Edmonton’s new zoning bylaw takes effect: up to eight homes allowed on residential lots that were limited to one or two.', 'Le nouveau règlement de zonage d’Edmonton entre en vigueur : jusqu’à huit logements permis sur des terrains résidentiels auparavant limités à un ou deux.'), 'https://edmonton.ca/zoningbylawrenewal', 'City of Edmonton'],
    ['2023-11-30', T('British Columbia passes Bill 44: three to six homes allowed on lots zoned for single-family homes, with local rules due by June 30, 2024.', 'La Colombie-Britannique adopte le projet de loi 44 : de trois à six logements permis sur les terrains zonés unifamiliaux, avec des règles locales exigées d’ici le 30 juin 2024.'), 'https://www.ubcm.ca/sites/default/files/2024-02/UBCM%20Housing%20Summit%20-%20Bill%2044-%20Janae%20Enns%20and%20Don%20Lidstone.pdf', 'Union of BC Municipalities'],
  ],
});
function doorBlock(gp, evs, extra = '') {
  const r = ranked(gp, gp.y), imp = PROVS.map(g => [g, gp.v(g, gp.y0), gp.v(g, gp.y)]).filter(x => x[1] != null && x[2] != null).map(x => [...x, gp.dir * (x[2] - x[1])]).sort((a, b) => b[3] - a[3]);
  const best = r[0], worst = r.at(-1), mi = imp[0];
  return `<article class="door"><h3>${gp.t}</h3>
    <div class="door-data"><div><span class="k">${T('Best now', 'Meilleur aujourd’hui')}</span><b>${best ? NAMES[best[0]] : '—'}</b><span>${best ? gp.f(best[1]) + ' · ' + gp.y : ''}</span></div>
      <div><span class="k">${T(`Most improved since ${gp.y0}`, `Plus forte amélioration depuis ${gp.y0}`)}</span><b>${mi && mi[3] > 0 ? NAMES[mi[0]] : T('none improved', 'aucune amélioration')}</b><span>${mi && mi[3] > 0 ? gp.f(mi[1]) + ' → ' + gp.f(mi[2]) : ''}</span></div>
      <div><span class="k">${T('Furthest behind', 'Le plus en retard')}</span><b>${worst ? NAMES[worst[0]] : '—'}</b><span>${worst ? gp.f(worst[1]) : ''}</span></div></div>
    ${extra}
    ${evs?.length ? `<h4>${T('What changed, and when', 'Ce qui a changé, et quand')}</h4><ol class="door-ev">${evs.slice().sort((a, b) => a[0] < b[0] ? -1 : 1).map(([d, t, u, s]) => `<li><time>${d}</time><span>${t} <a href="${esc(u)}" target="_blank" rel="noopener">${esc(s)} ↗</a></span></li>`).join('')}</ol>` : ''}
    <p class="rc-src">${esc(gp.src)} ${mapLink(gp.map, gp.y)}</p></article>`;
}
function fixedTab() {
  const ev = EVENTS(), G = Object.fromEntries(GAPS().map(g => [g.id, g])), W = D.water, first = W.in_effect[0], low = W.in_effect.reduce((a, b) => b[1] < a[1] ? b : a);
  const water = `<article class="door"><h3>${T('Long-term drinking water advisories, First Nations public systems', 'Avis à long terme sur l’eau potable, réseaux publics des Premières Nations')}</h3>
    <div class="door-data"><div><span class="k">${T('In effect', 'En vigueur')} ${first[0].slice(0, 4)}</span><b>${first[1]}</b></div><div><span class="k">${T('Lowest month', 'Mois le plus bas')}</span><b>${low[1]}</b><span>${low[0]}</span></div><div><span class="k">${T('Still in place', 'Toujours en vigueur')}</span><b>${W.active}</b><span>${T(`${W.lifted} lifted in all`, `${W.lifted} levés en tout`)}</span></div></div>
    <h4>${T('What changed, and when', 'Ce qui a changé, et quand')}</h4><ol class="door-ev">${ev.water.map(([d, t, u, s]) => `<li><time>${d}</time><span>${t} <a href="${esc(u)}" target="_blank" rel="noopener">${esc(s)} ↗</a></span></li>`).join('')}</ol>
    <p class="rc-src">Indigenous Services Canada <a class="rc-map" href="#wa=now" data-rcmap>${T('Open the map →', 'Ouvrir la carte →')}</a></p></article>`;
  return `<p class="rc-how">${T('For each gap: who is doing best now, who improved most, and dated changes that happened along the way, each with its source. They are listed because they happened, not because this page shows they caused any change in the numbers.', 'Pour chaque écart : qui fait le mieux aujourd’hui, qui s’est le plus amélioré, et les changements datés survenus en cours de route, chacun avec sa source. Ils figurent ici parce qu’ils ont eu lieu, pas parce que cette page montre qu’ils ont causé un changement dans les chiffres.')}</p>
    ${water}${doorBlock(G.nodoc, ev.nodoc)}${doorBlock(G.hpr, ev.hpr)}${doorBlock(G.renth, [])}${doorBlock(G.foodh, [])}${doorBlock(G.lp, [])}`;
}

function takeTab() {
  const g = S.g, gg = g === 'CAN' ? 'CAN' : g;
  // family doctors
  const share = doc(gg, 2022), p12 = D.calc.pop12[gg]?.['2022'], without = share != null && p12 ? share / 100 * p12 : null, docs = without ? without / S.panel : null;
  // homes: last five years
  const yE = 2025, yS = 2020, added = pop(gg, yE) - pop(gg, yS), hh = D.hh.data[gg]?.[yE], pphData = hh ? pop(gg, yE) / hh : null, pph = S.pph ?? pphData;
  let st = 0, ok = true; for (let y = yS + 1; y <= yE; y++) { const v = starts(gg, y); if (v == null) ok = false; else st += v; }
  const need = pph ? added / pph : null, gap = need != null && ok ? need - st : null;
  const lastAdd = pop(gg, yE) - pop(gg, yE - 1), lastSt = starts(gg, yE);
  // groceries / homes: raise needed
  const food = hoursX(gg, 'food', 2025, S.base), home = hoursX(gg, 'home', 2025, S.base), gas = hoursX(gg, 'gas', 2025, S.base);
  const raise = x => x == null ? '—' : x > 1 ? T(`a <b>${pctU((x - 1) * 100)}</b> higher median wage`, `un salaire médian <b>${pctU((x - 1) * 100)}</b> plus élevé`) : T('no raise: wages already kept up', 'aucune hausse : les salaires ont suivi');
  // productivity
  const c = peer('CAN', 'perworker', 2025) ?? peer('CAN', 'perworker', 2024), u = peer(S.peer, 'perworker', 2025) ?? peer(S.peer, 'perworker', 2024);
  return `<div class="rc-top">${provSel('rc-g3')}<p class="rc-how">${T('What-if arithmetic with numbers you can change. Not forecasts, and not advice: each one shows the size of a gap in plain units.', 'Calculs hypothétiques avec des chiffres que vous pouvez modifier. Ni prévisions ni conseils : chacun montre l’ampleur d’un écart en unités simples.')}</p></div>
  <div class="calc-grid">
    <article class="calc"><h3>${T('Family doctors', 'Médecins de famille')}</h3>
      <p>${share != null ? T(`In 2022, <b>${pctU(share, 1)}</b> of people 12 and over in ${NAMES[gg]} said they had no regular provider: about <b>${nf(Math.round(without / 1000) * 1000)}</b> people (share × ${nf(p12)} residents aged 12+ on July 1, 2022).`, `En 2022, <b>${pctU(share, 1)}</b> des personnes de 12 ans et plus en/au ${NAMES[gg]} disaient ne pas avoir de prestataire régulier : environ <b>${nf(Math.round(without / 1000) * 1000)}</b> personnes (part × ${nf(p12)} résidents de 12 ans et plus au 1er juillet 2022).`) : T('No survey value for this place.', 'Aucune valeur d’enquête pour ce lieu.')}</p>
      <label class="rc-range">${T('Patients one family doctor takes on (your assumption)', 'Patients qu’un médecin de famille prend en charge (votre hypothèse)')} <input type="range" id="rc-panel" min="500" max="2500" step="50" value="${S.panel}"><output>${nf(S.panel)}</output></label>
      <div class="calc-out">${docs ? T(`≈ <b>${nf(Math.ceil(docs))}</b> more full-time family doctors (or nurse practitioners) would be needed to take everyone on.`, `≈ <b>${nf(Math.ceil(docs))}</b> médecins de famille (ou infirmières praticiennes) de plus seraient nécessaires pour prendre tout le monde en charge.`) : '—'}</div>
      <p class="rc-src">${T('Survey population excludes people on reserves, in institutions and full-time Canadian Forces members, so the count is approximate. Some people without a provider are not looking for one.', 'La population de l’enquête exclut les personnes vivant dans les réserves, en établissement et les membres à temps plein des Forces canadiennes : le nombre est approximatif. Certaines personnes sans prestataire n’en cherchent pas.')} Statistics Canada 13-10-0096, 17-10-0005.</p></article>
    <article class="calc"><h3>${T('Homes', 'Logements')}</h3>
      <p>${T(`${NAMES[gg]} added <b>${nf(added)}</b> people from July ${yS} to July ${yE} and started <b>${ok ? nf(st) : '—'}</b> homes in ${yS + 1}–${yE}.`, `${NAMES[gg]} a gagné <b>${nf(added)}</b> personnes de juillet ${yS} à juillet ${yE} et mis en chantier <b>${ok ? nf(st) : '—'}</b> logements en ${yS + 1}–${yE}.`)}</p>
      <label class="rc-range">${T('People per home', 'Personnes par logement')} ${pphData ? T(`(${NAMES[gg]} average in ${yE}: ${nf(pphData, 2)})`, `(moyenne ${yE} : ${nf(pphData, 2)})`) : ''} <input type="range" id="rc-pph" min="1.8" max="3.2" step="0.05" value="${nf(pph, 2).replace(',', '.')}"><output>${nf(pph, 2)}</output></label>
      <div class="calc-out">${gap != null ? (gap > 0 ? T(`Housing those new residents at ${nf(pph, 2)} per home takes <b>${nf(need)}</b> homes: <b>${nf(gap)}</b> more than were started.`, `Loger ces nouveaux résidents à ${nf(pph, 2)} par logement demande <b>${nf(need)}</b> logements : <b>${nf(gap)}</b> de plus que ceux mis en chantier.`) : T(`Housing those new residents at ${nf(pph, 2)} per home takes ${nf(need)} homes; starts covered that, with ${nf(-gap)} to spare.`, `Loger ces nouveaux résidents à ${nf(pph, 2)} par logement demande ${nf(need)} logements; les mises en chantier ont suffi, avec ${nf(-gap)} de surplus.`)) : '—'}
        ${lastSt != null && pph ? `<br>${T(`Last year alone: ${nf(lastAdd)} people added → ${nf(lastAdd / pph)} homes at that rate; ${nf(lastSt)} were started.`, `L’an dernier seulement : ${nf(lastAdd)} personnes de plus → ${nf(lastAdd / pph)} logements à ce taux; ${nf(lastSt)} ont été mis en chantier.`)}` : ''}</div>
      <p class="rc-src">${T('Starts are homes begun, not finished. Some new residents move into existing homes; some homes replace demolished ones.', 'Les mises en chantier sont des logements commencés, pas terminés. Certains nouveaux résidents s’installent dans des logements existants; certains logements en remplacent d’autres démolis.')} Statistics Canada 34-10-0126, 17-10-0009, 17-10-0159.</p></article>
    <article class="calc"><h3>${T('Wages vs prices', 'Salaires et prix')}</h3>
      <label class="rc-sel">${T('Back to', 'Revenir à')} <select id="rc-base2">${yrs(1997, 2024).map(y => `<option ${y === S.base ? 'selected' : ''}>${y}</option>`).join('')}</select></label>
      <p>${T(`To buy the same groceries in the same hours of work as in ${S.base} would take ${raise(food)}.`, `Acheter la même épicerie avec les mêmes heures de travail qu’en ${S.base} demanderait ${raise(food)}.`)}</p>
      <p>${T(`For a new house: ${raise(home)}. For gasoline: ${raise(gas)}.`, `Pour une maison neuve : ${raise(home)}. Pour l’essence : ${raise(gas)}.`)}</p>
      <p class="rc-src">${T('Median hourly wage, 2025, against the same price index.', 'Salaire horaire médian, 2025, par rapport au même indice de prix.')} Statistics Canada 18-10-0005, 18-10-0205, 14-10-0064.</p></article>
    <article class="calc"><h3>${T('Output per worker', 'Production par travailleur')}</h3>
      <label class="rc-sel">${T('Compared with', 'Par rapport à')} <select id="rc-peer">${Object.keys(COUNTRY).filter(k => k !== 'CAN').map(k => `<option value="${k}" ${k === S.peer ? 'selected' : ''}>${COUNTRY[k]}</option>`).join('')}</select></label>
      <div class="calc-out">${c && u ? (u > c ? T(`Matching ${COUNTRY[S.peer]} would take <b>${pctU((u / c - 1) * 100)}</b> more output per worker in Canada.`, `Rattraper ${COUNTRY[S.peer]} demanderait <b>${pctU((u / c - 1) * 100)}</b> de production de plus par travailleur au Canada.`) : T(`Canada is already ${pctU((c / u - 1) * 100)} ahead of ${COUNTRY[S.peer]} per worker.`, `Le Canada devance déjà ${COUNTRY[S.peer]} de ${pctU((c / u - 1) * 100)} par travailleur.`)) : '—'}</div>
      <p class="rc-src">${T('GDP per person employed, constant 2021 dollars at purchasing power parity. World Bank, World Development Indicators (CC BY 4.0).', 'PIB par personne occupée, dollars constants de 2021 à parité de pouvoir d’achat. Banque mondiale, Indicateurs du développement dans le monde (CC BY 4.0).')}</p></article>
  </div>`;
}

const PEERCOL = { CAN: 'var(--accent)', USA: 'var(--ink-1)', OED: 'var(--ink-3)' };
function peersTab() {
  const P = D.prod.peers, Y1 = Math.max(...Object.values(P).map(c => Math.max(...Object.keys(c.perworker || {}).map(Number)))), y = P.CAN.perworker[Y1] ? Y1 : Y1 - 1;
  const ser = k => ['CAN', 'USA', 'OED', S.peer].filter((v, i, a) => a.indexOf(v) === i).map(c => ({ pts: yrs(1991, y).map(t => [t, peer(c, k, t)]), lab: COUNTRY[c].replace(/ \(.*\)/, ''), col: PEERCOL[c] || 'var(--dec-2)', cls: c === 'CAN' ? 'me' : '' }));
  const bars = Object.keys(P).map(c => [c, peer(c, 'perworker', y)]).filter(r => r[1]).sort((a, b) => b[1] - a[1]), mx = bars[0][1];
  const rel = yrs(1991, y).map(t => [t, peer('CAN', 'perworker', t) && peer('USA', 'perworker', t) ? peer('CAN', 'perworker', t) / peer('USA', 'perworker', t) * 100 : null]);
  const g = S.g === 'CAN' ? 'CAN' : S.g, pb = ['CAN', ...PROVS, 'YT', 'NT', 'NU'].map(k => [k, lp(k, 2024)]).filter(r => r[1]).sort((a, b) => b[1] - a[1]), pmx = pb[0][1];
  const lp0 = lp(g, 1997), lp1 = lp(g, 2024), c0 = comp(g, 1997), c1 = comp(g, 2024);
  return `<div class="rc-top"><label class="rc-sel">${T('Highlight', 'Mettre en évidence')} <select id="rc-peer2">${Object.keys(COUNTRY).filter(k => !['CAN', 'USA', 'OED'].includes(k)).map(k => `<option value="${k}" ${k === S.peer ? 'selected' : ''}>${COUNTRY[k]}</option>`).join('')}</select></label>
    <p class="rc-how">${T('How much the economy produces for each person working, in the same dollars everywhere (purchasing power parity), from 1991. Per worker, not per hour: places where people work fewer hours a year look lower per worker.', 'Ce que l’économie produit pour chaque personne qui travaille, en dollars comparables partout (parité de pouvoir d’achat), depuis 1991. Par travailleur, pas par heure : là où l’on travaille moins d’heures par an, le niveau par travailleur paraît plus bas.')}</p></div>
  <div class="peer-grid"><article class="calc"><h3>${T('Output per worker, 1991–', 'Production par travailleur, 1991–')}${y}</h3>${lines(ser('perworker'), { fmt: v => '$' + nf(v / 1000) + 'K' })}<p class="rc-src">World Bank WDI, SL.GDP.PCAP.EM.KD (CC BY 4.0)</p></article>
    <article class="calc"><h3>${T('Canada as a share of the United States, per worker', 'Le Canada en proportion des États-Unis, par travailleur')}</h3>${lines([{ pts: rel, lab: pctU(rel.at(-1)[1]), cls: 'me' }], { fmt: v => pctU(v), base: 100 })}<p class="rc-note">${T(`${pctU(rel[0][1])} in 1991, ${pctU(rel.at(-1)[1])} in ${y}.`, `${pctU(rel[0][1])} en 1991, ${pctU(rel.at(-1)[1])} en ${y}.`)}</p></article>
    <article class="calc"><h3>${T('Ranking', 'Classement')}, ${y}</h3><div class="bars">${bars.map(([c, v]) => `<div class="bar ${c === 'CAN' ? 'me' : ''}"><span>${COUNTRY[c]}</span><i style="width:${(v / mx * 100).toFixed(1)}%"></i><b>$${nf(v / 1000)}K</b></div>`).join('')}</div></article>
    <article class="calc"><h3>${T('Output per hour worked, by province, 2024', 'Production par heure travaillée, par province, 2024')}</h3><div class="bars">${pb.map(([k, v]) => `<div class="bar ${k === g ? 'me' : ''}"><span>${NAMES[k]}</span><i style="width:${(v / pmx * 100).toFixed(1)}%"></i><b>${money(v)}</b></div>`).join('')}</div>
      <p class="rc-note">${provSel('rc-g4')}</p>
      ${lp0 && lp1 && c0 && c1 ? `<p>${T(`${NAMES[g]}, 1997 → 2024: output per hour ${pctS((lp1 / lp0 - 1) * 100)} (after inflation); pay per hour ${pctS((c1 / c0 - 1) * 100)} before inflation.`, `${NAMES[g]}, 1997 → 2024 : production par heure ${pctS((lp1 / lp0 - 1) * 100)} (après inflation); rémunération par heure ${pctS((c1 / c0 - 1) * 100)} avant inflation.`)}</p>` : ''}
      <p class="rc-src">${T('Business sector, chained 2017 dollars per hour. High values in resource provinces and the territories reflect oil, gas and mining. Statistics Canada 36-10-0480.', 'Secteur des entreprises, dollars enchaînés de 2017 par heure. Les valeurs élevées des provinces productrices et des territoires reflètent le pétrole, le gaz et les mines. Statistique Canada 36-10-0480.')} ${mapLink('lp', 2024, g)}</p></article></div>`;
}

// ---------------------------------------------------------------- shell
function build() {
  el = document.createElement('section'); el.id = 'rc'; el.className = 'world'; el.hidden = true; el.setAttribute('aria-label', T('Report card', 'Bulletin'));
  el.innerHTML = `<header class="w-head"><div class="w-title"><span class="kick">${T('Gaps worth fixing', 'Écarts à combler')}</span><h1>${T('How is your province doing?', 'Comment s’en tire votre province?')}</h1></div><nav class="w-tabs">${TABS.map(([k, l]) => `<button data-rct="${k}">${l}</button>`).join('')}</nav></header><div class="w-body" id="rc-body"></div>`;
  document.body.appendChild(el);
  el.addEventListener('click', e => {
    const t = e.target.closest('[data-rct]'); if (t) { S.tab = t.dataset.rct; render(); el.querySelector('#rc-body').scrollTop = 0; return; }
    const a = e.target.closest('[data-rcmap]'); if (a) { e.preventDefault(); const h = a.getAttribute('href'); close(); if (h.startsWith('#wa=')) window.SHELL ? window.SHELL.go('wa') : window.WATER?.open(); else { location.hash = h; } }
  });
  el.addEventListener('input', e => {
    const id = e.target.id;
    if (e.target.matches('[data-rcg]')) { S.g = e.target.value; S.city = null; S.pph = null; render(); return; }
    if (id === 'rc-base' || id === 'rc-base2') { S.base = +e.target.value; render(); return; }
    if (id === 'rc-city') { S.city = e.target.value; render(); return; }
    if (id === 'rc-peer' || id === 'rc-peer2') { S.peer = e.target.value; render(); return; }
    if (id === 'rc-panel') { S.panel = +e.target.value; render(true); return; }
    if (id === 'rc-pph') { S.pph = +e.target.value; render(true); return; }
  });
  addEventListener('keydown', e => { if (e.key === 'Escape' && !el.hidden) close(); });
}
function render(keepFocus) {
  const f = keepFocus && document.activeElement?.id;
  el.querySelectorAll('[data-rct]').forEach(b => { const on = b.dataset.rct === S.tab; b.classList.toggle('on', on); b.setAttribute('aria-current', on ? 'page' : 'false'); });
  const fn = { card: cardTab, hours: hoursTab, fixed: fixedTab, take: takeTab, peers: peersTab }[S.tab] || cardTab;
  let html; try { html = fn(); } catch (err) { console.error(err); html = `<p>${T('Something went wrong drawing this page.', 'Un problème est survenu à l’affichage.')}</p>`; }
  el.querySelector('#rc-body').innerHTML = `<div class="rc rc-${S.tab}">${html}</div>`;
  if (f) { const n = document.getElementById(f); n?.focus(); }
  writeHash();
}
function writeHash() { const h = `#rc=${S.tab}/${S.g}${S.tab === 'hours' || S.tab === 'take' ? '/' + S.base : ''}`; if (location.hash !== h) history.replaceState(null, '', h); }
function readHash() { const h = decodeURIComponent(location.hash); if (!h.startsWith('#rc=')) return; const [t, g, b] = h.slice(4).split('/');
  if (TABS.some(x => x[0] === t)) S.tab = t; if (g === 'CAN' || PROVS.includes(g)) S.g = g; if (+b >= 1997 && +b <= 2024) S.base = +b; }
async function open(opts = {}) {
  if (!el) build();
  if (!location.hash.startsWith('#rc=')) prevHash = location.hash;
  el.hidden = false; document.body.classList.add('nb-on');
  if (!ready) ready = Promise.all(['../data/gaps/more.json', '../data/gaps/hours.json', '../data/gaps/productivity.json', '../data/gaps/calc.json', '../data/gaps/water.json', '../data/population.json',
    '../data/housing/construction.json', '../data/housing/households.json', '../data/more/lfs.json', '../data/more/crime.json'].map(J))
    .then(([more, hours, prod, calc, water, pop, hc, hh, lfs, crime]) => { D = { more, hours, prod, calc, water, pop, hc, hh, lfs, crime }; });
  await ready; readHash();
  if (opts.tab) S.tab = opts.tab; if (opts.g) S.g = opts.g;
  render(); el.querySelector('#rc-body').scrollTop = 0;
}
function close() { if (!el) return; el.hidden = true; document.body.classList.remove('nb-on'); history.replaceState(null, '', prevHash && !prevHash.startsWith('#rc=') ? prevHash : location.pathname + location.search); dispatchEvent(new Event('nb-close')); }
window.REPORT = { open, close, get state() { return S; }, get data() { return D; } };
if (location.hash.startsWith('#rc=')) open();
