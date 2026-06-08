from __future__ import annotations

import argparse
import sys

from gallery.build import run_build
from gallery.config import load_config
from gallery.deploy import prepare_build_dir
from gallery.errors import BuildLog
from gallery.index import run_index


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OST Astro Gallery static site generator")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("index", help="Scan DATA_DIR and write gallery.json + media")

    build_parser = sub.add_parser("build", help="Index (unless skipped) and render HTML site")
    build_parser.add_argument(
        "--skip-index",
        action="store_true",
        help="Re-render templates only using existing gallery.json and media in the build dir",
    )

    args = parser.parse_args(argv)
    config = load_config()
    log = BuildLog(log_file=config.log_file)

    if args.command == "index":
        if not prepare_build_dir(config, log):
            return 1
        run_index(config, log)
        return 1 if log.has_fatal else 0

    if args.command == "build":
        if not args.skip_index:
            if not prepare_build_dir(config, log):
                return 1
            run_index(config, log)
            if log.has_fatal:
                return 1
        ok = run_build(config, log)
        return 0 if ok else 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
