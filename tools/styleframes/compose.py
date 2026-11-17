import sys; sys.path.insert(0, '/tmp/sf')
from build import *

T = {
 'A': dict(name='A · Whiteout', bg='linear-gradient(180deg,#D3DCE6 0%,#E6ECF2 55%,#DCE3EA 100%)',
   nbr='#E1E7EE', nbr_line='#CBD4DF', land='#EEF2F7', land_shadow='#7C8DA6', relief_hi=(255, 255, 255), relief_lo=(84, 101, 128), relief_k=1.5, relief_o=.95,
   water='#C6D3E2', border='#9DAEC3', border_w=.7, col_a='#FFFFFF', col_b='#E2EAF5', col_c='#A8B9D2', col_top='#FFFFFF', col_shadow='rgba(40,60,100,.20)',
   fog='#E3E9F0', fog_o=.92, lens_bg='#F7F9FC', wire='#1E3CFF', wire_o=.55, wire_w=.8, lens_ring='#1E3CFF', lens_ring_w=3, lens_ring_shadow='rgba(20,40,140,.12)',
   ink='#0A1322', ink2='#3D4B60', ink3='#6A7890', accent='#1E3CFF', on_accent='#FFFFFF', glass='rgba(255,255,255,.72)', glass_line='rgba(10,19,34,.08)',
   display="'Funnel Display'", ui="'Funnel Sans'", mono="'Fragment Mono'", disp_w=600, disp_stretch='100%', disp_track='-.035em',
   fonts=[('Funnel Display', 'funnel-display-latin-wght-normal.woff2'), ('Funnel Sans', 'funnel-sans-latin-wght-normal.woff2'), ('Fragment Mono', 'fragment-mono-latin-400-normal.woff2')]),
 'B': dict(name='B · Survey night', bg='radial-gradient(90% 70% at 50% 42%,#0F1D35 0%,#070B13 60%,#04060A 100%)', mesh=True,
   nbr='#090D14', nbr_line='#1B2535', land='#151C27', land_shadow='#000000', relief_hi=(170, 190, 215), relief_lo=(0, 0, 0), relief_k=1.3, relief_o=.8,
   water='#06090F', border='#3C4C63', border_w=.7, col_a='#3A4659', col_b='#E4ECF6', col_c='#64748C', col_top='#FFFFFF', col_shadow='rgba(0,0,0,.55)',
   fog='#04060A', fog_o=.96, lens_bg='#03050A', wire='#E9F1FF', wire_o=.5, wire_w=.6, lens_ring='#F2EA4A', lens_ring_w=2.5, lens_ring_shadow='rgba(242,234,74,.10)',
   ink='#EEF3FA', ink2='#AEB9C9', ink3='#76839A', accent='#F2EA4A', on_accent='#05070B', glass='rgba(10,15,24,.62)', glass_line='rgba(233,241,255,.12)',
   display="'Host Grotesk'", ui="'Host Grotesk'", mono="'Martian Mono'", disp_w=300, disp_stretch='100%', disp_track='-.04em',
   fonts=[('Host Grotesk', 'host-grotesk-latin-wght-normal.woff2'), ('Martian Mono', 'martian-mono-latin-wght-normal.woff2')]),
 'C': dict(name='C · Blue hour', bg='linear-gradient(180deg,#071330 0%,#132C5C 46%,#3E63A0 78%,#7395C8 100%)',
   nbr='#16305C', nbr_line='#284777', land='#2B4776', land_shadow='#020818', relief_hi=(214, 232, 255), relief_lo=(4, 10, 30), relief_k=1.55, relief_o=.9,
   water='#10234A', border='#86A3D1', border_w=.7, col_a='#A9CBFF', col_b='#F2F8FF', col_c='#7092CF', col_top='#FFFFFF', col_shadow='rgba(0,5,25,.4)',
   fog='#0D2048', fog_o=.9, lens_bg='#081633', wire='#D7F1FF', wire_o=.6, wire_w=.7, lens_ring='#EAF7FF', lens_ring_w=3, lens_ring_shadow='rgba(0,8,30,.35)',
   ink='#F2F7FF', ink2='#BFD0EA', ink3='#8EA6CC', accent='#BDEBFF', on_accent='#071330', glass='rgba(8,19,48,.55)', glass_line='rgba(234,247,255,.14)',
   display="'Bricolage Grotesque'", ui="'Familjen Grotesk'", mono="'IBM Plex Mono'", disp_w=800, disp_stretch='75%', disp_track='-.03em',
   fonts=[('Bricolage Grotesque', 'bricolage-grotesque-latin-standard-normal.woff2'), ('Familjen Grotesk', 'familjen-grotesk-latin-wght-normal.woff2'), ('IBM Plex Mono', 'ibm-plex-mono-latin-500-normal.woff2')]),
}

AB = ANCH['AB']
def place(v, tx, ty):
    ax, ay = v.p(*AB); v.cx += (ax - tx) * v.mpp; v.cy -= (ay - ty) * v.mpp / v.t; return v
def css(t):
    ff = ''.join(font_face(n, f) for n, f in t['fonts'])
    return f'''<style>{ff}
*{{box-sizing:border-box;margin:0;padding:0}} body{{width:var(--W);height:var(--H);overflow:hidden;background:{t['bg']};color:{t['ink']};font-family:{t['ui']},sans-serif;-webkit-font-smoothing:antialiased}}
.stage{{position:relative;width:100%;height:100%;overflow:hidden}}
.disp{{font-family:{t['display']};font-weight:{t['disp_w']};font-stretch:{t['disp_stretch']};letter-spacing:{t['disp_track']};line-height:.9}}
.mono{{font-family:{t['mono']};font-variant-numeric:tabular-nums}}
.glass{{background:{t['glass']};backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);box-shadow:0 0 0 1px {t['glass_line']}}}
.k3{{color:{t['ink3']}}} .k2{{color:{t['ink2']}}} .acc{{color:{t['accent']}}}
</style>'''

def callout(v, t, lab_xy, fs, big, k_col, side='left'):
    """Leader line from the top of Alberta's 2026 column to a place-linked number."""
    x, y = v.p(*AB); h = col_h(P26['AB'], v, k_col)
    tx, ty = lab_xy
    knee = (tx + (60 if side == 'left' else -60) * fs / 14, ty)
    d = (f'M{x:.1f},{y-h:.1f}L{tx:.1f},{ty:.1f}L{tx + 120 * fs / 14:.1f},{ty:.1f}' if side == 'right' else f'M{x:.1f},{y-h:.1f}L{knee[0]:.1f},{knee[1]:.1f}L{tx:.1f},{ty:.1f}')
    return (f'<g><path d="{d}" fill="none" stroke="{t["ink"]}" stroke-width="{1.2*fs/14:.2f}"/>'
            f'<circle cx="{x:.1f}" cy="{y-h:.1f}" r="{3.2*fs/14:.1f}" fill="{t["accent"]}" stroke="{t["ink"]}" stroke-width="{1*fs/14:.1f}"/></g>')

def lens_plate(cx, top, t, s=1.0, year='1971'):
    return f'''<div class="glass" style="position:absolute;left:{cx}px;top:{top}px;transform:translateX(-50%);display:flex;align-items:center;gap:{8*s}px;padding:{6*s}px {8*s}px;border-radius:{999}px;font-size:{13*s}px;white-space:nowrap">
<span style="width:{26*s}px;height:{26*s}px;border-radius:50%;display:grid;place-items:center;color:{t['ink2']}">‹</span>
<span class="mono" style="font-size:{15*s}px;color:{t['ink']}">{year}</span><span class="k2">inside · drag the lens</span>
<span style="width:{26*s}px;height:{26*s}px;border-radius:50%;display:grid;place-items:center;color:{t['ink2']}">›</span></div>'''

def key_then_now(t, s=1.0):
    return f'''<div style="display:flex;gap:{14*s}px;align-items:center;font-size:{12.5*s}px" class="k2">
<span style="display:flex;align-items:center;gap:{6*s}px;white-space:nowrap"><svg width="{22*s}" height="{12*s}"><path d="M1,9 Q6,2 11,7 T21,4" fill="none" stroke="{t['wire']}" stroke-width="1.2"/><path d="M1,11 Q6,5 11,9 T21,7" fill="none" stroke="{t['wire']}" stroke-width="1.2" opacity=".5"/></svg>1971 · wireframe</span>
<span style="display:flex;align-items:center;gap:{6*s}px;white-space:nowrap"><span style="width:{18*s}px;height:{10*s}px;border-radius:2px;background:linear-gradient(90deg,{t['col_c']},{t['col_b']})"></span>2026 · solid</span></div>'''

def where(t, s=1.0, w=330):
    return f'''<div class="glass" style="display:flex;align-items:center;gap:{10*s}px;width:{w}px;padding:{7*s}px {7*s}px {7*s}px {16*s}px;border-radius:999px">
<span style="font-weight:600;font-size:{14.5*s}px">Where do you live?</span><span class="k3" style="flex:1;font-size:{13.5*s}px">City or postal code</span>
<span style="width:{32*s}px;height:{32*s}px;border-radius:50%;background:{t['accent']};color:{t['on_accent']};display:grid;place-items:center;font-size:{15*s}px">→</span></div>'''

def topbar(t):
    nav = ['Over time', 'Neighbourhoods', 'Climate', 'Report card', 'Money']
    return f'''<div style="position:absolute;left:24px;right:24px;top:18px;display:flex;align-items:center;gap:22px;font-size:14px">
<div style="display:flex;align-items:baseline;gap:8px"><span class="disp" style="font-size:22px;line-height:1">Canada</span><span class="k2" style="font-size:14px">through time</span></div>
<div class="glass" style="margin-left:18px;display:flex;gap:2px;padding:4px;border-radius:999px">{''.join(f'<span style="padding:6px 13px;border-radius:999px;{"background:"+t["ink"]+";color:"+t["on_ink"]+";" if i==0 else "color:"+t["ink2"]+";"}">{n}</span>' for i,n in enumerate(nav))}</div>
<div style="margin-left:auto;display:flex;gap:10px;align-items:center" class="k2"><span class="glass" style="padding:7px 14px;border-radius:999px">Search ⌕</span><span class="glass" style="padding:7px 11px;border-radius:999px">FR</span>
<span style="padding:7px 16px;border-radius:999px;background:{t['accent']};color:{t['on_accent']};font-weight:600">Share</span></div></div>'''

def timeline(t, left, right, bottom, s=1.0, pos=1.0):
    return f'''<div style="position:absolute;left:{left}px;right:{right}px;bottom:{bottom}px;display:flex;align-items:center;gap:{14*s}px">
<span style="width:{40*s}px;height:{40*s}px;border-radius:50%;background:{t['ink']};color:{t['on_ink']};display:grid;place-items:center;font-size:{14*s}px">▶</span>
<span class="mono k2" style="font-size:{12*s}px">1971</span>
<div style="flex:1;height:{2*s}px;background:{t['ink3']};opacity:.5;position:relative;border-radius:2px"></div>
<span class="mono" style="font-size:{12*s}px">2026</span>
<div style="position:absolute;left:{(54+40)*s}px;right:{46*s}px;top:50%;height:0">
 <div style="position:absolute;left:{pos*100}%;top:0;width:{16*s}px;height:{16*s}px;margin:-{8*s}px 0 0 -{8*s}px;border-radius:50%;background:{t['accent']};box-shadow:0 0 0 {4*s}px {t['glass']}"></div></div></div>'''

def mapctl(t, right, bottom, s=1.0):
    b = lambda c, on=False: f'<span style="width:{36*s}px;height:{36*s}px;border-radius:50%;display:grid;place-items:center;{"background:"+t["accent"]+";color:"+t["on_accent"] if on else ""}">{c}</span>'
    return f'<div class="glass k2" style="position:absolute;right:{right}px;bottom:{bottom}px;display:flex;flex-direction:column;gap:2px;padding:4px;border-radius:999px;font-size:{15*s}px">{b("+")}{b("−")}{b("3D")}{b("◎", True)}</div>'

def page(W, H, t, body, scale=1):
    return f'<!doctype html><html><head><meta charset="utf-8">{css(t)}<style>:root{{--W:{W}px;--H:{H}px}}</style></head><body><div class="stage">{body}</div></body></html>'

def hud(t, v):
    if t is not T['B']: return ''
    return f'''<div class="mono k3" style="position:absolute;left:24px;bottom:96px;font-size:10.5px;line-height:1.7">53.5461° N<br>113.4938° W<br><span class="acc">EDMONTON · AB</span></div>'''

def desktop(key):
    t = T[key]; W, H = 1440, 900
    v = place(View(W, H, 6.05e6, 2.72e6, 4200, .72), 560, 560)
    ax, ay = v.p(*AB)
    lens = (ax, ay - 40, 158)
    k_col = 62
    lab = (ax + 230, ay - 250)
    svg = map_svg(v, t, lens, k_col, 40, 9, callout(v, t, lab, 14, True, k_col, 'right'))
    big = f'''<div style="position:absolute;left:{lab[0]+8}px;top:{lab[1]-58}px;width:260px;text-align:left">
<div style="font-size:14px;font-weight:600">Alberta</div>
<div class="mono" style="font-size:24px;margin-top:4px;white-space:nowrap"><span class="k3">1.67M</span> → <span>5.10M</span></div>
<div class="k2" style="font-size:12.5px;margin-top:4px">3.1× the people since 1971</div></div>'''
    body = f'''{svg}{topbar(t)}
<div style="position:absolute;left:28px;top:96px;width:400px">
 <div style="display:flex;align-items:flex-end;gap:14px"><div class="disp" style="font-size:72px">People</div><div class="mono acc" style="font-size:30px;margin-bottom:6px">2026</div></div>
 <div class="k2" style="font-size:15px;line-height:1.45;margin-top:10px;width:330px">41,798,407 people lived in Canada on July 1, 2026 <span class="k3">(preliminary)</span>.</div>
 <div style="margin-top:16px">{where(t)}</div></div>
{big}
<div style="position:absolute;left:{lens[0]}px;top:{lens[1]+lens[2]+12}px">{lens_plate(0, 0, t)}</div>
<div style="position:absolute;right:28px;top:96px;text-align:right"><div style="padding:6px 0">
 <div class="k3" style="font-size:12px">Canada · July 1, 2026</div><div class="disp" style="font-size:44px;margin-top:4px">41.8M</div>
 <div class="mono k3" style="font-size:11px;margin-top:6px">22.0M in 1971 · StatCan 17-10-0009</div></div></div>
<div style="position:absolute;right:28px;top:250px">{key_then_now(t)}</div>
{mapctl(t, 28, 104)}{hud(t, v)}
{timeline(t, 28, 96, 30)}'''
    return page(W, H, t, body)

def phone(key):
    t = T[key]; W, H = 390, 844
    v = View(W, H, 5.0e6, 2.55e6, 6200, .74)
    ax, ay = v.p(*AB)
    lens = (ax + 6, ay - 34, 92)
    k_col = 70
    v.H = H;
    lab = (150, 236)
    svg = map_svg(v, t, lens, k_col, 30, 7, callout(v, t, lab, 11, True, k_col))
    sheet_bg = t['glass']
    body = f'''{svg}
<div style="position:absolute;left:16px;right:16px;top:14px;display:flex;align-items:center;justify-content:space-between;font-size:13px">
 <span class="disp" style="font-size:19px">Canada</span>
 <span class="glass k2" style="display:flex;gap:2px;padding:3px;border-radius:999px;font-size:12.5px"><span style="padding:5px 10px;border-radius:999px;background:{t['ink']};color:{t['on_ink']}">Over time</span><span style="padding:5px 9px">Cities</span><span style="padding:5px 9px">Climate</span><span style="padding:5px 6px">⋯</span></span></div>
<div style="position:absolute;left:16px;top:60px"><div style="display:flex;align-items:flex-end;gap:8px"><span class="disp" style="font-size:44px">People</span><span class="mono acc" style="font-size:19px;margin-bottom:3px">2026</span></div></div>
<div style="position:absolute;left:16px;top:118px">{where(t, .86, 300)}</div>
<div style="position:absolute;left:{lab[0]+6}px;top:{lab[1]-60}px;width:130px;text-align:left">
 <div style="font-size:12.5px;font-weight:600">Alberta</div><div class="mono" style="font-size:15px;white-space:nowrap"><span class="k3">1.67M</span> → 5.10M</div><div class="k2" style="font-size:11px">3.1× since 1971</div></div>
<div style="position:absolute;left:{lens[0]}px;top:{lens[1]+lens[2]+8}px">{lens_plate(0, 0, t, .78)}</div>
<div class="glass" style="position:absolute;left:10px;right:10px;bottom:10px;border-radius:24px;padding:14px 16px 16px">
 <div style="width:36px;height:4px;border-radius:2px;background:{t['ink3']};opacity:.5;margin:0 auto 10px"></div>
 <div style="display:flex;align-items:flex-end;justify-content:space-between"><div><div class="k3" style="font-size:11.5px">Canada · July 1, 2026</div><div class="disp" style="font-size:38px;margin-top:2px">41.8M</div></div>
 <div style="text-align:right">{key_then_now(t, .82)}</div></div>
 <div style="position:relative;height:44px;margin-top:10px">{timeline(t, 0, 0, 0, .86)}</div></div>'''
    return page(W, H, t, body)

def short(key):
    t = T[key]; W, H = 1080, 1920
    v = place(View(W, H, 5.15e6, 2.38e6, 2300, .74), 400, 1250)
    ax, ay = v.p(*AB)
    lens = (ax, ay - 70, 300)
    k_col = 62
    lab = (ax + 330, ay - 390)
    svg = map_svg(v, t, lens, k_col, 26, 15, callout(v, t, lab, 28, True, k_col, 'right'))
    head = {'A': 'Alberta<br>tripled.', 'B': 'Alberta<br>tripled.', 'C': 'Alberta<br>tripled.'}[key]
    body = f'''{svg}
<div style="position:absolute;left:72px;top:150px;right:72px">
 <div class="mono acc" style="font-size:30px">1971 → 2026</div>
 <div class="disp" style="font-size:{230 if key!='C' else 290}px;margin-top:22px">{head}</div></div>
<div style="position:absolute;left:{lab[0]+14}px;top:{lab[1]-180}px;width:380px;text-align:left">
 <div style="font-size:34px;font-weight:600">Alberta</div>
 <div class="mono" style="font-size:58px;white-space:nowrap;line-height:1.05;margin-top:6px"><span class="k3">1.67M</span></div>
 <div class="mono" style="font-size:58px;white-space:nowrap;line-height:1.05">→ 5.10M</div></div>
<div style="position:absolute;left:{lens[0]}px;top:{lens[1]+lens[2]+22}px">{lens_plate(0, 0, t, 2.1)}</div>
<div style="position:absolute;left:72px;right:72px;bottom:120px;display:flex;justify-content:space-between;align-items:flex-end">
 <div><div style="font-size:30px;font-weight:600">The Canadian Data Project</div><div class="mono k3" style="font-size:22px;margin-top:8px">Statistics Canada 17-10-0009 · 2026 preliminary</div></div>
 <div>{key_then_now(t, 2)}</div></div>'''
    return page(W, H, t, body)

if __name__ == '__main__':
  for k in 'ABC':
    (OUT / f'{k}_desktop.html').write_text(desktop(k))
    (OUT / f'{k}_phone.html').write_text(phone(k))
    (OUT / f'{k}_short.html').write_text(short(k))
  print('ok')
