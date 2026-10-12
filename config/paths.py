import os
import sys
from pathlib import Path

DEV_ROOT = Path(__file__).resolve().parent.parent
FROZEN_INSTALL_ROOT = Path(r"C:\ColegioJGC")


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def get_app_dir() -> Path:
    return Path(sys.executable).resolve().parent if is_frozen() else DEV_ROOT


def get_resource_dir() -> Path:
    return Path(sys._MEIPASS) if is_frozen() else DEV_ROOT


def _get_install_root() -> Path:
    return get_app_dir().parent if is_frozen() else DEV_ROOT


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_data_dir() -> Path:
    override = os.environ.get("COLEGIO_DATA_DIR")
    return _ensure_dir(Path(override) if override else _get_install_root() / "datos")


def get_backup_dir() -> Path:
    return _ensure_dir(_get_install_root() / "respaldos")
