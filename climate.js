// Climate: ECCC homogenized station records (AHCCD) and WGMS glacier mass balance.
// Station values are published annual figures. The only computations here are: each station's 1961–1990 average (needs 25 of
// the 30 years), differences from it, 10-year averages (need 8 of 10 years), counts of stations, and running sums of
// glacier balances. Every one is stated in the panel. Missing years stay missing.
const { Deck, OrthographicView, GeoJsonLayer, ScatterplotLayer, TextLayer } = window.deck;
const BASE = document.documentElement.dataset.base || '..';
const J = u => window.__DATA?.[u] ? Promise.resolve(window.__DATA[u]) : fetch(u.replace(/^\.\.\//, BASE + '/')).then(r => { if (!r.ok) throw new Error(u); return r.json(); });
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
const nf = (v, dp = 0) => v.toLocaleString('en-CA', { minimumFractionDigits: dp, maximumFractionDigits: dp });
const sgn = (v, dp = 1, u = '') => (v > 0 ? '+' : v < 0 ? '−' : '±') + nf(Math.abs(v), dp) + u;

let A, G, F, PROV, LAKES, el, deckI, ready, fready;
const S = { mode: 'temp', y: 2020, avg: true, st: null, gl: null, playing: false };
const MODES = [['temp', 'Temperature'], ['precip', 'Precipitation'], ['trend', 'Long-term warming'], ['ice', 'Glaciers'], ['forest', 'Forests']];
const yr = (s, k) => s[k] ? s[k][0] : null;
const at = (s, k, y) => { const p = s[k]; if (!p) return null; const i = y - p[0]; return i >= 0 && i < p[1].length ? p[1][i] : null; };
function baseline(s, k) { const key = '_b' + k; if (key in s) return s[key]; let n = 0, sum = 0; for (let y = 1961; y <= 1990; y++) { const v = at(s, k, y); if (v != null) { n++; sum += v; } } return s[key] = n >= 25 ? sum / n : null; }
function avg10(s, k, y) { let n = 0, sum = 0; for (let x = y - 9; x <= y; x++) { const v = at(s, k, x); if (v != null) { n++; sum += v; } } return n >= 8 ? sum / n : null; }
// anomaly: °C difference (temperature) or % of the 1961–1990 average (precipitation)
function anom(s, mode, y, smooth = S.avg) {
  const k = mode === 'temp' ? 't' : 'p', b = baseline(s, k); if (b == null) return null;
  const v = smooth ? avg10(s, k, y) : at(s, k, y); if (v == null) return null;
  return k === 't' ? v - b : b > 0 ? (v - b) / b * 100 : null;
}
const perDecade = (s, k) => { const t = s.trend?.[k]; if (!t || !t[1]) return null; const [a, b] = t[1].split('-').map(Number); return b - a + 1 >= 50 ? t[0] / (b - a + 1) * 10 : null; };   // published change over the record, per decade (records of 50+ years only)

// ---------------------------------------------------------------- colour (palette from the page)
const css = n => getComputedStyle(document.body).getPropertyValue(n).trim();
const hex = h => { h = h.replace('#', ''); return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16)); };
const lerp = (a, b, t) => a.map((x, i) => Math.round(x + (b[i] - x) * t));
const rampAt = (st, t) => { t = Math.max(0, Math.min(1, t)) * (st.length - 1); const i = Math.min(st.length - 2, Math.floor(t)); return lerp(st[i], st[i + 1], t - i); };
let PAL;
function pal() { PAL = { seq: [1, 2, 3, 4, 5].map(i => hex(css('--seq-' + i))), dec: [1, 2, 3].map(i => hex(css('--dec-' + i))), neu: hex(css('--neutral')), land: hex(css('--land')), line: hex(css('--boundary')),
  water: hex(css('--ocean')), sel: hex(css('--select')), ink: hex(css('--ink-1')), halo: hex(css('--halo')), page: css('--page') };
}
const DOM = { temp: 2.5, precip: 30, trend: 0.4 };
function col(mode, v) { if (v == null) return null; const d = DOM[mode], dead = d * 0.05; if (Math.abs(v) < dead) return PAL.neu;
  const up = mode === 'precip' ? v < 0 : v > 0;   // warmer and drier use the warm ramp; colder and wetter the cool ramp
  return up ? rampAt(PAL.seq, (Math.abs(v) - dead) / (d - dead)) : rampAt(PAL.dec, (Math.abs(v) - dead) / (d - dead)); }
const unit = mode => mode === 'precip' ? '%' : '°C';
const fmtA = (mode, v) => mode === 'precip' ? sgn(v, 0, '%') : mode === 'trend' ? sgn(v, 2, '°C') : sgn(v, 1, '°C');

// ---------------------------------------------------------------- shell
function build() {
  el = document.createElement('section'); el.id = 'cl'; el.className = 'nbx'; el.hidden = true; el.setAttribute('aria-label', 'Climate');
  el.innerHTML = `<header id="cl-top" class="nbx-top"><button class="nbx-back" aria-label="Back to the national map">← Canada</button>
    <div class="nbx-title"><span class="kick">Climate and land · Environment and Climate Change Canada, WGMS, Natural Resources Canada</span><h1>How Canada’s climate has changed</h1></div>
    <div id="cl-modes" role="tablist"></div></header>
  <aside id="cl-side" class="nbx-side"></aside>
  <div id="cl-map" class="nbx-map" aria-label="Map of climate stations"></div>
  <div id="cl-legend" class="nbx-legend"></div>
  <div id="cl-time" class="nbx-time"></div>
  <aside id="cl-detail" class="nbx-detail"></aside>
  <div id="cl-tip" class="nbx-tip" role="tooltip"></div>`;
  document.body.appendChild(el);
  el.querySelector('.nbx-back').onclick = close;
  el.addEventListener('click', e => {
    const m = e.target.closest('[data-clm]'); if (m) { S.mode = m.dataset.clm; S.gl = null; if (S.mode === 'precip' && S.y > A.p_years[1]) S.y = A.p_years[1]; if (S.mode === 'forest') { loadForest().then(() => { S.y = Math.max(F.years[0], Math.min(F.years[1], S.y)); render(); }); return; } render(); return; }
    if (e.target.closest('[data-clavg]')) { S.avg = e.target.closest('[data-clavg]').dataset.clavg === '1'; render(); return; }
    if (e.target.closest('[data-clplay]')) { togglePlay(); return; }
    const g = e.target.closest('[data-glac]'); if (g) { S.gl = g.dataset.glac; S.gy = null; render(); return; }
    if (e.target.closest('[data-clclear]')) { S.st = null; S.gl = null; render(); }
  });
  el.addEventListener('input', e => { if (e.target.id === 'cl-year') { S.y = +e.target.value; render(true); } });
  addEventListener('keydown', e => { if (e.key === 'Escape' && !el.hidden) { if (S.st || S.gl) { S.st = S.gl = null; render(); } else close(); } });
  addEventListener('resize', () => { if (!el.hidden) fit(); });
}
let timer = null, CLZ = null;
// Sideways drag on the map travels through the years (temperature, precipitation, forests) at the whole-Canada view; zoomed in,
// or with Shift held, drag moves the map. Two fingers always pinch and move it.
function bindScrub(mapBox) {
  const hud = document.createElement('div'); hud.className = 'cl-scrub'; hud.hidden = true; mapBox.appendChild(hud);
  let g = null; const pts = new Set();
  const fitZ = () => { const box = mapBox.getBoundingClientRect(); return Math.log2(Math.min(box.width / 5400, box.height / 4600) * 0.98); };
  const ok = e => (S.mode === 'temp' || S.mode === 'precip' || S.mode === 'forest') && !e.shiftKey && e.button === 0 && pts.size === 1 && (CLZ == null || CLZ <= fitZ() + 0.35);
  mapBox.addEventListener('pointerdown', e => { pts.add(e.pointerId); g = ok(e) ? { id: e.pointerId, x0: e.clientX, y0: e.clientY, y: S.y, on: false } : null; }, true);
  mapBox.addEventListener('pointermove', e => { if (!g || e.pointerId !== g.id) return; if (pts.size > 1) { g = null; hud.hidden = true; return; }
    const dx = e.clientX - g.x0, dy = e.clientY - g.y0;
    if (!g.on) { if (Math.abs(dx) > 9 && Math.abs(dx) > Math.abs(dy) * 1.2) { g.on = true; if (S.playing) togglePlay(); try { mapBox.setPointerCapture(e.pointerId); } catch (x) {} hud.hidden = false; } else return; }
    e.stopPropagation(); e.preventDefault();
    const [a, b] = range(), per = Math.max(8, Math.min(26, mapBox.clientWidth * 0.8 / (b - a))), y = Math.max(a, Math.min(b, Math.round(g.y + dx / per)));
    const r = mapBox.getBoundingClientRect(); hud.style.left = Math.max(80, Math.min(r.width - 80, e.clientX - r.left)) + 'px'; hud.style.top = Math.max(40, e.clientY - r.top - 96) + 'px';
    hud.textContent = S.mode === 'forest' || !S.avg ? y : `${y - 9}–${y}`; if (y !== S.y) { S.y = y; render(true); } }, true);
  const end = e => { pts.delete(e.pointerId); if (g && e.pointerId === g.id) { if (g.on) { e.stopPropagation(); hud.hidden = true; } g = null; } };
  mapBox.addEventListener('pointerup', end, true); mapBox.addEventListener('pointercancel', end, true);
}
function togglePlay() { S.playing = !S.playing; clearInterval(timer);
  if (S.playing) { const [y0, y1] = range(); if (S.y >= y1) S.y = Math.max(y0, 1900); timer = setInterval(() => { const [, b] = range(); if (S.y >= b) { S.playing = false; clearInterval(timer); render(); return; } S.y++; render(true); }, 160); }
  render(true); }
const range = () => S.mode === 'precip' ? [1900, A.p_years[1]] : S.mode === 'temp' ? [1900, A.t_years[1]] : S.mode === 'forest' ? F.years : [1900, 2020];

function fit() { if (!deckI) return; const box = el.querySelector('#cl-map').getBoundingClientRect(), b = [3700, 300, 9100, 4900];   // km, StatCan Lambert: all of Canada
  const z = Math.log2(Math.min(box.width / (b[2] - b[0]), box.height / (b[3] - b[1])) * 0.98);
  deckI.setProps({ initialViewState: { target: [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2 - 150, 0], zoom: z, minZoom: z - 0.5, maxZoom: z + 5 } }); }

// ---------------------------------------------------------------- data views
function stationRows() {
  if (S.mode === 'trend') return A.stations.map(s => [s, perDecade(s, 'temp_mean')]);
  return A.stations.map(s => [s, anom(s, S.mode, S.y)]);
}
function warmerShare(mode) {   // per year: stations above / below their 1961–1990 average (single years, not smoothed)
  const [y0, y1] = mode === 'precip' ? [1900, A.p_years[1]] : [1900, A.t_years[1]], out = [];
  for (let y = y0; y <= y1; y++) { let up = 0, n = 0; for (const s of A.stations) { const a = anom(s, mode, y, false); if (a == null) continue; n++; if (a > 0) up++; } out.push([y, n >= 30 ? up / n * 100 : null, n]); }
  return out;
}
const SHARE = {};

// ---------------------------------------------------------------- render
function render(fast) {
  pal(); writeHash();
  el.querySelector('#cl-modes').innerHTML = MODES.map(([k, l]) => `<button role="tab" data-clm="${k}" class="${S.mode === k ? 'on' : ''}" aria-selected="${S.mode === k}">${l}</button>`).join('');
  const timed = S.mode === 'temp' || S.mode === 'precip' || S.mode === 'forest', [y0, y1] = range();
  el.querySelector('#cl-time').hidden = !timed;
  if (timed) { const t = el.querySelector('#cl-time'); if (!t.querySelector('#cl-year') || !fast) t.innerHTML = `<button data-clplay class="play" aria-label="Play">${S.playing ? '❚❚' : '▶'}</button><b id="cl-y"></b><input id="cl-year" type="range" min="${y0}" max="${y1}" step="1" aria-label="Year"><span class="smooth"><button data-clavg="1" class="${S.avg ? 'on' : ''}">10-year average</button><button data-clavg="0" class="${S.avg ? '' : 'on'}">Single year</button></span>`;
    t.querySelector('#cl-year').value = S.y; t.querySelector('#cl-y').textContent = S.mode === 'forest' ? S.y : S.avg ? `${S.y - 9}–${S.y}` : S.y; const sm = t.querySelector('.smooth'); if (sm) sm.style.display = S.mode === 'forest' ? 'none' : ''; t.querySelector('[data-clplay]').textContent = S.playing ? '❚❚' : '▶'; }
  side(); detail(); legend(); drawMap();
}
function side() {
  const box = el.querySelector('#cl-side');
  if (S.mode === 'ice') { box.innerHTML = iceSide(); return; }
  if (S.mode === 'forest') { box.innerHTML = forestSide(); return; }
  const rows = stationRows().filter(r => r[1] != null), up = rows.filter(r => r[1] > 0).length, mode = S.mode;
  const share = SHARE[mode] ||= warmerShare(mode === 'trend' ? 'temp' : mode);
  const what = mode === 'temp' ? 'warmer' : mode === 'precip' ? 'wetter' : 'warmer';
  const head = mode === 'trend' ? `<h2>Long-term warming at each station</h2><p class="q">How much each station’s annual mean temperature changed per decade over its whole record (records of 50 years or more).</p>
      <div class="big"><b>${up} of ${rows.length}</b><span>stations warmed over their record</span></div>`
    : `<h2>${mode === 'temp' ? 'Temperature vs. 1961–1990' : 'Precipitation vs. 1961–1990'}</h2><p class="q">${mode === 'temp' ? 'How much warmer or colder each station was than its own 1961–1990 average.' : 'How much wetter or drier each station was, as a percentage of its own 1961–1990 average.'}</p>
      <div class="big"><b>${rows.length ? up + ' of ' + rows.length : '—'}</b><span>stations ${what} than their 1961–1990 average${S.avg ? ` (${S.y - 9}–${S.y} average)` : ` in ${S.y}`}</span></div>`;
  const med = rows.length ? rows.map(r => r[1]).sort((a, b) => a - b)[Math.floor(rows.length / 2)] : null;
  box.innerHTML = `${head}${med != null ? `<p class="rng">Middle station: <b>${fmtA(mode, med)}</b>${mode === 'trend' ? ' per decade' : ''}.</p>` : ''}
    <h4>${mode === 'precip' ? 'Share of stations wetter than 1961–1990, each year' : 'Share of stations warmer than 1961–1990, each year'}</h4>${shareChart(share, mode === 'trend' ? null : S.y)}
    <p class="def">${mode === 'temp' ? 'Homogenized annual mean temperature: ECCC adjusts each station’s record for moves and instrument changes so years can be compared. A station’s 1961–1990 average needs at least 25 of those 30 years; a 10-year average needs at least 8 of 10 years.'
      : mode === 'precip' ? 'Adjusted annual total precipitation (rain plus the water in snow). ECCC’s adjusted precipitation series currently end in 2017. A station’s 1961–1990 average needs at least 25 of those 30 years.'
      : 'ECCC’s published Theil-Sen trend over each station’s full record, divided by the record’s length to give a change per decade so stations with different records can be compared. Stations with records under 50 years are not shown.'}</p>
    <p class="def">Each dot is a weather station, not an area: the map shows where stations are, and the north has few of them. The chart counts stations, it is not a national average.</p>
    <p class="src">Source: Environment and Climate Change Canada, Adjusted and Homogenized Canadian Climate Data (AHCCD), via the MSC GeoMet API (temperature to ${A.t_years[1]}, precipitation to ${A.p_years[1]}).</p>`;
}
function shareChart(share, cur) {
  const W = 290, H = 90, pts = share.filter(r => r[1] != null); if (!pts.length) return '';
  const x0 = share[0][0], x1 = share[share.length - 1][0], X = y => (y - x0) / (x1 - x0) * W, Y = v => H - v / 100 * H;
  const bars = pts.map(([y, v, n]) => `<rect x="${X(y) - 1}" y="${Math.min(Y(v), Y(50))}" width="${Math.max(1.2, W / (x1 - x0) - 0.6)}" height="${Math.abs(Y(v) - Y(50))}" fill="rgb(${(v >= 50) !== (S.mode === 'precip') ? PAL.seq[3] : PAL.dec[1]})"><title>${y}: ${nf(v)}% of ${n} stations</title></rect>`).join('');
  return `<svg class="cl-share" viewBox="0 0 ${W} ${H + 16}" role="img" aria-label="Share of stations above their 1961–1990 average each year">
    <line x1="0" x2="${W}" y1="${Y(50)}" y2="${Y(50)}" class="mid"/>${bars}
    ${cur ? `<line x1="${X(cur)}" x2="${X(cur)}" y1="0" y2="${H}" class="cur"/>` : ''}
    <text x="0" y="${H + 12}">${x0}</text><text x="${W}" y="${H + 12}" text-anchor="end">${x1}</text><text x="${W}" y="${Y(50) - 3}" text-anchor="end" class="ax">half</text></svg>`;
}
function iceSide() {
  const long = G.glaciers.filter(g => g.n >= 40);
  return `<h2>Glaciers losing ice</h2><p class="q">Each year’s glacier-wide mass balance: snow gained minus ice and snow melted, as metres of water spread over the glacier.</p>
    <div class="big"><b>${long.filter(g => lastC(cum(g))[1] < 0).length} of ${long.length}</b><span>glaciers measured for 40+ years have a negative running total</span></div>
    <h4>Running total since monitoring began <small>m water equivalent</small></h4>${cumChart(long)}
    <div class="gl-list">${G.glaciers.map(g => { const last = lastC(cum(g)); return `<button data-glac="${g.id}" class="${S.gl === g.id ? 'on' : ''}"><span>${esc(g.name)}</span><i>${g.b[0]}–${g.b[0] + g.b[1].length - 1}</i><b>${last ? sgn(last[1], 1, ' m') : '—'}</b></button>`; }).join('')}</div>
    <p class="def">The running total adds up the measured years; a year with no measurement is skipped (the line breaks there) and the count of missing years is shown for each glacier. A glacier with a running total of −30 m has lost the equivalent of a 30-metre-deep layer of water across its whole area since monitoring began.</p>
    <p class="src">Source: WGMS (2026), Fluctuations of Glaciers Database, doi:10.5904/wgms-fog-2026-02-10. Canadian measurements by the Geological Survey of Canada and university programs.</p>`;
}
function cum(g) { let s = 0; const out = []; for (let i = 0; i < g.b[1].length; i++) { const v = g.b[1][i]; if (v == null) { out.push(null); continue; } s += v; out.push([g.b[0] + i, s]); } while (out.length && out[out.length - 1] == null) out.pop(); return out; }   // null marks a year with no measurement
const lastC = c => c.filter(Boolean).slice(-1)[0];
const gaps = g => g.b[1].filter(v => v == null).length;
const regionCol = g => g.region.includes('western') ? PAL.seq[3] : PAL.dec[2];
function cumChart(gs) {
  const W = 290, H = 150, all = gs.map(g => [g, cum(g)]), pts = all.flatMap(([, c]) => c.filter(Boolean)), x0 = 1959, x1 = Math.max(...pts.map(p => p[0])), lo = Math.min(...pts.map(p => p[1])), hi = 2;
  const X = y => (y - x0) / (x1 - x0) * W, Y = v => (hi - v) / (hi - lo) * H;
  const path = c => { let d = '', pen = false; for (const p of c) { if (!p) { pen = false; continue; } d += (pen ? 'L' : 'M') + X(p[0]).toFixed(1) + ' ' + Y(p[1]).toFixed(1); pen = true; } return d; };
  const lines = all.map(([g, c]) => `<path d="${path(c)}" class="${S.gl === g.id ? 'on' : ''}" stroke="rgb(${regionCol(g)})"><title>${esc(g.name)}</title></path>`).join('');
  // end labels, nudged apart so they don't overlap
  const lab = all.map(([g, c]) => [g, Y(lastC(c)[1]) + 3]).sort((a, b) => a[1] - b[1]); for (let i = 1; i < lab.length; i++) lab[i][1] = Math.max(lab[i][1], lab[i - 1][1] + 10);
  return `<svg class="cl-cum" viewBox="0 0 ${W + 78} ${H + 16}" role="img" aria-label="Running total of mass balance for long-monitored Canadian glaciers">
    <line x1="0" x2="${W}" y1="${Y(0)}" y2="${Y(0)}" class="mid"/>${lines}
    ${lab.map(([g, y]) => `<text x="${W + 4}" y="${y}" class="gl">${esc(g.name.replace(' Ice Cap', ''))}</text>`).join('')}
    <text x="0" y="${H + 12}">${x0}</text><text x="${W}" y="${H + 12}" text-anchor="end">${x1}</text><text x="2" y="${Y(0) - 3}" class="ax">0</text><text x="2" y="${H - 2}" class="ax">${nf(lo)} m</text></svg>
    <div class="lg2"><span><i style="background:rgb(${PAL.seq[3]})"></i>Rockies and Coast Mountains</span><span><i style="background:rgb(${PAL.dec[2]})"></i>Arctic ice caps</span></div>`;
}
function legend() {
  const box = el.querySelector('#cl-legend');
  if (S.mode === 'forest') { box.innerHTML = `<div class="lg-t">Forest disturbed, each ${F.cell_km} km square</div><div class="lg2"><span><i style="background:rgb(${FIRE()})"></i>Burned in ${S.y}</span><span><i style="background:rgb(${CUT()})"></i>Harvested in ${S.y}</span></div><div class="lg2"><span><i style="background:rgb(${PAL.seq[1]})"></i>Earlier years since 1985, paler with time</span></div><div class="lg-miss">Bigger dot: more hectares. Under 50 ha in a year (earlier years: under 1% of the square) not drawn, still counted.</div>`; return; }
  if (S.mode === 'ice') { box.innerHTML = `<div class="lg-t">Glaciers with 10+ years of mass balance</div><div class="lg2"><span><i style="background:rgb(${PAL.seq[3]})"></i>Western mountains</span><span><i style="background:rgb(${PAL.dec[2]})"></i>Arctic</span></div><div class="lg-miss">Bigger circle: more years measured</div>`; return; }
  const d = DOM[S.mode], st = Array.from({ length: 11 }, (_, i) => { const v = -d + i / 10 * 2 * d; return `rgb(${col(S.mode, v)}) ${i * 10}%`; });
  const lo = S.mode === 'precip' ? 'drier' : 'colder', hi = S.mode === 'precip' ? 'wetter' : 'warmer';
  box.innerHTML = `<div class="lg-t">${S.mode === 'trend' ? 'Change per decade' : 'Difference from 1961–1990'}</div><div class="lg-bar" style="background:linear-gradient(90deg,${st.join(',')})"></div>
    <div class="lg-ax"><span>${fmtA(S.mode, -d)} ${S.mode === 'trend' ? 'cooling' : lo}</span><span>${fmtA(S.mode, d)} ${S.mode === 'trend' ? 'warming' : hi}</span></div>
    <div class="lg-miss"><i class="ring"></i>No value for this period</div>`;
}
function stationChart(s, k) {
  const p = s[k]; if (!p) return '<p class="hint">No series published for this station.</p>';
  const pts = p[1].map((v, i) => [p[0] + i, v]).filter(r => r[1] != null), b = baseline(s, k);
  const x0 = pts[0][0], x1 = pts[pts.length - 1][0], vs = pts.map(r => r[1]), lo = Math.min(...vs), hi = Math.max(...vs), W = 290, H = 120;
  const X = y => (y - x0) / Math.max(1, x1 - x0) * W, Y = v => H - (v - lo) / (hi - lo || 1) * H;
  const dots = pts.map(([y, v]) => `<circle cx="${X(y).toFixed(1)}" cy="${Y(v).toFixed(1)}" r="1.6"><title>${y}: ${nf(v, 1)}${k === 't' ? ' °C' : ' mm'}</title></circle>`).join('');
  const sm = []; for (let y = x0 + 9; y <= x1; y++) { const a = avg10(s, k, y); sm.push(a == null ? null : [y, a]); }
  let path = '', pen = false; for (const q of sm) { if (!q) { pen = false; continue; } path += (pen ? 'L' : 'M') + X(q[0]).toFixed(1) + ' ' + Y(q[1]).toFixed(1); pen = true; }
  return `<svg class="cl-st" viewBox="0 0 ${W} ${H + 16}" role="img" aria-label="Annual values at this station">
    ${b != null ? `<line x1="0" x2="${W}" y1="${Y(b)}" y2="${Y(b)}" class="mid"/><text x="${W}" y="${Y(b) - 3}" text-anchor="end" class="ax">1961–1990 average ${nf(b, k === 't' ? 1 : 0)}${k === 't' ? '°C' : ' mm'}</text>` : ''}
    ${dots}<path d="${path}" class="sm"/>
    <text x="0" y="${H + 12}">${x0}</text><text x="${W}" y="${H + 12}" text-anchor="end">${x1}</text></svg>
    <div class="lg2"><span><i class="dot"></i>each year</span><span><i class="ln"></i>10-year average</span></div>`;
}
// Cross-section: the drop of the ice surface is to scale (glacier-wide average thinning = running total of mass balance ÷ 0.9,
// since ice is about 900 kg/m³); the valley and the starting thickness are a drawing, not survey data.
let XS_K = null;
function xsSvg(g, y) {
  if (XS_K == null) { const worst = Math.min(...G.glaciers.map(x => lastC(cum(x))?.[1] ?? 0)); XS_K = 52 / (Math.abs(worst) / 0.9 || 1); }
  const c = cum(g).filter(Boolean), y0 = g.b[0], y1 = lastC(cum(g))[0]; y = Math.max(y0, Math.min(y1, y));
  const at = c.filter(p => p[0] <= y).slice(-1)[0], we = at ? at[1] : 0, ice = we / 0.9, drop = Math.max(0, -ice) * XS_K, rise = Math.max(0, ice) * XS_K;
  const W = 290, H = 160, bed = x => 128 - 70 * (x / W) + 14 * Math.sin(x / W * Math.PI), top0 = x => bed(x) - 62 * Math.sin(Math.min(1, x / W * 1.15) * Math.PI * 0.92 + 0.12);
  const pts = Array.from({ length: 41 }, (_, i) => i / 40 * W), line = f => pts.map((x, i) => (i ? 'L' : 'M') + x.toFixed(1) + ' ' + f(x).toFixed(1)).join('');
  const now = x => Math.min(bed(x), top0(x) + drop - rise);
  const iceNow = line(now) + pts.slice().reverse().map(x => 'L' + x.toFixed(1) + ' ' + bed(x).toFixed(1)).join('') + 'Z';
  const lost = line(top0) + pts.slice().reverse().map(x => 'L' + x.toFixed(1) + ' ' + now(x).toFixed(1)).join('') + 'Z';
  const sb = 10 * XS_K, frac = (y - y0) / Math.max(1, y1 - y0);
  return `<svg class="cl-xs" viewBox="0 0 ${W} ${H + 28}" data-xs="${g.id}" role="img" aria-label="${esc(g.name)} cross-section, ${y}: surface ${ice < 0 ? 'lowered' : 'raised'} ${nf(Math.abs(ice), 1)} m of ice since ${y0}">
    <path d="${line(x => bed(x) + 4)}L${W} ${H}L0 ${H}Z" class="rock"/><path d="${lost}" class="lost"/><path d="${iceNow}" class="ice"/>
    <path d="${line(top0)}" class="was"/><text x="6" y="${top0(6) - 6}" class="lab">${y0} surface</text>
    <g class="sb"><line x1="${W - 8}" x2="${W - 8}" y1="18" y2="${18 + sb}"/><text x="${W - 12}" y="${22 + sb / 2}" text-anchor="end">10 m</text></g>
    <text x="8" y="16" class="yr">${y}</text><text x="8" y="31" class="val">${ice < 0 ? '−' : '+'}${nf(Math.abs(ice), 1)} m of ice</text>
    <line x1="0" x2="${W}" y1="${H + 14}" y2="${H + 14}" class="trk"/><circle cx="${frac * W}" cy="${H + 14}" r="6" class="knob"/>
    <text x="0" y="${H + 27}" class="tk">${y0}</text><text x="${W}" y="${H + 27}" class="tk" text-anchor="end">${y1}</text></svg>`;
}
function bindXs(box, g) {
  const sv = () => box.querySelector('svg.cl-xs'); let drag = false;
  const setFrom = e => { const r = sv().getBoundingClientRect(), y0 = g.b[0], y1 = lastC(cum(g))[0];
    S.gy = Math.round(y0 + Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)) * (y1 - y0)); sv().outerHTML = xsSvg(g, S.gy); bindXs(box, g); };
  const el2 = sv(); el2.style.touchAction = 'pan-y';
  el2.onpointerdown = e => { drag = true; el2.setPointerCapture?.(e.pointerId); setFrom(e); };
  el2.onpointermove = e => { if (drag || e.pointerType === 'mouse' && e.buttons) setFrom(e); };
  el2.onpointerup = el2.onpointercancel = () => { drag = false; };
}
function detail() {
  const box = el.querySelector('#cl-detail');
  if (S.mode === 'forest') { box.innerHTML = forestDetail(); return; }
  if (S.mode === 'ice') {
    const g = G.glaciers.find(x => x.id === S.gl);
    if (!g) { box.innerHTML = `<h3>Click a glacier</h3><p class="hint">Mass balance is measured with stakes and snow pits across the glacier every year. Only a handful of Canadian glaciers have long records; these are all of them in the WGMS database with 10 or more years.</p>`; return; }
    const c = cum(g), lc = lastC(c), ng = gaps(g), W = 290, H = 110, vals = g.b[1].map((v, i) => [g.b[0] + i, v]).filter(r => r[1] != null), lo = Math.min(0, ...vals.map(r => r[1])), hi = Math.max(0, ...vals.map(r => r[1]));
    const X = y => (y - g.b[0]) / Math.max(1, g.b[1].length - 1) * W, Y = v => (hi - v) / (hi - lo || 1) * H, bw = Math.max(1.5, W / g.b[1].length - 1);
    const neg = vals.filter(r => r[1] < 0).length;
    box.innerHTML = `<div class="dt-h"><div><span class="kick">${g.region.includes('western') ? 'Western mountains' : 'Arctic'} · ${nf(g.lat, 2)}°N</span><h3>${esc(g.name)}</h3></div><button data-clclear aria-label="Close">×</button></div>
      <div class="dt-pop"><b>${sgn(lc[1], 1, ' m')}</b> running total, ${g.b[0]}–${lc[0]}${ng ? ` <span class=\"gapn\">(${ng} year${ng > 1 ? 's' : ''} not measured)</span>` : ''}</div>
      <p class="hint">${neg} of ${vals.length} measured years were negative (more melt than snowfall).</p>
      <h4>Drag across the glacier <small>surface lowering to scale</small></h4>${xsSvg(g, S.gy ?? lc[0])}
      <p class="def">Average thinning across the whole glacier, to scale: the running total of mass balance converted to ice (÷ 0.9; ice is lighter than water). The valley and the starting thickness are a drawing, not a survey; the glacier also gets shorter, which this view doesn’t show.</p>
      <h4>Each year <small>m water equivalent</small></h4>
      <svg class="cl-st" viewBox="0 0 ${W} ${H + 16}"><line x1="0" x2="${W}" y1="${Y(0)}" y2="${Y(0)}" class="mid"/>${vals.map(([y, v]) => `<rect x="${X(y) - bw / 2}" y="${Math.min(Y(v), Y(0))}" width="${bw}" height="${Math.abs(Y(v) - Y(0))}" fill="rgb(${v < 0 ? PAL.dec[2] : PAL.seq[3]})"><title>${y}: ${sgn(v, 2, ' m')}</title></rect>`).join('')}
      <text x="0" y="${H + 12}">${g.b[0]}</text><text x="${W}" y="${H + 12}" text-anchor="end">${g.b[0] + g.b[1].length - 1}</text></svg>`;
    bindXs(box, g);
    return;
  }
  const s = A.stations.find(x => x.id === S.st);
  if (!s) { const rows = stationRows().filter(r => r[1] != null).sort((a, b) => b[1] - a[1]);
    const row = ([st, v]) => `<button data-clst="${st.id}"><span>${esc(st.name)} <i>${st.prov}</i></span><b>${fmtA(S.mode, v)}${S.mode === 'trend' ? '/dec' : ''}</b></button>`;
    box.innerHTML = `<h3>Click any station</h3><p class="hint">See its full record: every published year since it opened, with its 1961–1990 average and a 10-year average.</p>
      ${rows.length ? `<h4>${({ temp: 'Furthest above 1961–1990', precip: 'Wettest vs. 1961–1990', trend: 'Most warming per decade' })[S.mode]}</h4><div class="nb-list">${rows.slice(0, 6).map(row).join('')}</div><h4>${({ temp: 'Lowest vs. 1961–1990', precip: 'Driest vs. 1961–1990', trend: 'Least warming per decade' })[S.mode]}</h4><div class="nb-list">${rows.slice(-6).reverse().map(row).join('')}</div>` : ''}`;
    box.querySelectorAll('[data-clst]').forEach(b => b.onclick = () => { S.st = b.dataset.clst; render(); });
    return; }
  const tr = s.trend || {}, pd = perDecade(s, 'temp_mean');
  box.innerHTML = `<div class="dt-h"><div><span class="kick">${s.prov} · ${s.elev != null ? nf(s.elev) + ' m elevation · ' : ''}station ${esc(s.id)}</span><h3>${esc(s.name)}</h3></div><button data-clclear aria-label="Close">×</button></div>
    ${s.t ? `<h4>Annual mean temperature <small>°C</small></h4>${stationChart(s, 't')}` : ''}
    ${tr.temp_mean ? `<p class="hint">ECCC trend ${tr.temp_mean[1]}: <b>${sgn(tr.temp_mean[0], 1, '°C')}</b> over the record${pd != null ? ` (${sgn(pd, 2, '°C')} per decade)` : ''}.</p>` : ''}
    ${s.p ? `<h4>Annual precipitation <small>mm</small></h4>${stationChart(s, 'p')}` : ''}
    ${tr.total_precip ? `<p class="hint">ECCC trend ${tr.total_precip[1]}: <b>${sgn(tr.total_precip[0], 0, ' mm')}</b> over the record.</p>` : ''}
    <p class="src">Homogenized and adjusted values as published by ECCC. Gaps are years ECCC did not publish.</p>`;
}

function drawMap() {
  const key = [S.mode, S.y, S.avg, S.st, S.gl, PAL.page].join('|');
  const land = new GeoJsonLayer({ id: 'land', data: PROV, filled: true, stroked: true, getFillColor: [...PAL.land, 255], getLineColor: [...PAL.line, 120], lineWidthUnits: 'pixels', getLineWidth: 0.8, updateTriggers: { getFillColor: key, getLineColor: key } });
  const lakes = new GeoJsonLayer({ id: 'lakes', data: LAKES, filled: true, stroked: false, getFillColor: [...PAL.water, 255], updateTriggers: { getFillColor: key } });
  let marks;
  if (S.mode === 'forest') marks = forestMarks(key);
  else if (S.mode === 'ice') {
    marks = [new ScatterplotLayer({ id: 'gl', data: G.glaciers, pickable: true, getPosition: g => g.xy, radiusUnits: 'pixels', getRadius: g => 4 + Math.sqrt(g.n) * 1.1, stroked: true, lineWidthUnits: 'pixels',
        getLineWidth: g => g.id === S.gl ? 3 : 1.2, getFillColor: g => [...regionCol(g), 230], getLineColor: g => g.id === S.gl ? [...PAL.sel, 255] : [...PAL.ink, 200], updateTriggers: { getLineWidth: key, getLineColor: key, getFillColor: key } }),
      new TextLayer({ id: 'gl-lab', data: G.glaciers.filter(g => g.n >= 40 || g.id === S.gl), getPosition: g => g.xy, getText: g => g.name.replace(' Ice Cap', ''), getSize: 12, getColor: [...PAL.ink, 255], getPixelOffset: g => ({ Helm: [-10, 8], White: [10, 9], Meighen: [10, -7] })[g.name.replace(' Ice Cap', '')] || [10, 0], getTextAnchor: g => g.name === 'Helm' ? 'end' : 'start', getAlignmentBaseline: 'center',
        fontFamily: 'IBM Plex Sans, sans-serif', fontWeight: 600, outlineWidth: 4, outlineColor: [...PAL.halo, 230], fontSettings: { sdf: true }, characterSet: 'auto', updateTriggers: { getColor: key } })];
  } else {
    const rows = stationRows(), data = rows.map(([s, v]) => ({ s, v })).sort((a, b) => (a.v == null) - (b.v == null) || Math.abs(a.v ?? 0) - Math.abs(b.v ?? 0)).reverse();
    marks = [new ScatterplotLayer({ id: 'st', data, pickable: true, getPosition: d => d.s.xy, radiusUnits: 'pixels', getRadius: d => d.s.id === S.st ? 7 : d.v == null ? 2.2 : 4.6, stroked: true, lineWidthUnits: 'pixels',
      getLineWidth: d => d.s.id === S.st ? 2.5 : d.v == null ? 0.8 : 0.6, getFillColor: d => d.v == null ? [0, 0, 0, 0] : [...col(S.mode, d.v), 255], getLineColor: d => d.s.id === S.st ? [...PAL.sel, 255] : d.v == null ? [...PAL.ink, 70] : [...PAL.halo, 160],
      updateTriggers: { getRadius: key, getLineWidth: key, getFillColor: key, getLineColor: key }, transitions: { getFillColor: 120 } })];
  }
  deckI.setProps({ layers: [land, lakes, ...marks] });
  el.querySelector('#cl-map').style.background = `rgb(${PAL.water})`;
}
function tip({ object, x, y }) {
  const t = el.querySelector('#cl-tip'); if (!object) { t.style.display = 'none'; return; }
  if (object.b) { const l = lastC(cum(object)); t.innerHTML = `<b>${esc(object.name)}</b><span>${l ? `${sgn(l[1], 1, ' m')} running total, ${object.b[0]}–${l[0]}` : ''}</span>`; }
  else { const s = object.s; t.innerHTML = `<b>${esc(s.name)}, ${s.prov}</b><span>${object.v == null ? 'No value for this period' : fmtA(S.mode, object.v) + (S.mode === 'trend' ? ' per decade' : ' vs. 1961–1990')}</span>`; }
  t.style.display = 'block'; t.style.left = x + 14 + 'px'; t.style.top = y + 14 + 'px';
}


// ---------------------------------------------------------------- forests (NRCan CanLaD 1984–2015, aggregated to 9 km squares)
const FIRE = () => hex(css('--accent')), CUT = () => PAL.dec[2];
const loadForest = () => fready ||= J('../data/forest/disturbance.json').then(f => { F = f; });
const MIN_NOW = 50, MIN_PAST = 324;   // drawing only: squares below these hectares are not drawn but stay in every total
const haF = v => v >= 1e6 ? nf(v / 1e6, 2) + ' million ha' : nf(v) + ' ha';
function forestMarks(key) {
  const y = S.y, data = [];
  for (const c of F.cells) { let f = 0, h = 0, past = 0, last = 0;
    for (const [yy, a, b] of c[2]) { if (yy === y) { f = a; h = b; } else if (yy < y) { past += a + b; last = Math.max(last, yy); } }
    if (f + h >= MIN_NOW || past >= MIN_PAST) data.push({ c, f, h, past, last }); }
  const km = F.cell_km, side = d => Math.sqrt(d / (km * km * 100)) * km;   // a fully disturbed square is drawn its own width
  return [new ScatterplotLayer({ id: 'fo-past', data: data.filter(d => d.past >= MIN_PAST), getPosition: d => [d.c[0], d.c[1]], radiusUnits: 'common', getRadius: d => side(d.past) / 2,
      getFillColor: d => [...PAL.seq[2], Math.round(150 - Math.min(110, (y - d.last) * 5))], stroked: false, updateTriggers: { getFillColor: key, getRadius: key } }),
    new ScatterplotLayer({ id: 'fo-now', data: data.filter(d => d.f + d.h >= MIN_NOW), getPosition: d => [d.c[0], d.c[1]], radiusUnits: 'common', radiusMinPixels: 1.5, getRadius: d => side(d.f + d.h) / 2 * 1.4,
      getFillColor: d => [...(d.f >= d.h ? FIRE() : CUT()), 240], stroked: false, updateTriggers: { getFillColor: key, getRadius: key }, transitions: { getRadius: 120 } })];
}
function forestChart(g) {
  const T = F.totals[g], n = T.fire.length, Wd = 290, H = 110, mx = Math.max(...T.fire.map((v, i) => v + T.harvest[i])), X = i => i / n * Wd, bw = Wd / n - 1.2, Y = v => v / mx * H;
  const bars = T.fire.map((v, i) => { const hv = T.harvest[i], yr = F.years[0] + i;
    return `<rect x="${X(i)}" y="${H - Y(hv)}" width="${bw}" height="${Y(hv)}" fill="rgb(${CUT()})"><title>${yr}: ${haF(hv)} harvested</title></rect><rect x="${X(i)}" y="${H - Y(hv) - Y(v)}" width="${bw}" height="${Y(v)}" fill="rgb(${FIRE()})"><title>${yr}: ${haF(v)} burned</title></rect>`; }).join('');
  const k = S.y - F.years[0];
  return `<svg class="cl-share" viewBox="0 0 ${Wd} ${H + 16}" role="img" aria-label="Hectares burned and harvested each year">${bars}<line x1="${X(k) + bw / 2}" x2="${X(k) + bw / 2}" y1="0" y2="${H}" class="cur"/>
    <text x="0" y="${H + 12}">${F.years[0]}</text><text x="${Wd}" y="${H + 12}" text-anchor="end">${F.years[1]}</text><text x="${Wd}" y="10" text-anchor="end" class="ax">${haF(mx)}</text></svg>`;
}
function forestSide() {
  const T = F.totals.CAN, i = S.y - F.years[0], sum = a => a.reduce((x, y) => x + y, 0);
  return `<h2>Forests cut and burned, and growing back</h2><p class="q">Each year’s stand-replacing disturbance, mapped from Landsat satellite images at 30 m: forest that burned or was harvested.</p>
    <div class="big"><b>${haF(T.fire[i] + T.harvest[i])}</b><span>disturbed in ${S.y}: ${haF(T.fire[i])} burned, ${haF(T.harvest[i])} harvested</span></div>
    <p class="rng">1985–2015 together: <b>${haF(sum(T.fire))}</b> burned and <b>${haF(sum(T.harvest))}</b> harvested.</p>
    <h4>Each year <small><i class="sw" style="background:rgb(${FIRE()})"></i>burned <i class="sw" style="background:rgb(${CUT()})"></i>harvested</small></h4>${forestChart('CAN')}
    <p class="def">Fire swings hugely from year to year; harvest is steadier. Natural Resources Canada does not count harvest or fire as deforestation: the land stays forest and is expected to regrow. Pale squares show earlier disturbance, fading with the years since.</p>
    <p class="def">${F.notes.slice(1).map(esc).join(' ')}</p>
    <p class="src">Source: Natural Resources Canada, Canada Landsat Disturbance (CanLaD) 1984–2015, Open Government Licence – Canada. Totals add the 30 m pixels (0.09 ha each).</p>`;
}
function forestDetail() {
  const rows = Object.entries(F.totals).filter(([g]) => g !== 'CAN').map(([g, t]) => [g, t.fire.reduce((a, b) => a + b, 0), t.harvest.reduce((a, b) => a + b, 0)]).sort((a, b) => b[1] + b[2] - a[1] - a[2]);
  return `<h3>By province and territory</h3><p class="hint">Hectares disturbed, 1985–2015 together.</p><div class="nb-list">${rows.map(([g, f, h]) => `<div class="fo-row"><b>${g}</b><span>${haF(f)} burned</span><span>${haF(h)} harvested</span></div>`).join('')}</div>`;
}

// ---------------------------------------------------------------- open / close / hash
function writeHash() { const h = `#cl=${S.mode}/${S.y}${S.avg ? '' : '/y'}${S.st ? '/s' + S.st : ''}${S.gl ? '/g' + S.gl : ''}`; if (location.hash !== h) history.replaceState(null, '', h); }
async function readHash() { const h = decodeURIComponent(location.hash); if (!h.startsWith('#cl=')) return; const [m, y, ...rest] = h.slice(4).split('/');
  if (MODES.some(x => x[0] === m)) S.mode = m; if (+y >= 1900 && +y <= 2025) S.y = +y; if (S.mode === 'forest') { await loadForest(); S.y = Math.max(F.years[0], Math.min(F.years[1], S.y)); }
  for (const r of rest) { if (r === 'y') S.avg = false; else if (r[0] === 's') S.st = r.slice(1); else if (r[0] === 'g') S.gl = r.slice(1); } }
let prevHash = '';
async function open(opts = {}) {
  if (!el) build();
  if (!location.hash.startsWith('#cl=')) prevHash = location.hash;
  el.hidden = false; document.body.classList.add('nb-on');
  if (!ready) ready = Promise.all([J('../data/climate/ahccd.json'), J('../data/climate/glaciers.json'), J('../data/provinces.geojson'), J('../data/lakes.geojson')]).then(([a, g, p, l]) => {
    A = a; G = g; const km = fc => { const c = x => typeof x[0] === 'number' ? [x[0] / 1e3, x[1] / 1e3] : x.map(c); return { ...fc, features: fc.features.map(f => ({ ...f, geometry: { ...f.geometry, coordinates: c(f.geometry.coordinates) } })) }; };
    PROV = km(p); LAKES = km(l); S.y = A.t_years[1]; });
  await ready; await readHash();
  if (opts.mode) S.mode = opts.mode;
  if (!deckI) bindScrub(el.querySelector('#cl-map'));
  if (!deckI) deckI = new Deck({ parent: el.querySelector('#cl-map'), views: new OrthographicView({ flipY: false }), controller: { doubleClickZoom: true }, onViewStateChange: ({ viewState }) => { CLZ = viewState.zoom; }, initialViewState: { target: [6400, 2400, 0], zoom: -3 },
    getCursor: ({ isHovering }) => isHovering ? 'pointer' : 'grab', onHover: tip,
    onClick: ({ object }) => { if (!object) return; if (object.b) S.gl = object.id; else S.st = object.s.id; render(); }, style: { position: 'absolute', inset: 0 } });
  (window.__decks ||= {}).cl = deckI;
  render(); requestAnimationFrame(fit);
}
function close() { S.playing = false; clearInterval(timer); el.hidden = true; document.body.classList.remove('nb-on'); history.replaceState(null, '', prevHash || location.pathname + location.search); dispatchEvent(new Event('nb-close')); }
window.CLIMATE = { open, close, _render: () => render(), get forest() { return F; }, loadForest, get state() { return S; }, get data() { return { A, G }; }, anom, baseline, perDecade, cum };
if (location.hash.startsWith('#cl=')) open();
