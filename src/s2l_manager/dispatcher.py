"""TouchDesigner-facing dispatcher for decoded S2L DMX data."""

from __future__ import annotations

from typing import Dict

import s2l_unit as s2l

# single-line log format to keep the textport tidy
_LOG_PREFIX = "[s2l_manager]"

print(f"{_LOG_PREFIX} dispatcher module reloaded")


_last_values: Dict[str, Dict[str, int]] = {}


def _ensure_table():
    table = op("values")  # type: ignore[name-defined]
    if table and table.numRows == 0:
        table.appendRow(["instance", "parameter", "value"])
    return table


def _set_table_value(table, instance: str, key: str, value: int) -> None:
    for row in range(1, table.numRows):
        if table[row, 0].val == instance and table[row, 1].val == key:
            table[row, 2].val = value
            return
    table.appendRow([instance, key, value])


def update_from_dmx(
    universe: int,
    values: Dict[str, Dict[str, int]],
    defaults: Dict[str, Dict[str, int]],
) -> None:
    global _last_values
    table = _ensure_table()

    for instance, params in values.items():
        prev = _last_values.get(instance, {})
        for key, val in params.items():
            if prev.get(key) == val:
                continue
            print(f"{_LOG_PREFIX} {instance}:{key} -> {val}")
            if table:
                _set_table_value(table, instance, key, val)
        _last_values[instance] = params.copy()

    # TODO: integrate with audio logic / OSC outs.
