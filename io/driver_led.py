import os
import sys
import time
from pathlib import Path
from typing import Dict, Tuple

# /project1/io/driver_led - minimal, API-only, Palette-only, led_const-only

# TouchDesigner-compatible path resolution
try:
    if 'TOUCHDESIGNER_ROOT' in os.environ:
        BASE_PATH = Path(os.getenv('TOUCHDESIGNER_ROOT'))
    else:
        try:
            BASE_PATH = Path(project.folder).resolve()  # type: ignore
        except NameError:
            BASE_PATH = Path(__file__).resolve().parent.parent
except Exception:
    BASE_PATH = Path(r"c:\_DEV\TOUCHDESIGNER")
SRC_PATH = BASE_PATH / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from td_helpers.file_ring_buffer import FileRingBuffer

LED_CONST = op("/project1/io/led_const")
API = op("/project1/io/midicraft_enc_api")
PALETTE = op("/project1/io/midicraft_enc_led_palette")

_LED_STATE: Dict[Tuple[int, int], int] = {}
_MIDI_OUT_LOG = FileRingBuffer(
    BASE_PATH / "logs" / "midi_out.log",
    max_lines=400,
    persist=True,
)


def _flush_led_const() -> None:
    """Sync aggregated LED state into the Constant CHOP."""
    if not LED_CONST:
        return
    try:
        items = sorted(_LED_STATE.items())
        pars = LED_CONST.par
        has_num = hasattr(pars, "numchans")
        old_count = int(pars.numchans.eval()) if has_num else len(items)
        if has_num:
            pars.numchans = max(len(items), 1)
        for idx, ((ch, note), vel) in enumerate(items):
            name_par = f"name{idx}"
            val_par = f"value{idx}"
            try:
                pars[name_par] = f"ch{int(ch)}n{int(note)}"
            except (AttributeError, KeyError, TypeError):
                pass  # Parameter doesn't exist or invalid type
            try:
                pars[val_par] = int(vel)
            except (AttributeError, KeyError, TypeError, ValueError):
                pass  # Parameter doesn't exist or invalid type
        if old_count > len(items):
            for idx in range(len(items), old_count):
                name_par = f"name{idx}"
                val_par = f"value{idx}"
                try:
                    pars[name_par] = ""
                except (AttributeError, KeyError, TypeError):
                    pass  # Parameter doesn't exist
                try:
                    pars[val_par] = 0
                except (AttributeError, KeyError, TypeError):
                    pass  # Parameter doesn't exist
    except (AttributeError, TypeError, ValueError) as exc:
        print(f"[driver_led] ERROR flush led_const: {exc}")


def _palette_value(color, stage):
    """
    stage ? {'off','dark','bright'}
    palette_led: columns expected: name | off | dark | bright | complement (optional)
    """
    if not PALETTE or PALETTE.numRows < 2:
        # Fallback-Werte, damit nix crasht
        return 0 if stage == "off" else (12 if stage == "dark" else 26)
    cols = {PALETTE[0, c].val.strip().lower(): c for c in range(PALETTE.numCols)}
    ci_name = cols.get("name", 0)
    ci_stage = cols.get(stage)
    if ci_stage is None:
        return 0 if stage == "off" else (12 if stage == "dark" else 26)
    want = (color or "").strip().lower()
    for r in range(1, PALETTE.numRows):
        if PALETTE[r, ci_name] and PALETTE[r, ci_name].val.strip().lower() == want:
            v = PALETTE[r, ci_stage].val
            try:
                return int(float(v))
            except (ValueError, TypeError):
                return 0  # Invalid number format
    # not found -> defaults
    return 0 if stage == "off" else (12 if stage == "dark" else 26)


def _ch_note_for_target(target):
    """
    Single Source of Truth: midicraft_enc_api.led_note_for_target(target) -> (ch, note)
    """
    if not API:
        print("[driver_led] ERR: API op missing")
        return None
    func = getattr(API.module, "led_note_for_target", None)
    if not callable(func):
        print("[driver_led] ERR: API.led_note_for_target missing")
        return None
    try:
        ch, note = func(str(target))
        return int(ch), int(note)
    except (ValueError, TypeError, AttributeError) as exc:
        print(f"[driver_led] ERROR led_note_for_target({target}): {exc}")
        return None


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
    st = (state or "").strip().lower()
    if st not in ("off", "idle", "press"):
        st = "off"
    stage = "off" if st == "off" else ("bright" if st == "press" else "dark")

    chn = _ch_note_for_target(target)
    if not chn:
        print("[driver_led] WARN: no mapping for", target)
        return None
    ch, note = chn

    vel = _palette_value(color, stage)

    if do_send and LED_CONST:
        try:
            key = (int(ch), int(note))
            ivel = int(vel)
            if ivel <= 0:
                _LED_STATE.pop(key, None)
            else:
                _LED_STATE[key] = ivel
            _flush_led_const()
        except (ValueError, TypeError) as exc:
            print(f"[driver_led] ERROR send led_const: {exc}")
            return None
    try:
        status = "Note On" if int(vel) > 0 else "Note Off"
        _MIDI_OUT_LOG.append(
            f"{time.time():.3f} {status} ch{ch} note{note} vel{vel} target={target} state={st} color={color or ''}"
        )
    except (OSError, ValueError, TypeError):
        pass  # Log write failed, not critical
    return (ch, note, vel)


def all_menu_off(menu_color="white"):
    for i in range(1, 6):
        send_led(f"btn/{i}", "off", menu_color, do_send=True)


def test_all_btns(menu_color="white"):
    for i in range(1, 6):
        send_led(f"btn/{i}", "press", menu_color, True)


def reset():
    """Clear cached LED state and update the constant CHOP."""
    _LED_STATE.clear()
    _flush_led_const()


reset()
