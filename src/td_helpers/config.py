"""Project-wide configuration helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

try:
    import yaml
except ImportError as exc:  # pragma: no cover - should only happen if PyYAML missing
    raise RuntimeError(
        "PyYAML is required to load middleware.yaml. Install it or adjust the config loader."
    ) from exc

_CACHE: Dict[str, Any] | None = None
_DEFAULT_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "middleware.yaml"


def load() -> Dict[str, Any]:
    """Return parsed configuration from middleware.yaml."""
    global _CACHE
    if _CACHE is None:
        with _DEFAULT_PATH.open("r", encoding="utf-8") as stream:
            _CACHE = yaml.safe_load(stream) or {}
    return _CACHE


def logs_dir() -> Path:
    """Return absolute path to the logs directory."""
    cfg = load()
    base = Path(cfg.get("logging", {}).get("base_dir", "logs"))
    if not base.is_absolute():
        base = (_DEFAULT_PATH.parent.parent / base).resolve()
    return base


def log_file(key: str) -> Path:
    """Return absolute path for a named log file, e.g. 'osc_history_file'."""
    cfg = load().get("logging", {})
    path = Path(cfg.get(key, f"logs/{key}.log"))
    if not path.is_absolute():
        path = (_DEFAULT_PATH.parent.parent / path).resolve()
    return path


def log_setting(key: str, default: Any | None = None) -> Any | None:
    """Return arbitrary value from the logging block."""
    return load().get("logging", {}).get(key, default)
