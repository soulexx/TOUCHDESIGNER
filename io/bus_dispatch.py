from typing import Iterable, Optional, Tuple


_BUS_EVENTS_PATH = '/project1/io/bus_events'
_MENU_ENGINE_PATH = '/project1/layers/menus/menu_engine'


def _bus_table():
    """Return the DAT containing queued bus events."""
    return op(_BUS_EVENTS_PATH)


def _menu_engine_module():
    eng = op(_MENU_ENGINE_PATH)
    return getattr(eng, 'module', None) if eng else None


def _column_lookup(table) -> Optional[Tuple[int, int]]:
    cols = {table[0, c].val.strip().lower(): c for c in range(table.numCols)}
    path_idx = cols.get('path')
    val_idx = cols.get('val')
    if path_idx is None or val_idx is None:
        return None
    return path_idx, val_idx


def _iter_new_rows(table, start: int, path_idx: int, val_idx: int) -> Iterable[Tuple[str, float]]:
    for row in range(start, table.numRows):
        cell_path = table[row, path_idx]
        raw_path = cell_path.val if cell_path else ''
        path = (raw_path or '').strip()
        if not path:
            continue
        cell_val = table[row, val_idx]
        raw_val = cell_val.val if cell_val else ''
        try:
            value = float(raw_val)
        except (TypeError, ValueError):
            value = 0.0
        yield path, value


def onTableChange(dat):
    table = _bus_table()
    if not table:
        dat.store('last_row', 0)
        return
    if table.numRows < 2:
        dat.store('last_row', table.numRows)
        return

    column_indices = _column_lookup(table)
    if not column_indices:
        dat.store('last_row', table.numRows)
        return
    path_idx, val_idx = column_indices

    default_row = max(1, table.numRows - 1)
    last_row = int(dat.fetch('last_row', default_row))
    start = max(1, last_row)
    end = table.numRows
    if start >= end:
        dat.store('last_row', end)
        return

    module = _menu_engine_module()
    for path, value in _iter_new_rows(table, start, path_idx, val_idx):
        if not module:
            break
        try:
            print('[dispatch]', path, value)
            module.handle_event(path, value)
        except Exception as exc:
            print('[bus-dispatch] EXC handle_event:', exc)

    dat.store('last_row', end)
