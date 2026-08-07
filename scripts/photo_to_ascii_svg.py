"""
photo_to_ascii_svg.py

Converts a portrait photo → an animated ASCII-art SVG in the same
dark terminal aesthetic as info-card.svg and contrib-heatmap.svg.

Usage:
    python scripts/photo_to_ascii_svg.py photo.jpg
    python scripts/photo_to_ascii_svg.py photo.jpg divyal-11
    # writes avi-ascii.svg in the repo root

Dependencies: pillow only (no rembg, no opencv, no numpy)
"""

import sys
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter

# ── tunables ────────────────────────────────────────────────────────────────
# Dense ramp: index 0 = empty/white bg, last = solid/black shadow
# Characters chosen for visual weight at small monospace sizes
RAMP = " `.-':_,;^~!i|1tfIjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"

# Grid dimensions
COLS = 60     # characters wide
ROWS = 45     # characters tall (chars are ~2× taller than wide, so ROWS < COLS/2 × 2)

FONT_SIZE   = 8     # px — smaller = more detail
CHAR_W      = FONT_SIZE * 0.601   # monospace advance width
CHAR_H      = FONT_SIZE * 1.18    # line height

PAD_X       = 12
PAD_Y       = 44   # below title bar
BORDER_R    = 10

# Theme colours (matching info-card.svg)
BG      = "#0d1117"
BORDER  = "#30363d"
GREEN   = "#39d353"
BLUE    = "#58a6ff"
FG      = "#c9d1d9"

STAGGER = 0.013   # seconds between rows
FADE    = 0.28    # seconds per row fade

# ── portrait crop params ────────────────────────────────────────────────────
# For a standard headshot: face starts ~5% from top, ends ~70% from top
FACE_TOP    = 0.00   # fraction of image height to start crop (0 = very top)
FACE_BOTTOM = 0.85   # fraction of image height to end crop
# ────────────────────────────────────────────────────────────────────────────


def load_and_prepare(img_path: Path) -> Image.Image:
    """Open, auto-orient, square-crop to face region, enhance contrast."""
    img = Image.open(img_path)

    # Auto-orient from EXIF
    try:
        from PIL import ImageOps
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    img = img.convert("RGB")
    w, h = img.size

    # --- portrait crop: take center column, FACE_TOP to FACE_BOTTOM rows ---
    crop_top    = int(h * FACE_TOP)
    crop_bottom = int(h * FACE_BOTTOM)
    crop_h      = crop_bottom - crop_top
    crop_w      = min(w, crop_h)            # square
    crop_left   = (w - crop_w) // 2
    img = img.crop((crop_left, crop_top, crop_left + crop_w, crop_bottom))

    return img


def image_to_ascii_lines(img: Image.Image) -> list[str]:
    """
    Resize to (COLS, ROWS), convert to greyscale, map to ASCII ramp.

    Character cells are roughly 0.6× wide as tall.  To avoid squashing the
    portrait we resize to (COLS, ROWS) but the vertical sampling interval is
    effectively CHAR_H/CHAR_W ≈ 2× the horizontal one, so we use half as
    many rows as we might expect — ROWS is already tuned for this.
    """
    # Step 1: resize to a 2× intermediate for better downsampling quality
    inter_w = COLS * 4
    inter_h = int(inter_w * img.height / img.width)
    img = img.resize((inter_w, inter_h), Image.LANCZOS)

    # Step 2: greyscale + contrast/sharpness boost
    grey = img.convert("L")
    grey = ImageEnhance.Contrast(grey).enhance(1.6)
    grey = ImageEnhance.Sharpness(grey).enhance(2.0)
    grey = grey.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=2))

    # Step 3: downsample to char grid
    # Compensate for the fact that characters are CHAR_H/CHAR_W approx 2x taller:
    # map ROWS chars -> ROWS * (CHAR_H/CHAR_W) vertical pixels of source
    char_aspect = CHAR_H / CHAR_W   # approx 1.96
    target_h    = int(ROWS * char_aspect)  # vertical pixels to sample
    grey = grey.resize((COLS, target_h), Image.LANCZOS)

    # Step 4: sample every (target_h // ROWS) rows to get exactly ROWS lines
    step   = max(1, target_h // ROWS)
    pixels = list(grey.tobytes())  # flat list of 0-255 ints (one channel)

    # Remap 0..255 with mild gamma for better midtone separation
    lo = min(pixels)
    hi = max(pixels)
    span = hi - lo or 1

    lines = []
    for r in range(ROWS):
        src_row = min(r * step, target_h - 1)
        row_chars = []
        for c in range(COLS):
            v = pixels[src_row * COLS + c]
            # Normalise + soft S-curve
            n = (v - lo) / span            # 0 (dark) → 1 (bright)
            n = n ** 0.85                  # slight gamma lift for midtones
            n = max(0.0, min(1.0, n))
            # Map: bright pixel (light face area) → sparse char; dark → dense
            # Invert so shadows → dense chars, highlights → spaces
            n_inv = 1.0 - n
            idx = int(n_inv * (len(RAMP) - 1))
            row_chars.append(RAMP[idx])
        lines.append("".join(row_chars))

    return lines


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(lines: list[str], username: str) -> str:
    n_rows = len(lines)
    n_cols = max(len(l) for l in lines)

    W = int(PAD_X * 2 + n_cols * CHAR_W)
    H = int(PAD_Y + n_rows * CHAR_H + 22)

    parts = [
        f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'xmlns="http://www.w3.org/2000/svg">',
        # Background
        f'<rect x="0" y="0" width="{W}" height="{H}" rx="{BORDER_R}" '
        f'fill="{BG}" stroke="{BORDER}"/>',
        # Title bar
        f'<rect x="0" y="0" width="{W}" height="34" rx="{BORDER_R}" fill="{BORDER}"/>',
        f'<rect x="0" y="16" width="{W}" height="18" fill="{BORDER}"/>',
        # Traffic lights
        f'<circle cx="20" cy="17" r="6" fill="#ff5f56"/>',
        f'<circle cx="40" cy="17" r="6" fill="#ffbd2e"/>',
        f'<circle cx="60" cy="17" r="6" fill="#27c93f"/>',
        # Title
        f'<text x="{W//2}" y="21" text-anchor="middle" '
        f'font-family="Consolas,Menlo,monospace" font-size="12" fill="{FG}">'
        f'{esc(username)}@github</text>',
    ]

    for ri, line in enumerate(lines):
        y     = PAD_Y + ri * CHAR_H + CHAR_H * 0.82
        begin = ri * STAGGER
        parts.append(
            f'<g opacity="0" transform="translate(0,4)">'
            f'<text x="{PAD_X}" y="{y:.1f}" '
            f'font-family="Consolas,Menlo,monospace" font-size="{FONT_SIZE}" '
            f'fill="{GREEN}">{esc(line)}</text>'
            f'<animate attributeName="opacity" from="0" to="1" '
            f'begin="{begin:.3f}s" dur="{FADE}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="0 4" to="0 0" begin="{begin:.3f}s" dur="{FADE}s" '
            f'fill="freeze" calcMode="spline" keySplines="0.2 0 0.2 1" keyTimes="0;1"/>'
            f'</g>'
        )

    footer_y = int(PAD_Y + n_rows * CHAR_H + 14)
    parts.append(
        f'<text x="{W//2}" y="{footer_y}" text-anchor="middle" '
        f'font-family="Consolas,Menlo,monospace" font-size="11" fill="{BLUE}">'
        f'{esc(username)}</text>'
    )
    parts.append('</svg>')
    return "\n".join(parts)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/photo_to_ascii_svg.py <photo_path> [github_username]")
        sys.exit(1)

    photo_path = Path(sys.argv[1])
    if not photo_path.exists():
        # Also check repo root
        alt = Path(__file__).resolve().parent.parent / photo_path.name
        if alt.exists():
            photo_path = alt
        else:
            print(f"ERROR: Photo not found: {photo_path}")
            sys.exit(1)

    username = sys.argv[2] if len(sys.argv) > 2 else "divyal-11"
    out_path = Path(__file__).resolve().parent.parent / "avi-ascii.svg"

    print(f"Loading {photo_path} ...")
    img   = load_and_prepare(photo_path)
    print(f"Cropped to {img.size[0]}×{img.size[1]} px, converting to {COLS}×{ROWS} ASCII ...")
    lines = image_to_ascii_lines(img)
    svg   = build_svg(lines, username)
    out_path.write_text(svg, encoding="utf-8")
    print(f"Done -> {out_path}  ({len(lines)} rows x {COLS} cols, {len(svg):,} bytes)")
