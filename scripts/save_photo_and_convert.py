"""
save_photo_and_convert.py  — run once to generate avi-ascii.svg from the
base64-encoded portrait photo embedded below.

Usage:
    python scripts/save_photo_and_convert.py
"""

import base64, sys, io
from pathlib import Path
from PIL import Image

# ── ASCII density ramp (space = transparent bg, dense chars = dark areas) ──
RAMP = " .`'-_,;:i!|1tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
COLS = 52
ROWS = 36
FONT_SIZE = 9
CHAR_W    = FONT_SIZE * 0.602
CHAR_H    = FONT_SIZE * 1.22
PAD_X     = 16
PAD_Y     = 42
BG        = "#0d1117"
BORDER    = "#30363d"
GREEN     = "#39d353"
BLUE      = "#58a6ff"
FG        = "#c9d1d9"
STAGGER   = 0.018
FADE      = 0.30
USERNAME  = "divyal-11"

PHOTO_PATH = Path(__file__).resolve().parent.parent / "photo.jpg"
OUT_PATH   = Path(__file__).resolve().parent.parent / "avi-ascii.svg"


def photo_to_ascii(img_path: Path) -> list[str]:
    img = Image.open(img_path).convert("RGB")
    w, h = img.size

    # Square-crop biased slightly upward to center the face
    side     = min(w, h)
    left     = (w - side) // 2
    top_bias = int(h * 0.06)
    top      = max(0, (h - side) // 2 - top_bias)
    img      = img.crop((left, top, left + side, top + side))

    # Resize to char grid (chars are ~2x taller, so use ROWS//2 virtual rows
    # then duplicate each — actually just resize directly; CHAR_H handles it)
    img = img.resize((COLS, ROWS), Image.LANCZOS)

    # Convert to greyscale + mild contrast enhancement
    grey   = img.convert("L")
    pixels = list(grey.getdata())
    lo, hi = min(pixels), max(pixels)
    span   = hi - lo or 1

    lines = []
    for r in range(ROWS):
        row = []
        for c in range(COLS):
            v = pixels[r * COLS + c]
            n = (v - lo) / span
            # slight S-curve contrast
            n = max(0.0, min(1.0, n * 1.3 - 0.12))
            row.append(RAMP[int(n * (len(RAMP) - 1))])
        lines.append("".join(row))
    return lines


def esc(s: str) -> str:
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")


def build_svg(lines: list[str]) -> str:
    nR = len(lines)
    nC = max(len(l) for l in lines)
    W  = int(PAD_X * 2 + nC * CHAR_W)
    H  = int(PAD_Y + nR * CHAR_H + 22)

    parts = [
        f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg">',
        f'<rect x="0" y="0" width="{W}" height="{H}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
        # title bar
        f'<rect x="0" y="0" width="{W}" height="34" rx="10" fill="{BORDER}"/>',
        f'<rect x="0" y="16" width="{W}" height="18" fill="{BORDER}"/>',
        f'<circle cx="20" cy="17" r="6" fill="#ff5f56"/>',
        f'<circle cx="40" cy="17" r="6" fill="#ffbd2e"/>',
        f'<circle cx="60" cy="17" r="6" fill="#27c93f"/>',
        f'<text x="{W//2}" y="21" text-anchor="middle" font-family="Consolas,Menlo,monospace" font-size="12" fill="{FG}">{esc(USERNAME)}@github</text>',
    ]

    for ri, line in enumerate(lines):
        y     = PAD_Y + ri * CHAR_H + CHAR_H * 0.85
        begin = ri * STAGGER
        parts.append(
            f'<g opacity="0" transform="translate(0,5)">'
            f'<text x="{PAD_X}" y="{y:.1f}" font-family="Consolas,Menlo,monospace" '
            f'font-size="{FONT_SIZE}" fill="{GREEN}">{esc(line)}</text>'
            f'<animate attributeName="opacity" from="0" to="1" begin="{begin:.3f}s" dur="{FADE}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" from="0 5" to="0 0" '
            f'begin="{begin:.3f}s" dur="{FADE}s" fill="freeze" calcMode="spline" '
            f'keySplines="0.2 0 0.2 1" keyTimes="0;1"/>'
            f'</g>'
        )

    footer_y = int(PAD_Y + nR * CHAR_H + 14)
    parts.append(
        f'<text x="{W//2}" y="{footer_y}" text-anchor="middle" '
        f'font-family="Consolas,Menlo,monospace" font-size="11" fill="{BLUE}">{esc(USERNAME)}</text>'
    )
    parts.append('</svg>')
    return "\n".join(parts)


if __name__ == "__main__":
    if not PHOTO_PATH.exists():
        print(f"ERROR: photo not found at {PHOTO_PATH}")
        print("Please copy your photo as 'photo.jpg' into the repo root first.")
        sys.exit(1)

    print(f"Reading {PHOTO_PATH} ...")
    lines = photo_to_ascii(PHOTO_PATH)
    svg   = build_svg(lines)
    OUT_PATH.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUT_PATH}  ({len(lines)} rows × {COLS} cols, {len(svg)} bytes)")
