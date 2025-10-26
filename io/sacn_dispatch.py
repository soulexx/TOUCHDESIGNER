"""Glue between sACN DMX input and the S2L manager."""

from __future__ import annotations

from typing import Dict

import s2l_unit as s2l

# TouchDesigner path to the manager DAT/COMP that handles decoded data.
# Adjust to your actual dispatcher DAT location.
MANAGER_DAT_PATH = "/project1/src/s2l_manager/dispatcher"


DEBUG_RAW = False

# Performance: Cache instances per universe to avoid reloading config every frame
_instances_cache: Dict[int, list] = {}
# Performance: Cache defaults to avoid reloading config every frame
_defaults_cache: Dict[str, Dict[str, int]] | None = None


def _instances_for_universe(universe: int) -> list[s2l.InstanceDefinition]:
    if universe not in _instances_cache:
        _instances_cache[universe] = [
            inst
            for inst in s2l.load_instances()
            if inst.enabled and inst.universe == universe
        ]
    return _instances_cache[universe]


def _get_defaults() -> Dict[str, Dict[str, int]]:
    """Get defaults with caching to avoid file I/O every frame."""
    global _defaults_cache
    if _defaults_cache is None:
        _defaults_cache = s2l.load_defaults()
    return _defaults_cache


def handle_universe(payload: bytes, universe: int) -> None:
    """Decode DMX payload for a universe and forward it to the manager."""
    if not payload:
        return

    instances = _instances_for_universe(universe)
    if not instances:
        return

    if DEBUG_RAW:
        # Show first 20 bytes of payload
        first_bytes = [payload[i] if i < len(payload) else None for i in range(20)]
        print(f"[sacn_dispatch] Payload first 20 bytes: {first_bytes}")

        for inst in instances:
            start = inst.start_address - 1
            print(f"[sacn_dispatch] Instance {inst.instance}: start_address={inst.start_address}, offset={start}")
            coarse = payload[start] if start < len(payload) else None
            fine = payload[start + 1] if start + 1 < len(payload) else None
            print(f"[sacn_dispatch] raw bytes {inst.instance}: payload[{start}]={coarse}, payload[{start+1}]={fine}")

    try:
        values: Dict[str, Dict[str, int]] = s2l.decode_universe(payload, instances, scaling=False)
    except s2l.DMXBufferError as exc:
        print(f"[sacn_dispatch] invalid DMX buffer: {exc}")
        return

    defaults = _get_defaults()
    target = op(MANAGER_DAT_PATH)  # type: ignore[name-defined]
    if not target:
        print(f"[sacn_dispatch] manager not found at {MANAGER_DAT_PATH}")
        return

    update = getattr(target.module, "update_from_dmx", None)
    if not callable(update):
        print(f"[sacn_dispatch] manager at {MANAGER_DAT_PATH} missing update_from_dmx()")
        return

    update(universe, values, defaults)
