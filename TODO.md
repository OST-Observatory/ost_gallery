# TODO

## Data protection

- **Animated GIF/WebP keep their metadata.** Still images are re-encoded by
  Pillow and lose EXIF/XMP, but animated media are copied byte-for-byte
  (`_copy_validated` → `shutil.copy2` in `gallery/index.py`, ~117-123 and
  ~192-197). Comments, XMP or EXIF blocks (camera, software, possibly GPS or
  author) end up in `dist/media/`. Strip metadata on copy, e.g.
  `exiftool -all= -overwrite_original` on the copied files, or re-encode the
  frames with Pillow without `exif`/`xmp`/`comment`.
- **Photographer names are published.** The `TAKEN` field is shown on every
  detail page ("Taken by"). Prefer first names only (or ask for consent to the
  full name) and mention this in `docs/DATA_FORMAT.md`.
