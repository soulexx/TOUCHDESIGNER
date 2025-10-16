"""
Helpers to keep the EOS OSC subscribe alive and track connection state.

Copy this into a Text DAT in TouchDesigner (e.g. `subscribe_manager`) and import
the module via `mod('/project1/palette_logic/subscribe_manager')`.
"""

from typing import Iterable, Sequence, Optional


OSC_OUT_PATH = "/project1/io/oscout1"
STATUS_DAT = "eos_status"
PAL_TYPES: Sequence[str] = ("ip", "fp", "cp", "bp")


def _get_status_table():
    table = op(STATUS_DAT)
    if table is None:
        raise RuntimeError(f"Missing DAT '{STATUS_DAT}' for EOS status tracking.")
    return table


def _row_index(table, key: str) -> int:
    """Return DAT row index for the given key or -1 if missing."""
    for idx, row in enumerate(table.rows()):
        if len(row) and row[0].val == key:
            return idx
    return -1


def _set_status(key: str, value: str):
    table = _get_status_table()
    idx = _row_index(table, key)
    if idx < 0:
        table.appendRow([key, value])
    else:
        table[idx, 1] = value


def _get_status(key: str, default: str = "0") -> str:
    table = _get_status_table()
    idx = _row_index(table, key)
    if idx < 0:
        return default
    return table[idx, 1].val


def _send_osc(path: str, args: Iterable):
    osc_out = op(OSC_OUT_PATH)
    if osc_out is None:
        raise RuntimeError(f"OSC Out operator '{OSC_OUT_PATH}' not found.")
    osc_out.sendOSC(path, list(args))


def mark_activity():
    """Update the timestamp when we receive any OSC from EOS."""
    _set_status("last_seen", str(absTime.seconds))


def ensure_subscribed(force: bool = False, send_get: bool = True):
    """
    Make sure EOS is subscribed and optionally request initial palette lists.

    Args:
        force: if True, always send the subscribe command.
        send_get: if True, request /get/<type>/index after subscribing.
    """
    subscribed = _get_status("is_subscribed") == "1"
    if not subscribed or force:
        _send_osc("/eos/subscribe", [1])
        _set_status("is_subscribed", "1")
        _set_status("last_subscribe", str(absTime.seconds))

        if send_get:
            request_palette_indices()


def request_palette_indices():
    """Request index lists for every palette type."""
    for pal_type in PAL_TYPES:
        _send_osc(f"/eos/get/{pal_type}/index", [1, 50])


def reset_subscription_state():
    """Mark the subscription as unknown; used when EOS disconnects."""
    _set_status("is_subscribed", "0")
