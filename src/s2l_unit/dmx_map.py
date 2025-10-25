"""Central DMX parameter map for S2L_UNIT."""

from __future__ import annotations

from typing import Iterable, Tuple

from .models import ParameterDefinition

DMX_SLOTS_PER_INSTANCE = 19

# Slots follow the sACN payload order: playback, audio, FX.
_PARAMETERS: tuple[ParameterDefinition, ...] = (
    ParameterDefinition(
        name="Submaster",
        dmx_slot_start=1,
        dmx_slot_count=2,
        value_range=(1, 999),
        home_value=1,
        description="16-bit target submaster (coarse slot first, fine second)",
    ),
    ParameterDefinition(
        name="Cuelist",
        dmx_slot_start=3,
        dmx_slot_count=2,
        value_range=(1, 999),
        home_value=1,
        description="16-bit cuelist identifier",
    ),
    ParameterDefinition(
        name="StartCue",
        dmx_slot_start=5,
        dmx_slot_count=2,
        value_range=(0, 999),
        home_value=0,
        description="16-bit first cue in playback range",
    ),
    ParameterDefinition(
        name="EndCue",
        dmx_slot_start=7,
        dmx_slot_count=2,
        value_range=(0, 999),
        home_value=0,
        description="16-bit last cue in playback range",
    ),
    ParameterDefinition(
        name="Mode",
        dmx_slot_start=9,
        dmx_slot_count=2,
        value_range=(0, 1256),
        home_value=0,
        description="16-bit playback mode (0-5 auto, 1001+ bars)",
    ),
    ParameterDefinition(
        name="Sensitivity",
        dmx_slot_start=11,
        dmx_slot_count=1,
        value_range=(0, 100),
        home_value=50,
        description="Audio sensitivity 0-100",
    ),
    ParameterDefinition(
        name="Threshold",
        dmx_slot_start=12,
        dmx_slot_count=1,
        value_range=(0, 100),
        home_value=40,
        description="Trigger threshold 0-100",
    ),
    ParameterDefinition(
        name="LowCut_Hz",
        dmx_slot_start=13,
        dmx_slot_count=1,
        value_range=(20, 300),
        home_value=120,
        description="Audio low-cut in Hz",
    ),
    ParameterDefinition(
        name="HighCut_Hz",
        dmx_slot_start=14,
        dmx_slot_count=1,
        value_range=(2000, 8000),
        home_value=3500,
        description="Audio high-cut in Hz",
    ),
    ParameterDefinition(
        name="Lag_ms",
        dmx_slot_start=15,
        dmx_slot_count=1,
        value_range=(0, 500),
        home_value=150,
        description="Smoothing / holdback in milliseconds",
    ),
    ParameterDefinition(
        name="MinHold_s",
        dmx_slot_start=16,
        dmx_slot_count=1,
        value_range=(0, 8),
        home_value=6,
        description="Minimum hold time in seconds",
    ),
    ParameterDefinition(
        name="FX_Select",
        dmx_slot_start=17,
        dmx_slot_count=2,
        value_range=(1, 65535),
        home_value=1,
        description="16-bit FX preset identifier",
    ),
    ParameterDefinition(
        name="FX_Auto",
        dmx_slot_start=19,
        dmx_slot_count=1,
        value_range=(0, 255),
        home_value=0,
        description="Auto/beat behaviour (0=off,1=beat,2-255=auto)",
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
