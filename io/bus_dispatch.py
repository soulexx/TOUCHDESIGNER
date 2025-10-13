
def onTableChange(dat):
    T = op('/project1/io/bus_events')
    if not T or T.numRows < 2: 
        return
    r = T.numRows - 1
    cols = { T[0,c].val.strip().lower(): c for c in range(T.numCols) }
    if 'path' not in cols or 'val' not in cols:
        return
    p = T[r,cols['path']].val if T[r,cols['path']] else ''
    v = T[r,cols['val']].val  if T[r,cols['val']]  else '0'
    eng = op('/project1/layers/menus/menu_engine')
    if eng and p:
        try:
            print('[dispatch]', p, v)
            eng.module.handle_event(p, float(v))
        except Exception as e:
            print('[bus-dispatch] EXC handle_event:', e)
    return
