"""
Simple solution: Force frame_tick to reload sacn_dispatch module.

Run this ONCE after opening TouchDesigner or after editing sacn_dispatch.py
Then the automatic updates will work.
"""

import sys
import importlib

print("=" * 60)
print("RELOAD MODULES FOR FRAME TICK")
print("=" * 60)

# Remove from cache
modules_to_reload = ['sacn_dispatch', 'dispatcher', 's2l_unit']

for mod_name in modules_to_reload:
    if mod_name in sys.modules:
        del sys.modules[mod_name]
        print(f"✅ Removed {mod_name} from cache")

print()
print("Now the frame_tick will load the fresh modules on next frame!")
print()

# Trigger frame_tick once manually to force reload
frame_tick = op('/project1/io/frame_tick')
if frame_tick:
    print("Manually triggering frame_tick to force module reload...")

    # Execute it
    exec(frame_tick.text)

    # Call onFrameStart if it exists
    if 'onFrameStart' in dir():
        onFrameStart(frame_tick)
        print("✅ frame_tick executed with fresh modules")
    else:
        print("⚠️  onFrameStart not found")

print()

# Check values table
values = op('/project1/src/s2l_manager/values')
if values:
    print(f"values table: {values.numRows} rows")

    if values.numRows > 1:
        print("✅ Data written:")
        for r in range(1, min(8, values.numRows)):
            inst = values[r, 0].val
            param = values[r, 1].val
            val = values[r, 2].val
            if inst == 'S2L_UNIT_1' and param in ['Sensitivity', 'Threshold']:
                print(f"  {inst} | {param} | {val}")
    else:
        print("⚠️  Still empty - check if DMX has non-zero values")

print()
print("=" * 60)
print("TEST NOW:")
print("=" * 60)
print("1. Change a DMX value in Eos (e.g. Channel 11)")
print("2. Watch the textport - you should see:")
print("   [s2l_manager] S2L_UNIT_1:Sensitivity -> <new value>")
print()
print("If you see that, automatic updates are working! 🎉")
print("=" * 60)
