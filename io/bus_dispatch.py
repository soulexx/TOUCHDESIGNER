
def onTableChange(dat):
    T = op('/project1/io/bus_events')
    if not T or T.numRows < 2:
        dat.store('last_row', T.numRows if T else 0)
        return

    cols = { T[0,c].val.strip().lower(): c for c in range(T.numCols) }
    if 'path' not in cols or 'val' not in cols:
        dat.store('last_row', T.numRows)
        return

    default_row = max(1, T.numRows - 1)
    last_row = int(dat.fetch('last_row', default_row))
    start = max(1, last_row)
    end = T.numRows
    if start >= end:
        dat.store('last_row', end)
        return

    eng = op('/project1/layers/menus/menu_engine')
    for r in range(start, end):
        p = T[r,cols['path']].val if T[r,cols['path']] else ''
        v = T[r,cols['val']].val  if T[r,cols['val']]  else '0'
        if eng and p:
            try:
                print('[dispatch]', p, v)
                eng.module.handle_event(p, float(v))
            except Exception as e:
                print('[bus-dispatch] EXC handle_event:', e)
    dat.store('last_row', end)
    return
