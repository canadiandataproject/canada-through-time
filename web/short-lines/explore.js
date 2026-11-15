// v3 lines Short: any yearly series passed in the configuration (values computed and asserted by the config builder from
// registered raw files), with optional dated event markers. Every frame is a pure function of its number
// (window.CTT.renderFrame), so renders are reproducible. Missing years are gaps, never zero. Lines grow between years as
// animation (disclosed on screen).
const Q = new URLSearchParams(location.search);
const SC = JSON.parse(new TextDecoder().decode(Uint8Array.from(atob((Q.get('studio') || '').replace(/-/g, '+').replace(/_/g, '/')), c => c.charCodeAt(0))));
await Promise.all(['600 20px "Public Sans"', '500 20px "Public Sans"', '700 20px "Source Serif 4"', '600 20px "Source Serif 4"'].map(f => document.fonts.load(f)));
const T = await (await import('../short-themes/theme.js')).applyTheme(SC);   // look: colours and fonts for SVG drawing
const $ = id => document.getElementById(id);
const lerp = (a, b, t) => a + (b - a) * t, clamp01 = x => Math.max(0, Math.min(1, x)), ease = t => t * t * (3 - 2 * t);

// ---------------------------------------------------------------- data
const YR = []; for (let y = SC.years[0]; y <= SC.years[1]; y++) YR.push(y);
const K = YR.length;
const S = SC.series.map(g => {
  const cum = YR.map(y => g.values[y] ?? null), k0 = cum.findIndex(v => v != null);
  return { ...g, cum, k0, y0: YR[k0] };
});
const fmtM = v => (SC.prefix || '') + v.toFixed(SC.decimals ?? 2) + (SC.suffix || '');
const lastAt = (s, k) => { for (let j = Math.min(k, K - 1); j >= 0; j--) if (s.cum[j] != null) return [j, s.cum[j]]; return null; };

// ---------------------------------------------------------------- timeline
const fps = SC.fps || 30;
const SEG = []; let acc = 0, u = 0;
for (const st of SC.plan) {
  if (st.kind === 'jump') { u = st.to; continue; }   // cold open: start the timeline at another point
  const n = Math.round(st.s * fps);
  if (st.kind === 'run') { SEG.push({ ...st, n, u0: u, u1: st.to }); u = st.to; } else SEG.push({ ...st, n, u0: u, u1: u });
}
for (const s of SEG) { s.f0 = acc; acc += s.n; s.f1 = acc; }
const N = acc, fHook = Math.round(SC.hook.seconds * fps);
const shape = { linear: t => t, out: t => 1 - (1 - t) * (1 - t), in: t => t * t, inout: ease };
function where(f) {
  const s = SEG.find(x => f >= x.f0 && f < x.f1) || SEG.at(-1), t = s.n ? (f - s.f0) / s.n : 0;
  return { s, t, u: s.kind === 'run' ? lerp(s.u0, s.u1, (shape[s.ease] || shape.linear)(t)) : s.kind === 'loop' ? (SC.loopTo ?? 0) : s.u0 };
}

// ---------------------------------------------------------------- chart geometry
const X0 = 52, X1 = 428, Y0 = 470, Y1 = SC.chartBottom || 985, [VMIN, VMAX] = SC.yRange;
const px = k => X0 + (X1 - X0) * k / (K - 1), py = v => Y0 + (Y1 - Y0) * (VMAX - v) / (VMAX - VMIN);
function grid(alpha) {
  let o = `<g opacity="${alpha.toFixed(3)}">`;
  for (let v = SC.gridStart; v <= VMAX; v += SC.gridStep) {
    o += `<line x1="${X0}" x2="${X1 + 6}" y1="${py(v).toFixed(1)}" y2="${py(v).toFixed(1)}" stroke="${T.grid}" stroke-width="1"/>`;
    o += `<text x="${X0}" y="${(py(v) - 6).toFixed(1)}" font-family="${T.sans}" font-size="14" fill="${T.ink3}">${(SC.prefix || '') + v + (SC.suffix || '')}</text>`;
  }
  for (const y of SC.xTicks) { const k = y - YR[0]; o += `<text x="${px(k).toFixed(1)}" y="${(SC.panel ? SC.panel.bottom : Y1) + 24}" text-anchor="middle" font-family="${T.sans}" font-size="14" fill="${T.ink3}">${y}</text>`; }
  return o + '</g>';
}
function path(s, uu) {
  // segments between consecutive published years; a missing year breaks the line
  const kEnd = Math.floor(uu), t = uu - kEnd; let d = '', pen = false, tip = null;
  for (let k = s.k0; k <= Math.min(kEnd, K - 1); k++) {
    const v = s.cum[k]; if (v == null) { pen = false; continue; }
    d += (pen ? 'L' : 'M') + px(k).toFixed(1) + ',' + py(v).toFixed(1); pen = true; tip = [px(k), py(v)];
  }
  const kn = kEnd + 1;   // the next year's segment grows in as animation
  if (pen && t > 0 && kn < K && s.cum[kn] != null && s.cum[kEnd] != null) {
    const x = lerp(px(kEnd), px(kn), t), y = lerp(py(s.cum[kEnd]), py(s.cum[kn]), t); d += `L${x.toFixed(1)},${y.toFixed(1)}`; tip = [x, y];
  } else if (t > 0 && kn < K && s.cum[kn] != null && kn === s.k0) {   // first point appears
    tip = [px(kn), py(s.cum[kn])]; d += `M${tip[0].toFixed(1)},${tip[1].toFixed(1)}`;
  }
  return { d, tip };
}
let FR = 0;
function chart(uu, alpha, focus) {
  const k = Math.round(uu);
  let o = grid(alpha), labs = [];
  if (SC.panel) {                            // a second, separate panel (own scale, no shared axis) of yearly bars
    const P = SC.panel, vals = YR.map(y => P.values[y] ?? null), mx = Math.max(...vals.filter(v => v != null)), bw = (X1 - X0) / K * 0.72;
    o += `<text x="${X0}" y="${P.top - 10}" font-family="${T.sans}" font-size="16" font-weight="700" fill="${P.color}" opacity="${alpha.toFixed(3)}">${P.label}</text>`;
    o += `<line x1="${X0}" x2="${X1 + 6}" y1="${P.bottom}" y2="${P.bottom}" stroke="${T.grid}" stroke-width="1" opacity="${alpha.toFixed(3)}"/>`;
    let last = null;
    vals.forEach((v, k) => { if (v == null) return; const g = clamp01(uu - k + 1); if (g <= 0) return;
      const h = (P.bottom - P.top) * v / mx * ease(g), x = px(k) - bw / 2;
      o += `<rect x="${x.toFixed(1)}" y="${(P.bottom - h).toFixed(1)}" width="${bw.toFixed(1)}" height="${h.toFixed(1)}" fill="${P.color}" opacity="${(alpha * (focus && !focus.has(P.label) ? 0.25 : 0.9)).toFixed(3)}"/>`;
      if (k <= Math.round(uu)) last = [k, v]; });
    const kk = Math.round(uu);
    if (last) o += `<text x="${(X1 + 18).toFixed(1)}" y="${(P.top + 30).toFixed(1)}" font-family="${T.sans}" font-size="21" font-weight="600" fill="${T.ink1}" opacity="${alpha.toFixed(3)}"><tspan fill="${P.color}">●</tspan> ${last[1].toLocaleString('en-CA')}${last[0] < kk ? ` <tspan font-size="15" fill="${T.ink3}">(${YR[last[0]]})</tspan>` : ''}</text>`;
  }
  for (const ev of SC.events || []) {          // dated event markers appear as the timeline reaches them
    const ke = ev.year - YR[0] + (ev.frac || 0), a = alpha * clamp01((uu - ke) * 3);
    if (a <= 0) continue;
    const x = px(ke).toFixed(1);
    o += `<line x1="${x}" x2="${x}" y1="${Y0 - 10}" y2="${SC.panel ? SC.panel.bottom : Y1}" stroke="${T.ink1}" stroke-width="1.5" stroke-dasharray="5 5" opacity="${(a * 0.8).toFixed(3)}"/>`;
    o += `<text x="${(ev.anchor === 'end' ? +x - 6 : +x + 6).toFixed(1)}" text-anchor="${ev.anchor || 'start'}" y="${(Y0 - 14 + (ev.row || 0) * 20).toFixed(1)}" font-family="${T.sans}" font-size="16" font-weight="700" fill="${T.ink1}" opacity="${a.toFixed(3)}">${ev.label}</text>`;
  }
  // faint preview of every full line, so the first frame already shows where this goes (published values, not a forecast)
  if (SC.ghost) for (const s of S) o += `<path d="${path(s, K - 1).d}" fill="none" stroke="${s.color}" stroke-width="2" stroke-dasharray="2 5" opacity="${(alpha * SC.ghost).toFixed(3)}"/>`;
  for (const s of S) {
    const { d, tip } = path(s, uu); if (!tip) continue;
    const a = alpha * (focus && !focus.has(s.name) && !focus.has(s.label) ? 0.18 : 1), gi = 'ga' + s.name;
    if ((s.area ?? SC.area) && !d.slice(1).includes('M')) {   // soft area under an unbroken line
      o += `<defs><linearGradient id="${gi}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${s.color}" stop-opacity=".28"/><stop offset="1" stop-color="${s.color}" stop-opacity="0"/></linearGradient></defs>`;
      o += `<path d="${d}L${tip[0].toFixed(1)},${Y1}L${px(s.k0).toFixed(1)},${Y1}Z" fill="url(#${gi})" opacity="${a.toFixed(3)}"/>`;
    }
    o += `<path d="${d}" style="color:${s.color}" fill="none" stroke="${s.color}" stroke-width="${s.width || 4}" stroke-linejoin="round" stroke-linecap="round" opacity="${a.toFixed(3)}"/>`;
    const ph = ((FR % 24) / 24);                   // pulse ring on the moving tip
    o += `<circle cx="${tip[0].toFixed(1)}" cy="${tip[1].toFixed(1)}" r="${(7 + 14 * ph).toFixed(1)}" fill="none" stroke="${s.color}" stroke-width="2" opacity="${(a * 0.6 * (1 - ph)).toFixed(3)}"/>`;
    o += `<circle cx="${tip[0].toFixed(1)}" cy="${tip[1].toFixed(1)}" r="7" fill="${s.color}" stroke="${T.halo}" stroke-width="2.5" opacity="${a.toFixed(3)}"/>`;
    const la = lastAt(s, k); if (la) labs.push({ s, y: tip[1], v: la[1], a });
  }
  // labels at the right edge of the plot, pushed apart so they never overlap
  labs.sort((p, q) => p.y - q.y); const GAP = 27;
  for (let i = 1; i < labs.length; i++) labs[i].ly = Math.max(labs[i].y, (labs[i - 1].ly ?? labs[i - 1].y) + GAP);
  if (labs.length) labs[0].ly = labs[0].ly ?? labs[0].y;
  const over = labs.length ? labs.at(-1).ly - (Y1 + 4) : 0; if (over > 0) labs.forEach(l => l.ly -= over);
  for (const l of labs) {
    o += `<text x="${X1 + 18}" y="${(l.ly + 6).toFixed(1)}" font-family="${T.sans}" font-size="21" font-weight="600" fill="${T.ink1}" opacity="${l.a.toFixed(3)}"><tspan fill="${l.s.color}">●</tspan> ${l.s.label} <tspan font-weight="500" fill="${T.ink2}">${fmtM(l.v)}</tspan></text>`;
  }
  return o;
}

// ---------------------------------------------------------------- summary: first and last published value per series
function sumChart(grow) {
  let o = '', y = 0;
  S.forEach((s, i) => { const g = ease(clamp01(grow * S.length - i)), a = s.cum[s.k0], b = lastAt(s, K - 1);
    o += `<text x="0" y="${y + 24}" font-family="${T.sans}" font-size="19" font-weight="700" fill="${s.color}" opacity="${g.toFixed(3)}">${s.label}</text>`;
    o += `<text x="0" y="${y + 54}" font-family="${T.sans}" font-size="24" font-weight="600" fill="${T.ink1}" opacity="${g.toFixed(3)}">${s.y0}: ${fmtM(a)}  →  ${YR[b[0]]}: ${fmtM(b[1])}  (${b[1] >= a ? '+' : '−'}${Math.abs((b[1] / a - 1) * 100).toFixed(0)}%)</text>`;
    y += 74; });
  return `<svg width="640" height="${y}">${o}</svg>`;
}

// ---------------------------------------------------------------- frame
$('kicker').textContent = SC.kicker; $('q').innerHTML = SC.hook.question; $('note').innerHTML = SC.note;
$('yearbox').querySelector('.sub').innerHTML = SC.yearSub;
const sm = $('summary'); sm.querySelector('.kick').textContent = SC.summary.kicker; sm.querySelector('.big').textContent = SC.summary.big;
sm.querySelector('.line').innerHTML = SC.summary.line; sm.querySelector('.sub').innerHTML = SC.summary.sub;
function cueAt(f) {
  if (f <= 0) return '';
  const a = where(f), b = where(f - 1);
  if (a.s !== b.s && a.s.kind === 'beat' && a.s.sfx) return a.s.sfx;
  if (a.s !== b.s && a.s.kind === 'summary') return 'hit';
  if (a.s.kind === 'run' && a.s.riser && a.s.f1 - f === Math.round(1.6 * fps)) return 'riser';
  const ya = YR[Math.floor(a.u)], yb = YR[Math.floor(b.u)];
  if (a.s.kind === 'run' && ya !== yb && ya % 10 === 0) return 'tick';
  return '';
}

// rewind effect for cold opens: shown while a run goes backwards in time (pure function of the frame)
const rewEl = document.createElement('div'); rewEl.id = 'rewind';
rewEl.innerHTML = '<div class="rw-lines"></div><div class="rw-tag">◀◀ <span></span></div>';
Object.assign(rewEl.style, { position: 'absolute', inset: '0', pointerEvents: 'none', opacity: '0', zIndex: '20' });
document.getElementById('stage').appendChild(rewEl);
const rwCss = document.createElement('style');
rwCss.textContent = `#rewind .rw-lines{position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(255,255,255,.10) 0 2px,transparent 2px 6px);mix-blend-mode:overlay}
#rewind .rw-tag{position:absolute;left:50%;top:600px;transform:translateX(-50%);padding:14px 26px 12px;background:rgba(10,14,20,.86);color:#fff;font:700 54px/1 var(--sans);letter-spacing:.04em;border-radius:6px;white-space:nowrap}`;
document.head.appendChild(rwCss);
function rewindAt(w, f) {
  const s = w.s; if (!(s.kind === 'run' && s.u1 < s.u0)) { rewEl.style.opacity = 0; return; }
  const t = (f - s.f0) / Math.max(1, s.n); rewEl.style.opacity = Math.min(1, Math.sin(Math.PI * t) * 1.6).toFixed(3);
  rewEl.querySelector('span').textContent = YR[Math.max(0, Math.min(YR.length - 1, Math.round(w.u)))];
}

function renderFrame(f) {
  f = Math.max(0, Math.min(N - 1, Math.round(f)));
  FR = f; const w = where(f); rewindAt(w, f); const s = w.s, k = Math.round(w.u), y = YR[k];
  const inBeat = s.kind === 'beat', inSum = s.kind === 'summary', inLoop = s.kind === 'loop';
  const tIn = (n = 10) => clamp01((f - s.f0 + 1) / n), tOut = (n = 10) => clamp01((s.f1 - f) / n);
  const focus = inBeat && s.focus ? new Set(s.focus) : null;
  const sumA = inSum ? tIn(12) : inLoop ? clamp01(1 - (f - s.f0) / (s.n * 0.35)) : 0;
  const barsA = inSum ? 1 - tIn(12) : inLoop ? ease(clamp01(((f - s.f0) / s.n - 0.3) / 0.7)) : 1;
  $('chart').innerHTML = chart(w.u, barsA, focus && (s.instant ? tOut(8) : Math.min(tIn(8), tOut(8))) > 0.5 ? focus : null);
  $('year').textContent = y; $('yearbox').style.opacity = barsA.toFixed(3);
  $('head').style.opacity = (SC.keepHead ? 1 : inSum ? 1 - tIn(12) : inLoop ? barsA : 1).toFixed(3);
  const bt = $('beat');
  if (inBeat) { const a = s.instant ? tOut(9) : Math.min(tIn(9), tOut(9)); bt.querySelector('.kick').textContent = s.kicker; bt.querySelector('.big').textContent = s.big; bt.querySelector('.line').innerHTML = s.line;
    bt.style.opacity = a; bt.style.top = (s.cardTop || 560) + 'px'; bt.style.transform = `translateY(${((1 - ease(a)) * 24).toFixed(1)}px)`; } else bt.style.opacity = 0;
  sm.querySelector('.chart').innerHTML = SC.summary.chart === false ? '' : sumChart(inSum ? clamp01((f - s.f0 - 8) / 40) : 1); sm.style.opacity = sumA.toFixed(3);
  sm.style.transform = `scale(${(0.96 + 0.04 * ease(inSum ? tIn(14) : 1)).toFixed(4)})`;
  $('glow').style.opacity = (inBeat ? Math.min(tIn(9), tOut(9)) : inSum ? sumA * 0.8 : 0).toFixed(3);
  $('flash').style.opacity = 0;
  for (let d = 0; d < 6; d++) { const c = cueAt(f - d); if (c === 'hit') { $('flash').style.opacity = (0.35 * (1 - d / 6)).toFixed(3); break; } }
  return { frame: f, year: String(y), phase: f < fHook ? 'intro' : s.kind, title: SC.title,
    annotation: inBeat ? `${s.kicker}: ${s.big}. ${s.line.replace(/<[^>]+>/g, '')}` : inSum ? `${SC.summary.big} ${SC.summary.line.replace(/<[^>]+>/g, '')}` : '', cue: cueAt(f) };
}
window.CTT = { ready: false, frameCount: N, fps, renderFrame, config: SC, years: YR.map(String) };
window.CTX = { S, YR, SEG, where };
renderFrame(0);
setTimeout(() => { window.CTT.ready = true; }, 300);
