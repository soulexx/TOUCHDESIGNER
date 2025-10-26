import os
import sys
from pathlib import Path

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
IO_PATH = BASE_PATH / "io"
if str(IO_PATH) not in sys.path:
    sys.path.insert(0, str(IO_PATH))

from _midi_dispatcher import MidiDispatcher

# Default API zeigt auf den MIDIcon-Handler. Bei Bedarf kann der Pfad am DAT
# ueberschrieben werden: op('/project1/io/midiin2_callbacks').store('api_path', '<path>')
_HANDLER = MidiDispatcher(
    api_path="/project1/io/midicon_api",
    log_name="midi_in2.log",
    device_label="midicon_map",
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
            print("[midiin2_callbacks] debug_callback error:", exc)
    _HANDLER.handle(dat, rowIndex, message, channel, index, value, input, bytes)
