"""
Direct frame tick that doesn't rely on module imports.
This should be set as Execute DAT with Frame Start enabled.

SETUP:
1. Create a new Execute DAT at /project1/io/frame_tick_direct
2. Set its text to load from this file (Sync to File)
3. Enable: DAT Execute → Frame Start
4. Disable the old frame_tick

This will call the dispatcher DIRECTLY every frame without module caching issues.
"""

# Import required modules with full paths
import sys

# Ensure paths
if 'C:/_DEV/TOUCHDESIGNER/io' not in sys.path:
    sys.path.insert(0, 'C:/_DEV/TOUCHDESIGNER/io')

if 'C:/_DEV/TOUCHDESIGNER/src/s2l_unit' not in sys.path:
    sys.path.insert(0, 'C:/_DEV/TOUCHDESIGNER/src/s2l_unit')

# Import s2l_unit for decoding
import s2l_unit as s2l


# Configuration
DMX_CHOP_PATH = "/project1/io/EOS_Universe_016"
DISPATCHER_DAT_PATH = "/project1/src/s2l_manager/dispatcher"
UNIVERSE = 16

# Cache for performance
_instances_cache = None
_defaults_cache = None


def _get_instances():
    """Load and cache S2L instances for universe 16."""
    global _instances_cache
    if _instances_cache is None:
        all_instances = s2l.load_instances()
        _instances_cache = [
            inst for inst in all_instances
            if inst.enabled and inst.universe == UNIVERSE
        ]
    return _instances_cache


def _get_defaults():
    """Load and cache defaults."""
    global _defaults_cache
    if _defaults_cache is None:
        _defaults_cache = s2l.load_defaults()
    return _defaults_cache


def _chop_to_bytes(chop):
    """Convert CHOP to 512-byte DMX payload."""
    if not chop or chop.numSamples == 0:
        return None

    data = []
    for channel in chop.chans():
        raw = channel[0]
        value = max(0.0, min(255.0, raw))
        data.append(int(round(value)))

    # Ensure 512 bytes
    if len(data) > 512:
        data = data[-512:]
    elif len(data) < 512:
        data.extend([0] * (512 - len(data)))

    return bytes(data)


def onFrameStart(dat):
    """Called every frame - update DMX values to dispatcher."""

    # Get DMX CHOP
    dmx_chop = op(DMX_CHOP_PATH)
    if not dmx_chop:
        return

    # Convert to bytes
    payload = _chop_to_bytes(dmx_chop)
    if not payload:
        return

    # Get instances
    instances = _get_instances()
    if not instances:
        return

    # Decode DMX
    try:
        values = s2l.decode_universe(payload, instances, scaling=False)
    except s2l.DMXBufferError:
        return

    # Get dispatcher and call it
    dispatcher_dat = op(DISPATCHER_DAT_PATH)
    if not dispatcher_dat:
        print("[frame_tick_direct] ERROR: dispatcher not found")
        return

    update_func = getattr(dispatcher_dat.module, "update_from_dmx", None)
    if not callable(update_func):
        print("[frame_tick_direct] ERROR: update_from_dmx not found")
        return

    # Call dispatcher
    defaults = _get_defaults()
    update_func(UNIVERSE, values, defaults)
