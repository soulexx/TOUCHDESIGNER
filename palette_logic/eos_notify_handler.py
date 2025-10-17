# FILE: /project1/palette_logic/eos_notify_handler.py
# Zweck: Direktes Parsing der Eos OUT-Pfade aus address/args. Keine Table-Abhängigkeit.
import re
from .state import set_last_seen
from .pump  import queue_counts, on_list_ack

# Eos OUT-Pfadmuster
RE_COUNT = re.compile(r'^/eos/out/get/(ip|fp|cp|bp)/count$')
RE_LIST  = re.compile(r'^/eos/out/get/(ip|fp|cp|bp)/(\d+)/list/(\d+)/(\d+)$')
RE_CHAN  = re.compile(r'^/eos/out/get/(ip|fp|cp|bp)/(\d+)/channels/list/(\d+)/(\d+)$')
RE_BTYP  = re.compile(r'^/eos/out/get/(ip|fp|cp|bp)/(\d+)/bytype/list/(\d+)/(\d+)$')

# Hilfen für Tabellen pal_ip / pal_fp / pal_cp / pal_bp
def _tab(typ: str):
    p = f"/project1/palette_logic/pal_{typ}"
    t = op(p)
    if not t:
        t = parent().create(op.TABLEDAT, f"pal_{typ}")
    if t.numRows == 0:
        t.appendRow(['num','index','uid','label','absolute','locked','channels','bytype'])
    return t

def _upsert(t, num, idx, **fields):
    # upsert via (num,index)
    for r in range(1, t.numRows):
        if t[r,'num'] and t[r,'index'] and t[r,'num'].val == str(num) and t[r,'index'].val == str(idx):
            for k,v in fields.items():
                if t[0,k] is not None:
                    t[r,k] = str(v)
            return
    row = {'num':num,'index':idx, **fields}
    t.appendRow([str(row.get(c,'')) for c in [c.val for c in t.row(0)]])

def on_osc_receive(address: str, args: list, ts: float = 0.0):
    """
    Direkter Entry-Point für OSC-Pakete.
    address: z.B. '/eos/out/get/ip/1001/list/0/6'
    args:    Liste der Argumente (index, uid, label, absolute, locked, ...)
    ts:      optionaler Zeitstempel (nur für Debug)
    """
    # Lebenszeichen -> Watchdog beruhigen
    set_last_seen(op('/project1'))

    # --- /count ---
    m = RE_COUNT.match(address)
    if m:
        typ = m.group(1)
        # ETC sendet count als erstes Int-Argument
        count = int(args[0]) if args else 0
        queue_counts(op('/project1'), {typ: count})
        return

    # --- /list (Basis-Metadaten) ---
    m = RE_LIST.match(address)
    if m:
        typ, palnum, list_index, list_count = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
        # Erwartete Argumente laut Doku:
        #   0: itemIndex (0-basiert)
        #   1: UID (string)
        #   2: Label (string)
        #   3: absolute (bool/int)
        #   4: locked (bool/int)
        idx      = int(args[0]) if len(args) > 0 else list_index
        uid      = str(args[1]) if len(args) > 1 else ''
        label    = str(args[2]) if len(args) > 2 else ''
        absolute = str(args[3]).lower() in ('1','true','True') if len(args) > 3 else False
        locked   = str(args[4]).lower() in ('1','true','True') if len(args) > 4 else False

        t = _tab(typ)
        _upsert(t, palnum, idx, uid=uid, label=label, absolute=int(absolute), locked=int(locked))
        # inflight bestätigen → nächster Index
        on_list_ack(op('/project1'), typ, idx)
        return

    # --- /channels/list (optional) ---
    m = RE_CHAN.match(address)
    if m:
        typ, palnum, list_index, list_count = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
        idx   = int(args[0]) if len(args) > 0 else list_index
        uid   = str(args[1]) if len(args) > 1 else ''
        chans = str(args[2]) if len(args) > 2 else ''
        _upsert(_tab(typ), palnum, idx, uid=uid or '', channels=chans)
        return

    # --- /bytype/list (optional) ---
    m = RE_BTYP.match(address)
    if m:
        typ, palnum, list_index, list_count = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
        idx   = int(args[0]) if len(args) > 0 else list_index
        uid   = str(args[1]) if len(args) > 1 else ''
        bytyp = str(args[2]) if len(args) > 2 else ''
        _upsert(_tab(typ), palnum, idx, uid=uid or '', bytype=bytyp)
        return

    # andere Eos-Pfade ignorieren oder separat behandeln
    return
