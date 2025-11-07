"""Helpers for reading project-level feature flags stored on /project1.

Centralising the lookups keeps the individual DAT scripts light and allows
flags to be toggled from one place (project storage, environment variables or
defaults here).
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

try:
    import __main__  # TouchDesigner context exposes op via __main__

    _OP_FUNC = getattr(__main__, "op", None)
except Exception:  # pragma: no cover - TouchDesigner context only
    _OP_FUNC = None


DEFAULT_FLAGS: Dict[str, Any] = {
    "VIDEO_CONTROL_ENABLED": True,
    "S2L_AUDIO_ENABLED": True,
    "AUTO_CUE_ENABLED": True,
    "PALETTE_SYNC_ENABLED": True,
    "PALETTE_SUBSCRIBE_ENABLED": True,
    "BUS_HISTORY_LIMIT": 512,
}


def _project_comp():
    """Return the /project1 COMP if available."""
    if _OP_FUNC is None:
        return None
    try:
        return _OP_FUNC("/project1")
    except Exception:
        return None


def _env_override(name: str) -> Optional[str]:
    """Check for environment variable overrides (TD_FLAG_<NAME>)."""
    return os.environ.get(f"TD_FLAG_{name}")


def _coerce_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        norm = value.strip().lower()
        if norm in {"1", "true", "yes", "on"}:
            return True
        if norm in {"0", "false", "no", "off"}:
            return False
    return default


def _coerce_int(value: Any, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def get(name: str, default: Any | None = None) -> Any:
    """Return raw flag value with fallback to defaults."""
    if default is None:
        default = DEFAULT_FLAGS.get(name)

    env_value = _env_override(name)
    if env_value is not None:
        return env_value

    base = _project_comp()
    if base:
        try:
            stored = base.fetch(name, None)
            if stored is not None:
                return stored
        except Exception:
            pass
    return default


def bool_flag(name: str, default: bool | None = None) -> bool:
    """Return boolean flag."""
    if default is None:
        default = bool(DEFAULT_FLAGS.get(name, False))
    value = get(name, default)
    return _coerce_bool(value, default)


def int_flag(name: str, default: int | None = None) -> int:
    """Return integer flag."""
    if default is None:
        default = int(DEFAULT_FLAGS.get(name, 0))
    value = get(name, default)
    return _coerce_int(value, default)


def set_default(name: str, value: Any) -> None:
    """Override a default at runtime (useful for tests)."""
    DEFAULT_FLAGS[name] = value

