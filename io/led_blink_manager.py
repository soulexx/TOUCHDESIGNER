"""
Simple LED blink scheduler driven from an Execute DAT.

Usage
-----
- Call `tick()` every frame (see `io/led_blink_exec.py`).
- Start or stop blink patterns via `start()` / `stop()`.
- Keep the base (fallback) LED state in sync with `update_base()`.
"""

import json
import time
from typing import Dict, List, Optional, Tuple

_FALLBACK_PATTERN = [
    {"state": "press", "duration": 0.5},
    {"state": "idle", "duration": 0.5},
]

_patterns: Dict[str, List[Dict[str, float]]] = {}
_entries: Dict[str, Dict[str, object]] = {}
_base_states: Dict[str, Tuple[str, Optional[str]]] = {}


def _pattern_dat():
    return op("/project1/io/led_blink_patterns")


def _driver():
    return op("/project1/io/driver_led")


def _load_patterns():
    """Refresh pattern definitions from DAT (cheap enough to do per tick)."""
    dat = _pattern_dat()
    _patterns.clear()
    if not dat or dat.numRows < 2:
        return
    cols = {dat[0, c].val.strip().lower(): c for c in range(dat.numCols)}
    ci_name = cols.get("name")
    ci_stages = cols.get("stages")
    if ci_name is None or ci_stages is None:
        return
    for r in range(1, dat.numRows):
        cell_name = dat[r, ci_name]
        cell_stage = dat[r, ci_stages]
        if not cell_name or not cell_name.val.strip():
            continue
        try:
            raw = cell_stage.val if cell_stage else ""
            stages = json.loads(raw) if raw else []
        except Exception as exc:
            print("[led_blink] WARN bad stages", cell_name.val, exc)
            continue
        cleaned = []
        for st in stages:
            if not isinstance(st, dict):
                continue
            state = (st.get("state") or "").strip().lower()
            if not state:
                continue
            try:
                duration = float(st.get("duration", 0.1))
            except Exception:
                duration = 0.1
            duration = max(duration, 0.01)
            color = (st.get("color") or "").strip()
            cleaned.append({"state": state, "duration": duration, "color": color})
        if cleaned:
            _patterns[cell_name.val.strip().lower()] = cleaned


def _pattern_for(name: str) -> List[Dict[str, float]]:
    if not _patterns:
        _load_patterns()
    return _patterns.get((name or "").strip().lower(), _FALLBACK_PATTERN)


def reload_patterns() -> List[str]:
    _load_patterns()
    return list(_patterns.keys())


def _send_led(target: str, state: str, color: Optional[str]):
    drv = _driver()
    module = getattr(drv, "module", None) if drv else None
    if not module:
        return
    try:
        module.send_led(target, state, color or "", do_send=True)
    except Exception as exc:
        print("[led_blink] EXC send", target, state, color, exc)


def _entry_key(target: str) -> str:
    return str(target or "").strip().lstrip("/")


def _apply_step(entry: Dict[str, object], now: float, first_step: bool = False):
    steps: List[Dict[str, float]] = entry["steps"]  # type: ignore
    idx: int = entry["index"]  # type: ignore
    step = steps[idx]
    color = step.get("color") or entry.get("color") or ""
    _send_led(entry["target"], step["state"], color)  # type: ignore
    # Schedule next change relative to now so we do not drift.
    duration = max(float(step.get("duration", 0.1)), 0.01)
    entry["next_time"] = now + duration
    if first_step:
        entry["started_at"] = now


def start(
    target: str,
    pattern_name: str,
    color: Optional[str] = None,
    base_state: Optional[Tuple[str, Optional[str]]] = None,
    priority: int = 0,
) -> bool:
    key = _entry_key(target)
    if not key:
        return False
    existing = _entries.get(key)
    if existing and int(existing.get("priority", 0)) > priority:
        return False
    steps = _pattern_for(pattern_name)
    if not steps:
        return False
    now = time.monotonic()
    entry_color = color or (base_state[1] if base_state else None)
    entry = {
        "target": key,
        "steps": steps,
        "index": 0,
        "next_time": now,  # Force immediate execution
        "priority": priority,
        "color": entry_color,
        "base": base_state or _base_states.get(key),
        "started_at": now,
    }
    _entries[key] = entry
    _apply_step(entry, now, first_step=True)
    return True


def stop(target: str, restore: bool = True) -> bool:
    key = _entry_key(target)
    entry = _entries.pop(key, None)
    if not entry:
        return False
    if restore:
        base = entry.get("base") or _base_states.get(key)
        if base:
            state, color = base
            _send_led(key, state, color)
    return True


def stop_all(restore: bool = True):
    keys = list(_entries.keys())
    for key in keys:
        stop(key, restore=restore)


def update_base(target: str, state: Optional[str], color: Optional[str]):
    key = _entry_key(target)
    if not key:
        return
    if state is not None:
        _base_states[key] = (state, color)
    else:
        _base_states.pop(key, None)
    if key not in _entries and state is not None:
        _send_led(key, state, color)


def is_active(target: str) -> bool:
    return _entry_key(target) in _entries


def tick(now: Optional[float] = None):
    if not _entries:
        return
    if not _patterns:
        _load_patterns()
    now = time.monotonic() if now is None else now
    for key, entry in list(_entries.items()):
        steps: List[Dict[str, float]] = entry["steps"]  # type: ignore
        if not steps:
            _entries.pop(key, None)
            continue
        while now >= float(entry.get("next_time", now)):
            entry["index"] = (int(entry.get("index", 0)) + 1) % len(steps)
            _apply_step(entry, now)


def active_targets() -> List[str]:
    return list(_entries.keys())
