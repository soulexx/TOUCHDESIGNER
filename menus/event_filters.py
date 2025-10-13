
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
_fader_ema = {}                 # topic -> last

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

def fader_smooth(topic, val01):
    try: x = max(0.0, min(1.0, float(val01)))
    except: return None
    last = _fader_ema.get(topic)
    y = x if last is None else (FADER_ALPHA * x + (1 - FADER_ALPHA) * last)
    _fader_ema[topic] = y
    if last is None or abs(y - last) >= FADER_EPS:
        return float(y)
    return None
