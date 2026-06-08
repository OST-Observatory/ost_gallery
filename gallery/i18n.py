"""English UI strings for templates."""

STRINGS = {
    "nav.all": "All",
    "nav.galaxies": "Galaxies",
    "nav.nebulae": "Nebulae",
    "nav.starClusters": "Star Clusters",
    "nav.solarSystem": "Solar System",
    "nav.miscellaneous": "Miscellaneous",
    "nav.about": "About",
    "detail.date": "Date",
    "detail.viewFull": "View full resolution image",
    "detail.closeLightbox": "Close full resolution view",
    "detail.catalog": "Catalog",
    "detail.filters": "Filters",
    "detail.takenBy": "Taken by",
    "detail.credit": "Credit",
    "detail.license": "License",
    "detail.extraHeading": "Additional information",
    "detail.objectsHeading": "",
    "detail.back": "Back to gallery",
    "detail.backCategory": "Back to",
    "hero.viewDetails": "View details",
    "grid.empty": "No images in this category yet.",
    "meta.siteDescription": "Deep-sky and solar system images captured with our observatory telescopes.",
    "footer.tagline": "",
    "footer.licensePrefix": "Content on this site is licensed under a",
}


def t(key: str) -> str:
    return STRINGS.get(key, key)
