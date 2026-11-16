// Guided journey: a short film that drives the explorer itself. A warm, unhurried documentary style (title card, film grain,
// captions always on). It reads every number from the same published data the map uses, at the moment it is shown, so the
// captions can never disagree with the map. Any touch on the page pauses it; "Resume" carries on from the same scene.
// No narration audio yet: captions only, in the visitor's language. (Tyson records English; a French narrator to follow.)
const T = (en, fr) => window.T ? window.T(en, fr) : en;
const FR = () => window.LANG === 'fr';
const num = (v, dp = 0) => v.toLocaleString(FR() ? 'fr-CA' : 'en-CA', { minimumFractionDigits: dp, maximumFractionDigits: dp });
const wait = ms => new Promise(r => setTimeout(r, ms));

const C = () => window.CTX;
const V = (id, y, g = 'CAN') => { const m = C().M[id]; return m ? m.value(g, y) : null; };
const F = (id, v) => { const t = C().M[id].fmt(v); return FR() ? t.replace(/(\d),(\d{3})/g, '$1 $2').replace(/(\d)\.(\d)/g, '$1,$2').replace(/(\d)%/g, '$1 %') : t; };
const monthName = ym => new Date(+ym.slice(0, 4), +ym.slice(5, 7) - 1, 15).toLocaleDateString(FR() ? 'fr-CA' : 'en-CA', { month: 'long', year: 'numeric' });
const yrs = id => C().M[id].years;
const mapTo = (id, y) => { const c = C(); c.state.navQ = false; c.state.story = null; c.state.q = null; c.state.p = null; c.state.city = null; c.state.cmp = null; c.state.m = id; c.state.y = c.clampYear(c.M[id], y); c.update(); };
const goMap = () => { if (!/^#(nb|cl|mn|wa)=|^#about/.test(location.hash)) return; window.SHELL?.go('map'); };
async function sweep(id, a, b, ms) { const tok = J.token, n = Math.max(1, b - a); for (let y = a; y <= b; y++) { if (!J.on || tok !== J.token) return; while (J.paused) { await wait(150); if (tok !== J.token) return; } mapTo(id, y); await wait(ms / n); } }
const stopClimate = () => { if (window.CLIMATE?.state?.playing) document.querySelector('#cl [data-clplay]')?.click(); };

// ---------------------------------------------------------------- scenes
const SCENES = [
  { kind: 'card', t: () => T('Canada, measured', 'Le Canada, en chiffres'), s: () => T('A short journey through fifty-five years of the country, told by the numbers.', 'Un court voyage à travers cinquante-cinq ans du pays, raconté par les chiffres.'), ms: 5200 },
  { go: async () => { goMap(); const [a] = yrs('pop'); mapTo('pop', a); },
    cap: () => { const [a] = yrs('pop'); return T(`It begins in ${a}. There are ${num(V('pop', a) / 1e6, 1)} million people in Canada, and most of them live in a narrow band along the southern border.`,
      `Tout commence en ${a}. Le Canada compte ${num(V('pop', a) / 1e6, 1)} millions d’habitants, presque tous dans une mince bande le long de la frontière sud.`); }, ms: 7000 },
  { go: async () => { const [a, b] = yrs('pop'); await sweep('pop', a, b, 6500); },
    cap: () => { const [, b] = yrs('pop'); return T(`Year by year the country fills in. By ${b}: ${num(V('pop', b) / 1e6, 1)} million.`, `Année après année, le pays se remplit. En ${b} : ${num(V('pop', b) / 1e6, 1)} millions.`); }, ms: 8000 },
  { go: async () => { const [, b] = yrs('imm'); mapTo('imm', b); },
    cap: () => { const [a, b] = yrs('imm'); const y0 = a, v0 = V('imm', y0), v1 = V('imm', b);
      return T(`Where did the growth come from? More and more, from people arriving: ${F('imm', v0)} new permanent residents for every 1,000 people in ${y0}, ${F('imm', v1)} in ${b}.`,
        `D’où vient cette croissance? De plus en plus, de l’immigration : ${F('imm', v0)} nouveaux résidents permanents pour 1 000 habitants en ${y0}, ${F('imm', v1)} en ${b}.`); }, ms: 9000 },
  { go: async () => { const [, b] = yrs('o65'); mapTo('o65', b); await wait(300); if (!C().state.wipe) document.querySelector('[data-act=wipe]')?.click(); },
    cap: () => { const [a, b] = yrs('o65'); return T(`The country also grew older. Left of the line, ${a}: ${F('o65', V('o65', a))} of Canadians were 65 or over. Right of it, ${b}: ${F('o65', V('o65', b))}.`,
      `Le pays a aussi vieilli. À gauche de la ligne, ${a} : ${F('o65', V('o65', a))} des Canadiens avaient 65 ans ou plus. À droite, ${b} : ${F('o65', V('o65', b))}.`); }, ms: 9500,
    leave: () => { if (C().state.wipe) document.querySelector('[data-act=wipe]')?.click(); } },
  { go: async () => { const m = C().M.starts; mapTo('starts', m.years[0]); await wait(400); const [a, b] = m.years; await sweep('starts', a, b, 5000); },
    cap: () => { const [a, b] = yrs('starts'); return T(`Homes are a different story. New homes started for every 1,000 residents: ${F('starts', V('starts', a))} in ${a}, ${F('starts', V('starts', b))} in ${b}.`,
      `Le logement raconte autre chose. Mises en chantier pour 1 000 habitants : ${F('starts', V('starts', a))} en ${a}, ${F('starts', V('starts', b))} en ${b}.`); }, ms: 9000 },
  { go: async () => { location.hash = '#cl=forest/1985'; await wait(1500); await window.CLIMATE?.loadForest?.(); if (!window.CLIMATE?.state?.playing) document.querySelector('#cl [data-clplay]')?.click(); }, leave: stopClimate,
    cap: () => { const f = window.CLIMATE?.forest; if (!f) return T('The forests: burned and harvested, year by year.', 'Les forêts : brûlées et récoltées, année après année.');
      const s = a => a.reduce((x, y) => x + y, 0), fire = s(f.totals.CAN.fire), cut = s(f.totals.CAN.harvest);
      return T(`The land keeps its own record. From ${f.years[0]} to ${f.years[1]}, satellites saw ${num(fire / 1e6, 1)} million hectares of forest burn and ${num(cut / 1e6, 1)} million harvested. Most of it grows back: this is disturbance, not deforestation.`,
        `Le territoire tient son propre registre. De ${f.years[0]} à ${f.years[1]}, les satellites ont vu brûler ${num(fire / 1e6, 1)} millions d’hectares de forêt et ${num(cut / 1e6, 1)} millions être récoltés. La plupart repousse : c’est une perturbation, pas une déforestation.`); }, ms: 11000 },
  { go: async () => { location.hash = '#cl=ice/2020/g57'; await wait(1200); },
    cap: () => { const g = window.CLIMATE?.data?.G?.glaciers?.find(x => x.id === '57'); if (!g) return T('In the Rockies, the glaciers are thinning.', 'Dans les Rocheuses, les glaciers s’amincissent.');
      const c = window.CLIMATE.cum(g).filter(Boolean), last = c.at(-1);
      return T(`High in the Rockies, Peyto Glacier has been measured every year since ${g.b[0]}. Added up, it has lost ${num(-last[1], 1)} metres of water spread over the whole glacier, about ${num(-last[1] / 0.9, 0)} metres of ice.`,
        `Haut dans les Rocheuses, le glacier Peyto est mesuré chaque année depuis ${g.b[0]}. Au total, il a perdu ${num(-last[1], 1)} mètres d’eau répartis sur tout le glacier, environ ${num(-last[1] / 0.9, 0)} mètres de glace.`); }, ms: 10000 },
  { go: async () => { location.hash = '#wa='; await wait(1500); },
    cap: () => { const w = window.WATER?.data; if (!w?.in_effect?.length) return T('And some gaps are still open.', 'Et certains écarts restent à combler.');
      const [m0, n0] = w.in_effect[0], [m1, n1] = w.in_effect.at(-1);
      return T(`And some gaps are still open. In ${m0.slice(0, 4)}, ${n0} long-term drinking water advisories were in effect on First Nations public water systems. Most have since been lifted. As of ${monthName(m1)}, ${n1} remain.`,
        `Et certains écarts restent à combler. En ${m0.slice(0, 4)}, ${n0} avis à long terme sur la qualité de l’eau potable étaient en vigueur dans les réseaux publics des Premières Nations. La plupart ont été levés depuis. En ${monthName(m1)}, il en reste ${n1}.`); }, ms: 10500 },
  { kind: 'card', end: true, t: () => T('Now it’s your turn', 'À vous maintenant'), s: () => T('Every number here links back to the table it came from. Drag the map sideways to travel through time, or start with your own life.', 'Chaque chiffre renvoie au tableau d’où il vient. Glissez la carte de côté pour voyager dans le temps, ou commencez par votre propre vie.'), ms: 0 },
];

// ---------------------------------------------------------------- player
const J = { on: false, i: 0, paused: false, token: 0 };
const el = document.createElement('div'); el.id = 'journey'; el.hidden = true;
el.innerHTML = `<div class="jcard" hidden><div class="jgrain"></div><div class="jin"><div class="jk"></div><h1></h1><p></p><div class="jend" hidden></div></div></div>
  <div class="jbar"><div class="jdots"></div><p class="jcap" aria-live="polite"></p>
    <div class="jctl"><button data-j="prev" aria-label="${T('Previous', 'Précédent')}">‹</button><button data-j="pause" class="jp"></button><button data-j="next" aria-label="${T('Next', 'Suivant')}">›</button><button data-j="x" class="jx" aria-label="${T('End the journey', 'Terminer le voyage')}">×</button></div></div>`;
document.body.appendChild(el);
const card = el.querySelector('.jcard'), cap = el.querySelector('.jcap');
function dots() { el.querySelector('.jdots').innerHTML = SCENES.map((_, k) => `<i class="${k < J.i ? 'done' : k === J.i ? 'now' : ''}"></i>`).join(''); }
function setPause(p) { J.paused = p; el.querySelector('.jp').textContent = p ? T('▶ Resume', '▶ Reprendre') : '❚❚'; el.querySelector('.jp').setAttribute('aria-label', p ? T('Resume', 'Reprendre') : T('Pause', 'Pause')); el.classList.toggle('paused', p); }
async function hold(ms, tok) { let left = ms; while (left > 0) { if (tok !== J.token || !J.on) return false; await wait(100); if (!J.paused) left -= 100; } return tok === J.token; }
async function play(i) {
  const tok = ++J.token; SCENES[J.i]?.leave?.(); J.i = Math.max(0, Math.min(SCENES.length - 1, i)); dots(); const sc = SCENES[J.i];
  if (sc.kind === 'card') {
    card.hidden = false; el.classList.add('carded'); card.querySelector('.jk').textContent = T('The Canadian Data Project presents', 'Le Canadian Data Project présente');
    card.querySelector('h1').textContent = sc.t(); card.querySelector('p').textContent = sc.s(); cap.textContent = '';
    const end = card.querySelector('.jend'); end.hidden = !sc.end;
    if (sc.end) { end.innerHTML = `<button data-jgo="life">${T('Your life in Canada', 'Votre vie au Canada')}</button><button data-jgo="map">${T('Explore the map', 'Explorer la carte')}</button>`; return; }
    if (!(await hold(sc.ms, tok))) return; return play(J.i + 1); }
  card.hidden = true; el.classList.remove('carded'); cap.textContent = '';
  const going = Promise.resolve(sc.go?.()); await Promise.race([going, wait(1600)]); if (tok !== J.token) return;
  const show = () => { const t = sc.cap(); if (t === cap.textContent) return; cap.textContent = t; cap.classList.remove('in'); void cap.offsetWidth; cap.classList.add('in'); };
  show(); going.then(() => { if (tok === J.token) show(); });
  if (!(await hold(sc.ms, tok))) return; play(J.i + 1);
}
function start() { window.CTX2?.closeHome?.(); document.body.classList.remove('home-on'); J.on = true; el.hidden = false; document.body.classList.add('journey-on'); setPause(false); play(0); }
function end(to) { SCENES[J.i]?.leave?.(); J.on = false; J.token++; el.hidden = true; document.body.classList.remove('journey-on');
  if (to === 'life') { window.SHELL?.go('map'); setTimeout(() => { window.CTX2?.openHome?.(); setTimeout(() => document.getElementById('life-y')?.focus(), 200); }, 200); }
  else if (to === 'map') window.SHELL?.go('map'); }
el.addEventListener('click', e => { const b = e.target.closest('[data-j]'); if (b) { const a = b.dataset.j;
    if (a === 'pause') setPause(!J.paused); if (a === 'next') { setPause(false); play(J.i + 1); } if (a === 'prev') { setPause(false); play(J.i - 1); } if (a === 'x') end(); return; }
  const g = e.target.closest('[data-jgo]'); if (g) end(g.dataset.jgo); });
// taking over: any touch outside the caption bar pauses the film so the person can explore; Resume carries on
addEventListener('pointerdown', e => { if (J.on && !J.paused && !e.target.closest('#journey .jbar, #journey .jcard')) setPause(true); }, true);
addEventListener('keydown', e => { if (!J.on) return; if (e.key === 'Escape') end(); if (e.key === ' ') { setPause(!J.paused); e.preventDefault(); } if (e.key === 'ArrowRight' && e.altKey) play(J.i + 1); });
window.JOURNEY = { start, end, get on() { return J.on; } };
if (new URLSearchParams(location.search).get('journey') === '1') setTimeout(start, 2500);
