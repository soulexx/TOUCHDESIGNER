"""Utilities to decode S2L_UNIT parameter data from DMX universes."""

from __future__ import annotations

from typing import Dict, Iterable, Mapping, MutableMapping

from .config_loader import DMX_SLOTS_PER_INSTANCE
from .dmx_map import ParameterDefinition, parameters
from .models import InstanceDefinition


class DMXBufferError(ValueError):
    """Raised when the DMX buffer does not contain the expected data."""


def _ensure_length(buffer: bytes, offset: int, slots: int) -> None:
    required = offset + slots
    if required > len(buffer):
        raise DMXBufferError(
            f"DMX buffer too short: need {required} slots, buffer has {len(buffer)}"
        )


def _decode_uint16(coarse: int, fine: int) -> int:
    """Combine coarse/fine DMX slots into a 16-bit integer (MSB first)."""
    return (coarse << 8) | fine


def _scale_if_needed(raw: int, param: ParameterDefinition, max_raw: int) -> int:
    """Return raw value or scale it into the declared parameter range."""
    min_val, max_val = param.value_range
    if max_raw <= 0:
        return raw
    span = max_val - min_val
    if span <= 0:
        return max(min_val, min(max_val, raw))
    scaled = min_val + (raw / max_raw) * span
    if scaled < min_val:
        return int(min_val)
    if scaled > max_val:
        return int(max_val)
    return int(round(scaled))


def decode_parameter(buffer: bytes, param: ParameterDefinition, offset: int, *, scaling: bool = True) -> int:
    """Decode a single parameter from the DMX buffer."""
    slot_index = offset + param.dmx_slot_start - 1
    if param.dmx_slot_count == 1:
        _ensure_length(buffer, slot_index, 1)
        raw = buffer[slot_index]
        return _scale_if_needed(raw, param, 255) if scaling else raw

    if param.dmx_slot_count == 2:
        _ensure_length(buffer, slot_index, 2)
        # Standard DMX 16-bit: MSB first (coarse), LSB second (fine)
        coarse = buffer[slot_index]      # First byte = MSB (coarse/high byte)
        fine = buffer[slot_index + 1]    # Second byte = LSB (fine/low byte)
        raw = _decode_uint16(coarse, fine)
        return _scale_if_needed(raw, param, 65535) if scaling else raw

    raise DMXBufferError(
        f"Unsupported slot count {param.dmx_slot_count} for parameter {param.name}"
    )


def decode_instance(
    buffer: bytes,
    instance: InstanceDefinition,
    *,
    slots_per_instance: int | None = None,
    scaling: bool = True,
) -> Dict[str, int]:
    """Decode all parameters for one instance from the DMX buffer."""
    slots = slots_per_instance or DMX_SLOTS_PER_INSTANCE
    offset = instance.start_address - 1
    _ensure_length(buffer, offset, slots)

    values: Dict[str, int] = {}
    for param in parameters():
        values[param.name] = decode_parameter(buffer, param, offset, scaling=scaling)
    return values


def decode_universe(
    buffer: bytes,
    instances: Iterable[InstanceDefinition],
    *,
    slots_per_instance: int | None = None,
    scaling: bool = True,
) -> Dict[str, Dict[str, int]]:
    """Decode a full list of instances that share the same DMX universe."""
    slots = slots_per_instance or DMX_SLOTS_PER_INSTANCE
    result: Dict[str, Dict[str, int]] = {}

    for inst in instances:
        result[inst.instance] = decode_instance(buffer, inst, slots_per_instance=slots, scaling=scaling)

    return result


def apply_defaults(
    values: MutableMapping[str, int],
    defaults: Mapping[str, Mapping[str, int]],
    *,
    section: str,
) -> None:
    """Fill missing keys from defaults[section] if they are absent."""
    defaults_section = defaults.get(section, {})
    for key, fallback in defaults_section.items():
        values.setdefault(key, fallback)
