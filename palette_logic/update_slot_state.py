"""
Utility helpers to keep the button slot table in sync with EOS palette data.

This script is meant to live inside a Text DAT in TouchDesigner. Convert this
file into a DAT (or copy the contents) and call ``update_slot_state()`` from a
DAT Execute or whenever palette data changes.
"""

from typing import Dict, List, Optional


PALETTE_TABLES: Dict[str, str] = {
    "ip": "pal_ip",
    "fp": "pal_fp",
    "cp": "pal_cp",
    "bp": "pal_bp",
}

SLOT_TEMPLATES: Dict[str, str] = {
    key: f"slots_template_{key}"
    for key in PALETTE_TABLES.keys()
}

SLOT_STATE_DAT = "slot_state"
UI_STATE_DAT = "ui_state"


def _table_headers(table) -> Dict[str, int]:
    """Return a mapping of column name to column index for a DAT table."""
    header_row = table.row(0)
    return {cell.val: idx for idx, cell in enumerate(header_row)}


def _dict_from_table(table) -> Dict[str, str]:
    """Convert a two-column table (key/value) into a dictionary."""
    result = {}
    for row in table.rows()[1:]:
        if len(row) < 2:
            continue
        result[row[0].val] = row[1].val
    return result


def _get_palette_rows(palette_type: str) -> List[List[str]]:
    table_name = PALETTE_TABLES.get(palette_type)
    if not table_name:
        raise ValueError(f"Unsupported palette type '{palette_type}'")
    table = op(table_name)
    if table is None:
        raise RuntimeError(f"Missing DAT '{table_name}' for palette type '{palette_type}'")
    return table.rows()[1:]  # skip header


def _get_slot_template_rows(palette_type: str) -> List[List[str]]:
    template_name = SLOT_TEMPLATES.get(palette_type)
    if not template_name:
        raise ValueError(f"Unsupported palette type '{palette_type}'")
    table = op(template_name)
    if table is None:
        raise RuntimeError(f"Missing DAT '{template_name}' for palette type '{palette_type}'")
    return table.rows()[1:]  # skip header


def update_slot_state(palette_type: Optional[str] = None):
    """
    Populate the slot_state table from the palette list.

    Args:
        palette_type: Optional explicit palette type (ip/fp/cp/bp). If omitted,
                      the value from ui_state.current_type is used.
    """
    slot_state = op(SLOT_STATE_DAT)
    if slot_state is None:
        raise RuntimeError(f"Missing DAT '{SLOT_STATE_DAT}'")

    headers = _table_headers(slot_state)

    ui_state = op(UI_STATE_DAT)
    if ui_state is None:
        raise RuntimeError(f"Missing DAT '{UI_STATE_DAT}'")

    state = _dict_from_table(ui_state)
    palette_type = palette_type or state.get("current_type", "ip")
    page = int(state.get("page", 1) or 1)

    palette_rows = _get_palette_rows(palette_type)
    template_rows = _get_slot_template_rows(palette_type)

    page_size = len(template_rows)
    start_index = max(0, (page - 1) * page_size)

    for slot_idx, template_row in enumerate(template_rows):
        slot_name = template_row[0].val
        state_row_index = slot_idx + 1  # +1 because row 0 is header

        palette_index = start_index + slot_idx
        if palette_index < len(palette_rows):
            palette_row = palette_rows[palette_index]
            num = palette_row[0].val
            label = palette_row[2].val or num
            has_palette = "1"
        else:
            num = "0"
            label = "--"
            has_palette = "0"

        slot_state[state_row_index, headers["slot"]] = slot_name
        slot_state[state_row_index, headers["num"]] = num
        slot_state[state_row_index, headers["label"]] = label
        slot_state[state_row_index, headers["has_palette"]] = has_palette


# Allow manual testing inside TouchDesigner by calling this DAT directly.
def onPulse(par):
    update_slot_state()
