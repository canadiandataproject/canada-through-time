// Gaps worth fixing #1: long-term drinking water advisories on First Nations reserves (Indigenous Services Canada map data).
// Every advisory is drawn at the location ISC gives. The only computations: whether an advisory was in effect on a date
// (long-term start ≤ date < lift date), the monthly count of those (built in the pipeline), and years since the long-term
// start. Wording describes what happened; it does not assign blame or say what should be done.
const { Deck, OrthographicView, GeoJsonLayer, ScatterplotLayer, TextLayer } = window.deck;
const BASE = document.documentElement.dataset.base || '..';
const J = u => window.__DATA?.[u] ? Promise.resolve(window.__DATA[u]) : fetch(u.replace(/^\.\.\//, BASE + '/')).then(r => { if (!r.ok) throw new Error(u); return r.json(); });
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
const T = window.T || ((e) => e), FR = window.LANG === 'fr', L = a => FR ? a[1] || a[0] : a[0];
const PROVN = FR ? { ON: 'Ontario', MB: 'Manitoba', SK: 'Saskatchewan', AB: 'Alberta', BC: 'Colombie-Britannique', QC: 'Québec', NB: 'Nouveau-Brunswick', NS: 'Nouvelle-Écosse', PE: 'Île-du-Prince-Édouard', NL: 'Terre-Neuve-et-Labrador' }
  : { ON: 'Ontario', MB: 'Manitoba', SK: 'Saskatchewan', AB: 'Alberta', BC: 'British Columbia', QC: 'Quebec', NB: 'New Brunswick', NS: 'Nova Scotia', PE: 'Prince Edward Island', NL: 'Newfoundland and Labrador' };
const MON = FR ? ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juill.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'] : ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const fmtD = d => { if (!d) return T('date not given', 'date non indiquée'); const [y, m, dd] = d.split('-'); return FR ? `${+dd === 1 ? '1er' : +dd} ${MON[+m - 1]} ${y}` : `${MON[+m - 1]} ${+dd}, ${y}`; };
const fmtM = m => { const [y, mm] = m.split('-'); return `${MON[+mm - 1]} ${y}`; };
const fmtM1 = m => { const [y, mm] = m.split('-'); return FR ? `1er ${MON[+mm - 1]} ${y}` : `${MON[+mm - 1]} 1, ${y}`; };

let W, PROV, LAKES, el, deckI, ready, PAL;
const S = { i: null, sel: null, playing: false };   // i: index into W.in_effect (null = latest)
const css = n => getComputedStyle(document.body).getPropertyValue(n).trim();
const hex = h => { h = h.replace('#', ''); return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16)); };
function pal() { PAL = { land: hex(css('--land')), line: hex(css('--boundary')), water: hex(css('--ocean')), ink: hex(css('--ink-1')), halo: hex(css('--halo')), sel: hex(css('--select')),
  on: hex(css('--seq-5')), off: hex(css('--dec-2')), mute: hex(css('--ink-3')) }; }

const month = () => W.in_effect[S.i ?? W.in_effect.length - 1][0];
const dateOf = m => m + '-01';
const inEffect = (a, t) => a.set && a.set <= t && (a.active || a.lifted > t);
const yearsSince = (d, t) => d ? (new Date(t) - new Date(d)) / 3.15576e10 : null;
const today = () => W.in_effect.at(-1)[0] + '-01';

function build() {
  el = document.createElement('section'); el.id = 'wa'; el.className = 'nbx'; el.hidden = true; el.setAttribute('aria-label', T('Drinking water advisories', 'Avis sur la qualité de l’eau potable'));
  el.innerHTML = `<header class="nbx-top"><button class="nbx-back" aria-label="${T('Back to the national map', 'Retour à la carte nationale')}">← Canada</button>
    <div class="nbx-title"><span class="kick">${T('Gaps worth fixing · Indigenous Services Canada', 'Écarts à combler · Services aux Autochtones Canada')}</span><h1>${T('Drinking water advisories still in place', 'Les avis sur la qualité de l’eau potable toujours en vigueur')}</h1></div></header>
  <aside id="wa-side" class="nbx-side"></aside>
  <div id="wa-map" class="nbx-map" aria-label="${T('Map of long-term drinking water advisories', 'Carte des avis à long terme sur la qualité de l’eau potable')}"></div>
  <div id="wa-legend" class="nbx-legend"></div>
  <div id="wa-time" class="nbx-time"></div>
  <aside id="wa-detail" class="nbx-detail"></aside>
  <div id="wa-tip" class="nbx-tip" role="tooltip"></div>`;
  document.body.appendChild(el);
  el.querySelector('.nbx-back').onclick = close;
  el.addEventListener('click', e => {
    if (e.target.closest('[data-waplay]')) { togglePlay(); return; }
    const a = e.target.closest('[data-wa]'); if (a) { S.sel = a.dataset.wa; render(); return; }
    if (e.target.closest('[data-waclear]')) { S.sel = null; render(); }
  });
  el.addEventListener('input', e => { if (e.target.id === 'wa-month') { S.i = +e.target.value; S.playing = false; clearInterval(timer); render(true); } });
  addEventListener('keydown', e => { if (e.key === 'Escape' && !el.hidden) { if (S.sel) { S.sel = null; render(); } else close(); } });
  addEventListener('resize', () => { if (!el.hidden) fit(); });
}
let timer = null;
function togglePlay() { S.playing = !S.playing; clearInterval(timer);
  if (S.playing) { if (S.i == null || S.i >= W.in_effect.length - 1) S.i = 0; timer = setInterval(() => { if (S.i >= W.in_effect.length - 1) { S.playing = false; clearInterval(timer); S.i = null; render(); return; } S.i++; render(true); }, 110); }
  render(true); }
const clampTo = (v, b) => !b ? v : { ...v, target: [Math.max(b[0], Math.min(b[2], v.target[0])), Math.max(b[1], Math.min(b[3], v.target[1])), 0] };   // keep the view's centre over the mapped area
let PANB = null;
function fit() { if (!deckI) return; const box = el.querySelector('#wa-map').getBoundingClientRect(), b = [3900, 700, 8900, 2900];   // km, StatCan Lambert: the provinces, where the advisories are
  const z = Math.log2(Math.min(box.width / (b[2] - b[0]), box.height / (b[3] - b[1])) * 0.98); PANB = b;
  deckI.setProps({ initialViewState: { target: [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2, 0], zoom: z, minZoom: z - 0.5, maxZoom: z + 6 } }); }

function render(fast) {
  pal(); writeHash();
  const n = W.in_effect.length, i = S.i ?? n - 1, t = el.querySelector('#wa-time');
  if (!t.querySelector('#wa-month') || !fast) t.innerHTML = `<button data-waplay class="play" aria-label="${T('Play', 'Lecture')}">▶</button><b id="wa-y"></b><input id="wa-month" type="range" min="0" max="${n - 1}" step="1" aria-label="${T('Month', 'Mois')}">`;
  t.querySelector('#wa-month').value = i; t.querySelector('#wa-y').textContent = fmtM(month()); t.querySelector('[data-waplay]').textContent = S.playing ? '❚❚' : '▶';
  side(); detail(); legend(); drawMap();
}
function chart() {
  const Wd = 290, H = 96, s = W.in_effect, mx = Math.max(...s.map(r => r[1])), X = k => k / (s.length - 1) * Wd, Y = v => H - v / mx * H, k = S.i ?? s.length - 1;
  const d = s.map((r, j) => (j ? 'L' : 'M') + X(j).toFixed(1) + ' ' + Y(r[1]).toFixed(1)).join('');
  return `<svg class="wa-ch" viewBox="0 0 ${Wd} ${H + 18}" role="img" aria-label="${T('Long-term advisories in effect each month', 'Avis à long terme en vigueur chaque mois')}, ${fmtM(s[0][0])} – ${fmtM(s.at(-1)[0])}">
    <path d="${d}L${Wd} ${H}L0 ${H}Z" class="area"/><path d="${d}" class="ln"/><line x1="${X(k)}" x2="${X(k)}" y1="0" y2="${H}" class="cur"/><circle cx="${X(k)}" cy="${Y(s[k][1])}" r="3.5" class="dot"/>
    <text x="0" y="${H + 13}">${fmtM(s[0][0])}</text><text x="${Wd}" y="${H + 13}" text-anchor="end">${fmtM(s.at(-1)[0])}</text>
    <text x="6" y="${Y(s[0][1]) + 14}" class="ax">${s[0][1]}</text></svg>`;
}
function side() {
  const box = el.querySelector('#wa-side'), t = dateOf(month()), on = W.advisories.filter(a => inEffect(a, t)), latest = S.i == null || S.i === W.in_effect.length - 1;
  const liftedSince = W.advisories.filter(a => a.lifted && a.lifted <= t).length, s0 = W.in_effect[0];
  const longest = W.advisories.filter(a => a.active && a.set).sort((a, b) => a.set.localeCompare(b.set));
  const comms = new Set(on.map(a => a.community)).size;
  box.innerHTML = `<h2>${T('Water you can’t drink from the tap', 'De l’eau qu’on ne peut pas boire au robinet')}</h2>
    <p class="q">${T('A long-term drinking water advisory means a community’s public water system has been under a boil-water, do-not-consume or do-not-use advisory for more than a year.', 'Un avis à long terme sur la qualité de l’eau potable signifie que le réseau public d’eau d’une communauté fait l’objet d’un avis de faire bouillir l’eau, de ne pas consommer ou de ne pas utiliser depuis plus d’un an.')}</p>
    <div class="big"><b>${latest ? W.active : on.length}</b><span>${T('long-term advisories in effect', 'avis à long terme en vigueur')}${latest ? T(' (Indigenous Services Canada, latest file)', ' (Services aux Autochtones Canada, fichier le plus récent)') : T(` on ${fmtM1(month())}, in ${comms} communities`, ` le ${fmtM1(month())}, dans ${comms} communautés`)}</span></div>
    <p class="rng">${T(`${s0[1]} were in effect in ${fmtM(s0[0])}. <b>${liftedSince}</b> ${liftedSince === 1 ? 'has' : 'have'} been lifted since${latest ? '' : ` (to ${fmtM(month())})`}; others began after that date.`, `${s0[1]} étaient en vigueur en ${fmtM(s0[0])}. <b>${liftedSince}</b> ${liftedSince === 1 ? 'a été levé' : 'ont été levés'} depuis${latest ? '' : ` (jusqu’en ${fmtM(month())})`}; d’autres ont commencé après cette date.`)}</p>
    <h4>${T('In effect each month', 'En vigueur chaque mois')} <small>${T('long-term advisories', 'avis à long terme')}</small></h4>${chart()}
    <h4>${T('Longest in place', 'En place depuis le plus longtemps')}</h4>
    <div class="wa-list">${longest.slice(0, 8).map(a => `<button data-wa="${a.id}" class="${S.sel === a.id ? 'on' : ''}"><span>${esc(a.community)}<i>${esc(PROVN[a.prov] || a.prov)}</i></span><b>${Math.floor(yearsSince(a.set, today()))} ${T('yrs', 'ans')}</b></button>`).join('')}</div>
    <p class="def">${T(`Years counted from the date the advisory became long-term, to ${fmtM(W.in_effect.at(-1)[0])}. Tap one to see the system and the fix underway.`, `Années comptées à partir de la date où l’avis est devenu à long terme, jusqu’en ${fmtM(W.in_effect.at(-1)[0])}. Touchez-en un pour voir le réseau et les travaux en cours.`)}</p>
    <p class="def">${FR ? 'À long terme : en place depuis plus de 12 mois. Réseaux publics dans les réserves soutenus par Services aux Autochtones Canada; les puits privés, les réseaux non financés par le fédéral et les Premières Nations hors de ce programme (par exemple en Colombie-Britannique avec la Régie de la santé des Premières Nations, ou les nations autonomes) ne sont pas couverts de la même façon. Les comptes mensuels sont calculés à partir des dates de chaque avis; le fichier ne contient que les avis levés depuis novembre 2015. Un avis en vigueur n’a pas de date de début à long terme dans le fichier et n’est pas compté chaque mois. Un avis est placé aux coordonnées de sa communauté, car la longitude du fichier n’a pas de signe moins.' : W.notes.map(esc).join(' ')}</p>
    <p class="src">${T('Source: Indigenous Services Canada, map of lifted and active long-term drinking water advisories (map data file, English and French). The monthly line is counted from each advisory’s dates.', 'Source : Services aux Autochtones Canada, carte des avis à long terme sur la qualité de l’eau potable levés et en vigueur (fichier de données de la carte, en anglais et en français). La courbe mensuelle est comptée à partir des dates de chaque avis.')}</p>`;
}
function detail() {
  const box = el.querySelector('#wa-detail'), a = W.advisories.find(x => x.id === S.sel);
  if (!a) { box.innerHTML = `<h3>${T('Tap a dot', 'Touchez un point')}</h3><p class="hint">${T('Filled dots: advisories in effect on the date shown. Rings: advisories lifted by then. Drag the date or press play to watch them change.', 'Points pleins : avis en vigueur à la date affichée. Cercles : avis levés à cette date. Faites glisser la date ou appuyez sur lecture pour les voir changer.')}</p>`; return; }
  const yrs = a.active ? yearsSince(a.set, today()) : a.lifted && a.set ? yearsSince(a.set, a.lifted) : null;
  box.innerHTML = `<div class="dt-h"><div><span class="kick">${esc(PROVN[a.prov] || a.prov)} · ${a.active ? T('in effect', 'en vigueur') : T('lifted', 'levé')}</span><h3>${esc(a.community)}</h3></div><button data-waclear aria-label="${T('Close', 'Fermer')}">×</button></div>
    <div class="dt-pop"><b>${yrs != null ? Math.floor(yrs) + (Math.floor(yrs) === 1 ? T(' year', ' an') : T(' years', ' ans')) : '—'}</b> ${a.active ? T('as a long-term advisory so far', 'comme avis à long terme jusqu’ici') : T('as a long-term advisory before it was lifted', 'comme avis à long terme avant d’être levé')}</div>
    <dl class="wa-dl"><dt>${T('System', 'Réseau')}</dt><dd>${esc(a.system)}</dd><dt>${T('Advisory', 'Avis')}</dt><dd>${esc(L(a.type))}</dd><dt>${T('First issued', 'Émis la première fois')}</dt><dd>${fmtD(a.first)}</dd><dt>${T('Long-term since', 'À long terme depuis')}</dt><dd>${fmtD(a.set)}</dd>
    ${a.active ? `<dt>${T('Stage', 'Étape')}</dt><dd>${esc(L(a.phase))}</dd>` : `<dt>${T('Lifted', 'Levé le')}</dt><dd>${fmtD(a.lifted)}</dd>`}<dt>${a.active ? T('Fix underway', 'Travaux en cours') : T('What fixed it', 'Ce qui l’a réglé')}</dt><dd>${esc(L(a.fix)) || '—'}</dd><dt>${T('People served', 'Personnes desservies')}</dt><dd>${esc(L(a.people))}</dd></dl>
    <p class="src">${T('As described in ISC’s file. Stage “Complete” means the project is finished and the community is deciding when to lift the advisory, which in most provinces is the First Nation’s decision on public-health advice.', 'Tel que décrit dans le fichier de SAC. L’étape « Terminé » signifie que le projet est achevé et que la communauté décide quand lever l’avis; dans la plupart des provinces, c’est la Première Nation qui décide, sur avis de santé publique.')}</p>`;
}
function legend() {
  el.querySelector('#wa-legend').innerHTML = `<div class="lg-t">${T('Long-term drinking water advisories', 'Avis à long terme sur l’eau potable')}, ${fmtM1(month())}</div><div class="lg2"><span><i style="background:rgb(${PAL.on})"></i>${T('In effect', 'En vigueur')}</span><span><i style="background:transparent;border:1.5px solid rgb(${PAL.off})"></i>${T('Lifted by then', 'Levés à cette date')}</span></div><div class="lg-miss">${T('Public systems on reserve supported by ISC', 'Réseaux publics dans les réserves soutenus par SAC')}</div>`;
}
function drawMap() {
  const t = dateOf(month()), key = [t, S.sel, PAL.on].join('|');
  const data = W.advisories.filter(a => a.set || a.active).map(a => ({ a, on: inEffect(a, t) || (a.active && !a.set && (a.first || '') <= t), off: !!a.lifted && a.lifted <= t })).filter(d => d.on || d.off);
  data.sort((p, q) => p.on - q.on);
  const land = new GeoJsonLayer({ id: 'land', data: PROV, filled: true, stroked: true, getFillColor: [...PAL.land, 255], getLineColor: [...PAL.line, 120], lineWidthUnits: 'pixels', getLineWidth: 0.8, updateTriggers: { getFillColor: key } });
  const lakes = new GeoJsonLayer({ id: 'lakes', data: LAKES, filled: true, stroked: false, getFillColor: [...PAL.water, 255], updateTriggers: { getFillColor: key } });
  const dots = new ScatterplotLayer({ id: 'wa', data, pickable: true, getPosition: d => d.a.xy, radiusUnits: 'pixels', getRadius: d => d.a.id === S.sel ? 8 : d.on ? 5.5 : 4, stroked: true, filled: true, lineWidthUnits: 'pixels',
    getFillColor: d => d.on ? [...PAL.on, 235] : [0, 0, 0, 0], getLineColor: d => d.a.id === S.sel ? [...PAL.sel, 255] : d.on ? [...PAL.halo, 220] : [...PAL.off, 200], getLineWidth: d => d.a.id === S.sel ? 3 : d.on ? 1 : 1.4,
    updateTriggers: { getRadius: key, getFillColor: key, getLineColor: key, getLineWidth: key }, transitions: { getRadius: 150 } });
  const sel = data.filter(d => d.a.id === S.sel);
  const lab = new TextLayer({ id: 'wa-lab', data: sel, getPosition: d => d.a.xy, getText: d => d.a.community, getSize: 13, getColor: [...PAL.ink, 255], getPixelOffset: [10, 0], getTextAnchor: 'start', getAlignmentBaseline: 'center',
    fontFamily: 'IBM Plex Sans, sans-serif', fontWeight: 600, outlineWidth: 4, outlineColor: [...PAL.halo, 230], fontSettings: { sdf: true }, characterSet: 'auto', updateTriggers: { getText: key } });
  deckI.setProps({ layers: [land, lakes, dots, lab] });
  el.querySelector('#wa-map').style.background = `rgb(${PAL.water})`;
}
function tip({ object, x, y }) {
  const t = el.querySelector('#wa-tip'); if (!object) { t.style.display = 'none'; return; }
  const a = object.a; t.innerHTML = `<b>${esc(a.community)}</b><span>${object.on ? T(`In effect since ${fmtD(a.set)}`, `En vigueur depuis le ${fmtD(a.set)}`) : T(`Lifted ${fmtD(a.lifted)}`, `Levé le ${fmtD(a.lifted)}`)}</span>`;
  t.style.display = 'block'; t.style.left = x + 14 + 'px'; t.style.top = y + 14 + 'px';
}

function writeHash() { const h = `#wa=${S.i == null ? 'now' : month()}${S.sel ? '/a' + S.sel : ''}`; if (location.hash !== h) history.replaceState(null, '', h); }
function readHash() { const h = decodeURIComponent(location.hash); if (!h.startsWith('#wa=')) return; const [m, ...rest] = h.slice(4).split('/');
  const k = W.in_effect.findIndex(r => r[0] === m); S.i = k >= 0 && k < W.in_effect.length - 1 ? k : null;
  for (const r of rest) if (r[0] === 'a') S.sel = r.slice(1); }
let prevHash = '';
async function open(opts = {}) {
  if (!el) build();
  if (!location.hash.startsWith('#wa=')) prevHash = location.hash;
  el.hidden = false; document.body.classList.add('nb-on');
  if (!ready) ready = Promise.all([J('../data/gaps/water.json'), J('../data/provinces.geojson'), J('../data/lakes.geojson')]).then(([w, p, l]) => {
    W = w; const km = fc => { const c = x => typeof x[0] === 'number' ? [x[0] / 1e3, x[1] / 1e3] : x.map(c); return { ...fc, features: fc.features.map(f => ({ ...f, geometry: { ...f.geometry, coordinates: c(f.geometry.coordinates) } })) }; };
    PROV = km(p); LAKES = km(l); });
  await ready; readHash();
  if (opts.sel) S.sel = opts.sel;
  if (!deckI) deckI = new Deck({ parent: el.querySelector('#wa-map'), views: new OrthographicView({ flipY: false }), controller: { doubleClickZoom: true }, onViewStateChange: ({ viewState }) => clampTo(viewState, PANB), initialViewState: { target: [6400, 1800, 0], zoom: -3 },
    getCursor: ({ isHovering }) => isHovering ? 'pointer' : 'grab', onHover: tip,
    onClick: ({ object }) => { if (!object) return; S.sel = object.a.id; render(); }, style: { position: 'absolute', inset: 0 } });
  (window.__decks ||= {}).wa = deckI; window.MAPBTNS?.(el.querySelector('#wa-map'), () => deckI, fit);
  render(); requestAnimationFrame(fit);
}
function close() { S.playing = false; clearInterval(timer); el.hidden = true; document.body.classList.remove('nb-on'); history.replaceState(null, '', prevHash || location.pathname + location.search); dispatchEvent(new Event('nb-close')); }
window.WATER = { open, close, get state() { return S; }, get data() { return W; } };
