"""
photo_to_ascii_svg.py

Converts a portrait photo → an animated ASCII-art SVG in the same
dark terminal aesthetic as info-card.svg and contrib-heatmap.svg.

Usage:
    python scripts/photo_to_ascii_svg.py photo.jpg
    # writes avi-ascii.svg in the repo root

Dependencies: pillow only (no rembg, no opencv, no numpy)
"""

import sys
from pathlib import Path
from PIL import Image

# ── tunables ────────────────────────────────────────────────────────────────
# ASCII density ramp: darkest → brightest characters
RAMP = " .`-_':,;i!|1tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
# Output canvas: width in characters, height auto-computed from aspect ratio
COLS = 55
ROWS = 38          # roughly (COLS * char_h/char_w), chars ~2:1 h/w
FONT_SIZE = 9      # px, monospace
CHAR_W = FONT_SIZE * 0.60   # approximate advance width
CHAR_H = FONT_SIZE * 1.20   # line height
PAD_X = 18
PAD_Y = 42          # leave room for title bar
BORDER_RADIUS = 10

BG      = "#0d1117"
BORDER  = "#30363d"
GREEN   = "#39d353"
DIM     = "#8b949e"
BLUE    = "#58a6ff"
FG      = "#c9d1d9"

STAGGER = 0.015    # seconds per row, for cascade animation
FADE    = 0.35     # seconds per row fade duration
# ────────────────────────────────────────────────────────────────────────────


def photo_to_ascii(img_path: Path, cols: int, rows: int) -> list[str]:
    """Return a list of `rows` strings, each `cols` chars wide."""
    img = Image.open(img_path).convert("RGB")

    # ── crop to a square centred on the face ────────────────────────────────
    w, h = img.size
    # Bias the crop upward by 10 % so the face sits centrally
    top_bias = int(h * 0.08)
    side = min(w, h)
    left  = (w - side) // 2
    top   = max(0, (h - side) // 2 - top_bias)
    img   = img.crop((left, top, left + side, top + side))

    # ── resize to ASCII canvas ───────────────────────────────────────────────
    # Each character cell is roughly 2× taller than wide, so shrink height
    img = img.resize((cols, rows), Image.LANCZOS)

    # ── convert to greyscale with mild contrast boost ────────────────────────
    grey = img.convert("L")
    pixels = list(grey.getdata())

    lo, hi = min(pixels), max(pixels)
    span = hi - lo or 1

    lines = []
    for r in range(rows):
        row_chars = []
        for c in range(cols):
            v = pixels[r * cols + c]
            # normalise 0-1, raise contrast slightly
            n = (v - lo) / span
            n = max(0.0, min(1.0, n * 1.25 - 0.1))
            idx = int(n * (len(RAMP) - 1))
            row_chars.append(RAMP[idx])
        lines.append("".join(row_chars))
    return lines


def escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(lines: list[str], username: str) -> str:
    n_rows = len(lines)
    n_cols = max(len(l) for l in lines)

    canvas_w = PAD_X * 2 + n_cols * CHAR_W
    canvas_h = PAD_Y + n_rows * CHAR_H + 24   # 24 px footer

    svg_parts = []

    # ── background + title bar ───────────────────────────────────────────────
    svg_parts.append(
        f'<svg viewBox="0 0 {canvas_w:.0f} {canvas_h:.0f}" '
        f'width="{canvas_w:.0f}" height="{canvas_h:.0f}" '
        f'xmlns="http://www.w3.org/2000/svg">'
    )
    svg_parts.append(
        f'<rect x="0" y="0" width="{canvas_w:.0f}" height="{canvas_h:.0f}" '
        f'rx="{BORDER_RADIUS}" fill="{BG}" stroke="{BORDER}"/>'
    )
    # title bar strip
    svg_parts.append(
        f'<rect x="0" y="0" width="{canvas_w:.0f}" height="34" '
        f'rx="{BORDER_RADIUS}" fill="{BORDER}"/>'
    )
    svg_parts.append(
        f'<rect x="0" y="16" width="{canvas_w:.0f}" height="18" fill="{BORDER}"/>'
    )
    # traffic lights
    for cx, col in [(20, "#ff5f56"), (40, "#ffbd2e"), (60, "#27c93f")]:
        svg_parts.append(f'<circle cx="{cx}" cy="17" r="6" fill="{col}"/>')
    # title text
    svg_parts.append(
        f'<text x="{canvas_w/2:.0f}" y="21" text-anchor="middle" '
        f'font-family="Consolas, Menlo, monospace" font-size="12" fill="{FG}">'
        f'{escape(username)}@github — whoami</text>'
    )

    # ── ASCII rows with staggered fade-in ────────────────────────────────────
    for ri, line in enumerate(lines):
        y = PAD_Y + ri * CHAR_H + CHAR_H * 0.85   # baseline
        begin = ri * STAGGER
        safe  = escape(line)
        svg_parts.append(
            f'<g opacity="0" transform="translate(0,4)">'
            f'<text x="{PAD_X}" y="{y:.1f}" '
            f'font-family="Consolas, Menlo, monospace" font-size="{FONT_SIZE}" '
            f'letter-spacing="0" fill="{GREEN}">{safe}</text>'
            f'<animate attributeName="opacity" from="0" to="1" '
            f'begin="{begin:.3f}s" dur="{FADE}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="0 4" to="0 0" begin="{begin:.3f}s" dur="{FADE}s" '
            f'fill="freeze" calcMode="spline" keySplines="0.2 0 0.2 1" keyTimes="0;1"/>'
            f'</g>'
        )

    # ── footer label ─────────────────────────────────────────────────────────
    footer_y = PAD_Y + n_rows * CHAR_H + 14
    svg_parts.append(
        f'<text x="{canvas_w/2:.0f}" y="{footer_y:.0f}" text-anchor="middle" '
        f'font-family="Consolas, Menlo, monospace" font-size="11" fill="{BLUE}">'
        f'{escape(username)}</text>'
    )

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/photo_to_ascii_svg.py <photo_path> [github_username]")
        sys.exit(1)

    photo_path  = Path(sys.argv[1])
    username    = sys.argv[2] if len(sys.argv) > 2 else "divyal-11"
    out_path    = Path(__file__).resolve().parent.parent / "avi-ascii.svg"

    print(f"Converting {photo_path} → ASCII ({COLS}×{ROWS}) ...")
    lines = photo_to_ascii(photo_path, COLS, ROWS)
    svg   = build_svg(lines, username)
    out_path.write_text(svg, encoding="utf-8")
    print(f"Wrote {out_path}  ({len(lines)} rows × {COLS} cols)")
