"""Palette state management for EOS palette synchronisation."""
import time
from collections import deque
from typing import Deque, Dict, Optional

ORDER = ["ip", "fp", "cp", "bp"]
TABLE_HEADER = ["index", "num", "uid", "label", "channels", "bytype"]


class PaletteState:
    def __init__(self) -> None:
        now = time.perf_counter()
        self.base = None
        self.last_activity = now
        self.last_subscribe = 0.0
        self.last_count_request = 0.0
        self.subscribed = False
        self.counts: Dict[str, int] = {t: 0 for t in ORDER}
        self.queues: Dict[str, Deque[int]] = {t: deque() for t in ORDER}
        self.active: Dict[str, Optional[int]] = {t: None for t in ORDER}
        self.sent_at: Dict[str, float] = {t: 0.0 for t in ORDER}
        self.attempts: Dict[str, int] = {t: 0 for t in ORDER}

    def attach_base(self, base) -> None:
        if base and base != self.base:
            self.base = base

    def get_table(self, palette_type: str):
        if not self.base:
            return None
        return self.base.op(f"palette_logic/pal_{palette_type}")

    def ensure_table(self, palette_type: str, rows: int):
        table = self.get_table(palette_type)
        if not table:
            return None
        if table.numRows == 0:
            table.appendRow(TABLE_HEADER)
        else:
            while table.numCols < len(TABLE_HEADER):
                table.appendCol("")
            for col, name in enumerate(TABLE_HEADER):
                table[0, col] = name
        desired = max(rows, 0) + 1
        while table.numRows > desired:
            table.deleteRow(table.numRows - 1)
        while table.numRows < desired:
            table.appendRow([""] * table.numCols)
        return table


state = PaletteState()
__all__ = [
    "ORDER",
    "TABLE_HEADER",
    "state",
    "attach_base",
    "get_base",
    "get_table",
    "ensure_table",
    "get_osc_out",
    "mark_activity",
    "note_subscribe",
    "note_count_request",
]


def attach_base(base) -> None:
    state.attach_base(base)


def get_base():
    return state.base


def get_table(palette_type: str):
    return state.get_table(palette_type)


def ensure_table(palette_type: str, rows: int):
    return state.ensure_table(palette_type, rows)


def get_osc_out():
    base = get_base()
    return base.op("io/oscout1") if base else None


def mark_activity() -> None:
    state.last_activity = time.perf_counter()


def note_subscribe() -> None:
    state.subscribed = True
    state.last_subscribe = time.perf_counter()


def note_count_request() -> None:
    state.last_count_request = time.perf_counter()
