from __future__ import annotations

import json
import shutil
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

from gallery.categories import category_label
from gallery.config import CATEGORY_SLUGS, Config
from gallery.errors import BuildLog
from gallery.i18n import STRINGS, t
from gallery.deploy import finalize_build
from gallery.license import site_license


def _load_manifest(config: Config, log: BuildLog) -> dict | None:
    path = config.gallery_json_path
    if not path.is_file():
        log.fatal(str(path), "gallery.json not found — run index first")
        return None
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        log.fatal(str(path), f"Cannot read gallery.json: {exc}")
        return None


def _write_html(env: Environment, template_name: str, dest: Path, log: BuildLog, **ctx) -> bool:
    try:
        html = env.get_template(template_name).render(**ctx)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")
        return True
    except Exception as exc:
        log.fatal(template_name, f"Template render failed: {exc}")
        return False


def _copy_static(config: Config, log: BuildLog) -> bool:
    src = config.static_dir
    dest = config.build_dir / "static"
    if not src.is_dir():
        log.fatal(str(src), "Static assets directory missing")
        return False
    try:
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        return True
    except OSError as exc:
        log.fatal(str(dest), f"Static asset copy failed: {exc}")
        return False


def _nav_items(active: str) -> list[dict]:
    items = [
        {"slug": "", "label": t("nav.all"), "href": "/", "key": "all"},
        {"slug": "galaxies", "label": t("nav.galaxies"), "href": "/galaxies/", "key": "galaxies"},
        {"slug": "nebulae", "label": t("nav.nebulae"), "href": "/nebulae/", "key": "nebulae"},
        {"slug": "star-clusters", "label": t("nav.starClusters"), "href": "/star-clusters/", "key": "star-clusters"},
        {"slug": "solar-system", "label": t("nav.solarSystem"), "href": "/solar-system/", "key": "solar-system"},
        {"slug": "miscellaneous", "label": t("nav.miscellaneous"), "href": "/miscellaneous/", "key": "miscellaneous"},
        {"slug": "about", "label": t("nav.about"), "href": "/about/", "key": "about"},
    ]
    for item in items:
        item["active"] = item["key"] == active
    return items


def _license_context(config: Config) -> dict | None:
    info = site_license(config)
    if info is None:
        return None
    return {
        "short": info.short,
        "name": info.name,
        "url": info.url,
        "badge_src": info.badge_src,
    }


def _base_context(config: Config, manifest: dict, active: str) -> dict:
    meta = manifest.get("meta", {})
    return {
        "site_title": meta.get("siteTitle", config.site_title),
        "site_url": meta.get("siteUrl", config.site_url),
        "site_description": t("meta.siteDescription"),
        "site_license": _license_context(config),
        "nav_items": _nav_items(active),
        "t": t,
        "strings": STRINGS,
        "slide_interval_ms": meta.get("slideIntervalMs", config.slide_interval_ms),
    }


def run_build(config: Config, log: BuildLog | None = None) -> bool:
    log = log or BuildLog(log_file=config.log_file)

    try:
        config.build_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        log.fatal(str(config.build_dir), f"Build directory not writable: {exc}")
        return False

    manifest = _load_manifest(config, log)
    if manifest is None or log.has_fatal:
        return False

    if not _copy_static(config, log):
        return False

    env = Environment(
        loader=FileSystemLoader(config.templates_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.filters["category_label"] = category_label

    images = manifest.get("images", [])
    featured = manifest.get("featured", [])
    base = _base_context(config, manifest, "all")

    if not _write_html(
        env,
        "index.html",
        config.build_dir / "index.html",
        log,
        **base,
        featured=featured,
        images=images,
    ):
        return False

    for slug in CATEGORY_SLUGS:
        filtered = [img for img in images if img.get("category") == slug]
        ctx = _base_context(config, manifest, slug)
        if not _write_html(
            env,
            "category.html",
            config.build_dir / slug / "index.html",
            log,
            **ctx,
            category_slug=slug,
            category_title=category_label(slug),
            images=filtered,
        ):
            return False

    for image in images:
        ctx = _base_context(config, manifest, image.get("category", ""))
        if not _write_html(
            env,
            "detail.html",
            config.build_dir / "image" / image["slug"] / "index.html",
            log,
            **ctx,
            image=image,
            category_title=category_label(image.get("category", "")),
        ):
            return False

    about_path = config.content_dir / "about.md"
    about_html = ""
    if about_path.is_file():
        about_html = markdown.markdown(
            about_path.read_text(encoding="utf-8"),
            extensions=["extra", "sane_lists"],
        )

    if not _write_html(
        env,
        "about.html",
        config.build_dir / "about" / "index.html",
        log,
        **_base_context(config, manifest, "about"),
        about_html=about_html,
    ):
        return False

    if not _write_html(
        env,
        "404.html",
        config.build_dir / "404.html",
        log,
        **_base_context(config, manifest, ""),
    ):
        return False

    if log.has_fatal:
        return False

    print(f"Built {len(images)} detail pages into {config.build_dir}")
    return finalize_build(config, log)
