"""
Frame-start watchdog that keeps EOS subscribe alive.

Copy this into a Text DAT (e.g. `watchdog_exec_callbacks`) and attach it to an
Execute DAT set to `Frame Start`. The script periodically checks when the last
OSC packet arrived and re-sends the subscribe command if EOS has been silent.
"""

CHECK_INTERVAL = 1.0  # seconds between watchdog evaluations
SILENCE_TIMEOUT = 5.0  # seconds of no OSC traffic before re-subscribing

_next_check = 0.0


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

    now = absTime.seconds
    if now < _next_check:
        return

    _next_check = now + CHECK_INTERVAL

    last_seen = _status_value("last_seen")
    if now - last_seen > SILENCE_TIMEOUT:
        mod("/project1/palette_logic/subscribe_manager").ensure_subscribed(force=True)
