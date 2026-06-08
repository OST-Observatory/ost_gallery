from __future__ import annotations

import grp
import os
import pwd
import shutil
from pathlib import Path

from gallery.config import Config
from gallery.errors import BuildLog


def _resolve_owner(config: Config) -> tuple[int | None, int | None]:
    uid: int | None = None
    gid: int | None = None

    if config.deploy_user:
        try:
            uid = pwd.getpwnam(config.deploy_user).pw_uid
        except KeyError:
            pass

    if config.deploy_group:
        try:
            gid = grp.getgrnam(config.deploy_group).gr_gid
        except KeyError:
            pass

    return uid, gid


def apply_permissions(config: Config, root: Path, log: BuildLog) -> None:
    """Apply directory/file modes and optional ownership under root."""
    uid, gid = _resolve_owner(config)

    if config.deploy_user and uid is None:
        log.warning(str(root), f"Unknown DEPLOY_USER {config.deploy_user!r}; skipping chown")
    if config.deploy_group and gid is None:
        log.warning(str(root), f"Unknown DEPLOY_GROUP {config.deploy_group!r}; skipping chown")

    for path in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        try:
            if path.is_dir() or path.is_symlink():
                path.chmod(config.deploy_dir_mode)
            else:
                path.chmod(config.deploy_file_mode)
            if uid is not None or gid is not None:
                os.chown(
                    path,
                    uid if uid is not None else -1,
                    gid if gid is not None else -1,
                )
        except OSError as exc:
            log.warning(str(path), f"Could not set permissions: {exc}")

    try:
        root.chmod(config.deploy_dir_mode)
        if uid is not None or gid is not None:
            os.chown(
                root,
                uid if uid is not None else -1,
                gid if gid is not None else -1,
            )
    except OSError as exc:
        log.warning(str(root), f"Could not set permissions on build root: {exc}")


def prepare_build_dir(config: Config, log: BuildLog) -> bool:
    """Remove and recreate the active build directory (staging or output)."""
    target = config.build_dir
    try:
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as exc:
        log.fatal(str(target), f"Cannot prepare build directory: {exc}")
        return False


def finalize_build(config: Config, log: BuildLog) -> bool:
    """Apply permissions and atomically replace OUTPUT_DIR with the fresh build."""
    staging = config.build_dir
    dest = config.output_dir

    if not staging.is_dir():
        log.fatal(str(staging), "Build directory missing after build")
        return False

    apply_permissions(config, staging, log)

    if not config.atomic_build:
        print(f"Built site in {dest}")
        return True

    backup = dest.parent / f"{dest.name}.old"

    try:
        if backup.exists():
            shutil.rmtree(backup)
        if dest.exists():
            dest.rename(backup)
        staging.rename(dest)
        if backup.exists():
            shutil.rmtree(backup)
    except OSError as exc:
        log.fatal(str(dest), f"Atomic deploy failed: {exc}")
        if backup.exists() and not dest.exists():
            try:
                backup.rename(dest)
                log.warning(str(dest), "Restored previous site from backup after failed deploy")
            except OSError:
                pass
        return False

    print(f"Deployed site to {dest}")
    return True
