# c:\_DEV\TOUCHDESIGNER\src\tools\td_fix_palettes.py
import textwrap
import time
import td

TABLE_HEADER = ["index", "num", "uid", "label", "channels", "bytype"]

STATE_CODE = textwrap.dedent(
    """\
    \"\"\"Palette state management for EOS palette synchronisation.\"\"\"
    import time
    from collections import deque
    from typing import Deque, Dict, Optional

    ORDER = ["ip", "fp", "cp", "bp"]
    TABLE_HEADER = ["index", "num", "uid", "label", "channels", "bytype"]


    class PaletteState:
        def __init__(self) -> None:
            now = time.perf_counter()
            self.base = None
            self.last_activity = now
            self.last_subscribe = 0.0
            self.last_count_request = 0.0
            self.subscribed = False
            self.counts: Dict[str, int] = {t: 0 for t in ORDER}
            self.queues: Dict[str, Deque[int]] = {t: deque() for t in ORDER}
            self.active: Dict[str, Optional[int]] = {t: None for t in ORDER}
            self.sent_at: Dict[str, float] = {t: 0.0 for t in ORDER}
            self.attempts: Dict[str, int] = {t: 0 for t in ORDER}

        def attach_base(self, base) -> None:
            if base and base != self.base:
                self.base = base

        def get_table(self, palette_type: str):
            if not self.base:
                return None
            return self.base.op(f"palette_logic/pal_{palette_type}")

        def ensure_table(self, palette_type: str, rows: int):
            table = self.get_table(palette_type)
            if not table:
                return None
            if table.numRows == 0:
                table.appendRow(TABLE_HEADER)
            else:
                while table.numCols < len(TABLE_HEADER):
                    table.appendCol("")
                for col, name in enumerate(TABLE_HEADER):
                    table[0, col] = name
            desired = max(rows, 0) + 1
            while table.numRows > desired:
                table.deleteRow(table.numRows - 1)
            while table.numRows < desired:
                table.appendRow([""] * table.numCols)
            return table


    state = PaletteState()
    __all__ = [
        "ORDER",
        "TABLE_HEADER",
        "state",
        "attach_base",
        "get_base",
        "get_table",
        "ensure_table",
        "get_osc_out",
        "mark_activity",
        "note_subscribe",
        "note_count_request",
    ]


    def attach_base(base) -> None:
        state.attach_base(base)


    def get_base():
        return state.base


    def get_table(palette_type: str):
        return state.get_table(palette_type)


    def ensure_table(palette_type: str, rows: int):
        return state.ensure_table(palette_type, rows)


    def get_osc_out():
        base = get_base()
        return base.op("io/oscout1") if base else None


    def mark_activity() -> None:
        state.last_activity = time.perf_counter()


    def note_subscribe() -> None:
        state.subscribed = True
        state.last_subscribe = time.perf_counter()


    def note_count_request() -> None:
        state.last_count_request = time.perf_counter()
    """
)

PUMP_CODE = textwrap.dedent(
    """\
    \"\"\"Serial palette index pump.\"\"\"
    import time
    from typing import Dict
    from . import state
    from .state import ORDER

    INDEX_TIMEOUT = 3.0
    RETRY_LIMIT = 3


    def attach_base(base) -> None:
        state.attach_base(base)


    def queue_counts(base, mapping: Dict[str, int]) -> None:
        state.attach_base(base)
        now = time.perf_counter()
        state.state.last_count_request = now
        for palette_type, count in mapping.items():
            _apply_count(palette_type, int(count))
        for palette_type in mapping.keys():
            _send_next_index(palette_type)


    def _apply_count(palette_type: str, count: int) -> None:
        count = max(0, count)
        st = state.state
        st.counts[palette_type] = count
        queue = st.queues[palette_type]
        queue.clear()
        queue.extend(range(count))
        st.active[palette_type] = None
        st.sent_at[palette_type] = 0.0
        st.attempts[palette_type] = 0
        state.ensure_table(palette_type, count)


    def on_list_ack(base, palette_type: str, index: int) -> None:
        state.attach_base(base)
        st = state.state
        active = st.active[palette_type]
        if active != index:
            return
        queue = st.queues[palette_type]
        if queue and queue[0] == index:
            queue.popleft()
        elif index in queue:
            queue.remove(index)
        st.active[palette_type] = None
        st.sent_at[palette_type] = 0.0
        st.attempts[palette_type] = 0
        _send_next_index(palette_type)


    def tick(base) -> None:
        state.attach_base(base)
        st = state.state
        now = time.perf_counter()
        for palette_type in ORDER:
            active = st.active[palette_type]
            if active is None:
                if st.queues[palette_type]:
                    _send_next_index(palette_type)
                continue
            if now - st.sent_at[palette_type] <= INDEX_TIMEOUT:
                continue
            osc = state.get_osc_out()
            if not osc:
                continue
            if st.attempts[palette_type] >= RETRY_LIMIT:
                queue = st.queues[palette_type]
                if queue and queue[0] == active:
                    queue.popleft()
                st.active[palette_type] = None
                st.attempts[palette_type] = 0
                print(f"[palette] WARN giving up on {palette_type}:{active}")
                _send_next_index(palette_type)
            else:
                osc.sendOSC(f"/eos/get/{palette_type}/index/{active}", [])
                st.sent_at[palette_type] = now
                st.attempts[palette_type] += 1
                print(
                    f"[palette] resend {palette_type}:{active} attempt {st.attempts[palette_type]}"
                )


    def _send_next_index(palette_type: str) -> None:
        st = state.state
        if st.active[palette_type] is not None:
            return
        queue = st.queues[palette_type]
        if not queue:
            return
        osc = state.get_osc_out()
        if not osc:
            return
        index = queue[0]
        osc.sendOSC(f"/eos/get/{palette_type}/index/{index}", [])
        st.active[palette_type] = index
        st.sent_at[palette_type] = time.perf_counter()
        st.attempts[palette_type] = 1
        print(f"[palette] send index {palette_type} -> {index}")
    """
)

WATCHDOG_CODE = textwrap.dedent(
    """\
    \"\"\"Subscription / count watchdog.\"\"\"
    import time
    from . import state
    from .state import ORDER

    SUBSCRIBE_BACKOFF = 5.0
    COUNT_BACKOFF = 10.0


    def ensure_subscribed(base) -> None:
        state.attach_base(base)
        st = state.state
        now = time.perf_counter()
        osc = state.get_osc_out()
        if not osc:
            return
        if (now - st.last_activity) > SUBSCRIBE_BACKOFF and (
            now - st.last_subscribe
        ) > SUBSCRIBE_BACKOFF:
            osc.sendOSC("/eos/subscribe", [1])
            st.last_subscribe = now
            st.subscribed = True
            print("[palette] subscribe sent")
        if (now - st.last_count_request) > COUNT_BACKOFF:
            request_all_counts(base)


    def request_all_counts(base) -> None:
        state.attach_base(base)
        st = state.state
        osc = state.get_osc_out()
        if not osc:
            print("[palette] WARN osc_out DAT missing; cannot request counts")
            return
        st.last_count_request = time.perf_counter()
        for palette_type in ORDER:
            osc.sendOSC(f"/eos/get/{palette_type}/count", [])
            print(f"[palette] count request {palette_type}")
    """
)

EOS_HANDLER_CODE = textwrap.dedent(
    """\
    \"\"\"Parse incoming EOS OSC payloads and update palette tables.\"\"\"
    import re
    from typing import Sequence
    from . import state, pump
    from .state import ORDER, TABLE_HEADER

    RE_COUNT = re.compile(r"^/eos/out/get/(?P<typ>ip|fp|cp|bp)/count$")
    RE_LIST = re.compile(
        r"^/eos/out/get/(?P<typ>ip|fp|cp|bp)/(?P<num>\\d+)/list/(?P<idx>\\d+)/(?:\\d+)$"
    )
    RE_CHANNELS = re.compile(
        r"^/eos/out/get/(?P<typ>ip|fp|cp|bp)/(?P<num>\\d+)/channels/list/(?P<idx>\\d+)/(?:\\d+)$"
    )
    RE_BYTYPE = re.compile(
        r"^/eos/out/get/(?P<typ>ip|fp|cp|bp)/(?P<num>\\d+)/bytype/list/(?P<idx>\\d+)/(?:\\d+)$"
    )


    def _clean_label(tokens: Sequence[object]) -> str:
        cleaned = []
        for token in tokens:
            text = str(token).strip()
            if not text:
                continue
            lower = text.lower()
            if lower in {"true", "false", "0", "1"} and cleaned:
                continue
            cleaned.append(text)
        return " ".join(cleaned)


    def _update_row(palette_type: str, index: int, **fields) -> None:
        rows = max(state.state.counts.get(palette_type, 0), index + 1)
        table = state.ensure_table(palette_type, rows)
        if not table:
            return
        header = TABLE_HEADER
        row = index + 1
        table[row, header.index("index")] = str(index)
        if state.state.counts.get(palette_type, 0) < index + 1:
            state.state.counts[palette_type] = index + 1
        for key, value in fields.items():
            if value is None or key not in header:
                continue
            table[row, header.index(key)] = str(value)


    def on_osc_receive(address: str, args: Sequence[object], timestamp: float = 0.0) -> None:
        base = td.op("/project1")
        state.attach_base(base)
        state.mark_activity()
        if not address.startswith("/eos/out/get/"):
            return

        match = RE_COUNT.match(address)
        if match:
            palette_type = match.group("typ")
            count = int(float(args[0])) if args else 0
            pump.queue_counts(base, {palette_type: count})
            return

        match = RE_LIST.match(address)
        if match:
            palette_type = match.group("typ")
            palette_num = int(match.group("num"))
            index = int(float(args[0])) if args else int(match.group("idx"))
            uid = str(args[1]) if len(args) > 1 else ""
            label = _clean_label(args[2:])
            _update_row(
                palette_type, index, num=palette_num, uid=uid, label=label
            )
            pump.on_list_ack(base, palette_type, index)
            return

        match = RE_CHANNELS.match(address)
        if match:
            palette_type = match.group("typ")
            index = int(float(args[0])) if args else int(match.group("idx"))
            channels = " ".join(str(item) for item in args[1:])
            _update_row(palette_type, index, channels=channels)
            return

        match = RE_BYTYPE.match(address)
        if match:
            palette_type = match.group("typ")
            index = int(float(args[0])) if args else int(match.group("idx"))
            bytype = " ".join(str(item) for item in args[1:])
            _update_row(palette_type, index, bytype=bytype)
            return
    """
)

INIT_CODE = """"""

TICK_CODE = textwrap.dedent(
    """\
    def onFrameStart(frame):
        base = op('/project1')
        if not base:
            return
        if not bool(base.fetch('PALETTE_SYNC_ENABLED', False)):
            return
        try:
            watchdog = mod('/project1/palette_logic/watchdog')
            pump = mod('/project1/palette_logic/pump')
            state = mod('/project1/palette_logic/state')
        except Exception as exc:
            print('[tick_exec] palette modules unavailable:', exc)
            return
        state.attach_base(base)
        fps = max(int(absTime.rate), 1)
        if frame % fps == 0:
            watchdog.ensure_subscribed(base)
        pump_div = max(int(fps / 5), 1)
        if frame % pump_div == 0:
            pump.tick(base)
        return
    """
)


def _ensure_text_dat(parent, filename, content):
    name = filename.split(".")[0]
    dat = parent.op(name)
    if not dat:
        dat = parent.create("textDAT", name)
    if dat.text != content:
        dat.text = content
    return dat


def _ensure_palette_table(parent, name):
    table = parent.op(name)
    if not table:
        table = parent.create("tableDAT", name)
    if table.numRows == 0:
        table.appendRow(TABLE_HEADER)
    else:
        header = [cell.val for cell in table.row(0)]
        if header != TABLE_HEADER:
            table.clear()
            table.appendRow(TABLE_HEADER)
    return table


def _ensure_tick_exec(io_comp):
    tick = io_comp.op("tick_exec")
    if not tick:
        tick = io_comp.create("datExecuteDAT", "tick_exec")
    tick.par.active = True
    if hasattr(tick.par, "frame"):
        tick.par.frame = True
    if hasattr(tick.par, "framesustain"):
        tick.par.framesustain = True
    if tick.text != TICK_CODE:
        tick.text = TICK_CODE
    return tick


def _ensure_osc_out(io_comp):
    osc_out = io_comp.op("oscout1")
    if not osc_out:
        osc_out = io_comp.create("oscOutDAT", "oscout1")
    osc_out.par.port = 8001
    return osc_out


def _warn(msg):
    print(f"[palette] WARN {msg}")


def run_fix():
    project = td.op("/project1")
    if not project:
        raise RuntimeError("COMP /project1 not found")

    palette_logic = project.op("palette_logic")
    if not palette_logic:
        palette_logic = project.create("baseCOMP", "palette_logic")

    if project.fetch("PALETTE_SYNC_ENABLED", None) is None:
        project.store("PALETTE_SYNC_ENABLED", False)

    _ensure_text_dat(palette_logic, "state.py", STATE_CODE)
    _ensure_text_dat(palette_logic, "pump.py", PUMP_CODE)
    _ensure_text_dat(palette_logic, "watchdog.py", WATCHDOG_CODE)
    _ensure_text_dat(palette_logic, "eos_notify_handler.py", EOS_HANDLER_CODE)
    _ensure_text_dat(palette_logic, "__init__.py", INIT_CODE)

    for name in ("pal_ip", "pal_fp", "pal_cp", "pal_bp"):
        _ensure_palette_table(palette_logic, name)

    io_comp = project.op("io")
    if not io_comp:
        io_comp = project.create("baseCOMP", "io")

    _ensure_tick_exec(io_comp)
    osc_out = _ensure_osc_out(io_comp)

    osc_in = io_comp.op("osc_in")
    if not osc_in:
        osc_in = io_comp.op("oscin1_from_eos")
    if not osc_in:
        _warn("OSC In DAT /project1/io/osc_in fehlt")
    else:
        callbacks = (
            osc_in.par.callbacks.eval() if hasattr(osc_in.par, "callbacks") else ""
        )
        if not any(
            name in str(callbacks)
            for name in ("osc_in_callbacks", "oscin1_callbacks")
        ):
            _warn(
                "OSC In callbacks Feld verweist nicht auf io/osc_in_callbacks.py bzw. io/oscin1_callbacks.py"
            )

    palette_logic.mod.reload()
    palette_logic.mod.state.attach_base(project)
    palette_logic.mod.pump.attach_base(project)

    palettes_enabled = bool(project.fetch("PALETTE_SYNC_ENABLED", False))

    if osc_out and palettes_enabled:
        osc_out.sendOSC("/eos/filter/clear", [])
        time.sleep(0.05)
        osc_out.sendOSC("/eos/subscribe", [1])
        palette_logic.mod.watchdog.request_all_counts(project)
        time.sleep(0.05)
        palette_logic.mod.pump.tick(project)
    elif not osc_out:
        _warn("OSC Out DAT konnte nicht initialisiert werden")
    else:
        _warn(
            "Palette-Sync ist deaktiviert (PALETTE_SYNC_ENABLED=0); keine Subscribe-Anfragen gesendet."
        )

    print("[palette] TD palettes fix complete. Set OSC Out remote IP in Eos if required.")
