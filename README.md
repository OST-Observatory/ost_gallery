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

- Python 3.11+Objects
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


| Variable            | Description                                 | Default         |
| ------------------- | ------------------------------------------- | --------------- |
| `DATA_DIR`          | Path to image dataset                       | `./sample-data` |
| `OUTPUT_DIR`        | Built site output directory                 | `./dist`        |
| `FEATURED_COUNT`    | Recent images in home hero slideshow        | `5`             |
| `SLIDE_INTERVAL_MS` | Slideshow interval (ms)                     | `6000`          |
| `THUMB_MAX_WIDTH`   | Thumbnail width (px)                        | `600`           |
| `DISPLAY_MAX_WIDTH` | Detail image max width; `0` = full size WebP | `2400`         |
| `MAX_IMAGE_PIXELS`  | Skip images above this width×height count   | `200000000`      |
| `MAX_IMAGE_BYTES`   | Optional max file size before open; `0` = off | `0`           |
| `SITE_URL`          | Canonical site URL (optional)               | —               |
| `SITE_TITLE`        | Site title in header                        | `OST Gallery`   |
| `LOG_FILE`          | Optional append-only build log path         | —               |


## Data format

See [docs/DATA_FORMAT.md](docs/DATA_FORMAT.md) for the full specification.

Briefly: each date folder `YYYY.MM.DD` contains paired `name.png` (or `.jpg`) and `name.txt` files. Required metadata keys: `OBJECT`, `DATE`, `CLASS`.

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
2. Add `object_name.png` and `object_name.txt`.
3. Run `python -m gallery build`.
4. Deploy `OUTPUT_DIR` to your web server (see below).

## Apache 2 deployment

Typical server layout:


| Path                   | Purpose                       |
| ---------------------- | ----------------------------- |
| `/opt/ost_gallery`     | Git checkout, venv, `.env`    |
| `/var/gallery/data`    | `DATA_DIR` (existing dataset) |
| `/var/www/ost-gallery` | Published `DocumentRoot`      |


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
LOG_FILE=/var/log/ost-gallery-build.log
```

### 2. Build

```bash
source /opt/ost_gallery/.venv/bin/activate
cd /opt/ost_gallery
python -m gallery build
```

If you build into a staging directory first, sync to the docroot:

```bash
rsync -a --delete /opt/ost_gallery/dist/ /var/www/ost-gallery/
```

### 3. Apache virtual host

```apache
<VirtualHost *:443>
    ServerName gallery.example.org
    DocumentRoot /var/www/ost-gallery

    # Requires: a2enmod headers
    Header always set X-Content-Type-Options "nosniff"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
    Header always set X-Frame-Options "DENY"
    Header always set Strict-Transport-Security "max-age=63072000; includeSubDomains"
    Header always set Content-Security-Policy "default-src 'self'; img-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"

    <Directory /var/www/ost-gallery>
        Options -Indexes +SymLinksIfOwnerMatch
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

### 4. Permissions

- Build user: read `DATA_DIR`, write `OUTPUT_DIR`
- `www-data`: read-only on `/var/www/ost-gallery`

```bash
chown -R deploy:www-data /var/www/ost-gallery
chmod -R u=rwX,g=rX,o=rX /var/www/ost-gallery
```

### 5. Automated rebuild (cron)

```cron
30 6 * * * deploy cd /opt/ost_gallery && .venv/bin/python -m gallery build >> /var/log/ost-gallery-build.log 2>&1
```

HTTPS: use [Certbot](https://certbot.eff.org/) with the Apache plugin after the vhost is in place.

## Site structure


| URL               | Content                                      |
| ----------------- | -------------------------------------------- |
| `/`               | Hero slideshow (latest N images) + full grid |
| `/galaxies/`      | Galaxies category                            |
| `/nebulae/`       | Nebulae                                      |
| `/star-clusters/` | Star clusters                                |
| `/solar-system/`  | Solar system                                 |
| `/miscellaneous/` | Miscellaneous                                |
| `/about/`         | About page (from `content/about.md`)         |
| `/image/{slug}/`  | Image detail page                            |


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

## Development

- Templates: `gallery/templates/`
- Styles / scripts: `static/`
- About text: `content/about.md`
- Sample dataset: `sample-data/` (for local testing)

Edit templates or CSS, then:

```bash
python -m gallery build --skip-index   # fast re-render
```

### Dependencies and security updates

Pin or raise lower bounds in `requirements.txt` when installing. After changing dependencies, regenerate a lockfile if you use one (`pip-compile`, `uv lock`, …) and run:

```bash
pip install -r requirements.txt
pip-audit
```

Treat `DATA_DIR` as untrusted input (especially when synced from cloud storage): the indexer rejects symlinks, re-encodes published images, and sanitizes Markdown HTML on the about page.
## License

GNU General Public License v3.0 — see [LICENSE](LICENSE).