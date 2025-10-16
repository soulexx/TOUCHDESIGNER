"""Utility for keeping a rolling log file with a fixed number of lines."""

from __future__ import annotations

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
            self._flush()

    def extend(self, lines: Iterable[str]) -> None:
        """Append multiple lines."""
        with self._lock:
            for line in lines:
                self._buffer.append(_ensure_newline(line))
            self._flush()

    def snapshot(self) -> str:
        """Return current buffer contents as a single string."""
        with self._lock:
            return "".join(self._buffer)

    def clear(self) -> None:
        """Reset buffer and truncate on disk."""
        with self._lock:
            self._buffer.clear()
            self._path.write_text("", encoding=self._encoding)

    # Internal helpers ---------------------------------------------------

    def _load_existing(self) -> None:
        if not self._path.exists():
            return
        try:
            lines = self._path.read_text(encoding=self._encoding).splitlines(True)
        except OSError:
            return
        for line in lines[-self._max_lines :]:
            self._buffer.append(line if line.endswith("\n") else f"{line}\n")

    def _flush(self) -> None:
        self._maybe_rotate()
        try:
            self._path.write_text("".join(self._buffer), encoding=self._encoding)
        except OSError:
            # Suppress write errors to avoid crashing the TD callbacks; user can inspect logs.
            return

    def _maybe_rotate(self) -> None:
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
