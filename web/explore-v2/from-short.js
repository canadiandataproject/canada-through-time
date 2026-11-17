// "From the Short" landing: a video description links here with ?s=<number>#<view>. The view opens as usual; this adds a
// slim banner that names the video, says what's on screen, and offers one next question. Dismissed once per visit.
const SHORTS = {
  7: { t: 'Where Ottawa collects more than it spends', say: 'Federal money collected minus spent, per person, by province.', next: ['Federal spending per person, by province', '#fedexp-2025'] },
  8: { t: "How much ice have Canada's glaciers lost?", say: 'Every Canadian glacier measured 40+ years, as a running total.', next: ['Which weather stations have warmed most?', '#cl=temp/2020'] },
  9: { t: "How many of Canada's weather stations have warmed?", say: 'Each station vs its own 1961–1990 average. Drag the year.', next: ['How much ice have the glaciers lost?', '#cl=ice/2025/g57'] },
  10: { t: "Which province has Canada's lowest unemployment?", say: 'Unemployment rate by province. Drag the year back to 1976.', next: ['Where are wages highest?', '#inc-2023'] },
  11: { t: 'Did temporary foreign workers hold down wages?', say: 'Temporary residents as a share of each province.', next: ['Unemployment rate by province', '#ur-2025'] },
  12: { t: "Ottawa's $493 billion receipt", say: 'Federal spending in 2025–26. Tap a department to see its own receipt.', next: ['Federal spending per person, by province', '#fedexp-2025'] },
  13: { t: "Who got Ottawa's biggest contracts?", say: 'Every disclosed federal contract: by department, vendor and province.', next: ["Ottawa's $493B receipt", '#mn=spend/2026'] },
  14: { t: 'Toronto: one city, 1,227 neighbourhoods', say: 'Tap any neighbourhood, then "Share card" to compare it with the city.', next: ['Now try Edmonton', '#nb=835/hhinc'] },
  16: { t: 'Edmonton spread out: 1975 to 2020', say: 'Each colour is the first year a 100 m square was built up. Press play or drag the year slider to travel through time.', next: ['Now try Calgary', '#cl=sprawl/2020/ccalgary'] },
  15: { t: "Canada's temporary residents: 1.3M → 2.9M → 2.8M", say: 'Temporary residents as a share of each province. Drag the year.', next: ['Where do new permanent residents settle?', '#prdest-2025'] },
};
const n = +new URLSearchParams(location.search).get('s');
const k = 'ctt-from-' + n;
let seen = false; try { seen = sessionStorage.getItem(k) === '1'; } catch (e) { /* storage blocked */ }
if (SHORTS[n] && !seen) {
  const S = SHORTS[n], esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const el = document.createElement('aside'); el.id = 'from-short'; el.setAttribute('role', 'status');
  el.innerHTML = `<div class="fs-in"><span class="fs-k">From the Short</span><b>${esc(S.t)}</b><span class="fs-say">${esc(S.say)}</span>
    <a class="fs-next" href="${S.next[1]}">Next: ${esc(S.next[0])} →</a></div><button class="fs-x" aria-label="Close">×</button>`;
  const close = () => { el.remove(); document.body.classList.remove('from-short-on'); try { sessionStorage.setItem(k, '1'); } catch (e) { /* ignore */ } };
  el.querySelector('.fs-x').onclick = close;
  el.querySelector('.fs-next').addEventListener('click', () => setTimeout(close, 50));
  const place = () => { document.body.appendChild(el); document.body.classList.add('from-short-on'); };
  // the welcome screen would sit on top of the view the video promised: skip it for visitors arriving from a Short
  try { localStorage.setItem('ctt-home-seen', '1'); } catch (e) { /* ignore */ }
  if (document.readyState === 'complete') place(); else addEventListener('load', place);
  // after a few seconds, shrink to a one-line chip so it never hides the controls underneath (tap to expand again)
  setTimeout(() => el.classList.add('mini'), 7000);
  el.addEventListener('click', e => { if (el.classList.contains('mini') && !e.target.closest('.fs-x')) { e.preventDefault(); el.classList.remove('mini'); setTimeout(() => el.classList.add('mini'), 7000); } });
  setTimeout(() => window.CTX2?.closeHome?.(), 400);
}
