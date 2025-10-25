MAP_PATH = '/project1/io/midicraft_enc_map'
MAP = op(MAP_PATH)


def _refresh_map():
    global MAP
    if not MAP or not getattr(MAP, 'valid', True):
        MAP = op(MAP_PATH)
    return MAP


def _cols(table):
    return {table[0, c].val.strip().lower(): c for c in range(table.numCols)}


def _matches_channel(cell, incoming):
    val = (cell.val if cell else '').strip().lower()
    if not val:
        return False
    if val in {'*', 'any'}:
        return True
    try:
        return int(val) == int(incoming)
    except Exception:
        return False


def midi_to_topic(message: str, ch: int, idx: int):
    """
    message: 'Note On'/'Note Off'/'Control Change'
    returns (topic, kind) with kind in {'note','enc_rel','cc7','fader_msb','fader_lsb'}
    """
    table = _refresh_map()
    if not table or table.numRows < 2:
        return None, None

    msg = (message or '').strip()
    ch = int(ch)
    idx = int(idx)

    cols = _cols(table)
    ci_et = cols.get('etype')
    ci_ch = cols.get('ch')
    ci_idx = cols.get('idx')
    ci_top = cols.get('topic')
    ci_mode = cols.get('mode')

    expected = 'note' if msg in ('Note On', 'Note Off') else ('cc' if msg == 'Control Change' else None)
    if expected is None:
        return None, None

    for r in range(1, table.numRows):
        etype = table[r, ci_et].val
        if expected == 'note' and etype != 'note':
            continue
        if expected == 'cc' and etype not in ('cc', 'cc_lsb', 'cc_msb'):
            continue
        if ci_ch is not None and not _matches_channel(table[r, ci_ch], ch):
            continue
        if int(table[r, ci_idx].val) != idx:
            continue

        topic = table[r, ci_top].val.strip().lstrip('/')
        if etype == 'note':
            return topic, 'note'
        if etype == 'cc_lsb':
            return topic, 'fader_lsb'
        mode_cell = table[r, ci_mode] if ci_mode is not None else None
        mode = mode_cell.val.strip().lower() if mode_cell else ''
        if mode == 'rel':
            return topic, 'enc_rel'
        return topic, 'fader_msb' if topic.startswith('fader/') else 'cc7'
    return None, None


def led_note_for_target(target: str):
    """Return (channel, note) for LED feedback."""
    table = _refresh_map()
    if not table or table.numRows < 2:
        return (None, None)

    target = (target or '').strip().lstrip('/')
    if not target.startswith('btn/'):
        return (None, None)

    cols = _cols(table)
    ci_et = cols.get('etype')
    ci_ch = cols.get('ch')
    ci_idx = cols.get('idx')
    ci_top = cols.get('topic')

    for r in range(1, table.numRows):
        if table[r, ci_et].val != 'note':
            continue
        if table[r, ci_top].val.strip().lstrip('/') != target:
            continue
        try:
            ch_val = table[r, ci_ch].val.strip().lower()
            ch_num = int(ch_val) if ch_val not in {'*', 'any'} else 1
            return ch_num, int(table[r, ci_idx].val)
        except Exception:
            return (None, None)
    return (None, None)
