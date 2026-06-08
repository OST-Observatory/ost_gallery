# OST Gallery

Static web gallery for astrophotography images captured with observatory telescopes. The site is generated from a folder of images and sidecar metadata files — no database or CMS required.

## Architecture

```
DATA_DIR/          →  python -m gallery index  →  gallery.json + media/
                                              ↓
                         python -m gallery build  →  dist/  →  Apache DocumentRoot
```

1. **Index** — scan `DATA_DIR`, parse `.txt` metadata, generate WebP thumbnails and display images, write `gallery/data/gallery.json`.
2. **Build** — render Jinja2 HTML templates into `OUTPUT_DIR` (default `./dist`).

Invalid individual datasets are **logged and skipped**; the build continues with all valid entries.

## Requirements

- Python 3.11+
- Apache 2.4 (production)
- Linux or macOS recommended

Python dependencies: Pillow, Jinja2, python-dotenv, Markdown (see `requirements.txt`).

## Quick start

```bash
git clone <repository-url> ost_gallery
cd ost_gallery

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env — set DATA_DIR to your image dataset (sample-data/ works for a trial build)

python -m gallery build
cd dist && python -m http.server 8000
# Open http://localhost:8000
```

Or use the Makefile:

```bash
make install
make build
make dev
```

## Configuration

Copy `.env.example` to `.env` and adjust:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATA_DIR` | Path to image dataset | `./sample-data` |
| `OUTPUT_DIR` | Final site output (Apache DocumentRoot) | `./dist` |
| `STAGING_DIR` | Temporary build directory (default: `{OUTPUT_DIR}.staging`) | — |
| `ATOMIC_BUILD` | Build to staging, then atomically replace `OUTPUT_DIR` (`1`/`0`) | `1` |
| `DEPLOY_USER` | Optional owner after build (e.g. `deploy`) | — |
| `DEPLOY_GROUP` | Optional group after build (e.g. `www-data`) | — |
| `DEPLOY_DIR_MODE` | Directory mode (octal) | `755` |
| `DEPLOY_FILE_MODE` | File mode (octal) | `644` |
| `FEATURED_COUNT` | Recent images in home hero slideshow | `5` |
| `SLIDE_INTERVAL_MS` | Slideshow interval (ms) | `6000` |
| `THUMB_MAX_WIDTH` | Thumbnail width (px) | `600` |
| `DISPLAY_MAX_WIDTH` | Detail image max width; `0` = copy original | `2400` |
| `BASE_PATH` | URL prefix when not at site root (e.g. `/gallery`) | *(empty)* |
| `SITE_URL` | Canonical site URL (optional); include `BASE_PATH` if set | — |
| `SITE_TITLE` | Site title in header | `OST Gallery` |
| `SITE_LICENSE_SHORT` | Short license label (e.g. CC BY-NC-SA 3.0) | `CC BY-NC-SA 3.0` |
| `SITE_LICENSE_NAME` | Full license name in footer | Creative Commons … 3.0 License |
| `SITE_LICENSE_URL` | License URL (footer link) | `https://creativecommons.org/licenses/by-nc-sa/3.0/` |
| `SITE_LICENSE_BADGE` | Badge filename in `static/img/cc/` | `by-nc-sa` |
| `LOG_FILE` | Optional append-only build log path | — |

## Data format

See [docs/DATA_FORMAT.md](docs/DATA_FORMAT.md) for the full specification.

Briefly: each date folder `YYYY.MM.DD` contains paired image and metadata files (`name.png` + `name.txt`, or `.jpg`, `.gif`, …). Required metadata keys: `OBJECT`, `DATE`, `CLASS`.

Optional repeated `OBJECT_INFO = Name | description` lines in each `.txt` file populate the **“Objects in this image”** section on detail pages. See [docs/DATA_FORMAT.md](docs/DATA_FORMAT.md) for formats (including description-only lines). The key `OBJECTS` is accepted as an alias.

## CLI

```bash
python -m gallery index          # scan only
python -m gallery build          # index + render HTML
python -m gallery build --skip-index   # re-render templates only
```

Exit codes:

- `0` — completed (skipped entries are allowed)
- `1` — fatal error (missing `DATA_DIR`, unwritable output, template failure, …)

After each index run a summary is printed, e.g.:

```
Indexed 47 images, skipped 2, warnings 1
```

## Adding new images

1. Create or use a date folder under `DATA_DIR`, e.g. `2026.06.03/`.
2. Add `object_name.png` (or `.jpg`, `.gif`, …) and `object_name.txt`.
3. Run `python -m gallery build`.
4. Deploy `OUTPUT_DIR` to your web server (see below).

## Apache 2 deployment

Typical server layout:

| Path | Purpose |
|------|---------|
| `/opt/ost_gallery` | Git checkout, venv, `.env` |
| `/var/gallery/data` | `DATA_DIR` (existing dataset) |
| `/var/www/ost-gallery` | Published `DocumentRoot` |

### 1. Install and configure

```bash
cd /opt/ost_gallery
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set in `.env`:

```
DATA_DIR=/var/gallery/data
OUTPUT_DIR=/var/www/ost-gallery
BASE_PATH=
SITE_URL=https://gallery.example.org
LOG_FILE=/var/log/ost-gallery-build.log
```

For a subpath install (e.g. `https://www.myserver.com/gallery`), set `BASE_PATH=/gallery` and `SITE_URL=https://www.myserver.com/gallery`. After changing `BASE_PATH`, run a full build (not `--skip-index`) so media URLs in `gallery.json` are updated.

### 2. Build and deploy

With `ATOMIC_BUILD=1` (default), the gallery is built into a fresh staging directory and only replaces the live site when the build succeeds:

```bash
source /opt/ost_gallery/.venv/bin/activate
cd /opt/ost_gallery
python -m gallery build
```

Set `OUTPUT_DIR` to your Apache `DocumentRoot` (e.g. `/var/www/ost-gallery`). The build writes to `OUTPUT_DIR.staging`, applies permissions, then atomically swaps staging → `OUTPUT_DIR`. The previous site is removed; no manual `rsync --delete` is required.

For local development you can set `OUTPUT_DIR=./dist` and `ATOMIC_BUILD=1` in `.env`.

### 3. Apache virtual host

```apache
<VirtualHost *:443>
    ServerName gallery.example.org
    DocumentRoot /var/www/ost-gallery

    <IfModule mod_headers.c>
        Header always set X-Content-Type-Options "nosniff"
        Header always set X-Frame-Options "SAMEORIGIN"
        Header always set Referrer-Policy "strict-origin-when-cross-origin"
    </IfModule>

    <Directory /var/www/ost-gallery>
        Options -Indexes
        AllowOverride None
        Require all granted
        DirectoryIndex index.html
    </Directory>

    <Directory /var/www/ost-gallery/media>
        Require all granted
        <IfModule mod_expires.c>
            ExpiresActive On
            ExpiresDefault "access plus 30 days"
        </IfModule>
    </Directory>

    ErrorDocument 404 /404.html

    # SSL configured separately, e.g. certbot --apache
</VirtualHost>
```

Directory-style URLs (`/nebulae/`, `/image/crab-nebula-2026-03-05/`) work without `mod_rewrite` because each route is a folder containing `index.html`.

#### Subpath on an existing site (e.g. `/gallery`)

When the gallery lives under a path on a larger site, Apache serves the built files via `Alias` instead of `DocumentRoot`:

```apache
<VirtualHost *:443>
    ServerName www.meinserver.com
    DocumentRoot /var/www/meinserver

    # … main site config …

    Alias /gallery /var/www/ost-gallery

    # Default 404 for the main site (DocumentRoot)
    ErrorDocument 404 /404.html

    <Directory /var/www/ost-gallery>
        Options -Indexes
        AllowOverride None
        Require all granted
        DirectoryIndex index.html
        # 404 only for URLs under /gallery (overrides VirtualHost default here)
        ErrorDocument 404 /gallery/404.html
    </Directory>

    <Directory /var/www/ost-gallery/media>
        Require all granted
        <IfModule mod_expires.c>
            ExpiresActive On
            ExpiresDefault "access plus 30 days"
        </IfModule>
    </Directory>
</VirtualHost>
```

`.env` for this layout:

```
OUTPUT_DIR=/var/www/ost-gallery
BASE_PATH=/gallery
SITE_URL=https://www.meinserver.com/gallery
```

All internal links and asset URLs are prefixed with `BASE_PATH` at build time (`/gallery/static/…`, `/gallery/media/…`). No `mod_rewrite` is required.

### 4. Permissions

- Build user: read `DATA_DIR`, write parent of `OUTPUT_DIR` (for atomic rename)
- `www-data`: read-only on `/var/www/ost-gallery`

Set in `.env` to apply ownership and modes automatically after each successful build:

```
DEPLOY_USER=deploy
DEPLOY_GROUP=www-data
DEPLOY_DIR_MODE=755
DEPLOY_FILE_MODE=644
```

`chown` requires appropriate privileges (often via `sudo` for the build cron job, or membership in `www-data` with group-writable docroot).

### 5. Automated rebuild (cron)

```cron
30 6 * * * deploy cd /opt/ost_gallery && .venv/bin/python -m gallery build >> /var/log/ost-gallery-build.log 2>&1
```

One command rebuilds from scratch, deploys atomically, and applies permissions.

HTTPS: use [Certbot](https://certbot.eff.org/) with the Apache plugin after the vhost is in place.

## Site structure

| URL | Content |
|-----|---------|
| `/` | Hero slideshow (latest N images) + full grid |
| `/galaxies/` | Galaxies category |
| `/nebulae/` | Nebulae |
| `/star-clusters/` | Star clusters |
| `/solar-system/` | Solar system |
| `/miscellaneous/` | Miscellaneous |
| `/about/` | About page (from `content/about.md`) |
| `/image/{slug}/` | Image detail page |

## Troubleshooting

### Skipped images in build log

Check stderr or `LOG_FILE` for lines like:

```
2026-06-05T07:00:00Z [ERROR] 2026.03.05/missing_meta: Image has no matching .txt metadata file
```

Common fixes:

- Ensure every image has a same-named `.txt` file
- Include `OBJECT`, `DATE`, and `CLASS` in each `.txt`
- Verify image file is not corrupt (open locally)
- Resolve duplicate slugs (same filename on the same date)

### Pillow / WebP errors

Install system libraries if WebP encoding fails, then reinstall Pillow:

```bash
# Debian/Ubuntu
sudo apt install libwebp-dev
pip install --force-reinstall pillow
```

### Apache 403 Forbidden

- Check `DocumentRoot` path and `Require all granted`
- Verify `www-data` can read files under the docroot

### Apache 404 for category or detail pages

- Ensure `DirectoryIndex index.html` is set
- Confirm the build produced `dist/<category>/index.html` and `dist/image/<slug>/index.html`

### Empty hero slideshow

- Increase `FEATURED_COUNT` or add more recent dated images to `DATA_DIR`

### CSS/JS/images 404 under a subpath

- Set `BASE_PATH` in `.env` to match the Apache `Alias` (e.g. `/gallery`)
- Set `SITE_URL` to the full public URL including the path
- Re-run `python -m gallery build` (full index + build) after changing `BASE_PATH`

## Development

- Templates: `gallery/templates/`
- Styles / scripts: `static/`
- About text: `content/about.md`
- Sample dataset: `sample-data/` (for local testing)

Edit templates or CSS, then:

```bash
python -m gallery build --skip-index   # fast re-render
```

## License

GNU General Public License v3.0 — see [LICENSE](LICENSE).
