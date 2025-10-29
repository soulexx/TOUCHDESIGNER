"""
Auto-Cue Engine for S2L_UNIT System

Manages cue selection, firing, and history for automatic cue playback.

Modes:
- OFF (CH15 = 0-84): No auto-cue, submaster control only
- TIMER (CH15 = 85-169): Time-based random cue firing
- AUTOCUE (CH15 = 170-255): Music-driven cue firing with section detection

Architecture:
- Reads cue pool from EOS via DMX (CH3-8: Cuelist, StartCue, EndCue)
- Reads behavior parameters from DMX (CH15-19)
- Uses music_analyzer for section detection and song changes
- Maintains cue history per unit (no direct repeats, sane repetition over time)
- Fires cues via OSC to EOS
"""

from __future__ import annotations
from typing import Dict, List, Optional, Set
import time
import random

_LOG_PREFIX = "[auto_cue_engine]"
print(f"{_LOG_PREFIX} module loaded")

# Import TouchDesigner's op function
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

# Per-unit state
_unit_states: Dict[str, Dict] = {}
"""
Structure:
{
    'S2L_UNIT_1': {
        'mode': 'TIMER',                  # OFF, TIMER, AUTOCUE
        'current_cue': 27,                # Currently active cue
        'cue_history': [27, 23, 29],      # Last N cues (for anti-repeat)
        'last_fire_time': timestamp,      # When last cue was fired
        'last_switch_time': timestamp,    # When last mode switch happened
        'timer_next_fire': timestamp,     # Next scheduled fire (TIMER mode)
        'cuelist': 5,                     # Current cuelist
        'start_cue': 20,                  # Pool start
        'end_cue': 35,                    # Pool end
    },
    ...
}
"""

# Section-to-Cue mapping (per song)
# Each song gets 3 cues assigned: one for REFRAIN, one for STROPHE, one for BREAK


# ============================================================================
# PARAMETER SCALING (DMX to real units)
# ============================================================================

def _scale_ch16(dmx_value: int) -> float:
    """Scale CH16 (0-255) to seconds (1-100s)."""
    return 1.0 + (dmx_value / 255.0) * 99.0


def _scale_ch17(dmx_value: int) -> float:
    """Scale CH17 (0-255) to seconds (1-100s)."""
    return 1.0 + (dmx_value / 255.0) * 99.0


def _scale_ch18(dmx_value: int) -> float:
    """Scale CH18 (0-255) to milliseconds (0-2550ms)."""
    return dmx_value * 10.0


def _scale_ch19(dmx_value: int) -> float:
    """Scale CH19 (0-255) to seconds (1-990s)."""
    return 1.0 + (dmx_value / 255.0) * 989.0


def _decode_advance_mode(dmx_value: int) -> str:
    """Decode CH15 (AdvanceMode) to mode string.

    Args:
        dmx_value: 0-255

    Returns:
        "OFF", "TIMER", or "AUTOCUE"
    """
    if dmx_value <= 84:
        return "OFF"
    elif dmx_value <= 169:
        return "TIMER"
    else:
        return "AUTOCUE"


# ============================================================================
# OSC COMMUNICATION
# ============================================================================

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


def _fire_cue(cuelist: int, cue: int) -> bool:
    """Fire a specific cue in a cuelist via OSC on User 2.

    Args:
        cuelist: Cuelist number
        cue: Cue number

    Returns:
        True if OSC was sent successfully
    """
    address = f"/eos/user/2/cue/{cuelist}/{cue}/fire"
    success = _send_osc(address)
    if success:
        print(f"{_LOG_PREFIX} Fired cue {cue} in cuelist {cuelist} (User 2)")
    return success


# ============================================================================
# PARAMETER EXTRACTION
# ============================================================================

def _get_unit_params(values_table, instance_name: str) -> Optional[Dict]:
    """Extract all relevant parameters for a unit from values table.

    Args:
        values_table: DAT table with decoded DMX parameters
        instance_name: Unit name (e.g., "S2L_UNIT_1")

    Returns:
        Dict with all parameters, or None if unit not found
    """
    if not values_table or values_table.numRows < 2:
        return None

    params = {}
    for row in range(1, values_table.numRows):
        instance = values_table[row, 0].val
        if instance == instance_name:
            param_name = values_table[row, 1].val
            param_value = values_table[row, 2].val
            try:
                params[param_name] = int(param_value)
            except:
                params[param_name] = param_value

    # Check required parameters
    required = ['Cuelist', 'StartCue', 'EndCue', 'AutoCueMode', 'MinSectionTime',
                'CooldownAfterSwitch', 'RequireConfidenceFrames', 'SongCooldownTime']
    if not all(key in params for key in required):
        return None

    return params


# ============================================================================
# CUE SELECTION & HISTORY
# ============================================================================

def _get_or_create_section_mapping(unit_name: str, cuelist: int, start_cue: int, end_cue: int) -> Dict[str, int]:
    """Get or create section-to-cue mapping for current song.

    Each song gets 3 cues assigned:
    - REFRAIN → one cue
    - STROPHE → one cue
    - BREAK → one cue

    Args:
        unit_name: Unit identifier
        cuelist: Current cuelist number
        start_cue: Pool start (inclusive)
        end_cue: Pool end (inclusive)

    Returns:
        Dict with keys: REFRAIN, STROPHE, BREAK
    """
    global _unit_states

    if start_cue > end_cue or start_cue == 0:
        return {}

    # Get state
    if unit_name not in _unit_states:
        _unit_states[unit_name] = {
            'section_mapping': None,  # Dict: section_name -> cue_number
            'last_pool': None,  # Last known pool (cuelist, start, end)
        }

    state = _unit_states[unit_name]

    # Check if pool has changed (operator changed CH3-8 in EOS)
    current_pool = (cuelist, start_cue, end_cue)
    last_pool = state.get('last_pool')

    pool_changed = (last_pool is not None and last_pool != current_pool)

    if pool_changed:
        print(f"{_LOG_PREFIX} {unit_name}: Pool changed from {last_pool} to {current_pool} - resetting mapping")
        state['section_mapping'] = None

    # Check if we need to create new mapping (first time, after song change, or pool change)
    if state.get('section_mapping') is None:
        full_pool = list(range(start_cue, end_cue + 1))
        pool_size = len(full_pool)

        if pool_size < 3:
            # Not enough cues, assign what we have
            mapping = {}
            sections = ['REFRAIN', 'STROPHE', 'BREAK']
            for i, section in enumerate(sections):
                if i < pool_size:
                    mapping[section] = full_pool[i]
                else:
                    mapping[section] = full_pool[0]  # Reuse first cue
            print(f"{_LOG_PREFIX} {unit_name}: Pool too small ({pool_size} cues), reusing cues")
        else:
            # Select 3 random cues from pool (one for each section)
            selected_cues = random.sample(full_pool, 3)
            mapping = {
                'REFRAIN': selected_cues[0],
                'STROPHE': selected_cues[1],
                'BREAK': selected_cues[2],
            }

        state['section_mapping'] = mapping
        state['last_pool'] = current_pool
        print(f"{_LOG_PREFIX} {unit_name}: Section mapping: REFRAIN→{mapping['REFRAIN']}, STROPHE→{mapping['STROPHE']}, BREAK→{mapping['BREAK']}")

    return state['section_mapping']


def _get_cue_for_section(unit_name: str, section: str, cuelist: int, start_cue: int, end_cue: int) -> Optional[int]:
    """Get the cue number assigned to this section for current song.

    Args:
        unit_name: Unit identifier
        section: Section name (REFRAIN, STROPHE, BREAK)
        cuelist: Current cuelist number
        start_cue: Pool start
        end_cue: Pool end

    Returns:
        Cue number, or None if invalid
    """
    mapping = _get_or_create_section_mapping(unit_name, cuelist, start_cue, end_cue)

    if not mapping:
        return None

    return mapping.get(section)


def _clear_history(unit_name: str):
    """Clear section mapping for a unit (used on song change).

    Forces new section-to-cue mapping on next transition.
    """
    global _unit_states

    if unit_name in _unit_states:
        # Clear section mapping to force new assignment
        _unit_states[unit_name]['section_mapping'] = None
        print(f"{_LOG_PREFIX} 🎵 New song for {unit_name} - section mapping will be reset")


# ============================================================================
# MODE HANDLERS
# ============================================================================

def _process_off_mode(unit_name: str, params: Dict, current_time: float) -> bool:
    """Process OFF mode - do nothing.

    Returns:
        False (no cue fired)
    """
    return False


def _process_timer_mode(unit_name: str, params: Dict, current_time: float) -> bool:
    """Process TIMER mode - fire cues at regular intervals.

    Args:
        unit_name: Unit identifier
        params: Unit parameters from values table
        current_time: Current timestamp

    Returns:
        True if cue was fired
    """
    global _unit_states

    # Get or create state
    if unit_name not in _unit_states:
        _unit_states[unit_name] = {}

    state = _unit_states[unit_name]

    # Get parameters
    cuelist = params['Cuelist']
    start_cue = params['StartCue']
    end_cue = params['EndCue']
    interval_raw = params['MinSectionTime']  # CH16 = interval in Timer mode

    # Validate pool
    if cuelist == 0 or start_cue == 0 or end_cue == 0 or start_cue > end_cue:
        return False

    # Scale interval
    interval_sec = _scale_ch16(interval_raw)

    # Check if it's time to fire
    last_fire = state.get('last_fire_time', 0.0)
    time_since_fire = current_time - last_fire

    if time_since_fire < interval_sec:
        return False

    # Time to fire! Select next cue
    next_cue = _select_next_cue(unit_name, start_cue, end_cue)
    if next_cue is None:
        return False

    # Fire cue
    success = _fire_cue(cuelist, next_cue)

    if success:
        state['last_fire_time'] = current_time
        state['cuelist'] = cuelist
        state['start_cue'] = start_cue
        state['end_cue'] = end_cue
        return True

    return False


def _process_autocue_mode(
    unit_name: str,
    params: Dict,
    analyzer_output: Dict,
    current_time: float
) -> bool:
    """Process AUTOCUE mode - fire cues based on music analysis.

    Args:
        unit_name: Unit identifier
        params: Unit parameters from values table
        analyzer_output: Output from music_analyzer.analyze()
        current_time: Current timestamp

    Returns:
        True if cue was fired
    """
    global _unit_states

    # Get or create state
    if unit_name not in _unit_states:
        _unit_states[unit_name] = {}

    state = _unit_states[unit_name]

    # Get parameters
    cuelist = params['Cuelist']
    start_cue = params['StartCue']
    end_cue = params['EndCue']

    # Validate pool
    if cuelist == 0 or start_cue == 0 or end_cue == 0 or start_cue > end_cue:
        return False

    # Check if music analysis allows transition
    if not analyzer_output.get('allow_transition', False):
        return False

    # Get current section from analyzer
    current_section = analyzer_output.get('current_section', 'STROPHE')

    # Check cooldown (CH17) - but allow first fire or section change without cooldown
    cooldown_raw = params['CooldownAfterSwitch']
    cooldown_sec = _scale_ch17(cooldown_raw)

    last_fire = state.get('last_fire_time', 0.0)
    last_section = state.get('last_section_fired', None)
    time_since_fire = current_time - last_fire

    # If same section as last fired, respect cooldown
    if last_section == current_section and time_since_fire < cooldown_sec:
        return False

    # Get cue assigned to this section
    next_cue = _get_cue_for_section(unit_name, current_section, cuelist, start_cue, end_cue)
    if next_cue is None:
        return False

    # Fire cue
    success = _fire_cue(cuelist, next_cue)

    if success:
        state['last_fire_time'] = current_time
        state['last_section_fired'] = current_section
        state['cuelist'] = cuelist
        state['start_cue'] = start_cue
        state['end_cue'] = end_cue
        return True

    return False


# ============================================================================
# MAIN PROCESSING
# ============================================================================

def process_unit(
    unit_name: str,
    values_table,
    analyzer_output: Optional[Dict],
    current_time: float
) -> bool:
    """Process a single unit - main entry point.

    Args:
        unit_name: Unit identifier (e.g., "S2L_UNIT_1")
        values_table: DAT table with unit parameters
        analyzer_output: Output from music_analyzer.analyze() (for AutoCue mode)
        current_time: Current timestamp

    Returns:
        True if a cue was fired
    """
    # Get unit parameters
    params = _get_unit_params(values_table, unit_name)
    if not params:
        return False

    # Decode mode
    mode_raw = params.get('AutoCueMode', 0)
    mode = _decode_advance_mode(mode_raw)

    # Check for song change (clear history)
    # Use raw detection to reset mapping even if cooldown is active
    if analyzer_output and analyzer_output.get('new_song_detected_raw', False):
        _clear_history(unit_name)

    # Process based on mode
    if mode == "OFF":
        return _process_off_mode(unit_name, params, current_time)
    elif mode == "TIMER":
        return _process_timer_mode(unit_name, params, current_time)
    elif mode == "AUTOCUE":
        if analyzer_output is None:
            return False
        return _process_autocue_mode(unit_name, params, analyzer_output, current_time)

    return False


def process_all_units(
    values_table,
    analyzer_output: Optional[Dict],
    enabled_units: Optional[List[str]] = None
) -> int:
    """Process all enabled units.

    Args:
        values_table: DAT table with unit parameters
        analyzer_output: Output from music_analyzer (for AutoCue mode)
        enabled_units: List of unit names to process (if None, auto-detect from table)

    Returns:
        Number of units that fired cues
    """
    if not values_table or values_table.numRows < 2:
        return 0

    current_time = time.time()

    # Auto-detect units if not provided
    if enabled_units is None:
        enabled_units_set: Set[str] = set()
        for row in range(1, values_table.numRows):
            instance = values_table[row, 0].val
            enabled_units_set.add(instance)
        enabled_units = sorted(enabled_units_set)

    # Process each unit
    fired_count = 0
    for unit_name in enabled_units:
        if process_unit(unit_name, values_table, analyzer_output, current_time):
            fired_count += 1

    return fired_count


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_unit_state(unit_name: str) -> Dict:
    """Get current state for a unit (for debugging)."""
    global _unit_states
    return _unit_states.get(unit_name, {})


def clear_all_history():
    """Clear history for all units."""
    global _unit_states
    for unit_name in _unit_states:
        _unit_states[unit_name]['cue_history'].clear()
    print(f"{_LOG_PREFIX} Cleared all history")


def reset():
    """Reset all engine state."""
    global _unit_states
    _unit_states.clear()
    print(f"{_LOG_PREFIX} Engine reset")
