# /project1/layers/menus/menu_engine — minimal & robust

OSCDAT = op('/project1/io/oscout1')
STATE  = op('/project1')  # Storage: ACTIVE_MENU ∈ {None, 1..5}

def _set_active(idx:int):
    STATE.store('ACTIVE_MENU', int(idx))
    print('[menu] ACTIVE_MENU =', int(idx))

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

def apply_menu_leds(menu_idx:int):
    """Nur Buttons bekommen LEDs; Encoder/EncPush/Fader NICHT."""
    T   = op(f"/project1/layers/menus/menu_{int(menu_idx)}/map_osc")
    drv = op("/project1/io/driver_led")
    if not T or not drv:
        print("[menu] WARN: map/driver missing"); 
        return
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

    # Menü-Tasten-LEDs (exklusiv)
    mcolor = _menu_color(menu_idx)
    for i in range(1,6):
        topic = f"btn/{i}"
        drv.module.send_led(topic, "press" if i == int(menu_idx) else "off", mcolor, do_send=True)

def _send_osc(addr, payload):
    try:
        OSCDAT.sendOSC(addr, payload)
        print("[osc]", addr, payload)
    except Exception as e:
        print("[osc ERR]", addr, payload, e)

def handle_event(topic, value):
    # Topic normalisieren: '/enc/1' -> 'enc/1'
    t_raw = str(topic or '')
    t = t_raw.lstrip('/')

    # 1) Menütasten (exklusiv)
    if t.startswith('btn/'):
        try:
            idx = int(t.split('/')[-1])
        except:
            idx = None
        if idx and 1 <= idx <= 5 and float(value) >= 0.5:
            _set_active(idx)
            apply_menu_leds(idx)
        return True

    act = _get_active()
    if not act:
        return False

    # 2) Encoder relativ ('enc/x' -> 'enc/x/delta' nach Filter)
    if t.startswith('enc/'):
        FILT = op('/project1/layers/menus/event_filters')
        if FILT:
            d = FILT.module.enc_delta(t, value)
            if d is not None:
                look = t + '/delta'     # 'enc/1/delta'
                path, scale = _lookup(act, look)
                if path:
                    _send_osc(path, [int(d)])
                else:
                    _send_osc('/' + look, [int(d)])
        return True

    # 3) Fader 14-bit geglättet ('fader/x')
    if t.startswith('fader/'):
        FILT = op('/project1/layers/menus/event_filters')
        y = FILT.module.fader_smooth(t, value) if FILT else None
        if y is not None:
            path, scale = _lookup(act, t)
            if path:
                _send_osc(path, [float(y)*scale])
            else:
                _send_osc('/' + t, [float(y)])
        return True

    # 4) Standard: Lookup und raus
    path, scale = _lookup(act, t)
    if path:
        try: _send_osc(path, [float(value)*scale])
        except: _send_osc(path, [value])
    return True
