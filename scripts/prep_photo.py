"""
prep_photo.py

Turns a normal photo into a clean, high-contrast grayscale image that
converts well to ASCII art:
  1. Removes the background (rembg) so only the subject remains.
  2. Boosts local contrast (OpenCV CLAHE) so a flatly-lit face still
     gets real highlights/shadows.
  3. Composites onto pure white, so background maps to the blank end
     of the ASCII ramp (white -> space character).

Usage:
    python prep_photo.py source-photo.jpg
    # writes: source-prepped.png
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove


def prep_photo(input_path: str, output_path: str | None = None) -> str:
    input_path = Path(input_path)
    if output_path is None:
        output_path = input_path.with_name(input_path.stem + "-prepped.png")

    # 1. Remove background -> RGBA with subject isolated
    with open(input_path, "rb") as f:
        raw = f.read()
    cutout_bytes = remove(raw)

    cutout = Image.open(__import__("io").BytesIO(cutout_bytes)).convert("RGBA")

    # 2. Composite onto pure white background
    white_bg = Image.new("RGBA", cutout.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, cutout).convert("L")

    # 3. CLAHE contrast boost (needs OpenCV / numpy arrays)
    gray = np.array(composited)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    contrasted = clahe.apply(gray)

    # Re-flatten near-white background that CLAHE may have nudged off-white,
    # so it still maps cleanly to the blank end of the ASCII ramp.
    _, mask = cv2.threshold(contrasted, 245, 255, cv2.THRESH_BINARY)
    contrasted = np.where(mask == 255, 255, contrasted).astype("uint8")

    Image.fromarray(contrasted).save(output_path)
    print(f"Wrote {output_path}")
    return str(output_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python prep_photo.py <source-photo.jpg>")
        sys.exit(1)
    prep_photo(sys.argv[1])
