# /project1/layers/menus/menu_engine — minimal & robust

OSCDAT = op('/project1/io/oscout1')
STATE  = op('/project1')  # Storage: ACTIVE_MENU ? {None, 1..5}

def _set_active(idx:int):
    STATE.store('ACTIVE_MENU', int(idx))

def _get_active():
    return STATE.fetch('ACTIVE_MENU', None)

def _lookup(menu_idx:int, topic:str):
    """Look up normalized topic (no leading slash) in menu_X/map_osc."""
    T = op(f"/project1/layers/menus/menu_{int(menu_idx)}/map_osc")
    if not T: 
        return None, 1.0
    cols = { T[0,c].val.strip().lower(): c for c in range(T.numCols) }
    ci_topic = cols.get('topic'); ci_path = cols.get('path_out')
    ci_scale = cols.get('scale'); ci_en   = cols.get('enabled')
    t = (topic or '').lstrip('/')
    for r in range(1, T.numRows):
        if ci_en is not None and T[r,ci_en] and T[r,ci_en].val.strip() != '1':
            continue
        if T[r,ci_topic] and T[r,ci_topic].val.strip().lstrip('/') == t:
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
    for r in range(1, T.numRows):
        if not T[r,ci_topic]:
            continue
        if T[r,ci_topic].val.strip().lstrip('/') == t:
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
    for r in range(1, T.numRows):
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
    T   = op(f"/project1/layers/menus/menu_{int(menu_idx)}/map_osc")
    drv = op("/project1/io/driver_led")
    if not T or not drv:
        print("[menu] WARN: map/driver missing"); 
        return
    for topic in _all_menu_button_topics():
        drv.module.send_led(topic, "off", "", do_send=True)

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
            drv.module.send_led(topic, "idle", color, do_send=True)

    for i in range(1,6):
        topic = f"btn/{i}"
        color_i = _menu_color(i)
        state = "press" if i == int(menu_idx) else "idle"
        drv.module.send_led(topic, state, color_i, do_send=True)

def _send_osc(addr, payload):
    try:
        OSCDAT.sendOSC(addr, payload)
    except Exception as e:
        print("[osc ERR]", addr, payload, e)

def handle_event(topic, value):
    # Topic normalisieren: '/enc/1' -> 'enc/1'
    t_raw = str(topic or '')
    t = t_raw.lstrip('/')

    # 1) Menue-Tasten (exklusiv) sowie sonstige Buttons
    if t.startswith('btn/'):
        try:
            idx = int(t.split('/')[-1])
        except:
            idx = None
        if idx and 1 <= idx <= 5:
            try:
                pressed = float(value) >= 0.5
            except:
                pressed = False
            if pressed:
                previous = _get_active()
                if previous != idx:
                    _set_active(idx)
                    apply_menu_leds(idx)
            return True

        act_btn = _get_active()
        if act_btn:
            drv = op('/project1/io/driver_led')
            if drv:
                color = _button_color(act_btn, t)
                if color:
                    try:
                        state = 'press' if float(value) >= 0.5 else 'idle'
                    except:
                        state = 'idle'
                    drv.module.send_led(t, state, color, do_send=True)
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

    # 3) Fader 14-bit geglättet ('fader/x')
    if t.startswith('fader/'):
        parts = t.split('/')
        base_topic = '/'.join(parts[:2]) if len(parts) > 2 and parts[2] in ('msb', 'lsb') else t
        FILT = op('/project1/layers/menus/event_filters')
        filt_mod = FILT.module if FILT else None
        func = getattr(filt_mod, 'fader_smooth', None) if filt_mod else None
        y = func(t, value) if callable(func) else (float(value) if base_topic == t else None)
        if y is not None:
            path, scale = _lookup(act, base_topic)
            if path:
                _send_osc(path, [float(y) * scale])
            else:
                _send_osc('/' + base_topic, [float(y)])
        return True

    # 4) Standard: Lookup und raus
    path, scale = _lookup(act, t)
    if path:
        try: _send_osc(path, [float(value)*scale])
        except: _send_osc(path, [value])
    return True


