"""Central DMX parameter map for S2L_UNIT - NEW 14-channel structure.

This is the corrected patch definition:
- 14 DMX channels per unit (reduced from 19)
- Clearer structure: 8 channels for 16-bit selection, 6 channels for 8-bit values/modes
- Better audio envelope: Attack/Hold/Release instead of scattered parameters
- Band selection via DMX ranges
"""

from __future__ import annotations

from typing import Iterable, Tuple

from .models import ParameterDefinition

DMX_SLOTS_PER_INSTANCE = 19  # Reduced from 19

# NEW STRUCTURE:
# DMX 1-8:  16-bit selection parameters (High/Low byte pairs)
# DMX 9-14: 8-bit values/modes

_PARAMETERS: tuple[ParameterDefinition, ...] = (
    # ========== 16-bit Selection Parameters (Channels 1-8) ==========
    ParameterDefinition(
        name="Submaster",
        dmx_slot_start=1,
        dmx_slot_count=2,
        value_range=(0, 999),
        home_value=0,
        description="16-bit submaster selection (which submaster to use, NOT level!)",
    ),
    ParameterDefinition(
        name="Cuelist",
        dmx_slot_start=3,
        dmx_slot_count=2,
        value_range=(0, 999),
        home_value=0,
        description="16-bit cuelist selection (which list to use)",
    ),
    ParameterDefinition(
        name="StartCue",
        dmx_slot_start=5,
        dmx_slot_count=2,
        value_range=(0, 999),
        home_value=0,
        description="16-bit start cue number in selected cuelist",
    ),
    ParameterDefinition(
        name="EndCue",
        dmx_slot_start=7,
        dmx_slot_count=2,
        value_range=(0, 999),
        home_value=0,
        description="16-bit end cue number in selected cuelist",
    ),

    # ========== 8-bit Value Parameters (Channels 9-19) ==========
    # Audio Envelope Parameters (CH 9-12)
    ParameterDefinition(
        name="Threshold",
        dmx_slot_start=9,
        dmx_slot_count=1,
        value_range=(0, 255),
        home_value=128,
        description="Audio trigger threshold (0=most sensitive, 255=least sensitive)",
    ),
    ParameterDefinition(
        name="Attack",
        dmx_slot_start=10,
        dmx_slot_count=1,
        value_range=(0, 255),
        home_value=64,
        description="Attack time (0=fast attack, 255=slow attack)",
    ),
    ParameterDefinition(
        name="Hold",
        dmx_slot_start=11,
        dmx_slot_count=1,
        value_range=(0, 255),
        home_value=128,
        description="Hold time (how long peak is held)",
    ),
    ParameterDefinition(
        name="Release",
        dmx_slot_start=12,
        dmx_slot_count=1,
        value_range=(0, 255),
        home_value=128,
        description="Release time (0=fast release, 255=slow release)",
    ),

    # Audio Mode Parameters (CH 13-14)
    ParameterDefinition(
        name="FX_Polarity",
        dmx_slot_start=13,
        dmx_slot_count=1,
        value_range=(0, 255),
        home_value=0,
        description="Submaster FX polarity: 0-127=normal, 128-255=inverted",
    ),
    ParameterDefinition(
        name="Band",
        dmx_slot_start=14,
        dmx_slot_count=1,
        value_range=(0, 255),
        home_value=0,
        description="Analysis band/mode: 0-41=low, 42-84=mid, 85-127=high, 128-169=smsd, 170-212=fmsd, 213-255=spectralCentroid",
    ),

    # Auto Cue Parameters (CH 15-19)
    ParameterDefinition(
        name="AutoCueMode",
        dmx_slot_start=15,
        dmx_slot_count=1,
        value_range=(0, 255),
        home_value=0,
        description="Auto cue start mode: 0-127=disabled, 128-255=enabled",
    ),
    ParameterDefinition(
        name="MinSectionTime",
        dmx_slot_start=16,
        dmx_slot_count=1,
        value_range=(0, 255),
        home_value=128,
        description="Minimum section time before auto-switching cues",
    ),
    ParameterDefinition(
        name="CooldownAfterSwitch",
        dmx_slot_start=17,
        dmx_slot_count=1,
        value_range=(0, 255),
        home_value=64,
        description="Cooldown time after cue switch",
    ),
    ParameterDefinition(
        name="RequireConfidenceFrames",
        dmx_slot_start=18,
        dmx_slot_count=1,
        value_range=(0, 255),
        home_value=32,
        description="Required confidence frames before cue switch",
    ),
    ParameterDefinition(
        name="SongCooldownTime",
        dmx_slot_start=19,
        dmx_slot_count=1,
        value_range=(0, 255),
        home_value=128,
        description="Cooldown time for song-level changes",
    ),
)

_PARAMETERS_BY_NAME = {param.name: param for param in _PARAMETERS}


def parameters() -> tuple[ParameterDefinition, ...]:
    """Return all parameters in DMX order."""
    return _PARAMETERS


def iter_parameters() -> Iterable[ParameterDefinition]:
    """Iterator over all parameter definitions."""
    return _PARAMETERS


def parameter_by_name(name: str) -> ParameterDefinition:
    """Return the parameter definition identified by name."""
    try:
        return _PARAMETERS_BY_NAME[name]
    except KeyError as exc:
        raise KeyError(f"Unknown S2L parameter: {name!r}") from exc


def dmx_span_for(name: str) -> Tuple[int, int]:
    """Return (start, end) DMX slot numbers for a parameter."""
    param = parameter_by_name(name)
    start = param.dmx_slot_start
    end = start + param.dmx_slot_count - 1
    return start, end


def decode_band_mode(raw_value: int) -> str:
    """Decode the Band parameter into a human-readable mode string.

    Args:
        raw_value: DMX value 0-255

    Returns:
        One of: "low", "mid", "high", "smsd", "fmsd", "spectralCentroid"
    """
    if 0 <= raw_value <= 41:
        return "low"
    elif 42 <= raw_value <= 84:
        return "mid"
    elif 85 <= raw_value <= 127:
        return "high"
    elif 128 <= raw_value <= 169:
        return "smsd"
    elif 170 <= raw_value <= 212:
        return "fmsd"
    elif 213 <= raw_value <= 255:
        return "spectralCentroid"
    else:
        return "unknown"


def decode_fx_polarity(raw_value: int) -> str:
    """Decode the FX_Polarity parameter into a human-readable string.

    Args:
        raw_value: DMX value 0-255

    Returns:
        One of: "normal", "inverted"
    """
    return "normal" if raw_value <= 127 else "inverted"
