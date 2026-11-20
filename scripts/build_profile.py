"""Build the dynamic parts of the GitHub profile README.

Generates:
  - assets/header-{light,dark}.svg    animated "live transcript" banner
  - assets/waveform-{light,dark}.svg  last year's contributions drawn as an audio waveform
  - the "Now" section of README.md     latest public repositories

Standard library only. Needs a token in GITHUB_TOKEN or GH_TOKEN.
"""

from __future__ import annotations

import json
import math
import os
import re
import urllib.request
from datetime import datetime
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tech_grid import tech_svg  # noqa: E402

USER = os.environ.get("PROFILE_USER", "abirchebbi45")
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
README = ROOT / "README.md"

THEMES = {
    "light": {
        "bg1": "#f8fafc", "bg2": "#eef2ff", "border": "#e2e8f0",
        "text": "#0f172a", "muted": "#475569", "faint": "#94a3b8",
        "a1": "#6d28d9", "a2": "#0d9488", "line": "#cbd5e1",
    },
    "dark": {
        "bg1": "#0d1117", "bg2": "#161b2e", "border": "#30363d",
        "text": "#e6edf3", "muted": "#9da7b3", "faint": "#6e7681",
        "a1": "#a78bfa", "a2": "#2dd4bf", "line": "#30363d",
    },
}

FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,monospace"


# ---------------------------------------------------------------- GitHub API

def _token() -> str:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN or GH_TOKEN is required")
    return token


def _request(url: str, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Bearer {_token()}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-readme-builder",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def fetch_weeks() -> tuple[list[int], list[str], int, list[tuple[str, int]]]:
    """Weekly contribution totals for the last year, with month labels."""
    query = """query($login:String!){user(login:$login){contributionsCollection{
      contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}"""
    data = _request("https://api.github.com/graphql",
                    {"query": query, "variables": {"login": USER}})
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    totals, firsts, daily = [], [], []
    for week in cal["weeks"]:
        days = week["contributionDays"]
        totals.append(sum(d["contributionCount"] for d in days))
        firsts.append(days[0]["date"])
        daily.extend((d["date"], d["contributionCount"]) for d in days)
    return totals, firsts, cal["totalContributions"], daily


def year_stats(weeks: list[int], daily: list[tuple[str, int]], total: int) -> list[tuple[str, str]]:
    """Headline numbers derived only from the public contribution calendar."""
    active_weeks = sum(1 for w in weeks if w)
    longest = run = 0
    for _, count in daily:
        run = run + 1 if count else 0
        longest = max(longest, run)
    months: dict[str, int] = {}
    for date, count in daily:
        months[date[:7]] = months.get(date[:7], 0) + count
    busiest = max(months, key=months.get)
    busiest_label = datetime.strptime(busiest, "%Y-%m").strftime("%b %Y")
    return [
        (f"{total}", "contributions"),
        (f"{active_weeks}/{len(weeks)}", "active weeks"),
        (busiest_label, f"busiest month · {months[busiest]}"),
        (f"{longest} days", "longest streak"),
    ]


def fetch_recent_repos(limit: int = 4) -> list[dict]:
    repos = _request(f"https://api.github.com/users/{USER}/repos?per_page=100&sort=pushed")
    keep = [r for r in repos
            if not r["fork"] and not r["archived"] and r["name"].lower() != USER.lower()]
    return keep[:limit]


# ---------------------------------------------------------------- SVG: header

def header_svg(t: dict) -> str:
    w, h = 1200, 300
    # Animated waveform: bars pulse with staggered delays, like live audio.
    bars = []
    n = 44
    for i in range(n):
        x = 64 + i * 9
        base = 10 + 46 * abs(math.sin(i * 0.55)) * (0.55 + 0.45 * math.sin(i * 0.17))
        delay = (i % 11) * 0.09
        bars.append(
            f'<rect class="bar" x="{x}" y="{150 - base / 2:.1f}" width="4" height="{base:.1f}" rx="2" '
            f'style="animation-delay:{delay:.2f}s"/>'
        )
    line1 = "[00:00:01] SPEAKER_01"
    line2 = "AI Tech Lead — I take speech &amp; language AI from prototype to production."
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Abir Chebbi — AI Tech Lead">
<title>Abir Chebbi — AI Tech Lead</title>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t['bg1']}"/><stop offset="1" stop-color="{t['bg2']}"/></linearGradient>
  <linearGradient id="ac" gradientUnits="userSpaceOnUse" x1="64" y1="0" x2="460" y2="0"><stop offset="0" stop-color="{t['a1']}"/><stop offset="1" stop-color="{t['a2']}"/></linearGradient>
  <clipPath id="type"><rect class="typer" x="520" y="168" width="0" height="40"/></clipPath>
</defs>
<style>
  .bar {{ fill: url(#ac); transform-box: fill-box; transform-origin: center; animation: pulse 1.1s ease-in-out infinite alternate; }}
  @keyframes pulse {{ from {{ transform: scaleY(.35); }} to {{ transform: scaleY(1); }} }}
  .typer {{ animation: type 3.2s steps(74, end) .6s forwards; }}
  @keyframes type {{ to {{ width: 680px; }} }}
  .caret {{ animation: blink 1s step-end infinite, move 3.2s steps(74, end) .6s forwards; }}
  @keyframes blink {{ 50% {{ opacity: 0; }} }}
  @keyframes move {{ to {{ transform: translateX(680px); }} }}
  .fade {{ opacity: 0; animation: fade .8s ease-out forwards; }}
  @keyframes fade {{ to {{ opacity: 1; }} }}
  @media (prefers-reduced-motion: reduce) {{
    .bar, .caret {{ animation: none; }} .typer {{ animation: none; width: 680px; }} .fade {{ animation: none; opacity: 1; }}
  }}
</style>
<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="18" fill="url(#bg)" stroke="{t['border']}"/>
<g>{"".join(bars)}</g>
<line x1="470" y1="70" x2="470" y2="230" stroke="{t['line']}"/>
<text class="fade" x="520" y="118" font-family="{FONT}" font-size="54" font-weight="700" fill="{t['text']}">Abir Chebbi</text>
<text class="fade" x="520" y="160" font-family="{MONO}" font-size="15" fill="{t['faint']}" style="animation-delay:.3s">{line1}</text>
<g clip-path="url(#type)"><text x="520" y="194" font-family="{MONO}" font-size="15" fill="{t['muted']}">{line2}</text></g>
<rect class="caret" x="520" y="178" width="9" height="21" fill="{t['a2']}"/>
<text class="fade" x="520" y="244" font-family="{FONT}" font-size="15" fill="{t['faint']}" style="animation-delay:3.9s">Speech AI · RAG · LLMs · OCR · FastAPI · PostgreSQL RLS · React</text>
</svg>
'''


# ---------------------------------------------------------------- SVG: waveform

def waveform_svg(t: dict, weeks: list[int], firsts: list[str], total: int,
                 stats: list[tuple[str, str]]) -> str:
    w, h = 900, 300
    left, right, mid = 40, 860, 182
    n = len(weeks)
    step = (right - left) / max(n, 1)
    peak = max(weeks) or 1
    bars, labels = [], []
    last_month = None
    for i, (count, first) in enumerate(zip(weeks, firsts)):
        x = left + i * step
        amp = 4 + 70 * math.sqrt(count / peak) if count else 2
        delay = i * 0.025
        bars.append(
            f'<rect class="b" x="{x:.1f}" y="{mid - amp:.1f}" width="{max(step - 4, 2):.1f}" '
            f'height="{2 * amp:.1f}" rx="2" style="animation-delay:{delay:.2f}s">'
            f'<title>Week of {first}: {count} contributions</title></rect>'
        )
        month = first[:7]
        if month != last_month and i > 0:
            label = datetime.strptime(first, "%Y-%m-%d").strftime("%b")
            labels.append(f'<text x="{x:.1f}" y="{h - 30}" font-size="11" fill="{t["faint"]}">{label}</text>')
        last_month = month
    sweep = right - left
    col = (right - left) / len(stats)
    tiles = "".join(
        f'<text x="{left + i * col:.0f}" y="50" font-family="{FONT}" font-size="24" font-weight="700" fill="url(#g)">{value}</text>'
        f'<text x="{left + i * col:.0f}" y="70" font-family="{FONT}" font-size="12" fill="{t["muted"]}">{label}</text>'
        for i, (value, label) in enumerate(stats))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{total} contributions in the last year, drawn as an audio waveform">
<title>{total} contributions in the last year</title>
<defs><linearGradient id="g" gradientUnits="userSpaceOnUse" x1="{left}" y1="0" x2="{right}" y2="0"><stop offset="0" stop-color="{t['a1']}"/><stop offset="1" stop-color="{t['a2']}"/></linearGradient></defs>
<style>
  .b {{ fill: url(#g); transform-box: fill-box; transform-origin: center; transform: scaleY(0); animation: grow .6s ease-out forwards; }}
  @keyframes grow {{ to {{ transform: scaleY(1); }} }}
  .head {{ animation: sweep 6s linear 1.8s infinite; }}
  @keyframes sweep {{ from {{ transform: translateX(0); }} to {{ transform: translateX({sweep}px); }} }}
  @media (prefers-reduced-motion: reduce) {{ .b {{ animation: none; transform: none; }} .head {{ display: none; }} }}
</style>
<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="14" fill="{t['bg1']}" stroke="{t['border']}"/>
{tiles}
<line x1="{left}" y1="90" x2="{right}" y2="90" stroke="{t['line']}"/>
<line x1="{left}" y1="{mid}" x2="{right}" y2="{mid}" stroke="{t['line']}"/>
<g font-family="{FONT}">{"".join(bars)}{"".join(labels)}</g>
<line class="head" x1="{left}" y1="104" x2="{left}" y2="{h - 48}" stroke="{t['text']}" stroke-opacity=".45" stroke-width="1.5"/>
<text x="{left}" y="{h - 10}" font-family="{MONO}" font-size="12" fill="{t['muted']}">Last 12 months · public + private repositories · one bar = one week</text>
</svg>
'''


# ---------------------------------------------------------------- README "Now"

# Repositories created before this date are older work; "Now" only lists newer ones.
NEW_WORK_SINCE = os.environ.get("NEW_WORK_SINCE", "2026-11-20")

BUILDING_IN_PUBLIC = (
    "**Building in public.** Open-source tools around LLM evaluation, speech AI and "
    "PostgreSQL security — first release coming soon."
)


def now_section(repos: list[dict]) -> str:
    repos = [r for r in repos if r["created_at"][:10] >= NEW_WORK_SINCE]
    if not repos:
        return BUILDING_IN_PUBLIC
    lines = []
    for r in repos:
        desc = (r.get("description") or "").strip()
        if len(desc) > 110:
            desc = desc[:107].rstrip() + "…"
        when = datetime.strptime(r["pushed_at"][:10], "%Y-%m-%d").strftime("%b %Y")
        lines.append(f"- [**{r['name']}**]({r['html_url']}) — {desc} <sub>· updated {when}</sub>")
    stamp = datetime.utcnow().strftime("%Y-%m-%d")
    lines.append(f"\n<sub>Auto-updated weekly by a GitHub Action · last run {stamp}</sub>")
    return "\n".join(lines)


def replace_block(text: str, name: str, content: str) -> str:
    pattern = re.compile(rf"(<!-- {name}:START -->)(.*?)(<!-- {name}:END -->)", re.S)
    return pattern.sub(lambda m: f"{m.group(1)}\n{content}\n{m.group(3)}", text)


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    weeks, firsts, total, daily = fetch_weeks()
    stats = year_stats(weeks, daily, total)
    for name, theme in THEMES.items():
        (ASSETS / f"header-{name}.svg").write_text(header_svg(theme), encoding="utf-8")
        (ASSETS / f"stack-{name}.svg").write_text(
            tech_svg(theme, ASSETS / "icons.json", FONT, MONO), encoding="utf-8")
        (ASSETS / f"waveform-{name}.svg").write_text(
            waveform_svg(theme, weeks, firsts, total, stats), encoding="utf-8")
    text = README.read_text(encoding="utf-8")
    README.write_text(replace_block(text, "NOW", now_section(fetch_recent_repos())), encoding="utf-8")


if __name__ == "__main__":
    main()
