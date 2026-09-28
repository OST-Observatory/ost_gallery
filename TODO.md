# TODO

## Data protection

- [x] **Animated GIF/WebP keep their metadata** — done (2026-09): `gallery/metadata.py` removes
  comment/XMP/EXIF blocks losslessly when animated files are copied; files that cannot be parsed
  are skipped instead of published. Tests: `make test`.
- [x] **Photographer names are published** — no change needed: every photographer has consented to
  publication of the image under its license together with the name. Documented in
  `docs/DATA_FORMAT.md` (*Photographer names and consent*) and in the central privacy policy
  (`#gallery`, legal basis consent).
- [x] **Build log without rotation** — done (2026-09): production cron hands the build output to the
  journal (`systemd-cat -t ost-gallery-build`, 7 days); `LOG_FILE` stays optional for local use.
