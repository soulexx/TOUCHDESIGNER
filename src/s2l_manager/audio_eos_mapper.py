"""
Audio-to-Eos Mapper
Maps audio analysis values to Eos Submaster commands using S2L parameters.

Flow:
    audio_analysis CHOP → apply S2L parameters → generate OSC commands → Eos
"""

from __future__ import annotations
from typing import Dict, Optional
import time

_LOG_PREFIX = "[audio_eos_mapper]"
print(f"{_LOG_PREFIX} module loaded")

# Import TouchDesigner's 'op' function
try:
    import __main__
    op = __main__.op
except:
    try:
        op = globals()['op']
    except:
        op = None

# OSC output operator
_OSCOUT = None  # Will be set to op('/project1/io/oscout1')

# State tracking for level changes
_last_levels: Dict[str, float] = {}
_last_send_time: Dict[str, float] = {}

# Performance settings
MIN_LEVEL_CHANGE = 0.01  # Minimum change to trigger OSC send (1%)
MIN_SEND_INTERVAL = 0.05  # Minimum time between sends per sub (50ms)


def _get_osc_operator():
    """Lazy load OSC output operator."""
    global _OSCOUT, op

    # Ensure op is available
    if op is None:
        try:
            import __main__
            op = __main__.op
        except Exception as e:
            print(f"{_LOG_PREFIX} ERROR: Cannot access 'op': {e}")
            return None

    if _OSCOUT is None:
        try:
            _OSCOUT = op('/project1/io/oscout1')
        except Exception as e:
            print(f"{_LOG_PREFIX} ERROR: Cannot find OSC output: {e}")
    return _OSCOUT


def _send_osc(address: str, *args) -> bool:
    """Send OSC message to Eos."""
    osc_op = _get_osc_operator()
    if not osc_op:
        return False

    try:
        # TouchDesigner's sendOSC expects a list of values
        values = list(args) if args else []
        osc_op.sendOSC(address, values)
        # Uncomment for debugging:
        # print(f"{_LOG_PREFIX} OSC → {address} {values}")
        return True
    except Exception as e:
        print(f"{_LOG_PREFIX} ERROR sending OSC {address}: {e}")
        return False


def _should_send(sub_key: str, new_level: float) -> bool:
    """
    Check if we should send an OSC update based on:
    - Significant level change (>1%)
    - Minimum time interval between sends
    """
    now = time.time()

    # Check level change
    last_level = _last_levels.get(sub_key, -999)
    if abs(new_level - last_level) < MIN_LEVEL_CHANGE:
        return False

    # Check time interval
    last_time = _last_send_time.get(sub_key, 0)
    if (now - last_time) < MIN_SEND_INTERVAL:
        return False

    return True


def _apply_s2l_params(
    raw_value: float,
    sensitivity: float = 100.0,
    threshold: float = 0.0,
    lag_ms: float = 0.0,
    min_hold_s: float = 0.0
) -> float:
    """
    Apply S2L parameters to raw audio value.

    Args:
        raw_value: Audio analysis value (0.0-1.0)
        sensitivity: Gain multiplier (0-100%)
        threshold: Minimum trigger level (0-100%)
        lag_ms: Smoothing time (0-500ms) - NOT IMPLEMENTED YET
        min_hold_s: Minimum hold time (0-8s) - NOT IMPLEMENTED YET

    Returns:
        Processed value (0.0-1.0)
    """
    # Apply sensitivity (gain)
    value = raw_value * (sensitivity / 100.0)

    # Apply threshold
    threshold_norm = threshold / 100.0
    if value < threshold_norm:
        value = 0.0
    else:
        # Rescale above threshold
        value = (value - threshold_norm) / (1.0 - threshold_norm)

    # Clamp to 0-1
    value = max(0.0, min(1.0, value))

    # TODO: Implement lag (smoothing)
    # TODO: Implement min_hold

    return value


def _get_audio_value(chop_op, channel_name: str) -> Optional[float]:
    """Get a channel value from audio_analysis CHOP."""
    try:
        chan = chop_op[channel_name]
        if chan:
            return float(chan.eval())
    except Exception as e:
        print(f"{_LOG_PREFIX} ERROR reading channel {channel_name}: {e}")
    return None


def _get_instance_params(params_table, instance_name: str) -> Optional[Dict[str, float]]:
    """
    Get S2L parameters for a specific instance from audio_params_table.

    Returns dict with keys: Sensitivity, Threshold, LowCut_Hz, HighCut_Hz, Lag_ms, MinHold_s
    """
    try:
        # Find row for this instance
        for row in range(1, params_table.numRows):
            if params_table[row, 0].val == instance_name:
                return {
                    'Sensitivity': float(params_table[row, 1].val or 100),
                    'Threshold': float(params_table[row, 2].val or 0),
                    'LowCut_Hz': float(params_table[row, 3].val or 20),
                    'HighCut_Hz': float(params_table[row, 4].val or 8000),
                    'Lag_ms': float(params_table[row, 5].val or 0),
                    'MinHold_s': float(params_table[row, 6].val or 0),
                }
    except Exception as e:
        print(f"{_LOG_PREFIX} ERROR getting params for {instance_name}: {e}")

    return None


def send_submaster_level(sub_number: int, level: float) -> bool:
    """
    Send 'Sub <n> At <level>' to Eos.

    Args:
        sub_number: Submaster number (1-999)
        level: Level as float (0.0-1.0) for Eos
    """
    if not 1 <= sub_number <= 999:
        print(f"{_LOG_PREFIX} ERROR: Invalid submaster number {sub_number}")
        return False

    # Clamp to 0.0-1.0 (Eos expects this range)
    if not 0.0 <= level <= 1.0:
        level = max(0.0, min(1.0, level))

    # Eos OSC format: /eos/sub/<n> <level>
    # Level must be 0.0-1.0 (not percentage!)
    address = f"/eos/sub/{sub_number}"
    return _send_osc(address, level)


def send_cue_go(cuelist: int, cue: Optional[float] = None) -> bool:
    """
    Send 'Cue <cuelist> <cue> Go' to Eos.

    Args:
        cuelist: Cuelist number
        cue: Optional specific cue number (if None, advances current cue)
    """
    # Eos OSC format: /eos/cue/<cuelist>/fire or /eos/cue/<cuelist>/<cue>/fire
    if cue is not None:
        address = f"/eos/cue/{cuelist}/{cue}/fire"
    else:
        address = f"/eos/cue/{cuelist}/fire"

    return _send_osc(address)


def process_audio_to_subs(
    audio_analysis_op,
    audio_params_table_op,
    submaster_mapping: Dict[str, int]
) -> None:
    """
    Main processing function: reads audio analysis, applies S2L params, sends to Eos.

    Args:
        audio_analysis_op: The audio_analysis CHOP operator
        audio_params_table_op: The audio_params_table DAT operator
        submaster_mapping: Dict mapping audio channels to submaster numbers
                          e.g. {'low': 1, 'mid': 2, 'high': 3, 'kick': 4}

    Example:
        process_audio_to_subs(
            op('audio_analysis'),
            op('audio_params_table'),
            {'low': 1, 'mid': 2, 'high': 3, 'kick': 4, 'snare': 5}
        )
    """
    if not audio_analysis_op or not audio_params_table_op:
        return

    now = time.time()

    for audio_channel, sub_number in submaster_mapping.items():
        # Read raw audio value
        raw_value = _get_audio_value(audio_analysis_op, audio_channel)
        if raw_value is None:
            continue

        # Get S2L parameters (use first instance for now - TODO: per-instance mapping)
        # For now, we'll use S2L_UNIT_1 params for all channels
        params = _get_instance_params(audio_params_table_op, 'S2L_UNIT_1')
        if params is None:
            # Use defaults if no params found
            params = {
                'Sensitivity': 100.0,
                'Threshold': 0.0,
                'Lag_ms': 0.0,
                'MinHold_s': 0.0
            }

        # Apply S2L parameters
        processed_value = _apply_s2l_params(
            raw_value,
            sensitivity=params['Sensitivity'],
            threshold=params['Threshold'],
            lag_ms=params['Lag_ms'],
            min_hold_s=params['MinHold_s']
        )

        # Clamp to 0.0-1.0 (Eos range)
        level = max(0.0, min(1.0, processed_value))

        # Check if we should send
        sub_key = f"sub_{sub_number}"
        if _should_send(sub_key, level):
            if send_submaster_level(sub_number, level):
                _last_levels[sub_key] = level
                _last_send_time[sub_key] = now


# Convenience function for single channel mapping
def map_audio_channel_to_sub(
    audio_analysis_op,
    audio_params_table_op,
    channel_name: str,
    sub_number: int,
    instance_name: str = 'S2L_UNIT_1'
) -> None:
    """
    Map a single audio channel to a submaster.

    Example:
        map_audio_channel_to_sub(op('audio_analysis'), op('audio_params_table'), 'kick', 10)
    """
    raw_value = _get_audio_value(audio_analysis_op, channel_name)
    if raw_value is None:
        return

    params = _get_instance_params(audio_params_table_op, instance_name)
    if params is None:
        params = {'Sensitivity': 100.0, 'Threshold': 0.0, 'Lag_ms': 0.0, 'MinHold_s': 0.0}

    processed_value = _apply_s2l_params(
        raw_value,
        sensitivity=params['Sensitivity'],
        threshold=params['Threshold'],
        lag_ms=params['Lag_ms'],
        min_hold_s=params['MinHold_s']
    )

    level = max(0.0, min(1.0, processed_value))
    sub_key = f"sub_{sub_number}"

    if _should_send(sub_key, level):
        if send_submaster_level(sub_number, level):
            _last_levels[sub_key] = level
            _last_send_time[sub_key] = time.time()
