"""
Execute script for audio-to-Eos mapping.
Place this on an Execute DAT and set it to run on Frame Start.

This script is called every frame and processes audio analysis values
into Eos submaster commands based on S2L parameters.
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

# Reload module on every execute for development
if 'audio_eos_mapper' in sys.modules:
    importlib.reload(sys.modules['audio_eos_mapper'])

import audio_eos_mapper as mapper

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

    if not ENABLE_MAPPING:
        return

    try:
        # Get operators - Using ACTUAL paths from your TouchDesigner project
        audio_analysis = op('/project1/s2l_audio/fixutres/audio_analysis')
        audio_params = op('/project1/src/s2l_manager/audio_params_table')

        if not audio_analysis or not audio_params:
            # Only log once, not every frame
            if frame % 60 == 0:  # Log every 60 frames (~1 second at 60fps)
                print("[audio_eos_exec] ERROR: Cannot find required operators")
            return

        # Process audio → submasters
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
