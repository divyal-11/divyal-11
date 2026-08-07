"""
render_heatmap_svg.py

Reads data/contributions.json and draws the classic 53-week x 7-day
calendar as rounded, colored boxes. Reveals once with a diagonal,
line-after-line slide-down (CSS keyframes that play on load, then
freeze -- no looping), plus a Less->More legend and a stats footer.

Usage:
    python render_heatmap_svg.py
    # writes: ../contrib-heatmap.svg
"""

import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "contributions.json"
OUT_PATH = Path(__file__).resolve().parent.parent / "contrib-heatmap.svg"

# none -> brightest (level 5 kept as a neon top end, matches the style
# of the highest activity days rather than GitHub's stock 0-4 scale)
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

CELL = 11
GAP = 3
LEFT_PAD = 30
TOP_PAD = 20
LEGEND_H = 30
FOOTER_H = 24
STAGGER_PER_DIAGONAL = 0.02
CELL_FADE_DUR = 0.35

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def level_for_count(count: int, max_count: int) -> int:
    if count <= 0:
        return 0
    if max_count <= 0:
        return 1
    ratio = count / max_count
    if ratio > 0.85:
        return 5
    if ratio > 0.6:
        return 4
    if ratio > 0.35:
        return 3
    if ratio > 0.1:
        return 2
    return 1


def build_weeks(days: list[dict]) -> list[list[dict | None]]:
    """Group days into weeks (columns) of 7 (Sun..Sat rows), padding the
    first/last week so every column has 7 slots."""
    if not days:
        return []

    from datetime import datetime

    weeks: list[list[dict | None]] = []
    current_week: list[dict | None] = []

    first_date = datetime.strptime(days[0]["date"], "%Y-%m-%d")
    lead_pad = (first_date.weekday() + 1) % 7  # Python Mon=0 -> GitHub Sun=0
    current_week.extend([None] * lead_pad)

    for d in days:
        current_week.append(d)
        if len(current_week) == 7:
            weeks.append(current_week)
            current_week = []

    if current_week:
        current_week.extend([None] * (7 - len(current_week)))
        weeks.append(current_week)

    return weeks


def build_svg(payload: dict) -> str:
    days = payload["days"]
    stats = payload["stats"]
    max_count = max((d["count"] or 0) for d in days) if days else 0

    weeks = build_weeks(days)
    n_weeks = len(weeks)

    width = LEFT_PAD + n_weeks * (CELL + GAP) + 20
    height = TOP_PAD + 7 * (CELL + GAP) + LEGEND_H + FOOTER_H

    cells_svg = []
    month_labels = []
    seen_months = set()

    for wi, week in enumerate(weeks):
        x = LEFT_PAD + wi * (CELL + GAP)
        for di, day in enumerate(week):
            y = TOP_PAD + di * (CELL + GAP)
            if day is None:
                continue
            count = day["count"] or 0
            level = level_for_count(count, max_count)
            color = PALETTE[level]
            date = day["date"]
            month_key = date[:7]
            if di == 0 and month_key not in seen_months:
                seen_months.add(month_key)
                month = int(date[5:7])
                month_labels.append((x, MONTH_NAMES[month - 1]))

            # diagonal stagger: cells further down-right start later
            begin = (wi + di) * STAGGER_PER_DIAGONAL
            cells_svg.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" '
                f'fill="{color}" opacity="0" transform="translate(0,-6)">'
                f'<title>{count} contribution{"s" if count != 1 else ""} on {date}</title>'
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{begin:.3f}s" dur="{CELL_FADE_DUR}s" fill="freeze" />'
                f'<animateTransform attributeName="transform" type="translate" '
                f'from="0 -6" to="0 0" begin="{begin:.3f}s" dur="{CELL_FADE_DUR}s" '
                f'fill="freeze" calcMode="spline" keySplines="0.2 0 0.2 1" keyTimes="0;1" />'
                f'</rect>'
            )

    month_svg = "".join(
        f'<text x="{x}" y="{TOP_PAD - 6}" font-family="Consolas, Menlo, monospace" '
        f'font-size="10" fill="#8b949e">{name}</text>'
        for x, name in month_labels
    )

    legend_y = TOP_PAD + 7 * (CELL + GAP) + 12
    legend_swatches = []
    lx = LEFT_PAD
    legend_swatches.append(
        f'<text x="{lx}" y="{legend_y + 9}" font-family="Consolas, Menlo, monospace" '
        f'font-size="10" fill="#8b949e">Less</text>'
    )
    lx += 34
    for level, color in enumerate(PALETTE):
        legend_swatches.append(
            f'<rect x="{lx}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}" />'
        )
        lx += CELL + GAP
    legend_swatches.append(
        f'<text x="{lx + 4}" y="{legend_y + 9}" font-family="Consolas, Menlo, monospace" '
        f'font-size="10" fill="#8b949e">More</text>'
    )

    footer_y = legend_y + LEGEND_H
    footer_text = (
        f'{stats["total_last_year"]} contributions in the last year · '
        f'current streak {stats["current_streak"]}d · longest streak {stats["longest_streak"]}d'
    )

    svg = (
        f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'{month_svg}'
        f'{"".join(cells_svg)}'
        f'{"".join(legend_swatches)}'
        f'<text x="{LEFT_PAD}" y="{footer_y}" font-family="Consolas, Menlo, monospace" '
        f'font-size="11" fill="#8b949e">{footer_text}</text>'
        f'</svg>'
    )
    return svg


if __name__ == "__main__":
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    svg = build_svg(payload)
    OUT_PATH.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
