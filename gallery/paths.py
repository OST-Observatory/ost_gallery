from __future__ import annotations


def normalize_base_path(value: str) -> str:
    """Return '' or a path like '/gallery' without trailing slash."""
    value = value.strip()
    if not value or value == "/":
        return ""
    if not value.startswith("/"):
        value = f"/{value}"
    return value.rstrip("/")


def public_url(base_path: str, path: str) -> str:
    """Prefix an absolute site path with the configured base path."""
    if not path.startswith("/"):
        path = f"/{path}"
    if not base_path:
        return path
    return f"{base_path}{path}"
