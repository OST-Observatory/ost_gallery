from __future__ import annotations

from dataclasses import dataclass

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


@dataclass(frozen=True)
class LicenseInfo:
    short: str
    name: str
    url: str
    badge_src: str


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
    if key.strip().lower().startswith("http"):
        return LicenseInfo(
            short=key.strip(),
            name=key.strip(),
            url=key.strip(),
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
    if license_raw and license_info is None and license_raw.lower().startswith("http"):
        license_info = LicenseInfo(
            short=license_raw,
            name=license_raw,
            url=license_raw,
            badge_src="",
        )

    show_license = bool(license_raw.strip()) and bool(license_info)

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
