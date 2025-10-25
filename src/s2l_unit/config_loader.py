"""Helpers to read configuration files for S2L_UNIT."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List

from .dmx_map import DMX_SLOTS_PER_INSTANCE, parameter_by_name, parameters
from .models import Defaults, InstanceDefinition

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config" / "s2l_unit"
INSTANCES_FILE = CONFIG_DIR / "instances.csv"
DEFAULTS_FILE = CONFIG_DIR / "defaults.json"

_instances_cache: List[InstanceDefinition] | None = None
_defaults_cache: Defaults | None = None


def _to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_instance(row: Dict[str, str]) -> InstanceDefinition:
    return InstanceDefinition(
        instance=row["instance"],
        enabled=_to_bool(row.get("enabled", "true")),
        universe=int(row.get("universe", "1")),
        start_address=int(row.get("start_address", "1")),
        eos_ip=row.get("eos_ip", "127.0.0.1"),
        description=row.get("description") or None,
    )


def _validate_slots(instances: List[InstanceDefinition]) -> None:
    for inst in instances:
        start, end = inst.dmx_range(DMX_SLOTS_PER_INSTANCE)
        if start < 1:
            raise ValueError(
                f"Instance {inst.instance}: start address must be >= 1 (is {start})"
            )
        if end > 512:
            raise ValueError(
                f"Instance {inst.instance}: DMX range {start}-{end} exceeds universe (max 512)"
            )


def load_instances(force_reload: bool = False) -> List[InstanceDefinition]:
    """Return all S2L instances defined in the CSV file."""
    global _instances_cache
    if _instances_cache is not None and not force_reload:
        return _instances_cache

    if not INSTANCES_FILE.exists():
        raise FileNotFoundError(f"S2L instances.csv missing: {INSTANCES_FILE}")

    with INSTANCES_FILE.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = [
            row for row in reader if any((value or "").strip() for value in row.values())
        ]

    instances = [_parse_instance(row) for row in rows]
    _validate_slots(instances)
    _instances_cache = instances
    return instances


def load_defaults(force_reload: bool = False) -> Defaults:
    """Return global default values for S2L."""
    global _defaults_cache
    if _defaults_cache is not None and not force_reload:
        return _defaults_cache

    if not DEFAULTS_FILE.exists():
        raise FileNotFoundError(f"S2L defaults.json missing: {DEFAULTS_FILE}")

    with DEFAULTS_FILE.open("r", encoding="utf-8") as fh:
        defaults: Defaults = json.load(fh)

    _defaults_cache = defaults
    return defaults


__all__ = [
    "CONFIG_DIR",
    "DEFAULTS_FILE",
    "DMX_SLOTS_PER_INSTANCE",
    "INSTANCES_FILE",
    "load_defaults",
    "load_instances",
    "parameter_by_name",
    "parameters",
]
