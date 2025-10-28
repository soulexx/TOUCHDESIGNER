"""
Per-Unit Audio Engine for S2L_UNIT system.

Architecture:
- Each S2L_UNIT independently controls ONE submaster
- Each unit selects its own audio band (low/mid/high/smsd/fmsd/spectralCentroid)
- Each unit has its own envelope (threshold/attack/hold/release)
- Each unit can be normal or inverted polarity

Flow per frame:
1. Read values table (DMX-decoded parameters for all units)
2. For each enabled unit:
   a. Get selected submaster number
   b. Get selected audio band
   c. Read audio level from audio_analysis CHOP
   d. Apply threshold
   e. Apply envelope (attack/hold/release)
   f. Apply polarity (normal/inverted)
   g. Send OSC to selected submaster
"""

from __future__ import annotations
from typing import Dict, Optional
import time

_LOG_PREFIX = "[audio_engine_perunit]"
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

# Import S2L_UNIT helpers
import sys
if 'C:/_DEV/TOUCHDESIGNER/src' not in sys.path:
    sys.path.insert(0, 'C:/_DEV/TOUCHDESIGNER/src')
from s2l_unit import dmx_map as s2l

# OSC output operator
_OSCOUT = None  # Will be set to op('/project1/io/oscout1')

# Per-unit envelope state
_unit_states: Dict[str, Dict] = {}
"""
Structure:
{
    'S2L_UNIT_1': {
        'triggered': False,
        'envelope_value': 0.0,
        'attack_start_time': 0.0,
        'hold_start_time': 0.0,
        'release_start_time': 0.0,
        'last_osc_level': 0.0,
        'last_osc_time': 0.0
    },
    ...
}
"""

# Performance settings
MIN_LEVEL_CHANGE = 0.01  # Minimum change to trigger OSC send (1%)
MIN_SEND_INTERVAL = 0.05  # Minimum time between sends per sub (50ms)


def _get_osc_operator():
    """Lazy load OSC output operator."""
    global _OSCOUT, op

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
    osc = _get_osc_operator()
    if not osc:
        return False

    try:
        osc.sendOSC(address, args)
        return True
    except Exception as e:
        print(f"{_LOG_PREFIX} ERROR sending OSC {address}: {e}")
        return False


def _get_unit_params(values_table, instance_name: str) -> Optional[Dict[str, int]]:
    """Extract all parameters for a single unit from values table.

    Returns dict with keys: Submaster, Band, Threshold, Attack, Hold, Release, FX_Polarity
    """
    if not values_table or values_table.numRows < 2:
        return None

    params = {}
    for row in range(1, values_table.numRows):
        instance = values_table[row, 0].val
        if instance == instance_name:
            param_name = values_table[row, 1].val
            param_value = int(values_table[row, 2].val)
            params[param_name] = param_value

    # Check if we have required params
    required = ['Submaster', 'Band', 'Threshold', 'Attack', 'Hold', 'Release', 'FX_Polarity']
    if not all(key in params for key in required):
        return None

    return params


def _get_audio_value(audio_chop, band_name: str) -> float:
    """Read audio level for specified band from audio_analysis CHOP.

    Args:
        audio_chop: The audio_analysis CHOP operator
        band_name: One of: "low", "mid", "high", "smsd", "fmsd", "spectralCentroid"

    Returns:
        Audio level 0.0-1.0, or 0.0 if channel not found
    """
    if not audio_chop or audio_chop.numSamples == 0:
        return 0.0

    try:
        channel = audio_chop[band_name]
        if channel:
            return max(0.0, min(1.0, channel[0]))
    except:
        pass

    return 0.0


def _apply_envelope(
    unit_name: str,
    audio_level: float,
    threshold: int,
    attack: int,
    hold: int,
    release: int,
    current_time: float
) -> float:
    """Apply ADHR envelope to audio level.

    Args:
        unit_name: Unit identifier for state tracking
        audio_level: Raw audio level 0.0-1.0
        threshold: DMX threshold 0-255
        attack: DMX attack time 0-255
        hold: DMX hold time 0-255
        release: DMX release time 0-255
        current_time: Current time in seconds

    Returns:
        Envelope value 0.0-1.0
    """
    global _unit_states

    # Initialize unit state if needed
    if unit_name not in _unit_states:
        _unit_states[unit_name] = {
            'triggered': False,
            'envelope_value': 0.0,
            'attack_start_time': 0.0,
            'hold_start_time': 0.0,
            'release_start_time': 0.0,
        }

    state = _unit_states[unit_name]

    # Convert DMX values to time (0-255 → 0-2 seconds)
    threshold_normalized = threshold / 255.0
    attack_time = (attack / 255.0) * 2.0  # 0-2 seconds
    hold_time = (hold / 255.0) * 2.0
    release_time = (release / 255.0) * 2.0

    # Check if triggered
    triggered = audio_level > threshold_normalized

    if triggered and not state['triggered']:
        # New trigger: start attack phase
        state['triggered'] = True
        state['attack_start_time'] = current_time
        state['hold_start_time'] = 0.0
        state['release_start_time'] = 0.0

    elif not triggered and state['triggered']:
        # Trigger released: start release phase
        state['triggered'] = False
        state['release_start_time'] = current_time

    # Calculate envelope value based on phase
    if state['triggered']:
        # Attack or Hold phase
        time_since_attack = current_time - state['attack_start_time']

        if time_since_attack < attack_time:
            # Attack phase: ramp up
            if attack_time > 0:
                progress = time_since_attack / attack_time
                state['envelope_value'] = progress
            else:
                state['envelope_value'] = 1.0  # Instant attack

        else:
            # Hold phase: stay at 1.0
            if state['hold_start_time'] == 0.0:
                state['hold_start_time'] = current_time

            # Check if hold time has expired
            time_in_hold = current_time - state['hold_start_time']
            if time_in_hold >= hold_time:
                # Hold time expired, start release
                state['triggered'] = False
                state['release_start_time'] = current_time
                state['envelope_value'] = 1.0  # Start release from full level
            else:
                # Still in hold phase
                state['envelope_value'] = 1.0

    elif state['release_start_time'] > 0.0:
        # Release phase: ramp down
        time_since_release = current_time - state['release_start_time']

        if time_since_release < release_time:
            if release_time > 0:
                progress = 1.0 - (time_since_release / release_time)
                state['envelope_value'] = max(0.0, progress * state['envelope_value'])
            else:
                state['envelope_value'] = 0.0  # Instant release
        else:
            state['envelope_value'] = 0.0
            state['release_start_time'] = 0.0

    return state['envelope_value']


def _should_send_osc(unit_name: str, level: float, current_time: float) -> bool:
    """Check if OSC should be sent based on change detection."""
    global _unit_states

    if unit_name not in _unit_states:
        return True

    state = _unit_states[unit_name]
    last_level = state.get('last_osc_level', -1.0)  # -1 means never sent
    last_time = state.get('last_osc_time', 0.0)

    # Always send on first OSC for this unit
    if last_level < 0:
        return True

    # Check level change
    level_changed = abs(level - last_level) >= MIN_LEVEL_CHANGE

    # Check time interval
    time_passed = (current_time - last_time) >= MIN_SEND_INTERVAL

    return level_changed and time_passed


def process_unit(
    values_table,
    audio_chop,
    instance_name: str,
    current_time: float
) -> bool:
    """Process a single S2L_UNIT.

    Args:
        values_table: DAT table with unit parameters
        audio_chop: Audio analysis CHOP
        instance_name: Unit name (e.g., "S2L_UNIT_1")
        current_time: Current time in seconds

    Returns:
        True if OSC was sent, False otherwise
    """
    global _unit_states

    # Get unit parameters from values table
    params = _get_unit_params(values_table, instance_name)
    if not params:
        return False

    # Extract parameters
    submaster = params['Submaster']
    band_raw = params['Band']
    threshold = params['Threshold']
    attack = params['Attack']
    hold = params['Hold']
    release = params['Release']
    polarity_raw = params['FX_Polarity']

    # Skip if submaster is 0 (disabled)
    if submaster == 0:
        return False

    # Decode band name
    band_name = s2l.decode_band_mode(band_raw)
    if band_name == "unknown":
        return False

    # Get audio level for selected band
    audio_level = _get_audio_value(audio_chop, band_name)

    # Apply envelope
    envelope_value = _apply_envelope(
        instance_name,
        audio_level,
        threshold,
        attack,
        hold,
        release,
        current_time
    )

    # Apply polarity
    polarity = s2l.decode_fx_polarity(polarity_raw)
    if polarity == "inverted":
        envelope_value = 1.0 - envelope_value

    # Scale to 0-100 for Eos
    eos_level = envelope_value * 100.0

    # Send OSC if level changed
    if _should_send_osc(instance_name, eos_level, current_time):
        success = _send_osc(f"/eos/sub/{submaster}", eos_level)
        if success:
            # Update state
            if instance_name not in _unit_states:
                _unit_states[instance_name] = {}
            _unit_states[instance_name]['last_osc_level'] = eos_level
            _unit_states[instance_name]['last_osc_time'] = current_time
            return True

    return False


def process_all_units(values_table, audio_chop) -> int:
    """Process all enabled S2L_UNITs.

    Args:
        values_table: DAT table with unit parameters
        audio_chop: Audio analysis CHOP

    Returns:
        Number of units that sent OSC
    """
    if not values_table or values_table.numRows < 2:
        return 0

    current_time = time.time()
    sent_count = 0

    # Get unique instance names from values table
    instances = set()
    for row in range(1, values_table.numRows):
        instance = values_table[row, 0].val
        instances.add(instance)

    # Process each unit
    for instance_name in sorted(instances):
        if process_unit(values_table, audio_chop, instance_name, current_time):
            sent_count += 1

    return sent_count


def clear_states():
    """Clear all unit states (useful for testing)."""
    global _unit_states
    _unit_states.clear()
    print(f"{_LOG_PREFIX} All unit states cleared")


# Module-level test function
def test_single_unit(instance_name: str = "S2L_UNIT_1"):
    """Test processing for a single unit.

    Usage from textport:
        import audio_engine_perunit
        audio_engine_perunit.test_single_unit("S2L_UNIT_1")
    """
    global op
    if op is None:
        try:
            import __main__
            op = __main__.op
        except:
            print(f"{_LOG_PREFIX} ERROR: Not in TouchDesigner context")
            return

    values_table = op('/project1/src/s2l_manager/values')
    audio_chop = op('/project1/s2l_audio/fixutres/audio_analysis')

    if not values_table:
        print(f"{_LOG_PREFIX} ERROR: Cannot find values table")
        return

    if not audio_chop:
        print(f"{_LOG_PREFIX} ERROR: Cannot find audio_analysis CHOP")
        return

    current_time = time.time()
    success = process_unit(values_table, audio_chop, instance_name, current_time)

    if success:
        print(f"{_LOG_PREFIX} ✅ {instance_name} processed and OSC sent")
    else:
        print(f"{_LOG_PREFIX} ⚠️  {instance_name} processed but no OSC sent")

    # Show current params
    params = _get_unit_params(values_table, instance_name)
    if params:
        print(f"{_LOG_PREFIX} Parameters:")
        for key, val in params.items():
            print(f"  {key}: {val}")
