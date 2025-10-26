# /project1/layers/menus/menu_engine � minimal & robust
import re

OSCDAT = op('/project1/io/oscout1')
STATE  = op('/project1')  # Storage: ACTIVE_MENU ? {None, 1..5}
DRV    = op('/project1/io/driver_led')
BLINK  = op('/project1/io/led_blink_manager')

_MULTI_ADDR_SPLIT = re.compile(r'\s*(?:&&|\|\||\||[,;\n])\s*')

def _iter_path_targets(path_spec):
    """Return normalized OSC addresses for a map entry (supports multi-send)."""
    if path_spec is None:
        return []
    if isinstance(path_spec, (list, tuple)):
        paths = []
        for item in path_spec:
            paths.extend(_iter_path_targets(item))
        return paths
    try:
        raw = str(path_spec)
    except Exception:
        raw = ''
    raw = raw.replace('\r', '').strip()
    if not raw:
        return []
    if _MULTI_ADDR_SPLIT.search(raw):
        parts = _MULTI_ADDR_SPLIT.split(raw)
    else:
        parts = [raw]
    return [p for p in (part.strip() for part in parts) if p]

def _send_path_spec(path_spec, payload):
    """Send payload to each OSC address defined in the spec."""
    sent = False
    for addr in _iter_path_targets(path_spec):
        _send_osc(addr, payload)
        sent = True
    return sent


def _normalize_submenu_key(value: str) -> str:
    if not value:
        return ''
    cleaned = re.sub(r'[^a-z0-9]+', '_', value.strip().lower())
    return cleaned.strip('_')


_SUBMENU_CONFIG = {
    4: [
        {"key": _normalize_submenu_key("form"), "label": "submenu 4.1 form", "blink": None},
        {"key": _normalize_submenu_key("image"), "label": "submenu 4.2 image", "blink": "slow"},
        {"key": _normalize_submenu_key("shutter"), "label": "submenu 4.3 shutter", "blink": "fast"},
    ],
}


def _submenu_state_key(menu_idx: int) -> str:
    return f"MENU_{int(menu_idx)}_SUBINDEX"


def _get_submenu_index(menu_idx: int):
    cfg = _SUBMENU_CONFIG.get(int(menu_idx))
    if not cfg:
        return None
    key = _submenu_state_key(menu_idx)
    raw = STATE.fetch(key, 0)
    try:
        idx = int(raw)
    except Exception:
        idx = 0
    idx = idx % len(cfg)
    if raw != idx:
        STATE.store(key, idx)
    return idx


def _set_submenu_index(menu_idx: int, idx: int):
    cfg = _SUBMENU_CONFIG.get(int(menu_idx))
    if not cfg:
        return
    total = len(cfg)
    idx = int(idx) % total
    STATE.store(_submenu_state_key(menu_idx), idx)


def _active_submenu_entry(menu_idx: int):
    cfg = _SUBMENU_CONFIG.get(int(menu_idx))
    if not cfg:
        return None
    idx = _get_submenu_index(menu_idx)
    if idx is None:
        return None
    return cfg[int(idx) % len(cfg)]


def _advance_submenu(menu_idx: int):
    cfg = _SUBMENU_CONFIG.get(int(menu_idx))
    if not cfg:
        return
    idx = _get_submenu_index(menu_idx) or 0
    _set_submenu_index(menu_idx, idx + 1)
    entry = _active_submenu_entry(menu_idx)
    try:
        label = entry.get("label") if entry else "?"
        print(f"[submenu] menu_{menu_idx} -> {label}")
    except Exception:
        pass


def _active_submenu_key(menu_idx: int) -> str:
    entry = _active_submenu_entry(menu_idx)
    return entry.get("key", "") if entry else ""


def _submenu_tracker(menu_idx: int):
    return {
        "has_sections": False,
        "current": "",
        "active": _active_submenu_key(menu_idx),
    }


def _update_submenu_tracker(tracker, topic_value: str):
    if not topic_value:
        return False
    text = topic_value.strip()
    if not text.lower().startswith("__submenu__"):
        return False
    rest = text[len("__submenu__"):].strip(" _:\t")
    tracker["has_sections"] = True
    tracker["current"] = _normalize_submenu_key(rest)
    return True


def _row_visible_for_submenu(tracker) -> bool:
    if not tracker["has_sections"]:
        return True
    current = tracker.get("current") or ""
    if not current:
        return True
    active = tracker.get("active") or ""
    if not active:
        return True
    return current == active


def _blink_module():
    return getattr(BLINK, "module", None) if BLINK else None


def _update_submenu_led_feedback(active_menu_idx: int):
    if 4 not in _SUBMENU_CONFIG:
        return
    mod = _blink_module()
    if not mod:
        return
    target = "btn/4"
    color = _menu_color(4)
    base_state = "press" if int(active_menu_idx) == 4 else "idle"
    try:
        mod.update_base(target, base_state, color)
    except Exception:
        pass
    if int(active_menu_idx) != 4:
        try:
            mod.stop(target)
        except Exception:
            pass
        return
    entry = _active_submenu_entry(4)
    pattern = entry.get("blink") if entry else None
    if pattern:
        try:
            mod.start(target, pattern, color=color, base_state=(base_state, color), priority=10)
        except Exception:
            pass
    else:
        try:
            mod.stop(target)
        except Exception:
            pass

def _set_active(idx:int):
    idx = int(idx)
    STATE.store('ACTIVE_MENU', idx)
    if idx in _SUBMENU_CONFIG:
        _get_submenu_index(idx)
    try:
        print('[menu active] menu_' + str(idx))
    except Exception:
        pass

def _get_active():
    return STATE.fetch('ACTIVE_MENU', None)

DEFAULT_MENU = 5
MENU_SELECT_ACTIONS = {
    # menu button index -> OSC path spec (multi-send supported)
    1: "/eos/key/macro && /eos/key/1 && /eos/key/2 && /eos/key/0 && /eos/key/1 && /eos/key/enter",
    2: "/eos/key/macro && /eos/key/1 && /eos/key/2 && /eos/key/0 && /eos/key/2 && /eos/key/enter",
    3: "/eos/key/macro && /eos/key/1 && /eos/key/2 && /eos/key/0 && /eos/key/3 && /eos/key/enter",
}

_FADER_QUANT_DIGITS = 3

def _quantize_fader_value(val):
    try:
        v = float(val)
    except Exception:
        return val
    if not (-1e9 < v < 1e9):
        return val
    v = max(0.0, min(1.0, v))
    return round(v, _FADER_QUANT_DIGITS)

def _ensure_active():
    act = _get_active()
    if not act:
        _set_active(DEFAULT_MENU)
        try:
            apply_menu_leds(DEFAULT_MENU)
        except Exception:
            pass


def _lookup(menu_idx:int, topic:str):
    """Look up normalized topic (no leading slash) in menu_X/map_osc."""
    T = op(f"/project1/layers/menus/menu_{int(menu_idx)}/map_osc")
    if not T: 
        return None, 1.0
    cols = { T[0,c].val.strip().lower(): c for c in range(T.numCols) }
    ci_topic = cols.get('topic'); ci_path = cols.get('path_out')
    ci_scale = cols.get('scale'); ci_en   = cols.get('enabled')
    if ci_topic is None:
        return None, 1.0
    t = (topic or '').lstrip('/')
    tracker = _submenu_tracker(menu_idx)
    for r in range(1, T.numRows):
        topic_cell = T[r,ci_topic]
        topic_val = topic_cell.val.strip() if topic_cell else ''
        if topic_val and _update_submenu_tracker(tracker, topic_val):
            continue
        if not _row_visible_for_submenu(tracker):
            continue
        if ci_en is not None and T[r,ci_en] and T[r,ci_en].val.strip() != '1':
            continue
        if not topic_cell:
            continue
        if topic_cell.val.strip().lstrip('/') == t:
            path  = T[r,ci_path].val if (ci_path is not None and T[r,ci_path]) else ''
            scale = float(T[r,ci_scale].val) if (ci_scale is not None and T[r,ci_scale] and T[r,ci_scale].val) else 1.0
            return path, scale
    return None, 1.0

def _topic_color(menu_idx:int, topic:str):
    T = op(f"/project1/layers/menus/menu_{int(menu_idx)}/map_osc")
    if not T:
        return ''
    cols = { T[0,c].val.strip().lower(): c for c in range(T.numCols) }
    ci_topic = cols.get('topic'); ci_color = cols.get('led_color')
    if ci_topic is None or ci_color is None:
        return ''
    t = (topic or '').lstrip('/')
    tracker = _submenu_tracker(menu_idx)
    for r in range(1, T.numRows):
        topic_cell = T[r,ci_topic]
        topic_val = topic_cell.val.strip() if topic_cell else ''
        if topic_val and _update_submenu_tracker(tracker, topic_val):
            continue
        if not _row_visible_for_submenu(tracker):
            continue
        if not topic_cell:
            continue
        if topic_cell.val.strip().lstrip('/') == t:
            return T[r,ci_color].val.strip() if T[r,ci_color] else ''
    return ''

def _button_color(menu_idx:int, topic:str):
    color = _topic_color(menu_idx, topic)
    return color if color else _menu_color(menu_idx)
 
def _all_menu_button_topics():
    topics = set()
    for idx in range(1,6):
        T = op(f"/project1/layers/menus/menu_{int(idx)}/map_osc")
        if not T or T.numRows < 2:
            continue
        cols = { T[0,c].val.strip().lower(): c for c in range(T.numCols) }
        ci_topic = cols.get('topic')
        if ci_topic is None:
            continue
        for r in range(1, T.numRows):
            if not T[r,ci_topic]:
                continue
            topic = T[r,ci_topic].val.strip().lstrip('/')
            if topic and topic.startswith('btn/'):
                topics.add(topic)
    return topics

def _menu_color(menu_idx:int):
    T = op(f"/project1/layers/menus/menu_{int(menu_idx)}/map_osc")
    if not T: return 'white'
    cols = { T[0,c].val.strip().lower(): c for c in range(T.numCols) }
    ci_topic=cols.get('topic'); ci_color=cols.get('led_color')
    if ci_topic is None or ci_color is None: return 'white'
    tracker = _submenu_tracker(menu_idx)
    for r in range(1, T.numRows):
        topic_cell = T[r,ci_topic]
        topic_val = topic_cell.val.strip() if topic_cell else ''
        if topic_val and _update_submenu_tracker(tracker, topic_val):
            continue
        if not _row_visible_for_submenu(tracker):
            continue
        if T[r,ci_topic] and T[r,ci_topic].val.strip() == '__menu_color__':
            v = T[r,ci_color].val.strip()
            return v if v else 'white'
    return 'white'


def _wheel_stage_path(base_path, stage):
    stage = (stage or 'normal').strip().lower()
    if not base_path or not isinstance(base_path, str):
        return None
    if not base_path.startswith('/eos/wheel/'):
        # Only wheel paths get stage variants.
        return base_path if stage == 'normal' else None
    suffix = base_path[len('/eos/wheel/') :].strip('/')
    if not suffix:
        return base_path if stage == 'normal' else None
    if suffix == 'level':
        # Level wheel uses explicit mode commands, not fine/coarse suffixes.
        return base_path
    if stage == 'fine':
        return f"/eos/wheel/fine/{suffix}"
    if stage == 'coarse':
        return f"/eos/wheel/coarse/{suffix}"
    return base_path

_LEVEL_MODE_CACHE = {}  # topic -> last wheel mode (fine=1.0, coarse=0.0)

def apply_menu_leds(menu_idx:int):
    """Nur Buttons bekommen LEDs; Encoder/EncPush/Fader NICHT."""
    T = op(f"/project1/layers/menus/menu_{int(menu_idx)}/map_osc")
    if not T or not DRV:
        print("[menu] WARN: map/driver missing");
        return
    for topic in _all_menu_button_topics():
        DRV.module.send_led(topic, "off", "", do_send=True)

    cols = { T[0,c].val.strip().lower(): c for c in range(T.numCols) }
    ci_topic = cols.get("topic"); ci_color = cols.get("led_color"); ci_en = cols.get("enabled")

    # Nur Buttons aus der Map im Idle anleuchten
    for r in range(1, T.numRows):
        if not T[r,ci_topic]: 
            continue
        if ci_en is not None and T[r,ci_en] and T[r,ci_en].val.strip() != "1":
            continue
        topic = T[r,ci_topic].val.strip().lstrip("/")
        if topic.startswith("__") or not topic.startswith("btn/"):
            continue
        color = (T[r,ci_color].val.strip() if (ci_color is not None and T[r,ci_color]) else "")
        if color:
            DRV.module.send_led(topic, "idle", color, do_send=True)

    for i in range(1,6):
        topic = f"btn/{i}"
        color_i = _menu_color(i)
        state = "press" if i == int(menu_idx) else "idle"
        DRV.module.send_led(topic, state, color_i, do_send=True)
    _update_submenu_led_feedback(menu_idx)

def _send_osc(addr, payload):
    try:
        print("[osc out]", addr, payload)
    except Exception:
        pass
    try:
        OSCDAT.sendOSC(addr, payload)
    except Exception as e:
        print("[osc ERR]", addr, payload, e)

def handle_event(topic, value):
    _ensure_active()
    # Topic normalisieren: '/enc/1' -> 'enc/1'
    t_raw = str(topic or '')
    t = t_raw.lstrip('/')

    # 1) Menue-Tasten (exklusiv) sowie sonstige Buttons
    if t.startswith('btn/'):
        try:
            idx = int(t.split('/')[-1])
        except (ValueError, IndexError, AttributeError):
            idx = None
        if idx and 1 <= idx <= 5:
            try:
                analog_value = float(value)
            except (ValueError, TypeError):
                analog_value = 0.0
            pressed = analog_value >= 0.5
            previous = _get_active()
            if pressed:
                if previous != idx:
                    _set_active(idx)
                    apply_menu_leds(idx)
                elif idx == 4:
                    _advance_submenu(idx)
                    apply_menu_leds(idx)
            action_spec = MENU_SELECT_ACTIONS.get(idx)
            if action_spec is not None:
                _send_path_spec(action_spec, [analog_value])
            return True

        act_btn = _get_active()
        if act_btn and DRV:
            color = _button_color(act_btn, t)
            if color:
                try:
                    state = 'press' if float(value) >= 0.5 else 'idle'
                except (ValueError, TypeError):
                    state = 'idle'
                DRV.module.send_led(t, state, color, do_send=True)
        # Button-Events ohne Menue-Wechsel laufen weiter zur OSC-Verarbeitung

    act = _get_active()
    if not act:
        return False

    # 2) Encoder relativ ('enc/x' -> 'enc/x/delta' nach Filter)
    if t.startswith('enc/'):
        FILT = op('/project1/layers/menus/event_filters')
        filt_mod = FILT.module if FILT else None
        func = getattr(filt_mod, 'enc_delta', None) if filt_mod else None

        events = None
        if callable(func):
            res = func(t, value)
            if res is None:
                return True
            if isinstance(res, list) and res and isinstance(res[0], (list, tuple)):
                events = res
            else:
                events = [res]
        else:
            try:
                events = [('normal', int(value), {'stop_before': False})]
            except Exception:
                events = None

        if not events:
            return True

        for evt in events:
            if not isinstance(evt, (list, tuple)) or len(evt) < 2:
                continue
            stage = str(evt[0] or 'normal').strip().lower()
            payload = evt[1]
            meta = evt[2] if len(evt) >= 3 and isinstance(evt[2], dict) else {}
            stop_before = bool(meta.get('stop_before'))

            if stop_before:
                _send_osc('/eos/switch/level', [0.0])

            if stage == 'turbo':
                try:
                    switch_val = float(payload)
                except Exception:
                    continue
                _LEVEL_MODE_CACHE.pop(t, None)
                _send_osc('/eos/switch/level', [switch_val])
                continue
            if stage == 'turbo_stop':
                _LEVEL_MODE_CACHE.pop(t, None)
                _send_osc('/eos/switch/level', [0.0])
                continue

            try:
                delta_int = int(payload)
            except Exception:
                continue
            if delta_int == 0:
                continue

            look = t + '/delta'     # 'enc/1/delta'
            path, scale = _lookup(act, look)
            base_path = (path or '').strip() if path else ''

            if scale is not None:
                try:
                    scale_val = float(scale)
                except Exception:
                    scale_val = 1.0
            else:
                scale_val = 1.0
            if not base_path:
                scale_val = 1.0

            send_path = base_path or None
            if send_path:
                stage_path = _wheel_stage_path(send_path, stage)
                if stage_path:
                    send_path = stage_path
            if not send_path:
                fallback_paths = {
                    'fine': '/eos/wheel/level',
                    'normal': '/eos/wheel/level',
                }
                send_path = fallback_paths.get(stage, '/' + look)
                scale_val = 1.0

            payload_value = float(delta_int) * scale_val
            if send_path.startswith('/eos/wheel/'):
                if send_path == '/eos/wheel/level':
                    desired_mode = 1.0 if stage == 'fine' else 0.0
                    last_mode = _LEVEL_MODE_CACHE.get(t)
                    if last_mode is None or abs(last_mode - desired_mode) > 1e-6:
                        _send_osc('/eos/wheel', [float(desired_mode)])
                        _LEVEL_MODE_CACHE[t] = desired_mode
                else:
                    _LEVEL_MODE_CACHE.pop(t, None)
                _send_osc(send_path, [payload_value])
            else:
                payload_out = int(round(payload_value)) if abs(payload_value - round(payload_value)) < 1e-6 else payload_value
                _send_osc(send_path, [payload_out])
        return True

    # 3) Fader 14-bit gegl�ttet ('fader/x')
    if t.startswith('fader/'):
        parts = t.split('/')
        base_topic = '/'.join(parts[:2]) if len(parts) > 2 and parts[2] in ('msb', 'lsb') else t
        FILT = op('/project1/layers/menus/event_filters')
        filt_mod = FILT.module if FILT else None
        func = getattr(filt_mod, 'fader_smooth', None) if filt_mod else None
        y = func(t, value) if callable(func) else (float(value) if base_topic == t else None)
        if y is not None:
            y = _quantize_fader_value(y)
            path, scale = _lookup(act, base_topic)
            if path:
                _send_osc(path, [float(y) * scale])
            else:
                _send_osc('/' + base_topic, [float(y)])
        return True

    # 4) Standard: Lookup und raus
    path, scale = _lookup(act, t)
    if path:
        try:
            val_out = float(value)
        except Exception:
            val_out = value
        if isinstance(val_out, (int, float)) and t.startswith('fader/'):
            val_out = _quantize_fader_value(val_out)
        try:
            _send_path_spec(path, [float(val_out) * scale])
        except Exception:
            _send_path_spec(path, [val_out])
    return True




