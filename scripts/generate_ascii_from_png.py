"""
generate_ascii_from_png.py

Converts the generated ASCII art PNG reference image into a proper SVG
by sampling the green pixel density to map to actual ASCII characters.

Alternatively, just runs photo_to_ascii_svg.py if photo.jpg is present.

Usage:
    python scripts/generate_ascii_from_png.py
"""

import sys
from pathlib import Path
from PIL import Image

# ── Settings ────────────────────────────────────────────────────────────────
PHOTO_JPG = Path(__file__).resolve().parent.parent / "photo.jpg"
REF_PNG   = Path(r"C:\Users\divya\.gemini\antigravity-ide\brain\033c0e8f-4776-4312-90fb-b7aeabda84b8\ascii_art_clean_1786133469850.png")
OUT_PATH  = Path(__file__).resolve().parent.parent / "avi-ascii.svg"

# ASCII ramp: space (light/bg) → dense chars (dark/shadow)
RAMP = " .`'-_,;:i!|1tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"

COLS = 52
ROWS = 38
FONT_SIZE = 8.5
CHAR_W    = FONT_SIZE * 0.602
CHAR_H    = FONT_SIZE * 1.20
PAD_X     = 14
PAD_Y     = 42
BG        = "#0d1117"
BORDER    = "#30363d"
GREEN     = "#39d353"
BLUE      = "#58a6ff"
FG        = "#c9d1d9"
STAGGER   = 0.018
FADE      = 0.28
USERNAME  = "divyal-11"


def image_to_ascii(img_path: Path, invert: bool = False) -> list[str]:
    """Convert any image to ASCII art rows."""
    img = Image.open(img_path).convert("RGB")
    w, h = img.size

    # For the PNG ref image, crop to just the portrait region (center)
    if img_path.suffix == ".png" and w == h:
        # Crop center 70% to focus on face region
        margin = int(w * 0.05)
        img = img.crop((margin, margin, w - margin, h - margin))

    # Square-crop biased upward for faces
    w2, h2 = img.size
    side     = min(w2, h2)
    left     = (w2 - side) // 2
    top_bias = int(h2 * 0.06) if img_path.suffix == ".jpg" else 0
    top      = max(0, (h2 - side) // 2 - top_bias)
    img      = img.crop((left, top, left + side, top + side))

    # Resize to char grid
    img = img.resize((COLS, ROWS), Image.LANCZOS)

    # For the reference PNG: extract green channel (ascii chars are green on black)
    # Green channel intensity = density of characters = darkness in portrait
    if img_path.suffix == ".png":
        r_ch, g_ch, b_ch = img.split()
        pixels = list(g_ch.getdata())
        # In this image: bright green = chars = dark face areas; black = background = light face
        # So we need to invert: high green → dense char
        invert = False  # green channel already maps: bright=chars=darker portrait areas
    else:
        grey   = img.convert("L")
        pixels = list(grey.getdata())
        invert = True   # for real photos: bright pixel = light = sparse char

    lo, hi = min(pixels), max(pixels)
    span   = hi - lo or 1

    lines = []
    for r in range(ROWS):
        row = []
        for c in range(COLS):
            v = pixels[r * COLS + c]
            n = (v - lo) / span
            n = max(0.0, min(1.0, n * 1.3 - 0.12))
            if invert:
                n = 1.0 - n
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
    # Prefer actual photo if present
    if PHOTO_JPG.exists():
        src = PHOTO_JPG
        print(f"Using {src}")
    elif REF_PNG.exists():
        src = REF_PNG
        print(f"Photo not found; using reference PNG: {src}")
    else:
        print("ERROR: Neither photo.jpg nor reference PNG found.")
        sys.exit(1)

    lines = image_to_ascii(src)
    svg   = build_svg(lines)
    OUT_PATH.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUT_PATH}  ({len(lines)} rows × {COLS} cols)")
