"""Utilities for duplicating Textport output into a rolling log file."""

from __future__ import annotations

import io
import sys
import time
from pathlib import Path
from typing import Optional, TextIO

from .file_ring_buffer import FileRingBuffer


class TextportMirror(io.TextIOBase):
    """File-like object that mirrors writes into a FileRingBuffer."""

    def __init__(self, buffer: FileRingBuffer, original: TextIO) -> None:
        self._buffer = buffer
        self._original = original

    def write(self, s: str) -> int:
        self._buffer.append(f"{time.time():.3f} {s.rstrip()}")
        return self._original.write(s)

    def flush(self) -> None:
        self._original.flush()


class TextportLogger:
    """Context manager to mirror stdout/stderr for the TouchDesigner Textport."""

    def __init__(self, log_path: Path, max_lines: int = 400) -> None:
        self._buffer = FileRingBuffer(log_path, max_lines=max_lines)
        self._stdout: Optional[TextIO] = None
        self._stderr: Optional[TextIO] = None

    def install(self) -> None:
        if self._stdout is not None:
            return
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        sys.stdout = TextportMirror(self._buffer, sys.stdout)  # type: ignore
        sys.stderr = TextportMirror(self._buffer, sys.stderr)  # type: ignore

    def uninstall(self) -> None:
        if self._stdout is None:
            return
        sys.stdout = self._stdout  # type: ignore
        sys.stderr = self._stderr  # type: ignore
        self._stdout = None
        self._stderr = None
