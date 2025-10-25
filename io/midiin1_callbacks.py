import os
import sys
from pathlib import Path

# Portable path resolution: support both environment variable and relative path
BASE_PATH = Path(os.getenv('TOUCHDESIGNER_ROOT', Path(__file__).resolve().parent.parent))
IO_PATH = BASE_PATH / "io"
if str(IO_PATH) not in sys.path:
    sys.path.insert(0, str(IO_PATH))

from _midi_dispatcher import MidiDispatcher

_HANDLER = MidiDispatcher(
    api_path="/project1/io/midicraft_enc_api",
    log_name="midi_in.log",
    device_label="midicraft_enc_map",
)


def _ensure_defaults(dat):
    if dat.fetch("device_label", None) is None:
        dat.store("device_label", _HANDLER.default_label)


def onReceiveMIDI(dat, rowIndex, message, channel, index, value, input, bytes):
    _ensure_defaults(dat)
    dbg = dat.fetch("debug_callback", None)
    if callable(dbg):
        try:
            dbg(dat, rowIndex, message, channel, index, value, input, bytes)
        except Exception as exc:
            print("[midiin1_callbacks] debug_callback error:", exc)
    _HANDLER.handle(dat, rowIndex, message, channel, index, value, input, bytes)
