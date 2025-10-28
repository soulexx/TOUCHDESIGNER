# Import TouchDesigner's op() function
try:
    import __main__
    op = __main__.op
except:
    op = None

# Absolute paths
VALUES_TABLE_PATH = '/project1/src/s2l_manager/values'
AUDIO_PARAMS_TABLE_PATH = '/project1/src/s2l_manager/audio_params_table'

target_cols = ['Sensitivity','Threshold','LowCut_Hz','HighCut_Hz','Lag_ms','MinHold_s']

def build_table():
    src = op(VALUES_TABLE_PATH)
    dest = op(AUDIO_PARAMS_TABLE_PATH)
    dest.clear()
    dest.appendRow(['instance'] + target_cols)

    rows = {}
    for r in range(1, src.numRows):
        # Handle both multi-column tables and single-column TSV
        if src.numCols >= 3:
            # Multi-column table (proper format)
            inst = src[r, 0].val
            param = src[r, 1].val
            value = src[r, 2].val
        else:
            # Single column - parse TAB-separated values
            # Note: TD stores literal \t as two characters, not a tab character
            line = src[r, 0].val
            # Try escaped \t first (most common in TD)
            parts = line.split('\\t')
            if len(parts) < 3:
                # Fallback: try real tab character
                parts = line.split('\t')
            if len(parts) < 3:
                continue
            inst = parts[0].strip()
            param = parts[1].strip()
            value = parts[2].strip()

        if param not in target_cols:
            continue
        rows.setdefault(inst, {})[param] = value

    for inst, data in rows.items():
        dest.appendRow([inst] + [data.get(col, '') for col in target_cols])

def onTableChange(dat):
    build_table()
    return
