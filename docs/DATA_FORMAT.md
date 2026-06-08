# Data format

## Directory layout

```
DATA_DIR/
├── 2026.03.05/
│   ├── crab_nebula.png
│   └── crab_nebula.txt
├── 2026.02.14/
│   ├── andromeda.jpg
│   └── andromeda.txt
└── ...
```

Each observation night is a folder named `YYYY.MM.DD`. For every image file there must be a metadata file with the same base name and a `.txt` extension.

Supported image formats: `.png`, `.jpg`, `.jpeg`, `.webp`

## Metadata file (`.txt`)

Lines starting with `#` are comments. Fields use the format `KEY = value` (spaces or tabs around `=` are allowed).

| Key | Required | Description |
|-----|----------|-------------|
| `OBJECT` | yes | Display name of the object |
| `DATE` | yes | Observation date as `YYYY.MM.DD` |
| `CLASS` | yes | Object class (see below) |
| `CAT` | no | Catalogue designation(s), comma-separated |
| `FILTER` | no | Filters used |
| `EXTRA` | no | Additional notes about the capture (exposure, processing, …) |
| `TAKEN` | no | Photographer / observer name |
| `OBJECT_INFO` | no | Object information for the detail page (repeatable, see below) |
| `OBJECTS` | no | Alias for `OBJECT_INFO` (same format) |
| `CREDIT` | no | Per-image credit line (shown on detail page only) |
| `LICENSE` | no | Per-image license override (e.g. `BY-NC-SA-3.0` or a URL) |

### CLASS values

The `CLASS` field is mapped to gallery categories:

| CLASS examples | Gallery category |
|----------------|------------------|
| `nebula`, `nebulae` | Nebulae |
| `galaxy`, `galaxies` | Galaxies |
| `cluster`, `star_cluster` | Star Clusters |
| `solar`, `planet`, `moon` | Solar System |
| anything else | Miscellaneous |

### Object information (`OBJECT_INFO`)

Add one or more lines to describe objects visible in the image. These appear in the **“Objects in this image”** section on the detail page.

**Format A — name and description** (recommended for multiple objects):

```
OBJECT_INFO = M 1 | Supernova remnant in the constellation Taurus
OBJECT_INFO = Barnard 33 | Dark nebula silhouetted against bright emission nebulosity
```

Use a pipe `|` to separate the object name from a short description.

**Format B — description only** (for a single general note):

```
OBJECT_INFO = This field also contains several background galaxies visible as faint smudges.
```

The line may be repeated for several entries. The legacy key `OBJECTS` is accepted as an alias for `OBJECT_INFO`.

### Per-image credit and license

The site-wide default license is configured in `.env` (see README). For exceptions:

```
CREDIT  = Image © Jane Doe
LICENSE = BY-NC-SA-3.0
```

`LICENSE` accepts known keys (`BY-NC-SA-3.0`, `BY-NC-SA-4.0`, `BY-3.0`, `BY-4.0`) or a full license URL. Shown on the detail page only when it differs from the site default or when `CREDIT` is set.

### Example

```
OBJECT	= Crab Nebula
DATE	= 2026.03.05
CAT     = M 1
FILTER	= Halpha, OIII, SII
CLASS	= nebula
EXTRA	= Composite of 60 frames, ~5 hours total exposure.
TAKEN	= Rainer
OBJECT_INFO = M 1 | Supernova remnant in Taurus, remnant of a supernova observed in 1054 CE.
```

## Optional Markdown sidecar (advanced)

As an alternative to `OBJECT_INFO` lines, you may optionally add `name.objects.md` next to the image. The indexer merges both sources. For most use cases, `OBJECT_INFO` in the `.txt` file is sufficient.

## Build behaviour for bad data

If a single image/metadata pair is invalid, the build **logs the problem and continues**. Fix the reported file and rebuild. See the main [README](../README.md) troubleshooting section.
