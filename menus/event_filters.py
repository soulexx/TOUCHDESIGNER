# --- event_filters: einfache Normalisierung ---
import math
import time
from collections import defaultdict

# Encoder
ENC_DEADZONE         = 0     # |delta| <= 0 -> ignorieren (nur echte Nullwerte)
ENC_THRESHOLD        = 1     # kumulieren bis |sum| >= 1
ENC_ACCEL            = 0     # 0=aus, >0 verstaerkt deltas (int)

ENC_FINE_SPEED_MAX   = 4.0   # cps: darunter -> fine
ENC_NORMAL_SPEED_MIN = 4.0   # cps: ab hier normal
ENC_COARSE_SPEED_MIN = 12.0  # cps: ab hier logarithmisch gross/ coarse

ENC_COARSE_STEP_MIN  = 4     # minimaler coarse-step (Betrag)
ENC_COARSE_STEP_MAX  = 10    # maximaler coarse-step
ENC_COARSE_SPEED_MAX = 40.0  # cps -> maximale Skalierung

ENC_DEBUG            = False  # True -> Debug-Log pro Event

# Fader
FADER_ALPHA = 1.0
FADER_EPS   = 0.0

# Button Long Press
BUTTON_LONG_PRESS_MS = 1000  # 1 second threshold

_enc_acc       = defaultdict(int)          # topic -> sum
_enc_last_ts   = defaultdict(float)        # topic -> last timestamp
_enc_stage     = defaultdict(lambda: 'normal')  # topic -> last stage
_fader_ema   = {}                  # base-topic -> last
_fader_parts = defaultdict(lambda: {'msb': None, 'lsb': None})  # base-topic -> latest 7-bit parts
_btn_press_start = {}              # topic -> timestamp when button was pressed
_btn_toggle_state = {}             # topic -> current toggle state (0/1)

def _clamp(val, lo, hi):
    return max(lo, min(hi, val))


def _remap(value, in_min, in_max, out_min, out_max):
    if in_max <= in_min:
        return out_min
    if value is None:
        return out_min
    t = (value - in_min) / (in_max - in_min)
    t = _clamp(t, 0.0, 1.0)
    return out_min + t * (out_max - out_min)


def _decide_stage(speed):
    if speed is None:
        return 'normal'
    if speed <= ENC_FINE_SPEED_MAX:
        return 'fine'
    if speed >= ENC_COARSE_SPEED_MIN:
        return 'coarse'
    return 'normal'


def enc_delta(topic, raw_delta):
    now = time.monotonic()
    try:
        raw = int(raw_delta)
    except Exception:
        return None
    if abs(raw) <= ENC_DEADZONE:
        return None

    last_ts = _enc_last_ts[topic]
    dt = (now - last_ts) if last_ts else None
    _enc_last_ts[topic] = now

    speed = None
    if dt and dt > 1e-6:
        speed = abs(raw) / dt

    new_stage = _decide_stage(speed)
    _enc_stage[topic] = new_stage
    _enc_acc[topic] += raw

    if abs(_enc_acc[topic]) >= ENC_THRESHOLD:
        out = _enc_acc[topic]
        _enc_acc[topic] = 0

        if ENC_ACCEL:
            out = int(out * ENC_ACCEL)

        if ENC_DEBUG:
            spd_log = f"{speed:.2f}" if speed is not None else "?"
            print("[enc]", f"{time.time():.3f}", topic, new_stage, out,
                  "speed=", spd_log)

        if new_stage == 'coarse':
            spd = speed if speed is not None else ENC_COARSE_SPEED_MIN
            magnitude = ENC_COARSE_STEP_MIN + math.log10(
                max(1.0, spd) / ENC_COARSE_SPEED_MIN
            )
            magnitude = _clamp(magnitude, ENC_COARSE_STEP_MIN, ENC_COARSE_STEP_MAX)
            coarse_val = int(round(magnitude))
            if coarse_val <= 0:
                coarse_val = ENC_COARSE_STEP_MIN
            coarse_val = coarse_val if out > 0 else -coarse_val
            return ('coarse', coarse_val, {'speed': speed})

        stage_name = 'fine' if new_stage == 'fine' else 'normal'
        return (stage_name, int(out), {'speed': speed})

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
    Kombiniert 7-bit oder 14-bit Fader (MSB/LSB) und liefert geglaetteten 0..1 Wert.
    topic kann 'fader/x', 'fader/x/msb' oder 'fader/x/lsb' sein.
    """
    try:
        x = _clamp01(val01)
    except Exception:
        return None

    base, part = _base_topic(topic)
    store = _fader_parts[base]

    if part == 'msb':
        store['msb'] = int(round(x * 127.0))
        store['lsb'] = None  # Auf naechstes LSB warten
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

    _fader_ema[base] = value
    return float(value)


def button_press(topic, value):
    """
    Handle button press with optimistic short press and long press detection.

    Optimistic Press Pattern:
    - On button press: immediately return ('press', value) for instant feedback
    - On button release: check hold duration
      - If < 1000ms: short press (already handled)
      - If >= 1000ms: return ('long_press', toggle_value) for long action

    Args:
        topic (str): Button topic (e.g., 'btn/11', 'encPush/2')
        value (float): Button value (0 = released, 1 = pressed)

    Returns:
        - ('press', value): On button press - execute short action immediately
        - ('long_press', toggle_value): On long press release - execute long action
        - None: On short press release (already handled)

    Example usage in menu_engine:
        result = button_press(topic, value)
        if result:
            action_type, payload = result
            if action_type == 'press':
                # Execute short action (path_out)
                send_osc(short_path, payload)
            elif action_type == 'long_press':
                # Execute long action (path_out_long) with toggle
                send_osc(long_path, payload)
    """
    now = time.monotonic()

    try:
        val = float(value)
    except Exception:
        val = 0.0

    is_pressed = val >= 0.5

    if is_pressed:
        # Button just pressed - store timestamp and return immediate action
        _btn_press_start[topic] = now
        return ('press', val)
    else:
        # Button released - check if it was a long press
        press_start = _btn_press_start.get(topic)
        if press_start is None:
            # No press start recorded, ignore
            return None

        # Clear press start
        _btn_press_start.pop(topic, None)

        # Calculate hold duration
        duration_ms = (now - press_start) * 1000.0

        if duration_ms >= BUTTON_LONG_PRESS_MS:
            # Long press detected - toggle state
            current = _btn_toggle_state.get(topic, 0)
            new_state = 1 if current == 0 else 0
            _btn_toggle_state[topic] = new_state
            return ('long_press', float(new_state))
        else:
            # Short press - already handled on press event
            return None

