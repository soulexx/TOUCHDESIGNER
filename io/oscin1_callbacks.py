"""Legacy shim that re-exports the optimised OSC callback implementation."""

import sys
from pathlib import Path
import importlib

BASE_PATH = Path(r"c:\_DEV\TOUCHDESIGNER")
IO_PATH = BASE_PATH / "io"
if str(IO_PATH) not in sys.path:
    sys.path.insert(0, str(IO_PATH))

osc_module = importlib.import_module("osc_in_callbacks")

# Re-export public symbols for TouchDesigner callbacks.
globals().update({k: getattr(osc_module, k) for k in dir(osc_module) if not k.startswith("_")})

__all__ = [k for k in globals() if not k.startswith("_")]
