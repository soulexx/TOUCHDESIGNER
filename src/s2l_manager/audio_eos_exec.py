"""
Execute script for audio-to-Eos mapping.
Place this on an Execute DAT and set it to run on Frame Start.

This script is called every frame and:
1. Updates DMX values from Eos to values table
2. Rebuilds audio_params_table from values
3. Processes audio analysis with S2L parameters
4. Sends OSC to Eos submasters
"""

import sys
import importlib

# Import TouchDesigner's 'op' function
try:
    import __main__
    op = __main__.op
except:
    # Fallback: try to get from builtins
    try:
        op = globals()['op']
    except:
        op = None

# Setup paths
if 'C:/_DEV/TOUCHDESIGNER/io' not in sys.path:
    sys.path.insert(0, 'C:/_DEV/TOUCHDESIGNER/io')
if 'C:/_DEV/TOUCHDESIGNER/src/s2l_unit' not in sys.path:
    sys.path.insert(0, 'C:/_DEV/TOUCHDESIGNER/src/s2l_unit')
if 'C:/_DEV/TOUCHDESIGNER/src/s2l_manager' not in sys.path:
    sys.path.insert(0, 'C:/_DEV/TOUCHDESIGNER/src/s2l_manager')

# Import modules
import audio_eos_mapper as mapper
import s2l_unit as s2l

# DMX Update Configuration
DMX_CHOP_PATH = "/project1/io/EOS_Universe_016"
DISPATCHER_DAT_PATH = "/project1/src/s2l_manager/dispatcher"
DMX_UNIVERSE = 16

# Cache for DMX processing
_dmx_instances_cache = None
_dmx_defaults_cache = None
_last_dmx_update_frame = -100  # Update DMX every N frames

# Configuration: Map audio channels to Eos submaster numbers
# Adjust these submaster numbers to match your Eos show
# IMPORTANT: Channel names must EXACTLY match your audio_analysis CHOP!
SUBMASTER_MAPPING = {
    'low': 11,              # Bass frequencies → Submaster 11
    'mid': 12,              # Mid frequencies → Submaster 12
    'high': 13,             # High frequencies → Submaster 13
    'kick': 14,             # Kick drum → Submaster 14
    'snare': 15,            # Snare → Submaster 15
    'rythm': 16,            # Rhythm detection → Submaster 16 (note: 'rythm' not 'rhythm')
    'smsd': 17,             # Spectral Mean Standard Deviation → Submaster 17
    'fmsd': 18,             # Flux Mean Standard Deviation → Submaster 18
    'spectralCentroid': 19, # Spectral Centroid → Submaster 19
}

# Enable/disable mapping
ENABLE_MAPPING = True
# How often to update DMX (every N frames, 1=every frame, 10=every 10 frames)
DMX_UPDATE_INTERVAL = 5


def _update_dmx_values(current_frame):
    """Update DMX values from Eos to values table."""
    global _dmx_instances_cache, _dmx_defaults_cache, _last_dmx_update_frame, op

    # Only update every N frames to reduce CPU load
    if current_frame - _last_dmx_update_frame < DMX_UPDATE_INTERVAL:
        return

    _last_dmx_update_frame = current_frame

    try:
        # Get DMX CHOP
        dmx_chop = op(DMX_CHOP_PATH)
        if not dmx_chop or dmx_chop.numSamples == 0:
            return

        # Convert CHOP to bytes
        data = []
        for channel in dmx_chop.chans():
            raw = channel[0]
            value = max(0.0, min(255.0, raw))
            data.append(int(round(value)))

        # Pad to 512 bytes
        if len(data) > 512:
            data = data[-512:]
        elif len(data) < 512:
            data.extend([0] * (512 - len(data)))

        payload = bytes(data)

        # Get instances (cached)
        if _dmx_instances_cache is None:
            all_instances = s2l.load_instances()
            _dmx_instances_cache = [
                inst for inst in all_instances
                if inst.enabled and inst.universe == DMX_UNIVERSE
            ]

        if not _dmx_instances_cache:
            return

        # Decode DMX
        values = s2l.decode_universe(payload, _dmx_instances_cache, scaling=False)

        # Get defaults (cached)
        if _dmx_defaults_cache is None:
            _dmx_defaults_cache = s2l.load_defaults()

        # Get dispatcher and update
        dispatcher_dat = op(DISPATCHER_DAT_PATH)
        if dispatcher_dat:
            update_func = getattr(dispatcher_dat.module, "update_from_dmx", None)
            if callable(update_func):
                update_func(DMX_UNIVERSE, values, _dmx_defaults_cache)

    except Exception as e:
        # Log errors occasionally, not every frame
        if current_frame % 300 == 0:  # Every 5 seconds at 60fps
            print(f"[audio_eos_exec] DMX update error: {e}")


def onFrameStart(frame):
    """Called every frame start - processes audio and sends OSC to Eos."""
    global op

    # Get op if not available
    if op is None:
        try:
            import __main__
            op = __main__.op
        except:
            return

    # STEP 1: Update DMX values from Eos every N frames
    _update_dmx_values(frame)

    if not ENABLE_MAPPING:
        return

    try:
        # STEP 2: Get operators
        audio_analysis = op('/project1/s2l_audio/fixutres/audio_analysis')
        audio_params = op('/project1/src/s2l_manager/audio_params_table')

        if not audio_analysis or not audio_params:
            # Only log once, not every frame
            if frame % 60 == 0:  # Log every 60 frames (~1 second at 60fps)
                print("[audio_eos_exec] ERROR: Cannot find required operators")
            return

        # STEP 3: Process audio → submasters with S2L parameters
        mapper.process_audio_to_subs(
            audio_analysis,
            audio_params,
            SUBMASTER_MAPPING
        )

    except Exception as e:
        # Only log errors occasionally to avoid spam
        if frame % 60 == 0:
            print(f"[audio_eos_exec] ERROR in onFrameStart: {e}")


# Alternative: Process on cook (DAT changes)
def onTableChange(dat):
    """Called when audio_params_table changes - can trigger immediate update."""
    pass


# Alternative: Process on value change
def onValueChange(channel, sampleIndex, val, prev):
    """Called when CHOP values change - can be used for trigger-based processing."""
    pass


# For testing: Call this manually from textport
def test_single_channel(channel='kick', sub=10):
    """
    Test function: Maps a single audio channel to a submaster.

    Usage from textport:
        import audio_eos_exec
        audio_eos_exec.test_single_channel('kick', 10)
    """
    global op
    if op is None:
        try:
            import __main__
            op = __main__.op
        except:
            print("[test] ERROR: Cannot access 'op' - not in TouchDesigner context")
            return

    audio_analysis = op('/project1/s2l_audio/fixutres/audio_analysis')
    audio_params = op('/project1/src/s2l_manager/audio_params_table')

    if not audio_analysis or not audio_params:
        print("[test] ERROR: Cannot find operators")
        return

    mapper.map_audio_channel_to_sub(
        audio_analysis,
        audio_params,
        channel,
        sub
    )
    print(f"[test] Mapped {channel} → Sub {sub}")


def test_all_mappings():
    """
    Test function: Runs one iteration of all mappings.

    Usage from textport:
        import audio_eos_exec
        audio_eos_exec.test_all_mappings()
    """
    global op
    if op is None:
        try:
            import __main__
            op = __main__.op
        except:
            print("[test] ERROR: Cannot access 'op' - not in TouchDesigner context")
            return

    audio_analysis = op('/project1/s2l_audio/fixutres/audio_analysis')
    audio_params = op('/project1/src/s2l_manager/audio_params_table')

    if not audio_analysis or not audio_params:
        print("[test] ERROR: Cannot find operators")
        return

    mapper.process_audio_to_subs(
        audio_analysis,
        audio_params,
        SUBMASTER_MAPPING
    )
    print(f"[test] Processed {len(SUBMASTER_MAPPING)} mappings")
