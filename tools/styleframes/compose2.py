"""Paired frames: one interface, Whiteout = light mode, Blue hour = dark mode.
Same layout, same real numbers, same controls and lens in both; the mode changes atmosphere and map treatment only.
Type: Bricolage Grotesque condensed (display), Familjen Grotesk (interface), IBM Plex Mono (figures)."""
import sys; sys.path.insert(0, '/tmp/sf')
from compose import *

TYPE = dict(display="'Bricolage Grotesque'", ui="'Familjen Grotesk'", mono="'IBM Plex Mono'", disp_w=760, disp_stretch='80%', disp_track='-.018em',
            fonts=[('Bricolage Grotesque', 'bricolage-grotesque-latin-standard-normal.woff2'), ('Familjen Grotesk', 'familjen-grotesk-latin-wght-normal.woff2'),
                   ('IBM Plex Mono', 'ibm-plex-mono-latin-500-normal.woff2')])
L = dict(T['A'], **TYPE, vox_tops=['#D2DDE8','#DAE3EC','#E3EAF1','#EDF2F7'], vox_side='#C1CFDD', nbr='#D9DBE0', nbr_line='#C2C6CE', nrelief_hi=(255,255,255), nrelief_lo=(96,100,110), nrelief_k=1.2, nrelief_o=.6, egg=dict(W='#FFFFFF',s='#DCE4EE',O='#22314F',h='#5A6B88',P='#F2A7B8',d='#5E6E86',K='#0B1A3D',S='#3B4A63',R='#E0283A',N='#A8B6C8',T='#F1E7C8',w='#A9BCD3',C='#BFD3FF',M='#55647B',Y='#1E3CFF',b='#1E3CFF',b_o=.13), name='Light · Whiteout', mode='light', mesh=True, on_ink='#FFFFFF', ink3='#55647B',
         lens_bg='#F2F5FB', wire='#1E3CFF', wire_o=.42, wire_w=.7)
D = dict(T['C'], **TYPE, vox_tops=['#11264F','#162E5C','#1D3A6E','#2C5190'], vox_side='#0A1A3C', nbr='#1C2638', nbr_line='#2E3A50', nrelief_hi=(150,162,182), nrelief_lo=(2,6,14), nrelief_k=1.3, nrelief_o=.75, egg=dict(W='#F2F8FF',s='#C9D9EC',O='#030A1A',h='#8A9CBB',P='#F2A7B8',d='#5E7090',K='#020814',S='#5D6F8E',R='#FF4A5C',N='#A9BAD4',T='#F1E7C8',w='#4E78B8',C='#BDEBFF',M='#C9D6EA',Y='#BDEBFF',b='#BDEBFF',b_o=.16), name='Dark · Blue hour', mode='dark', mesh=True, on_ink='#071330',
         lens_bg='#0B1A3D', wire='#D7F1FF', wire_o=.5, wire_w=.65)
M = {'L': L, 'D': D}

def mode_toggle(t, s=1.0):
    sun = f'<svg width="{15*s}" height="{15*s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M5.3 18.7l1.6-1.6M17.1 6.9l1.6-1.6"/></svg>'
    moon = f'<svg width="{15*s}" height="{15*s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg>'
    on = lambda a: f'background:{t["ink"]};color:{t["on_ink"]};' if a else f'color:{t["ink2"]};'
    return (f'<span class="glass" style="display:flex;gap:2px;padding:{3*s}px;border-radius:999px">'
            f'<span style="width:{30*s}px;height:{30*s}px;border-radius:50%;display:grid;place-items:center;{on(t["mode"]=="light")}">{sun}</span>'
            f'<span style="width:{30*s}px;height:{30*s}px;border-radius:50%;display:grid;place-items:center;{on(t["mode"]=="dark")}">{moon}</span></span>')

def topbar2(t):
    nav = ['Over time', 'Neighbourhoods', 'Climate', 'Report card', 'Money']
    pills = ''.join(f'<span style="padding:7px 14px;border-radius:999px;{"background:"+t["ink"]+";color:"+t["on_ink"]+";" if i==0 else "color:"+t["ink2"]+";"}">{n}</span>' for i, n in enumerate(nav))
    return f'''<div style="position:absolute;left:24px;right:24px;top:18px;display:flex;align-items:center;gap:22px;font-size:14.5px">
<div style="display:flex;align-items:baseline;gap:8px"><span class="disp" style="font-size:27px;line-height:1">Canada</span><span class="k2" style="font-size:14.5px">through time</span></div>
<div class="glass" style="margin-left:14px;display:flex;gap:2px;padding:4px;border-radius:999px">{pills}</div>
<div style="margin-left:auto;display:flex;gap:10px;align-items:center" class="k2"><span class="glass" style="padding:8px 15px;border-radius:999px">Search ⌕</span>{mode_toggle(t)}
<span class="glass" style="padding:8px 12px;border-radius:999px">FR</span><span style="padding:8px 17px;border-radius:999px;background:{t['accent']};color:{t['on_accent']};font-weight:600">Share</span></div></div>'''

def desktop2(m, vox=0):
    t = M[m]; W, H = 1440, 900
    v = place(View(W, H, 6.05e6, 2.72e6, 4200, .72), 560, 560)
    ax, ay = v.p(*AB); lens = (ax, ay - 40, 158); k_col = 62; lab = (ax + 230, ay - 250)
    svg = map_svg(v, t, lens, k_col, 40, 9, callout(v, t, lab, 14, True, k_col, 'right'), vox=vox)
    body = f'''{svg}{topbar2(t)}
<div style="position:absolute;left:28px;top:100px;width:420px">
 <div style="display:flex;align-items:flex-end;gap:14px"><div class="disp" style="font-size:84px">People</div><div class="mono acc" style="font-size:28px;margin-bottom:8px">2026</div></div>
 <div class="k2" style="font-size:16px;line-height:1.45;margin-top:12px;width:340px">41,798,407 people lived in Canada on July 1, 2026 <span class="k3">(preliminary)</span>.</div>
 <div style="margin-top:18px">{where(t, 1.0, 340)}</div></div>
<div style="position:absolute;left:{lab[0]+8}px;top:{lab[1]-64}px;width:280px">
 <div class="disp" style="font-size:26px;line-height:1">Alberta</div>
 <div class="mono" style="font-size:22px;margin-top:6px;white-space:nowrap"><span class="k3">1.67M</span> → <span>5.10M</span></div>
 <div class="k2" style="font-size:13px;margin-top:5px">3.1× the people since 1971</div></div>
<div style="position:absolute;left:{lens[0]}px;top:{lens[1]+lens[2]+12}px">{lens_plate(0, 0, t)}</div>
<div style="position:absolute;right:28px;top:100px;text-align:right">
 <div class="k3" style="font-size:13px">Canada · July 1, 2026</div><div class="disp" style="font-size:60px;margin-top:4px">41.8M</div>
 <div class="mono k3" style="font-size:12px;margin-top:6px">22.0M in 1971 · StatCan 17-10-0009</div></div>
<div style="position:absolute;right:28px;top:252px">{key_then_now(t)}</div>
{mapctl(t, 28, 104)}{timeline(t, 28, 96, 30)}'''
    return page(W, H, t, body)

def phone2(m, vox=0):
    t = M[m]; W, H = 390, 844
    v = place(View(W, H, 5.0e6, 2.55e6, 6400, .74), 150, 478)
    ax, ay = v.p(*AB); lens = (ax, ay - 26, 92); k_col = 62; lab = (ax + 96, ay - 172)
    svg = map_svg(v, t, lens, k_col, 30, 7, callout(v, t, lab, 11, True, k_col, 'right'), vox=vox)
    body = f'''{svg}
<div style="position:absolute;left:16px;right:16px;top:14px;display:flex;align-items:center;gap:8px;font-size:13px">
 <span class="disp" style="font-size:24px">Canada</span>
 <span class="glass k2" style="margin-left:auto;display:flex;gap:2px;padding:3px;border-radius:999px;font-size:13px"><span style="padding:6px 11px;border-radius:999px;background:{t['ink']};color:{t['on_ink']}">Over time</span><span style="padding:6px 9px">Cities</span><span style="padding:6px 8px">⋯</span></span>
 {mode_toggle(t, .9)}</div>
<div style="position:absolute;left:16px;top:62px"><div style="display:flex;align-items:flex-end;gap:8px"><span class="disp" style="font-size:54px">People</span><span class="mono acc" style="font-size:18px;margin-bottom:6px">2026</span></div></div>
<div style="position:absolute;left:16px;top:130px">{where(t, .88, 310)}</div>
<div style="position:absolute;left:{lab[0]+6}px;top:{lab[1]-62}px;width:140px">
 <div class="disp" style="font-size:20px;line-height:1">Alberta</div><div class="mono" style="font-size:14px;white-space:nowrap;margin-top:3px"><span class="k3">1.67M</span> → 5.10M</div><div class="k2" style="font-size:12px;margin-top:2px">3.1× since 1971</div></div>
<div style="position:absolute;left:{lens[0]}px;top:{lens[1]+lens[2]+8}px">{lens_plate(0, 0, t, .8)}</div>
<div class="glass" style="position:absolute;left:10px;right:10px;bottom:10px;border-radius:24px;padding:14px 16px 16px">
 <div style="width:36px;height:4px;border-radius:2px;background:{t['ink3']};opacity:.5;margin:0 auto 10px"></div>
 <div style="display:flex;align-items:flex-end;justify-content:space-between"><div><div class="k3" style="font-size:12px">Canada · July 1, 2026</div><div class="disp" style="font-size:46px;margin-top:2px">41.8M</div></div>
 <div style="text-align:right">{key_then_now(t, .84)}</div></div>
 <div style="position:relative;height:44px;margin-top:10px">{timeline(t, 0, 0, 0, .86)}</div></div>'''
    return page(W, H, t, body)

def short2(m):
    t = M[m]; W, H = 1080, 1920
    v = place(View(W, H, 5.15e6, 2.38e6, 2300, .74), 400, 1330)
    ax, ay = v.p(*AB); lens = (ax, ay - 70, 290); k_col = 62; lab = (ax + 330, ay - 390)
    svg = map_svg(v, t, lens, k_col, 26, 15, callout(v, t, lab, 28, True, k_col, 'right'))
    body = f'''{svg}
<div style="position:absolute;left:72px;top:140px;right:72px">
 <div class="mono acc" style="font-size:32px">1971 → 2026</div>
 <div class="disp" style="font-size:250px;margin-top:20px;line-height:.9">Alberta<br>tripled.</div></div>
<div style="position:absolute;left:{lab[0]+14}px;top:{lab[1]-188}px;width:380px">
 <div class="disp" style="font-size:52px;line-height:1">Alberta</div>
 <div class="mono" style="font-size:56px;white-space:nowrap;line-height:1.08;margin-top:10px"><span class="k3">1.67M</span></div>
 <div class="mono" style="font-size:56px;white-space:nowrap;line-height:1.08">→ 5.10M</div></div>
<div style="position:absolute;left:{lens[0]}px;top:{lens[1]+lens[2]+24}px">{lens_plate(0, 0, t, 2.1)}</div>
<div style="position:absolute;left:72px;right:72px;bottom:120px;display:flex;justify-content:space-between;align-items:flex-end">
 <div><div class="disp" style="font-size:44px">The Canadian Data Project</div><div class="mono k3" style="font-size:22px;margin-top:10px">Statistics Canada 17-10-0009 · 2026 preliminary</div></div>
 <div>{key_then_now(t, 1.9)}</div></div>'''
    return page(W, H, t, body)

if __name__ == '__main__':
    for m in 'LD':
        (OUT / f'{m}_desktop.html').write_text(desktop2(m))
        (OUT / f'{m}_phone.html').write_text(phone2(m))
        (OUT / f'{m}_short.html').write_text(short2(m))
        (OUT / f'{m}_desktopvox.html').write_text(desktop2(m, 8))
        (OUT / f'{m}_phonevox.html').write_text(phone2(m, 6))
    print('ok')
