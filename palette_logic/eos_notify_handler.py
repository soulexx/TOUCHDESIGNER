"""
Callbacks for handling incoming OSC messages from EOS.

This script expects to be used inside a DAT Execute DAT attached to the OSC In
DAT. Adapt the OSC path parsing as needed for your show file.
"""

import shlex
from typing import Dict, Optional, List


DAM_TAIL_SUFFIXES = (
    "/list",
    "/channels/list",
    "/byType/list",
)

PALETTE_TYPES = ("ip", "fp", "cp", "bp")


def _manager():
    return mod("/project1/palette_logic/subscribe_manager")


def _store_palette_list(palette_type: str, page_data: Dict[int, Dict[str, str]]):
    """
    Store palette data into the corresponding table.

    Args:
        palette_type: palette prefix (ip/fp/cp/bp).
        page_data: mapping index -> {"num": ..., "uid": ..., "label": ...}
    """
    table = op(f"pal_{palette_type}")
    if table is None:
        raise RuntimeError(f"Missing DAT pal_{palette_type}")

    table.clear()
    table.appendRow(["num", "uid", "label"])

    for _, data in sorted(page_data.items()):
        table.appendRow([data["num"], data["uid"], data["label"]])


def _path_info(path: str) -> Optional[Dict[str, str]]:
    """
    Extract palette information from an EOS OSC path.

    Returns dict with keys: type, palette_id, chunk
    """
    parts = [p for p in path.split("/") if p]
    if not parts:
        return None

    for idx, part in enumerate(parts):
        if part in PALETTE_TYPES:
            palette_type = part
            tail = parts[idx + 1 :] if idx + 1 < len(parts) else []

            if not tail:
                return {"type": palette_type, "palette_id": None, "chunk": ""}

            # First element may be palette id or chunk identifier
            palette_id = tail[0]
            chunk = "/".join(tail[1:]) if len(tail) > 1 else ""

            if palette_id in ("list", "index", "notify"):
                # No palette number provided
                palette_id = None
            elif palette_id in ("channels", "byType"):
                return None

            if chunk.startswith("channels") or chunk.startswith("byType"):
                return None

            return {"type": palette_type, "palette_id": palette_id, "chunk": chunk}

    return None


def _parse_palette_row(row) -> Optional[Dict[str, str]]:
    cells = [cell.val for cell in row]

    # Prefer parsing the combined OSC message stored in the first column.
    message = cells[0].strip()
    if len(message) >= 2 and message[0] == message[-1] == "'":
        message = message[1:-1]

    tokens: List[str] = []
    if message.startswith("/"):
        try:
            tokens = shlex.split(message)
        except ValueError:
            tokens = message.split()

    if tokens:
        path = tokens[0]
        info = _path_info(path)
        if not info or not info.get("chunk", "").startswith("list"):
            return None

        values = tokens[1:]
        if not values:
            return None

        try:
            index = int(float(values[0]))
        except (ValueError, TypeError):
            return None

        uid = values[1] if len(values) > 1 else ""
        label_tokens = values[2:]
        label = " ".join(label_tokens).strip().strip('"')
        if not label:
            label = info.get("palette_id") or str(index)

        num = info.get("palette_id") or label

        return {
            "type": info["type"],
            "index": index,
            "num": num,
            "uid": uid.strip('"'),
            "label": label,
        }

    # Fallback: rely on separated columns provided by OSC In DAT.
    raw_path = cells[1] if len(cells) > 1 and cells[1] else cells[0]
    path = raw_path.strip().strip('\'"')
    info = _path_info(path)
    if not info or not info.get("chunk", "").startswith("list"):
        return None

    values = [val.strip().strip('\'"') for val in cells[2:] if val]
    if not values:
        return None

    try:
        index = int(float(values[0]))
    except (ValueError, TypeError):
        return None

    uid = values[1] if len(values) > 1 else ""

    label_tokens: List[str] = []
    for token in values[2:]:
        token = token.strip()
        if token:
            label_tokens.append(token)

    label = " ".join(label_tokens).strip()
    if not label:
        label = info.get("palette_id") or str(index)

    num = info.get("palette_id") or label

    return {
        "type": info["type"],
        "index": index,
        "num": num,
        "uid": uid,
        "label": label,
    }


def _handle_get_index(dat):
    """
    Handle responses from /eos/get/<type>/index queries.

    Each relevant row looks like:
        [path, index, uid, label, ...]
    """

    page_data: Dict[str, Dict[int, Dict[str, str]]] = {}

    for message in dat.rows():
        parsed = _parse_palette_row(message)
        if parsed is None:
            continue

        palette_type = parsed["type"]
        if palette_type not in page_data:
            page_data[palette_type] = {}

        page_data[palette_type][parsed["index"]] = {
            "num": parsed["num"],
            "uid": parsed["uid"],
            "label": parsed["label"],
        }

    touched_types = []
    for palette_type, rows in page_data.items():
        if rows:
            _store_palette_list(palette_type, rows)
            touched_types.append(palette_type)

    return touched_types


def onTableChange(dat):
    """
    DAT Execute hook: react to incoming OSC rows.

    `dat` is the OSC In DAT.
    """
    if dat.numRows < 2:
        return

    first_row = dat.row(1)
    path = first_row[0].val

    _manager().mark_activity()

    info = _path_info(path)
    if info is None:
        return

    updated_types = _handle_get_index(dat)
    for palette_type in updated_types:
        mod('/project1/palette_logic/update_slot_state').update_slot_state(palette_type)

