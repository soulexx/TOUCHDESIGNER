"""Legacy shim that re-exports the optimised OSC callback implementation."""

import os
import sys
from pathlib import Path
import importlib

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

# TouchDesigner lädt DAT-Skripte manchmal sehr früh und erwartet dabei bereits
# ein Modul `project1`. Falls es noch nicht existiert, legen wir einen Dummy an,
# damit `previousimport`-Wrapper keinen ImportError wirft.
if "project1" not in sys.modules:
    import types

    sys.modules["project1"] = types.ModuleType("project1")

osc_module = importlib.import_module("osc_in_callbacks")

# Re-export public symbols for TouchDesigner callbacks.
globals().update({k: getattr(osc_module, k) for k in dir(osc_module) if not k.startswith("_")})

__all__ = [k for k in globals() if not k.startswith("_")]
