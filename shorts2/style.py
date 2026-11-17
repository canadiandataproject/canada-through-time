"""Route identity for Shorts (from 2026-11-17): Whiteout (light) and Blue hour (dark), the same look as the explorer.

Every new Short after the current Buffer queue uses this module for colour and type. Rules (Tyson, standing):
no default sans, no off-white paper, no orange; no serif headlines, tiny letter-spaced capitals, hairline dividers or
chart cards. Display: Bricolage Grotesque at width 80, weight 760. Interface text: Familjen Grotesk. Figures: IBM Plex Mono.
Then = wireframe, now = lit solid; numbers are tied to places with leader lines; the sea is small stepped cubes.

    from style import MODE, font
    M = MODE['dark']; f = font('display', 120)
"""
from pathlib import Path
from PIL import ImageFont

FONTS = Path(__file__).resolve().parent / "fonts"

MODE = {
    "light": dict(name="Whiteout", bg="#E3E9F0", bg_top="#D3DCE6", bg_bottom="#DCE3EA", land="#F4F7FB", neighbour="#D9DBE0", border="#7E92AE",
                  ink="#0A1322", ink2="#3D4B60", ink3="#55647B", accent="#1E3CFF", on_accent="#FFFFFF", spike="#22325C", wire="#1E3CFF",
                  glass=(255, 255, 255, 188), glass_line=(10, 19, 34, 23), less="#D9799F", more="#2D50D9",
                  vox=["#CFDAE6", "#D7E1EB", "#E0E8F0", "#EAF0F6"], vox_side="#B9C8D9"),
    "dark": dict(name="Blue hour", bg="#0B1A3D", bg_top="#071330", bg_bottom="#3E63A0", land="#2B4776", neighbour="#1C2638", border="#A9C3EA",
                 ink="#F2F7FF", ink2="#BFD0EA", ink3="#8EA6CC", accent="#BDEBFF", on_accent="#071330", spike="#F2F8FF", wire="#D7F1FF",
                 glass=(8, 19, 48, 158), glass_line=(234, 247, 255, 36), less="#F09AC4", more="#8FBDF2",
                 vox=["#11264F", "#162E5C", "#1D3A6E", "#2C5190"], vox_side="#08163A"),
}


def font(kind: str, size: int, weight: int | None = None) -> ImageFont.FreeTypeFont:
    """kind: 'display' (Bricolage, condensed), 'ui' (Familjen Grotesk), 'mono' (IBM Plex Mono, figures)."""
    if kind == "display":
        f = ImageFont.truetype(str(FONTS / "BricolageGrotesque-Variable.ttf"), size)
        f.set_variation_by_axes([96, weight or 760, 80])          # opsz, wght, wdth
        return f
    if kind == "ui":
        f = ImageFont.truetype(str(FONTS / "FamiljenGrotesk-Variable.ttf"), size)
        f.set_variation_by_axes([weight or 500])
        return f
    return ImageFont.truetype(str(FONTS / ("IBMPlexMono-Medium.ttf" if (weight or 500) >= 500 else "IBMPlexMono-Regular.ttf")), size)
