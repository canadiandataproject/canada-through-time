"""Style frames for Canada Through Time: A Whiteout, B Survey night, C Blue hour.
Each direction: desktop map screen (1440x900), phone (390x844 @2x), Short opener (1080x1920).
Real geometry (StatCan Lambert, metres) and real data: Alberta 1,665,717 (1971) -> 5,101,050 (2026, preliminary).
Static visual exploration only: no app code is touched."""
import json, base64, io, math
from pathlib import Path
import numpy as np
from PIL import Image

D = Path('/home/claude/canada-through-time/web/data')
OUT = Path('/tmp/sf/out'); OUT.mkdir(parents=True, exist_ok=True)
prov = json.load(open(D / 'provinces.geojson'))['features']
ctx = json.load(open(D / 'context_countries.geojson'))['features']
lakes = [f for f in json.load(open(D / 'lakes.geojson'))['features']]
pop = json.load(open(D / 'population.json'))
P71 = {g: pop['series'][g][0] for g in pop['series']}
P26 = {g: pop['series'][g][-1] for g in pop['series']}
assert P71['AB'] == 1665717 and P26['AB'] == 5101050 and pop['dates'][0] == '1971-07-01' and pop['dates'][-1] == '2026-07-01'
P71['NT+NU'] = P71.get('NT+NU', P71.get('NT', 0));
ANCH = {f['properties']['abbr']: (f['properties']['lx'], f['properties']['ly']) for f in prov}

rel = np.array(Image.open(D / 'relief/relief_canada_3km.png')).astype(float)
SH = np.where(rel[..., 0] > 127, 1, -1) * rel[..., 3] / 255.0       # +highlight / -shadow
RB = [3660e3, 630e3, 9040e3, 5270e3]; RH, RW = SH.shape

def font_face(name, file, fmt='woff2', wght='100 900'):
    b = base64.b64encode(open(f'/tmp/sf/fonts/{file}', 'rb').read()).decode()
    return f"@font-face{{font-family:'{name}';src:url(data:font/{fmt};base64,{b}) format('woff2');font-weight:{wght};font-stretch:50% 200%;}}"

# neighbours (USA, Greenland, ...) get their own relief from the same Natural Earth SR_50M source, 6 km cells
NB = [2300e3, -1000e3, 10600e3, 6700e3]
def _nbr_relief():
    cache = Path('/tmp/sf/nbr_relief.npy')
    if cache.exists(): return np.load(cache)
    from pyproj import Transformer
    from PIL import ImageDraw
    Image.MAX_IMAGE_PIXELS = None
    src = np.asarray(Image.open('/home/claude/canada-through-time/data/raw/naturalearth/SR_50M.tif').convert('L'), dtype=np.float32)
    H, W = src.shape; cell = 6000.0; X0, Y0, X1, Y1 = NB
    nx, ny = int((X1 - X0) / cell), int((Y1 - Y0) / cell)
    gx, gy = np.meshgrid(X0 + (np.arange(nx) + .5) * cell, Y1 - (np.arange(ny) + .5) * cell)
    lon, lat = Transformer.from_crs(3347, 4326, always_xy=True).transform(gx, gy)
    px = np.clip(((lon + 180) / 360 * W).astype(int), 0, W - 1); py = np.clip(((90 - lat) / 180 * H).astype(int), 0, H - 1)
    g = src[py, px]
    mask = Image.new('L', (nx, ny), 0); d = ImageDraw.Draw(mask)
    for f in ctx:
        for r in rings(f['geometry']): d.polygon([((x - X0) / cell, (Y1 - y) / cell) for x, y in r], fill=255)
    m = np.asarray(mask) > 0
    dev = (g - 205.1) / 255.0                                   # same flat-ground grey as the Canada layer
    out = np.where(dev > 0, 1, -1) * np.clip(np.abs(dev) * 2.6, 0, 1) * m
    np.save(cache, out); return out

def nbr_relief_png(theme):
    S = _nbr_relief(); hi, lo, k = theme['nrelief_hi'], theme['nrelief_lo'], theme['nrelief_k']
    rgb = np.where((S > 0)[..., None], np.array(hi)[None, None, :], np.array(lo)[None, None, :])
    out = np.dstack([rgb, np.clip(np.abs(S) * k * 255, 0, 255)]).astype(np.uint8)
    buf = io.BytesIO(); Image.fromarray(out, 'RGBA').save(buf, 'PNG'); return base64.b64encode(buf.getvalue()).decode()

def relief_png(theme):
    """Recolour the relief overlay for a theme: highlights and shadows as RGBA."""
    hi, lo, k = theme['relief_hi'], theme['relief_lo'], theme['relief_k']
    a = np.abs(SH) * k
    rgb = np.where((SH > 0)[..., None], np.array(hi)[None, None, :], np.array(lo)[None, None, :])
    out = np.dstack([rgb, np.clip(a * 255, 0, 255)]).astype(np.uint8)
    buf = io.BytesIO(); Image.fromarray(out, 'RGBA').save(buf, 'PNG'); return base64.b64encode(buf.getvalue()).decode()

class View:
    def __init__(s, W, H, cx, cy, mpp, tilt=0.74):
        s.W, s.H, s.cx, s.cy, s.mpp, s.t = W, H, cx, cy, mpp, tilt
    def p(s, x, y):
        return (s.W / 2 + (x - s.cx) / s.mpp, s.H / 2 - (y - s.cy) / s.mpp * s.t)

def rings(geom):
    cs = geom['coordinates']
    if geom['type'] == 'Polygon': cs = [cs]
    for poly in cs:
        for r in poly: yield r

def path_d(geom, v, minpx=1.2):
    out = []
    for r in rings(geom):
        pts = [v.p(*c) for c in r]
        xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
        if max(xs) - min(xs) < minpx and max(ys) - min(ys) < minpx: continue
        if max(xs) < -50 or min(xs) > v.W + 50 or max(ys) < -50 or min(ys) > v.H + 50: continue
        simp = [pts[0]]
        for q in pts[1:]:
            if abs(q[0] - simp[-1][0]) + abs(q[1] - simp[-1][1]) > 0.8: simp.append(q)
        out.append('M' + 'L'.join(f'{a:.1f},{b:.1f}' for a, b in simp) + 'Z')
    return ''.join(out)

def wire(v, step_km, amp, vertical=False, sample_km=6):
    """Wireframe terrain: lines of constant northing displaced by the shaded relief (light up, shadow down)."""
    segs = []
    ys = np.arange(RB[1], RB[3], step_km * 1e3)
    xs = np.arange(RB[0], RB[2], sample_km * 1e3)
    for y in ys:
        row = int((RB[3] - y) / 3e3)
        if not 0 <= row < RH: continue
        pts = []
        for x in xs:
            col = int((x - RB[0]) / 3e3)
            if not 0 <= col < RW: continue
            sx, sy = v.p(x, y); sy -= SH[row, col] * amp
            pts.append((sx, sy))
        if pts: segs.append('M' + 'L'.join(f'{a:.1f},{b:.1f}' for a, b in pts))
    if vertical:
        for x in np.arange(RB[0], RB[2], step_km * 1e3 * 1.6):
            col = int((x - RB[0]) / 3e3)
            if not 0 <= col < RW: continue
            pts = []
            for y in np.arange(RB[1], RB[3], sample_km * 1e3):
                row = int((RB[3] - y) / 3e3)
                if not 0 <= row < RH: continue
                sx, sy = v.p(x, y); sy -= SH[row, col] * amp
                pts.append((sx, sy))
            segs.append('M' + 'L'.join(f'{a:.1f},{b:.1f}' for a, b in pts))
    return ''.join(segs)

SHOW = ['BC', 'AB', 'SK', 'MB', 'ON', 'QC', 'NB', 'NS', 'PE', 'NL', 'YT', 'NT', 'NU']
def col_h(n, v, k): return n / 1e6 * k / v.mpp * 1e3

def columns(v, theme, k, then=False, only=None, w=None):
    """Population columns at each province's label point: solid (now, 2026) or wire (then, 1971)."""
    w = w or max(9, 62e3 / v.mpp)
    out = []
    for g in SHOW:
        if only and g not in only: continue
        n = (P71 if then else P26).get(g)
        if not n: continue
        x, y = v.p(*ANCH[g]); h = col_h(n, v, k); ex = w / 2; ey = w * 0.22
        if then:
            c = theme['wire']
            out.append(f'<g fill="none" stroke="{c}" stroke-width="{theme["wire_w"]*1.3}"><ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{ex:.1f}" ry="{ey:.1f}"/>'
                       f'<ellipse cx="{x:.1f}" cy="{y-h:.1f}" rx="{ex:.1f}" ry="{ey:.1f}"/><path d="M{x-ex:.1f},{y:.1f}V{y-h:.1f}M{x+ex:.1f},{y:.1f}V{y-h:.1f}"/>'
                       + ''.join(f'<ellipse cx="{x:.1f}" cy="{y-h*f:.1f}" rx="{ex:.1f}" ry="{ey:.1f}" opacity=".45"/>' for f in (0.25, 0.5, 0.75)) + '</g>')
        else:
            out.append(f'<g><ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{ex*1.9:.1f}" ry="{ey*1.9:.1f}" fill="{theme["col_shadow"]}"/>'
                       f'<rect x="{x-ex:.1f}" y="{y-h:.1f}" width="{w:.1f}" height="{h:.1f}" fill="url(#colg)"/>'
                       f'<ellipse cx="{x:.1f}" cy="{y-h:.1f}" rx="{ex:.1f}" ry="{ey:.1f}" fill="{theme["col_top"]}"/></g>')
    return ''.join(out)

def voxel_ocean(v, theme, cell):
    """8-bit ocean: small cubes that step up and down in rings spreading from every coast, plus a long swell.
    Height is quantised to four steps for the 8-bit look. Drawn under the land, so coasts cut it cleanly."""
    from matplotlib.path import Path as MPath
    from scipy.ndimage import distance_transform_edt
    tops, side = theme['vox_tops'], theme['vox_side']
    xs = np.arange(0, v.W + cell, cell); ys = np.arange(0, v.H + cell, cell)
    gx, gy = np.meshgrid(xs + cell / 2, ys + cell / 2); pts = np.c_[gx.ravel(), gy.ravel()]
    landm = np.zeros(len(pts), bool)
    for f in prov + ctx:
        for r in rings(f['geometry']):
            poly = np.array([v.p(*c) for c in r])
            if poly[:, 0].max() < 0 or poly[:, 0].min() > v.W or poly[:, 1].max() < 0 or poly[:, 1].min() > v.H: continue
            landm |= MPath(poly).contains_points(pts)
    landm = landm.reshape(gx.shape)
    dist = distance_transform_edt(~landm)                       # cells from the nearest coast
    out = []
    for j in range(len(ys)):
        for i in range(len(xs)):
            if landm[j, i]: continue
            d = dist[j, i]
            w = 1.2 * math.sin(d * 1.15) * math.exp(-d / 9) + 0.45 * math.sin(i * 0.21 + j * 0.09) + 0.25 * math.sin(i * -0.07 + j * 0.31)
            lvl = int(np.clip((w + 1.6) / 3.2 * 4, 0, 3))
            lift = lvl * cell * 0.16
            x, y = xs[i], ys[j]
            out.append(f'<rect x="{x:.0f}" y="{y - lift + cell*0.45:.1f}" width="{cell-1:.0f}" height="{lift + cell*0.25:.1f}" fill="{side}"/>'
                       f'<rect x="{x:.0f}" y="{y - lift:.1f}" width="{cell-1:.0f}" height="{cell*0.72:.1f}" fill="{tops[lvl]}"/>')
    return f'<g>{"".join(out)}</g>'

def nbr_relief_svg(v, theme, nbr):
    (x0, y0), (x1, y1) = v.p(NB[0], NB[3]), v.p(NB[2], NB[1])
    return (f'<clipPath id="nbrc"><path d="{nbr}"/></clipPath><g clip-path="url(#nbrc)"><image href="data:image/png;base64,{nbr_relief_png(theme)}" '
            f'x="{x0:.1f}" y="{y0:.1f}" width="{x1-x0:.1f}" height="{y1-y0:.1f}" preserveAspectRatio="none" opacity="{theme["nrelief_o"]}"/></g>')

def map_svg(v, theme, lens, k_col, wire_step, wire_amp, extra='', focus_g='AB', vox=0):
    """lens = (sx, sy, r) in screen px."""
    land = ''.join(path_d(f['geometry'], v) for f in prov)
    nbr = ''.join(path_d(f['geometry'], v) for f in ctx)
    lk = ''.join(path_d(f['geometry'], v, 2.5) for f in lakes)
    borders = land
    rl, rb_, rr, rt = RB
    (ix0, iy0), (ix1, iy1) = v.p(rl, rt), v.p(rr, rb_)
    rimg = relief_png(theme)
    wd = wire(v, wire_step, wire_amp, vertical=theme.get('mesh', False))
    lx, ly, lr = lens
    focus = (f'<g opacity=".5">' + columns(v, theme, k_col, only=[focus_g]) + '</g>' + columns(v, dict(theme, wire=theme['lens_ring'], wire_w=theme['wire_w']*2.4), k_col, then=True, only=[focus_g])) if focus_g else ''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{v.W}" height="{v.H}" viewBox="0 0 {v.W} {v.H}" style="position:absolute;inset:0">
<defs>
 <clipPath id="land"><path d="{land}"/></clipPath>
 <clipPath id="lens"><circle cx="{lx}" cy="{ly}" r="{lr}"/></clipPath>
 <linearGradient id="colg" x1="0" x2="1"><stop offset="0" stop-color="{theme['col_a']}"/><stop offset=".55" stop-color="{theme['col_b']}"/><stop offset="1" stop-color="{theme['col_c']}"/></linearGradient>
 <radialGradient id="fog" cx="50%" cy="46%" r="70%"><stop offset=".55" stop-color="{theme['fog']}" stop-opacity="0"/><stop offset="1" stop-color="{theme['fog']}" stop-opacity="{theme['fog_o']}"/></radialGradient>
 <filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="{theme.get('land_shadow_blur', 14)}"/></filter>
</defs>
{voxel_ocean(v, theme, vox) if vox else ''}
<path d="{nbr}" fill="{theme['nbr']}" stroke="{theme['nbr_line']}" stroke-width=".8"/>
{nbr_relief_svg(v, theme, nbr) if theme.get('nrelief_hi') else ''}
<path d="{land}" fill="{theme['land_shadow']}" transform="translate(0,{theme.get('slab', 10)})" filter="url(#soft)" opacity=".55"/>
<path d="{land}" fill="{theme['land']}"/>
<g clip-path="url(#land)"><image href="data:image/png;base64,{rimg}" x="{ix0:.1f}" y="{iy0:.1f}" width="{ix1-ix0:.1f}" height="{iy1-iy0:.1f}" preserveAspectRatio="none" opacity="{theme['relief_o']}"/></g>
<path d="{lk}" fill="{theme['water']}"/>
<path d="{borders}" fill="none" stroke="{theme['border']}" stroke-width="{theme['border_w']}" stroke-linejoin="round"/>
{columns(v, theme, k_col)}
{eggs(v, theme, max(1.6, vox*0.3)) if vox and theme.get('egg') else ''}
<rect width="{v.W}" height="{v.H}" fill="url(#fog)" pointer-events="none"/>
<!-- lens: inside, the past as wireframe -->
<g clip-path="url(#lens)">
 <rect width="{v.W}" height="{v.H}" fill="{theme['lens_bg']}"/>
 <path d="{nbr}" fill="none" stroke="{theme['wire']}" stroke-opacity=".18" stroke-width=".7"/>
 <g clip-path="url(#land)"><path d="{wd}" fill="none" stroke="{theme['wire']}" stroke-width="{theme['wire_w']}" stroke-opacity="{theme['wire_o']}"/></g>
 <path d="{borders}" fill="none" stroke="{theme['wire']}" stroke-width="{theme['wire_w']*1.4}" stroke-opacity=".9"/>
 {columns(v, theme, k_col, then=True)}
</g>
<circle cx="{lx}" cy="{ly}" r="{lr}" fill="none" stroke="{theme['lens_ring_shadow']}" stroke-width="10"/>
<circle cx="{lx}" cy="{ly}" r="{lr}" fill="none" stroke="{theme['lens_ring']}" stroke-width="{theme['lens_ring_w']}"/>
{focus}
{extra}
</svg>'''

# ---- easter eggs: pixel sprites that live in the 8-bit ocean (static here; animated in the app) ----
EGGS = {
 # name: (lon, lat, sprite rows, what it does in the app).  ' ' empty, ~ wake, b beam; the rest are palette keys.
 'bear': (-80.6, 61.2, [
  "                     WW  WW     ",
  "                    WWWWWWWW    ",
  "         WWWWWW     WWWWWWWWW   ",
  "      WWWWWWWWWWW  WWWWWWKWWWW  ",
  "     WWWWWWWWWWWWWWWWWWWWWWWWWW ",
  "    sWWWWWWWWWWWWWWWWWWWWWWWWWWK",
  "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
  " ~  ~    ~   ~    ~   ~    ~  ~ "], 'paddles a slow lap of Hudson Bay'),
 'sub': (-148.0, 71.5, [
  "             KK                    ",
  "             K                     ",
  "           hhhhhh                  ",
  "          SSSSSSSS                 ",
  "          SSRSSSSS                 ",
  "    hhhhhhhhhhhhhhhhhhhhhhhhhh     ",
  "  SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS  ",
  "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
  " ~  ~   ~    ~    ~   ~  ~   ~  ~  "], 'creeps along the Beaufort shelf, dives, resurfaces'),
 'ufo': (-94.0, 46.5, [
  "          CCCC          ",
  "        CCCCCCCC        ",
  "       CCCCCCCCCC       ",
  "   hhhhhhhhhhhhhhhhhh   ",
  " MMMMMMMMMMMMMMMMMMMMMM ",
  "MMYMMMMYMMMMYMMMMYMMMMYM",
  " MMMMMMMMMMMMMMMMMMMMMM ",
  "      KKKKKKKKKKKK      ",
  "       bbbbbbbbbb       ",
  "      bbbbbbbbbbbb      ",
  "      bbbbbbbbbbbb      ",
  "     bbbbbbbbbbbbbb     ",
  "     bbbbbbbbbbbbbb     ",
  "    bbbbbbbbbbbbbbbb    ",
  "    bbbbbbbbbbbbbbbb    ",
  "   bbbWWKKWWWWWWbbbbb   ",
  "   bbbWWKKWWWWKKWWWWbb  ",
  "   bbbWWWWWWWKKWWWWPbb  ",
  "   bbbWWWWWWWWWWWbbbbb  ",
  "   bbbbKbbKbbKbbKbbbbb  "], 'hovers over Minnesota, beams up a cow, leaves'),
 'narwhal': (-66.0, 73.5, [
  "TTTTTTT                        ",
  "       TTT   NNNNNNNN      NN  ",
  "          NNNNNNNNNNNNN   NNN  ",
  "         NNKNNNNdNNNdNNNNNNN   ",
  "         NNNNNNNNNNNNNNNNNN    ",
  "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
  "  ~   ~    ~   ~    ~    ~   ~ "], 'surfaces in Baffin Bay every so often'),
 'orca': (-128.5, 49.6, [
  "     K                     K    ",
  "     KK                    KK   ",
  "    KKK                   KKK   ",
  "    KKKK                  KKKK  ",
  "   KKKKKK                KKKKK  ",
  "  KKKKKKKWW             KKKKKKWW",
  "~~~~~~~~~~~~~~       ~~~~~~~~~~~~",
  " ~   ~    ~  ~        ~   ~   ~ "], 'two fins cruising off Vancouver Island'),
}

def _mix(h, k=.32, to='#000000'):
    a = [int(h[i:i+2], 16) for i in (1, 3, 5)]; b = [int(to[i:i+2], 16) for i in (1, 3, 5)]
    return '#' + ''.join(f'{round(x*(1-k)+y*k):02x}' for x, y in zip(a, b))

def eggs(v, theme, p, which=None):
    """Fine pixel sprites: flat pixels, a 1-px ink outline so they read at small sizes, a soft drop shadow."""
    from pyproj import Transformer
    tr = Transformer.from_crs(4326, 3347, always_xy=True)
    pal = theme['egg']; out = []
    for name, (lo, la, rows, _) in EGGS.items():
        if which and name not in which: continue
        sx, sy = v.p(*tr.transform(lo, la))
        n = max(len(r) for r in rows); rows = [r.ljust(n) for r in rows]
        w, h = n * p, len(rows) * p
        if sx < -w or sx > v.W + w or sy < -h or sy > v.H + h: continue
        x0, y0 = sx - w / 2, sy - h * .75
        solid = {(i, j) for j, r in enumerate(rows) for i, ch in enumerate(r) if ch not in ' ~b'}
        rect = lambda i, j, c, o=1: f'<rect x="{x0 + i*p:.2f}" y="{y0 + j*p:.2f}" width="{p+.05:.2f}" height="{p+.05:.2f}" fill="{c}"' + (f' opacity="{o}"' if o != 1 else '') + '/>'
        g = []
        if name == 'ufo':
            g.append(f'<ellipse cx="{sx:.1f}" cy="{y0 + h + p:.1f}" rx="{w*.38:.1f}" ry="{p*1.4:.1f}" fill="{pal["K"]}" opacity=".2"/>')
        # drop shadow + outline ring
        ring = {(i + di, j + dj) for i, j in solid for di in (-1, 0, 1) for dj in (-1, 0, 1)} - solid
        g += [rect(i + .6, j + .8, pal['K'], .22) for i, j in solid]
        for j, r in enumerate(rows):
            for i, ch in enumerate(r):
                if ch == '~': g.append(rect(i, j, pal['w'], .9))
                elif ch == 'b': g.append(rect(i, j, pal['b'], pal['b_o']))
        g += [rect(i, j, pal['O']) for i, j in ring if not (0 <= j < len(rows) and 0 <= i < n and rows[j][i] == 'b') or True]
        g += [rect(i, j, pal[rows[j][i]]) for i, j in solid]
        out.append(f'<g data-egg="{name}" shape-rendering="crispEdges">{"".join(g)}</g>')
    return ''.join(out)
