"""Deep debug: why is handle_universe not writing to values table?"""

import sys

# Setup paths
sacn_path = 'C:/_DEV/TOUCHDESIGNER/io'
if sacn_path not in sys.path:
    sys.path.insert(0, sacn_path)

print("=" * 60)
print("DEEP DEBUG: Why handle_universe doesn't write")
print("=" * 60)

# Import fresh
if 'sacn_dispatch' in sys.modules:
    del sys.modules['sacn_dispatch']

import sacn_dispatch
print(f"✅ sacn_dispatch imported: {sacn_dispatch}")
print()

# Check what MANAGER_DAT_PATH is
print(f"MANAGER_DAT_PATH: {sacn_dispatch.MANAGER_DAT_PATH}")

# Try to get the manager DAT
manager_dat = op(sacn_dispatch.MANAGER_DAT_PATH)
if manager_dat:
    print(f"✅ Manager DAT found: {manager_dat}")
else:
    print(f"❌ Manager DAT NOT FOUND at {sacn_dispatch.MANAGER_DAT_PATH}")
    print()
    print("Let me search for dispatcher...")

    # Search for it
    possible_paths = [
        '/project1/src/s2l_manager/dispatcher',
        '/project1/s2l_manager/dispatcher',
        '//s2l_manager/dispatcher'
    ]

    for path in possible_paths:
        test_op = op(path)
        if test_op:
            print(f"  Found at: {path}")

print()

if manager_dat:
    # Check if it has the update_from_dmx function
    print("Checking manager DAT module...")

    if hasattr(manager_dat, 'module'):
        print(f"  ✅ Has .module: {manager_dat.module}")

        if hasattr(manager_dat.module, 'update_from_dmx'):
            print(f"  ✅ Has .module.update_from_dmx: {manager_dat.module.update_from_dmx}")

            # Try to call it directly
            print()
            print("Testing direct call to dispatcher.update_from_dmx()...")

            test_values = {
                'S2L_UNIT_1': {
                    'Sensitivity': 99,
                    'Threshold': 88
                }
            }
            test_defaults = {}

            try:
                manager_dat.module.update_from_dmx(16, test_values, test_defaults)
                print("  ✅ Direct call succeeded")
            except Exception as e:
                print(f"  ❌ Direct call failed: {e}")
                import traceback
                traceback.print_exc()

        else:
            print(f"  ❌ Does NOT have .module.update_from_dmx")
    else:
        print(f"  ❌ Does NOT have .module attribute")

print()

# Check values table directly
values = op('/project1/src/s2l_manager/values')
if values:
    print(f"values table: {values.numRows} rows, {values.numCols} cols")

    if values.numRows > 1:
        print("Content:")
        for r in range(1, min(5, values.numRows)):
            row = [values[r, c].val for c in range(values.numCols)]
            print(f"  Row {r}: {row}")
    else:
        print("  Empty (only header)")

print()
print("=" * 60)
print("DIAGNOSIS:")

if not manager_dat:
    print("❌ The dispatcher DAT cannot be found!")
    print("   sacn_dispatch is looking for: " + sacn_dispatch.MANAGER_DAT_PATH)
    print("   But this path doesn't exist in TouchDesigner")
    print()
    print("SOLUTION: Check the actual path of the dispatcher DAT in TD")

elif not hasattr(manager_dat, 'module') or not hasattr(manager_dat.module, 'update_from_dmx'):
    print("❌ The dispatcher DAT doesn't have the update_from_dmx function!")
    print("   This means the dispatcher.py code is not loaded in the DAT")
    print()
    print("SOLUTION: Make sure the dispatcher DAT has 'Sync to File' enabled")
    print("   and points to: C:/_DEV/TOUCHDESIGNER/src/s2l_manager/dispatcher.py")

print("=" * 60)
