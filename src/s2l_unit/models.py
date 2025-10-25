"""Data models for the S2L_UNIT subsystem."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class ParameterDefinition:
    """Describe a single S2L parameter provided via DMX."""

    name: str
    dmx_slot_start: int
    dmx_slot_count: int
    value_range: Tuple[int, int]
    home_value: int
    description: str


@dataclass(frozen=True)
class InstanceDefinition:
    """CSV configuration row representing one S2L instance."""

    instance: str
    enabled: bool
    universe: int
    start_address: int
    eos_ip: str
    description: str | None = None

    def dmx_range(self, slots_per_instance: int) -> Tuple[int, int]:
        """Return (start, end) DMX slot numbers for this instance."""
        start = self.start_address
        end = start + slots_per_instance - 1
        return start, end


Defaults = Dict[str, Any]
