// Zoom buttons for the flat maps (neighbourhoods, climate, water advisories): +, − and "fit", centred at the bottom of the map,
// matching the national map's buttons. Wheel, drag and pinch still work as before; these are for people who don't use them.
window.MAPBTNS = (box, getDeck, fit) => {
  if (box.querySelector('.mapbtns')) return;
  const T = window.T || (e => e);
  const d = document.createElement('div'); d.className = 'mapbtns'; d.setAttribute('role', 'toolbar');
  d.innerHTML = `<button data-z="1" aria-label="${T('Zoom in', 'Zoom avant')}">+</button><button data-z="-1" aria-label="${T('Zoom out', 'Zoom arrière')}">−</button><button data-z="0" aria-label="${T('Fit the whole map', 'Afficher toute la carte')}">⌂</button>`;
  box.appendChild(d);
  d.addEventListener('pointerdown', e => e.stopPropagation());
  d.addEventListener('click', e => { const b = e.target.closest('[data-z]'); if (!b) return; e.stopPropagation(); const dk = getDeck(); if (!dk) return;
    if (b.dataset.z === '0') { fit(); return; }
    const vs = dk.viewState || {}, cur = vs.target ? vs : Object.values(vs).find(v => v && v.target); if (!cur) return;
    const z = Math.max(cur.minZoom ?? -Infinity, Math.min(cur.maxZoom ?? Infinity, cur.zoom + (+b.dataset.z) * 0.7));
    dk.setProps({ initialViewState: { ...cur, zoom: z, transitionDuration: 300 } }); });
};
