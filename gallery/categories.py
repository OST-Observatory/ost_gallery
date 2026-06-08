from __future__ import annotations

CLASS_TO_CATEGORY: dict[str, str] = {
    "nebula": "nebulae",
    "nebulae": "nebulae",
    "galaxy": "galaxies",
    "galaxies": "galaxies",
    "cluster": "star-clusters",
    "star_cluster": "star-clusters",
    "star cluster": "star-clusters",
    "open_cluster": "star-clusters",
    "globular": "star-clusters",
    "solar": "solar-system",
    "planet": "solar-system",
    "moon": "solar-system",
    "sun": "solar-system",
    "comet": "solar-system",
}


def class_to_category(class_value: str) -> str:
    normalized = class_value.strip().lower()
    return CLASS_TO_CATEGORY.get(normalized, "miscellaneous")


def category_label(slug: str) -> str:
    labels = {
        "galaxies": "Galaxies",
        "nebulae": "Nebulae",
        "star-clusters": "Star Clusters",
        "solar-system": "Solar System",
        "miscellaneous": "Miscellaneous",
    }
    return labels.get(slug, slug.replace("-", " ").title())
