"""Animated tech-stack grid (light/dark SVG), built from vendored Simple Icons paths.

Logos: Simple Icons (CC0), path data stored in assets/icons.json.
Concepts without a logo (RAG, OCR, RLS...) get a monogram tile in the profile's accent gradient.
"""

from __future__ import annotations

import json
from pathlib import Path

# (row label, [(icon slug or None, caption, monogram if no slug)])
ROWS = [
    ("AI / ML", [
        ("python", "Python", None), ("pytorch", "PyTorch", None), ("huggingface", "Hugging Face", None),
        (None, "Whisper", "~wave"), (None, "Diarization", "SPK"), (None, "Local LLMs", "LLM"),
        (None, "RAG", "RAG"), (None, "OCR", "OCR"),
    ]),
    ("Backend &amp; data", [
        ("fastapi", "FastAPI", None), ("postgresql", "PostgreSQL", None), ("sqlalchemy", "SQLAlchemy", None),
        ("qdrant", "Qdrant", None), (None, "Row-Level Sec.", "RLS"), (None, "pgTAP", "TAP"),
    ]),
    ("Frontend", [
        ("react", "React", None), ("typescript", "TypeScript", None), ("tailwindcss", "Tailwind", None),
        ("vite", "Vite", None),
    ]),
    ("Delivery", [
        ("docker", "Docker", None), (None, "Dokploy", "DPL"), ("githubactions", "GitHub Actions", None),
        ("linux", "Linux", None),
    ]),
    ("Earlier", [
        ("opencv", "OpenCV", None), (None, "YOLOv8", "YOLO"), ("nvidia", "Jetson Orin", None), ("ros", "ROS 2", None),
    ]),
]


def _lum(hex_color: str) -> float:
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def _contrast(a: str, b: str) -> float:
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def tech_svg(t: dict, icons_file: Path, font: str, mono: str) -> str:
    icons = json.loads(icons_file.read_text(encoding="utf-8"))
    w = 900
    label_w, x0, tile, gap, row_h, top = 150, 190, 54, 84, 100, 34
    h = top + len(ROWS) * row_h + 10
    tile_bg = t["bg2"].lstrip("#")
    parts, k = [], 0
    for r, (label, items) in enumerate(ROWS):
        y = top + r * row_h
        parts.append(f'<text x="40" y="{y + 32}" font-family="{font}" font-size="13" font-weight="600" fill="{t["muted"]}">{label}</text>')
        for i, (slug, caption, mono_txt) in enumerate(items):
            x = x0 + i * gap
            cx = x + tile / 2
            if slug:
                color = icons[slug]["hex"]
                if _contrast(color, tile_bg) < 2.2:   # dark logo on dark tile: use text colour
                    color = t["text"].lstrip("#")
                s = 26 / 24
                glyph = (f'<path transform="translate({cx - 13:.1f} {y + 14}) scale({s:.4f})" '
                         f'd="{icons[slug]["d"]}" fill="#{color}"/>')
            elif mono_txt == "~wave":
                bars = [6, 14, 22, 12, 18, 8, 16, 10]
                glyph = "".join(
                    f'<rect x="{cx - 17 + j * 4.6:.1f}" y="{y + 27 - b / 2}" width="2.6" height="{b}" rx="1.3" fill="url(#acc)"/>'
                    for j, b in enumerate(bars))
            else:
                size = 15 if len(mono_txt) <= 3 else 12.5
                glyph = (f'<text x="{cx}" y="{y + 32}" text-anchor="middle" font-family="{mono}" '
                         f'font-size="{size}" font-weight="700" fill="url(#acc)">{mono_txt}</text>')
            delay = 0.15 + k * 0.045
            float_delay = (k * 0.37) % 4
            parts.append(
                f'<g class="pop" style="animation-delay:{delay:.2f}s"><g class="float" style="animation-delay:-{float_delay:.2f}s">'
                f'<rect x="{x}" y="{y}" width="{tile}" height="{tile}" rx="14" fill="{t["bg2"]}" stroke="{t["border"]}"/>'
                f'{glyph}'
                f'<text x="{cx}" y="{y + tile + 17}" text-anchor="middle" font-family="{font}" font-size="11" fill="{t["muted"]}">{caption}</text>'
                f'</g></g>')
            k += 1
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Tech stack: Python, PyTorch, Whisper, local LLMs, RAG, OCR, FastAPI, PostgreSQL, React, TypeScript, Docker and more">
<title>Tech stack</title>
<defs>
  <linearGradient id="acc" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t['a1']}"/><stop offset="1" stop-color="{t['a2']}"/></linearGradient>
  <linearGradient id="shine" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t['a2']}" stop-opacity="0"/><stop offset=".5" stop-color="{t['a2']}" stop-opacity=".10"/><stop offset="1" stop-color="{t['a2']}" stop-opacity="0"/></linearGradient>
  <clipPath id="card"><rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="14"/></clipPath>
</defs>
<style>
  .pop {{ opacity: 0; transform-box: fill-box; transform-origin: center; animation: pop .55s cubic-bezier(.2,.9,.3,1.25) forwards; }}
  @keyframes pop {{ from {{ opacity: 0; transform: scale(.6); }} to {{ opacity: 1; transform: scale(1); }} }}
  .float {{ animation: float 4s ease-in-out infinite; }}
  @keyframes float {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-3px); }} }}
  .shine {{ animation: shine 7s ease-in-out 2.5s infinite; }}
  @keyframes shine {{ from {{ transform: translateX(-300px); }} 40%,to {{ transform: translateX({w + 300}px); }} }}
  @media (prefers-reduced-motion: reduce) {{ .pop {{ animation: none; opacity: 1; }} .float, .shine {{ animation: none; }} .shine {{ display: none; }} }}
</style>
<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="14" fill="{t['bg1']}" stroke="{t['border']}"/>
<g clip-path="url(#card)"><rect class="shine" x="0" y="0" width="260" height="{h}" fill="url(#shine)"/></g>
{"".join(parts)}
</svg>
'''
