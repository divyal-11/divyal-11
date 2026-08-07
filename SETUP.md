# Setup

## 0. Create the magic repo (once)
Your GitHub username, exactly, as a public repo:

    gh repo create YOUR_GITHUB_USERNAME --public --clone
    cd YOUR_GITHUB_USERNAME
    # copy scripts/, .github/, README.md, SETUP.md from this bundle in here

## 1. Install deps
    python -m venv .venv && source .venv/bin/activate
    pip install -r scripts/requirements.txt

## 2. Edit the info card content
Open `scripts/make_info_card.py` and edit the `CONFIG` dict at the top
(already pre-filled with placeholder text based on your stack — swap in
your real "Now" / "Prev" line and username).

## 3. Generate the ASCII portrait (run once, or whenever your photo changes)
    python scripts/prep_photo.py your-photo.jpg
    python scripts/make_ascii_svg.py your-photo-prepped.png --out avi-ascii.svg

## 4. Generate the info card
    python scripts/make_info_card.py
    # writes info-card.svg

## 5. Generate the live heatmap
    python scripts/fetch_contributions.py YOUR_GITHUB_USERNAME
    python scripts/render_heatmap_svg.py
    # writes contrib-heatmap.svg

## 6. Wire up the workflow
In `.github/workflows/update-profile-art.yml`, replace
`YOUR_GITHUB_USERNAME` with your real username.

## 7. Commit + push
    git add .
    git commit -m "profile art: ascii portrait + info card + live heatmap"
    git push

Then trigger the workflow once by hand (Actions tab → Update profile art →
Run workflow) to confirm it commits a fresh heatmap SVG.

## Notes
- GitHub strips `<style>` blocks and most inline CSS from READMEs, but
  renders SVGs embedded via `<img>` and plays their SMIL/CSS animation —
  that's why all the motion lives *inside* each SVG file, not the README.
- The only vertical spacing GitHub honors in the README is `<br>` — inline
  `style="margin-top:..."` is stripped.
- `<h1>`/`<h2>` draw a full-width underline; use `<h3>` to avoid that.
- Keep the heatmap width (860) equal to the two-column widths (370 + 490)
  so the edges line up.
