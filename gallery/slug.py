from __future__ import annotations

import re
import unicodedata


def normalize_filename(name: str) -> str:
    stem = name.rsplit(".", 1)[0] if "." in name else name
    normalized = unicodedata.normalize("NFKD", stem)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or "image"


def make_slug(filename: str, date: str) -> str:
    date_part = date.replace(".", "-")
    return f"{normalize_filename(filename)}-{date_part}"
