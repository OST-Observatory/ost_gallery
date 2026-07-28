from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from gallery.config import Config

KNOWN_LICENSES: dict[str, dict[str, str]] = {
    "BY-NC-SA-3.0": {
        "short": "CC BY-NC-SA 3.0",
        "name": "Creative Commons Attribution-NonCommercial-ShareAlike 3.0",
        "url": "https://creativecommons.org/licenses/by-nc-sa/3.0/",
        "badge": "by-nc-sa",
    },
    "BY-NC-SA-4.0": {
        "short": "CC BY-NC-SA 4.0",
        "name": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0",
        "url": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
        "badge": "by-nc-sa",
    },
    "BY-3.0": {
        "short": "CC BY 3.0",
        "name": "Creative Commons Attribution 3.0",
        "url": "https://creativecommons.org/licenses/by/3.0/",
        "badge": "by",
    },
    "BY-4.0": {
        "short": "CC BY 4.0",
        "name": "Creative Commons Attribution 4.0",
        "url": "https://creativecommons.org/licenses/by/4.0/",
        "badge": "by",
    },
}

# Domains allowed when LICENSE is a custom URL (prevents open redirects / phishing links).
LICENSE_URL_ALLOWED_HOSTS = frozenset(
    {
        "creativecommons.org",
        "www.creativecommons.org",
        "opensource.org",
        "www.opensource.org",
        "spdx.org",
        "www.spdx.org",
    }
)


@dataclass(frozen=True)
class LicenseInfo:
    short: str
    name: str
    url: str
    badge_src: str


def _safe_license_url(url: str) -> str | None:
    """Accept only http(s) URLs on an allowlisted host."""
    raw = url.strip()
    try:
        parsed = urlparse(raw)
    except ValueError:
        return None
    if parsed.scheme not in {"http", "https"}:
        return None
    if not parsed.netloc:
        return None
    host = parsed.hostname
    if not host or host.lower() not in LICENSE_URL_ALLOWED_HOSTS:
        return None
    return raw


def resolve_license_key(key: str) -> LicenseInfo | None:
    normalized = key.strip().upper().replace(" ", "")
    if normalized in KNOWN_LICENSES:
        data = KNOWN_LICENSES[normalized]
        return LicenseInfo(
            short=data["short"],
            name=data["name"],
            url=data["url"],
            badge_src=f"/static/img/cc/{data['badge']}.svg",
        )
    safe_url = _safe_license_url(key)
    if safe_url:
        return LicenseInfo(
            short=safe_url,
            name=safe_url,
            url=safe_url,
            badge_src="",
        )
    return None


def site_license(config: Config) -> LicenseInfo | None:
    if not config.site_license_url:
        return None
    return LicenseInfo(
        short=config.site_license_short or config.site_license_name,
        name=config.site_license_name or config.site_license_short,
        url=config.site_license_url,
        badge_src=f"/static/img/cc/{config.site_license_badge}.svg"
        if config.site_license_badge
        else "",
    )


def image_license_fields(
    credit: str,
    license_raw: str,
    default: LicenseInfo | None,
) -> dict:
    """Build optional per-image credit/license display fields."""
    credit = credit.strip()
    license_raw = license_raw.strip()

    license_info = resolve_license_key(license_raw) if license_raw else None

    show_license = bool(license_raw) and bool(license_info)

    return {
        "credit": credit,
        "license": {
            "short": license_info.short,
            "name": license_info.name,
            "url": license_info.url,
            "badge_src": license_info.badge_src,
        }
        if license_info and show_license
        else None,
    }
