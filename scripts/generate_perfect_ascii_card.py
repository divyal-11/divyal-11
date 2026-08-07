"""
generate_perfect_ascii_card.py

Generates a perfectly dimensioned avi-ascii.svg terminal card from photo image.png.
Matches info-card.svg theme, fits 100% within viewBox, zero clipping.
"""

import sys
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter

PHOTO_PATH = Path("C:/Users/divya/Downloads/github-profile-art/image.png")
OUT_PATH   = Path("C:/Users/divya/Downloads/github-profile-art/divyal-11/avi-ascii.svg")

USERNAME = "divyal-11"

# ASCII Density Ramp (dark -> bright mapped to dense -> sparse)
RAMP = " .`:-=+*cs#%@"

# Canvas & Layout Params
VIEW_W = 370
VIEW_H = 470
PADDING_X = 14
TITLE_BAR_H = 34

# ASCII Grid Params
COLS = 50
ROWS = 32
FONT_SIZE = 8.5
ROW_HEIGHT = 11.8
START_Y = 52

BG_COLOR     = "#0d1117"
BORDER_COLOR = "#30363d"
GREEN_COLOR  = "#39d353"
BLUE_COLOR   = "#58a6ff"
TITLE_COLOR  = "#c9d1d9"

STAGGER_DUR  = 0.020  # sec between rows
FADE_DUR     = 0.35   # sec fade duration


def photo_to_ascii(photo_file: Path) -> list[str]:
    img = Image.open(photo_file).convert("RGB")
    w, h = img.size

    # Crop face: square crop top 85%
    crop_size = min(w, int(h * 0.85))
    left = (w - crop_size) // 2
    top = int(h * 0.05)
    crop = img.crop((left, top, left + crop_size, top + crop_size))

    # Resize to ASCII grid dimensions
    grey = crop.convert("L")
    grey = ImageEnhance.Contrast(grey).enhance(1.7)
    grey = ImageEnhance.Sharpness(grey).enhance(2.0)
    grey = grey.resize((COLS, ROWS), Image.LANCZOS)

    pixels = list(grey.tobytes())
    lo, hi = min(pixels), max(pixels)
    span = hi - lo or 1

    lines = []
    ramp_len = len(RAMP) - 1
    for r in range(ROWS):
        line = []
        for c in range(COLS):
            v = pixels[r * COLS + c]
            n = (v - lo) / span
            # Invert: dark area -> dense char
            idx = int((1.0 - n) * ramp_len)
            idx = max(0, min(ramp_len, idx))
            line.append(RAMP[idx])
        lines.append("".join(line))
    return lines


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(lines: list[str]) -> str:
    parts = [
        f'<svg viewBox="0 0 {VIEW_W} {VIEW_H}" width="{VIEW_W}" height="{VIEW_H}" xmlns="http://www.w3.org/2000/svg">',
        # Background card
        f'<rect x="0" y="0" width="{VIEW_W}" height="{VIEW_H}" rx="10" fill="{BG_COLOR}" stroke="{BORDER_COLOR}" />',
        # Title bar
        f'<rect x="0" y="0" width="{VIEW_W}" height="{TITLE_BAR_H}" rx="10" fill="{BORDER_COLOR}" />',
        f'<rect x="0" y="16" width="{VIEW_W}" height="18" fill="{BORDER_COLOR}" />',
        # Traffic light buttons
        f'<circle cx="20" cy="17" r="6" fill="#ff5f56" />',
        f'<circle cx="40" cy="17" r="6" fill="#ffbd2e" />',
        f'<circle cx="60" cy="17" r="6" fill="#27c93f" />',
        # Title text
        f'<text x="{VIEW_W / 2}" y="21" text-anchor="middle" font-family="Consolas, Menlo, monospace" font-size="12" fill="{TITLE_COLOR}">{esc(USERNAME)}@github</text>',
    ]

    # ASCII text lines
    for r, line in enumerate(lines):
        y = START_Y + r * ROW_HEIGHT
        begin = r * STAGGER_DUR
        safe_line = esc(line)
        parts.append(
            f'<g opacity="0" transform="translate(0,-4)">'
            f'<text x="{PADDING_X}" y="{y:.1f}" font-family="Consolas, Menlo, monospace" font-size="{FONT_SIZE}" fill="{GREEN_COLOR}" xml:space="preserve">{safe_line}</text>'
            f'<animate attributeName="opacity" from="0" to="1" begin="{begin:.3f}s" dur="{FADE_DUR}s" fill="freeze" />'
            f'<animateTransform attributeName="transform" type="translate" from="0 -4" to="0 0" begin="{begin:.3f}s" dur="{FADE_DUR}s" fill="freeze" calcMode="spline" keySplines="0.2 0 0.2 1" keyTimes="0;1" />'
            f'</g>'
        )

    # Footer username tag
    footer_y = START_Y + ROWS * ROW_HEIGHT + 14
    parts.append(
        f'<text x="{VIEW_W / 2}" y="{footer_y:.1f}" text-anchor="middle" font-family="Consolas, Menlo, monospace" font-size="12" font-weight="bold" fill="{BLUE_COLOR}">{esc(USERNAME)}</text>'
    )

    parts.append('</svg>')
    return "\n".join(parts)


if __name__ == "__main__":
    lines = photo_to_ascii(PHOTO_PATH)
    svg = build_svg(lines)
    OUT_PATH.write_text(svg, encoding="utf-8")
    print(f"Successfully generated {OUT_PATH} ({len(svg)} bytes, viewBox 0 0 {VIEW_W} {VIEW_H})")
