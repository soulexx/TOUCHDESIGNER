target_cols = ['Sensitivity','Threshold','LowCut_Hz','HighCut_Hz','Lag_ms','MinHold_s']

def build_table():
    src = op('values')
    dest = op('audio_params_table')
    dest.clear()
    dest.appendRow(['instance'] + target_cols)

    rows = {}
    for r in range(1, src.numRows):
        inst = src[r, 0].val
        param = src[r, 1].val
        if param not in target_cols:
            continue
        value = src[r, 2].val
        rows.setdefault(inst, {})[param] = value

    for inst, data in rows.items():
        dest.appendRow([inst] + [data.get(col, '') for col in target_cols])

def onTableChange(dat):
    build_table()
    return
