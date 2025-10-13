
MAP = op('/project1/io/midicraft_enc_map')

def _cols(T):
    return { T[0,c].val.strip().lower(): c for c in range(T.numCols) }

def midi_to_topic(message:str, ch:int, idx:int):
    """
    message: 'Note On'/'Note Off'/'Control Change'
    returns (topic, kind) with kind ∈ {'note','enc_rel','cc7','fader_msb','fader_lsb'}
    Einspurig: wir lesen direkt aus midicraft_enc_map (ohne dir).
    """
    if not MAP or MAP.numRows < 2:
        return None, None
    msg = (message or '').strip()
    ch  = int(ch); idx = int(idx)

    C = _cols(MAP)
    ci_et=C.get('etype'); ci_ch=C.get('ch'); ci_idx=C.get('idx'); ci_top=C.get('topic'); ci_mode=C.get('mode')

    # Erwartete etype für Nachricht
    et_req = 'note' if msg in ('Note On','Note Off') else ('cc' if msg=='Control Change' else None)
    if et_req is None:
        return None, None

    for r in range(1, MAP.numRows):
        et = MAP[r,ci_et].val
        if et_req=='note' and et!='note':
            continue
        if et_req=='cc' and et not in ('cc','cc_lsb'):
            continue
        if int(MAP[r,ci_ch].val) != ch:
            continue
        if int(MAP[r,ci_idx].val) != idx:
            continue

        topic = MAP[r,ci_top].val.strip().lstrip('/')
        if et=='note':
            return topic, 'note'
        if et=='cc_lsb':
            return topic, 'fader_lsb'
        mode = MAP[r,ci_mode].val.strip().lower() if MAP[r,ci_mode] else ''
        if mode=='rel':
            return topic, 'enc_rel'
        return topic, 'fader_msb' if topic.startswith('fader/') else 'cc7'
    return None, None

def led_note_for_target(target:str):
    """
    Einspurig: LED-Note = dieselbe Zeile, die BTN-Input definiert (etype='note', topic='btn/*').
    Gibt (ch, note) zurück.
    """
    if not MAP or MAP.numRows < 2:
        return (None, None)
    t = (target or '').strip().lstrip('/')
    if not t.startswith('btn/'):
        return (None, None)
    C = _cols(MAP)
    ci_et=C.get('etype'); ci_ch=C.get('ch'); ci_idx=C.get('idx'); ci_top=C.get('topic')
    for r in range(1, MAP.numRows):
        if MAP[r,ci_et].val!='note':
            continue
        if MAP[r,ci_top].val.strip().lstrip('/') != t:
            continue
        try:
            return int(MAP[r,ci_ch].val), int(MAP[r,ci_idx].val)
        except:
            return (None, None)
    return (None, None)
