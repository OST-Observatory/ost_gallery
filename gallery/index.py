from __future__ import annotations

import json
import shutil
import warnings
from pathlib import Path

from PIL import Image
from PIL.Image import DecompressionBombWarning

from gallery.categories import class_to_category
from gallery.config import Config, IMAGE_EXTENSIONS
from gallery.errors import BuildLog
from gallery.parse_txt import parse_objects_md, parse_txt_file
from gallery.license import image_license_fields, resolve_license_key, site_license
from gallery.paths import public_url
from gallery.slug import make_slug

REQUIRED_FIELDS = ("OBJECT", "DATE", "CLASS")


def _save_webp(img: Image.Image, dest: Path, max_width: int | None = None) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    working = img.convert("RGB") if img.mode in ("RGBA", "P", "LA") else img
    if max_width and working.width > max_width:
        ratio = max_width / working.width
        new_size = (max_width, max(int(working.height * ratio), 1))
        working = working.resize(new_size, Image.Resampling.LANCZOS)
    working.save(dest, "WEBP", quality=85, method=6)


def _copy_original(
    image_path: Path,
    output_base: Path,
    rel_folder: str,
    base_path: str,
) -> str:
    stem = image_path.stem
    suffix = image_path.suffix.lower()
    dest = output_base / "media" / "original" / rel_folder / f"{stem}{suffix}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(image_path, dest)
    return public_url(base_path, f"/media/original/{rel_folder}/{stem}{suffix}")


def _log_image_warnings(caught: list[warnings.WarningMessage], label: str, log: BuildLog) -> None:
    for recorded in caught:
        if issubclass(recorded.category, DecompressionBombWarning):
            log.warning(label, f"Decompression bomb warning: {recorded.message}")


def _process_image(
    image_path: Path,
    output_base: Path,
    rel_folder: str,
    config: Config,
    log: BuildLog,
) -> tuple[str, str, str] | None:
    stem = image_path.stem
    label = f"{rel_folder}/{image_path.name}"
    thumb_rel = public_url(config.base_path, f"/media/thumbs/{rel_folder}/{stem}.webp")
    display_rel = public_url(config.base_path, f"/media/display/{rel_folder}/{stem}.webp")
    thumb_dest = output_base / "media" / "thumbs" / rel_folder / f"{stem}.webp"
    display_dest = output_base / "media" / "display" / rel_folder / f"{stem}.webp"

    try:
        full_rel = _copy_original(image_path, output_base, rel_folder, config.base_path)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DecompressionBombWarning)
            with Image.open(image_path) as img:
                img.load()
                _log_image_warnings(caught, label, log)
                _save_webp(img, thumb_dest, config.thumb_max_width)
                if config.display_max_width == 0:
                    display_dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(image_path, display_dest.with_suffix(image_path.suffix))
                    display_rel = public_url(
                        config.base_path,
                        f"/media/display/{rel_folder}/{stem}{image_path.suffix.lower()}",
                    )
                else:
                    _save_webp(img, display_dest, config.display_max_width)
    except OSError as exc:
        log.skip(label, f"Image processing failed: {exc}")
        return None

    return thumb_rel, display_rel, full_rel


def _collect_pairs(data_dir: Path, log: BuildLog) -> list[tuple[Path, Path, str]]:
    """Return list of (image_path, txt_path, rel_folder_id)."""
    pairs: list[tuple[Path, Path, str]] = []
    seen_txt: set[Path] = set()

    if not data_dir.is_dir():
        log.fatal(str(data_dir), "DATA_DIR does not exist or is not a directory")
        return pairs

    for date_dir in sorted(data_dir.iterdir()):
        if not date_dir.is_dir():
            continue

        rel_folder = date_dir.name
        images_by_stem: dict[str, Path] = {}
        txts_by_stem: dict[str, Path] = {}

        for item in date_dir.iterdir():
            if not item.is_file():
                continue
            stem = item.stem
            suffix = item.suffix.lower()
            if suffix in IMAGE_EXTENSIONS:
                images_by_stem[stem] = item
            elif suffix == ".txt" and not item.name.endswith(".objects.md"):
                txts_by_stem[stem] = item

        all_stems = set(images_by_stem) | set(txts_by_stem)
        for stem in sorted(all_stems):
            image_path = images_by_stem.get(stem)
            txt_path = txts_by_stem.get(stem)
            label = f"{date_dir.name}/{stem}"

            if image_path and txt_path:
                pairs.append((image_path, txt_path, rel_folder))
                seen_txt.add(txt_path)
            elif image_path:
                log.skip(label, "Image has no matching .txt metadata file")
            elif txt_path:
                log.skip(label, ".txt metadata has no matching image file")

    return pairs


def run_index(config: Config, log: BuildLog | None = None) -> dict:
    log = log or BuildLog(log_file=config.log_file)

    if not config.data_dir.is_dir():
        log.fatal(str(config.data_dir), "DATA_DIR does not exist or is not readable")
        return {"images": [], "featured": [], "meta": {}}

    try:
        config.build_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        log.fatal(str(config.build_dir), f"Cannot create build directory: {exc}")
        return {"images": [], "featured": [], "meta": {}}

    pairs = _collect_pairs(config.data_dir, log)
    if log.has_fatal:
        return {"images": [], "featured": [], "meta": {}}

    entries: list[dict] = []
    seen_slugs: dict[str, str] = {}

    for image_path, txt_path, rel_folder in pairs:
        label = f"{rel_folder}/{image_path.stem}"
        parsed = parse_txt_file(txt_path, log)
        if parsed is None:
            continue

        missing = [f for f in REQUIRED_FIELDS if f not in parsed.fields]
        if missing:
            log.skip(label, f"Missing required fields: {', '.join(missing)}")
            continue

        date_value = parsed.fields["DATE"]
        if date_value != rel_folder:
            log.warning(label, f"DATE {date_value!r} differs from folder name {rel_folder!r}")

        slug = make_slug(image_path.name, date_value)
        if slug in seen_slugs:
            log.skip(label, f"Duplicate slug {slug!r} (already used by {seen_slugs[slug]})")
            continue

        rel_id = f"{rel_folder}/{image_path.stem}"
        license_raw = parsed.fields.get("LICENSE", "")
        if license_raw.strip() and not resolve_license_key(license_raw):
            log.warning(label, f"Unknown LICENSE value {license_raw!r}; ignored on detail page")

        media = _process_image(image_path, config.build_dir, rel_folder, config, log)
        if media is None:
            continue

        thumb_src, image_src, full_src = media
        category = class_to_category(parsed.fields["CLASS"])

        objects_md_path = txt_path.with_suffix(".objects.md")
        objects_from_md = parse_objects_md(objects_md_path, log)
        objects = [
            {"name": o.name, "description": o.description}
            for o in (parsed.objects + objects_from_md)
        ]

        license_fields = image_license_fields(
            parsed.fields.get("CREDIT", ""),
            license_raw,
            site_license(config),
        )
        if license_fields["license"] and license_fields["license"].get("badge_src"):
            license_fields["license"]["badge_src"] = public_url(
                config.base_path,
                license_fields["license"]["badge_src"],
            )

        entry = {
            "id": rel_id,
            "slug": slug,
            "object": parsed.fields["OBJECT"],
            "date": date_value,
            "catalog": parsed.fields.get("CAT", ""),
            "filters": parsed.fields.get("FILTER", ""),
            "category": category,
            "extra": parsed.fields.get("EXTRA", ""),
            "takenBy": parsed.fields.get("TAKEN", ""),
            "credit": license_fields["credit"],
            "license": license_fields["license"],
            "imageSrc": image_src,
            "fullSrc": full_src,
            "thumbSrc": thumb_src,
            "objects": objects,
        }
        entries.append(entry)
        seen_slugs[slug] = label
        log.record_indexed()

    entries.sort(key=lambda e: (e["date"].replace(".", ""), e["object"].lower()), reverse=True)
    featured = entries[: config.featured_count]

    manifest = {
        "meta": {
            "siteTitle": config.site_title,
            "siteUrl": config.site_url,
            "featuredCount": config.featured_count,
            "slideIntervalMs": config.slide_interval_ms,
            "totalImages": len(entries),
        },
        "featured": featured,
        "images": entries,
    }

    config.gallery_json_path.parent.mkdir(parents=True, exist_ok=True)
    with config.gallery_json_path.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)

    log.print_summary()
    return manifest
