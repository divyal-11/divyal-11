"""
make_ascii_svg.py

Downsamples a grayscale image to a character grid and maps each cell's
brightness to a glyph from a density ramp (sparse -> dense == bright -> dark).
Renders the grid as a monochrome SVG where each row wipes in left-to-right,
staggered top to bottom, using SMIL <animate> on a per-row clipPath.
GitHub renders <img>-embedded SVGs and plays their SMIL/CSS animation.

Usage:
    python make_ascii_svg.py source-prepped.png
    # writes: avi-ascii.svg   (rename OUT_FILE below, or pass --out)
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

# bright (sparse) -> dark (dense); leading space clears background to nothing
RAMP = " .`:-=+*cs#%@"

CHAR_W = 6.2      # px advance per column (monospace-ish)
CHAR_H = 12        # px advance per row
FONT_SIZE = 12
FILL_COLOR = "#c9d1d9"          # single light-gray fill, no per-char color
BG_COLOR = "transparent"
ROW_STAGGER = 0.035              # seconds between each row's wipe starting
WIPE_DURATION = 0.5              # seconds for one row to fully wipe in


def image_to_grid(img_path: str, cols: int = 100, rows: int = 53) -> list[list[str]]:
    img = Image.open(img_path).convert("L").resize((cols, rows), Image.LANCZOS)
    arr = np.array(img)
    ramp_len = len(RAMP) - 1
    grid = []
    for r in range(rows):
        line = []
        for c in range(cols):
            brightness = arr[r, c] / 255.0          # 0 = black, 1 = white
            idx = round((1 - brightness) * ramp_len)  # invert: dark -> high idx
            line.append(RAMP[idx])
        grid.append(line)
    return grid


def build_svg(grid: list[list[str]]) -> str:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    width = cols * CHAR_W + 20
    height = rows * CHAR_H + 20

    defs = []
    row_groups = []

    for r, line in enumerate(grid):
        text = "".join(line).replace("&", "&amp;").replace("<", "&lt;")
        # Skip fully-blank rows quickly (still needs a clip to keep timing simple)
        clip_id = f"clip-row-{r}"
        y = 10 + (r + 1) * CHAR_H - 2

        defs.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="0" y="{y - CHAR_H + 2}" width="0" height="{CHAR_H}">'
            f'<animate attributeName="width" from="0" to="{width}" '
            f'begin="{r * ROW_STAGGER:.3f}s" dur="{WIPE_DURATION}s" '
            f'fill="freeze" calcMode="linear" />'
            f'</rect>'
            f'</clipPath>'
        )

        cursor_begin = r * ROW_STAGGER
        row_groups.append(
            f'<g clip-path="url(#{clip_id})">'
            f'<text x="10" y="{y}" font-family="Consolas, Menlo, monospace" '
            f'font-size="{FONT_SIZE}" xml:space="preserve" fill="{FILL_COLOR}">'
            f'{text}</text>'
            f'<rect x="10" y="{y - CHAR_H + 3}" width="{CHAR_W * 1.4:.1f}" height="{CHAR_H - 2}" '
            f'fill="{FILL_COLOR}" opacity="0.85">'
            f'<animate attributeName="x" from="10" to="{width}" '
            f'begin="{cursor_begin:.3f}s" dur="{WIPE_DURATION}s" fill="freeze" />'
            f'<animate attributeName="opacity" from="0.85" to="0" '
            f'begin="{cursor_begin + WIPE_DURATION:.3f}s" dur="0.15s" fill="freeze" />'
            f'</rect>'
            f'</g>'
        )

    svg = (
        f'<svg viewBox="0 0 {width:.0f} {height:.0f}" width="{width:.0f}" height="{height:.0f}" '
        f'xmlns="http://www.w3.org/2000/svg" style="background:{BG_COLOR}">'
        f'<defs>{"".join(defs)}</defs>'
        f'{"".join(row_groups)}'
        f'</svg>'
    )
    return svg


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("image", help="path to the *-prepped.png from prep_photo.py")
    ap.add_argument("--cols", type=int, default=100)
    ap.add_argument("--rows", type=int, default=53)
    ap.add_argument("--out", default="avi-ascii.svg")
    args = ap.parse_args()

    grid = image_to_grid(args.image, cols=args.cols, rows=args.rows)
    svg = build_svg(grid)
    Path(args.out).write_text(svg, encoding="utf-8")
    print(f"Wrote {args.out}")
