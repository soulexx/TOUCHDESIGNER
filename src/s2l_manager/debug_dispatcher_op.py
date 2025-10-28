"""Debug if dispatcher has access to op() and the values table."""

import sys
import importlib

# Reload dispatcher
manager_path = 'C:/_DEV/TOUCHDESIGNER/src/s2l_manager'
if manager_path not in sys.path:
    sys.path.insert(0, manager_path)

import dispatcher
importlib.reload(dispatcher)

print("=" * 60)
print("DISPATCHER DEBUG")
print("=" * 60)

print(f"dispatcher module: {dispatcher}")
print(f"Has 'op': {hasattr(dispatcher, 'op')}")
if hasattr(dispatcher, 'op'):
    print(f"  dispatcher.op = {dispatcher.op}")
print()

print(f"VALUES_TABLE_PATH: {dispatcher.VALUES_TABLE_PATH}")
print()

# Try to call _ensure_table
print("Calling dispatcher._ensure_table()...")
try:
    table = dispatcher._ensure_table()
    if table:
        print(f"✅ Got table: {table}")
        print(f"   Rows: {table.numRows}")
        print(f"   Cols: {table.numCols}")
    else:
        print("❌ _ensure_table() returned None")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()

# Try to manually call update_from_dmx
print("Testing dispatcher.update_from_dmx()...")

test_values = {
    'S2L_UNIT_1': {
        'Sensitivity': 123,
        'Threshold': 234
    }
}

test_defaults = {}

try:
    dispatcher.update_from_dmx(16, test_values, test_defaults)
    print("✅ update_from_dmx() called successfully")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()

# Check values table again
values = op('/project1/src/s2l_manager/values')
if values:
    print(f"values table: {values.numRows} rows, {values.numCols} cols")
    if values.numRows > 1:
        for r in range(1, min(5, values.numRows)):
            print(f"  Row {r}: {values[r,0].val} | {values[r,1].val} | {values[r,2].val}")
else:
    print("❌ values table not found")

print("=" * 60)
