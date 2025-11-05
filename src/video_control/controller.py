"""High level helpers to drive a video TOP from Python.

The helper is designed to run inside TouchDesigner.  It wraps a single
TOP (typically a ``moviefileinTOP``) and exposes a small API for common
transport actions such as play, pause, stop and timeline scrubbing.

Usage inside TouchDesigner::

    import video_control
    vc = video_control.get_controller()
    vc.play()
    vc.set_normalized_time(0.5)  # jump to middle of the clip

The controller resolves the target operator in the following order:

1. Explicit path passed to :class:`VideoController`.
2. Value stored on ``/project1`` under ``VIDEO_TOP_PATH``.
3. The built-in default ``/project1/media/moviefilein1``.

You can persist a different default by calling
``VideoController.set_default_path(path, persist=True)``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Storage key that can be set on /project1 to override the default TOP.
_DEFAULT_STORAGE_KEY = "VIDEO_TOP_PATH"

# Sensible default path that can be edited after importing the module.
_DEFAULT_VIDEO_TOP = "/project1/media/moviefilein1"


def _touchdesigner_op(path: str):
    """Return ``op(path)`` or raise a helpful error when outside TD."""
    op_func = globals().get("op")
    if op_func is None:
        try:
            from td import op as td_op  # type: ignore
        except Exception:
            td_op = None
        op_func = td_op
    if op_func is None:  # pragma: no cover - only outside TD
        raise RuntimeError(
            "TouchDesigner 'op()' function is not available. "
            "Import video_control inside a TouchDesigner session."
        )

    result = op_func(path)
    return result


def _fetch_project_storage(key: str) -> Optional[str]:
    project = _touchdesigner_op("/project1")
    if not project:
        return None
    try:
        value = project.fetch(key, None)
    except Exception:
        value = None
    if not value:
        return None
    return str(value)


def _store_project_value(key: str, value: str) -> None:
    project = _touchdesigner_op("/project1")
    if not project:
        raise RuntimeError("Cannot persist video path: '/project1' not found")
    project.store(key, value)


def _first_child_with_parameter(comp, par_name: str):
    """Return first child that exposes `par_name` or None."""
    try:
        candidates = comp.ops("*")
    except Exception:
        return None
    for child in candidates:
        par_block = getattr(child, "par", None)
        if par_block is None:
            continue
        if getattr(par_block, par_name, None) is not None:
            return child
    return None


@dataclass
class VideoInfo:
    """Snapshot of the transport state."""

    path: str
    playing: bool
    frame: int
    total_frames: Optional[int]
    seconds: Optional[float]
    length_seconds: Optional[float]
    rate: Optional[float]


class VideoController:
    """Lightweight wrapper around a movie/top operator."""

    def __init__(
        self,
        player_path: Optional[str] = None,
        *,
        storage_key: str = _DEFAULT_STORAGE_KEY,
        default_path: str = _DEFAULT_VIDEO_TOP,
    ) -> None:
        self._explicit_path = str(player_path).strip() if player_path else None
        self._storage_key = storage_key
        self._default_path = default_path

    # ------------------------------------------------------------------ #
    # Operator resolution
    # ------------------------------------------------------------------ #
    def _current_path(self) -> str:
        if self._explicit_path:
            return self._explicit_path
        stored = _fetch_project_storage(self._storage_key)
        if stored:
            return stored
        return self._default_path

    def _target(self):
        path = self._current_path()
        if not path:
            raise RuntimeError("Video TOP path is empty")
        target = _touchdesigner_op(path)
        if target is None:
            raise RuntimeError(f"Video TOP '{path}' not found")

        # Accept a COMP wrapper and fall back to the first child with a play parameter
        if getattr(target, "isCOMP", False):
            resolved = _first_child_with_parameter(target, "play")
            if resolved is not None:
                target = resolved
        return target

    def set_default_path(self, path: str, *, persist: bool = False) -> None:
        """Override the target TOP path (optionally storing it on /project1)."""
        cleaned = str(path or "").strip()
        if not cleaned:
            raise ValueError("Path must not be empty")
        self._explicit_path = cleaned
        if persist:
            _store_project_value(self._storage_key, cleaned)

    # ------------------------------------------------------------------ #
    # Parameter helpers
    # ------------------------------------------------------------------ #
    def _get_par(self, target, name: str):
        par_block = getattr(target, "par", None)
        par = getattr(par_block, name, None) if par_block else None
        if par is None:
            raise RuntimeError(f"Operator '{target.path}' has no parameter '{name}'")
        return par

    def _set_par(self, target, name: str, value) -> None:
        par = self._get_par(target, name)
        par.val = value

    def _pulse_par(self, target, name: str) -> None:
        par = self._get_par(target, name)
        pulse = getattr(par, "pulse", None)
        if callable(pulse):
            pulse()
        else:
            par.val = 1
            par.val = 0

    # ------------------------------------------------------------------ #
    # Transport controls
    # ------------------------------------------------------------------ #
    def play(self) -> None:
        target = self._target()
        # Switch to sequential mode for playback
        if hasattr(target.par, "playmode"):
            self._set_par(target, "playmode", "sequential")
        self._set_par(target, "play", 1)

    def pause(self) -> None:
        target = self._target()
        self._set_par(target, "play", 0)
        # Switch to index mode for scrubbing
        if hasattr(target.par, "playmode"):
            self._set_par(target, "playmode", "indexmode")

    def toggle(self) -> None:
        target = self._target()
        par = self._get_par(target, "play")
        current = bool(par.eval())
        if current:
            self.pause()
        else:
            self.play()

    def stop(self) -> None:
        target = self._target()
        self._set_par(target, "play", 0)
        # Switch to index mode for scrubbing
        if hasattr(target.par, "playmode"):
            self._set_par(target, "playmode", "indexmode")
        # Reset to start if index parameter exists
        try:
            self._set_par(target, "index", 0)
        except RuntimeError:
            pass
        # Some setups use cuepulse to restart from cue 1
        if getattr(target.par, "resettop", None) is not None:
            self._pulse_par(target, "resettop")

    # ------------------------------------------------------------------ #
    # Timeline helpers
    # ------------------------------------------------------------------ #
    def _frame_count(self, target) -> Optional[int]:
        for attr in ("numImages", "numframes", "numFrames", "numSamples"):
            if hasattr(target, attr):
                try:
                    count = int(getattr(target, attr))
                    if count > 0:
                        return count
                except Exception:
                    continue
        length_par = getattr(getattr(target, "par", None), "length", None)
        if length_par:
            try:
                count = int(length_par.eval())
                if count > 0:
                    return count
            except Exception:
                pass
        return None

    def _rate(self, target) -> Optional[float]:
        for attr in ("rate", "playbackRate"):
            if hasattr(target, attr):
                try:
                    value = float(getattr(target, attr))
                    if value > 0:
                        return value
                except Exception:
                    continue
        rate_par = getattr(getattr(target, "par", None), "rate", None)
        if rate_par:
            try:
                value = float(rate_par.eval())
                if value > 0:
                    return value
            except Exception:
                pass
        return None

    def _current_frame(self, target) -> Optional[int]:
        try:
            frame_par = self._get_par(target, "index")
        except RuntimeError:
            return None
        try:
            return int(round(float(frame_par.eval())))
        except Exception:
            return None

    def set_frame(self, frame_index: int) -> None:
        target = self._target()
        self._set_par(target, "index", int(frame_index))

    def seek_frames(self, delta_frames: int) -> None:
        target = self._target()
        current = self._current_frame(target) or 0
        self._set_par(target, "index", current + int(delta_frames))

    def set_seconds(self, seconds: float) -> None:
        target = self._target()
        rate = self._rate(target)
        if not rate:
            raise RuntimeError("Cannot convert seconds – rate not available on video TOP")
        frame = int(round(float(seconds) * rate))
        self._set_par(target, "index", frame)

    def seek_seconds(self, delta_seconds: float) -> None:
        target = self._target()
        rate = self._rate(target)
        if not rate:
            raise RuntimeError("Cannot convert seconds – rate not available on video TOP")
        current = self._current_frame(target) or 0
        frame = current + int(round(float(delta_seconds) * rate))
        self._set_par(target, "index", frame)

    def set_normalized_time(self, value: float) -> None:
        target = self._target()
        normalized = max(0.0, min(1.0, float(value)))
        total = self._frame_count(target)
        if not total or total <= 1:
            self._set_par(target, "index", int(normalized * 1000.0))
            return
        frame = int(round(normalized * (total - 1)))
        # Always update the frame
        try:
            print(f"[vc] Setting frame {frame} (normalized={normalized:.6f}, total={total})")
            self._set_par(target, "index", frame)
            # Verify it was set
            actual = self._current_frame(target)
            print(f"[vc] Frame after set: {actual}")
        except Exception as e:
            print(f"[vc] ERROR setting frame: {e}")
            import traceback
            traceback.print_exc()

    # ------------------------------------------------------------------ #
    # Introspection
    # ------------------------------------------------------------------ #
    def info(self) -> VideoInfo:
        target = self._target()
        play_par = self._get_par(target, "play")
        playing = bool(play_par.eval())
        current_frame = self._current_frame(target) or 0
        total = self._frame_count(target)

        rate = self._rate(target)
        seconds = None
        length_seconds = None
        if rate and rate > 0:
            seconds = current_frame / rate
            if total:
                length_seconds = total / rate

        return VideoInfo(
            path=str(target.path),
            playing=playing,
            frame=current_frame,
            total_frames=total,
            seconds=seconds,
            length_seconds=length_seconds,
            rate=rate,
        )


_controller_singleton: Optional[VideoController] = None


def get_controller(reuse: bool = True) -> VideoController:
    """Return a shared :class:`VideoController` instance."""
    global _controller_singleton
    if reuse and _controller_singleton is not None:
        return _controller_singleton
    controller = VideoController()
    if reuse:
        _controller_singleton = controller
    return controller
