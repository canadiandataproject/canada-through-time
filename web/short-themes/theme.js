// Shared look for the v3 Short engines. A configuration's `theme` ("dark", "broadcast", "notebook") loads
// short-themes/<theme>.css on top of the engine's own stylesheet, adds the theme's decorative layers, waits for its
// fonts, and returns the colour tokens the engines draw SVG with. No theme = the original cream look.
const BASE = { page: '#EFEADB', ink1: '#1F1D14', ink2: '#4A4636', ink3: '#655F4E', accent: '#B8472F', land: '#FBF8EF', landStroke: '#B9B19C',
  grid: '#D6CFBC', zero: '#8C8672', other: '#ABA592', barInk: '#FFFFFF', halo: '#FBF8EF', sans: 'Public Sans', num: 'Source Serif 4' };
export async function applyTheme(SC) {
  const th = SC.theme;
  if (th) {
    document.body.classList.add('theme-' + th);
    const link = Object.assign(document.createElement('link'), { rel: 'stylesheet', href: `../short-themes/${th}.css` });
    await new Promise((ok, bad) => { link.onload = ok; link.onerror = () => bad(new Error('theme ' + th)); document.head.appendChild(link); });
    const stage = document.getElementById('stage');
    for (const cls of ['deco-a', 'deco-b', 'deco-c']) { const d = document.createElement('div'); d.className = cls; stage.insertBefore(d, stage.children[1]); }
    if (SC.channel) { const b = document.createElement('div'); b.id = 'bug'; b.textContent = SC.channel; stage.appendChild(b); }
  }
  const cs = getComputedStyle(document.documentElement), v = k => cs.getPropertyValue('--t-' + k).trim();
  const T = {}; for (const k of Object.keys(BASE)) T[k] = v(k.replace(/[A-Z]/g, c => '-' + c.toLowerCase())) || BASE[k];
  const fonts = (v('fonts') || '').split('|').map(s => s.trim().replace(/^"|"$/g, '')).filter(Boolean);
  await Promise.all(fonts.map(f => document.fonts.load(f)));
  return T;
}
