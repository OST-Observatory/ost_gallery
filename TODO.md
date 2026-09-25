# TODO

## Data protection

- [x] **Animated GIF/WebP keep their metadata** — done (2026-09): `gallery/metadata.py` removes
  comment/XMP/EXIF blocks losslessly when animated files are copied; files that cannot be parsed
  are skipped instead of published. Tests: `make test`.
- [x] **Photographer names are published** — no change needed: every photographer has consented to
  publication of the image under its license together with the name. Documented in
  `docs/DATA_FORMAT.md` (*Photographer names and consent*) and in the central privacy policy
  (`#gallery`, legal basis consent).
