MAP_PATH = '/project1/io/midicon_map'
MAP = None


def _resolve_op():
    try:
        return op  # type: ignore[name-defined]
    except Exception:
        pass
    try:
        import td  # type: ignore[import-not-found]

        return td.op  # type: ignore[attr-defined]
    except Exception:
        pass
    return None


def _refresh_map():
    global MAP
    op_fn = _resolve_op()
    if op_fn is None:
        return MAP
    if not MAP or not getattr(MAP, 'valid', True):
        try:
            MAP = op_fn(MAP_PATH)
        except Exception:
            MAP = None
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
    """Map incoming MIDI to topic/kind."""
    table = _refresh_map()
    if not table or table.numRows < 2:
        return None, None

    msg = (message or '').strip()
    ch = int(ch)
    idx = int(idx)
    if msg in ("Note On", "Note Off"):
        idx = max(idx - 1, 0)
    elif msg == "Control Change":
        idx = max(idx - 1, 0)

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
        etype = table[r, ci_et].val if ci_et is not None else ''
        if expected == 'note' and etype != 'note':
            continue
        if expected == 'cc' and etype not in ('cc', 'cc_lsb', 'cc_msb'):
            continue

        if ci_ch is not None:
            if not _matches_channel(table[r, ci_ch], ch):
                continue
        if ci_idx is not None:
            try:
                if int(table[r, ci_idx].val) != idx:
                    continue
            except Exception:
                continue

        topic = table[r, ci_top].val.strip().lstrip('/') if ci_top is not None else ''
        if not topic:
            continue

        if etype == 'note':
            if topic.startswith('midicon/wheel/'):
                base, _, action = topic.rpartition('/')
                if action == 'up':
                    return base, 'enc_rel_up'
                if action == 'down':
                    return base, 'enc_rel_down'
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
    table = _refresh_map()
    if not table or table.numRows < 2:
        return (None, None)

    tgt = (target or '').strip().lstrip('/')
    cols = _cols(table)
    ci_et = cols.get('etype')
    ci_ch = cols.get('ch')
    ci_idx = cols.get('idx')
    ci_top = cols.get('topic')
    if ci_et is None or ci_ch is None or ci_idx is None or ci_top is None:
        return (None, None)

    for r in range(1, table.numRows):
        if table[r, ci_et].val != 'note':
            continue
        topic = table[r, ci_top].val.strip().lstrip('/')
        if topic != tgt:
            continue
        try:
            ch_val = table[r, ci_ch].val.strip().lower()
            ch = int(ch_val) if ch_val not in {'*', 'any'} else 1
            return ch, int(table[r, ci_idx].val)
        except Exception:
            return (None, None)
    return (None, None)
