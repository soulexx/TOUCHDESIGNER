"""
Helpers to keep the EOS OSC subscribe alive and track connection state.

Copy this into a Text DAT in TouchDesigner (e.g. `subscribe_manager`) and import
the module via `mod('/project1/palette_logic/subscribe_manager')`.
"""

import time
from collections import deque
from typing import Deque, Dict, Iterable, Optional, Sequence


OSC_OUT_PATH = "/project1/io/oscout1"
STATUS_DAT = "eos_status"
PAL_TYPES: Sequence[str] = ("ip", "fp", "cp", "bp")
_MAX_INDEX_REQUESTS = 512  # safety guard against runaway loops
_LAST_COUNTS: Dict[str, int] = {}
_INDEX_QUEUES: Dict[str, Deque[int]] = {pal: deque() for pal in PAL_TYPES}
_ACTIVE_INDEX: Dict[str, Optional[int]] = {pal: None for pal in PAL_TYPES}
_SUBSCRIBE_BACKOFF = 5.0
_COUNT_BACKOFF = 2.0
_LAST_COUNT_REQUEST = 0.0


def _ensure_header(table):
    if table.numRows == 0:
        table.appendRow(["num", "uid", "label"])


def _trim_table(pal_type: str, count: int):
    table = op(f"pal_{pal_type}")
    if not table:
        return
    _ensure_header(table)
    desired = max(0, count) + 1
    while table.numRows > desired:
        table.deleteRow(table.numRows - 1)
    while table.numRows < desired:
        table.appendRow(["", "", ""])


def _extend_table(pal_type: str, count: int):
    _trim_table(pal_type, count)


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


def _wait_for_message(match, timeout=5.0):
    osc_in = op("/project1/io/oscin1_from_eos")
    if osc_in is None:
        raise RuntimeError("OSC In DAT '/project1/io/oscin1_from_eos' not found")
    last = int(osc_in.numRows)
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        current = int(osc_in.numRows)
        if current > last:
            rows = [osc_in.row(i) for i in range(last, current)]
            last = current
            for row in rows:
                result = match(row)
                if result is not None:
                    return result
        time.sleep(0.05)
    raise RuntimeError("Timeout waiting for OSC response")

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
    now = absTime.seconds
    last_seen = float(_get_status("last_seen", "0"))
    last_subscribe = float(_get_status("last_subscribe", "0"))

    should_subscribe = force or not subscribed or (now - last_seen > _SUBSCRIBE_BACKOFF and now - last_subscribe > _SUBSCRIBE_BACKOFF)

    if should_subscribe:
        if now - last_subscribe >= 0.5 or force:
            _send_osc("/eos/subscribe", [1])
            _set_status("is_subscribed", "1")
            _set_status("last_subscribe", str(now))
            if send_get:
                request_all_counts()
    elif send_get and now - last_seen > _COUNT_BACKOFF:
        request_all_counts()


def request_all_counts():
    """Request palette counts for every type so we can enumerate indices."""
    osc_in = op("/project1/io/oscin1_from_eos")
    if osc_in:
        osc_in.store("last_row", osc_in.numRows)
    global _LAST_COUNT_REQUEST
    _LAST_COUNT_REQUEST = absTime.seconds
    for pal_type in PAL_TYPES:
        request_palette_count(pal_type)


def request_palette_count(pal_type: str):
    """Ask EOS how many palettes of a given type exist."""
    _send_osc(f"/eos/get/{pal_type}/count", [])


def request_indices_for_count(pal_type: str, count: int):
    """Synchronise a palette type with EOS by requesting each index once."""
    count = max(0, min(int(count), _MAX_INDEX_REQUESTS))
    prev = _LAST_COUNTS.get(pal_type, 0)
    queue = _INDEX_QUEUES[pal_type]
    active = _ACTIVE_INDEX[pal_type]

    if count <= 0:
        queue.clear()
        _ACTIVE_INDEX[pal_type] = None
        _LAST_COUNTS[pal_type] = 0
        _trim_table(pal_type, 0)
        return

    restart = count < prev or prev == 0

    if restart:
        queue.clear()
        _ACTIVE_INDEX[pal_type] = None
        _trim_table(pal_type, count)
        # EOS uses 1-based palette numbers (1, 2, 3, ..., count)
        queue.extend(range(1, count + 1))
        _LAST_COUNTS[pal_type] = count
        print(f"[palette] restart queue {pal_type}: count={count}")
        _send_next_index(pal_type)
        return

    if count > prev:
        # Add new palette numbers (1-based)
        new_indices = list(range(prev + 1, count + 1))
        queue.extend(new_indices)
        _extend_table(pal_type, count)
        _LAST_COUNTS[pal_type] = count
        print(f"[palette] extend queue {pal_type}: add {new_indices}")
        if active is None:
            _send_next_index(pal_type)
        return

    # count unchanged; kick queue if idle
    _LAST_COUNTS[pal_type] = count
    if active is None and queue:
        _send_next_index(pal_type)


def _send_next_index(pal_type: str):
    queue = _INDEX_QUEUES[pal_type]
    if _ACTIVE_INDEX[pal_type] is not None:
        return
    if not queue:
        return
    palette_num = queue.popleft()
    _ACTIVE_INDEX[pal_type] = palette_num
    # Use correct EOS OSC API: /eos/get/{type}/{num}/list/{index}/{count}
    _send_osc(f"/eos/get/{pal_type}/{palette_num}/list/0/1", [])
    print(f"[palette] send {pal_type} palette #{palette_num}")


def notify_index_processed(pal_type: str, index: int):
    active = _ACTIVE_INDEX.get(pal_type)
    if active == index:
        _ACTIVE_INDEX[pal_type] = None
    queue = _INDEX_QUEUES.get(pal_type)
    if queue is None:
        return
    if queue:
        _send_next_index(pal_type)



def sync_palettes(pal_type: str = 'ip', timeout: float = 5.0):
    """Fetch all palette entries for the given type in a blocking manner."""
    handler = mod('/project1/palette_logic/eos_notify_handler')
    osc_out = op(OSC_OUT_PATH)
    if not handler or not osc_out:
        raise RuntimeError('OSC modules not initialised')

    def _count_match(row):
        parsed = handler._parse_count_row(row)
        if parsed and parsed['type'] == pal_type:
            return parsed['count']
        return None

    def _index_match(expected_index):
        def _inner(row):
            parsed = handler._parse_palette_row(row)
            if parsed and parsed['type'] == pal_type and parsed['index'] == expected_index:
                return parsed
            return None
        return _inner

    osc_in = op('/project1/io/oscin1_from_eos')
    if osc_in is None:
        raise RuntimeError("OSC In DAT '/project1/io/oscin1_from_eos' not found")

    osc_in.store('last_row', osc_in.numRows)
    _send_osc(f'/eos/get/{pal_type}/count', [])
    prev_count = _LAST_COUNTS.get(pal_type, 0)
    try:
        count = _wait_for_message(_count_match, timeout=timeout)
    except RuntimeError:
        if prev_count > 0:
            count = prev_count
        else:
            raise
    _trim_table(pal_type, count)

    # EOS uses 1-based palette numbers
    for palette_num in range(1, count + 1):
        osc_in.store('last_row', osc_in.numRows)
        # Use correct EOS OSC API: /eos/get/{type}/{num}/list/{index}/{count}
        _send_osc(f'/eos/get/{pal_type}/{palette_num}/list/0/1', [])
        try:
            parsed = _wait_for_message(_index_match(palette_num), timeout=timeout)
        except RuntimeError:
            print(f'[palette] WARN timeout waiting for {pal_type} palette #{palette_num}')
            continue
        handler._update_palette_row(pal_type, palette_num, parsed['num'], parsed['uid'], parsed['label'])

    _INDEX_QUEUES[pal_type].clear()
    _ACTIVE_INDEX[pal_type] = None
    _LAST_COUNTS[pal_type] = count
    print(f'[palette] {pal_type} sync complete ({count} entries)')

def sync_intensity_palettes(timeout: float = 5.0):
    return sync_palettes('ip', timeout=timeout)

def reset_subscription_state():
    """Mark the subscription as unknown; used when EOS disconnects."""
    _set_status("is_subscribed", "0")
