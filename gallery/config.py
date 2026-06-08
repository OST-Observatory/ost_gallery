from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from gallery.paths import normalize_base_path

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

CATEGORY_SLUGS = [
    "galaxies",
    "nebulae",
    "star-clusters",
    "solar-system",
    "miscellaneous",
]


def _env_int(name: str, default: int, *, minimum: int = 0) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        print(
            f"WARNING: invalid {name}={raw!r}, using default {default}",
            file=sys.stderr,
        )
        return default
    if value < minimum:
        print(
            f"WARNING: {name}={value} is below minimum {minimum}, using default {default}",
            file=sys.stderr,
        )
        return default
    return value


def _env_octal(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw, 8)
    except ValueError:
        print(
            f"WARNING: invalid octal {name}={raw!r}, using default {octal(default)[2:]}",
            file=sys.stderr,
        )
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    print(f"WARNING: invalid {name}={raw!r}, using default {default}", file=sys.stderr)
    return default


@dataclass(frozen=True)
class Config:
    data_dir: Path
    output_dir: Path
    staging_dir: Path
    atomic_build: bool
    featured_count: int
    slide_interval_ms: int
    thumb_max_width: int
    display_max_width: int
    base_path: str
    site_url: str
    site_title: str
    site_license_short: str
    site_license_name: str
    site_license_url: str
    site_license_badge: str
    deploy_user: str | None
    deploy_group: str | None
    deploy_dir_mode: int
    deploy_file_mode: int
    log_file: Path | None

    @property
    def build_dir(self) -> Path:
        return self.staging_dir if self.atomic_build else self.output_dir

    @property
    def gallery_json_path(self) -> Path:
        return Path(__file__).resolve().parent / "data" / "gallery.json"

    @property
    def templates_dir(self) -> Path:
        return Path(__file__).resolve().parent / "templates"

    @property
    def static_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent / "static"

    @property
    def content_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent / "content"


def load_config(env_file: Path | None = None) -> Config:
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

    data_dir = Path(os.environ.get("DATA_DIR", "./sample-data")).resolve()
    output_dir = Path(os.environ.get("OUTPUT_DIR", "./dist")).resolve()
    staging_raw = os.environ.get("STAGING_DIR", "").strip()
    staging_dir = Path(staging_raw).resolve() if staging_raw else output_dir.parent / f"{output_dir.name}.staging"
    log_file_raw = os.environ.get("LOG_FILE", "").strip()
    deploy_user = os.environ.get("DEPLOY_USER", "").strip() or None
    deploy_group = os.environ.get("DEPLOY_GROUP", "").strip() or None

    return Config(
        data_dir=data_dir,
        output_dir=output_dir,
        staging_dir=staging_dir,
        atomic_build=_env_bool("ATOMIC_BUILD", True),
        featured_count=_env_int("FEATURED_COUNT", 5, minimum=1),
        slide_interval_ms=_env_int("SLIDE_INTERVAL_MS", 6000, minimum=1000),
        thumb_max_width=_env_int("THUMB_MAX_WIDTH", 600, minimum=1),
        display_max_width=_env_int("DISPLAY_MAX_WIDTH", 2400, minimum=0),
        base_path=normalize_base_path(os.environ.get("BASE_PATH", "")),
        site_url=os.environ.get("SITE_URL", "").rstrip("/"),
        site_title=os.environ.get("SITE_TITLE", "OST Gallery"),
        site_license_short=os.environ.get("SITE_LICENSE_SHORT", "CC BY-NC-SA 3.0"),
        site_license_name=os.environ.get(
            "SITE_LICENSE_NAME",
            "Creative Commons Attribution-NonCommercial-ShareAlike 3.0",
        ),
        site_license_url=os.environ.get(
            "SITE_LICENSE_URL",
            "https://creativecommons.org/licenses/by-nc-sa/3.0/",
        ),
        site_license_badge=os.environ.get("SITE_LICENSE_BADGE", "by-nc-sa"),
        deploy_user=deploy_user,
        deploy_group=deploy_group,
        deploy_dir_mode=_env_octal("DEPLOY_DIR_MODE", 0o755),
        deploy_file_mode=_env_octal("DEPLOY_FILE_MODE", 0o644),
        log_file=Path(log_file_raw).resolve() if log_file_raw else None,
    )
