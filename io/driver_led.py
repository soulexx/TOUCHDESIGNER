# /project1/io/driver_led — minimal, API-only, Palette-only, led_const-only

LED_CONST = op('/project1/io/led_const')
API       = op('/project1/io/midicraft_enc_api')
PALETTE   = op('/project1/io/palette_led')

# ---- intern: palette lookup ----
def _palette_value(color, stage):
    """
    stage ∈ {'off','dark','bright'}
    palette_led: columns expected: name | off | dark | bright | complement (optional)
    """
    if not PALETTE or PALETTE.numRows < 2:
        # Fallback-Werte, damit nix crasht
        return 0 if stage=='off' else (12 if stage=='dark' else 26)
    cols = {PALETTE[0,c].val.strip().lower(): c for c in range(PALETTE.numCols)}
    ci_name  = cols.get('name', 0)
    ci_stage = cols.get(stage)
    if ci_stage is None:
        return 0 if stage=='off' else (12 if stage=='dark' else 26)
    want = (color or '').strip().lower()
    for r in range(1, PALETTE.numRows):
        if PALETTE[r, ci_name] and PALETTE[r, ci_name].val.strip().lower() == want:
            v = PALETTE[r, ci_stage].val
            try: return int(float(v))
            except: return 0
    # not found -> defaults
    return 0 if stage=='off' else (12 if stage=='dark' else 26)

# ---- intern: (ch, note) nur aus API ----
def _ch_note_for_target(target):
    """
    Single Source of Truth: midicraft_enc_api.led_note_for_target(target) -> (ch, note)
    """
    if not API:
        print('[driver_led] ERR: API op missing')
        return None
    func = getattr(API.module, 'led_note_for_target', None)
    if not callable(func):
        print('[driver_led] ERR: API.led_note_for_target missing')
        return None
    try:
        ch, note = func(str(target))
        return int(ch), int(note)
    except Exception as e:
        print('[driver_led] EXC led_note_for_target:', e)
        return None

# ---- public: senden ----
def send_led(target, state, color, do_send=True):
    """
    target: 'btn/x' (später ggf. mehr)
    state : 'off' | 'idle' | 'press'
      idle  -> dark
      press -> bright
      off   -> off (0)
    color : name aus palette_led (z.B. 'blue')
    returns: (ch, note, vel) or None
    """
    st = (state or '').strip().lower()
    if st not in ('off','idle','press'):
        st = 'off'
    stage = 'off' if st=='off' else ('bright' if st=='press' else 'dark')

    chn = _ch_note_for_target(target)
    if not chn:
        print('[driver_led] WARN: no mapping for', target)
        return None
    ch, note = chn

    vel = _palette_value(color, stage)

    if do_send and LED_CONST:
        try:
            LED_CONST.par.name0  = f'ch{int(ch)}n{int(note)}'
            LED_CONST.par.value0 = int(vel)
        except Exception as e:
            print('[driver_led] EXC send led_const:', e)
            return None
    return (ch, note, vel)

# ---- helpers ----
def all_menu_off(menu_color='white'):
    for i in range(1,6):
        send_led(f'btn/{i}', 'off', menu_color, do_send=True)

def test_all_btns(menu_color='white'):
    for i in range(1,6):
        send_led(f'btn/{i}','press',menu_color,True)
