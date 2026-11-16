// English / French. The choice is remembered on this device only; the first visit follows the browser's language.
// T(en, fr) returns the French text when French is on and a French text exists; otherwise the English.
// Data terms use the publishers' own French titles (Statistics Canada, Indigenous Services Canada), not machine translation.
const KEY = 'ctt-lang';
let lang = 'en';
try { lang = localStorage.getItem(KEY) || ((navigator.language || '').toLowerCase().startsWith('fr') ? 'fr' : 'en'); } catch (e) { lang = (navigator.language || '').toLowerCase().startsWith('fr') ? 'fr' : 'en'; }
const q = new URLSearchParams(location.search).get('lang'); if (q === 'fr' || q === 'en') lang = q;
document.documentElement.lang = lang;
window.LANG = lang;
window.T = (en, fr) => lang === 'fr' && fr ? fr : en;
window.setLang = l => { try { localStorage.setItem(KEY, l); } catch (e) { /* storage blocked: the choice lasts for this page only */ }
  const u = new URL(location.href); u.searchParams.set('lang', l); location.replace(u.toString()); };
