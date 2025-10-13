
# --- event_filters: einfache Normalisierung ---
from collections import defaultdict

# Encoder
ENC_DEADZONE   = 1     # |delta| <= 1 -> ignorieren
ENC_THRESHOLD  = 2     # kumulieren bis |sum| >= 2
ENC_ACCEL      = 0     # 0=aus, >0 verstärkt deltas (int)

# Fader
FADER_ALPHA = 0.18     # EMA (0..1)
FADER_EPS   = 0.002    # Hysterese

_enc_acc   = defaultdict(int)   # topic -> sum
_fader_ema = {}                 # base-topic -> last
_fader_parts = defaultdict(lambda: {'msb': None, 'lsb': None})  # base-topic -> latest 7-bit parts

def enc_delta(topic, raw_delta):
    try: d = int(raw_delta)
    except: return None
    if abs(d) <= ENC_DEADZONE:
        return None
    if ENC_ACCEL:
        d = int(d * ENC_ACCEL)
    _enc_acc[topic] += d
    if abs(_enc_acc[topic]) >= ENC_THRESHOLD:
        out = _enc_acc[topic]
        _enc_acc[topic] = 0
        return int(out)
    return None

def _clamp01(val):
    return max(0.0, min(1.0, float(val)))

def _base_topic(topic):
    parts = topic.split('/')
    if len(parts) > 2 and parts[-1] in ('msb', 'lsb'):
        return '/'.join(parts[:-1]), parts[-1]
    return topic, None

def fader_smooth(topic, val01):
    """
    Kombiniert 7-bit oder 14-bit Fader (MSB/LSB) und liefert gegl�tteten 0..1 Wert.
    topic kann 'fader/x', 'fader/x/msb' oder 'fader/x/lsb' sein.
    """
    try:
        x = _clamp01(val01)
    except:
        return None

    base, part = _base_topic(topic)
    store = _fader_parts[base]

    if part == 'msb':
        store['msb'] = int(round(x * 127.0))
        store['lsb'] = None  # Auf n�chstes LSB warten
        return None

    if part == 'lsb':
        store['lsb'] = int(round(x * 127.0))
        msb = store.get('msb')
        if msb is None:
            return None
        lsb = store.get('lsb') or 0
        value = ((msb << 7) | lsb) / 16383.0
    else:
        # 7-bit Fader direkt (z.B. wenn nur MSB existiert)
        value = x
        store['msb'] = int(round(x * 127.0))
        store['lsb'] = 0

    last = _fader_ema.get(base)
    y = value if last is None else (FADER_ALPHA * value + (1 - FADER_ALPHA) * last)
    _fader_ema[base] = y
    if last is None or abs(y - last) >= FADER_EPS:
        return float(y)
    return None
