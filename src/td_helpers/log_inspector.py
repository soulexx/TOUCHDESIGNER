"""Utilities to inspect OSC/MIDI logs written by the TouchDesigner helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional


@dataclass
class LogEntry:
    timestamp: float
    text: str


def read_log(path: Path, *, limit: Optional[int] = None) -> Iterator[LogEntry]:
    """Yield entries from a log file newest-last."""
    if not path.exists():
        return iter(())
    count = 0
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split(" ", 1)
            try:
                ts = float(parts[0])
                rest = parts[1] if len(parts) > 1 else ""
            except (ValueError, IndexError):
                ts = 0.0
                rest = line
            yield LogEntry(timestamp=ts, text=rest)
            count += 1
            if limit and count >= limit:
                break


def filter_contains(entries: Iterable[LogEntry], needle: str) -> Iterator[LogEntry]:
    """Return entries containing the substring (case-insensitive)."""
    lowered = needle.lower()
    for entry in entries:
        if lowered in entry.text.lower():
            yield entry


def last_matching(path: Path, needle: str, limit: int = 50) -> Iterator[LogEntry]:
    """Convenience to read the last N entries and filter by substring."""
    lines = list(read_log(path))
    lines = lines[-limit:]
    return filter_contains(lines, needle)
