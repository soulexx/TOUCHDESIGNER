import sys
import time
from pathlib import Path
from typing import Optional

BASE_PATH = Path(r"c:\_DEV\TOUCHDESIGNER")
SRC_PATH = BASE_PATH / "src"
IO_PATH = BASE_PATH / "io"
for candidate in (SRC_PATH, IO_PATH):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from td_helpers.file_ring_buffer import FileRingBuffer


def _resolve_op_callable():
    """Return a callable similar to TD's op() function if available."""
    try:
        return op  # type: ignore[name-defined]
    except Exception:
        pass
    try:
        import td

        return td.op  # type: ignore[attr-defined]
    except Exception:
        pass
    proj = globals().get("project")
    if proj and hasattr(proj, "op"):
        return proj.op
    return None


_OP_CALLABLE = _resolve_op_callable()


class MidiDispatcher:
    """
    Small helper that converts raw TouchDesigner MIDI callbacks into events in
    `/project1/io/bus_events`.  A single instance can be shared by multiple DATs:

        handler = MidiDispatcher(api_path="/project1/io/midicon_api")
        def onReceiveMIDI(...):
            handler.handle(...)
    """

    def __init__(
        self,
        *,
        api_path: str,
        log_name: str = "midi_in.log",
        bus_dat_path: str = "/project1/io/bus_events",
        filter_op_path: str = "/project1/layers/menus/event_filters",
        max_log_lines: int = 400,
        device_label: Optional[str] = None,
    ) -> None:
        self._api_path = api_path
        self._bus_dat_path = bus_dat_path
        self._filter_op_path = filter_op_path
        self._log = FileRingBuffer(
            BASE_PATH / "logs" / log_name,
            max_lines=max_log_lines,
            persist=True,
        )
        self._default_label = (device_label or "device").strip() or "device"

    # ------------------------------------------------------------------ helpers
    def _fetch_op(self, path: Optional[str]):
        if not path:
            return None
        op_fn = _resolve_op_callable()
        if op_fn is None:
            return None
        try:
            return op_fn(path)
        except Exception:
            return None

    def _resolve_api(self, dat):
        override = None
        try:
            override = dat.fetch("api_path", None)
        except Exception:
            override = None
        path = override or self._api_path
        comp = self._fetch_op(path)
        if not comp:
            return None, None
        try:
            return comp.module, comp
        except Exception:
            return None, comp

    def _resolve_filter(self, dat):
        override = None
        try:
            override = dat.fetch("filter_op_path", None)
        except Exception:
            override = None
        path = override or self._filter_op_path
        comp = self._fetch_op(path)
        if not comp:
            return None
        try:
            return comp.module
        except Exception:
            return None

    def _extract_label_from_api(self, api_module, api_comp) -> Optional[str]:
        map_op = getattr(api_module, "MAP", None)
        if map_op is None or not getattr(map_op, "valid", True):
            map_path = getattr(api_module, "MAP_PATH", None)
            if map_path:
                map_op = self._fetch_op(map_path)
                if map_op:
                    try:
                        setattr(api_module, "MAP", map_op)
                    except Exception:
                        pass
        if map_op is None and api_comp is not None:
            try:
                map_path = api_comp.par.Mapdat.eval() if hasattr(api_comp.par, "Mapdat") else None
            except Exception:
                map_path = None
            if map_path:
                map_op = self._fetch_op(map_path)
        if map_op is None:
            return None
        if getattr(map_op, "name", ""):
            return map_op.name
        try:
            return map_op.path.rsplit("/", 1)[-1]
        except Exception:
            return None

    def _source_name(self, dat, api_module, api_comp, input_obj) -> str:
        label = None
        try:
            label = dat.fetch("device_label", None)
        except Exception:
            label = None

        if not label:
            label = self._extract_label_from_api(api_module, api_comp)

        if not label:
            try:
                if input_obj and not isinstance(input_obj, (bool, int, float)):
                    label = getattr(input_obj, "name", str(input_obj))
                elif isinstance(input_obj, str):
                    label = input_obj
            except Exception:
                label = None

        label = (str(label).strip() if label else "") or self._default_label
        return label

    def _append_bus(self, topic, etype, channel, index, value, raw, src):
        table = self._fetch_op(self._bus_dat_path)
        if not table:
            return
        if table.numRows == 0:
            table.appendRow(["ts", "src", "etype", "ch", "id", "val", "raw", "path"])
        table.appendRow(
            [
                time.time(),
                src,
                etype,
                channel,
                index,
                value,
                "" if raw is None else raw,
                "/" + topic.lstrip("/"),
            ]
        )

    # ----------------------------------------------------------------- public
    def handle(self, dat, rowIndex, message, channel, index, value, input_obj, bytes):
        try:
            self._log.append(
                f"{time.time():.3f} IN {message} ch{channel} idx{index} val{value}"
            )
        except Exception:
            pass

        api_module, api_comp = self._resolve_api(dat)
        if api_module is None:
            return

        filt_module = self._resolve_filter(dat)
        midi_to_topic = getattr(api_module, "midi_to_topic", None)
        if not callable(midi_to_topic):
            return

        topic, kind = midi_to_topic(message, int(channel), int(index))
        if not topic:
            return

        src_name = self._source_name(dat, api_module, api_comp, input_obj)

        if message in ("Note On", "Note Off"):
            is_press = message == "Note On" and int(value) > 0
            wheel_topic = None
            wheel_dir = 0
            if kind in ("enc_rel_up", "enc_rel_down"):
                wheel_topic = topic
                wheel_dir = 1 if kind == "enc_rel_up" else -1
            elif topic.startswith("midicon/wheel/"):
                base, _, action = topic.rpartition("/")
                if action in ("up", "down"):
                    wheel_topic = base
                    wheel_dir = 1 if action == "up" else -1
            if wheel_topic is not None:
                if not is_press:
                    return
                self._append_bus(
                    wheel_topic,
                    "enc_rel",
                    channel,
                    index,
                    wheel_dir,
                    raw=value,
                    src=src_name,
                )
                return
            v = 1 if is_press else 0
            self._append_bus(topic, "note", channel, index, v, raw=value, src=src_name)
            return

        if message != "Control Change":
            return

        if kind in ("enc_rel", "enc_rel_up", "enc_rel_down"):
            if kind == "enc_rel_up":
                delta = 1
            elif kind == "enc_rel_down":
                delta = -1
            else:
                delta = int(value) if int(value) < 64 else int(value) - 128
            self._append_bus(topic, "enc_rel", channel, index, delta, raw=value, src=src_name)
            return

        if kind in ("fader_msb", "fader_lsb"):
            part = "msb" if kind == "fader_msb" else "lsb"
            norm = float(value) / 127.0
            combined = None
            if filt_module:
                smooth = getattr(filt_module, "fader_smooth", None)
                if callable(smooth):
                    combined = smooth(topic + "/" + part, norm)
            if combined is None and part == "msb":
                combined = norm
            if combined is not None:
                self._append_bus(
                    topic,
                    "cc7",
                    channel,
                    index,
                    float(combined),
                    raw=value,
                    src=src_name,
                )
            return

        self._append_bus(
            topic,
            "cc7",
            channel,
            index,
            float(value) / 127.0,
            raw=value,
            src=src_name,
        )

    @property
    def default_label(self) -> str:
        return self._default_label
