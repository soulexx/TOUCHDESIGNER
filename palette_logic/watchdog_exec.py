"""
Frame-start watchdog that keeps EOS subscribe alive.

Copy this into a Text DAT (e.g. `watchdog_exec_callbacks`) and attach it to an
Execute DAT set to `Frame Start`. The script periodically checks when the last
OSC packet arrived and re-sends the subscribe command if EOS has been silent.
"""

import sys
from pathlib import Path

try:
    BASE_PATH = Path(project.folder).resolve()  # type: ignore[name-defined]
except Exception:
    BASE_PATH = Path(__file__).resolve().parent.parent if "__file__" in globals() else None
SRC_PATH = BASE_PATH / "src" if BASE_PATH else None
if SRC_PATH and SRC_PATH.exists() and str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

try:
    from td_helpers import project_flags
except Exception:
    project_flags = None

CHECK_INTERVAL = 1.0  # seconds between watchdog evaluations
SILENCE_TIMEOUT = 5.0  # seconds of no OSC traffic before re-subscribing

ENABLE_WATCHDOG = True

_next_check = 0.0


def _watchdog_enabled() -> bool:
    """Return whether the palette subscribe watchdog should run."""
    if project_flags:
        try:
            return project_flags.bool_flag("PALETTE_SUBSCRIBE_ENABLED", ENABLE_WATCHDOG)
        except Exception:
            pass
    base = None
    try:
        base = op("/project1")
    except Exception:
        base = None
    if base:
        try:
            flag = base.fetch("PALETTE_SUBSCRIBE_ENABLED", None)
            if flag is not None:
                return bool(flag)
        except Exception:
            pass
    return bool(ENABLE_WATCHDOG)


def _status_value(key: str, default: float = 0.0) -> float:
    table = op("eos_status")
    if table is None:
        return default
    row = table.row(key)
    if row is None:
        return default
    try:
        return float(row[1].val)
    except (ValueError, TypeError):
        return default


def onFrameStart(frame):
    global _next_check

    if not _watchdog_enabled():
        return

    now = absTime.seconds
    if now < _next_check:
        return

    _next_check = now + CHECK_INTERVAL

    last_seen = _status_value("last_seen")
    if now - last_seen > SILENCE_TIMEOUT:
        mod("/project1/palette_logic/subscribe_manager").ensure_subscribed(force=True)
