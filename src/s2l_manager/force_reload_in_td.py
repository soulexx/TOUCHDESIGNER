"""Force TouchDesigner to reload the dispatcher code INTO the DAT itself."""

print("=" * 60)
print("FORCE RELOAD DISPATCHER INTO TOUCHDESIGNER")
print("=" * 60)

# The issue: frame_tick imports sacn_dispatch, but TD caches it
# Solution: Reload the dispatcher DAT content from the file

import sys
import importlib

# Step 1: Clear Python module cache
print("Step 1: Clearing Python module cache...")
if 'sacn_dispatch' in sys.modules:
    del sys.modules['sacn_dispatch']
    print("  ✅ Removed sacn_dispatch from sys.modules")

if 'dispatcher' in sys.modules:
    del sys.modules['dispatcher']
    print("  ✅ Removed dispatcher from sys.modules")

print()

# Step 2: Force frame_tick to reload sacn_dispatch
print("Step 2: Forcing frame_tick to reload sacn_dispatch...")

frame_tick = op('/project1/io/frame_tick')
if frame_tick:
    # Execute the frame_tick code to force import
    exec(frame_tick.text)
    print("  ✅ frame_tick code executed")

    # Now test if it works
    if 'sacn_dispatch' in dir():
        print("  ✅ sacn_dispatch is now in scope")

        # Check if it has the fixed code
        if hasattr(sacn_dispatch, 'op'):
            print(f"  ✅ sacn_dispatch.op exists: {sacn_dispatch.op}")
        else:
            print("  ❌ sacn_dispatch.op does NOT exist!")

        # Reload it
        importlib.reload(sacn_dispatch)
        print("  ✅ sacn_dispatch reloaded")

print()

# Step 3: Test by manually calling handle_universe
print("Step 3: Testing handle_universe with current DMX...")

uni16 = op('/project1/io/EOS_Universe_016')
if uni16:
    # Convert to bytes
    data = []
    for channel in uni16.chans():
        raw = channel[0]
        value = max(0.0, min(255.0, raw))
        data.append(int(round(value)))

    if len(data) > 512:
        data = data[-512:]
    elif len(data) < 512:
        data.extend([0] * (512 - len(data)))

    payload = bytes(data)

    # Clear cache
    if hasattr(sacn_dispatch, '_instances_cache'):
        sacn_dispatch._instances_cache.clear()

    # Call it
    print(f"  Calling handle_universe(payload, 16)...")
    sacn_dispatch.handle_universe(payload, 16)

print()

# Step 4: Check values table
values = op('/project1/src/s2l_manager/values')
if values:
    print(f"Step 4: values table now has {values.numRows} rows")

    if values.numRows > 1:
        print("  ✅ SUCCESS! Values written:")
        for r in range(1, min(8, values.numRows)):
            inst = values[r, 0].val
            param = values[r, 1].val
            val = values[r, 2].val
            if inst == 'S2L_UNIT_1':
                print(f"    {inst} | {param} | {val}")
    else:
        print("  ❌ STILL EMPTY - frame_tick needs manual intervention")

print()
print("=" * 60)
print("NEXT STEP:")
print("=" * 60)
print("If values table is now populated, change a DMX value in Eos")
print("and watch the textport. You should see:")
print("  [s2l_manager] S2L_UNIT_1:Sensitivity -> <new value>")
print()
print("If you DON'T see that, the frame_tick automatic update is not working.")
print("You'll need to manually trigger updates after DMX changes.")
print("=" * 60)
