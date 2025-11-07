"""
Auto-Cue Execute DAT Script

Place this on an Execute DAT and set it to run on Frame Start.

This orchestrates:
1. Music analysis (section detection, song recognition)
2. Auto-cue engine (cue selection and firing)

Setup:
1. Create Execute DAT: /project1/src/s2l_manager/auto_cue_exec
2. Set parameter "Execute" to "On"
3. Enable "Frame Start" callback
4. Ensure paths to operators are correct (see CONFIGURATION below)

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
if 'C:/_DEV/TOUCHDESIGNER/src' not in sys.path:
    sys.path.insert(0, 'C:/_DEV/TOUCHDESIGNER/src')
if 'C:/_DEV/TOUCHDESIGNER/src/s2l_manager' not in sys.path:
    sys.path.insert(0, 'C:/_DEV/TOUCHDESIGNER/src/s2l_manager')

# Import engines
import music_analyzer
import auto_cue_engine
from td_helpers import project_flags

# ============================================================================
# CONFIGURATION
# ============================================================================

VALUES_TABLE_PATH = "/project1/src/s2l_manager/values"
AUDIO_CHOP_PATH = "/project1/s2l_audio/fixutres/audio_analysis"

ENABLE_PROCESSING = True
LOG_INTERVAL = 300  # Log stats every N frames (~5 seconds at 60fps)

# Default parameters (used when unit has no DMX values yet)
DEFAULT_CONFIDENCE_MS = 1000.0
DEFAULT_MIN_SECTION_TIME_SEC = 8.0
DEFAULT_COOLDOWN_SEC = 3.0
DEFAULT_SONG_COOLDOWN_SEC = 30.0

# ============================================================================
# FRAME COUNTER
# ============================================================================

_frame_count = 0
_total_cues_fired = 0
_last_analyzer_output = None


def _processing_enabled() -> bool:
    """Return whether auto-cue processing should run this frame."""
    if project_flags:
        try:
            return project_flags.bool_flag("AUTO_CUE_ENABLED", ENABLE_PROCESSING)
        except Exception:
            pass
    if op:
        base = op("/project1")
        if base:
            try:
                override = base.fetch("AUTO_CUE_ENABLED", None)
                if override is not None:
                    return bool(override)
            except Exception:
                pass
    return bool(ENABLE_PROCESSING)


# ============================================================================
# PARAMETER EXTRACTION
# ============================================================================

def _get_analyzer_params_from_table(values_table):
    """Extract analyzer parameters from first enabled unit.

    Since all units share the same music analysis, we just take
    parameters from the first unit we find.

    Returns:
        Dict with: confidence_ms, min_section_time_sec, cooldown_sec, song_cooldown_sec
    """
    if not values_table or values_table.numRows < 2:
        return {
            'confidence_ms': DEFAULT_CONFIDENCE_MS,
            'min_section_time_sec': DEFAULT_MIN_SECTION_TIME_SEC,
            'cooldown_sec': DEFAULT_COOLDOWN_SEC,
            'song_cooldown_sec': DEFAULT_SONG_COOLDOWN_SEC,
        }

    # Find first unit and extract CH16-19
    params = {}
    first_unit = None

    for row in range(1, values_table.numRows):
        instance = values_table[row, 0].val
        if first_unit is None:
            first_unit = instance

        if instance == first_unit:
            param_name = values_table[row, 1].val
            param_value = values_table[row, 2].val

            if param_name == 'MinSectionTime':
                # CH16: 0-255 -> 1-100s
                dmx = int(param_value)
                params['min_section_time_sec'] = 1.0 + (dmx / 255.0) * 99.0

            elif param_name == 'CooldownAfterSwitch':
                # CH17: 0-255 -> 1-100s
                dmx = int(param_value)
                params['cooldown_sec'] = 1.0 + (dmx / 255.0) * 99.0

            elif param_name == 'RequireConfidenceFrames':
                # CH18: 0-255 -> 0-2550ms
                dmx = int(param_value)
                params['confidence_ms'] = dmx * 10.0

            elif param_name == 'SongCooldownTime':
                # CH19: 0-255 -> 1-990s
                dmx = int(param_value)
                params['song_cooldown_sec'] = 1.0 + (dmx / 255.0) * 989.0

    # Fill in defaults for missing params
    params.setdefault('confidence_ms', DEFAULT_CONFIDENCE_MS)
    params.setdefault('min_section_time_sec', DEFAULT_MIN_SECTION_TIME_SEC)
    params.setdefault('cooldown_sec', DEFAULT_COOLDOWN_SEC)
    params.setdefault('song_cooldown_sec', DEFAULT_SONG_COOLDOWN_SEC)

    return params


# ============================================================================
# MAIN FRAME CALLBACK
# ============================================================================

def onFrameStart(frame):
    """Called every frame start - orchestrates music analysis and cue firing."""
    global op, _frame_count, _total_cues_fired, _last_analyzer_output

    _frame_count += 1

    # Get op if not available
    if op is None:
        try:
            import __main__
            op = __main__.op
        except:
            return

    if not _processing_enabled():
        return

    try:
        # Get operators
        values_table = op(VALUES_TABLE_PATH)
        audio_chop = op(AUDIO_CHOP_PATH)

        if not values_table:
            if _frame_count % LOG_INTERVAL == 0:
                print(f"[auto_cue_exec] ERROR: Cannot find values table at {VALUES_TABLE_PATH}")
            return

        if not audio_chop:
            if _frame_count % LOG_INTERVAL == 0:
                print(f"[auto_cue_exec] ERROR: Cannot find audio CHOP at {AUDIO_CHOP_PATH}")
            return

        # Extract analyzer parameters from values table
        analyzer_params = _get_analyzer_params_from_table(values_table)

        # Run music analyzer
        analyzer_output = music_analyzer.analyze(
            audio_chop=audio_chop,
            confidence_ms=analyzer_params['confidence_ms'],
            min_section_time_sec=analyzer_params['min_section_time_sec'],
            cooldown_sec=analyzer_params['cooldown_sec'],
            song_cooldown_sec=analyzer_params['song_cooldown_sec'],
        )

        _last_analyzer_output = analyzer_output

        # Process all units with auto-cue engine
        fired_count = auto_cue_engine.process_all_units(
            values_table=values_table,
            analyzer_output=analyzer_output,
        )

        _total_cues_fired += fired_count

        # Log stats periodically
        if _frame_count % LOG_INTERVAL == 0:
            section = analyzer_output.get('current_section', 'UNKNOWN')
            stable_ms = analyzer_output.get('section_stable_ms', 0)
            print(f"[auto_cue_exec] Frame {_frame_count}: Section={section} ({stable_ms:.0f}ms), Fired={fired_count}, Total={_total_cues_fired}")

        # Log song changes immediately
        if analyzer_output.get('new_song_detected', False):
            print(f"[auto_cue_exec] 🎵 NEW SONG DETECTED at frame {_frame_count}")

    except Exception as e:
        # Only log errors occasionally to avoid spam
        if _frame_count % 60 == 0:
            print(f"[auto_cue_exec] ERROR in onFrameStart: {e}")
            import traceback
            traceback.print_exc()


# ============================================================================
# TEST FUNCTIONS (call from Textport)
# ============================================================================

def test_analyzer():
    """
    Test music analyzer with current audio.

    Usage from textport:
        exec_dat = op('/project1/src/s2l_manager/auto_cue_exec')
        exec_dat.module.test_analyzer()
    """
    global op

    if op is None:
        try:
            import __main__
            op = __main__.op
        except:
            print("[test] ERROR: Not in TouchDesigner context")
            return

    audio_chop = op(AUDIO_CHOP_PATH)
    if not audio_chop:
        print(f"[test] ERROR: Cannot find audio CHOP at {AUDIO_CHOP_PATH}")
        return

    # Run analyzer with default params
    result = music_analyzer.analyze(
        audio_chop=audio_chop,
        confidence_ms=DEFAULT_CONFIDENCE_MS,
        min_section_time_sec=DEFAULT_MIN_SECTION_TIME_SEC,
        cooldown_sec=DEFAULT_COOLDOWN_SEC,
        song_cooldown_sec=DEFAULT_SONG_COOLDOWN_SEC,
    )

    print("=" * 80)
    print("MUSIC ANALYZER TEST")
    print("=" * 80)
    print(f"Current section: {result['current_section']}")
    print(f"Section stable: {result['section_stable_ms']:.0f}ms")
    print(f"New song detected: {result['new_song_detected']}")
    print(f"Allow transition: {result['allow_transition']}")
    print()
    print("Scores:")
    for key, val in result['scores'].items():
        print(f"  {key}: {val:.3f}")
    print("=" * 80)


def test_unit(unit_name="S2L_UNIT_1"):
    """
    Test auto-cue engine for a specific unit.

    Usage from textport:
        exec_dat = op('/project1/src/s2l_manager/auto_cue_exec')
        exec_dat.module.test_unit("S2L_UNIT_1")
    """
    global op, _last_analyzer_output

    if op is None:
        try:
            import __main__
            op = __main__.op
        except:
            print("[test] ERROR: Not in TouchDesigner context")
            return

    values_table = op(VALUES_TABLE_PATH)
    if not values_table:
        print(f"[test] ERROR: Cannot find values table at {VALUES_TABLE_PATH}")
        return

    # Get unit state
    state = auto_cue_engine.get_unit_state(unit_name)

    print("=" * 80)
    print(f"AUTO-CUE ENGINE TEST: {unit_name}")
    print("=" * 80)

    # Show current parameters
    print("Parameters from values table:")
    for row in range(1, values_table.numRows):
        if values_table[row, 0].val == unit_name:
            param = values_table[row, 1].val
            value = values_table[row, 2].val

            # Show scaled value for key params
            if param == 'AutoCueMode':
                mode = auto_cue_engine._decode_advance_mode(int(value))
                print(f"  {param:25s} = {value:3s} ({mode})")
            elif param == 'MinSectionTime':
                scaled = auto_cue_engine._scale_ch16(int(value))
                print(f"  {param:25s} = {value:3s} ({scaled:.1f}s)")
            elif param == 'CooldownAfterSwitch':
                scaled = auto_cue_engine._scale_ch17(int(value))
                print(f"  {param:25s} = {value:3s} ({scaled:.1f}s)")
            elif param == 'RequireConfidenceFrames':
                scaled = auto_cue_engine._scale_ch18(int(value))
                print(f"  {param:25s} = {value:3s} ({scaled:.0f}ms)")
            elif param == 'SongCooldownTime':
                scaled = auto_cue_engine._scale_ch19(int(value))
                print(f"  {param:25s} = {value:3s} ({scaled:.0f}s)")
            else:
                print(f"  {param:25s} = {value}")

    print()
    print("Current state:")
    if state:
        for key, val in state.items():
            if key == 'cue_history':
                print(f"  {key:20s} = {val}")
            elif key in ['last_fire_time', 'last_switch_time', 'timer_next_fire']:
                if val:
                    import time
                    ago = time.time() - val
                    print(f"  {key:20s} = {ago:.1f}s ago")
                else:
                    print(f"  {key:20s} = never")
            else:
                print(f"  {key:20s} = {val}")
    else:
        print("  No state yet (unit not processed)")

    print()
    print("Last analyzer output:")
    if _last_analyzer_output:
        print(f"  Section: {_last_analyzer_output['current_section']}")
        print(f"  Stable: {_last_analyzer_output['section_stable_ms']:.0f}ms")
        print(f"  Allow transition: {_last_analyzer_output['allow_transition']}")
    else:
        print("  Not available yet")

    print("=" * 80)


def show_config():
    """
    Show current configuration and operator paths.

    Usage from textport:
        exec_dat = op('/project1/src/s2l_manager/auto_cue_exec')
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
    print("AUTO-CUE EXEC CONFIGURATION")
    print("=" * 80)
    print(f"Enabled: {_processing_enabled()} (default={ENABLE_PROCESSING})")
    print(f"Values table: {VALUES_TABLE_PATH}")
    print(f"Audio CHOP: {AUDIO_CHOP_PATH}")
    print(f"Log interval: {LOG_INTERVAL} frames")
    print()
    print(f"Frame count: {_frame_count}")
    print(f"Total cues fired: {_total_cues_fired}")
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

    print(f"  OSC output: {'✅ Found' if osc_out else '❌ NOT FOUND'}")

    print("=" * 80)


def reload_modules():
    """
    Reload all modules (useful during development).

    Usage from textport:
        exec_dat = op('/project1/src/s2l_manager/auto_cue_exec')
        exec_dat.module.reload_modules()
    """
    import importlib
    importlib.reload(music_analyzer)
    importlib.reload(auto_cue_engine)
    print("[reload] Modules reloaded: music_analyzer, auto_cue_engine")


def reset_all():
    """
    Reset all engine state (history, section tracking, etc.).

    Usage from textport:
        exec_dat = op('/project1/src/s2l_manager/auto_cue_exec')
        exec_dat.module.reset_all()
    """
    music_analyzer.reset()
    auto_cue_engine.reset()
    print("[reset] All state cleared")
