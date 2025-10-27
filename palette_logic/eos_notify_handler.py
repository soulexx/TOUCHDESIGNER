"""Parse incoming EOS OSC payloads and update palette tables."""
import re
from typing import Sequence

# TouchDesigner-compatible module loading
def _get_module(name):
    """Get palette_logic module using TouchDesigner's mod() function."""
    base = op('/project1')
    if not base:
        raise RuntimeError("Project base not found")
    return mod(f'/project1/palette_logic/{name}')

state = _get_module('state')
pump = _get_module('pump')
ORDER = state.ORDER
TABLE_HEADER = state.TABLE_HEADER

RE_COUNT = re.compile(r"^/eos/out/get/(?P<typ>ip|fp|cp|bp)/count$")
RE_LIST = re.compile(
    r"^/eos/out/get/(?P<typ>ip|fp|cp|bp)/(?P<num>\d+)/list/(?P<idx>\d+)/(?:\d+)$"
)
RE_CHANNELS = re.compile(
    r"^/eos/out/get/(?P<typ>ip|fp|cp|bp)/(?P<num>\d+)/channels/list/(?P<idx>\d+)/(?:\d+)$"
)
RE_BYTYPE = re.compile(
    r"^/eos/out/get/(?P<typ>ip|fp|cp|bp)/(?P<num>\d+)/bytype/list/(?P<idx>\d+)/(?:\d+)$"
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
    # index is now the 1-based palette number (not 0-based array index)
    rows = max(state.state.counts.get(palette_type, 0), index)
    table = state.ensure_table(palette_type, rows)
    if not table:
        return
    header = TABLE_HEADER
    # Row 0 = header, Row 1 = Palette #1, etc.
    row = index
    table[row, header.index("index")] = str(index)
    if state.state.counts.get(palette_type, 0) < index:
        state.state.counts[palette_type] = index
    for key, value in fields.items():
        if value is None or key not in header:
            continue
        table[row, header.index(key)] = str(value)


def on_osc_receive(address: str, args: Sequence[object], timestamp: float = 0.0) -> None:
    base = op("/project1")
    state.attach_base(base)
    state.mark_activity()
    if not address.startswith("/eos/out/get/"):
        return

    match = RE_COUNT.match(address)
    if match:
        palette_type = match.group("typ")
        count = int(float(args[0])) if args else 0
        print(f"[palette] DEBUG received count: {palette_type}={count} | OSC: {address} {args}")
        pump.queue_counts(base, {palette_type: count})
        return

    match = RE_LIST.match(address)
    if match:
        palette_type = match.group("typ")
        palette_num = int(match.group("num"))
        list_index = int(float(args[0])) if args else int(match.group("idx"))
        uid = str(args[1]) if len(args) > 1 else ""
        label = _clean_label(args[2:])
        print(f"[palette] DEBUG received list: {palette_type} #{palette_num} list_idx={list_index} uid={uid} label='{label}'")
        # Use palette_num (not list_index) for row and ACK - that's what pump expects!
        _update_row(
            palette_type, palette_num, num=palette_num, uid=uid, label=label
        )
        pump.on_list_ack(base, palette_type, palette_num)
        return

    match = RE_CHANNELS.match(address)
    if match:
        palette_type = match.group("typ")
        palette_num = int(match.group("num"))
        channels = " ".join(str(item) for item in args[1:])
        print(f"[palette] DEBUG received channels: {palette_type} #{palette_num} channels='{channels}'")
        _update_row(palette_type, palette_num, channels=channels)
        return

    match = RE_BYTYPE.match(address)
    if match:
        palette_type = match.group("typ")
        palette_num = int(match.group("num"))
        bytype = " ".join(str(item) for item in args[1:])
        print(f"[palette] DEBUG received bytype: {palette_type} #{palette_num} bytype='{bytype}'")
        _update_row(palette_type, palette_num, bytype=bytype)
        return

    # Log unrecognized EOS messages for debugging
    print(f"[palette] DEBUG unrecognized OSC: {address} {args}")
