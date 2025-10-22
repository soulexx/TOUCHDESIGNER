"""Utility for keeping a rolling log file with a fixed number of lines."""

from __future__ import annotations

import os
import time
from collections import deque
from pathlib import Path
from threading import Lock
from typing import Iterable, Optional, Union


PathLike = Union[str, Path]


class FileRingBuffer:
    """Maintain a rolling buffer of text lines mirrored to disk."""

    def __init__(
        self,
        path: PathLike,
        *,
        max_lines: int = 200,
        rotation_bytes: Optional[int] = 2 * 1024 * 1024,
        encoding: str = "utf-8",
        flush_interval: float = 0.25,
        persist: Optional[bool] = None,
    ) -> None:
        if max_lines <= 0:
            raise ValueError("max_lines must be greater than zero")

        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._max_lines = max_lines
        self._rotation_bytes = rotation_bytes
        self._encoding = encoding
        self._buffer = deque(maxlen=max_lines)
        self._lock = Lock()
        self._persist = self._resolve_persist(persist)
        self._flush_interval = (
            max(float(flush_interval), 0.0) if self._persist else 0.0
        )
        self._last_flush = 0.0
        self._dirty = False

        self._load_existing()

    # Public API ---------------------------------------------------------

    @property
    def path(self) -> Path:
        return self._path

    @property
    def max_lines(self) -> int:
        return self._max_lines

    def append(self, line: str) -> None:
        """Append a single line and flush to disk."""
        with self._lock:
            self._buffer.append(_ensure_newline(line))
            self._dirty = True
            self._flush_if_needed_locked()

    def extend(self, lines: Iterable[str]) -> None:
        """Append multiple lines."""
        with self._lock:
            for line in lines:
                self._buffer.append(_ensure_newline(line))
            self._dirty = True
            self._flush_if_needed_locked()

    def snapshot(self) -> str:
        """Return current buffer contents as a single string."""
        with self._lock:
            return "".join(self._buffer)

    def clear(self) -> None:
        """Reset buffer and truncate on disk."""
        with self._lock:
            self._buffer.clear()
            if self._persist:
                self._path.write_text("", encoding=self._encoding)
            self._dirty = False
            self._last_flush = time.perf_counter()

    # Internal helpers ---------------------------------------------------

    def _resolve_persist(self, override: Optional[bool]) -> bool:
        if override is not None:
            return bool(override)
        env = os.environ.get("TD_FILE_RING_PERSIST")
        if env is not None:
            return env.strip().lower() in {"1", "true", "yes", "on"}
        return False

    def _load_existing(self) -> None:
        if not self._persist or not self._path.exists():
            return
        try:
            lines = self._path.read_text(encoding=self._encoding).splitlines(True)
        except OSError:
            return
        for line in lines[-self._max_lines :]:
            self._buffer.append(line if line.endswith("\n") else f"{line}\n")

    def _flush_if_needed_locked(self, *, force: bool = False) -> None:
        if not self._dirty and not force:
            return
        now = time.perf_counter()
        if (
            not force
            and self._flush_interval > 0.0
            and (now - self._last_flush) < self._flush_interval
        ):
            return
        self._write_buffer_locked()
        self._last_flush = now
        self._dirty = False

    def _write_buffer_locked(self) -> None:
        if not self._persist:
            return
        self._maybe_rotate()
        try:
            self._path.write_text("".join(self._buffer), encoding=self._encoding)
        except OSError:
            # Suppress write errors to avoid crashing the TD callbacks; user can inspect logs.
            return

    def _maybe_rotate(self) -> None:
        if not self._persist:
            return
        if (
            self._rotation_bytes is None
            or self._rotation_bytes <= 0
            or not self._path.exists()
        ):
            return

        try:
            if self._path.stat().st_size <= self._rotation_bytes:
                return
        except OSError:
            return

        rotated = self._path.with_suffix(self._path.suffix + ".1")
        try:
            if rotated.exists():
                rotated.unlink()
            self._path.rename(rotated)
        except OSError:
            # If rotation fails, keep writing to the original file.
            pass

def _ensure_newline(line: str) -> str:
    return line if line.endswith("\n") else f"{line}\n"
