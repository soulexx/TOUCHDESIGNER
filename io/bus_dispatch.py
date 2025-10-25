
import os
import sys
import time
from pathlib import Path

# Portable path resolution: support both environment variable and relative path
BASE_PATH = Path(os.getenv('TOUCHDESIGNER_ROOT', Path(__file__).resolve().parent.parent))
SRC_PATH = BASE_PATH / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from td_helpers.file_ring_buffer import FileRingBuffer

_BUS_LOG = FileRingBuffer(
    BASE_PATH / "logs" / "bus_dispatch.log",
    max_lines=500,
    persist=True,
)


def onTableChange(dat):
    T = op('/project1/io/bus_events')
    if not T or T.numRows < 2:
        dat.store('last_row', T.numRows if T else 0)
        return

    cols = { T[0,c].val.strip().lower(): c for c in range(T.numCols) }
    if 'path' not in cols or 'val' not in cols:
        dat.store('last_row', T.numRows)
        return
    src_col = cols.get('src')
    ch_col = cols.get('ch')

    default_row = max(1, T.numRows - 1)
    last_row = int(dat.fetch('last_row', default_row))
    start = max(1, last_row)
    end = T.numRows
    if start >= end:
        dat.store('last_row', end)
        return

    eng = op('/project1/layers/menus/menu_engine')
    flag = dat.fetch('debug_print', None)
    if flag is None:
        dat.store('debug_print', True)
    debug_print = bool(dat.fetch('debug_print', True))
    for r in range(start, end):
        p = T[r,cols['path']].val if T[r,cols['path']] else ''
        v = T[r,cols['val']].val  if T[r,cols['val']]  else '0'
        s = ''
        if src_col is not None:
            cell = T[r, src_col]
            if cell:
                s = cell.val
        ch_val = ''
        if ch_col is not None:
            ch_cell = T[r, ch_col]
            if ch_cell and ch_cell.val:
                ch_val = ch_cell.val
        label = (s or '').strip() or 'dispatch'
        ch_tag = f" ch{ch_val}" if ch_val else ''
        if not p:
            continue

        try:
            should_log = not p.startswith('/midi/scaled/')
            if should_log:
                _BUS_LOG.append(f"{time.time():.3f} [{label}{ch_tag}] {p} {v}")
                if debug_print:
                    print(f'[{label}{ch_tag}]', p, v)
            if eng:
                eng.module.handle_event(p, float(v))
        except Exception as e:
            if debug_print:
                print('[bus-dispatch] EXC handle_event:', e)
    dat.store('last_row', end)
    return
