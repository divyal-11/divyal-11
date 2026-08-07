"""
make_info_card.py

Hand-authored SVG that looks like `neofetch` output: a title bar, then
colored key/value rows. Each row fades + slides in on a short stagger.

Edit the CONFIG block below with your own details, then run:
    python make_info_card.py            # writes info-card.svg (animated)
    STATIC=1 python make_info_card.py    # writes a frozen frame (for previews)
"""

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIG — edit this block
# ---------------------------------------------------------------------------
CONFIG = {
    "user_at_host": "divyal-11@github",
    "now": "Final-Year CS (AIML) @ IIIT Nagpur",
    "prev": "Full-Stack + AI Engineering Internships",
    "stack": "TypeScript · Next.js · Node.js · PostgreSQL · Redis · Docker",
    "ai_stack": "LangGraph · LangChain · RAG Pipelines",
    "highlights": [
        "URL Shortener — Next.js/Prisma/Redis, deployed (Vercel/Neon/Upstash)",
        "HireCodec — real-time collaborative interview platform",
        "LedgerCore — double-entry accounting engine",
        "PulseBoard — live infrastructure metrics dashboard",
    ],
}
# ---------------------------------------------------------------------------

WIDTH = 490
LABEL_COLOR = "#39d353"
VALUE_COLOR = "#c9d1d9"
BG_COLOR = "#0d1117"
BORDER_COLOR = "#30363d"
TITLE_COLOR = "#58a6ff"
LINE_HEIGHT = 22
STAGGER = 0.12
FADE_DUR = 0.4


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_rows(cfg: dict) -> list[tuple[str, str]]:
    rows = [
        ("Now", cfg["now"]),
        ("Prev", cfg["prev"]),
        ("Stack", cfg["stack"]),
        ("AI/ML", cfg["ai_stack"]),
    ]
    for i, h in enumerate(cfg["highlights"]):
        label = "Highlights" if i == 0 else ""
        rows.append((label, h))
    return rows


def build_svg(cfg: dict, static: bool = False) -> str:
    rows = build_rows(cfg)
    title = f"{cfg['user_at_host']}: ~"
    height = 50 + LINE_HEIGHT * (len(rows) + 1)

    lines_svg = []
    for i, (label, value) in enumerate(rows):
        y = 60 + i * LINE_HEIGHT
        label_span = f'<tspan fill="{LABEL_COLOR}" font-weight="600">{esc(label)}</tspan>' if label else ""
        sep = "  " if label else ""
        text = (
            f'<text x="24" y="{y}" font-family="Consolas, Menlo, monospace" '
            f'font-size="13" fill="{VALUE_COLOR}">'
            f'{label_span}{sep}<tspan fill="{VALUE_COLOR}">{esc(value)}</tspan>'
            f'</text>'
        )
        if static:
            lines_svg.append(f'<g>{text}</g>')
        else:
            begin = i * STAGGER
            lines_svg.append(
                f'<g opacity="0" transform="translate(-12,0)">'
                f'{text}'
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{begin:.2f}s" dur="{FADE_DUR}s" fill="freeze" />'
                f'<animateTransform attributeName="transform" type="translate" '
                f'from="-12 0" to="0 0" begin="{begin:.2f}s" dur="{FADE_DUR}s" '
                f'fill="freeze" additive="sum" calcMode="spline" '
                f'keySplines="0.2 0 0.2 1" keyTimes="0;1" />'
                f'</g>'
            )

    svg = (
        f'<svg viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<rect x="0" y="0" width="{WIDTH}" height="{height}" rx="10" '
        f'fill="{BG_COLOR}" stroke="{BORDER_COLOR}" />'
        f'<rect x="0" y="0" width="{WIDTH}" height="34" rx="10" fill="{BORDER_COLOR}" />'
        f'<rect x="0" y="16" width="{WIDTH}" height="18" fill="{BORDER_COLOR}" />'
        f'<circle cx="20" cy="17" r="6" fill="#ff5f56" />'
        f'<circle cx="40" cy="17" r="6" fill="#ffbd2e" />'
        f'<circle cx="60" cy="17" r="6" fill="#27c93f" />'
        f'<text x="{WIDTH / 2}" y="21" text-anchor="middle" font-family="Consolas, Menlo, monospace" '
        f'font-size="12" fill="{VALUE_COLOR}">{esc(title)}</text>'
        f'{"".join(lines_svg)}'
        f'</svg>'
    )
    return svg


if __name__ == "__main__":
    static = bool(os.environ.get("STATIC"))
    svg = build_svg(CONFIG, static=static)
    out = "info-card-static.svg" if static else "info-card.svg"
    Path(out).write_text(svg, encoding="utf-8")
    print(f"Wrote {out}")
