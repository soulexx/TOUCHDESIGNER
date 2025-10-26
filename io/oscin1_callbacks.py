"""OSC callback implementation for TouchDesigner."""
import os
import sys
from pathlib import Path
from typing import Dict, Sequence

# Portable path resolution: support both environment variable and relative path
BASE_PATH = Path(os.getenv('TOUCHDESIGNER_ROOT', Path(__file__).resolve().parent.parent))
SRC_PATH = BASE_PATH / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

_MENU_PREFIXES = {"menu", "midicraft", "device", "input"}
_OP_CACHE: Dict[str, object] = {}


def _get_op(path: str):
    """Cache expensive op() lookups; cache invalidates when operator disappears."""
    cached = _OP_CACHE.get(path)
    if cached is not None:
        if getattr(cached, "valid", True):
            return cached
        _OP_CACHE.pop(path, None)
    target = op(path)
    if target:
        _OP_CACHE[path] = target
    return target


def _get_project():
    return _get_op("/project1")


def _normalize_menu_topic(address: str) -> str:
    if not address:
        return ""
    parts = address.strip("/").split("/")
    if not parts:
        return ""
    if parts[0].lower() in _MENU_PREFIXES and len(parts) > 1:
        parts = parts[1:]
    if parts and parts[0].lower() == "menus" and len(parts) > 1:
        parts = parts[1:]
    if parts and parts[0].isdigit():
        parts = parts[1:]
    return "/".join(parts)


def _handle_menu_event(address: str, args: Sequence[object]) -> bool:
    topic = _normalize_menu_topic(address)
    if not topic:
        return False
    eng = _get_op("/project1/layers/menus/menu_engine")
    if not eng:
        return False
    try:
        value = args[0] if args else 0
    except Exception:
        value = 0
    try:
        return bool(eng.module.handle_event(topic, value))
    except Exception as exc:
        print("[osc_in] menu handler error:", topic, exc)
        return True


def _handle_palette_event(address: str, args: Sequence[object]) -> None:
    base = _get_project()
    if not base or not bool(base.fetch("PALETTE_SYNC_ENABLED", False)):
        return
    handler_comp = _get_op("/project1/palette_logic/eos_notify_handler")
    if not handler_comp:
        return
    try:
        handler = handler_comp.module
        handler.on_osc_receive(address, args, absTime.seconds)
    except Exception as exc:
        print("[osc_in] palette handler error:", address, exc)


def onReceiveOSC(dat, rowIndex, message, bytes, peer):
    address = ""
    args: Sequence[object] = ()
    try:
        address = message.address or ""
        args = tuple(message.vals)
    except Exception:
        return

    if address.startswith("/eos/"):
        _handle_palette_event(address, args)
    else:
        _handle_menu_event(address, args)

    return
