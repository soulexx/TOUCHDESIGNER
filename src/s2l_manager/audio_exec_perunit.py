"""
Per-Unit Audio Execute Script

Place this on an Execute DAT and set it to run on Frame Start.

This replaces the old audio_eos_exec.py with per-unit processing:
- Each S2L_UNIT independently controls one submaster
- DMX from Eos controls which submaster and which audio band each unit uses
- Each unit has its own envelope (attack/hold/release)

Setup:
1. Create Execute DAT: /project1/src/s2l_manager/audio_exec
2. Set parameter "Execute" to "On"
3. Enable "Frame Start" callback
4. Point CHOP parameter to audio_analysis CHOP (if using CHOP Execute mode)

Required operators:
- /project1/src/s2l_manager/values (DMX-decoded parameters table)
- /project1/s2l_audio/fixutres/audio_analysis (audio analysis CHOP)
- /project1/io/oscout1 (OSC output to Eos)
"""

import sys

# Import TouchDesigner's 'op' function
try:
    import __main__
    op = __main__.op
except:
    op = None

# Setup paths
if 'C:/_DEV/TOUCHDESIGNER/src/s2l_unit' not in sys.path:
    sys.path.insert(0, 'C:/_DEV/TOUCHDESIGNER/src/s2l_unit')
if 'C:/_DEV/TOUCHDESIGNER/src/s2l_manager' not in sys.path:
    sys.path.insert(0, 'C:/_DEV/TOUCHDESIGNER/src/s2l_manager')

# Import audio engine
import audio_engine_perunit as engine

# Configuration
VALUES_TABLE_PATH = "/project1/src/s2l_manager/values"
AUDIO_CHOP_PATH = "/project1/s2l_audio/fixutres/audio_analysis"
ENABLE_PROCESSING = True
LOG_INTERVAL = 300  # Log stats every 300 frames (~5 seconds at 60fps)

# Frame counter
_frame_count = 0
_total_osc_sent = 0


def onFrameStart(frame):
    """Called every frame start - processes all units and sends OSC to Eos."""
    global op, _frame_count, _total_osc_sent

    _frame_count += 1

    # Get op if not available
    if op is None:
        try:
            import __main__
            op = __main__.op
        except:
            return

    if not ENABLE_PROCESSING:
        return

    try:
        # Get operators
        values_table = op(VALUES_TABLE_PATH)
        audio_chop = op(AUDIO_CHOP_PATH)

        if not values_table:
            if _frame_count % LOG_INTERVAL == 0:
                print(f"[audio_exec_perunit] ERROR: Cannot find values table at {VALUES_TABLE_PATH}")
            return

        if not audio_chop:
            if _frame_count % LOG_INTERVAL == 0:
                print(f"[audio_exec_perunit] ERROR: Cannot find audio CHOP at {AUDIO_CHOP_PATH}")
            return

        # Process all units
        sent_count = engine.process_all_units(values_table, audio_chop)
        _total_osc_sent += sent_count

        # Log stats periodically
        if _frame_count % LOG_INTERVAL == 0:
            print(f"[audio_exec_perunit] Frame {_frame_count}: {sent_count} units sent OSC (total: {_total_osc_sent})")

    except Exception as e:
        # Only log errors occasionally to avoid spam
        if _frame_count % 60 == 0:
            print(f"[audio_exec_perunit] ERROR in onFrameStart: {e}")
            import traceback
            traceback.print_exc()


def onValueChange(channel, sampleIndex, val, prev):
    """Called when CHOP values change - can trigger immediate processing."""
    # Alternative mode: process on audio value change instead of every frame
    # Currently disabled - using onFrameStart instead
    pass


def onTableChange(dat):
    """Called when values table changes - can trigger immediate processing."""
    # Could be used to clear envelope states when DMX params change
    pass


# ============================================================================
# TEST FUNCTIONS (call from Textport)
# ============================================================================

def test_unit(unit_name="S2L_UNIT_1"):
    """
    Test processing for a single unit.

    Usage from textport:
        exec_dat = op('/project1/src/s2l_manager/audio_exec')
        exec_dat.module.test_unit("S2L_UNIT_1")
    """
    engine.test_single_unit(unit_name)


def test_all():
    """
    Test processing all units once.

    Usage from textport:
        exec_dat = op('/project1/src/s2l_manager/audio_exec')
        exec_dat.module.test_all()
    """
    global op
    if op is None:
        try:
            import __main__
            op = __main__.op
        except:
            print("[test] ERROR: Not in TouchDesigner context")
            return

    values_table = op(VALUES_TABLE_PATH)
    audio_chop = op(AUDIO_CHOP_PATH)

    if not values_table or not audio_chop:
        print("[test] ERROR: Cannot find required operators")
        return

    sent_count = engine.process_all_units(values_table, audio_chop)
    print(f"[test] Processed all units, {sent_count} sent OSC")


def clear_states():
    """
    Clear all envelope states (useful when changing DMX params).

    Usage from textport:
        exec_dat = op('/project1/src/s2l_manager/audio_exec')
        exec_dat.module.clear_states()
    """
    engine.clear_states()


def show_config():
    """
    Show current configuration and operator paths.

    Usage from textport:
        exec_dat = op('/project1/src/s2l_manager/audio_exec')
        exec_dat.module.show_config()
    """
    global op
    if op is None:
        try:
            import __main__
            op = __main__.op
        except:
            print("[config] ERROR: Not in TouchDesigner context")
            return

    print("=" * 80)
    print("AUDIO EXEC PER-UNIT CONFIGURATION")
    print("=" * 80)
    print(f"Enabled: {ENABLE_PROCESSING}")
    print(f"Values table: {VALUES_TABLE_PATH}")
    print(f"Audio CHOP: {AUDIO_CHOP_PATH}")
    print(f"Log interval: {LOG_INTERVAL} frames")
    print()

    # Check operators
    values_table = op(VALUES_TABLE_PATH)
    audio_chop = op(AUDIO_CHOP_PATH)
    osc_out = op('/project1/io/oscout1')

    print("Operator Status:")
    print(f"  Values table: {'✅ Found' if values_table else '❌ NOT FOUND'}")
    if values_table:
        print(f"    Rows: {values_table.numRows}")
        print(f"    Cols: {values_table.numCols}")

    print(f"  Audio CHOP: {'✅ Found' if audio_chop else '❌ NOT FOUND'}")
    if audio_chop:
        print(f"    Channels: {audio_chop.numChans}")
        print(f"    Samples: {audio_chop.numSamples}")
        if audio_chop.numChans > 0:
            print(f"    Channel names: {[ch.name for ch in audio_chop.chans()[:10]]}")

    print(f"  OSC output: {'✅ Found' if osc_out else '❌ NOT FOUND'}")
    if osc_out:
        print(f"    Type: {osc_out.type}")

    print()
    print("=" * 80)


def reload_engine():
    """
    Reload the audio engine module (useful during development).

    Usage from textport:
        exec_dat = op('/project1/src/s2l_manager/audio_exec')
        exec_dat.module.reload_engine()
    """
    import importlib
    importlib.reload(engine)
    print("[reload] Audio engine module reloaded")
